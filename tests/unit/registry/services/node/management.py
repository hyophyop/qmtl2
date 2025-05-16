from unittest.mock import MagicMock
from unittest.mock import ANY

import pytest

from qmtl.models.datanode import DataNode, IntervalSettings, NodeTags, NodeType
from qmtl.models.status import NodeStatus, StatusType
from qmtl.registry.services.node.management import Neo4jNodeManagementService


@pytest.fixture
def mock_neo4j_client():
    return MagicMock()


@pytest.fixture
def service(mock_neo4j_client):
    return Neo4jNodeManagementService(mock_neo4j_client)


@pytest.fixture
def sample_node():
    return DataNode(
        node_id="1234567890abcdef1234567890abcdef",
        type=NodeType.RAW,
        data_format={"fields": ["a", "b"]},
        params={"foo": "bar"},
        dependencies=[],
        ttl=3600,
        tags=NodeTags(predefined=["RAW"]),
        interval_settings=IntervalSettings(interval="1d", period=7),
    )


def test_create_node_success(service, mock_neo4j_client, sample_node):
    mock_neo4j_client.execute_query.side_effect = [[], [{"node_id": sample_node.node_id}]]
    node_id = service.create_node(sample_node)
    assert node_id == sample_node.node_id


def test_create_node_already_exists(service, mock_neo4j_client, sample_node):
    mock_neo4j_client.execute_query.side_effect = [[{"n": {"node_id": sample_node.node_id}}]]
    with pytest.raises(Exception):
        service.create_node(sample_node)


def test_get_node_found(service, mock_neo4j_client, sample_node):
    mock_neo4j_client.execute_query.return_value = [{"n": sample_node.model_dump()}]
    node = service.get_node(sample_node.node_id)
    assert node.node_id == sample_node.node_id


def test_get_node_not_found(service, mock_neo4j_client):
    mock_neo4j_client.execute_query.return_value = []
    node = service.get_node("notfound")
    assert node is None


def test_delete_node_success(service, mock_neo4j_client, sample_node):
    mock_neo4j_client.execute_query.return_value = [{"deleted": 1}]
    assert service.delete_node(sample_node.node_id) is True


def test_delete_node_not_found(service, mock_neo4j_client):
    mock_neo4j_client.execute_query.return_value = [{"deleted": 0}]
    assert service.delete_node("notfound") is False


def test_list_nodes(service, mock_neo4j_client, sample_node):
    mock_neo4j_client.execute_query.return_value = [{"n": sample_node.model_dump()}]
    nodes = service.list_nodes()
    assert len(nodes) == 1
    assert nodes[0].node_id == sample_node.node_id


def test_list_zero_deps(service, mock_neo4j_client, sample_node):
    mock_neo4j_client.execute_query.return_value = [{"n": sample_node.model_dump()}]
    nodes = service.list_zero_deps()
    assert len(nodes) == 1
    assert nodes[0].node_id == sample_node.node_id


def test_add_contains_relationship(service, mock_neo4j_client):
    service.add_contains_relationship("ver1", "node1")
    mock_neo4j_client.execute_query.assert_called_with(
        ANY, {"strategy_version_id": "ver1", "node_id": "node1"}, None
    )


def test_remove_contains_relationship(service, mock_neo4j_client):
    service.remove_contains_relationship("ver1", "node1")
    mock_neo4j_client.execute_query.assert_called_with(
        ANY, {"strategy_version_id": "ver1", "node_id": "node1"}, None
    )


def test_get_node_ref_count(service, mock_neo4j_client):
    mock_neo4j_client.execute_query.return_value = [{"ref_count": 2}]
    count = service.get_node_ref_count("node1")
    assert count == 2
    mock_neo4j_client.execute_query.assert_called_with(ANY, {"node_id": "node1"}, None)

    mock_neo4j_client.execute_query.return_value = []
    count = service.get_node_ref_count("node1")
    assert count == 0


def test_get_node_ref_strategies(service, mock_neo4j_client):
    mock_neo4j_client.execute_query.return_value = [{"version_id": "ver1"}, {"version_id": "ver2"}]
    versions = service.get_node_ref_strategies("node1")
    assert versions == ["ver1", "ver2"]
    mock_neo4j_client.execute_query.assert_called_with(ANY, {"node_id": "node1"}, None)

    mock_neo4j_client.execute_query.return_value = []
    versions = service.get_node_ref_strategies("node1")
    assert versions == []


def test_get_strategy_nodes(service, mock_neo4j_client, sample_node):
    mock_neo4j_client.execute_query.return_value = [{"n": sample_node.model_dump()}]
    nodes = service.get_strategy_nodes("ver1")
    assert len(nodes) == 1
    assert nodes[0].node_id == sample_node.node_id
    mock_neo4j_client.execute_query.assert_called_with(ANY, {"strategy_version_id": "ver1"}, None)

    mock_neo4j_client.execute_query.return_value = []
    nodes = service.get_strategy_nodes("ver1")
    assert len(nodes) == 0


def test_update_and_get_node_status(service, mock_neo4j_client):
    # NodeStatus 저장 후 조회
    node_id = "1234567890abcdef1234567890abcdef"
    status_obj = NodeStatus(
        node_id=node_id,
        status=StatusType.RUNNING,
        resource={"cpu": 0.5, "mem": 256},
        meta={"last_active": "2025-05-12T12:00:00"},
    )
    # update_node_status는 execute_query만 호출, 반환값 없음
    mock_neo4j_client.execute_query.return_value = None
    service.update_node_status(node_id, status_obj)
    # get_node_status는 execute_query로 NodeStatus dict 반환
    mock_neo4j_client.execute_query.return_value = [{"s": status_obj.model_dump()}]
    result = service.get_node_status(node_id)
    assert result is not None
    assert result.node_id == node_id
    assert result.status == StatusType.RUNNING
    assert result.resource["cpu"] == 0.5
    assert result.meta["last_active"] == "2025-05-12T12:00:00"


def test_get_node_status_not_found(service, mock_neo4j_client):
    # 없는 node_id 조회 시 None 반환
    mock_neo4j_client.execute_query.return_value = []
    result = service.get_node_status("notfound")
    assert result is None
