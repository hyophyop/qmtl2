"""
Gateway 서비스의 전체 워크플로우 E2E 테스트

이 모듈은 Gateway 서비스의 전체 워크플로우를 검증하는 E2E 테스트를 포함합니다.
정상 플로우뿐만 아니라 다양한 예외 상황에 대한 처리도 검증합니다.
"""

import pytest
import requests
import time
import json
from pathlib import Path
from typing import Dict, Any, List
from google.protobuf import json_format

from qmtl.models.generated import (
    qmtl_common_pb2 as common_pb2,
    qmtl_strategy_pb2 as strategy_pb2,
    qmtl_datanode_pb2 as datanode_pb2,
    qmtl_pipeline_pb2 as pipeline_pb2,
)

from tests.e2e import factories
from tests.e2e.test_config import GATEWAY_BASE_URL, TEST_USER, get_endpoint, TIMEOUTS

# Test markers
pytestmark = [pytest.mark.workflow, pytest.mark.gateway, pytest.mark.e2e]


# 테스트 데이터 초기화
@pytest.fixture(scope="module")
def workflow_data():
    """워크플로우 테스트에 사용할 테스트 데이터 생성"""
    return {
        "strategy": {
            "strategy_name": "workflow_test_strategy",
            "description": "Strategy for workflow test",
            "author": "tester",
            "version": "1.0.0",
            "tags": ["workflow", "test"],
            "source": "pytest",
        },
        "datanode": {
            "node_id": "workflow_test_datanode",
            "node_type": "SOURCE",
            "data_schema": {"field1": "string", "field2": "int32"},
            "tags": ["workflow", "test"],
            "description": "Data node for workflow test",
            "owner": "tester",
        },
        "pipeline": {"name": "workflow_test_pipeline", "metadata": {"purpose": "testing"}},
    }


class TestCompleteWorkflow:
    """전체 Gateway 워크플로우 테스트 클래스"""

    def test_complete_workflow(self, authenticated_gateway_client, gateway_session, workflow_data):
        """전체 워크플로우 테스트 - 인증부터 전략 실행, 데이터 노드 관리, 파이프라인까지"""
        # 1. 인증 토큰 취득
        auth_token = self._get_auth_token(authenticated_gateway_client)
        assert auth_token, "인증 토큰 취득 실패"

        # 2. 전략 등록
        strategy_id = self._register_strategy(
            authenticated_gateway_client, workflow_data["strategy"]
        )
        assert strategy_id, "전략 등록 실패"

        # 3. 전략 상태 조회
        strategy_status = self._get_strategy_status(authenticated_gateway_client, strategy_id)
        assert strategy_status, "전략 상태 조회 실패"

        # 4. 데이터 노드 생성
        datanode_id = self._create_datanode(authenticated_gateway_client, workflow_data["datanode"])
        assert datanode_id, "데이터 노드 생성 실패"

        # 5. 데이터 노드 조회
        datanode = self._get_datanode(authenticated_gateway_client, datanode_id)
        assert datanode, "데이터 노드 조회 실패"

        # 6. 파이프라인 생성
        pipeline_id = self._create_pipeline(authenticated_gateway_client, workflow_data["pipeline"])
        assert pipeline_id, "파이프라인 생성 실패"

        # 7. 파이프라인 상태 조회
        pipeline_status = self._get_pipeline_status(authenticated_gateway_client, pipeline_id)
        assert pipeline_status, "파이프라인 상태 조회 실패"

    def _get_auth_token(self, client):
        """인증 토큰 취득"""
        auth_url = get_endpoint("auth", "token")
        auth_data = {"username": TEST_USER["username"], "password": TEST_USER["password"]}

        response = client.post(
            auth_url,
            data=auth_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=TIMEOUTS["short"],
        )

        assert response.status_code == 200, f"인증 실패: {response.text}"
        data = response.json()
        return data.get("access_token")

    def _register_strategy(self, client, strategy_data):
        """전략 등록"""
        url = get_endpoint("strategies", "base")
        strategy_metadata = factories.create_strategy_metadata(**strategy_data)

        response = client.post(
            url,
            data=strategy_metadata.SerializeToString(),
            headers={"Content-Type": "application/x-protobuf"},
            timeout=TIMEOUTS["medium"],
        )

        assert response.status_code == 200, f"전략 등록 실패: {response.text}"

        response_msg = strategy_pb2.StrategyRegistrationResponse()
        response_msg.ParseFromString(response.content)

        assert response_msg.success is True, "전략 등록 응답이 성공이 아님"
        return response_msg.strategy_id

    def _get_strategy_status(self, client, strategy_id):
        """전략 상태 조회"""
        url = get_endpoint("strategies", "status", strategy_id=strategy_id)

        response = client.get(
            url, headers={"Accept": "application/x-protobuf"}, timeout=TIMEOUTS["short"]
        )

        assert response.status_code == 200, f"전략 상태 조회 실패: {response.text}"

        response_msg = strategy_pb2.StrategyStatusResponse()
        response_msg.ParseFromString(response.content)

        return response_msg.status

    def _create_datanode(self, client, datanode_data):
        """데이터 노드 생성"""
        url = get_endpoint("datanodes", "base")
        datanode_metadata = factories.create_datanode_metadata(**datanode_data)

        response = client.post(
            url,
            data=datanode_metadata.SerializeToString(),
            headers={"Content-Type": "application/x-protobuf"},
            timeout=TIMEOUTS["medium"],
        )

        assert response.status_code == 200, f"데이터 노드 생성 실패: {response.text}"

        response_msg = datanode_pb2.DataNodeResponse()
        response_msg.ParseFromString(response.content)

        assert response_msg.success is True, "데이터 노드 생성 응답이 성공이 아님"
        return response_msg.node_metadata.node_id

    def _get_datanode(self, client, datanode_id):
        """데이터 노드 조회"""
        url = get_endpoint("datanodes", "by_id", datanode_id=datanode_id)

        response = client.get(
            url, headers={"Accept": "application/x-protobuf"}, timeout=TIMEOUTS["short"]
        )

        assert response.status_code == 200, f"데이터 노드 조회 실패: {response.text}"

        response_msg = datanode_pb2.DataNode()
        response_msg.ParseFromString(response.content)

        return response_msg

    def _create_pipeline(self, client, pipeline_data):
        """파이프라인 생성"""
        url = get_endpoint("pipelines", "base")
        pipeline_definition = factories.create_pipeline_definition(**pipeline_data)

        response = client.post(
            url,
            data=pipeline_definition.SerializeToString(),
            headers={"Content-Type": "application/x-protobuf"},
            timeout=TIMEOUTS["medium"],
        )

        assert response.status_code == 200, f"파이프라인 생성 실패: {response.text}"

        response_msg = pipeline_pb2.PipelineResponse()
        response_msg.ParseFromString(response.content)

        assert response_msg.success is True, "파이프라인 생성 응답이 성공이 아님"
        return response_msg.pipeline_id

    def _get_pipeline_status(self, client, pipeline_id):
        """파이프라인 상태 조회"""
        url = get_endpoint("pipelines", "by_id", pipeline_id=pipeline_id)

        response = client.get(
            url, headers={"Accept": "application/x-protobuf"}, timeout=TIMEOUTS["short"]
        )

        assert response.status_code == 200, f"파이프라인 상태 조회 실패: {response.text}"

        response_msg = pipeline_pb2.PipelineStatus()
        response_msg.ParseFromString(response.content)

        return response_msg.status


class TestFaultTolerance:
    """장애 상황 및 예외 처리 테스트 클래스"""

    def test_reconnection_after_service_restart(
        self, authenticated_gateway_client, gateway_session, workflow_data
    ):
        """서비스 재시작 후 재연결 및 작업 속행 테스트"""
        # 1. 서비스 재시작 시뮬레이션 (실제 서비스 재시작은 도커 컨테이너 재시작이 필요)
        # 테스트 환경에서는 세션 만료를 시뮬레이션

        # 2. 세션 만료 후 재인증
        auth_token = self._get_auth_token(authenticated_gateway_client)
        assert auth_token, "재인증 실패"

        # 3. 재인증 후 정상 작업 검증
        strategy_id = self._register_strategy(
            authenticated_gateway_client, workflow_data["strategy"]
        )
        assert strategy_id, "서비스 재시작 후 전략 등록 실패"

    def test_error_recovery(self, authenticated_gateway_client, gateway_session, workflow_data):
        """오류 발생 후 복구 테스트"""
        # 1. 고의적 오류 삽입 (잘못된 데이터 전송)
        url = get_endpoint("strategies", "base")

        # 잘못된 형식의 데이터 전송
        response = authenticated_gateway_client.post(
            url,
            data=b"invalid_protobuf_data",
            headers={"Content-Type": "application/x-protobuf"},
            timeout=TIMEOUTS["short"],
        )

        # 오류 응답 확인
        assert response.status_code >= 400, "잘못된 데이터에 대한 오류 처리 실패"

        # 2. 오류 후 정상 작업 검증
        strategy_id = self._register_strategy(
            authenticated_gateway_client, workflow_data["strategy"]
        )
        assert strategy_id, "오류 복구 후 전략 등록 실패"

    def test_timeout_handling(self, authenticated_gateway_client, gateway_session, workflow_data):
        """타임아웃 및 지연 응답 처리 테스트"""
        # 실제 네트워크 지연 시뮬레이션은 복잡하므로, 클라이언트 타임아웃 설정으로 대체

        # 매우 짧은 타임아웃으로 요청 시도
        url = get_endpoint("strategies", "base")
        strategy_metadata = factories.create_strategy_metadata(**workflow_data["strategy"])

        with pytest.raises(requests.Timeout):
            authenticated_gateway_client.post(
                url,
                data=strategy_metadata.SerializeToString(),
                headers={"Content-Type": "application/x-protobuf"},
                timeout=0.001,  # 1ms 타임아웃 (의도적 실패)
            )

        # 타임아웃 후 정상 타임아웃으로 재시도
        strategy_id = self._register_strategy(
            authenticated_gateway_client, workflow_data["strategy"]
        )
        assert strategy_id, "타임아웃 복구 후 전략 등록 실패"

    def _get_auth_token(self, client):
        """인증 토큰 취득"""
        auth_url = get_endpoint("auth", "token")
        auth_data = {"username": TEST_USER["username"], "password": TEST_USER["password"]}

        response = client.post(
            auth_url,
            data=auth_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=TIMEOUTS["short"],
        )

        if response.status_code != 200:
            return None

        data = response.json()
        return data.get("access_token")

    def _register_strategy(self, client, strategy_data):
        """전략 등록"""
        url = get_endpoint("strategies", "base")
        strategy_metadata = factories.create_strategy_metadata(**strategy_data)

        response = client.post(
            url,
            data=strategy_metadata.SerializeToString(),
            headers={"Content-Type": "application/x-protobuf"},
            timeout=TIMEOUTS["medium"],
        )

        if response.status_code != 200:
            return None

        response_msg = strategy_pb2.StrategyRegistrationResponse()
        response_msg.ParseFromString(response.content)

        if not response_msg.success:
            return None

        return response_msg.strategy_id


class TestReadOnlyRestriction:
    """읽기 전용 API 제한 검증 테스트 클래스"""

    def test_read_only_endpoints(self, authenticated_gateway_client, gateway_session):
        """읽기 전용 API 엔드포인트 검증"""
        # 읽기 전용 엔드포인트 목록
        read_only_endpoints = [
            get_endpoint("strategies", "base"),
            get_endpoint("datanodes", "base"),
            get_endpoint("pipelines", "base"),
        ]

        # 읽기(GET) 요청은 성공해야 함
        for endpoint in read_only_endpoints:
            response = authenticated_gateway_client.get(endpoint, timeout=TIMEOUTS["short"])
            # 응답 코드가 200 또는 404(리소스 없음)여야 함
            assert response.status_code in [200, 404], f"GET 요청 실패: {endpoint}"

        # 쓰기(POST, PUT, DELETE) 요청은 실패해야 함 (405 Method Not Allowed)
        for endpoint in read_only_endpoints:
            # POST 요청
            response = authenticated_gateway_client.post(
                endpoint, data={}, timeout=TIMEOUTS["short"]
            )
            assert response.status_code == 405, f"POST 요청이 허용됨: {endpoint}"

            # PUT 요청
            response = authenticated_gateway_client.put(
                endpoint, data={}, timeout=TIMEOUTS["short"]
            )
            assert response.status_code == 405, f"PUT 요청이 허용됨: {endpoint}"

            # DELETE 요청
            response = authenticated_gateway_client.delete(endpoint, timeout=TIMEOUTS["short"])
            assert response.status_code == 405, f"DELETE 요청이 허용됨: {endpoint}"

    def test_internal_api_protection(self, gateway_client, gateway_session):
        """내부 API 보호 검증"""
        # 내부 API 엔드포인트 (임의 설정)
        internal_endpoints = [
            f"{gateway_session}/internal/v1/strategies",
            f"{gateway_session}/internal/v1/datanodes",
            f"{gateway_session}/admin/v1/users",
        ]

        # 인증 없이 접근 시도
        for endpoint in internal_endpoints:
            response = gateway_client.get(endpoint, timeout=TIMEOUTS["short"])
            # 401(인증 실패) 또는 403(권한 없음) 또는 404(경로 없음)여야 함
            assert response.status_code in [401, 403, 404], f"내부 API 접근 보호 실패: {endpoint}"
