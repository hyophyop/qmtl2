import pytest
from unittest.mock import MagicMock, patch
from qmtl.dag_manager.registry.services.node.management import Neo4jNodeManagementService
from qmtl.common.errors.exceptions import DatabaseError
from qmtl.models.datanode import NodeStreamSettings, IntervalSettings, DataNode
from qmtl.sdk.models import IntervalEnum


def test_create_node_success():
    mock_client = MagicMock()
    mock_client.execute_query.side_effect = [[], [{"node_id": "n1"}]]
    service = Neo4jNodeManagementService(neo4j_client=mock_client)
    node = MagicMock()
    node.node_id = "n1"
    node.type = MagicMock(value="DATA")
    node.data_format = {}
    node.params = {}
    node.dependencies = []
    node.ttl = None
    node.tags = None
    node.interval_settings = None
    node.stream_settings = None
    assert service.create_node(node) == "n1"


def test_create_node_already_exists():
    mock_client = MagicMock()
    mock_client.execute_query.side_effect = [[{"n": "exists"}]]
    service = Neo4jNodeManagementService(neo4j_client=mock_client)
    node = MagicMock()
    node.node_id = "n1"
    with pytest.raises(DatabaseError):
        service.create_node(node)


def test_get_node_success():
    mock_client = MagicMock()
    stream_settings = NodeStreamSettings(
        intervals={IntervalEnum.MINUTE: IntervalSettings(interval=IntervalEnum.MINUTE, period=1)}
    ).model_dump()
    interval_settings = IntervalSettings(interval=IntervalEnum.MINUTE, period=1).model_dump()
    node_data = {
        "n": {
            "node_id": "a" * 32,  # 32자리 소문자 16진수
            "type": "RAW",  # Enum 값
            "data_format": "{}",
            "params": "{}",
            "dependencies": [],
            "ttl": None,
            "tags": "{}",
            "interval_settings": interval_settings,
            "stream_settings": stream_settings,
        }
    }
    mock_client.execute_query.return_value = [node_data]
    service = Neo4jNodeManagementService(neo4j_client=mock_client)
    with patch.object(DataNode, "model_validate", wraps=DataNode.model_validate) as mock_validate:
        service.get_node("a" * 32)
        assert mock_validate.called


def test_get_node_not_found():
    mock_client = MagicMock()
    mock_client.execute_query.return_value = []
    service = Neo4jNodeManagementService(neo4j_client=mock_client)
    assert service.get_node("n1") is None


def test_delete_node_success():
    mock_client = MagicMock()
    mock_client.execute_query.return_value = [{"deleted": 1}]
    service = Neo4jNodeManagementService(neo4j_client=mock_client)
    assert service.delete_node("n1") is True


def test_delete_node_not_found():
    mock_client = MagicMock()
    mock_client.execute_query.return_value = [{"deleted": 0}]
    service = Neo4jNodeManagementService(neo4j_client=mock_client)
    assert service.delete_node("n1") is False


def test_list_nodes_success():
    mock_client = MagicMock()
    mock_client.execute_query.return_value = [{"n": {}}]
    service = Neo4jNodeManagementService(neo4j_client=mock_client)
    # DataNode.model_validate를 모킹
    import qmtl.models.datanode

    qmtl.models.datanode.DataNode = MagicMock()
    assert isinstance(service.list_nodes(), list)


def test_get_strategy_dag(monkeypatch):
    service = Neo4jNodeManagementService(neo4j_client=MagicMock())
    dummy_nodes = [
        MagicMock(node_id="n1", dependencies=[]),
        MagicMock(node_id="n2", dependencies=["n1"]),
    ]
    monkeypatch.setattr(service, "get_strategy_nodes", lambda x: dummy_nodes)
    node_map, topo_result = service.get_strategy_dag("dummy_strategy")
    assert set(node_map.keys()) == {"n1", "n2"}
    assert "n1" in topo_result.order and "n2" in topo_result.order


def test_get_ready_nodes(monkeypatch):
    service = Neo4jNodeManagementService(neo4j_client=MagicMock())
    dummy_nodes = [
        MagicMock(node_id="n1", dependencies=[]),
        MagicMock(node_id="n2", dependencies=["n1"]),
    ]
    monkeypatch.setattr(service, "get_strategy_nodes", lambda x: dummy_nodes)
    node_status_map = {"n1": "READY", "n2": "PENDING"}
    ready_nodes = service.get_ready_nodes("dummy_strategy", node_status_map)
    assert any(n.node_id == "n1" for n in ready_nodes)


def test_enqueue_ready_nodes():
    service = Neo4jNodeManagementService(neo4j_client=MagicMock())
    ready_nodes = [MagicMock(node_id="n1")]
    queue_repo = MagicMock()
    status_service = MagicMock()
    result = service.enqueue_ready_nodes(ready_nodes, queue_repo, status_service)
    queue_repo.push.assert_called_with("n1")
    status_service.update_node_status.assert_called_with("n1", "READY")
    assert result == ready_nodes
