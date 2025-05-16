# filepath: tests/unit/orchestrator/services/test_event_client.py
import pytest
from qmtl.orchestrator.services.event_client import EventClient

def test_event_client_subscribe(monkeypatch):
    class DummyRedis:
        def pubsub(self):
            class DummyPubSub:
                def subscribe(self, **kwargs):
                    self.subscribed = kwargs
                def run_in_thread(self, sleep_time=0.1):
                    pass
            return DummyPubSub()
    monkeypatch.setattr("redis.from_url", lambda url: DummyRedis())
    client = EventClient()
    client.subscribe_node_status("n1", lambda msg: None)
    client.subscribe_pipeline_status("p1", lambda msg: None)
    client.subscribe_alerts("n1", lambda msg: None)
    # 내부 pubsub 객체가 subscribe 호출됨을 확인
    assert hasattr(client.pubsub, "subscribed")
