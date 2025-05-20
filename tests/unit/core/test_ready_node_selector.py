from qmtl.dag_manager.core.ready_node_selector import ReadyNodeSelector
from qmtl.models.datanode import DataNode, NodeStreamSettings, IntervalSettings
from qmtl.sdk.models import IntervalEnum


# Helpers ---------------------------------------------------------------


def _stream():
    interval_settings = IntervalSettings(interval=IntervalEnum.MINUTE, period=1)
    return NodeStreamSettings(intervals={IntervalEnum.MINUTE: interval_settings})


class DummyNodeService:
    def __init__(self, nodes):
        self._nodes = nodes

    def get_strategy_nodes(self, strategy_version_id):
        return self._nodes


class DummyStatusService:
    def __init__(self, status_map):
        # status_map[(pipeline_id, node_id)] -> status str
        self.map = status_map

    def get_node_status(self, pipeline_id, node_id):  # noqa: D401
        s = self.map.get((pipeline_id, node_id))
        return {"status": s} if s else None


# ----------------------------------------------------------------------


def test_ready_node_selector():
    # Build simple DAG: n1 -> n2 -> n3
    n1 = DataNode(
        node_id="1" * 32, data_format={"type": "csv"}, dependencies=[], stream_settings=_stream()
    )
    n2 = DataNode(
        node_id="2" * 32,
        data_format={"type": "csv"},
        dependencies=[n1.node_id],
        stream_settings=_stream(),
    )
    n3 = DataNode(
        node_id="3" * 32,
        data_format={"type": "csv"},
        dependencies=[n2.node_id],
        stream_settings=_stream(),
    )
    nodes = [n1, n2, n3]
    # 상태: n1 완료, n2 대기, n3 미정
    node_status_map = {
        n1.node_id: "COMPLETED",
        n2.node_id: "PENDING",
        n3.node_id: None,
    }
    selector = ReadyNodeSelector(nodes, node_status_map)
    ready_nodes = selector.get_ready_nodes()
    # n2만 ready여야 함
    assert len(ready_nodes) == 1
    assert ready_nodes[0].node_id == n2.node_id
