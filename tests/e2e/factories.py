"""
Test data factories for Gateway integration tests.

This module provides factory functions to generate test data for integration tests.
"""
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime, timedelta

from qmtl.models.generated import (
    qmtl_common_pb2 as common_pb2,
    qmtl_strategy_pb2 as strategy_pb2,
    qmtl_datanode_pb2 as datanode_pb2,
    qmtl_pipeline_pb2 as pipeline_pb2
)


def create_test_user(
    user_id: Optional[str] = None,
    username: str = "testuser",
    email: str = "test@example.com",
    full_name: str = "Test User",
    is_active: bool = True,
    is_superuser: bool = False,
    roles: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Create a test user dictionary."""
    if user_id is None:
        user_id = str(uuid.uuid4())
    if roles is None:
        roles = ["user"]
    
    return {
        "id": user_id,
        "username": username,
        "email": email,
        "full_name": full_name,
        "is_active": is_active,
        "is_superuser": is_superuser,
        "roles": roles,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }


def create_auth_request(
    username: str = "testuser",
    password: str = "testpass"
) -> Dict[str, str]:
    """Create an authentication request."""
    return {
        "username": username,
        "password": password
    }


def create_auth_response(
    access_token: str = "test_jwt_token",
    token_type: str = "bearer",
    expires_in: int = 3600
) -> Dict[str, Any]:
    """Create an authentication response."""
    return {
        "access_token": access_token,
        "token_type": token_type,
        "expires_in": expires_in
    }


def create_strategy_metadata(
    strategy_name: str = "test_strategy",
    description: str = "Test strategy",
    author: str = "tester",
    version: str = "1.0.0",
    tags: Optional[List[str]] = None,
    source: str = "pytest",
    extra_data: Optional[Dict[str, str]] = None
) -> strategy_pb2.StrategyMetadata:
    """Create a StrategyMetadata protobuf message for testing."""
    if tags is None:
        tags = ["test", "integration"]
    if extra_data is None:
        extra_data = {"test_key": "test_value"}
    
    return strategy_pb2.StrategyMetadata(
        strategy_name=strategy_name,
        description=description,
        author=author,
        version=version,
        tags=tags,
        source=source,
        extra_data=extra_data
    )


def create_datanode_metadata(
    node_id: Optional[str] = None,
    node_type: str = "SOURCE",
    data_format: Optional[Dict[str, str]] = None,
    tags: Optional[list] = None,
    description: str = "Test data node",
    owner: str = "tester"
) -> datanode_pb2.DataNode:
    """Create a DataNodeMetadata protobuf message for testing."""
    if node_id is None:
        node_id = f"test_node_{uuid.uuid4().hex[:8]}"
    if data_format is None:
        data_format = {"field1": "string", "field2": "int32"}
    if tags is None:
        tags = ["test", "source"]
    
    return datanode_pb2.DataNode(
        node_id=node_id,
        type=node_type,
        data_format=[datanode_pb2.DataNode.DataFormatEntry(key=k, value=v) for k, v in data_format.items()],
        tags=None,  # NodeTags 메시지로 래핑 필요시 별도 처리
        # description, owner 등은 실제 proto에 맞게 추가
    )


def create_pipeline_definition(
    name: str = "test_pipeline",
    nodes: Optional[list] = None,
    query_nodes: Optional[list] = None,
    metadata: Optional[dict] = None
) -> pipeline_pb2.PipelineDefinition:
    """Create a PipelineMetadata protobuf message for testing."""
    if nodes is None:
        nodes = []
    if query_nodes is None:
        query_nodes = []
    if metadata is None:
        metadata = {}
    return pipeline_pb2.PipelineDefinition(
        name=name,
        nodes=nodes,
        query_nodes=query_nodes,
        metadata=[pipeline_pb2.PipelineDefinition.MetadataEntry(key=k, value=v) for k, v in metadata.items()]
    )


    
