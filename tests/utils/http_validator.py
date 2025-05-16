"""
HTTP 요청 검증 유틸리티 - 테스트 코드의 HTTP 요청 파라미터를 검증하는 도구
"""

from typing import Any, Dict

import httpx
from fastapi.testclient import TestClient

from qmtl.common.http.client import HTTPClient


class HttpParameterValidator:
    """
    HTTP 요청 파라미터 검증기

    테스트 코드에서 HTTP 요청 시 올바른 파라미터를 사용하는지 검증합니다.
    특히 json_content와 같은 잘못된 파라미터 대신 json을 사용하는지 확인합니다.
    """

    DEPRECATED_PARAMS = {
        "json_content": "json",  # 잘못된 파라미터 => 올바른 파라미터
        "content": "data",
    }

    REQUIRED_HTTP_LIBS = [httpx, TestClient, HTTPClient]

    @classmethod
    def validate_request_params(cls, params: Dict[str, Any]) -> bool:
        """
        HTTP 요청 파라미터가 올바른지 검증

        Args:
            params: 검증할 HTTP 요청 파라미터 딕셔너리

        Returns:
            bool: 요청 파라미터가 유효한지 여부

        Raises:
            ValueError: 잘못된 파라미터가 발견된 경우
        """
        for bad_param, good_param in cls.DEPRECATED_PARAMS.items():
            if bad_param in params:
                raise ValueError(
                    f"HTTP 요청에 잘못된 파라미터 '{bad_param}'가 사용되었습니다. "
                    f"대신 '{good_param}'를 사용하세요."
                )
        return True

    @classmethod
    def patch_client(cls, client_obj: Any) -> None:
        """
        HTTP 클라이언트 객체의 request 메서드를 패치하여 파라미터 검증 추가

        Args:
            client_obj: 패치할 HTTP 클라이언트 객체
        """
        original_request = client_obj.request

        def validated_request(*args, **kwargs):
            cls.validate_request_params(kwargs)
            return original_request(*args, **kwargs)

        client_obj.request = validated_request

    @classmethod
    def wrap_test_client(cls, client: TestClient) -> TestClient:
        """
        FastAPI TestClient를 래핑하여 모든 요청 메서드(get, post 등)에
        파라미터 검증 로직 추가

        Args:
            client: 원본 TestClient 객체

        Returns:
            TestClient: 검증 로직이 추가된 TestClient 객체
        """
        for method_name in ["get", "post", "put", "delete", "patch", "request"]:
            if hasattr(client, method_name):
                original_method = getattr(client, method_name)

                def make_wrapped_method(orig_method):
                    def wrapped_method(*args, **kwargs):
                        # json_content 대신 json 사용 검증
                        if "json_content" in kwargs:
                            raise ValueError(
                                "TestClient에서 'json_content' 대신 'json'을 사용하세요."
                            )
                        return orig_method(*args, **kwargs)

                    return wrapped_method

                setattr(client, method_name, make_wrapped_method(original_method))

        return client


def create_validated_test_client(app) -> TestClient:
    """
    파라미터 검증이 포함된 TestClient 생성

    Args:
        app: FastAPI 애플리케이션 객체

    Returns:
        TestClient: 검증 로직이 추가된 TestClient 객체
    """
    client = TestClient(app)
    return HttpParameterValidator.wrap_test_client(client)
