from qmtl.dag_manager.core.graph_builder import GraphBuilder
from qmtl.models.datanode import DataNode, NodeStreamSettings, IntervalSettings
from qmtl.sdk.models import IntervalEnum
import pytest


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _build_stream_settings():
    interval_settings = IntervalSettings(interval=IntervalEnum.MINUTE, period=1)
    return NodeStreamSettings(intervals={IntervalEnum.MINUTE: interval_settings})


class DummyNodeService:
    """get_strategy_nodes 만 구현한 최소 서비스 더블(double)"""

    def __init__(self, nodes):
        self._nodes = nodes

    def get_strategy_nodes(self, strategy_version_id):  # noqa: D401,D403 (simple)
        return self._nodes


# ---------------------------------------------------------------------------
# Happy path: DAG with linear dependencies
# ---------------------------------------------------------------------------


def test_graph_builder_topological_order():
    n1 = DataNode(
        node_id="1" * 32,
        data_format={"type": "csv"},
        dependencies=[],
        stream_settings=_build_stream_settings(),
    )
    n2 = DataNode(
        node_id="2" * 32,
        data_format={"type": "csv"},
        dependencies=[n1.node_id],
        stream_settings=_build_stream_settings(),
    )
    n3 = DataNode(
        node_id="3" * 32,
        data_format={"type": "csv"},
        dependencies=[n2.node_id],
        stream_settings=_build_stream_settings(),
    )
    nodes = [n1, n2, n3]
    builder = GraphBuilder(nodes)
    node_map, topo = builder.build_dag()
    assert set(node_map.keys()) == {n1.node_id, n2.node_id, n3.node_id}
    assert topo.order == [n1.node_id, n2.node_id, n3.node_id]


# ---------------------------------------------------------------------------
# Negative path: cyclic dependency detection
# ---------------------------------------------------------------------------


def test_graph_builder_cycle_detection():
    a = DataNode(
        node_id="a" * 32,
        data_format={"type": "csv"},
        dependencies=["c" * 32],
        stream_settings=_build_stream_settings(),
    )
    b = DataNode(
        node_id="b" * 32,
        data_format={"type": "csv"},
        dependencies=[a.node_id],
        stream_settings=_build_stream_settings(),
    )
    c = DataNode(
        node_id="c" * 32,
        data_format={"type": "csv"},
        dependencies=[b.node_id],
        stream_settings=_build_stream_settings(),
    )
    nodes = [a, b, c]
    builder = GraphBuilder(nodes)
    with pytest.raises(ValueError):
        builder.build_dag()
