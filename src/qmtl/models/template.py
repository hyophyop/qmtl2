"""
템플릿/권한 관리용 Pydantic 모델 (MULTI-8)
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class TemplateType(str):
    NODE = "NODE"
    STRATEGY = "STRATEGY"
    DAG = "DAG"

class TemplateMetadata(BaseModel):
    name: str = Field(..., description="템플릿 이름")
    description: Optional[str] = Field(None, description="설명")
    owner: str = Field(..., description="소유자(사용자 ID)")
    is_public: bool = Field(default=False, description="공개 여부")
    tags: List[str] = Field(default_factory=list, description="태그")
    created_at: int = Field(..., description="생성 시각(UNIX timestamp)")
    updated_at: Optional[int] = Field(None, description="수정 시각(UNIX timestamp)")
    extra: Dict[str, Any] = Field(default_factory=dict, description="추가 메타데이터")
    model_config = {"extra": "forbid"}

from typing import Literal

class NodeTemplate(BaseModel):
    template_id: str = Field(..., description="템플릿 ID(해시)")
    type: Literal["NODE"] = Field("NODE", description="템플릿 타입: NODE")
    metadata: TemplateMetadata
    node: Dict[str, Any] = Field(..., description="DataNode 직렬화 데이터")
    model_config = {"extra": "forbid"}

class StrategyTemplate(BaseModel):
    template_id: str = Field(..., description="템플릿 ID(해시)")
    type: Literal["STRATEGY"] = Field("STRATEGY", description="템플릿 타입: STRATEGY")
    metadata: TemplateMetadata
    strategy: Dict[str, Any] = Field(..., description="Strategy 직렬화 데이터")
    model_config = {"extra": "forbid"}

class DAGTemplate(BaseModel):
    template_id: str = Field(..., description="템플릿 ID(해시)")
    type: Literal["DAG"] = Field("DAG", description="템플릿 타입: DAG")
    metadata: TemplateMetadata
    dag: Dict[str, Any] = Field(..., description="DAG 직렬화 데이터(nodes, edges 등)")
    model_config = {"extra": "forbid"}

from enum import Enum

class PermissionLevel(str, Enum):
    OWNER = "OWNER"
    EDITOR = "EDITOR"
    VIEWER = "VIEWER"

class TemplatePermission(BaseModel):
    template_id: str = Field(...)
    user_id: str = Field(...)
    level: PermissionLevel = Field(...)
    granted_at: int = Field(...)
    model_config = {"extra": "forbid"}
