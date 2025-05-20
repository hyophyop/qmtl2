# filepath: tests/unit/registry/services/test_event.py
import pytest
from qmtl.models.generated.qmtl_events_pb2 import NodeStatusEvent, PipelineStatusEvent, AlertEvent
from qmtl.dag_manager.registry.services.event import EventPublisher, EventSubscriber
import time

def test_publish_and_subscribe(monkeypatch):
    # Redis 모킹: 실제 Redis 연결 없이 publish/subscribe 동작만 검증
    class DummyRedis:
        def __init__(self):
            self.published = []
        def publish(self, channel, msg):
            self.published.append((channel, msg))
        def pubsub(self):
            class DummyPubSub:
                def subscribe(self, **kwargs):
                    self.subscribed = kwargs
                def run_in_thread(self, sleep_time=0.1):
                    pass
            return DummyPubSub()
    monkeypatch.setattr("redis.from_url", lambda url: DummyRedis())
    pub = EventPublisher()
    node_event = NodeStatusEvent(node_id="n1", status="RUNNING")
    pub.publish_node_status(node_event)
    assert any("event:node:n1" in ch for ch, _ in pub.redis.published)
    assert any("event:node_status" in ch for ch, _ in pub.redis.published)
    pipe_event = PipelineStatusEvent(pipeline_id="p1", status="COMPLETED")
    pub.publish_pipeline_status(pipe_event)
    assert any("event:pipeline:p1" in ch for ch, _ in pub.redis.published)
    alert_event = AlertEvent(target_id="n1", message="Alert!")
    pub.publish_alert(alert_event)
    assert any("event:alert:n1" in ch for ch, _ in pub.redis.published)
    assert any("event:alert" in ch for ch, _ in pub.redis.published)
    # 구독자 subscribe 동작 검증
    sub = EventSubscriber()
    sub.subscribe(["event:node:n1", "event:alert"], lambda msg: None)
    assert hasattr(sub.pubsub, "subscribed")
