"""
Gateway 에러 처리 미들웨어 테스트

이 모듈은 Gateway 서비스의 에러 처리 미들웨어(error.py)에 대한 단위 테스트를 포함합니다.
"""

import pytest
import json
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException

from qmtl.gateway.middlewares.error import ErrorHandlingMiddleware


class TestErrorHandlingMiddleware:
    """에러 처리 미들웨어 테스트 클래스"""

    @pytest.fixture
    def error_middleware(self):
        """에러 처리 미들웨어 픽스처"""
        return ErrorHandlingMiddleware()

    @pytest.mark.asyncio
    async def test_handle_http_exception(self, error_middleware):
        """HTTP 예외 처리 테스트"""
        # 모의 요청 객체
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/test/path"
        mock_request.method = "GET"
        # 요청 ID가 없는 경우
        mock_request.state = MagicMock()
        (
            delattr(mock_request.state, "request_id")
            if hasattr(mock_request.state, "request_id")
            else None
        )

        # HTTP 예외
        http_exc = HTTPException(status_code=404, detail="Resource not found")

        # 예외 처리
        response = error_middleware._handle_http_exception(mock_request, http_exc)

        # 응답 검증
        assert isinstance(response, JSONResponse)
        assert response.status_code == 404

        # 응답 내용 확인
        content = json.loads(response.body)
        assert content["detail"] == "Resource not found"

    @pytest.mark.asyncio
    async def test_handle_validation_error(self, error_middleware):
        """요청 유효성 검증 예외 처리 테스트"""
        # 모의 요청 객체
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/test/path"
        mock_request.method = "POST"

        # 유효성 검증 예외
        val_exc = RequestValidationError(
            errors=[{"loc": ["body", "field"], "msg": "Field required"}]
        )

        # 예외 처리
        response = error_middleware._handle_validation_error(mock_request, val_exc)

        # 응답 검증
        assert isinstance(response, JSONResponse)
        assert response.status_code == 422

        # 응답 내용 확인
        content = json.loads(response.body)
        assert content["detail"] == "Request validation error"
        assert "errors" in content
        assert isinstance(content["errors"], list)

    @pytest.mark.asyncio
    async def test_handle_server_error(self, error_middleware):
        """서버 오류 처리 테스트"""
        # 모의 요청 객체
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/test/path"
        mock_request.method = "GET"

        # 서버 오류
        exc = ValueError("Unexpected server error")

        # 예외 처리
        response = error_middleware._handle_server_error(mock_request, exc)

        # 응답 검증
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500

        # 응답 내용 확인
        content = json.loads(response.body)
        assert content["detail"] == "Internal server error"

    @pytest.mark.asyncio
    async def test_middleware_call_success(self, error_middleware):
        """미들웨어 호출 성공 테스트"""
        # 모의 요청 객체
        mock_request = MagicMock(spec=Request)

        # 모의 응답 객체
        mock_response = MagicMock(spec=Response)

        # 다음 미들웨어 호출 함수
        mock_call_next = AsyncMock()
        mock_call_next.return_value = mock_response

        # 미들웨어 호출
        response = await error_middleware(mock_request, mock_call_next)

        # 응답 검증
        assert response == mock_response

    @pytest.mark.asyncio
    async def test_middleware_call_http_exception(self, error_middleware):
        """미들웨어 HTTP 예외 처리 테스트"""
        # 모의 요청 객체
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/test/path"
        mock_request.method = "GET"

        # HTTP 예외를 발생시키는 다음 미들웨어 호출 함수
        mock_call_next = AsyncMock()
        mock_call_next.side_effect = HTTPException(status_code=403, detail="Forbidden")

        # 미들웨어 호출
        with patch.object(error_middleware, "_handle_http_exception") as mock_handler:
            mock_handler.return_value = JSONResponse(
                status_code=403, content={"detail": "Forbidden"}
            )
            await error_middleware(mock_request, mock_call_next)

            # 핸들러 호출 확인
            mock_handler.assert_called_once()
            args, kwargs = mock_handler.call_args
            assert args[0] == mock_request
            assert isinstance(args[1], HTTPException)
            assert args[1].status_code == 403
            assert args[1].detail == "Forbidden"

    @pytest.mark.asyncio
    async def test_middleware_call_validation_error(self, error_middleware):
        """미들웨어 유효성 검증 예외 처리 테스트"""
        # 모의 요청 객체
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/test/path"
        mock_request.method = "POST"

        # 유효성 검증 예외를 발생시키는 다음 미들웨어 호출 함수
        mock_call_next = AsyncMock()
        mock_call_next.side_effect = RequestValidationError(
            errors=[{"loc": ["body", "field"], "msg": "Field required"}]
        )

        # 미들웨어 호출
        with patch.object(error_middleware, "_handle_validation_error") as mock_handler:
            mock_handler.return_value = JSONResponse(
                status_code=422, content={"detail": "Request validation error", "errors": []}
            )
            await error_middleware(mock_request, mock_call_next)

            # 핸들러 호출 확인
            mock_handler.assert_called_once()
            args, kwargs = mock_handler.call_args
            assert args[0] == mock_request
            assert isinstance(args[1], RequestValidationError)

    @pytest.mark.asyncio
    async def test_middleware_call_server_error(self, error_middleware):
        """미들웨어 서버 오류 처리 테스트"""
        # 모의 요청 객체
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/test/path"
        mock_request.method = "GET"

        # 서버 오류를 발생시키는 다음 미들웨어 호출 함수
        mock_call_next = AsyncMock()
        mock_call_next.side_effect = ValueError("Unexpected server error")

        # 미들웨어 호출
        with patch.object(error_middleware, "_handle_server_error") as mock_handler:
            mock_handler.return_value = JSONResponse(
                status_code=500, content={"detail": "Internal server error"}
            )
            await error_middleware(mock_request, mock_call_next)

            # 핸들러 호출 확인
            mock_handler.assert_called_once()
            args, kwargs = mock_handler.call_args
            assert args[0] == mock_request
            assert isinstance(args[1], ValueError)
            assert str(args[1]) == "Unexpected server error"
