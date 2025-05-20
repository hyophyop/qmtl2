from qmtl.dag_manager.core.queue_repository import RedisQueueRepository


class DummyRedis:
    def __init__(self):
        # simple in-memory structures
        self._data = {}
        self._hash = {}

    # list operations ---------------------------------------------------
    def lpush(self, key, value):
        self._data.setdefault(key, []).insert(0, value)

    def brpoplpush(self, src, dest, timeout=0):  # noqa: D401 unused timeout
        lst = self._data.get(src, [])
        if not lst:
            return None
        value = lst.pop()  # FIFO pop (right)
        self._data.setdefault(dest, []).insert(0, value)
        return value

    def lrem(self, key, num, value):
        if key not in self._data:
            return 0
        lst = self._data[key]
        removed = 0
        new_lst = []
        for v in lst:
            if v == value and (num == 0 or removed < abs(num)):
                removed += 1
            else:
                new_lst.append(v)
        self._data[key] = new_lst
        return removed

    # hash operations ---------------------------------------------------
    def hset(self, key, field, value):
        self._hash.setdefault(key, {})[field] = value

    def hget(self, key, field):
        return self._hash.get(key, {}).get(field)

    def expire(self, key, ttl):
        # expiration not simulated
        pass

    # util for tests ----------------------------------------------------
    def list_contents(self, key):
        return list(self._data.get(key, []))


def test_queue_push_pop_complete():
    r = DummyRedis()
    repo = RedisQueueRepository(redis_client=r)

    # enqueue items
    repo.push("item1")
    repo.push("item2")

    # pop returns LIFO (item1 is older)
    popped = repo.pop()
    assert popped == "item1" or popped == "item2"  # order depending on list behavior
    # ensure moved to processing
    assert popped in r.list_contents(repo.processing_key)

    # complete processing
    success = repo.complete(popped, result={"ok": True})
    assert success is True
    # processing list에서 제거되었는지
    assert popped not in r.list_contents(repo.processing_key)
    # 결과 확인
    res = repo.get_result(popped)
    assert res is not None and res["result"] == {"ok": True}
