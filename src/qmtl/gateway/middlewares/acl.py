"""Gateway 접근 제어 미들웨어.

이 모듈은 Gateway API 요청에 대한 접근 제어(ACL)를 처리하는 미들웨어를 제공합니다.
"""

from fastapi import Request, HTTPException, status
from typing import List, Callable, Optional
from pydantic import BaseModel, field_validator
import re


class ACLRule(BaseModel):
    """ACL 규칙 모델."""

    path_pattern: str
    allowed_roles: List[str]
    allowed_methods: List[str] = ["GET"]

    # 정규식 패턴 유효성 검증
    @field_validator("path_pattern")
    def validate_path_pattern(cls, v):
        try:
            re.compile(v)
        except re.error:
            raise ValueError(f"Invalid regex pattern: {v}")
        return v


class ACLConfig(BaseModel):
    """ACL 설정 모델."""

    rules: List[ACLRule]
    # 기본적으로 모든 경로는 접근 거부 (화이트리스트 방식)
    default_deny: bool = True
    # 인증 면제 경로 (ACL 검사 자체를 건너뜀)
    exclude_paths: List[str] = ["/health", "/", "/docs", "/openapi.json"]


class ACLMiddleware:
    """ACL(Access Control List) 미들웨어."""

    def __init__(self, config: ACLConfig):
        """미들웨어 초기화.

        Args:
            config: ACL 설정
        """
        self.config = config
        # 경로 패턴 컴파일
        self.compiled_rules = [(re.compile(rule.path_pattern), rule) for rule in config.rules]

    async def __call__(self, request: Request, call_next: Callable):
        """미들웨어 콜 함수.

        Args:
            request: FastAPI 요청 객체
            call_next: 다음 미들웨어 또는 라우트 핸들러를 호출하는 함수

        Returns:
            FastAPI 응답 객체
        """
        # 인증 면제 경로 확인
        if request.url.path in self.config.exclude_paths:
            return await call_next(request)

        # 요청 경로에 대한 ACL 규칙 검색
        matched_rule = self._find_matching_rule(request.url.path)

        # 읽기 전용 API의 경우 GET 요청만 허용
        if request.url.path.startswith("/v1/gateway") and request.method != "GET":
            raise HTTPException(
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                detail="Only GET requests are allowed for this endpoint",
            )

        # 사용자 역할 확인 (인증 미들웨어에서 설정된 사용자 정보 사용)
        user = getattr(request.state, "user", None)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
            )

        user_roles = user.get("roles", [])

        # 규칙이 없고 기본 거부 정책이면 접근 거부
        if not matched_rule and self.config.default_deny:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied by default policy"
            )

        # 규칙이 있으면 접근 권한 검사
        if matched_rule:
            # HTTP 메서드 검사
            if request.method not in matched_rule.allowed_methods:
                raise HTTPException(
                    status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                    detail=f"Method {request.method} not allowed",
                )

            # 역할 검사
            if not any(role in matched_rule.allowed_roles for role in user_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
                )

        return await call_next(request)

    def _find_matching_rule(self, path: str) -> Optional[ACLRule]:
        """요청 경로에 맞는 ACL 규칙을 찾습니다.

        Args:
            path: 요청 경로

        Returns:
            매칭된 ACL 규칙 또는 None
        """
        for pattern, rule in self.compiled_rules:
            if pattern.match(path):
                return rule
        return None


# 기본 ACL 규칙 설정 예시
default_acl_rules = [
    ACLRule(
        path_pattern=r"^/v1/gateway/strategies$",
        allowed_roles=["user", "admin"],
        allowed_methods=["GET"],
    ),
    ACLRule(
        path_pattern=r"^/v1/gateway/strategies/[^/]+/status$",
        allowed_roles=["user", "admin", "service"],
        allowed_methods=["GET"],
    ),
    ACLRule(
        path_pattern=r"^/v1/gateway/callbacks$",
        allowed_roles=["admin", "service"],
        allowed_methods=["GET"],
    ),
    ACLRule(
        path_pattern=r"^/v1/gateway/nodes$",
        allowed_roles=["user", "admin"],
        allowed_methods=["GET"],
    ),
    ACLRule(
        path_pattern=r"^/v1/gateway/events$",
        allowed_roles=["user", "admin", "service"],
        allowed_methods=["GET"],
    ),
]
