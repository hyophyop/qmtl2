import pytest

from qmtl.common.errors.exceptions import CyclicDependencyError
from qmtl.models.datanode import DataNode, NodeTag
from qmtl.dag_manager.strategy.dag_service import DAGService
from qmtl.sdk.models import IntervalEnum


def make_stream_settings_dict():
    return {
        "intervals": {
            IntervalEnum.DAY: {
                "interval": IntervalEnum.DAY,
                "period": 1,
            }
        }
    }


@pytest.fixture
def dag_service():
    return DAGService()


@pytest.fixture
def simple_nodes():
    """단순 노드 구조 (A -> B -> C)"""
    return [
        DataNode(
            node_id="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            type=NodeTag.FEATURE,
            data_format={"type": "json"},
            dependencies=[],
            stream_settings=make_stream_settings_dict(),
        ),
        DataNode(
            node_id="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            type=NodeTag.FEATURE,
            data_format={"type": "json"},
            dependencies=["aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"],
            stream_settings=make_stream_settings_dict(),
        ),
        DataNode(
            node_id="cccccccccccccccccccccccccccccccc",
            type=NodeTag.SIGNAL,
            data_format={"type": "json"},
            dependencies=["bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"],
            stream_settings=make_stream_settings_dict(),
        ),
    ]


@pytest.fixture
def cyclic_nodes():
    """사이클이 있는 노드 구조 (A -> B -> C -> A)"""
    return [
        DataNode(
            node_id="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            type=NodeTag.FEATURE,
            data_format={"type": "json"},
            dependencies=["cccccccccccccccccccccccccccccccc"],
            stream_settings=make_stream_settings_dict(),
        ),
        DataNode(
            node_id="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            type=NodeTag.FEATURE,
            data_format={"type": "json"},
            dependencies=["aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"],
            stream_settings=make_stream_settings_dict(),
        ),
        DataNode(
            node_id="cccccccccccccccccccccccccccccccc",
            type=NodeTag.SIGNAL,
            data_format={"type": "json"},
            dependencies=["bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"],
            stream_settings=make_stream_settings_dict(),
        ),
    ]


@pytest.fixture
def complex_nodes():
    """복잡한 DAG 구조 (다중 의존성)
    A -> B -> D
      \     /
        C -/
    """
    return [
        DataNode(
            node_id="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            type=NodeTag.RAW,
            data_format={"type": "json"},
            dependencies=[],
            stream_settings=make_stream_settings_dict(),
        ),
        DataNode(
            node_id="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            type=NodeTag.FEATURE,
            data_format={"type": "json"},
            dependencies=["aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"],
            stream_settings=make_stream_settings_dict(),
        ),
        DataNode(
            node_id="cccccccccccccccccccccccccccccccc",
            type=NodeTag.FEATURE,
            data_format={"type": "json"},
            dependencies=["aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"],
            stream_settings=make_stream_settings_dict(),
        ),
        DataNode(
            node_id="dddddddddddddddddddddddddddddddd",
            type=NodeTag.SIGNAL,
            data_format={"type": "json"},
            dependencies=["bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", "cccccccccccccccccccccccccccccccc"],
            stream_settings=make_stream_settings_dict(),
        ),
    ]


def test_build_dag_simple(dag_service, simple_nodes):
    """단순 DAG 구성 테스트"""
    dag_service.build_dag(simple_nodes)
    assert len(dag_service.nodes) == 3
    assert set(dag_service.get_root_nodes()) == {"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}
    assert set(dag_service.get_leaf_nodes()) == {"cccccccccccccccccccccccccccccccc"}


def test_verify_acyclic_simple(dag_service, simple_nodes):
    """단순 DAG 사이클 검증 테스트"""
    dag_service.build_dag(simple_nodes)
    assert dag_service.verify_acyclic() is True


def test_verify_acyclic_cyclic(dag_service, cyclic_nodes):
    """사이클 있는 DAG 검증 테스트"""
    with pytest.raises(CyclicDependencyError):
        dag_service.build_dag(cyclic_nodes)


def test_topological_order_simple(dag_service, simple_nodes):
    """단순 DAG 위상 정렬 테스트"""
    dag_service.build_dag(simple_nodes)
    topo_order = dag_service.get_topological_order()
    # A가 B보다 먼저, B가 C보다 먼저 오는지 검증
    a_idx = topo_order.index("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
    b_idx = topo_order.index("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb")
    c_idx = topo_order.index("cccccccccccccccccccccccccccccccc")
    assert a_idx < b_idx < c_idx


def test_topological_order_complex(dag_service, complex_nodes):
    """복잡한 DAG 위상 정렬 테스트"""
    dag_service.build_dag(complex_nodes)
    topo_order = dag_service.get_topological_order()
    # A가 B, C보다 먼저, B와 C가 D보다 먼저 오는지 검증
    a_idx = topo_order.index("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
    b_idx = topo_order.index("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb")
    c_idx = topo_order.index("cccccccccccccccccccccccccccccccc")
    d_idx = topo_order.index("dddddddddddddddddddddddddddddddd")
    assert a_idx < b_idx
    assert a_idx < c_idx
    assert b_idx < d_idx
    assert c_idx < d_idx


def test_get_dependencies(dag_service, complex_nodes):
    """노드 의존성 조회 테스트"""
    dag_service.build_dag(complex_nodes)
    deps = dag_service.get_dependencies("dddddddddddddddddddddddddddddddd")
    assert len(deps) == 2
    assert set(d.node_id for d in deps) == {
        "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "cccccccccccccccccccccccccccccccc",
    }


def test_get_dependents(dag_service, complex_nodes):
    """노드에 의존하는 노드 조회 테스트"""
    dag_service.build_dag(complex_nodes)
    deps = dag_service.get_dependents("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
    assert len(deps) == 2
    assert set(d.node_id for d in deps) == {
        "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "cccccccccccccccccccccccccccccccc",
    }


def test_reset(dag_service, simple_nodes):
    """DAG 상태 초기화 테스트"""
    dag_service.build_dag(simple_nodes)
    assert len(dag_service.nodes) > 0

    dag_service.reset()
    assert len(dag_service.nodes) == 0
    assert len(dag_service.adjacency_list) == 0
    assert len(dag_service.reverse_adjacency_list) == 0
    assert dag_service.verified is False
