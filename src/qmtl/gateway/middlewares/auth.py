"""Gateway 인증 미들웨어.

이 모듈은 Gateway API 요청에 대한 인증을 처리하는 미들웨어를 제공합니다.
JWT 토큰 기반 인증과 API 키 기반 인증을 지원합니다.
"""

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from typing import Optional, Dict, List, Any, Callable
import time
from pydantic import BaseModel


class JWTConfig(BaseModel):
    """JWT 설정 모델."""

    secret_key: str
    algorithm: str = "HS256"
    # 특정 엔드포인트에 대한 인증 면제 경로 (예: 상태 확인, 문서)
    exclude_paths: List[str] = ["/health", "/", "/docs", "/openapi.json"]


class JWTAuthMiddleware:
    """JWT 토큰 기반 인증 미들웨어."""

    def __init__(self, config: JWTConfig):
        """미들웨어 초기화.

        Args:
            config: JWT 설정
        """
        self.config = config
        self.security = HTTPBearer(auto_error=False)

    async def __call__(self, request: Request, call_next: Callable):
        """미들웨어 콜 함수.

        Args:
            request: FastAPI 요청 객체
            call_next: 다음 미들웨어 또는 라우트 핸들러를 호출하는 함수

        Returns:
            FastAPI 응답 객체
        """
        # 인증 제외 경로 확인
        if request.url.path in self.config.exclude_paths:
            return await call_next(request)

        # 읽기 전용 API의 경우 GET 요청만 허용
        if request.method != "GET" and request.url.path.startswith("/v1/gateway"):
            raise HTTPException(
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                detail="Only GET requests are allowed for this endpoint",
            )

        # Bearer 토큰 추출
        credentials: Optional[HTTPAuthorizationCredentials] = await self.security(request)
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # JWT 토큰 검증
        try:
            payload = jwt.decode(
                credentials.credentials, self.config.secret_key, algorithms=[self.config.algorithm]
            )

            # 토큰 만료 확인
            if "exp" in payload and payload["exp"] < time.time():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # 요청 상태에 사용자 정보 추가
            request.state.user = payload

        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return await call_next(request)


def create_access_token(
    data: Dict[str, Any],
    secret_key: str,
    algorithm: str = "HS256",
    expires_delta: Optional[int] = None,
) -> str:
    """액세스 토큰 생성 유틸리티 함수.

    Args:
        data: 토큰에 인코딩할 데이터
        secret_key: JWT 시크릿 키
        algorithm: JWT 알고리즘
        expires_delta: 만료 시간(초)

    Returns:
        JWT 토큰 문자열
    """
    to_encode = data.copy()

    if expires_delta:
        expire = time.time() + expires_delta
        to_encode.update({"exp": expire})

    return jwt.encode(to_encode, secret_key, algorithm=algorithm)
