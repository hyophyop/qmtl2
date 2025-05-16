from typing import Any, Dict, List, Literal, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field


class IntervalEnum(str, Enum):
    MINUTE = "1m"
    HOUR = "1h"
    DAY = "1d"
    # 필요시 추가


class IntervalSettings(BaseModel):
    """인터벌 데이터 관리 설정 (interval: Enum, period: int)"""

    interval: IntervalEnum = Field(..., description="데이터 수집 주기 (Enum)")
    period: int = Field(..., description="보관 기간(정수, interval 단위로 해석)")
    max_history: int = Field(default=100, description="보관할 최대 히스토리 항목 수")
    model_config = {"extra": "forbid"}

    @classmethod
    def __get_validators__(cls):
        yield cls.validate_types

    @classmethod
    def validate_types(cls, values):
        # interval: str -> Enum 변환
        interval = values.get("interval")
        if isinstance(interval, str):
            try:
                values["interval"] = IntervalEnum(interval)
            except ValueError:
                raise ValueError(f"interval은 IntervalEnum 값이어야 합니다: {list(IntervalEnum)}")
        elif not isinstance(interval, IntervalEnum):
            raise ValueError("interval은 IntervalEnum 타입이어야 합니다.")
        # period: str -> int 변환 (예전 스타일 호환)
        period = values.get("period")
        if isinstance(period, str):
            try:
                values["period"] = int(period)
            except Exception:
                raise ValueError("period는 int(정수)여야 하며, 문자열이면 변환 가능해야 합니다.")
        elif not isinstance(period, int):
            raise ValueError("period는 int(정수)여야 합니다.")
        return values


class NodeStreamSettings(BaseModel):
    """노드 스트림 설정 (인터벌별 설정 관리)"""

    intervals: Dict[IntervalEnum, Union[IntervalSettings, Dict[str, Any]]] = Field(
        ..., min_items=1, description="최소 1개 이상의 interval 필요"
    )
    model_config = {"extra": "forbid"}

    def __init__(self, **data):
        super().__init__(**data)
        # dict 형태의 interval 설정을 IntervalSettings 객체로 변환, 키도 Enum으로 변환
        new_intervals = {}
        for interval, settings in self.intervals.items():
            enum_key = IntervalEnum(interval) if isinstance(interval, str) else interval
            if isinstance(settings, dict):
                new_intervals[enum_key] = IntervalSettings(**settings)
            else:
                new_intervals[enum_key] = settings
        self.intervals = new_intervals
        # interval 필수 검증
        if not self.intervals or len(self.intervals) == 0:
            raise ValueError("NodeStreamSettings에는 최소 1개 이상의 interval이 필요합니다.")
        for k, v in self.intervals.items():
            interval = getattr(v, "interval", None) or (
                v.get("interval") if isinstance(v, dict) else None
            )
            if not interval:
                raise ValueError(
                    f"NodeStreamSettings의 intervals[{k}]에 interval이 누락되었습니다."
                )


class NodeDefinition(BaseModel):
    """
    SDK용 노드 정의 모델 (직렬화/역직렬화용)
    """

    name: str
    tags: Optional[List[str]] = Field(default_factory=list)
    params: Optional[Dict[str, Any]] = None
    upstreams: Optional[List[str]] = Field(default_factory=list)
    key_params: Optional[List[str]] = Field(default_factory=list)
    stream_settings: Optional[Dict[str, NodeStreamSettings]] = Field(default_factory=dict)
    model_config = {"extra": "forbid"}

    @classmethod
    def from_definition(cls, data: Dict[str, Any]) -> "NodeDefinition":
        """
        dict → NodeDefinition 역직렬화
        직렬화 dict에서 node_id 등 정의에 없는 필드는 제거
        """
        allowed = set(cls.model_fields.keys())
        filtered = {k: v for k, v in data.items() if k in allowed}
        # stream_settings: dict[str, dict] → dict[str, NodeStreamSettings]
        stream_settings = filtered.get("stream_settings")
        if stream_settings and isinstance(stream_settings, dict):
            # stream_settings는 dict[str, dict] 구조일 수 있음
            def _to_nodestreamsettings(val):
                if isinstance(val, NodeStreamSettings):
                    return val
                elif isinstance(val, dict):
                    # 내부 value가 dict면 IntervalSettings로 변환
                    intervals = {}
                    for k, v in val.get("intervals", val).items():
                        if isinstance(v, IntervalSettings):
                            intervals[k] = v
                        elif isinstance(v, dict):
                            intervals[k] = IntervalSettings(**v)
                    return NodeStreamSettings(intervals=intervals)
                else:
                    raise ValueError(
                        "stream_settings value는 NodeStreamSettings 또는 dict여야 합니다."
                    )

            filtered["stream_settings"] = {
                k: _to_nodestreamsettings(v) for k, v in stream_settings.items()
            }
        return cls(**filtered)


class QueryNodeDefinition(NodeDefinition):
    """쿼리 노드 정의 모델"""

    query_tags: List[str] = Field(..., description="매칭할 노드의 태그 목록")
    interval: Optional[str] = Field(default=None, description="데이터 인터벌 필터")
    period: Optional[int] = Field(default=None, description="데이터 피리어드 필터")
    model_config = {"extra": "forbid"}

    @classmethod
    def from_definition(cls, data: Dict[str, Any]) -> "QueryNodeDefinition":
        allowed = set(cls.model_fields.keys())
        filtered = {k: v for k, v in data.items() if k in allowed}
        # period가 str로 들어오면 int로 변환 시도
        if "period" in filtered and isinstance(filtered["period"], str):
            try:
                filtered["period"] = int(filtered["period"].replace("d", ""))
            except Exception:
                pass
        return super().from_definition(filtered)


class PipelineDefinition(BaseModel):
    """
    SDK용 파이프라인 정의 모델 (직렬화/역직렬화용)
    """

    name: str
    nodes: List[NodeDefinition]
    query_nodes: Optional[List[QueryNodeDefinition]] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    model_config = {"extra": "forbid"}

    @classmethod
    def from_definition(cls, data: Dict[str, Any]) -> "PipelineDefinition":
        allowed = set(cls.model_fields.keys())
        filtered = {k: v for k, v in data.items() if k in allowed}
        nodes = [NodeDefinition.from_definition(n) for n in filtered.get("nodes", [])]
        query_nodes = (
            [QueryNodeDefinition.from_definition(q) for q in filtered.get("query_nodes", [])]
            if filtered.get("query_nodes")
            else []
        )
        metadata = filtered.get("metadata", {})
        return cls(name=filtered["name"], nodes=nodes, query_nodes=query_nodes, metadata=metadata)


class AnalyzerDefinition(PipelineDefinition):
    """분석기 정의 모델"""

    analyzer_type: str = Field(default="custom")
    tags: List[str] = Field(default_factory=lambda: ["ANALYZER"])
    model_config = {"extra": "forbid"}

    @classmethod
    def from_definition(cls, data: Dict[str, Any]) -> "AnalyzerDefinition":
        allowed = set(cls.model_fields.keys())
        filtered = {k: v for k, v in data.items() if k in allowed}
        return super().from_definition(filtered)


class QueryNodeResultSelector(BaseModel):
    """QueryNode 결과 가공/선택용 Selector 모델 (체이닝 지원)"""

    mode: Literal["list", "batch", "random", "filter"] = "list"
    batch_size: Optional[int] = None
    sample_size: Optional[int] = None
    filter_meta: Optional[Dict[str, Any]] = None
    model_config = {"extra": "forbid"}
