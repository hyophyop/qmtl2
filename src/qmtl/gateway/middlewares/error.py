"""Gateway 오류 처리 미들웨어.

이 모듈은 Gateway API 요청 처리 중 발생하는 예외를 처리하는 미들웨어를 제공합니다.
"""

import logging
import traceback
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from typing import Callable
from pydantic import ValidationError

# 로깅 설정
logger = logging.getLogger("gateway.middleware")


class ErrorHandlingMiddleware:
    """오류 처리 미들웨어."""

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """미들웨어 콜 함수.

        Args:
            request: FastAPI 요청 객체
            call_next: 다음 미들웨어 또는 라우트 핸들러를 호출하는 함수

        Returns:
            FastAPI 응답 객체
        """
        try:
            return await call_next(request)

        except HTTPException as exc:
            # FastAPI HTTP 예외는 그대로 처리 (상태 코드, 헤더 등)
            return self._handle_http_exception(request, exc)

        except RequestValidationError as exc:
            # 요청 검증 오류
            return self._handle_validation_error(request, exc)

        except ValidationError as exc:
            # Pydantic 검증 오류
            return self._handle_pydantic_error(request, exc)

        except Exception as exc:
            # 예상치 못한 서버 오류
            return self._handle_server_error(request, exc)

    def _handle_http_exception(self, request: Request, exc: HTTPException) -> JSONResponse:
        """HTTP 예외 처리.

        Args:
            request: FastAPI 요청 객체
            exc: HTTP 예외

        Returns:
            JSONResponse
        """
        log_level = logging.ERROR if exc.status_code >= 500 else logging.WARNING
        logger.log(
            log_level,
            f"HTTP {exc.status_code} error: {exc.detail}",
            extra={
                "path": request.url.path,
                "method": request.method,
                "status_code": exc.status_code,
                "request_id": getattr(request.state, "request_id", None),
            },
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=getattr(exc, "headers", None),
        )

    def _handle_validation_error(
        self, request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """요청 검증 오류 처리.

        Args:
            request: FastAPI 요청 객체
            exc: 검증 예외

        Returns:
            JSONResponse
        """
        logger.warning(
            f"Request validation error: {str(exc)}",
            extra={
                "path": request.url.path,
                "method": request.method,
                "errors": str(exc.errors()),
                "request_id": getattr(request.state, "request_id", None),
            },
        )

        return JSONResponse(
            status_code=422, content={"detail": "Request validation error", "errors": exc.errors()}
        )

    def _handle_pydantic_error(self, request: Request, exc: ValidationError) -> JSONResponse:
        """Pydantic 검증 오류 처리.

        Args:
            request: FastAPI 요청 객체
            exc: Pydantic 검증 예외

        Returns:
            JSONResponse
        """
        logger.warning(
            f"Pydantic validation error: {str(exc)}",
            extra={
                "path": request.url.path,
                "method": request.method,
                "errors": str(exc.errors()),
                "request_id": getattr(request.state, "request_id", None),
            },
        )

        return JSONResponse(
            status_code=422, content={"detail": "Data validation error", "errors": exc.errors()}
        )

    def _handle_server_error(self, request: Request, exc: Exception) -> JSONResponse:
        """서버 오류 처리.

        Args:
            request: FastAPI 요청 객체
            exc: 예외

        Returns:
            JSONResponse
        """
        # 스택 트레이스 로깅
        tb_str = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))

        logger.error(
            f"Unexpected error: {str(exc)}",
            extra={
                "path": request.url.path,
                "method": request.method,
                "error": str(exc),
                "traceback": tb_str,
                "request_id": getattr(request.state, "request_id", None),
            },
        )

        # 운영 환경에서는 상세 오류를 클라이언트에 노출하지 않음
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error"
                # 디버그 모드에서만 추가 정보 제공 (옵션)
                # "error": str(exc) if settings.DEBUG else None
            },
        )
