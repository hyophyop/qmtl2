from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, model_validator


class StatusType(str, Enum):
    """파이프라인 및 노드 상태 타입"""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"



class NodeErrorDetail(BaseModel):
    """노드 장애/에러 상세 정보 모델"""
    code: Optional[str] = Field(default=None, description="에러 코드")
    message: Optional[str] = Field(default=None, description="에러 메시지")
    occurred_at: Optional[datetime] = Field(default=None, description="에러 발생 시각")
    recovered_at: Optional[datetime] = Field(default=None, description="복구 시각")
    recovery_count: int = Field(default=0, description="복구 시도 횟수")
    extra: Optional[Dict[str, Any]] = Field(default=None, description="추가 정보")
    model_config = {"extra": "forbid"}


class NodeStatus(BaseModel):
    """노드 상태 및 리소스/메타데이터/장애 정보 모델"""

    node_id: str
    status: StatusType = Field(default=StatusType.PENDING)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    resource: Optional[Dict[str, Any]] = None  # 예: {"cpu": 0.1, "mem": 128}
    meta: Optional[Dict[str, Any]] = None  # 예: {"last_active": "...", ...}
    error_detail: Optional[NodeErrorDetail] = Field(default=None, description="노드 장애/에러 상세 정보")
    last_recovered_at: Optional[datetime] = Field(default=None, description="마지막 복구 시각")
    recovery_count: int = Field(default=0, description="복구 시도 누적 횟수")

    model_config = {"extra": "forbid", "use_enum_values": True}



class PipelineStatus(BaseModel):
    """파이프라인 상태 및 장애/복구 정보 모델"""

    pipeline_id: str
    status: StatusType = Field(default=StatusType.PENDING)
    params: Dict[str, Any] = Field(default_factory=dict)
    start_time: datetime
    last_update: datetime
    end_time: Optional[datetime] = None
    progress: float = 0.0
    result: Optional[Dict[str, Any]] = None
    error_detail: Optional[NodeErrorDetail] = Field(default=None, description="파이프라인 장애/에러 상세 정보")
    last_recovered_at: Optional[datetime] = Field(default=None, description="마지막 복구 시각")
    recovery_count: int = Field(default=0, description="복구 시도 누적 횟수")

    model_config = {"extra": "forbid", "use_enum_values": True}

    @model_validator(mode="before")
    @classmethod
    def ensure_datetime_fields(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """날짜 필드가 문자열인 경우 datetime으로 변환"""
        for field in ["start_time", "last_update", "end_time", "last_recovered_at"]:
            if field in data and isinstance(data[field], str):
                try:
                    data[field] = datetime.fromisoformat(data[field])
                except (ValueError, TypeError):
                    pass
        return data


class ExecutionDetail(BaseModel):
    """실행 세부 정보 모델"""

    execution_id: str = Field(..., description="실행 ID")
    strategy_id: str = Field(..., description="전략 ID")
    version_id: str = Field(..., description="전략 버전 ID")
    status: str = Field(..., description="실행 상태")
    start_time: Optional[int] = Field(None, description="시작 시간(유닉스 타임스탬프)")
    end_time: Optional[int] = Field(None, description="종료 시간(유닉스 타임스탬프)")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="실행 파라미터")
    result: Optional[Dict[str, Any]] = Field(default=None, description="실행 결과")
    model_config = {"extra": "forbid"}
