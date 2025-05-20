# filepath: src/qmtl/registry/services/event.py
"""
Registry 상태 변화 이벤트 발행/구독 서비스 (MULTI-7)
- Redis Pub/Sub 기반 (확장 가능)
- NodeStatusEvent, PipelineStatusEvent, AlertEvent 발행/구독
"""
from typing import Any, Dict, Optional
import json
import redis
from datetime import datetime
from qmtl.models.generated import qmtl_events_pb2

class EventPublisher:
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis = redis.from_url(redis_url)

    def publish_node_status(self, event: qmtl_events_pb2.NodeStatusEvent):
        self.redis.publish(f"event:node:{event.node_id}", event.SerializeToString())
        self.redis.publish("event:node_status", event.SerializeToString())

    def publish_pipeline_status(self, event: qmtl_events_pb2.PipelineStatusEvent):
        self.redis.publish(f"event:pipeline:{event.pipeline_id}", event.SerializeToString())
        self.redis.publish("event:pipeline_status", event.SerializeToString())

    def publish_alert(self, event: qmtl_events_pb2.AlertEvent):
        self.redis.publish(f"event:alert:{event.target_id}", event.SerializeToString())
        self.redis.publish("event:alert", event.SerializeToString())

class EventSubscriber:
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis = redis.from_url(redis_url)
        self.pubsub = self.redis.pubsub()

    def subscribe(self, channels, callback):
        if isinstance(channels, str):
            channels = [channels]
        self.pubsub.subscribe(**{ch: callback for ch in channels})
        self.pubsub.run_in_thread(sleep_time=0.1)

# 사용 예시: EventPublisher().publish_node_status(NodeStatusEvent(...))
