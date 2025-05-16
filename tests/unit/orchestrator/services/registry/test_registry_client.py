from unittest.mock import patch

import pytest
import httpx

from qmtl.common.errors.exceptions import RegistryClientError
from qmtl.models.datanode import DataNode, IntervalSettings, NodeTags, NodeType
from qmtl.models.strategy import StrategyMetadata
from qmtl.orchestrator.services.registry.registry_client import RegistryClient


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


@pytest.fixture
def sample_strategy_metadata():
    return StrategyMetadata(
        strategy_name="test-strategy",
        description="Test Strategy",
        tags=["test"],
    )


@pytest.fixture
def client():
    with patch("qmtl.orchestrator.services.registry.registry_client.Client"):
        registry_client = RegistryClient("http://localhost:8000")
        yield registry_client


def test_register_node(client, sample_node):
    client.client.post.return_value.json.return_value = {"node_id": sample_node.node_id}
    client.client.post.return_value.status_code = 201

    result = client.register_node(sample_node)

    assert result == sample_node.node_id
    client.client.post.assert_called_with(
        f"{client.nodes_path}", json={"node": sample_node.model_dump()}
    )


def test_register_strategy(client, sample_strategy_metadata):
    client.client.post.return_value.json.return_value = {"version_id": "test-version-id"}
    client.client.post.return_value.status_code = 201

    result = client.register_strategy(sample_strategy_metadata)

    assert result == "test-version-id"
    client.client.post.assert_called_with(
        f"{client.strategies_path}", json={"metadata": sample_strategy_metadata.model_dump()}
    )


def test_get_node(client, sample_node):
    client.client.get.return_value.json.return_value = {"node": sample_node.model_dump()}
    client.client.get.return_value.status_code = 200

    result = client.get_node(sample_node.node_id)

    assert result is not None
    assert result.node_id == sample_node.node_id
    client.client.get.assert_called_with(f"{client.nodes_path}/{sample_node.node_id}")


def test_add_contains_relationship(client):
    strategy_id = "test-version-id"
    node_id = "1234567890abcdef1234567890abcdef"

    client.client.post.return_value.status_code = 200

    result = client.add_contains_relationship(strategy_id, node_id)

    assert result is True
    client.client.post.assert_called_with(f"{client.strategies_path}/{strategy_id}/nodes/{node_id}")


def test_remove_contains_relationship(client):
    strategy_id = "test-version-id"
    node_id = "1234567890abcdef1234567890abcdef"

    client.client.delete.return_value.status_code = 200

    result = client.remove_contains_relationship(strategy_id, node_id)

    assert result is True
    client.client.delete.assert_called_with(
        f"{client.strategies_path}/{strategy_id}/nodes/{node_id}"
    )


def test_get_node_ref_count(client):
    node_id = "1234567890abcdef1234567890abcdef"

    client.client.get.return_value.json.return_value = {"ref_count": 3}
    client.client.get.return_value.status_code = 200

    result = client.get_node_ref_count(node_id)

    assert result == 3
    client.client.get.assert_called_with(f"{client.nodes_path}/{node_id}/ref-count")


def test_get_node_ref_strategies(client):
    node_id = "1234567890abcdef1234567890abcdef"
    strategy_ids = ["ver1", "ver2", "ver3"]

    client.client.get.return_value.json.return_value = {"strategy_version_ids": strategy_ids}
    client.client.get.return_value.status_code = 200

    result = client.get_node_ref_strategies(node_id)

    assert result == strategy_ids
    client.client.get.assert_called_with(f"{client.nodes_path}/{node_id}/ref-strategies")


def test_get_strategy_nodes(client, sample_node):
    strategy_id = "test-version-id"

    client.client.get.return_value.json.return_value = {"nodes": [sample_node.model_dump()]}
    client.client.get.return_value.status_code = 200

    result = client.get_strategy_nodes(strategy_id)

    assert len(result) == 1
    assert result[0].node_id == sample_node.node_id
    client.client.get.assert_called_with(f"{client.strategies_path}/{strategy_id}/nodes")


def test_add_contains_relationship_error(client):
    strategy_id = "test-version-id"
    node_id = "1234567890abcdef1234567890abcdef"

    client.client.post.side_effect = httpx.HTTPError("Connection error")

    with pytest.raises(RegistryClientError):
        client.add_contains_relationship(strategy_id, node_id)


def test_get_node_ref_count_not_found(client):
    node_id = "1234567890abcdef1234567890abcdef"

    client.client.get.return_value.status_code = 404

    result = client.get_node_ref_count(node_id)

    assert result == 0
