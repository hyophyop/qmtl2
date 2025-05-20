from qmtl.dag_manager.core.queue_worker import QueueWorker
from qmtl.models.datanode import DataNode, NodeStreamSettings, IntervalSettings
from qmtl.sdk.models import IntervalEnum
from unittest.mock import MagicMock

# Dummy Redis identical to one used before ----------------------------------


class DummyRedis:
    def __init__(self):
        self._data = {}
        self._hash = {}

    def lpush(self, key, value):
        self._data.setdefault(key, []).insert(0, value)

    def brpoplpush(self, src, dest, timeout=0):
        lst = self._data.get(src, [])
        if not lst:
            return None
        val = lst.pop()
        self._data.setdefault(dest, []).insert(0, val)
        return val

    def lrem(self, key, num, value):
        if key not in self._data:
            return 0
        lst = self._data[key]
        count = 0
        self._data[key] = [
            v
            for v in lst
            if not (v == value and (num == 0 or count < abs(num)) and (count := count + 1))
        ]
        return count

    def hset(self, key, field, value):
        self._hash.setdefault(key, {})[field] = value

    def hget(self, key, field):
        return self._hash.get(key, {}).get(field)

    def expire(self, key, ttl):
        pass

    def list_contents(self, key):
        return list(self._data.get(key, []))


# Helpers -------------------------------------------------------------------


def _stream():
    interval_settings = IntervalSettings(interval=IntervalEnum.MINUTE, period=1)
    return NodeStreamSettings(intervals={IntervalEnum.MINUTE: interval_settings})


class DummyNodeService:
    def __init__(self, nodes):
        self._nodes = nodes

    def get_strategy_nodes(self, strategy_version_id):
        return self._nodes


# ---------------------------------------------------------------------------


def test_queue_worker_flow():
    # DAG: n1 -> n2 -> n3
    n1 = DataNode(
        node_id="1" * 32, data_format={"type": "csv"}, dependencies=[], stream_settings=_stream()
    )
    n2 = DataNode(
        node_id="2" * 32,
        data_format={"type": "csv"},
        dependencies=[n1.node_id],
        stream_settings=_stream(),
    )
    ready_nodes = [n2]
    push_fn = MagicMock()
    update_status_fn = MagicMock()
    complete_fn = MagicMock(return_value=True)
    worker = QueueWorker(
        push_fn=push_fn,
        update_status_fn=update_status_fn,
        complete_fn=complete_fn,
    )
    # enqueue
    result = worker.enqueue_ready_nodes(ready_nodes)
    push_fn.assert_called_with(n2.node_id)
    update_status_fn.assert_called_with(n2.node_id, "READY")
    assert result == ready_nodes
    # complete
    assert worker.complete_node(n2.node_id, result="ok") is True
    update_status_fn.assert_called_with(n2.node_id, "COMPLETED")
    complete_fn.assert_called_with(n2.node_id, "ok")


class DummyStatusService:
    def __init__(self, status_map=None):
        # status_map[(pipeline_id, node_id)] -> status str
        self.map = status_map or {}

    # minimal API subset
    def get_node_status(self, pipeline_id, node_id):  # noqa: D401
        s = self.map.get((pipeline_id, node_id))
        return {"status": s} if s else None

    def update_node_status(self, pipeline_id, node_id, status, result=None):  # noqa: D401
        self.map[(pipeline_id, node_id)] = status
