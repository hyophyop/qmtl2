from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, model_validator
from qmtl.sdk.models import IntervalEnum


class NodeType(str, Enum):
    RAW = "RAW"
    CANDLE = "CANDLE"
    FEATURE = "FEATURE"
    ORDERBOOK = "ORDERBOOK"
    RISK = "RISK"
    SIGNAL = "SIGNAL"
    ML_PRED = "ML_PRED"
    ANALYZER = "ANALYZER"
    CORRELATION = "CORRELATION"
    VOLATILITY = "VOLATILITY"
    TREND = "TREND"
    ANOMALY = "ANOMALY"


# NodeTag: NodeType와 동일 값, NodeType은 하위 호환성용
class NodeTag(str, Enum):
    RAW = "RAW"
    CANDLE = "CANDLE"
    FEATURE = "FEATURE"
    ORDERBOOK = "ORDERBOOK"
    RISK = "RISK"
    SIGNAL = "SIGNAL"
    ML_PRED = "ML_PRED"
    ANALYZER = "ANALYZER"
    CORRELATION = "CORRELATION"
    VOLATILITY = "VOLATILITY"
    TREND = "TREND"
    ANOMALY = "ANOMALY"


class NodeTags(BaseModel):
    predefined: Optional[List[NodeTag]] = Field(default_factory=list)
    custom: Optional[List[str]] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class IntervalSettings(BaseModel):
    """인터벌 데이터 관리 설정 (interval: Enum, period: int)"""

    interval: IntervalEnum = Field(..., description="데이터 수집 주기 (Enum)")
    period: int = Field(..., description="보관 기간(정수, interval 단위로 해석)")
    max_history: Optional[int] = Field(default=None)
    model_config = {"extra": "forbid"}

    @model_validator(mode="before")
    @classmethod
    def check_interval(cls, values):
        interval = values.get("interval")
        if isinstance(interval, str):
            try:
                values["interval"] = IntervalEnum(interval)
            except ValueError:
                raise ValueError(f"interval은 IntervalEnum 값이어야 합니다: {list(IntervalEnum)}")
        elif not isinstance(interval, IntervalEnum):
            raise ValueError("interval은 IntervalEnum 타입이어야 합니다.")
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
    intervals: Dict[IntervalEnum, IntervalSettings] = Field(
        ..., min_items=1, description="최소 1개 이상의 interval 필요"
    )
    model_config = {"extra": "forbid"}

    @model_validator(mode="before")
    @classmethod
    def check_intervals(cls, values):
        intervals = None
        if "intervals" in values:
            if isinstance(values["intervals"], dict):
                intervals = values["intervals"]
                # str 키를 Enum으로 변환
                new_intervals = {}
                for k, v in intervals.items():
                    enum_key = IntervalEnum(k) if isinstance(k, str) else k
                    new_intervals[enum_key] = v
                values["intervals"] = new_intervals
                intervals = new_intervals
            elif hasattr(values["intervals"], "items"):
                intervals = dict(values["intervals"].items())
            else:
                intervals = None
        if not intervals or not isinstance(intervals, dict) or len(intervals) == 0:
            raise ValueError("NodeStreamSettings에는 최소 1개 이상의 interval이 필요합니다.")
        for k, v in intervals.items():
            if not hasattr(v, "interval") and (not isinstance(v, dict) or "interval" not in v):
                raise ValueError(f"intervals[{k}]에 interval 필드가 누락되었습니다.")
        return values


class DataNode(BaseModel):
    node_id: str = Field(..., pattern=r"^[a-f0-9]{32}$")
    type: Optional[NodeType] = None  # 하위 호환성 유지
    data_format: Dict[str, Any] = Field(...)
    params: Optional[Dict[str, Any]] = None
    dependencies: List[str] = Field(default_factory=list)
    ttl: Optional[int] = None
    tags: Optional[NodeTags] = Field(default_factory=NodeTags)
    # 신규: stream_settings 사용 권장
    stream_settings: Optional[NodeStreamSettings] = None
    # 구버전 호환: interval_settings (내부적으로 stream_settings로 변환)
    interval_settings: Optional[IntervalSettings] = None
    model_config = {"extra": "forbid"}

    @model_validator(mode="before")
    @classmethod
    def migrate_interval_settings(cls, values):
        # interval_settings → stream_settings 변환 (점진적 마이그레이션)
        interval_settings = values.get("interval_settings")
        stream_settings = values.get("stream_settings")
        if interval_settings and not stream_settings:
            # 단일 interval_settings → intervals[interval]로 변환
            if isinstance(interval_settings, dict):
                interval_obj = IntervalSettings(**interval_settings)
            elif isinstance(interval_settings, IntervalSettings):
                interval_obj = interval_settings
            else:
                raise ValueError("interval_settings must be dict or IntervalSettings")
            # 기본 interval 키는 interval 값(str)
            interval_key = interval_obj.interval if hasattr(interval_obj, "interval") else "default"
            values["stream_settings"] = NodeStreamSettings(intervals={interval_key: interval_obj})
        return values

    @model_validator(mode="before")
    @classmethod
    def check_node_id(cls, values):
        node_id = values.get("node_id")
        if node_id and not isinstance(node_id, str):
            raise ValueError("node_id must be a string")
        return values

    @model_validator(mode="before")
    @classmethod
    def check_interval_required(cls, values):
        stream_settings = values.get("stream_settings")
        interval_settings = values.get("interval_settings")
        # stream_settings 우선
        if stream_settings:
            if hasattr(stream_settings, "intervals"):
                intervals = stream_settings.intervals
            elif isinstance(stream_settings, dict):
                intervals = stream_settings.get("intervals")
            else:
                intervals = None
            if not intervals or len(intervals) == 0:
                raise ValueError(
                    "DataNode의 stream_settings에는 최소 1개 이상의 interval이 필요합니다."
                )
            for k, v in intervals.items():
                interval = getattr(v, "interval", None) or (
                    v.get("interval") if isinstance(v, dict) else None
                )
                if not interval:
                    raise ValueError(
                        f"DataNode의 stream_settings[{k}]에 interval이 누락되었습니다."
                    )
        elif interval_settings:
            interval = getattr(interval_settings, "interval", None) or (
                interval_settings.get("interval") if isinstance(interval_settings, dict) else None
            )
            if not interval:
                raise ValueError("DataNode의 interval_settings에 interval이 누락되었습니다.")
        else:
            raise ValueError(
                "DataNode에는 stream_settings 또는 interval_settings가 반드시 필요하며, interval이 명시되어야 합니다."
            )
        return values

    @property
    def primary_tag(self) -> Optional[str]:
        """대표 태그(우선순위: predefined[0] > type > custom[0])"""
        if self.tags and self.tags.predefined:
            return self.tags.predefined[0].value
        if self.type:
            return self.type.value
        if self.tags and self.tags.custom:
            return self.tags.custom[0]
        return None


class TopoSortResult(BaseModel):
    """위상 정렬 결과를 담는 Pydantic 모델"""

    order: List[str] = Field(default_factory=list, description="위상 정렬된 노드 ID 리스트")
    node_map: Dict[str, DataNode] = Field(
        default_factory=dict, description="노드 ID를 키로, DataNode 객체를 값으로 하는 사전"
    )
    model_config = {"extra": "forbid"}


class DAGNodeDependency(BaseModel):
    """DAG 노드 의존성 정보 모델"""

    id: str = Field(..., description="의존하는 노드 ID")
    type: Union[str, NodeType] = Field(..., description="의존하는 노드 타입")
    model_config = {"extra": "forbid"}


class DAGNode(BaseModel):
    """DAG 노드 정보 모델"""

    id: str = Field(..., description="노드 ID")
    type: Union[str, NodeType] = Field(..., description="노드 타입")
    dependencies: List[DAGNodeDependency] = Field(
        default_factory=list, description="노드 의존성 목록"
    )
    params: Optional[Dict[str, Any]] = Field(default=None, description="노드 파라미터")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="노드 메타데이터")
    model_config = {"extra": "forbid"}


class DAGEdge(BaseModel):
    """DAG 엣지 정보 모델"""

    source: str = Field(..., description="소스 노드 ID")
    target: str = Field(..., description="타겟 노드 ID")
    model_config = {"extra": "forbid"}
