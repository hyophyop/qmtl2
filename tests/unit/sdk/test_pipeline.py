import pytest

from qmtl.sdk import Analyzer, ProcessingNode, Pipeline, QueryNode
from qmtl.sdk.models import (
    QueryNodeResultSelector,
    IntervalSettings,
    IntervalEnum,
    NodeStreamSettings,
)
from qmtl.sdk.node import SourceNode, SourceProcessor


# 기본 테스트 함수
def add_func(value):
    return value + 1


def multiply_func(value, factor=2):
    return value * factor


def combine_func(a, b):
    return a + b


# Node 클래스 테스트
def test_node_instantiation():
    node = SourceNode(
        name="test_node",
        source=type("S", (), {"fetch": staticmethod(lambda: 1)})(),
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    assert node.name == "test_node"
    assert node.tags == []
    assert node.upstreams == []
    assert node.key_params == []
    assert node.node_id == "test_node"


def test_node_with_upstreams():
    node = ProcessingNode(
        name="test_node",
        fn=lambda x: x,
        upstreams=["upstream1", "upstream2"],
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    assert node.upstreams == ["upstream1", "upstream2"]


def test_node_with_key_params():
    node = SourceNode(
        name="test_node",
        source=type("S", (), {"fetch": staticmethod(lambda: 1)})(),
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    assert node.key_params == []
    assert node.node_id == "test_node"


def test_node_with_interval_settings():
    node = SourceNode(
        name="test_node",
        source=type("S", (), {"fetch": staticmethod(lambda: 1)})(),
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    assert node.name == "test_node"


def test_node_id_generation():
    # 동일한 함수와 매개변수로 생성한 노드는 동일한 ID를 가져야 함
    node1 = ProcessingNode(
        name="node1",
        fn=multiply_func,
        key_params=["factor"],
        upstreams=["up"],
        factor=3,
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    node2 = ProcessingNode(
        name="node2",
        fn=multiply_func,
        key_params=["factor"],
        upstreams=["up"],
        factor=3,
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    assert node1.node_id == node2.node_id

    # 매개변수가 다르면 다른 ID를 가져야 함
    node3 = ProcessingNode(
        name="node3",
        fn=multiply_func,
        key_params=["factor"],
        upstreams=["up"],
        factor=4,
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    assert node1.node_id != node3.node_id


def test_node_execute():
    node = ProcessingNode(
        name="add",
        fn=add_func,
        upstreams=["upstream"],
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    result = node.execute({"upstream": 5})
    assert result == 6


def test_node_execute_with_key_params():
    node = ProcessingNode(
        name="multiply",
        fn=multiply_func,
        key_params=["factor"],
        upstreams=["value"],
        factor=3,
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    result = node.execute({"value": 5})
    assert result == 15


def test_node_execute_with_multiple_upstreams():
    node = ProcessingNode(
        name="combine",
        fn=combine_func,
        upstreams=["a", "b"],
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    result = node.execute({"a": 3, "b": 4})
    assert result == 7


def test_node_execute_missing_upstream():
    node = ProcessingNode(
        name="add",
        fn=add_func,
        upstreams=["upstream"],
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    with pytest.raises(ValueError):
        node.execute({})


def test_node_to_definition():
    node = ProcessingNode(
        name="test",
        fn=lambda x: x,
        tags=["RAW"],
        upstreams=["upstream"],
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    definition = node.to_definition()
    assert definition["name"] == "test"
    assert definition["tags"] == ["RAW"]
    assert definition["upstreams"] == ["upstream"]
    assert "node_id" in definition
    assert "fn" not in definition  # 함수는 직렬화되지 않아야 함

    # 역직렬화 테스트
    from qmtl.sdk.models import NodeDefinition

    node_def = NodeDefinition.from_definition(definition)
    assert node_def.name == "test"
    assert node_def.tags == ["RAW"]
    assert node_def.upstreams == ["upstream"]


def test_node_missing_interval():
    pipeline = Pipeline(name="test_missing_interval")
    node = ProcessingNode(name="n1", fn=lambda x: x, upstreams=["up"])
    with pytest.raises(Exception):
        pipeline.add_node(node)


def test_sourcenode_missing_interval():
    class DummySource:
        def fetch(self):
            return 1

    import pytest

    pipeline = Pipeline(name="test_missing_interval")
    node = SourceNode(name="src1", source=DummySource())
    with pytest.raises(Exception):
        pipeline.add_node(node)


# QueryNode 클래스 테스트
def test_query_node_instantiation():
    qnode = QueryNode(
        name="qnode",
        tags=["FEATURE"],
        interval=IntervalEnum.DAY,
        period=7,
        upstreams=["_dummy"],
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    assert qnode.name == "qnode"
    assert qnode.query_tags == ["FEATURE"]
    assert qnode.interval == IntervalEnum.DAY
    assert qnode.period == 7


def test_query_node_to_definition():
    qnode = QueryNode(
        name="qnode",
        tags=["FEATURE"],
        interval=IntervalEnum.DAY,
        period=7,
        upstreams=["_dummy"],
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    definition = qnode.to_definition()
    assert definition["name"] == "qnode"
    assert definition["query_tags"] == ["FEATURE"]
    assert definition["interval"] == IntervalEnum.DAY
    assert definition["period"] == 7

    # 역직렬화 테스트
    from qmtl.sdk.models import QueryNodeDefinition

    qnode_def = QueryNodeDefinition.from_definition(definition)
    assert qnode_def.name == "qnode"
    assert qnode_def.query_tags == ["FEATURE"]
    assert qnode_def.interval == IntervalEnum.DAY
    assert qnode_def.period == 7


# Pipeline 클래스 테스트
def test_pipeline_instantiation():
    pipeline = Pipeline(name="test_pipeline")
    assert pipeline.name == "test_pipeline"
    assert pipeline.nodes == {}
    assert pipeline.query_nodes == {}


def test_pipeline_add_node():
    pipeline = Pipeline(name="test_pipeline")
    node = ProcessingNode(
        name="test_node",
        fn=lambda x: x,
        upstreams=["up"],
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    added_node = pipeline.add_node(node)
    assert added_node is node
    assert pipeline.nodes["test_node"] is node


def test_pipeline_add_duplicate_node():
    pipeline = Pipeline(name="test_pipeline")
    node1 = ProcessingNode(
        name="test_node",
        fn=lambda x: x,
        upstreams=["up"],
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    node2 = ProcessingNode(
        name="test_node",
        fn=lambda x: x * 2,
        upstreams=["up"],
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    pipeline.add_node(node1)
    with pytest.raises(ValueError):
        pipeline.add_node(node2)


def test_pipeline_add_query_node():
    pipeline = Pipeline(name="test_pipeline")
    qnode = QueryNode(
        name="qnode",
        tags=["FEATURE"],
        upstreams=["_dummy"],
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    result = pipeline.add_query_node(qnode)
    assert result == "qnode"
    assert pipeline.query_nodes["qnode"] is qnode


def test_pipeline_get_node():
    pipeline = Pipeline(name="test_pipeline")
    node = ProcessingNode(
        name="test_node",
        fn=lambda x: x,
        upstreams=["up"],
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    pipeline.add_node(node)
    assert pipeline.get_node("test_node") is node
    assert pipeline.get_node("non_existent") is None


def test_pipeline_dependencies():
    pipeline = Pipeline(name="test_pipeline")
    node_a = SourceNode(
        name="A",
        source=type("S", (), {"fetch": staticmethod(lambda: 1)})(),
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    pipeline.nodes["A"] = node_a
    pipeline.add_node(
        ProcessingNode(
            name="B",
            fn=lambda x: x + 1,
            upstreams=["A"],
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
    )
    pipeline.add_node(
        ProcessingNode(
            name="C",
            fn=lambda x: x * 2,
            upstreams=["B"],
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
    )

    deps = pipeline.get_dependencies()
    assert deps["A"] == set()
    assert deps["B"] == {"A"}
    assert deps["C"] == {"B"}


def test_pipeline_topological_sort():
    pipeline = Pipeline(name="test_pipeline")
    pipeline.add_node(
        ProcessingNode(
            name="C",
            fn=lambda x, y: x + y,
            upstreams=["A", "B"],
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
    )
    pipeline.add_node(
        ProcessingNode(
            name="B",
            fn=lambda x: x * 2,
            upstreams=["A"],
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
    )
    node_a = SourceNode(
        name="A",
        source=type("S", (), {"fetch": staticmethod(lambda: 1)})(),
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    pipeline.nodes["A"] = node_a

    order = pipeline.get_execution_order()
    # A는 B와 C 이전에, B는 C 이전에 실행되어야 함
    assert order.index("A") < order.index("B")
    assert order.index("A") < order.index("C")
    assert order.index("B") < order.index("C")


def test_pipeline_cyclic_dependency():
    pipeline = Pipeline(name="test_pipeline")
    pipeline.add_node(
        ProcessingNode(
            name="A",
            fn=lambda x: x + 1,
            upstreams=["C"],
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
    )
    pipeline.add_node(
        ProcessingNode(
            name="B",
            fn=lambda x: x * 2,
            upstreams=["A"],
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
    )
    pipeline.add_node(
        ProcessingNode(
            name="C",
            fn=lambda x: x / 2,
            upstreams=["B"],
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
    )
    with pytest.raises(ValueError):
        pipeline.get_execution_order()


@pytest.mark.timeout(10)
def test_pipeline_execute():
    pipeline = Pipeline(name="test_pipeline")
    node_a = SourceNode(
        name="A",
        source=type("S", (), {"fetch": staticmethod(lambda: 1)})(),
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    pipeline.nodes["A"] = node_a
    pipeline.add_node(
        ProcessingNode(
            name="B",
            fn=lambda value: value + 1,
            upstreams=["A"],
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
    )
    pipeline.add_node(
        ProcessingNode(
            name="C",
            fn=lambda value: value * 2,
            upstreams=["B"],
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
    )

    # parallel=False로 설정하여 로컬 실행
    results = pipeline.execute(parallel=False)
    assert results["A"] == 1
    assert results["B"] == 2
    assert results["C"] == 4


def test_pipeline_execute_with_inputs():
    pipeline = Pipeline(name="test_pipeline")

    class DummySource(SourceProcessor):
        def fetch(self):
            return 5

    source = DummySource()
    source_node = SourceNode(
        name="source",
        source=source,
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    pipeline.nodes["source"] = source_node

    pipeline.add_node(
        ProcessingNode(
            name="A",
            fn=lambda value: value,
            upstreams=["source"],
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
    )
    pipeline.add_node(
        ProcessingNode(
            name="B",
            fn=lambda value: value + 1,
            upstreams=["A"],
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
    )
    pipeline.add_node(
        ProcessingNode(
            name="C",
            fn=lambda value: value * 2,
            upstreams=["B"],
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
    )

    results = pipeline.execute(parallel=False)
    assert results["A"] == 5
    assert results["B"] == 6
    assert results["C"] == 12


@pytest.mark.timeout(10)
def test_pipeline_execute_complex_dag():
    pipeline = Pipeline(name="complex_dag")

    # 가상의 DAG:
    #     A
    #    / \
    #   B   C
    #   |   |
    #   D   E
    #    \ /
    #     F

    node_a = SourceNode(
        name="A",
        source=type("S", (), {"fetch": staticmethod(lambda: 10)})(),
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    pipeline.nodes["A"] = node_a
    pipeline.add_node(
        ProcessingNode(
            name="B",
            fn=lambda value: value // 2,
            upstreams=["A"],
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
    )
    pipeline.add_node(
        ProcessingNode(
            name="C",
            fn=lambda value: value * 2,
            upstreams=["A"],
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
    )
    pipeline.add_node(
        ProcessingNode(
            name="D",
            fn=lambda value: value - 1,
            upstreams=["B"],
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
    )
    pipeline.add_node(
        ProcessingNode(
            name="E",
            fn=lambda value: value + 5,
            upstreams=["C"],
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
    )
    pipeline.add_node(
        ProcessingNode(
            name="F",
            fn=lambda d, e: d * e,
            upstreams=["D", "E"],
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
    )

    results = pipeline.execute(parallel=False)
    assert results["A"] == 10
    assert results["B"] == 5
    assert results["C"] == 20
    assert results["D"] == 4
    assert results["E"] == 25
    assert results["F"] == 100  # 4 * 25


def test_pipeline_to_definition():
    pipeline = Pipeline(name="test_pipeline")
    node_a = SourceNode(
        name="A",
        source=type("S", (), {"fetch": staticmethod(lambda: 1)})(),
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    pipeline.nodes["A"] = node_a
    pipeline.add_node(
        ProcessingNode(
            name="B",
            fn=lambda x: x + 1,
            upstreams=["A"],
            tags=["FEATURE"],
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
    )

    definition = pipeline.to_definition()
    assert definition["name"] == "test_pipeline"
    assert len(definition["nodes"]) == 2
    assert definition["nodes"][0]["name"] in ["A", "B"]
    assert definition["nodes"][1]["name"] in ["A", "B"]

    # 역직렬화 테스트
    from qmtl.sdk.models import PipelineDefinition

    pipeline_def = PipelineDefinition.from_definition(definition)
    assert pipeline_def.name == "test_pipeline"
    assert len(pipeline_def.nodes) == 2
    node_names = [n.name for n in pipeline_def.nodes]
    assert set(node_names) == {"A", "B"}


def test_pipeline_get_history():
    pipeline = Pipeline(name="test_pipeline")
    node_a = SourceNode(
        name="A",
        source=type("S", (), {"fetch": staticmethod(lambda: 42)})(),
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    pipeline.nodes["A"] = node_a

    # 노드 객체의 results_cache 초기화
    node_a.results_cache = {}
    pipeline.results_cache = {}

    # 노드를 실행하여 결과 캐싱
    pipeline.execute(parallel=False)

    # 히스토리 데이터 가져오기
    history = pipeline.get_history("A")
    print("get_history:", history)
    assert len(history) == 1
    assert history[0] == 42


def test_pipeline_get_history_nonexistent_node():
    pipeline = Pipeline(name="test_pipeline")
    with pytest.raises(ValueError):
        pipeline.get_history("nonexistent")


# Analyzer 클래스 테스트
def test_analyzer_instantiation():
    analyzer = Analyzer(name="test_analyzer")
    assert analyzer.name == "test_analyzer"
    assert "ANALYZER" in analyzer.tags


def test_analyzer_with_tags():
    analyzer = Analyzer(name="test_analyzer", tags=["CORRELATION"])
    assert "ANALYZER" in analyzer.tags
    assert "CORRELATION" in analyzer.tags


def test_analyzer_to_definition():
    analyzer = Analyzer(name="test_analyzer")
    definition = analyzer.to_definition()
    assert definition["name"] == "test_analyzer"
    assert definition["type"] == "analyzer"
    assert "ANALYZER" in definition["tags"]


def test_analyzer_querynode_tag_filtering():
    from qmtl.sdk.node import SourceNode

    # 노드 3개: FEATURE, RAW, FEATURE+RAW
    node1 = SourceNode(
        name="n1",
        source=type("S", (), {"fetch": staticmethod(lambda: 10)})(),
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    node1.tags = ["FEATURE"]
    node2 = SourceNode(
        name="n2",
        source=type("S", (), {"fetch": staticmethod(lambda: 20)})(),
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    node2.tags = ["RAW"]
    node3 = SourceNode(
        name="n3",
        source=type("S", (), {"fetch": staticmethod(lambda: 30)})(),
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    node3.tags = ["FEATURE", "RAW"]
    analyzer = Analyzer(name="test_analyzer")
    analyzer.add_node(node1)
    analyzer.add_node(node2)
    analyzer.add_node(node3)
    # FEATURE 태그로 QueryNode 추가
    qnode = QueryNode(
        name="q1",
        tags=["FEATURE"],
        interval=IntervalEnum.DAY,
        result_selector=QueryNodeResultSelector(mode="list"),
        upstreams=["_dummy"],
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    analyzer.add_query_node(qnode)
    results = analyzer.execute(local=True)
    # FEATURE 태그가 포함된 노드만 결과에 포함되어야 함
    assert set(results["q1"].keys()) == {"n1", "n3"}
    assert results["q1"]["n1"] == 10
    assert results["q1"]["n3"] == 30


def test_analyzer_querynode_tag_and_interval_filtering():
    from qmtl.sdk.node import SourceNode

    # 노드 2개: FEATURE+interval=1d, FEATURE+interval=1h
    node1 = SourceNode(
        name="n1",
        source=type("S", (), {"fetch": staticmethod(lambda: 1)})(),
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    node1.tags = ["FEATURE"]
    node2 = SourceNode(
        name="n2",
        source=type("S", (), {"fetch": staticmethod(lambda: 2)})(),
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.HOUR: IntervalSettings(interval=IntervalEnum.HOUR, period=7)}
        ),
    )
    node2.tags = ["FEATURE"]
    analyzer = Analyzer(name="test_analyzer")
    analyzer.add_node(node1)
    analyzer.add_node(node2)
    # FEATURE+1d 조건 QueryNode
    qnode = QueryNode(
        name="q1",
        tags=["FEATURE"],
        interval=IntervalEnum.DAY,
        result_selector=QueryNodeResultSelector(mode="list"),
        upstreams=["_dummy"],
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    analyzer.add_query_node(qnode)
    results = analyzer.execute(local=True)
    assert set(results["q1"].keys()) == {"n1"}
    assert results["q1"]["n1"] == 1


def test_analyzer_querynode_tag_and_period_filtering():
    from qmtl.sdk.node import SourceNode

    # 노드 2개: FEATURE+period=7d, FEATURE+period=3d
    node1 = SourceNode(
        name="n1",
        source=type("S", (), {"fetch": staticmethod(lambda: 1)})(),
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=7)}
        ),
    )
    node1.tags = ["FEATURE"]
    node2 = SourceNode(
        name="n2",
        source=type("S", (), {"fetch": staticmethod(lambda: 2)})(),
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=3)}
        ),
    )
    node2.tags = ["FEATURE"]
    analyzer = Analyzer(name="test_analyzer")
    analyzer.add_node(node1)
    analyzer.add_node(node2)
    # FEATURE+period=7d 조건 QueryNode
    qnode = QueryNode(
        name="q1",
        tags=["FEATURE"],
        period=7,
        interval=IntervalEnum.DAY,
        result_selector=QueryNodeResultSelector(mode="list"),
        upstreams=["_dummy"],
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=7)}
        ),
    )
    analyzer.add_query_node(qnode)
    results = analyzer.execute(local=True)
    assert set(results["q1"].keys()) == {"n1"}
    assert results["q1"]["n1"] == 1


def test_analyzer_querynode_selector_chaining():
    from qmtl.sdk.node import SourceNode

    default_intervals = {
        IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=14),
        IntervalEnum.HOUR: IntervalSettings(interval=IntervalEnum.HOUR, period=7),
    }
    # 노드 4개: FEATURE+interval=1d, FEATURE+interval=1d, FEATURE+interval=1h, RAW
    node1 = SourceNode(
        name="n1",
        source=type("S", (), {"fetch": staticmethod(lambda: 1)})(),
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    node1.tags = ["FEATURE"]
    node2 = SourceNode(
        name="n2",
        source=type("S", (), {"fetch": staticmethod(lambda: 2)})(),
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    node2.tags = ["FEATURE"]
    node3 = SourceNode(
        name="n3",
        source=type("S", (), {"fetch": staticmethod(lambda: 3)})(),
        stream_settings=None,
    )
    node3.tags = ["FEATURE"]
    node4 = SourceNode(
        name="n4",
        source=type("S", (), {"fetch": staticmethod(lambda: 4)})(),
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    node4.tags = ["RAW"]
    analyzer = Analyzer(name="test_analyzer", default_intervals=default_intervals)
    analyzer.add_node(node1)
    analyzer.add_node(node2)
    analyzer.add_node(node3)
    analyzer.add_node(node4)
    # FEATURE+1d 조건 QueryNode + selector 체이닝
    qnode = QueryNode(
        name="q1",
        tags=["FEATURE"],
        interval=IntervalEnum.DAY,
        result_selector=QueryNodeResultSelector(mode="random", sample_size=1),
        upstreams=["_dummy"],
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    analyzer.add_query_node(qnode)
    results = analyzer.execute(local=True)
    # FEATURE+1d 조건에 해당하는 노드 중 첫 번째 값만 반환
    assert set(results["q1"].keys()).issubset({"n1", "n2", "n3"})
    assert len(results["q1"]) == 1


def test_node_id_changes_on_code_change():
    def fn1(x):
        return x + 1

    def fn2(x):
        return x + 2  # 코드 한 글자만 다름

    node1 = ProcessingNode(
        name="n",
        fn=fn1,
        upstreams=["up"],
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    node2 = ProcessingNode(
        name="n",
        fn=fn2,
        upstreams=["up"],
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    assert node1.node_id != node2.node_id


def test_node_id_changes_on_key_params_change():
    def fn(x, factor=1):
        return x * factor

    node1 = ProcessingNode(
        name="n",
        fn=fn,
        key_params=["factor"],
        factor=2,
        upstreams=["up"],
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    node2 = ProcessingNode(
        name="n",
        fn=fn,
        key_params=["factor"],
        factor=3,
        upstreams=["up"],
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    assert node1.node_id != node2.node_id


def test_node_id_same_on_key_params_order():
    def fn(x, a=1, b=2):
        return x + a + b

    node1 = ProcessingNode(
        name="n",
        fn=fn,
        key_params=["a", "b"],
        a=10,
        b=20,
        upstreams=["up"],
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    node2 = ProcessingNode(
        name="n",
        fn=fn,
        key_params=["b", "a"],
        a=10,
        b=20,
        upstreams=["up"],
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    assert node1.node_id == node2.node_id


def test_pipeline_default_intervals_and_override():
    """Pipeline의 default_intervals가 노드에 자동 적용되고, 노드별 오버라이드가 동작하는지 테스트"""
    default_intervals = {
        IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=14),
        IntervalEnum.HOUR: IntervalSettings(interval=IntervalEnum.HOUR, period=7),
    }
    pipeline = Pipeline(name="test_default_intervals", default_intervals=default_intervals)

    # 1. 노드에 interval만 있고 period가 없으면 default_intervals의 period가 자동 적용됨
    node1 = ProcessingNode(
        name="n1",
        fn=lambda x: x,
        upstreams=["up"],
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    pipeline.add_node(node1)
    assert node1.stream_settings.intervals[IntervalEnum.DAY].period == 14

    # 2. 노드에 period가 명시되어 있으면 오버라이드됨
    node2 = ProcessingNode(
        name="n2",
        fn=lambda x: x,
        upstreams=["up"],
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=30)}
        ),
    )
    pipeline.add_node(node2)
    assert node2.stream_settings.intervals[IntervalEnum.DAY].period == 30

    # 3. default_intervals에만 있는 interval도 노드에 자동 추가됨
    node3 = ProcessingNode(
        name="n3",
        fn=lambda x: x,
        upstreams=["up"],
        stream_settings=None,
    )
    pipeline.add_node(node3)
    assert node3.stream_settings.intervals[IntervalEnum.DAY].period == 14
    assert node3.stream_settings.intervals[IntervalEnum.HOUR].period == 7

    # 4. period가 어디에도 없으면 예외 발생
    pipeline2 = Pipeline(
        name="test_no_period",
        default_intervals={},
    )
    node4 = ProcessingNode(
        name="n4",
        fn=lambda x: x,
        upstreams=["up"],
        stream_settings=None,
    )
    with pytest.raises(ValueError):
        pipeline2.add_node(node4)
