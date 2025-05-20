"""Gateway 로깅 미들웨어.

이 모듈은 Gateway API 요청/응답에 대한 로깅을 처리하는 미들웨어를 제공합니다.
"""

import time
import json
import logging
from fastapi import Request, Response
from typing import Callable
import uuid


# 로깅 설정
logger = logging.getLogger("gateway.middleware")


class LoggingMiddleware:
    """요청/응답 로깅 미들웨어."""

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """미들웨어 콜 함수.

        Args:
            request: FastAPI 요청 객체
            call_next: 다음 미들웨어 또는 라우트 핸들러를 호출하는 함수

        Returns:
            FastAPI 응답 객체
        """
        # 요청 ID 생성 (추적 목적)
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # 시작 시간 기록
        start_time = time.time()

        # 요청 정보 로깅
        await self._log_request(request, request_id)

        # 다음 미들웨어 또는 라우트 핸들러 호출
        try:
            response = await call_next(request)

            # 응답 성공 로깅
            self._log_response(
                request_id=request_id,
                status_code=response.status_code,
                processing_time=time.time() - start_time,
            )

            return response

        except Exception as e:
            # 예외 로깅
            logger.exception(
                f"Request failed: {request_id} - {request.method} {request.url.path}",
                extra={"request_id": request_id, "error": str(e)},
            )
            raise

    async def _log_request(self, request: Request, request_id: str) -> None:
        """요청 정보를 로깅합니다.

        Args:
            request: FastAPI 요청 객체
            request_id: 요청 ID
        """
        # 요청 헤더 추출 (민감 정보 제외)
        headers = dict(request.headers)
        if "authorization" in headers:
            headers["authorization"] = "[REDACTED]"

        # 요청 바디 추출 (가능한 경우)
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body_bytes = await request.body()
                if body_bytes:
                    try:
                        # JSON 바디 파싱 시도
                        body = json.loads(body_bytes.decode())
                    except json.JSONDecodeError:
                        # 일반 텍스트로 처리
                        body = "[Non-JSON body]"
            except Exception:
                body = "[Body read error]"

        # 로깅
        logger.info(
            f"Request: {request_id} - {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "headers": headers,
                "body": body,
                "client_ip": request.client.host if request.client else None,
            },
        )

    def _log_response(self, request_id: str, status_code: int, processing_time: float) -> None:
        """응답 정보를 로깅합니다.

        Args:
            request_id: 요청 ID
            status_code: HTTP 상태 코드
            processing_time: 요청 처리 시간 (초)
        """
        logger.info(
            f"Response: {request_id} - Status: {status_code} - Time: {processing_time:.4f}s",
            extra={
                "request_id": request_id,
                "status_code": status_code,
                "processing_time": processing_time,
            },
        )
