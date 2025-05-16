from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AnalyzerDefinition(BaseModel):
    """분석기 제출용 모델"""

    name: str = Field(..., description="분석기 이름")
    description: Optional[str] = Field(None, description="설명")
    tags: List[str] = Field(default_factory=list, description="분석기 태그")
    source: str = Field(..., description="분석기 소스 코드 (base64 또는 plain)")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="추가 파라미터")


class AnalyzerMetadata(BaseModel):
    analyzer_id: str = Field(..., description="분석기 고유 ID")
    name: str = Field(...)
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    created_at: int = Field(..., description="생성 시각(UNIX timestamp)")
    status: str = Field(..., description="상태 (REGISTERED/ACTIVE/INACTIVE)")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AnalyzerActivateRequest(BaseModel):
    mode: str = Field(..., description="활성화 모드 (LIVE/DRYRUN 등)")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AnalyzerResult(BaseModel):
    analyzer_id: str = Field(...)
    result: Dict[str, Any] = Field(default_factory=dict)
    generated_at: int = Field(..., description="결과 생성 시각(UNIX timestamp)")
    status: str = Field(..., description="결과 상태 (SUCCESS/FAIL/IN_PROGRESS)")
    error: Optional[str] = None


model_config = {
    "extra": "forbid",
    "populate_by_name": True,
}
