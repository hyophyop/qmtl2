"""
Gateway 인증 미들웨어 테스트

이 모듈은 Gateway 서비스의 인증 미들웨어(auth.py)에 대한 단위 테스트를 포함합니다.
"""

import pytest
import time
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi import HTTPException

from qmtl.gateway.middlewares.auth import JWTConfig, JWTAuthMiddleware, create_access_token


class TestAuthMiddleware:
    """인증 미들웨어 테스트 클래스"""

    @pytest.fixture
    def jwt_config(self):
        """JWT 설정 픽스처"""
        return JWTConfig(
            secret_key="test_secret",
            algorithm="HS256",
            exclude_paths=["/health", "/", "/docs", "/openapi.json"],
        )

    @pytest.fixture
    def auth_middleware(self, jwt_config):
        """인증 미들웨어 픽스처"""
        return JWTAuthMiddleware(jwt_config)

    @pytest.mark.asyncio
    async def test_call_excluded_path(self, auth_middleware):
        """제외 경로 호출 테스트"""
        # Mock 요청 및 콜백
        mock_request = MagicMock()
        mock_request.url.path = "/health"
        # 비동기 함수로 콜백 모킹
        mock_call_next = AsyncMock()
        mock_call_next.return_value = "response"

        # 미들웨어 호출
        response = await auth_middleware(mock_request, mock_call_next)

        # 다음 미들웨어가 호출되었는지 확인
        mock_call_next.assert_called_once_with(mock_request)
        assert response == "response"

    @pytest.mark.asyncio
    async def test_call_read_only_violation(self, auth_middleware):
        """읽기 전용 API 위반 테스트"""
        # Mock 요청 (POST 메서드, 읽기 전용 경로)
        mock_request = MagicMock()
        mock_request.url.path = "/v1/gateway/strategies"
        mock_request.method = "POST"
        mock_call_next = AsyncMock()

        # HTTP 예외가 발생해야 함
        with pytest.raises(HTTPException) as excinfo:
            await auth_middleware(mock_request, mock_call_next)

        # 상태 코드 및 메시지 확인
        assert excinfo.value.status_code == 405
        assert "Only GET requests are allowed" in excinfo.value.detail

    @pytest.mark.asyncio
    async def test_call_no_credentials(self, auth_middleware):
        """인증 정보 없음 테스트"""
        # Mock 요청 (인증 정보 없음)
        mock_request = MagicMock()
        mock_request.url.path = "/v1/gateway/strategies"
        mock_request.method = "GET"
        # Authorization 헤더 추가
        mock_headers = MagicMock()
        mock_headers.get.return_value = None
        mock_request.headers = mock_headers
        mock_call_next = AsyncMock()

        # security 메서드를 패치하여 None 반환
        with patch.object(auth_middleware.security, "__call__", return_value=None):
            # HTTP 예외가 발생해야 함
            with pytest.raises(HTTPException) as excinfo:
                await auth_middleware(mock_request, mock_call_next)

            # 상태 코드 및 메시지 확인
            assert excinfo.value.status_code == 401
            assert "Not authenticated" in excinfo.value.detail

    @pytest.mark.asyncio
    async def test_call_valid_token(self, auth_middleware, jwt_config):
        """유효한 토큰 테스트"""
        # 유효한 토큰 생성
        token_data = {"sub": "test_user", "roles": ["user"]}
        token = create_access_token(token_data, jwt_config.secret_key, jwt_config.algorithm, 3600)

        # Mock 요청 및 인증 정보
        mock_request = MagicMock()
        mock_request.url.path = "/v1/gateway/strategies"
        mock_request.method = "GET"
        # Authorization 헤더 추가
        mock_headers = MagicMock()
        mock_headers.get.return_value = f"Bearer {token}"
        mock_request.headers = mock_headers
        mock_credentials = MagicMock()
        mock_credentials.credentials = token
        mock_call_next = AsyncMock()
        mock_call_next.return_value = "response"

        # security 메서드를 패치하여 mock_credentials 반환
        with patch.object(auth_middleware.security, "__call__", return_value=mock_credentials):
            # 미들웨어 호출
            response = await auth_middleware(mock_request, mock_call_next)

            # 다음 미들웨어가 호출되었는지 확인
            mock_call_next.assert_called_once_with(mock_request)
            assert response == "response"

            # 요청 상태에 사용자 정보가 추가되었는지 확인
            assert hasattr(mock_request.state, "user")
            assert mock_request.state.user["sub"] == "test_user"
            assert "user" in mock_request.state.user["roles"]

    @pytest.mark.asyncio
    async def test_call_expired_token(self, auth_middleware, jwt_config):
        """만료된 토큰 테스트"""
        # 만료된 토큰 생성
        token_data = {"sub": "test_user", "roles": ["user"], "exp": time.time() - 100}
        token = create_access_token(token_data, jwt_config.secret_key, jwt_config.algorithm)

        # Mock 요청 및 인증 정보
        mock_request = MagicMock()
        mock_request.url.path = "/v1/gateway/strategies"
        mock_request.method = "GET"
        # Authorization 헤더 추가
        mock_headers = MagicMock()
        mock_headers.get.return_value = f"Bearer {token}"
        mock_request.headers = mock_headers
        mock_credentials = MagicMock()
        mock_credentials.credentials = token
        mock_call_next = AsyncMock()

        # security 메서드를 패치하여 mock_credentials 반환
        with patch.object(auth_middleware.security, "__call__", return_value=mock_credentials):
            # HTTP 예외가 발생해야 함
            with pytest.raises(HTTPException) as excinfo:
                await auth_middleware(mock_request, mock_call_next)

            # 상태 코드 및 메시지 확인
            assert excinfo.value.status_code == 401
            assert "Invalid authentication credentials" in excinfo.value.detail

    @pytest.mark.asyncio
    async def test_call_invalid_token(self, auth_middleware):
        """잘못된 토큰 테스트"""
        # 잘못된 토큰
        invalid_token = "invalid.token.format"

        # Mock 요청 및 인증 정보
        mock_request = MagicMock()
        mock_request.url.path = "/v1/gateway/strategies"
        mock_request.method = "GET"
        # Authorization 헤더 추가
        mock_headers = MagicMock()
        mock_headers.get.return_value = f"Bearer {invalid_token}"
        mock_request.headers = mock_headers
        mock_credentials = MagicMock()
        mock_credentials.credentials = invalid_token
        mock_call_next = AsyncMock()

        # security 메서드를 패치하여 mock_credentials 반환
        with patch.object(auth_middleware.security, "__call__", return_value=mock_credentials):
            # HTTP 예외가 발생해야 함
            with pytest.raises(HTTPException) as excinfo:
                await auth_middleware(mock_request, mock_call_next)

            # 상태 코드 및 메시지 확인
            assert excinfo.value.status_code == 401
            assert "Invalid authentication credentials" in excinfo.value.detail

    def test_create_access_token(self, jwt_config):
        """액세스 토큰 생성 테스트"""
        # 토큰 데이터
        token_data = {"sub": "test_user", "roles": ["user"]}

        # 만료 시간 있는 토큰 생성
        token = create_access_token(
            token_data, jwt_config.secret_key, jwt_config.algorithm, expires_delta=3600
        )

        # 토큰이 문자열이어야 함
        assert isinstance(token, str)

        # 토큰 디코드 및 검증
        from jose import jwt

        payload = jwt.decode(token, jwt_config.secret_key, algorithms=[jwt_config.algorithm])
        assert payload["sub"] == "test_user"
        assert "user" in payload["roles"]
        assert "exp" in payload
