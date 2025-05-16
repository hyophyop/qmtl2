# filepath: src/qmtl/orchestrator/services/event_client.py
"""
Orchestrator 실시간 상태 구독/알림 연동 클라이언트 (MULTI-7)
- Registry의 Redis Pub/Sub 이벤트 구독
- 대시보드/알림 시스템 연동 Hook 예시
"""
import json
import redis
from qmtl.models.event import NodeStatusEvent, PipelineStatusEvent, AlertEvent, EventType

class EventClient:
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis = redis.from_url(redis_url)
        self.pubsub = self.redis.pubsub()

    def subscribe_node_status(self, node_id: str, callback):
        channel = f"event:node:{node_id}"
        self.pubsub.subscribe(**{channel: callback})
        self.pubsub.run_in_thread(sleep_time=0.1)

    def subscribe_pipeline_status(self, pipeline_id: str, callback):
        channel = f"event:pipeline:{pipeline_id}"
        self.pubsub.subscribe(**{channel: callback})
        self.pubsub.run_in_thread(sleep_time=0.1)

    def subscribe_alerts(self, target_id: str, callback):
        channel = f"event:alert:{target_id}"
        self.pubsub.subscribe(**{channel: callback})
        self.pubsub.run_in_thread(sleep_time=0.1)

# 대시보드/알림 시스템 연동 예시:
# def dashboard_callback(msg):
#     event = json.loads(msg['data'])
#     ... # 대시보드/알림 처리
# EventClient().subscribe_node_status(node_id, dashboard_callback)
