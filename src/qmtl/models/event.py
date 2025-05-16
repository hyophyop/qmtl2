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
