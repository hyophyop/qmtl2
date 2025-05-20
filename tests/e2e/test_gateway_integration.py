"""
Integration tests for the Gateway service.

This module contains integration tests that verify the interaction between
SDK, Gateway, and DAG Manager components, focusing on data exchange,
serialization, and authentication/ACL validation.
"""

import json
import pytest
import requests
import time
from google.protobuf import json_format
from typing import Dict, Any, Optional

from qmtl.models.generated import (
    qmtl_common_pb2 as common_pb2,
    qmtl_strategy_pb2 as strategy_pb2,
    qmtl_datanode_pb2 as datanode_pb2,
    qmtl_pipeline_pb2 as pipeline_pb2,
)

from tests.e2e import factories
from tests.e2e.test_config import GATEWAY_BASE_URL, TEST_USER, get_endpoint, TIMEOUTS
from tests.templates.gateway_roundtrip_template import (
    basic_roundtrip_test,
    retrieve_roundtrip_test,
    compare_proto_objects,
)

# Test markers
pytestmark = [pytest.mark.integration, pytest.mark.gateway, pytest.mark.e2e]

# Test data
TEST_STRATEGY = {
    "strategy_name": "test_strategy_integration",
    "description": "Integration test strategy",
    "author": "tester",
    "version": "1.0.0",
    "tags": ["integration", "test"],
    "source": "pytest",
}

TEST_DATANODE = {
    "node_id": "test_datanode_integration",
    "node_type": "SOURCE",
    "data_schema": {"field1": "string", "field2": "int32"},
    "tags": ["integration", "test"],
    "description": "Integration test data node",
    "owner": "tester",
}


@pytest.mark.usefixtures("docker_compose_up_down")
class TestGatewayAuthentication:
    """Test authentication and authorization flows."""

    def test_successful_authentication(self, gateway_client, gateway_session):
        """Test successful authentication with valid credentials."""
        # Given
        auth_url = get_endpoint("auth", "token")
        auth_data = {"username": TEST_USER["username"], "password": TEST_USER["password"]}

        # When
        response = gateway_client.post(
            auth_url,
            data=auth_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=TIMEOUTS["short"],
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"].lower() == "bearer"
        assert "expires_in" in data

    def test_invalid_credentials(self, gateway_client, gateway_session):
        """Test authentication with invalid credentials."""
        # Given
        auth_url = get_endpoint("auth", "token")
        auth_data = {"username": "invalid_user", "password": "wrong_password"}

        # When
        response = gateway_client.post(
            auth_url,
            data=auth_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=TIMEOUTS["short"],
        )

        # Then
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Incorrect username or password" in data["detail"]

    def test_protected_endpoint_without_token(self, gateway_client, gateway_session):
        """Test accessing a protected endpoint without a token."""
        # Given
        url = get_endpoint("strategies", "base")

        # When
        response = gateway_client.get(url, timeout=TIMEOUTS["short"])

        # Then
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Not authenticated" in data["detail"]

    def test_protected_endpoint_with_invalid_token(self, gateway_client, gateway_session):
        """Test accessing a protected endpoint with an invalid token."""
        # Given
        url = get_endpoint("strategies", "base")
        headers = {"Authorization": "Bearer invalid_token_123", "Accept": "application/json"}

        # When
        response = gateway_client.get(url, headers=headers, timeout=TIMEOUTS["short"])

        # Then
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Could not validate credentials" in data["detail"]


class TestStrategyManagement:
    """Test strategy management operations."""

    def test_register_strategy(self, authenticated_gateway_client, gateway_session):
        """Test registering a new strategy."""
        # Given
        url = get_endpoint("strategies", "base")
        strategy_metadata = factories.create_strategy_metadata(**TEST_STRATEGY)

        # When
        response = authenticated_gateway_client.post(
            url,
            data=strategy_metadata.SerializeToString(),
            headers={"Content-Type": "application/x-protobuf"},
            timeout=TIMEOUTS["medium"],
        )

        # Then
        assert response.status_code == 200

        # Parse the response as a StrategyRegistrationResponse
        response_msg = strategy_pb2.StrategyRegistrationResponse()
        response_msg.ParseFromString(response.content)

        assert response_msg.success is True
        assert response_msg.strategy_id
        assert response_msg.status == strategy_pb2.StrategyStatus.ACTIVE

    def test_get_strategy(self, authenticated_gateway_client, gateway_session):
        """Test retrieving a strategy by ID."""
        # First, register a strategy
        register_url = get_endpoint("strategies", "base")
        strategy_metadata = factories.create_strategy_metadata(**TEST_STRATEGY)

        register_response = authenticated_gateway_client.post(
            register_url,
            data=strategy_metadata.SerializeToString(),
            headers={"Content-Type": "application/x-protobuf"},
            timeout=TIMEOUTS["medium"],
        )
        assert register_response.status_code == 200

        # Get the strategy ID from the registration response
        register_response_msg = strategy_pb2.StrategyRegistrationResponse()
        register_response_msg.ParseFromString(register_response.content)
        strategy_id = register_response_msg.strategy_id

        # Now, retrieve the strategy
        get_url = get_endpoint("strategies", "by_id", strategy_id=strategy_id)

        response = authenticated_gateway_client.get(
            get_url, headers={"Accept": "application/x-protobuf"}, timeout=TIMEOUTS["short"]
        )

        # Then
        assert response.status_code == 200

        # Parse the response as a StrategyMetadata
        response_msg = strategy_pb2.StrategyMetadata()
        response_msg.ParseFromString(response.content)

        assert response_msg.strategy_name == TEST_STRATEGY["strategy_name"]
        assert response_msg.description == TEST_STRATEGY["description"]
        assert response_msg.author == TEST_STRATEGY["author"]
        assert response_msg.version == TEST_STRATEGY["version"]


class TestDataNodeManagement:
    """Test data node management operations."""

    def test_create_datanode(self, authenticated_gateway_client, gateway_session):
        """Test creating a new data node."""
        # Given
        url = get_endpoint("datanodes", "base")
        datanode_metadata = factories.create_datanode_metadata(**TEST_DATANODE)

        # When
        response = authenticated_gateway_client.post(
            url,
            data=datanode_metadata.SerializeToString(),
            headers={"Content-Type": "application/x-protobuf"},
            timeout=TIMEOUTS["medium"],
        )

        # Then
        assert response.status_code == 200

        # Parse the response as a DataNodeResponse
        response_msg = datanode_pb2.DataNodeResponse()
        response_msg.ParseFromString(response.content)

        assert response_msg.success is True
        assert response_msg.node_metadata.node_id == TEST_DATANODE["node_id"]
        assert response_msg.node_metadata.node_type == TEST_DATANODE["node_type"]
        assert response_msg.node_metadata.description == TEST_DATANODE["description"]
        assert response_msg.node_metadata.owner == TEST_DATANODE["owner"]

    def test_get_datanode(self, authenticated_gateway_client, gateway_session):
        """Test retrieving a data node by ID."""
        # First, create a data node
        create_url = get_endpoint("datanodes", "base")
        datanode_metadata = factories.create_datanode_metadata(**TEST_DATANODE)

        create_response = authenticated_gateway_client.post(
            create_url,
            data=datanode_metadata.SerializeToString(),
            headers={"Content-Type": "application/x-protobuf"},
            timeout=TIMEOUTS["medium"],
        )
        assert create_response.status_code == 200

        # Get the node ID from the creation response
        create_response_msg = datanode_pb2.DataNodeResponse()
        create_response_msg.ParseFromString(create_response.content)
        node_id = create_response_msg.node_metadata.node_id

        # Now, retrieve the data node
        get_url = get_endpoint("datanodes", "by_id", datanode_id=node_id)

        response = authenticated_gateway_client.get(
            get_url, headers={"Accept": "application/x-protobuf"}, timeout=TIMEOUTS["short"]
        )

        # Then
        assert response.status_code == 200

        # Parse the response as a DataNodeMetadata
        response_msg = datanode_pb2.DataNodeMetadata()
        response_msg.ParseFromString(response.content)

        assert response_msg.node_id == node_id
        assert response_msg.node_type == TEST_DATANODE["node_type"]
        assert response_msg.description == TEST_DATANODE["description"]
        assert response_msg.owner == TEST_DATANODE["owner"]


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_nonexistent_endpoint(self, authenticated_gateway_client, gateway_session):
        """Test accessing a non-existent endpoint."""
        # Given
        url = f"{gateway_session}/api/v1/nonexistent"

        # When
        response = authenticated_gateway_client.get(
            url, headers={"Accept": "application/json"}, timeout=TIMEOUTS["short"]
        )

        # Then
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Not Found" in data["detail"]

    def test_invalid_protobuf(self, authenticated_gateway_client, gateway_session):
        """Test sending invalid protobuf data."""
        # Given
        url = get_endpoint("strategies", "base")

        # When
        response = authenticated_gateway_client.post(
            url,
            data=b"invalid_protobuf_data",
            headers={"Content-Type": "application/x-protobuf"},
            timeout=TIMEOUTS["short"],
        )

        # Then
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Invalid protobuf data" in data["detail"]


class TestGatewayDAGManagerIntegration:
    """Gateway와 DAG Manager 간 통합 테스트 클래스"""

    def test_strategy_registration_to_dag_manager(self, authenticated_gateway_client):
        """전략 등록 및 DAG Manager 전달 테스트"""
        # 1. 테스트용 전략 생성
        strategy_data = {
            "strategy_name": "integration_test_strategy",
            "description": "Strategy for integration test",
            "author": "tester",
            "version": "1.0.0",
            "tags": ["integration", "test"],
            "source": "pytest",
        }
        strategy = factories.create_strategy_metadata(**strategy_data)

        # 2. Gateway API를 통해 전략 등록
        url = get_endpoint("strategies", "base")
        response = authenticated_gateway_client.post(
            url,
            data=strategy.SerializeToString(),
            headers={"Content-Type": "application/x-protobuf"},
            timeout=TIMEOUTS["medium"],
        )

        # 3. 응답 검증
        assert response.status_code == 200
        response_msg = strategy_pb2.StrategyRegistrationResponse()
        response_msg.ParseFromString(response.content)
        assert response_msg.success, "전략 등록 실패"
        strategy_id = response_msg.strategy_id

        # 4. DAG Manager를 통해 등록된 전략 조회
        strategy_url = get_endpoint("strategies", "by_id", strategy_id=strategy_id)
        response = authenticated_gateway_client.get(
            strategy_url,
            headers={"Accept": "application/x-protobuf"},
            timeout=TIMEOUTS["short"],
        )

        # 5. 조회 결과 검증
        assert response.status_code == 200, f"전략 조회 실패: {response.status_code}"
        retrieved_strategy = strategy_pb2.StrategyMetadata()
        retrieved_strategy.ParseFromString(response.content)

        # 6. 원본 전략과 조회된 전략 비교
        assert retrieved_strategy.strategy_name == strategy.strategy_name
        assert retrieved_strategy.description == strategy.description
        assert retrieved_strategy.author == strategy.author
        assert retrieved_strategy.version == strategy.version
        assert list(retrieved_strategy.tags) == list(strategy.tags)
        assert retrieved_strategy.source == strategy.source

    def test_datanode_creation_to_dag_manager(self, authenticated_gateway_client):
        """데이터 노드 생성 및 DAG Manager 전달 테스트"""
        # 1. 테스트용 데이터 노드 생성
        datanode_data = {
            "node_id": f"integration_test_datanode_{int(time.time())}",
            "node_type": "SOURCE",
            "data_schema": {"field1": "string", "field2": "int32"},
            "tags": ["integration", "test"],
            "description": "Data node for integration test",
            "owner": "tester",
        }
        datanode = factories.create_datanode_metadata(**datanode_data)

        # 2. Gateway API를 통해 데이터 노드 생성
        url = get_endpoint("datanodes", "base")
        response = authenticated_gateway_client.post(
            url,
            data=datanode.SerializeToString(),
            headers={"Content-Type": "application/x-protobuf"},
            timeout=TIMEOUTS["medium"],
        )

        # 3. 응답 검증
        assert response.status_code == 200
        response_msg = datanode_pb2.DataNodeResponse()
        response_msg.ParseFromString(response.content)
        assert response_msg.success, "데이터 노드 생성 실패"

        # 4. DAG Manager를 통해 생성된 데이터 노드 조회
        datanode_url = get_endpoint("datanodes", "by_id", datanode_id=datanode_data["node_id"])
        response = authenticated_gateway_client.get(
            datanode_url,
            headers={"Accept": "application/x-protobuf"},
            timeout=TIMEOUTS["short"],
        )

        # 5. 조회 결과 검증
        assert response.status_code == 200, f"데이터 노드 조회 실패: {response.status_code}"
        retrieved_datanode = datanode_pb2.DataNode()
        retrieved_datanode.ParseFromString(response.content)

        # 6. 원본 데이터 노드와 조회된 데이터 노드 비교
        assert retrieved_datanode.node_id == datanode.node_id
        assert retrieved_datanode.type == datanode.type
        assert retrieved_datanode.description == datanode.description
        assert list(retrieved_datanode.tags) == list(datanode.tags)


class TestProtobufRoundtripIntegration:
    """Protobuf 라운드트립 통합 테스트 클래스"""

    def test_strategy_roundtrip_integration(self, authenticated_gateway_client):
        """전략 Protobuf 라운드트립 통합 테스트"""
        # 1. 테스트용 전략 생성
        strategy_data = {
            "strategy_name": "roundtrip_test_strategy",
            "description": "Strategy for roundtrip test",
            "author": "tester",
            "version": "1.0.0",
            "tags": ["roundtrip", "test"],
            "source": "pytest",
        }
        strategy = factories.create_strategy_metadata(**strategy_data)

        # 2. 템플릿 함수를 사용한 라운드트립 테스트
        create_url = get_endpoint("strategies", "base")
        response = basic_roundtrip_test(
            message_obj=strategy,
            client_fixture=authenticated_gateway_client,
            endpoint=create_url,
            response_cls=strategy_pb2.StrategyRegistrationResponse,
        )

        # 3. 응답 검증
        assert response.success, "템플릿 기반 전략 등록 실패"
        strategy_id = response.strategy_id

        # 4. 생성된 리소스 조회
        retrieve_url = get_endpoint("strategies", "by_id", strategy_id=strategy_id)
        retrieved_strategy = retrieve_roundtrip_test(
            resource_id=strategy_id,
            client_fixture=authenticated_gateway_client,
            endpoint=retrieve_url,
            response_cls=strategy_pb2.StrategyMetadata,
        )

        # 5. 원본과 조회 결과 비교
        assert compare_proto_objects(
            strategy,
            retrieved_strategy,
            ["strategy_name", "description", "version", "author", "tags", "source"],
        ), "템플릿 기반 비교: 원본과 조회된 전략 객체가 일치하지 않음"

    def test_pipeline_roundtrip_integration(self, authenticated_gateway_client):
        """파이프라인 Protobuf 라운드트립 통합 테스트"""
        # 1. 테스트용 파이프라인 생성
        pipeline_data = {
            "name": "roundtrip_test_pipeline",
            "metadata": {"purpose": "testing", "environment": "development"},
        }
        pipeline = factories.create_pipeline_definition(**pipeline_data)

        # 2. 템플릿 함수를 사용한 라운드트립 테스트
        create_url = get_endpoint("pipelines", "base")
        response = basic_roundtrip_test(
            message_obj=pipeline,
            client_fixture=authenticated_gateway_client,
            endpoint=create_url,
            response_cls=pipeline_pb2.PipelineResponse,
        )

        # 3. 응답 검증
        assert response.success, "템플릿 기반 파이프라인 생성 실패"
        pipeline_id = response.pipeline_id

        # 4. 생성된 리소스 조회
        retrieve_url = get_endpoint("pipelines", "by_id", pipeline_id=pipeline_id)
        retrieved_pipeline = retrieve_roundtrip_test(
            resource_id=pipeline_id,
            client_fixture=authenticated_gateway_client,
            endpoint=retrieve_url,
            response_cls=pipeline_pb2.Pipeline,
        )

        # 5. 원본과 조회 결과 비교 (파이프라인 ID는 서버에서 생성되므로 제외)
        assert retrieved_pipeline.name == pipeline.name, "파이프라인 이름이 일치하지 않음"
        assert (
            retrieved_pipeline.metadata.items() == pipeline.metadata.items()
        ), "파이프라인 메타데이터가 일치하지 않음"


class TestGatewayMessageConsistency:
    """Gateway 메시지 일관성 테스트 클래스"""

    def test_binary_json_consistency(self, authenticated_gateway_client):
        """바이너리와 JSON 형식의 일관성 테스트"""
        # 1. 테스트용 전략 생성
        strategy_data = {
            "strategy_name": "format_test_strategy",
            "description": "Strategy for format consistency test",
            "author": "tester",
            "version": "1.0.0",
            "tags": ["format", "test"],
            "source": "pytest",
        }
        strategy = factories.create_strategy_metadata(**strategy_data)

        # 2. Binary 형식으로 등록
        binary_url = get_endpoint("strategies", "base")
        binary_response = authenticated_gateway_client.post(
            binary_url,
            data=strategy.SerializeToString(),
            headers={"Content-Type": "application/x-protobuf"},
            timeout=TIMEOUTS["medium"],
        )

        # 3. 응답 검증
        assert binary_response.status_code == 200
        binary_response_msg = strategy_pb2.StrategyRegistrationResponse()
        binary_response_msg.ParseFromString(binary_response.content)
        assert binary_response_msg.success, "바이너리 형식 전략 등록 실패"
        binary_strategy_id = binary_response_msg.strategy_id

        # 4. JSON 형식으로 전략 조회
        json_url = get_endpoint("strategies", "by_id", strategy_id=binary_strategy_id)
        json_response = authenticated_gateway_client.get(
            json_url,
            headers={"Accept": "application/json"},
            timeout=TIMEOUTS["short"],
        )

        # 5. 응답 검증
        assert json_response.status_code == 200
        json_data = json_response.json()

        # 6. JSON 응답에서 필드 비교
        assert json_data["strategy_name"] == strategy.strategy_name
        assert json_data["description"] == strategy.description
        assert json_data["author"] == strategy.author
        assert json_data["version"] == strategy.version
        assert json_data["tags"] == list(strategy.tags)
        assert json_data["source"] == strategy.source


# TODO: Add more test cases for:
# - Concurrency and performance testing
# - Schema validation and versioning
# - Integration with DAG Manager service
# - Error handling and edge cases
# - ACL and permission testing
