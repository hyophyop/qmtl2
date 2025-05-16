from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class StrategyMetadata(BaseModel):
    strategy_name: Optional[str] = None
    submitted_at: Optional[int] = None
    description: Optional[str] = None
    author: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    version: Optional[str] = None
    source: Optional[str] = None
    extra_data: Dict[str, Any] = Field(default_factory=dict)
    model_config = {"extra": "forbid"}


class SharedStrategyModel(BaseModel):
    strategy_name: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    model_config = {"extra": "forbid"}


class StrategyVersion(BaseModel):
    strategy_code: str  # 실제 파이썬 전략 코드(소스)
    created_at: int
    metadata: Optional[StrategyMetadata] = None
    model_config = {"extra": "forbid"}


class NodeSnapshot(BaseModel):
    """스냅샷 시점의 노드 정보(정책 Node ID 기준)"""

    node_id: str = Field(..., pattern=r"^[a-f0-9]{32}$", description="정책 Node ID (32자리 해시)")
    data: Dict[str, Any] = Field(..., description="DataNode 또는 DAGNode 직렬화 데이터")
    # 필요시 추가: params, stream_settings, tags 등
    model_config = {"extra": "forbid"}


class StrategySnapshot(BaseModel):
    """파이프라인별 DAG 스냅샷(버전별, 롤백/비교/재실행용)"""

    pipeline_id: str = Field(..., description="정책 Pipeline ID (32자리 해시)")
    created_at: int = Field(..., description="스냅샷 생성 시각(UNIX timestamp)")
    nodes: List[NodeSnapshot] = Field(..., description="스냅샷 시점의 노드 목록")
    edges: List[Dict[str, str]] = Field(..., description="DAG 엣지 정보(source/target Node ID)")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="추가 메타데이터")
    model_config = {"extra": "forbid"}
