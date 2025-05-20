# filepath: src/qmtl/models/event.py
"""
실시간 상태/이벤트/알림 모델 정의 (MULTI-7)
- NodeStatusEvent, PipelineStatusEvent, AlertEvent 등
- Pydantic v2 스타일, Node ID/Pipeline ID 기준
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

# [DEPRECATED] 이 파일의 Pydantic 모델은 protobuf(qmtl_events.proto) 기반으로 대체됩니다.
# 서비스 코드에서는 반드시 generated/qmtl_events_pb2.py를 import하여 사용하세요.
# 예시:
#   from qmtl.models.generated import qmtl_events_pb2
#   event = qmtl_events_pb2.NodeStatusEvent(...)

class EventType(str, Enum):
    NODE_STATUS = "NODE_STATUS"
    PIPELINE_STATUS = "PIPELINE_STATUS"
    ALERT = "ALERT"

class NodeStatusEvent(BaseModel):
    event_type: EventType = Field(default=EventType.NODE_STATUS)
    node_id: str
    status: str  # StatusType 값 (ex: RUNNING, COMPLETED)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    meta: Optional[Dict[str, Any]] = None

class PipelineStatusEvent(BaseModel):
    event_type: EventType = Field(default=EventType.PIPELINE_STATUS)
    pipeline_id: str
    status: str  # StatusType 값
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    meta: Optional[Dict[str, Any]] = None

class AlertEvent(BaseModel):
    event_type: EventType = Field(default=EventType.ALERT)
    target_id: str  # node_id or pipeline_id
    level: str = Field(default="INFO")  # INFO/WARN/ERROR
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    meta: Optional[Dict[str, Any]] = None

# (확장 가능: 이벤트 배치, 구독/필터 모델 등)
