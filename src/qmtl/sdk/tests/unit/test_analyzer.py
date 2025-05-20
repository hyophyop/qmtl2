"""
Analyzer/QueryNode 단위 테스트 (SDK)
"""

from qmtl.sdk.analyzer import Analyzer
from qmtl.sdk.node import QueryNode, SourceNode, ProcessingNode
from qmtl.sdk.models import NodeStreamSettings, IntervalSettings, IntervalEnum


def test_analyzer_querynode_tag_filtering():
    # 태그가 다른 노드 3개 생성
    n1 = ProcessingNode(
        name="n1",
        fn=lambda: 1,
        tags=["A", "B"],
        upstreams=["input"],
        stream_settings=NodeStreamSettings(
            intervals={"1d": IntervalSettings(interval="1d", period=1)}
        ),
    )
    n2 = ProcessingNode(
        name="n2",
        fn=lambda: 2,
        tags=["A", "C"],
        upstreams=["input"],
        stream_settings=NodeStreamSettings(
            intervals={"1d": IntervalSettings(interval="1d", period=1)}
        ),
    )
    n3 = ProcessingNode(
        name="n3",
        fn=lambda: 3,
        tags=["B", "C"],
        upstreams=["input"],
        stream_settings=NodeStreamSettings(
            intervals={"1d": IntervalSettings(interval="1d", period=1)}
        ),
    )
    # 파이프라인/분석기 생성 및 노드 등록
    analyzer = Analyzer(name="test-analyzer")
    analyzer.add_node(n1)
    analyzer.add_node(n2)
    analyzer.add_node(n3)
    # QueryNode: 태그 A+B 모두 가진 노드만
    qn = QueryNode(
        name="q1",
        tags=["A", "B"],
        stream_settings=NodeStreamSettings(
            intervals={"1d": IntervalSettings(interval="1d", period=1)}
        ),
    )
    analyzer.query_nodes[qn.name] = qn
    matched = analyzer.find_nodes_by_query(qn)
    assert len(matched) == 1
    assert matched[0].name == "n1"
    # QueryNode: 태그 C만 가진 노드 모두
    qn2 = QueryNode(
        name="q2",
        tags=["C"],
        stream_settings=NodeStreamSettings(
            intervals={"1d": IntervalSettings(interval="1d", period=1)}
        ),
    )
    analyzer.query_nodes[qn2.name] = qn2
    matched2 = analyzer.find_nodes_by_query(qn2)
    assert set(n.name for n in matched2) == {"n2", "n3"}


def test_analyzer_execute_local():
    mock_source = type("MockSource", (), {"fetch": staticmethod(lambda: 10)})()
    n1 = SourceNode(
        name="n1",
        source=mock_source,
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
        tags=["A"],
    )
    n2 = SourceNode(
        name="n2",
        source=type("MockSource", (), {"fetch": staticmethod(lambda: 20)})(),
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
        tags=["B"],
    )
    analyzer = Analyzer(name="exec-analyzer")
    analyzer.add_node(n1)
    analyzer.add_node(n2)
    qn = QueryNode(
        name="qA",
        tags=["A"],
        upstreams=["n1"],
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    analyzer.query_nodes[qn.name] = qn
    results = analyzer.execute(local=True)
    assert "qA" in results
    assert results["qA"]["n1"] == 10
