"""
QMTL SDK Models Module - protobuf 기반으로 변환
"""

from enum import Enum

# protobuf 모델 import
from qmtl.models.generated import qmtl_pipeline_pb2, qmtl_common_pb2, qmtl_datanode_pb2


# IntervalEnum: protobuf enum과 Python enum 간 변환을 위한 래퍼 클래스
class IntervalEnum(str, Enum):
    MINUTE = "1m"
    HOUR = "1h"
    DAY = "1d"
    # 필요시 추가


# protobuf enum → Python enum 매핑
PROTO_TO_SDK_INTERVAL = {
    qmtl_common_pb2.IntervalEnum.MINUTE: IntervalEnum.MINUTE,
    qmtl_common_pb2.IntervalEnum.HOUR: IntervalEnum.HOUR,
    qmtl_common_pb2.IntervalEnum.DAY: IntervalEnum.DAY,
}

# Python enum → protobuf enum 매핑
SDK_TO_PROTO_INTERVAL = {
    IntervalEnum.MINUTE: qmtl_common_pb2.IntervalEnum.MINUTE,
    IntervalEnum.HOUR: qmtl_common_pb2.IntervalEnum.HOUR,
    IntervalEnum.DAY: qmtl_common_pb2.IntervalEnum.DAY,
    "1m": qmtl_common_pb2.IntervalEnum.MINUTE,
    "1h": qmtl_common_pb2.IntervalEnum.HOUR,
    "1d": qmtl_common_pb2.IntervalEnum.DAY,
}


# Helper functions for converting between protobuf and SDK types
def create_interval_settings(interval_enum, period, max_history=None):
    """IntervalSettings 생성 헬퍼 함수"""
    proto_interval = SDK_TO_PROTO_INTERVAL.get(interval_enum, qmtl_common_pb2.IntervalEnum.MINUTE)
    interval_settings = qmtl_common_pb2.IntervalSettings(interval=proto_interval, period=period)
    if max_history is not None:
        interval_settings.max_history = max_history
    return interval_settings


def create_node_stream_settings(intervals_dict):
    """NodeStreamSettings 생성 헬퍼 함수"""
    node_stream_settings = qmtl_datanode_pb2.NodeStreamSettings()
    for interval_key, settings in intervals_dict.items():
        if isinstance(settings, dict):
            # dict 형태의 설정을 protobuf IntervalSettings로 변환
            interval = settings.get("interval")
            period = settings.get("period")
            max_history = settings.get("max_history")

            proto_settings = create_interval_settings(
                interval_enum=interval, period=period, max_history=max_history
            )
        else:
            # IntervalSettings 객체를 사용하여 protobuf로 변환
            proto_settings = create_interval_settings(
                interval_enum=settings.interval,
                period=settings.period,
                max_history=getattr(settings, "max_history", None),
            )

        # enum key를 문자열로 변환 (map 키 요구사항)
        interval_key_str = (
            interval_key.value if isinstance(interval_key, Enum) else str(interval_key)
        )
        node_stream_settings.intervals[interval_key_str].CopyFrom(proto_settings)

    return node_stream_settings


def create_node_definition(
    name, tags=None, params=None, upstreams=None, key_params=None, stream_settings=None
):
    """NodeDefinition 생성 헬퍼 함수"""
    node_def = qmtl_pipeline_pb2.NodeDefinition(name=name)

    if tags:
        node_def.tags.extend(tags)

    if params:
        for k, v in params.items():
            # protobuf는 문자열 값만 허용하므로 변환
            node_def.params[k] = str(v)

    if upstreams:
        node_def.upstreams.extend(upstreams)

    if key_params:
        node_def.key_params.extend(key_params)

    if stream_settings:
        for k, v in stream_settings.items():
            proto_stream_settings = create_node_stream_settings(
                v.intervals if hasattr(v, "intervals") else v
            )
            node_def.stream_settings[k] = proto_stream_settings

    return node_def


def create_query_node_definition(
    name,
    query_tags,
    tags=None,
    params=None,
    upstreams=None,
    key_params=None,
    stream_settings=None,
    interval=None,
    period=None,
):
    """QueryNodeDefinition 생성 헬퍼 함수"""
    query_node_def = qmtl_pipeline_pb2.QueryNodeDefinition(name=name)
    query_node_def.query_tags.extend(query_tags)

    if tags:
        query_node_def.tags.extend(tags)

    if params:
        for k, v in params.items():
            # protobuf는 문자열 값만 허용하므로 변환
            query_node_def.params[k] = str(v)

    if upstreams:
        query_node_def.upstreams.extend(upstreams)

    if key_params:
        query_node_def.key_params.extend(key_params)

    if stream_settings:
        for k, v in stream_settings.items():
            proto_stream_settings = create_node_stream_settings(
                v.intervals if hasattr(v, "intervals") else v
            )
            query_node_def.stream_settings[k] = proto_stream_settings

    if interval is not None:
        query_node_def.interval = interval

    if period is not None:
        query_node_def.period = period

    return query_node_def


def create_pipeline_definition(name, nodes=None, query_nodes=None, metadata=None):
    """PipelineDefinition 생성 헬퍼 함수"""
    pipeline_def = qmtl_pipeline_pb2.PipelineDefinition(name=name)

    if nodes:
        # NodeDefinition 객체를 pipeline에 추가
        for node in nodes:
            # 이미 NodeDefinition protobuf 객체인 경우
            if isinstance(node, qmtl_pipeline_pb2.NodeDefinition):
                pipeline_def.nodes.append(node)
            else:
                # dict인 경우 NodeDefinition으로 변환
                node_def = create_node_definition(
                    name=node.get("name") or node.name,
                    tags=node.get("tags") or getattr(node, "tags", None),
                    params=node.get("params") or getattr(node, "params", None),
                    upstreams=node.get("upstreams") or getattr(node, "upstreams", None),
                    key_params=node.get("key_params") or getattr(node, "key_params", None),
                    stream_settings=node.get("stream_settings")
                    or getattr(node, "stream_settings", None),
                )
                pipeline_def.nodes.append(node_def)

    if query_nodes:
        # QueryNodeDefinition 객체를 pipeline에 추가
        for qnode in query_nodes:
            # 이미 QueryNodeDefinition protobuf 객체인 경우
            if isinstance(qnode, qmtl_pipeline_pb2.QueryNodeDefinition):
                pipeline_def.query_nodes.append(qnode)
            else:
                # dict인 경우 QueryNodeDefinition으로 변환
                qnode_def = create_query_node_definition(
                    name=qnode.get("name") or qnode.name,
                    query_tags=qnode.get("query_tags") or qnode.query_tags,
                    tags=qnode.get("tags") or getattr(qnode, "tags", None),
                    params=qnode.get("params") or getattr(qnode, "params", None),
                    upstreams=qnode.get("upstreams") or getattr(qnode, "upstreams", None),
                    key_params=qnode.get("key_params") or getattr(qnode, "key_params", None),
                    stream_settings=qnode.get("stream_settings")
                    or getattr(qnode, "stream_settings", None),
                    interval=qnode.get("interval") or getattr(qnode, "interval", None),
                    period=qnode.get("period") or getattr(qnode, "period", None),
                )
                pipeline_def.query_nodes.append(qnode_def)

    if metadata:
        for k, v in metadata.items():
            # protobuf는 문자열 값만 허용하므로 변환
            pipeline_def.metadata[k] = str(v)

    return pipeline_def


def create_analyzer_definition(
    name, nodes=None, query_nodes=None, metadata=None, analyzer_type="custom", tags=None
):
    """AnalyzerDefinition 생성 헬퍼 함수"""
    analyzer_def = qmtl_pipeline_pb2.AnalyzerDefinition(name=name, analyzer_type=analyzer_type)

    # 태그가 없으면 기본값으로 "ANALYZER" 추가
    if not tags:
        tags = ["ANALYZER"]
    analyzer_def.tags.extend(tags)

    if nodes:
        for node in nodes:
            if isinstance(node, qmtl_pipeline_pb2.NodeDefinition):
                analyzer_def.nodes.append(node)
            else:
                node_def = create_node_definition(
                    name=node.get("name") or node.name,
                    tags=node.get("tags") or getattr(node, "tags", None),
                    params=node.get("params") or getattr(node, "params", None),
                    upstreams=node.get("upstreams") or getattr(node, "upstreams", None),
                    key_params=node.get("key_params") or getattr(node, "key_params", None),
                    stream_settings=node.get("stream_settings")
                    or getattr(node, "stream_settings", None),
                )
                analyzer_def.nodes.append(node_def)

    if query_nodes:
        for qnode in query_nodes:
            if isinstance(qnode, qmtl_pipeline_pb2.QueryNodeDefinition):
                analyzer_def.query_nodes.append(qnode)
            else:
                qnode_def = create_query_node_definition(
                    name=qnode.get("name") or qnode.name,
                    query_tags=qnode.get("query_tags") or qnode.query_tags,
                    tags=qnode.get("tags") or getattr(qnode, "tags", None),
                    params=qnode.get("params") or getattr(qnode, "params", None),
                    upstreams=qnode.get("upstreams") or getattr(qnode, "upstreams", None),
                    key_params=qnode.get("key_params") or getattr(qnode, "key_params", None),
                    stream_settings=qnode.get("stream_settings")
                    or getattr(qnode, "stream_settings", None),
                    interval=qnode.get("interval") or getattr(qnode, "interval", None),
                    period=qnode.get("period") or getattr(qnode, "period", None),
                )
                analyzer_def.query_nodes.append(qnode_def)

    if metadata:
        for k, v in metadata.items():
            analyzer_def.metadata[k] = str(v)

    return analyzer_def


def create_query_node_result_selector(mode, batch_size=None, sample_size=None, filter_meta=None):
    """QueryNodeResultSelector 생성 헬퍼 함수"""
    selector_modes = {
        "list": qmtl_pipeline_pb2.SelectorMode.LIST,
        "batch": qmtl_pipeline_pb2.SelectorMode.BATCH,
        "random": qmtl_pipeline_pb2.SelectorMode.RANDOM,
        "filter": qmtl_pipeline_pb2.SelectorMode.FILTER,
    }

    proto_mode = selector_modes.get(mode, qmtl_pipeline_pb2.SelectorMode.LIST)
    selector = qmtl_pipeline_pb2.QueryNodeResultSelector(mode=proto_mode)

    if batch_size is not None:
        selector.batch_size = batch_size

    if sample_size is not None:
        selector.sample_size = sample_size

    if filter_meta:
        for k, v in filter_meta.items():
            selector.filter_meta[k] = str(v)

    return selector


# 하위 호환성을 위한 기존 Pydantic 모델과 유사한 래퍼 클래스
class IntervalSettings:
    """인터벌 데이터 관리 설정 (interval: Enum, period: int) - protobuf 래퍼 클래스"""

    def __init__(self, interval, period, max_history=100):
        self.interval = interval
        self.period = period
        self.max_history = max_history
        self._proto = create_interval_settings(interval, period, max_history)

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(f"No attribute {name}")
        try:
            return getattr(self._proto, name)
        except AttributeError:
            raise AttributeError(f"No attribute {name}")

    def to_proto(self):
        """protobuf 객체 반환"""
        return self._proto


class NodeStreamSettings:
    """노드 스트림 설정 (인터벌별 설정 관리) - protobuf 래퍼 클래스"""

    def __init__(self, intervals):
        self.intervals = intervals
        self._proto = create_node_stream_settings(intervals)

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(f"No attribute {name}")
        try:
            return getattr(self._proto, name)
        except AttributeError:
            raise AttributeError(f"No attribute {name}")

    def to_proto(self):
        """protobuf 객체 반환"""
        return self._proto

    def to_dict(self):
        """dict 변환 (intervals만)"""
        def interval_to_dict(v):
            # IntervalSettings 등은 __dict__만 1회 변환
            if hasattr(v, "__dict__"):
                return {k: val for k, val in v.__dict__.items() if not k.startswith("_")}
            return v
        return {k: interval_to_dict(v) for k, v in self.intervals.items()}


class NodeDefinition:
    """SDK용 노드 정의 모델 (protobuf 래퍼 클래스)"""

    def __init__(
        self, name, tags=None, params=None, upstreams=None, key_params=None, stream_settings=None
    ):
        self.name = name
        self.tags = tags or []
        self.params = params or {}
        self.upstreams = upstreams or []
        self.key_params = key_params or []
        self.stream_settings = stream_settings or {}
        self._proto = create_node_definition(
            name, tags, params, upstreams, key_params, stream_settings
        )

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(f"No attribute {name}")
        try:
            return getattr(self._proto, name)
        except AttributeError:
            raise AttributeError(f"No attribute {name}")

    @classmethod
    def from_definition(cls, data):
        """dict → NodeDefinition 역직렬화"""
        return cls(
            name=data.get("name"),
            tags=data.get("tags", []),
            params=data.get("params", {}),
            upstreams=data.get("upstreams", []),
            key_params=data.get("key_params", []),
            stream_settings=data.get("stream_settings", {}),
        )

    def to_proto(self):
        """protobuf 객체 반환"""
        return self._proto


class QueryNodeDefinition(NodeDefinition):
    """쿼리 노드 정의 모델 (protobuf 래퍼 클래스)"""

    def __init__(
        self,
        name,
        query_tags,
        tags=None,
        params=None,
        upstreams=None,
        key_params=None,
        stream_settings=None,
        interval=None,
        period=None,
    ):
        super().__init__(name, tags, params, upstreams, key_params, stream_settings)
        self.query_tags = query_tags
        self.interval = interval
        self.period = period
        self._proto = create_query_node_definition(
            name, query_tags, tags, params, upstreams, key_params, stream_settings, interval, period
        )

    @classmethod
    def from_definition(cls, data):
        """dict → QueryNodeDefinition 역직렬화"""
        # period가 str로 들어오면 int로 변환 시도
        period = data.get("period")
        if isinstance(period, str):
            try:
                period = int(period.replace("d", ""))
            except Exception:
                pass

        return cls(
            name=data.get("name"),
            query_tags=data.get("query_tags", []),
            tags=data.get("tags", []),
            params=data.get("params", {}),
            upstreams=data.get("upstreams", []),
            key_params=data.get("key_params", []),
            stream_settings=data.get("stream_settings", {}),
            interval=data.get("interval"),
            period=period,
        )


# 기존 Pydantic 모델 대체용 클래스 (하위 호환성 유지)
class PipelineDefinition:
    """
    SDK용 파이프라인 정의 모델 (protobuf 래퍼 클래스)
    """

    def __init__(self, name, nodes=None, query_nodes=None, metadata=None):
        self.name = name
        self._proto = create_pipeline_definition(name, nodes, query_nodes, metadata)

    @property
    def nodes(self):
        return list(self._proto.nodes)

    @property
    def query_nodes(self):
        return list(self._proto.query_nodes)

    @property
    def metadata(self):
        return dict(self._proto.metadata)

    @classmethod
    def from_definition(cls, data):
        """dict → PipelineDefinition 역직렬화"""
        return cls(
            name=data.get("name"),
            nodes=data.get("nodes", []),
            query_nodes=data.get("query_nodes", []),
            metadata=data.get("metadata", {}),
        )

    def to_proto(self):
        """protobuf 객체 반환"""
        return self._proto


class AnalyzerDefinition(PipelineDefinition):
    """분석기 정의 모델 (protobuf 래퍼 클래스)"""

    def __init__(
        self, name, nodes=None, query_nodes=None, metadata=None, analyzer_type="custom", tags=None
    ):
        self.name = name
        self.analyzer_type = analyzer_type
        self.tags = tags or ["ANALYZER"]
        self._proto = create_analyzer_definition(
            name, nodes, query_nodes, metadata, analyzer_type, self.tags
        )

    @classmethod
    def from_definition(cls, data):
        """dict → AnalyzerDefinition 역직렬화"""
        return cls(
            name=data.get("name"),
            nodes=data.get("nodes", []),
            query_nodes=data.get("query_nodes", []),
            metadata=data.get("metadata", {}),
            analyzer_type=data.get("analyzer_type", "custom"),
            tags=data.get("tags", ["ANALYZER"]),
        )

    @property
    def analyzer_type(self):
        return self._proto.analyzer_type

    @analyzer_type.setter
    def analyzer_type(self, value):
        if hasattr(self, "_proto"):
            self._proto.analyzer_type = value
        else:
            self._analyzer_type = value


class QueryNodeResultSelector:
    """QueryNode 결과 가공/선택용 Selector 모델 (protobuf 래퍼 클래스)"""

    def __init__(self, mode="list", batch_size=None, sample_size=None, filter_meta=None):
        self.mode = mode
        self.batch_size = batch_size
        self.sample_size = sample_size
        self.filter_meta = filter_meta or {}
        self._proto = create_query_node_result_selector(mode, batch_size, sample_size, filter_meta)

    def to_proto(self):
        """protobuf 객체 반환"""
        return self._proto
