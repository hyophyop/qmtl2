"""
Unit tests for src/qmtl/sdk/execution/state_manager.py
커버리지 80% 달성을 위한 실제 단위/엣지케이스 테스트
"""
import pytest
from unittest.mock import MagicMock, patch
from src.qmtl.sdk.execution.state_manager import StateManager

@pytest.fixture
def mock_redis():
    with patch("src.qmtl.sdk.execution.state_manager.redis") as mock_redis_mod:
        mock_redis_mod.from_url.return_value = MagicMock()
        mock_redis_mod.ConnectionError = Exception
        yield mock_redis_mod

@patch("src.qmtl.sdk.execution.state_manager.redis")
def test_state_manager_init(mock_redis_mod):
    sm = StateManager(redis_uri="redis://test")
    assert sm.redis_uri == "redis://test"
    assert sm._redis is None

@patch("src.qmtl.sdk.execution.state_manager.redis")
def test_set_get_delete_exists_keys_clear(mock_redis_mod):
    mock_redis = MagicMock()
    mock_redis_mod.from_url.return_value = mock_redis
    sm = StateManager()
    sm._redis = mock_redis
    # set/get
    mock_redis.set.return_value = True
    mock_redis.get.return_value = b'{"a":1}'
    assert sm.set("k", {"a": 1})
    assert sm.get("k") == {"a": 1}
    # delete
    mock_redis.delete.return_value = 1
    assert sm.delete("k")
    # exists
    mock_redis.exists.return_value = 1
    assert sm.exists("k")
    # keys: keys 메서드 patch
    mock_redis.keys.return_value = [b"k1", b"k2"]
    keys = sm.keys("*")
    assert keys == ["k1", "k2"]
    # clear: scan_iter generator 새로 할당
    mock_redis.scan_iter.side_effect = lambda pattern=None: (k for k in [b"k1", b"k2"])
    mock_redis.delete.return_value = 2  # 여러 키 삭제 시 반환값은 삭제된 개수
    assert sm.clear() == 2

@patch("src.qmtl.sdk.execution.state_manager.redis")
def test_save_and_get_history(mock_redis_mod):
    mock_redis = MagicMock()
    mock_redis_mod.from_url.return_value = mock_redis
    sm = StateManager()
    sm._redis = mock_redis
    # save_history
    mock_redis.pipeline.return_value = MagicMock()
    mock_redis.llen.return_value = 1
    sm.set = MagicMock()
    assert sm.save_history("n", "1d", {"v": 1})
    # get_history (no filter)
    mock_redis.lrange.return_value = [b'{"timestamp":1,"value":1}']
    result = sm.get_history("n", "1d", 1)
    assert result[0]["value"] == 1
    # get_interval_data
    sm.get_history = MagicMock(return_value=[{"value": 2}])
    assert sm.get_interval_data("n", "1d") == [2]

@patch("src.qmtl.sdk.execution.state_manager.redis")
def test_update_ttl_and_metadata(mock_redis_mod):
    mock_redis = MagicMock()
    mock_redis_mod.from_url.return_value = mock_redis
    sm = StateManager()
    sm._redis = mock_redis
    mock_redis.expire.return_value = True
    sm.get = MagicMock(return_value={})
    sm.set = MagicMock()
    assert sm.update_ttl("n", "1d", 10)
    # get_history_metadata
    mock_redis.llen.return_value = 3
    sm.get = MagicMock(return_value={"foo": "bar"})
    meta = sm.get_history_metadata("n", "1d")
    assert meta["foo"] == "bar"
    assert meta["actual_count"] == 3

@patch("src.qmtl.sdk.execution.state_manager.redis")
def test_clean_expired_data_and_clear_all(mock_redis_mod):
    mock_redis = MagicMock()
    mock_redis_mod.from_url.return_value = mock_redis
    sm = StateManager()
    sm._redis = mock_redis
    # clean_expired_data (모두 -2로 설정해 2개 삭제)
    mock_redis.scan_iter.return_value = iter([b"k1", b"k2"])
    mock_redis.ttl.side_effect = [-2, -2]
    mock_redis.delete.return_value = 1
    assert sm.clean_expired_data() == 2
    # clear_all
    mock_redis.scan_iter.return_value = iter([b"k1", b"k2"])
    mock_redis.delete.return_value = 1
    assert sm.clear_all() == 2

@patch("src.qmtl.sdk.execution.state_manager.redis")
def test_set_get_exception_handling(mock_redis_mod):
    mock_redis = MagicMock()
    mock_redis_mod.from_url.return_value = mock_redis
    sm = StateManager()
    sm._redis = mock_redis
    # set 예외
    mock_redis.set.side_effect = Exception("fail")
    assert not sm.set("k", {"a": 1})
    # get 예외
    mock_redis.get.side_effect = Exception("fail")
    assert sm.get("k") is None
    # delete 예외
    mock_redis.delete.side_effect = Exception("fail")
    assert not sm.delete("k")
    # exists 예외
    mock_redis.exists.side_effect = Exception("fail")
    assert not sm.exists("k")
