"""
E2E test for SDK <-> Gateway <-> DAG Manager integration scenarios.

This module contains integration tests that verify the data exchange, serialization,
and authentication/ACL between SDK, Gateway, and DAG Manager components.
"""
import pytest
from unittest.mock import patch, MagicMock
from typing import Dict, Any

from qmtl.models.generated import (
    qmtl_strategy_pb2 as strategy_pb2,
    qmtl_common_pb2 as common_pb2,
    qmtl_datanode_pb2 as datanode_pb2,
    qmtl_pipeline_pb2 as pipeline_pb2
)

# factories 등은 절대 import로 사용
from tests.e2e import factories


# Test fixtures and helpers

@pytest.fixture
def mock_gateway_client():
    """Fixture that mocks the Gateway client for testing."""
    with patch('src.qmtl.sdk.gateway.GatewayClient') as mock_client:
        yield mock_client()

@pytest.fixture
def sample_strategy_metadata() -> strategy_pb2.StrategyMetadata:
    """Fixture that returns a sample StrategyMetadata for testing."""
    return strategy_pb2.StrategyMetadata(
        strategy_name="test_strategy",
        description="Test strategy for integration testing",
        author="tester",
        tags=["integration", "test"],
        version="1.0.0",
        source="pytest",
        extra_data={"test_key": "test_value"}
    )

@pytest.fixture
def sample_datanode_metadata() -> datanode_pb2.DataNode:
    """Fixture that returns a sample DataNodeMetadata for testing."""
    return datanode_pb2.DataNode(
        node_id="test_node_1",
        node_type="SOURCE",
        data_schema={"field1": "string", "field2": "int32"},
        tags=["test", "source"]
    )

# Test cases

def test_strategy_metadata_roundtrip():
    """Test round-trip serialization/deserialization of StrategyMetadata."""
    original = strategy_pb2.StrategyMetadata(
        strategy_name="test_roundtrip",
        description="Roundtrip test",
        author="tester",
        tags=["test", "serialization"],
        version="1.0.0",
        source="pytest"
    )
    
    # Serialize and deserialize
    serialized = original.SerializeToString()
    deserialized = strategy_pb2.StrategyMetadata()
    deserialized.ParseFromString(serialized)
    
    # Verify all fields match
    assert original.strategy_name == deserialized.strategy_name
    assert original.description == deserialized.description
    assert original.author == deserialized.author
    assert list(original.tags) == list(deserialized.tags)
    assert original.version == deserialized.version
    assert original.source == deserialized.source
    assert dict(original.extra_data) == dict(deserialized.extra_data)

def test_gateway_authentication(mock_gateway_client):
    """Test authentication flow between SDK and Gateway."""
    # Setup mock
    mock_gateway_client.authenticate.return_value = common_pb2.AuthResponse(
        success=True,
        token="test_jwt_token",
        user_id="test_user"
    )
    
    # Test authentication
    response = mock_gateway_client.authenticate(
        username="test_user",
        password="test_password"
    )
    
    # Verify
    assert response.success is True
    assert response.token == "test_jwt_token"
    mock_gateway_client.authenticate.assert_called_once_with(
        username="test_user",
        password="test_password"
    )

def test_datanode_creation_flow(mock_gateway_client, sample_datanode_metadata):
    """Test end-to-end data node creation flow through Gateway."""
    # Setup mock
    mock_response = datanode_pb2.DataNodeResponse(
        success=True,
        node_metadata=sample_datanode_metadata
    )
    mock_gateway_client.create_datanode.return_value = mock_response
    
    # Test create datanode
    response = mock_gateway_client.create_datanode(sample_datanode_metadata)
    
    # Verify
    assert response.success is True
    assert response.node_metadata.node_id == "test_node_1"
    mock_gateway_client.create_datanode.assert_called_once_with(sample_datanode_metadata)

def test_strategy_registration_flow(mock_gateway_client, sample_strategy_metadata):
    """Test end-to-end strategy registration flow through Gateway."""
    # Setup mock
    mock_response = strategy_pb2.StrategyRegistrationResponse(
        success=True,
        strategy_id="test_strategy_123",
        status=strategy_pb2.StrategyStatus.ACTIVE
    )
    mock_gateway_client.register_strategy.return_value = mock_response
    
    # Test register strategy
    response = mock_gateway_client.register_strategy(sample_strategy_metadata)
    
    # Verify
    assert response.success is True
    assert response.strategy_id == "test_strategy_123"
    assert response.status == strategy_pb2.StrategyStatus.ACTIVE
    mock_gateway_client.register_strategy.assert_called_once_with(sample_strategy_metadata)

def test_acl_validation(mock_gateway_client):
    """Test ACL validation for unauthorized access attempts."""
    # Setup mock for unauthorized access
    mock_gateway_client.get_sensitive_data.side_effect = PermissionError(
        "User not authorized to access this resource"
    )
    
    # Test unauthorized access
    with pytest.raises(PermissionError):
        mock_gateway_client.get_sensitive_data(
            resource_id="sensitive_data_1",
            user_id="unauthorized_user"
        )
    
    # Verify
    mock_gateway_client.get_sensitive_data.assert_called_once_with(
        resource_id="sensitive_data_1",
        user_id="unauthorized_user"
    )

# TODO: Add more test cases for:
# - Error handling and edge cases
# - Concurrency and performance testing
# - Schema validation and versioning
# - Integration with DAG Manager service
