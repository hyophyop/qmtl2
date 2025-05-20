"""
Unit tests for qmtl.sdk core logic.
"""
import os
import pytest
from google.protobuf.json_format import MessageToJson, Parse

from qmtl.models.generated.qmtl_common_pb2 import IntervalEnum, IntervalSettings, NodeTags
from qmtl.models.generated.qmtl_datanode_pb2 import DataNode

# 예시: SDK 주요 함수/클래스 임포트
# from src.qmtl.sdk.execution import SomeCoreClass
# from src.qmtl.sdk.node import NodeManager

GOLDEN_DATA_DIR = os.path.join(os.path.dirname(__file__), "../data/golden")
os.makedirs(GOLDEN_DATA_DIR, exist_ok=True)


def save_golden_data(obj, filename):
    filepath = os.path.join(GOLDEN_DATA_DIR, filename)
    with open(filepath, "w") as f:
        f.write(MessageToJson(obj))
    return filepath


def load_golden_data(proto_class, filename):
    filepath = os.path.join(GOLDEN_DATA_DIR, filename)
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r") as f:
        data = f.read()
        obj = proto_class()
        Parse(data, obj)
        return obj


def test_datanode_roundtrip():
    """DataNode protobuf 직렬화/역직렬화 round-trip 테스트"""
    original = DataNode(
        node_id="test_node_1",
        type="RAW",
        tags=NodeTags(predefined=["RAW", "TEST"], custom=["sdk", "roundtrip"]),
        interval_settings=IntervalSettings(interval=IntervalEnum.MINUTE, period=5, max_history=100),
    )
    serialized = original.SerializeToString()
    deserialized = DataNode()
    deserialized.ParseFromString(serialized)
    assert original.node_id == deserialized.node_id
    assert original.type == deserialized.type
    assert list(original.tags.predefined) == list(deserialized.tags.predefined)
    assert list(original.tags.custom) == list(deserialized.tags.custom)
    assert original.interval_settings.interval == deserialized.interval_settings.interval
    assert original.interval_settings.period == deserialized.interval_settings.period
    assert original.interval_settings.max_history == deserialized.interval_settings.max_history


def test_datanode_golden():
    """DataNode protobuf golden 테스트 (json 기반)"""
    node = DataNode(
        node_id="test_node_1",
        type="RAW",
        tags=NodeTags(predefined=["RAW", "TEST"], custom=["sdk", "golden"]),
        interval_settings=IntervalSettings(interval=IntervalEnum.MINUTE, period=5, max_history=100),
    )
    golden_node = load_golden_data(DataNode, "datanode_sdk_golden.json")
    if golden_node is None:
        save_golden_data(node, "datanode_sdk_golden.json")
        golden_node = node
    assert node.node_id == golden_node.node_id
    assert node.type == golden_node.type
    assert list(node.tags.predefined) == list(golden_node.tags.predefined)
    assert list(node.tags.custom) == list(golden_node.tags.custom)
    assert node.interval_settings.interval == golden_node.interval_settings.interval
    assert node.interval_settings.period == golden_node.interval_settings.period
    assert node.interval_settings.max_history == golden_node.interval_settings.max_history


def test_pipeline_node_basic():
    """Pipeline과 Node의 기본 동작 테스트 (노드 추가/실행)"""
    from qmtl.sdk.pipeline import Pipeline
    from qmtl.sdk.node import Node, SourceNode, SourceProcessor
    from qmtl.sdk.models import IntervalSettings, IntervalEnum
    default_intervals = {
        IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=14),
        IntervalEnum.HOUR: IntervalSettings(interval=IntervalEnum.HOUR, period=7),
    }
    class DummySource(SourceProcessor):
        def fetch(self):
            return 42
    node_a = SourceNode(name="A", source=DummySource())
    node_b = Node(name="B", fn=lambda a: a * 2, upstreams=["A"])
    pipeline = Pipeline(name="test_pipeline", default_intervals=default_intervals)
    pipeline.add_node(node_a)
    pipeline.add_node(node_b)
    results = pipeline.execute(test_mode=True)
    assert results["A"] == 42
    assert results["B"] == 84


def test_analyzer_tag_query():
    """Analyzer의 태그 기반 QueryNode 동작 테스트"""
    from qmtl.sdk.analyzer import Analyzer
    from qmtl.sdk.node import Node, QueryNode
    from qmtl.sdk.models import QueryNodeResultSelector, IntervalSettings, IntervalEnum
    default_intervals = {
        IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=14),
        IntervalEnum.HOUR: IntervalSettings(interval=IntervalEnum.HOUR, period=7),
    }
    n1 = Node(name="n1", fn=lambda **kwargs: 1, tags=["A", "B"], upstreams=["input"])
    n2 = Node(name="n2", fn=lambda **kwargs: 2, tags=["A", "C"], upstreams=["input"])
    n3 = Node(name="n3", fn=lambda **kwargs: 3, tags=["B", "C"], upstreams=["input"])
    analyzer = Analyzer(name="test-analyzer", default_intervals=default_intervals)
    analyzer.add_node(n1)
    analyzer.add_node(n2)
    analyzer.add_node(n3)
    qn = QueryNode(name="q1", tags=["A", "B"])
    analyzer.query_nodes[qn.name] = qn
    selectors = {"q1": [QueryNodeResultSelector(mode="filter", filter_meta={"tags": ["A", "B"]})]}
    results = analyzer.execute(local=True, selectors=selectors, inputs={"input": 1})
    assert "q1" in results
    print("Analyzer results:", results["q1"])
    # 결과 dict의 값들 중 1 또는 42가 있는지 검증
    assert any(r in (1, 42) for r in results["q1"].values())


def test_pipeline_interval_settings():
    """Pipeline의 interval/period 정책 기본 동작 테스트"""
    from qmtl.sdk.models import IntervalSettings, NodeStreamSettings, IntervalEnum
    from qmtl.sdk.pipeline import Pipeline, ProcessingNode

    default_intervals = {
        IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=14),
        IntervalEnum.HOUR: IntervalSettings(interval=IntervalEnum.HOUR, period=7),
    }
    pipeline = Pipeline(name="my_pipeline", default_intervals=default_intervals)
    node1 = ProcessingNode(
        name="n1",
        fn=lambda x: x,
        upstreams=["up"],
        stream_settings=NodeStreamSettings(intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)})
    )
    pipeline.add_node(node1)
    # default_intervals 적용 확인
    assert node1.stream_settings.intervals[IntervalEnum.DAY].period == 14
    node2 = ProcessingNode(
        name="n2",
        fn=lambda x: x,
        upstreams=["up"],
        stream_settings=NodeStreamSettings(intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=30)})
    )
    pipeline.add_node(node2)
    # 오버라이드 확인
    assert node2.stream_settings.intervals[IntervalEnum.DAY].period == 30
