"""
RedisClient 히스토리 저장/조회/삭제, TTL/max_items 관리 단위 테스트 (INTERVAL-3)
"""

import pytest

from src.qmtl.common.redis.redis_client import RedisClient, RedisSettings


@pytest.fixture(scope="module")
def redis_settings():
    return RedisSettings(host="localhost", port=6379, db=0, password=None)


@pytest.fixture(scope="module")
def redis_client(redis_session):
    # redis_session의 연결 정보를 사용하여 RedisClient 생성
    settings = RedisSettings(
        host=redis_session.connection_pool.connection_kwargs["host"],
        port=redis_session.connection_pool.connection_kwargs["port"],
        db=redis_session.connection_pool.connection_kwargs["db"],
        password=redis_session.connection_pool.connection_kwargs.get("password"),
    )
    client = RedisClient(settings=settings)
    # 싱글턴 내부 connection을 fixture의 redis_session으로 강제 주입
    client._connection = redis_session
    return client


def test_save_and_get_history(redis_client, redis_clean):
    node_id, interval = "n1", "1h"
    # 5개 저장, max_items=3
    for i in range(5):
        redis_client.save_history(node_id, interval, f"v{i}", max_items=3)
    # 최신 3개만 남아야 함
    history = redis_client.get_history(node_id, interval, count=10)
    # bytes → str 변환
    history = [v.decode() if isinstance(v, bytes) else v for v in history]
    assert history == ["v4", "v3", "v2"]


def test_history_ttl(redis_client, redis_clean):
    node_id, interval = "n2", "1d"
    redis_client.save_history(node_id, interval, "foo", max_items=5, ttl=2)
    key = f"node:{node_id}:history:{interval}"
    ttl = redis_client.conn.ttl(key)
    assert 0 < ttl <= 2


def test_delete_history(redis_client, redis_clean):
    node_id, interval = "n3", "1h"
    redis_client.save_history(node_id, interval, "bar", max_items=5)
    deleted = redis_client.delete_history(node_id, interval)
    assert deleted == 1
    assert redis_client.get_history(node_id, interval) == []
