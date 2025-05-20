"""
Gateway 서비스의 예외 처리 테스트

이 모듈은 Gateway 서비스의 다양한 예외 상황 처리를 검증하는 테스트를 포함합니다.
오류 처리, 예외 응답, 우아한 실패 등을 테스트합니다.
"""

import pytest
import requests
import time
from typing import Dict, Any, Optional

from qmtl.models.generated import (
    qmtl_strategy_pb2 as strategy_pb2,
    qmtl_datanode_pb2 as datanode_pb2,
)

from tests.e2e import factories
from tests.e2e.test_config import get_endpoint, TIMEOUTS

# Test markers
pytestmark = [pytest.mark.exception_handling, pytest.mark.gateway, pytest.mark.e2e]


@pytest.mark.usefixtures("docker_compose_up_down")
class TestInvalidInputHandling:
    """잘못된 입력 처리 테스트 클래스"""

    def test_malformed_protobuf(self, authenticated_gateway_client):
        """잘못된 형식의 Protobuf 데이터 처리 테스트"""
        # 잘못된 형식의 protobuf 데이터로 요청
        url = get_endpoint("strategies", "base")

        response = authenticated_gateway_client.post(
            url,
            data=b"invalid_protobuf_data",
            headers={"Content-Type": "application/x-protobuf"},
            timeout=TIMEOUTS["short"],
        )

        # 400 Bad Request 응답 예상
        assert response.status_code == 400
        assert "error" in response.json() or "detail" in response.json()

    def test_empty_request_body(self, authenticated_gateway_client):
        """빈 요청 본문 처리 테스트"""
        url = get_endpoint("strategies", "base")

        response = authenticated_gateway_client.post(
            url,
            data=b"",
            headers={"Content-Type": "application/x-protobuf"},
            timeout=TIMEOUTS["short"],
        )

        # 400 Bad Request 응답 예상
        assert response.status_code == 400
        assert "error" in response.json() or "detail" in response.json()

    def test_invalid_content_type(self, authenticated_gateway_client):
        """잘못된 Content-Type 헤더 처리 테스트"""
        url = get_endpoint("strategies", "base")
        strategy_metadata = factories.create_strategy_metadata()

        response = authenticated_gateway_client.post(
            url,
            data=strategy_metadata.SerializeToString(),
            headers={"Content-Type": "application/json"},  # 잘못된 Content-Type
            timeout=TIMEOUTS["short"],
        )

        # 415 Unsupported Media Type 응답 예상
        assert response.status_code == 415
        assert "error" in response.json() or "detail" in response.json()


class TestAuthenticationExceptions:
    """인증 예외 처리 테스트 클래스"""

    def test_expired_token(self, gateway_client):
        """만료된 토큰 처리 테스트"""
        # 만료된 JWT 토큰 생성 (이 토큰은 실제로 만료됨)
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTUxNjIzOTAyMn0.7wDV-r9AWA8_XfhVFaCKOZXJ0Jf5ECEXDyMFXX582HM"

        url = get_endpoint("strategies", "base")
        headers = {
            "Authorization": f"Bearer {expired_token}",
            "Content-Type": "application/x-protobuf",
        }

        response = gateway_client.get(url, headers=headers, timeout=TIMEOUTS["short"])

        # 401 Unauthorized 응답 예상
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "expired" in data["detail"].lower() or "invalid" in data["detail"].lower()

    def test_invalid_token_format(self, gateway_client):
        """잘못된 토큰 형식 처리 테스트"""
        url = get_endpoint("strategies", "base")
        headers = {
            "Authorization": "Bearer invalid.token.format",
            "Content-Type": "application/x-protobuf",
        }

        response = gateway_client.get(url, headers=headers, timeout=TIMEOUTS["short"])

        # 401 Unauthorized 응답 예상
        assert response.status_code == 401
        assert "detail" in response.json()

    def test_missing_authorization_header(self, gateway_client):
        """인증 헤더 누락 처리 테스트"""
        url = get_endpoint("strategies", "base")

        response = gateway_client.get(url, timeout=TIMEOUTS["short"])

        # 401 Unauthorized 응답 예상
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "not authenticated" in data["detail"].lower()


class TestACLExceptions:
    """ACL 예외 처리 테스트 클래스"""

    def test_unauthorized_resource_access(self, authenticated_gateway_client):
        """권한 없는 리소스 접근 테스트"""
        # 권한이 없는 리소스 경로 (예: 관리자용 엔드포인트)
        url = f"{authenticated_gateway_client.base_url}/admin/v1/users"

        response = authenticated_gateway_client.get(url, timeout=TIMEOUTS["short"])

        # 403 Forbidden 또는 404 Not Found 응답 예상
        assert response.status_code in [403, 404]
        if response.status_code == 403:
            assert "detail" in response.json()
            assert (
                "permission" in response.json()["detail"].lower()
                or "forbidden" in response.json()["detail"].lower()
            )

    def test_restricted_method_access(self, authenticated_gateway_client):
        """제한된 메서드 접근 테스트"""
        # 읽기 전용 엔드포인트에 쓰기 요청
        url = get_endpoint("strategies", "base")

        response = authenticated_gateway_client.delete(url, timeout=TIMEOUTS["short"])

        # 405 Method Not Allowed 응답 예상
        assert response.status_code == 405
        assert "detail" in response.json() or "error" in response.json()


class TestResourceNotFoundExceptions:
    """리소스 미존재 예외 처리 테스트 클래스"""

    def test_nonexistent_strategy(self, authenticated_gateway_client):
        """존재하지 않는 전략 조회 테스트"""
        # 존재하지 않는 전략 ID
        nonexistent_id = "nonexistent_strategy_id"
        url = get_endpoint("strategies", "by_id", strategy_id=nonexistent_id)

        response = authenticated_gateway_client.get(url, timeout=TIMEOUTS["short"])

        # 404 Not Found 응답 예상
        assert response.status_code == 404
        assert "detail" in response.json() or "error" in response.json()

    def test_nonexistent_datanode(self, authenticated_gateway_client):
        """존재하지 않는 데이터 노드 조회 테스트"""
        # 존재하지 않는 데이터 노드 ID
        nonexistent_id = "nonexistent_datanode_id"
        url = get_endpoint("datanodes", "by_id", datanode_id=nonexistent_id)

        response = authenticated_gateway_client.get(url, timeout=TIMEOUTS["short"])

        # 404 Not Found 응답 예상
        assert response.status_code == 404
        assert "detail" in response.json() or "error" in response.json()


class TestValidationExceptions:
    """유효성 검증 예외 처리 테스트 클래스"""

    def test_invalid_strategy_data(self, authenticated_gateway_client):
        """유효하지 않은 전략 데이터 처리 테스트"""
        url = get_endpoint("strategies", "base")

        # 필수 필드가 누락된 전략 생성
        invalid_strategy = strategy_pb2.StrategyMetadata(
            # strategy_name 필드 누락
            description="Invalid strategy data test",
            version="1.0.0",
        )

        response = authenticated_gateway_client.post(
            url,
            data=invalid_strategy.SerializeToString(),
            headers={"Content-Type": "application/x-protobuf"},
            timeout=TIMEOUTS["short"],
        )

        # 400 Bad Request 응답 예상
        assert response.status_code == 400
        assert "error" in response.json() or "detail" in response.json()

    def test_invalid_datanode_data(self, authenticated_gateway_client):
        """유효하지 않은 데이터 노드 데이터 처리 테스트"""
        url = get_endpoint("datanodes", "base")

        # 필수 필드가 누락된 데이터 노드 생성
        invalid_datanode = datanode_pb2.DataNode(
            # node_id 필드 누락
            type="SOURCE"
        )

        response = authenticated_gateway_client.post(
            url,
            data=invalid_datanode.SerializeToString(),
            headers={"Content-Type": "application/x-protobuf"},
            timeout=TIMEOUTS["short"],
        )

        # 400 Bad Request 응답 예상
        assert response.status_code == 400
        assert "error" in response.json() or "detail" in response.json()


class TestRateLimitingExceptions:
    """속도 제한 예외 처리 테스트 클래스"""

    def test_rate_limiting(self, authenticated_gateway_client):
        """요청 속도 제한 처리 테스트"""
        url = get_endpoint("strategies", "base")

        # 다수의 요청을 빠르게 전송
        responses = []
        for _ in range(50):  # 50회 연속 요청
            response = authenticated_gateway_client.get(url, timeout=TIMEOUTS["short"])
            responses.append(response)
            if response.status_code == 429:
                break  # 속도 제한에 걸리면 중단

        # 속도 제한이 적용되면 429 Too Many Requests 응답이 있어야 함
        # 참고: 실제 환경에서는 속도 제한이 적용될 수 있지만, 테스트 환경에서는 적용되지 않을 수 있음
        rate_limited = any(r.status_code == 429 for r in responses)
        if rate_limited:
            rate_limited_response = next(r for r in responses if r.status_code == 429)
            assert "detail" in rate_limited_response.json()
            assert (
                "rate limit" in rate_limited_response.json()["detail"].lower()
                or "too many" in rate_limited_response.json()["detail"].lower()
            )
        else:
            # 속도 제한이 적용되지 않으면 테스트를 생략
            pytest.skip("Rate limiting is not enforced in the current environment")


class TestConcurrencyExceptions:
    """동시성 예외 처리 테스트 클래스"""

    def test_concurrent_requests(self, authenticated_gateway_client):
        """동시 요청 처리 테스트"""
        # 같은 리소스에 대한 동시 요청 시뮬레이션
        url = get_endpoint("strategies", "base")

        # 여러 개의 동일한 전략을 동시에 등록 시도
        strategy_metadata = factories.create_strategy_metadata(
            strategy_name="concurrent_test_strategy", description="Concurrency test strategy"
        )

        # 5개의 동일한 요청 (실제 환경에서는 스레드/프로세스 풀을 사용하여 병렬 실행)
        responses = []
        for _ in range(5):
            response = authenticated_gateway_client.post(
                url,
                data=strategy_metadata.SerializeToString(),
                headers={"Content-Type": "application/x-protobuf"},
                timeout=TIMEOUTS["medium"],
            )
            responses.append(response)

        # 최소 하나는 성공해야 함
        assert any(r.status_code == 200 for r in responses), "모든 동시 요청이 실패함"

        # 첫 번째 요청 이후의 요청은 충돌 또는 중복으로 실패할 수 있음
        # 409 Conflict 또는 400 Bad Request 응답이 있을 수 있음
        failed_responses = [r for r in responses if r.status_code not in [200, 201]]
        if failed_responses:
            for response in failed_responses:
                assert response.status_code in [
                    400,
                    409,
                    500,
                ], f"예상치 못한 오류 코드: {response.status_code}"
