# tests/unit/core/test_event_client.py
import pytest
from unittest.mock import MagicMock, patch
from qmtl.dag_manager.event_client import EventClient

@pytest.fixture
def mock_redis_pubsub():
    class DummyPubSub:
        def subscribe(self, **kwargs):
            self.subscribed = True
        def run_in_thread(self, sleep_time=0.1):
            self.running = True
    return DummyPubSub()

@pytest.fixture
def mock_redis(monkeypatch, mock_redis_pubsub):
    class DummyRedis:
        def pubsub(self):
            return mock_redis_pubsub
    monkeypatch.setattr("redis.from_url", lambda *a, **k: DummyRedis())
    return DummyRedis()

def test_event_client_subscribe_node_status(mock_redis):
    client = EventClient()
    callback = MagicMock()
    client.subscribe_node_status("n1", callback)
    # smoke: no exception, pubsub.subscribe called
    assert hasattr(client.pubsub, "subscribed")

@patch("qmtl.dag_manager.event_client.redis")
@patch("qmtl.dag_manager.event_client.qmtl_events_pb2")
def test_event_client_subscribe_node_status(mock_pb2, mock_redis):
    # Redis와 protobuf 메시지 mocking
    pubsub = MagicMock()
    mock_redis.from_url.return_value.pubsub.return_value = pubsub
    client = EventClient("redis://test")
    callback = MagicMock()
    # 구독 메서드 호출
    client.subscribe_node_status("node1", callback)
    # pubsub.subscribe가 올바르게 호출되었는지 확인
    assert pubsub.subscribe.called
    # 콜백 함수가 정상적으로 등록되는지 확인
    args, kwargs = pubsub.subscribe.call_args
    assert "event:node:node1" in kwargs
    # 메시지 수신 시 protobuf 파싱 및 콜백 호출 확인
    proto_cb = kwargs["event:node:node1"]
    msg = {"type": "message", "data": b"dummy"}
    event_obj = MagicMock()
    mock_pb2.NodeStatusEvent.return_value = event_obj
    proto_cb(msg)
    event_obj.ParseFromString.assert_called_once_with(b"dummy")
    callback.assert_called_once_with(event_obj)

def test_event_client_subscribe_pipeline_status(mock_redis):
    client = EventClient()
    callback = MagicMock()
    client.subscribe_pipeline_status("p1", callback)
    assert hasattr(client.pubsub, "subscribed")

def test_event_client_subscribe_alerts(mock_redis):
    client = EventClient()
    callback = MagicMock()
    client.subscribe_alerts("target1", callback)
    assert hasattr(client.pubsub, "subscribed")
