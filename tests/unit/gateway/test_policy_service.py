"""
Gateway 정책 서비스 테스트

이 모듈은 Gateway 서비스의 정책 서비스(policy.py)에 대한 단위 테스트를 포함합니다.
"""

import pytest
from unittest.mock import MagicMock, patch

from qmtl.gateway.services.policy import PolicyService, ResourceType, ActionType, Policy, PolicyRule


class TestPolicyService:
    """정책 서비스 테스트 클래스"""

    @pytest.fixture
    def policy_service(self):
        """정책 서비스 픽스처"""
        return PolicyService()

    def test_load_default_policies(self, policy_service):
        """기본 정책 로드 테스트"""
        # 기본 정책 확인
        assert "read-only" in policy_service.policies
        assert "admin" in policy_service.policies
        assert "service" in policy_service.policies

        # 읽기 전용 정책 확인
        read_only = policy_service.policies["read-only"]
        assert read_only.name == "Read Only Policy"
        assert "user" in read_only.roles

        # 읽기 전용 정책은 READ 작업만 허용
        for rule in read_only.rules:
            assert ActionType.READ in rule.actions
            assert ActionType.CREATE not in rule.actions
            assert ActionType.DELETE not in rule.actions

        # 관리자 정책 확인
        admin = policy_service.policies["admin"]
        assert admin.name == "Admin Policy"
        assert "admin" in admin.roles

        # 관리자 정책은 모든 작업 허용
        strategy_rule = next(
            (r for r in admin.rules if r.resource_type == ResourceType.STRATEGY), None
        )
        assert strategy_rule is not None
        assert ActionType.READ in strategy_rule.actions
        assert ActionType.CREATE in strategy_rule.actions
        assert ActionType.UPDATE in strategy_rule.actions
        assert ActionType.DELETE in strategy_rule.actions
        assert ActionType.EXECUTE in strategy_rule.actions

    def test_evaluate_access_allow(self, policy_service):
        """접근 허용 테스트"""
        # 관리자는 전략 생성 가능
        assert policy_service.evaluate_access(
            user_roles=["admin"], resource_type=ResourceType.STRATEGY, action=ActionType.CREATE
        )

        # 사용자는 전략 조회 가능
        assert policy_service.evaluate_access(
            user_roles=["user"], resource_type=ResourceType.STRATEGY, action=ActionType.READ
        )

        # 서비스는 콜백 생성 가능
        assert policy_service.evaluate_access(
            user_roles=["service"], resource_type=ResourceType.CALLBACK, action=ActionType.CREATE
        )

    def test_evaluate_access_deny(self, policy_service):
        """접근 거부 테스트"""
        # 사용자는 전략 생성 불가
        assert not policy_service.evaluate_access(
            user_roles=["user"], resource_type=ResourceType.STRATEGY, action=ActionType.CREATE
        )

        # 사용자는 전략 삭제 불가
        assert not policy_service.evaluate_access(
            user_roles=["user"], resource_type=ResourceType.STRATEGY, action=ActionType.DELETE
        )

        # 서비스는 노드 삭제 불가
        assert not policy_service.evaluate_access(
            user_roles=["service"], resource_type=ResourceType.NODE, action=ActionType.DELETE
        )

    def test_evaluate_access_multiple_roles(self, policy_service):
        """다중 역할 테스트"""
        # 사용자 + 관리자 역할이 있으면 전략 생성 가능
        assert policy_service.evaluate_access(
            user_roles=["user", "admin"],
            resource_type=ResourceType.STRATEGY,
            action=ActionType.CREATE,
        )

        # 관리자 역할이 없으면 전략 생성 불가
        assert not policy_service.evaluate_access(
            user_roles=["user", "service"],
            resource_type=ResourceType.STRATEGY,
            action=ActionType.DELETE,
        )

    def test_evaluate_access_resource_id(self, policy_service):
        """리소스 ID 기반 테스트"""
        # 리소스 ID가 있는 경우
        assert policy_service.evaluate_access(
            user_roles=["admin"],
            resource_type=ResourceType.STRATEGY,
            action=ActionType.UPDATE,
            resource_id="test-strategy-1",
        )

        # 기본 정책은 리소스 ID를 지정하지 않음 (모든 ID에 적용)
        read_only = policy_service.policies["read-only"]
        for rule in read_only.rules:
            assert rule.resource_id is None

    def test_custom_policy(self):
        """사용자 정의 정책 테스트"""
        # 사용자 정의 정책 생성
        custom_policy = Policy(
            policy_id="custom",
            name="Custom Policy",
            description="Custom test policy",
            roles=["tester"],
            rules=[
                PolicyRule(
                    resource_type=ResourceType.STRATEGY,
                    resource_id="test-strategy",
                    actions=[ActionType.READ, ActionType.EXECUTE],
                    effect="allow",
                ),
                PolicyRule(
                    resource_type=ResourceType.NODE, actions=[ActionType.READ], effect="allow"
                ),
                # 명시적 거부 규칙
                PolicyRule(
                    resource_type=ResourceType.STRATEGY,
                    resource_id="restricted-strategy",
                    actions=[ActionType.READ, ActionType.EXECUTE],
                    effect="deny",
                ),
            ],
        )

        # 정책 서비스 인스턴스
        policy_service = PolicyService()
        # 사용자 정의 정책 추가
        policy_service.policies["custom"] = custom_policy

        # 허용된 작업 테스트
        assert policy_service.evaluate_access(
            user_roles=["tester"],
            resource_type=ResourceType.STRATEGY,
            action=ActionType.READ,
            resource_id="test-strategy",
        )

        # 허용되지 않은 작업 테스트
        assert not policy_service.evaluate_access(
            user_roles=["tester"],
            resource_type=ResourceType.STRATEGY,
            action=ActionType.UPDATE,
            resource_id="test-strategy",
        )

        # 명시적 거부 규칙 테스트
        assert not policy_service.evaluate_access(
            user_roles=["tester"],
            resource_type=ResourceType.STRATEGY,
            action=ActionType.READ,
            resource_id="restricted-strategy",
        )

        # 관리자 역할이 추가되면 명시적 거부에도 불구하고 접근 가능
        assert policy_service.evaluate_access(
            user_roles=["tester", "admin"],
            resource_type=ResourceType.STRATEGY,
            action=ActionType.READ,
            resource_id="restricted-strategy",
        )
