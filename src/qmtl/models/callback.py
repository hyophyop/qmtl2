from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator

class NodeCallbackType(str, Enum):
    ON_EXECUTE = "on_execute"
    ON_STOP = "on_stop"
    ON_REFCOUNT_ZERO = "on_refcount_zero"

class NodeCallbackRequest(BaseModel):
    node_id: str = Field(..., description="정책 Node ID(32자리 해시)")
    callback_type: NodeCallbackType = Field(..., description="콜백 트리거 타입")
    url: str = Field(..., description="콜백을 호출할 엔드포인트 URL")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="콜백에 전달할 추가 메타데이터")

    model_config = {"extra": "forbid"}

class NodeCallbackResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    callback_id: Optional[str] = None

    model_config = {"extra": "forbid"}

class NodeCallbackEvent(BaseModel):
    node_id: str
    callback_type: NodeCallbackType
    event_payload: Optional[Dict[str, Any]] = None
    triggered_at: Optional[str] = None  # ISO8601 timestamp

    model_config = {"extra": "forbid"}
