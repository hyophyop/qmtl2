# pytest: test
"""
Unit tests for StateManager in qmtl.sdk.execution.state_manager
(redis 모듈은 mock 처리)
"""
import pytest
from unittest.mock import MagicMock, patch
from qmtl.sdk.execution.state_manager import StateManager

@pytest.fixture
def mock_redis():
    with patch("qmtl.sdk.execution.state_manager.redis") as mock_redis_mod:
        mock_redis_mod.from_url.return_value = MagicMock()
        mock_redis_mod.ConnectionError = Exception
        yield mock_redis_mod

def test_init_and_redis_property(mock_redis):
    sm = StateManager(redis_uri="redis://dummy")
    r = sm.redis
    assert mock_redis.from_url.called
    assert r is sm._redis

def test_set_and_get(mock_redis):
    sm = StateManager(redis_uri="redis://dummy")
    sm.redis.set.return_value = True
    sm.redis.get.return_value = b'"val"'
    assert sm.set("k", "val") is True
    assert sm.get("k") == "val"

def test_delete_and_exists(mock_redis):
    sm = StateManager(redis_uri="redis://dummy")
    sm.redis.delete.return_value = 1
    sm.redis.exists.return_value = True
    assert sm.delete("k") is True
    assert sm.exists("k") is True

def test_keys_and_clear(mock_redis):
    sm = StateManager(redis_uri="redis://dummy")
    sm.redis.keys.return_value = [b"a", b"b"]
    sm.redis.delete.return_value = 2
    assert sm.keys("*") == ["a", "b"]
    assert sm.clear() == 2

def test_set_importerror():
    with patch("qmtl.sdk.execution.state_manager.REDIS_AVAILABLE", False):
        with pytest.raises(ImportError):
            StateManager()
