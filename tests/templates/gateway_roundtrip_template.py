"""
Gateway 라운드트립 테스트 템플릿

이 모듈은 Gateway 서비스에서 사용할 수 있는 protobuf 라운드트립 테스트 템플릿을 제공합니다.
"""

import pytest
from typing import Any, Dict, Optional, Type, TypeVar
from google.protobuf.message import Message

# 타입 정의
T = TypeVar("T", bound=Message)


def basic_roundtrip_test(
    message_obj: Message,
    client_fixture: Any,
    endpoint: str,
    response_cls: Type[Message],
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 5,
) -> Message:
    """
    기본 프로토버프 라운드트립 테스트 함수

    Args:
        message_obj: 테스트할 프로토버프 메시지 객체
        client_fixture: 테스트 클라이언트 픽스처
        endpoint: 테스트할 엔드포인트
        response_cls: 응답 메시지 클래스
        headers: 요청 헤더 (기본값은 application/x-protobuf)
        timeout: 요청 타임아웃 (초)

    Returns:
        Message: 응답으로 받은 프로토버프 메시지 객체

    Examples:
        >>> strategy = factories.create_strategy_metadata(strategy_name="test")
        >>> response = basic_roundtrip_test(
        ...     message_obj=strategy,
        ...     client_fixture=authenticated_gateway_client,
        ...     endpoint="/api/v1/strategies",
        ...     response_cls=strategy_pb2.StrategyRegistrationResponse
        ... )
        >>> assert response.success
    """
    # 기본 헤더 설정
    if headers is None:
        headers = {"Content-Type": "application/x-protobuf", "Accept": "application/x-protobuf"}

    # 메시지 직렬화 및 전송
    serialized_data = message_obj.SerializeToString()
    response = client_fixture.post(endpoint, data=serialized_data, headers=headers, timeout=timeout)

    # 응답 검증
    assert (
        response.status_code == 200
    ), f"Status code must be 200, got {response.status_code}: {response.text}"

    # 응답 역직렬화
    response_obj = response_cls()
    response_obj.ParseFromString(response.content)

    return response_obj


def retrieve_roundtrip_test(
    resource_id: str,
    client_fixture: Any,
    endpoint: str,
    response_cls: Type[T],
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 5,
) -> T:
    """
    리소스 조회 프로토버프 라운드트립 테스트 함수

    Args:
        resource_id: 조회할 리소스 ID
        client_fixture: 테스트 클라이언트 픽스처
        endpoint: 테스트할 엔드포인트 (리소스 ID 포함)
        response_cls: 응답 메시지 클래스
        headers: 요청 헤더 (기본값은 application/x-protobuf)
        timeout: 요청 타임아웃 (초)

    Returns:
        T: 응답으로 받은 프로토버프 메시지 객체

    Examples:
        >>> response = retrieve_roundtrip_test(
        ...     resource_id="test_strategy_1",
        ...     client_fixture=authenticated_gateway_client,
        ...     endpoint="/api/v1/strategies/test_strategy_1",
        ...     response_cls=strategy_pb2.StrategyMetadata
        ... )
        >>> assert response.strategy_name == "test_strategy_1"
    """
    # 기본 헤더 설정
    if headers is None:
        headers = {"Accept": "application/x-protobuf"}

    # GET 요청 전송
    response = client_fixture.get(endpoint, headers=headers, timeout=timeout)

    # 응답 검증
    assert (
        response.status_code == 200
    ), f"Status code must be 200, got {response.status_code}: {response.text}"

    # 응답 역직렬화
    response_obj = response_cls()
    response_obj.ParseFromString(response.content)

    return response_obj


def compare_proto_objects(
    original: Message, retrieved: Message, fields_to_compare: Optional[list] = None
) -> bool:
    """
    두 프로토버프 객체 비교 함수

    Args:
        original: 원본 프로토버프 객체
        retrieved: 조회된 프로토버프 객체
        fields_to_compare: 비교할 필드 목록 (None이면 모든 필드 비교)

    Returns:
        bool: 두 객체가 동일하면 True, 아니면 False

    Examples:
        >>> original = factories.create_strategy_metadata(strategy_name="test")
        >>> retrieved = retrieve_roundtrip_test(...)
        >>> assert compare_proto_objects(original, retrieved, ["strategy_name", "version"])
    """
    # 필드 목록이 지정되지 않은 경우, 모든 필드 비교
    if fields_to_compare is None:
        # ListFields()는 값이 설정된 필드만 반환
        original_fields = {field[0].name for field in original.ListFields()}
        retrieved_fields = {field[0].name for field in retrieved.ListFields()}

        # 설정된 필드 목록이 동일한지 확인
        if original_fields != retrieved_fields:
            print(f"Field sets don't match: {original_fields} vs {retrieved_fields}")
            return False

        fields_to_compare = list(original_fields)

    # 지정된 필드들에 대해 값 비교
    for field in fields_to_compare:
        original_value = getattr(original, field)
        retrieved_value = getattr(retrieved, field)

        # 반복 필드는 목록으로 변환하여 비교
        if hasattr(original_value, "__iter__") and not isinstance(original_value, (str, bytes)):
            original_value = list(original_value)
            retrieved_value = list(retrieved_value)

        if original_value != retrieved_value:
            print(f"Field {field} doesn't match: {original_value} vs {retrieved_value}")
            return False

    return True


# 템플릿 테스트 예시
class TemplateGatewayRoundtripTests:
    """Gateway 라운드트립 테스트 템플릿 클래스"""

    @pytest.mark.template
    def test_strategy_roundtrip_template(self, authenticated_gateway_client):
        """전략 라운드트립 테스트 템플릿"""
        # 이 테스트는 실행되지 않음, 단지 템플릿으로만 사용
        pytest.skip("This is just a template test")

        # 테스트에서 사용할 데이터 및 함수
        from qmtl.models.generated import qmtl_strategy_pb2 as strategy_pb2
        from tests.e2e import factories
        from tests.e2e.test_config import get_endpoint

        # 1. 테스트 데이터 생성
        strategy_data = {
            "strategy_name": "roundtrip_template_strategy",
            "description": "Strategy for roundtrip template test",
            "version": "1.0.0",
        }
        strategy = factories.create_strategy_metadata(**strategy_data)

        # 2. 리소스 생성 요청
        create_url = get_endpoint("strategies", "base")
        response = basic_roundtrip_test(
            message_obj=strategy,
            client_fixture=authenticated_gateway_client,
            endpoint=create_url,
            response_cls=strategy_pb2.StrategyRegistrationResponse,
        )

        # 3. 응답 확인
        assert response.success, "Strategy creation failed"
        strategy_id = response.strategy_id

        # 4. 리소스 조회 요청
        retrieve_url = get_endpoint("strategies", "by_id", strategy_id=strategy_id)
        retrieved_strategy = retrieve_roundtrip_test(
            resource_id=strategy_id,
            client_fixture=authenticated_gateway_client,
            endpoint=retrieve_url,
            response_cls=strategy_pb2.StrategyMetadata,
        )

        # 5. 원본과 조회 결과 비교
        assert compare_proto_objects(
            strategy, retrieved_strategy, ["strategy_name", "description", "version"]
        ), "Original and retrieved strategy objects don't match"
