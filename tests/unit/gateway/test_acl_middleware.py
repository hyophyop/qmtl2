"""
Gateway ACL 미들웨어 테스트

이 모듈은 Gateway 서비스의 ACL 미들웨어(acl.py)에 대한 단위 테스트를 포함합니다.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi import HTTPException

from qmtl.gateway.middlewares.acl import ACLMiddleware, ACLConfig, ACLRule


class TestACLMiddleware:
    """ACL 미들웨어 테스트 클래스"""

    @pytest.fixture
    def acl_rules(self):
        """ACL 규칙 픽스처"""
        return [
            ACLRule(
                path_pattern=r"^/v1/gateway/strategies$",
                allowed_roles=["user", "admin"],
                allowed_methods=["GET"],
            ),
            ACLRule(
                path_pattern=r"^/v1/gateway/nodes$",
                allowed_roles=["user", "admin"],
                allowed_methods=["GET"],
            ),
            ACLRule(
                path_pattern=r"^/v1/gateway/admin$",
                allowed_roles=["admin"],
                allowed_methods=["GET", "POST"],
            ),
        ]

    @pytest.fixture
    def acl_config(self, acl_rules):
        """ACL 설정 픽스처"""
        return ACLConfig(
            rules=acl_rules,
            default_deny=True,
            exclude_paths=["/health", "/", "/docs", "/openapi.json"],
        )

    @pytest.fixture
    def acl_middleware(self, acl_config):
        """ACL 미들웨어 픽스처"""
        return ACLMiddleware(acl_config)

    def test_find_matching_rule(self, acl_middleware):
        """매칭 규칙 검색 테스트"""
        # 전략 경로에 매칭되는 규칙
        rule = acl_middleware._find_matching_rule("/v1/gateway/strategies")
        assert rule is not None
        assert rule.path_pattern == r"^/v1/gateway/strategies$"
        assert "user" in rule.allowed_roles
        assert "GET" in rule.allowed_methods

        # 관리자 경로에 매칭되는 규칙
        rule = acl_middleware._find_matching_rule("/v1/gateway/admin")
        assert rule is not None
        assert rule.path_pattern == r"^/v1/gateway/admin$"
        assert "admin" in rule.allowed_roles
        assert "GET" in rule.allowed_methods
        assert "POST" in rule.allowed_methods

        # 매칭되는 규칙 없음
        rule = acl_middleware._find_matching_rule("/v1/gateway/nonexistent")
        assert rule is None

    @pytest.mark.asyncio
    async def test_call_excluded_path(self, acl_middleware):
        """제외 경로 호출 테스트"""
        # Mock 요청 및 콜백
        mock_request = MagicMock()
        mock_request.url.path = "/health"
        mock_call_next = AsyncMock()
        mock_call_next.return_value = "response"

        # 미들웨어 호출
        response = await acl_middleware(mock_request, mock_call_next)

        # 다음 미들웨어가 호출되었는지 확인
        mock_call_next.assert_called_once_with(mock_request)
        assert response == "response"

    @pytest.mark.asyncio
    async def test_call_read_only_violation(self, acl_middleware):
        """읽기 전용 API 위반 테스트"""
        # Mock 요청 (POST 메서드, 읽기 전용 경로)
        mock_request = MagicMock()
        mock_request.url.path = "/v1/gateway/strategies"
        mock_request.method = "POST"
        mock_call_next = AsyncMock()

        # HTTP 예외가 발생해야 함
        with pytest.raises(HTTPException) as excinfo:
            await acl_middleware(mock_request, mock_call_next)

        # 상태 코드 및 메시지 확인
        assert excinfo.value.status_code == 405
        assert "Only GET requests are allowed" in excinfo.value.detail

    @pytest.mark.asyncio
    async def test_call_no_user(self, acl_middleware):
        """사용자 정보 없음 테스트"""
        # Mock 요청 (읽기 전용이 아닌 경로)
        mock_request = MagicMock()
        mock_request.url.path = "/v1/gateway/admin"
        mock_request.method = "GET"
        # 사용자 정보 없음
        mock_request.state = MagicMock()
        delattr(mock_request.state, "user") if hasattr(mock_request.state, "user") else None
        mock_call_next = AsyncMock()

        # HTTP 예외가 발생해야 함
        with pytest.raises(HTTPException) as excinfo:
            await acl_middleware(mock_request, mock_call_next)

        # 상태 코드 및 메시지 확인
        assert excinfo.value.status_code == 401
        assert "Authentication required" in excinfo.value.detail

    @pytest.mark.asyncio
    async def test_call_default_deny(self, acl_middleware):
        """기본 거부 정책 테스트"""
        # Mock 요청 (존재하지 않는 경로)
        mock_request = MagicMock()
        mock_request.url.path = "/v1/gateway/nonexistent"
        mock_request.method = "GET"
        # 사용자 정보
        mock_request.state.user = {"roles": ["user"]}
        mock_call_next = AsyncMock()

        # HTTP 예외가 발생해야 함
        with pytest.raises(HTTPException) as excinfo:
            await acl_middleware(mock_request, mock_call_next)

        # 상태 코드 및 메시지 확인
        assert excinfo.value.status_code == 403
        assert "Access denied by default policy" in excinfo.value.detail

    @pytest.mark.asyncio
    async def test_call_method_not_allowed(self, acl_middleware):
        """허용되지 않는 메서드 테스트"""
        # Mock 요청 (허용되지 않는 메서드)
        mock_request = MagicMock()
        mock_request.url.path = "/v1/gateway/strategies"
        mock_request.method = "DELETE"  # 허용되지 않는 메서드
        # 사용자 정보
        mock_request.state.user = {"roles": ["admin"]}
        mock_call_next = AsyncMock()

        # _find_matching_rule 메서드를 패치하여 규칙 반환
        rule = ACLRule(
            path_pattern=r"^/v1/gateway/strategies$",
            allowed_roles=["user", "admin"],
            allowed_methods=["GET"],
        )
        with patch.object(acl_middleware, "_find_matching_rule", return_value=rule):
            # HTTP 예외가 발생해야 함
            with pytest.raises(HTTPException) as excinfo:
                await acl_middleware(mock_request, mock_call_next)

            # 상태 코드 및 메시지 확인
            assert excinfo.value.status_code == 405
            assert "Method DELETE not allowed" in excinfo.value.detail

    @pytest.mark.asyncio
    async def test_call_insufficient_permissions(self, acl_middleware):
        """권한 부족 테스트"""
        # Mock 요청 (권한 없는 사용자)
        mock_request = MagicMock()
        mock_request.url.path = "/v1/gateway/admin"
        mock_request.method = "GET"
        # 권한 없는 사용자 정보
        mock_request.state.user = {"roles": ["user"]}  # admin 권한 필요
        mock_call_next = AsyncMock()

        # _find_matching_rule 메서드를 패치하여 규칙 반환
        rule = ACLRule(
            path_pattern=r"^/v1/gateway/admin$",
            allowed_roles=["admin"],
            allowed_methods=["GET", "POST"],
        )
        with patch.object(acl_middleware, "_find_matching_rule", return_value=rule):
            # HTTP 예외가 발생해야 함
            with pytest.raises(HTTPException) as excinfo:
                await acl_middleware(mock_request, mock_call_next)

            # 상태 코드 및 메시지 확인
            assert excinfo.value.status_code == 403
            assert "Insufficient permissions" in excinfo.value.detail

    @pytest.mark.asyncio
    async def test_call_allowed(self, acl_middleware):
        """접근 허용 테스트"""
        # Mock 요청 (권한 있는 사용자)
        mock_request = MagicMock()
        mock_request.url.path = "/v1/gateway/strategies"
        mock_request.method = "GET"
        # 권한 있는 사용자 정보
        mock_request.state.user = {"roles": ["user"]}
        mock_call_next = AsyncMock()
        mock_call_next.return_value = "response"

        # _find_matching_rule 메서드를 패치하여 규칙 반환
        rule = ACLRule(
            path_pattern=r"^/v1/gateway/strategies$",
            allowed_roles=["user", "admin"],
            allowed_methods=["GET"],
        )
        with patch.object(acl_middleware, "_find_matching_rule", return_value=rule):
            # 미들웨어 호출
            response = await acl_middleware(mock_request, mock_call_next)

            # 다음 미들웨어가 호출되었는지 확인
            mock_call_next.assert_called_once_with(mock_request)
            assert response == "response"
