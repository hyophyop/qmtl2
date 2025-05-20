"""
Gateway와 DAG Manager 간 통합 테스트

이 모듈은 Gateway와 DAG Manager 사이의 데이터 교환, 직렬화/역직렬화,
인증 및 ACL 검증을 확인하는 통합 테스트를 포함합니다.
"""

import json
import pytest
import requests
import time
from google.protobuf import json_format
from qmtl.models.generated import qmtl_strategy_pb2, qmtl_datanode_pb2

# Test markers
pytestmark = [pytest.mark.integration, pytest.mark.gateway, pytest.mark.dag_manager]

# 테스트 데이터
TEST_STRATEGY = {
    "strategy_name": "test_gateway_dag_integration",
    "description": "Integration test strategy for gateway-dag communication",
    "author": "tester",
    "version": "1.0.0",
    "tags": ["integration", "test", "gateway-dag"],
    "source": "pytest",
}

TEST_DATANODE = {
    "node_id": "test_datanode_gateway_dag",
    "node_type": "SOURCE",
    "data_schema": {"field1": "string", "field2": "int32"},
    "tags": ["integration", "test", "gateway-dag"],
    "description": "Integration test data node for gateway-dag",
    "owner": "tester",
}


# Docker fixture 설정
@pytest.fixture(scope="session")
def test_services(gateway_dag_docker):
    """Gateway와 DAG Manager 서비스 URL 제공"""
    return {"gateway_url": "http://localhost:8000", "dag_manager_url": "http://localhost:8001"}


@pytest.fixture(scope="session")
def gateway_session(test_services):
    """Gateway 서비스 세션 fixture"""
    gateway_url = test_services["gateway_url"]
    yield gateway_url


@pytest.fixture(scope="session")
def dag_manager_session(test_services):
    """DAG Manager 서비스 세션 fixture"""
    dag_manager_url = test_services["dag_manager_url"]
    yield dag_manager_url


def wait_for_service(url, service_name, max_retries=30, delay=1):
    """서비스가 준비될 때까지 기다리는 유틸리티 함수"""
    print(f"{service_name} 서비스 준비 대기 중: {url}")
    for i in range(max_retries):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"{service_name} 서비스 준비 완료!")
                return True
        except Exception:
            print(f"{service_name} 서비스 준비 중... 재시도 {i+1}/{max_retries}")
        time.sleep(delay)

    pytest.fail(f"{service_name} 서비스가 준비되지 않았습니다. 테스트를 진행할 수 없습니다.")


# 테스트 클래스
class TestGatewayDagManagerIntegration:
    """Gateway와 DAG Manager 간 통합 테스트 클래스"""

    def test_strategy_registration_flow(self, gateway_session, dag_manager_session):
        """Gateway를 통한 전략 등록 및 DAG Manager 동기화 테스트"""
        # 전략 데이터를 protobuf로 변환
        strategy = qmtl_strategy_pb2.Strategy()
        json_format.Parse(json.dumps(TEST_STRATEGY), strategy)

        # Gateway에 전략 등록 요청
        headers = {"Content-Type": "application/x-protobuf"}
        response = requests.post(
            f"{gateway_session}/api/v1/strategies",
            data=strategy.SerializeToString(),
            headers=headers,
        )
        assert response.status_code == 201

        # DAG Manager에서 전략 조회하여 동기화 확인
        time.sleep(1)  # 동기화 대기
        response = requests.get(
            f"{dag_manager_session}/api/v1/strategies/{TEST_STRATEGY['strategy_name']}"
        )
        assert response.status_code == 200

        # 응답을 protobuf로 파싱하여 데이터 일치 확인
        received_strategy = qmtl_strategy_pb2.Strategy()
        received_strategy.ParseFromString(response.content)
        assert received_strategy.strategy_name == TEST_STRATEGY["strategy_name"]
        assert received_strategy.description == TEST_STRATEGY["description"]

    def test_datanode_creation_flow(self, gateway_session, dag_manager_session):
        """Gateway를 통한 데이터노드 생성 및 DAG Manager 동기화 테스트"""
        # 데이터노드 protobuf 생성
        datanode = qmtl_datanode_pb2.DataNode()
        json_format.Parse(json.dumps(TEST_DATANODE), datanode)

        # Gateway에 데이터노드 생성 요청
        headers = {"Content-Type": "application/x-protobuf"}
        response = requests.post(
            f"{gateway_session}/api/v1/datanodes",
            data=datanode.SerializeToString(),
            headers=headers,
        )
        assert response.status_code == 201

        # DAG Manager에서 데이터노드 조회하여 동기화 확인
        time.sleep(1)  # 동기화 대기
        response = requests.get(
            f"{dag_manager_session}/api/v1/datanodes/{TEST_DATANODE['node_id']}"
        )
        assert response.status_code == 200

        # 응답을 protobuf로 파싱하여 데이터 일치 확인
        received_datanode = qmtl_datanode_pb2.DataNode()
        received_datanode.ParseFromString(response.content)
        assert received_datanode.node_id == TEST_DATANODE["node_id"]
        assert received_datanode.description == TEST_DATANODE["description"]

    def test_acl_validation(self, gateway_session, dag_manager_session):
        """Gateway ACL 검증과 DAG Manager 권한 전파 테스트"""
        # 인증되지 않은 요청 테스트
        headers = {"Content-Type": "application/x-protobuf"}
        response = requests.get(f"{gateway_session}/api/v1/strategies", headers=headers)
        assert response.status_code == 401

        # 잘못된 권한으로 요청 테스트
        headers = {
            "Content-Type": "application/x-protobuf",
            "Authorization": "Bearer invalid_token",
        }
        response = requests.get(f"{gateway_session}/api/v1/strategies", headers=headers)
        assert response.status_code == 403

        # DAG Manager도 동일한 ACL 정책 적용 확인
        response = requests.get(f"{dag_manager_session}/api/v1/strategies", headers=headers)
        assert response.status_code == 403

    def test_data_serialization_consistency(self, gateway_session, dag_manager_session):
        """Gateway↔DAG Manager 간 protobuf 직렬화/역직렬화 일관성 테스트"""
        # 전략 데이터로 직렬화 테스트
        strategy = qmtl_strategy_pb2.Strategy()
        json_format.Parse(json.dumps(TEST_STRATEGY), strategy)
        serialized = strategy.SerializeToString()

        # Gateway에 전송
        headers = {"Content-Type": "application/x-protobuf"}
        response = requests.post(
            f"{gateway_session}/api/v1/strategies", data=serialized, headers=headers
        )
        assert response.status_code == 201

        # DAG Manager에서 조회
        time.sleep(1)  # 동기화 대기
        response = requests.get(
            f"{dag_manager_session}/api/v1/strategies/{TEST_STRATEGY['strategy_name']}"
        )
        assert response.status_code == 200

        # 역직렬화하여 데이터 일치 확인
        received = qmtl_strategy_pb2.Strategy()
        received.ParseFromString(response.content)

        # 주요 필드 비교
        assert received.strategy_name == strategy.strategy_name
        assert received.description == strategy.description
        assert received.version == strategy.version
        assert list(received.tags) == list(strategy.tags)
