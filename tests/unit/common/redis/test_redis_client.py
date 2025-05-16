"""
RedisClient 단위 테스트 (INTERVAL-3)
- 연결 성공/실패
- ping
- set/get
"""

import pytest

from src.qmtl.common.redis.redis_client import RedisClient, RedisSettings


@pytest.fixture(scope="module")
def redis_settings():
    return RedisSettings(host="localhost", port=6379, db=0, password=None)


@pytest.fixture(scope="module")
def redis_client(redis_settings, redis_session):
    # redis_session fixture로 docker-compose 기반 Redis 컨테이너 보장
    return RedisClient(settings=redis_settings)


def test_redis_connection_success(redis_client):
    assert redis_client.ping() is True


def test_redis_set_get(redis_client, redis_clean):
    key, value = "test_key", "test_value"
    redis_client.set(key, value)
    assert redis_client.get(key) == value


def test_redis_connection_fail():
    # RedisClient 싱글턴 리셋 (테스트 목적)
    from src.qmtl.common.redis.redis_client import RedisClient

    RedisClient._instance = None
    RedisClient._connection = None
    RedisClient._settings = None
    bad_settings = RedisSettings(host="localhost", port=6399, db=0)
    with pytest.raises(Exception):
        RedisClient(settings=bad_settings).ping()
