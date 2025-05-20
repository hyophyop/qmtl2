"""Gateway 정책 서비스.

이 모듈은 Gateway 서비스의 정책 관리와 적용을 담당하는 클래스를 제공합니다.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ResourceType(str, Enum):
    """리소스 유형 열거형."""

    STRATEGY = "strategy"
    NODE = "node"
    CALLBACK = "callback"
    EVENT = "event"
    STREAM = "stream"


class ActionType(str, Enum):
    """작업 유형 열거형."""

    READ = "read"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"


class PolicyRule(BaseModel):
    """정책 규칙 모델."""

    resource_type: ResourceType
    resource_id: Optional[str] = None  # None이면 모든 리소스 ID에 적용
    actions: List[ActionType]
    effect: str = "allow"  # 'allow' 또는 'deny'
    conditions: Dict[str, Any] = Field(default_factory=dict)  # 조건 (예: 소유자 확인, 시간 제한 등)


class Policy(BaseModel):
    """정책 모델."""

    policy_id: str
    name: str
    description: Optional[str] = None
    roles: List[str]  # 이 정책이 적용되는 역할
    rules: List[PolicyRule]


class PolicyService:
    """Gateway 정책 관리 및 적용 서비스."""

    def __init__(self):
        """서비스 초기화."""
        # 정책 저장소 (실제로는 DB나 외부 스토리지에서 로드)
        self.policies: Dict[str, Policy] = {}
        # 기본 정책 로드
        self._load_default_policies()

    def _load_default_policies(self):
        """기본 정책을 로드합니다."""
        # 읽기 전용 정책
        read_only_policy = Policy(
            policy_id="read-only",
            name="Read Only Policy",
            description="읽기 전용 접근 권한을 제공하는 정책",
            roles=["user"],
            rules=[
                PolicyRule(
                    resource_type=ResourceType.STRATEGY, actions=[ActionType.READ], effect="allow"
                ),
                PolicyRule(
                    resource_type=ResourceType.NODE, actions=[ActionType.READ], effect="allow"
                ),
                PolicyRule(
                    resource_type=ResourceType.EVENT, actions=[ActionType.READ], effect="allow"
                ),
            ],
        )

        # 관리자 정책
        admin_policy = Policy(
            policy_id="admin",
            name="Admin Policy",
            description="모든 리소스에 대한 완전한 접근 권한을 제공하는 정책",
            roles=["admin"],
            rules=[
                PolicyRule(
                    resource_type=ResourceType.STRATEGY,
                    actions=[
                        ActionType.READ,
                        ActionType.CREATE,
                        ActionType.UPDATE,
                        ActionType.DELETE,
                        ActionType.EXECUTE,
                    ],
                    effect="allow",
                ),
                PolicyRule(
                    resource_type=ResourceType.NODE,
                    actions=[
                        ActionType.READ,
                        ActionType.CREATE,
                        ActionType.UPDATE,
                        ActionType.DELETE,
                    ],
                    effect="allow",
                ),
                PolicyRule(
                    resource_type=ResourceType.CALLBACK,
                    actions=[
                        ActionType.READ,
                        ActionType.CREATE,
                        ActionType.UPDATE,
                        ActionType.DELETE,
                    ],
                    effect="allow",
                ),
                PolicyRule(
                    resource_type=ResourceType.EVENT,
                    actions=[ActionType.READ, ActionType.CREATE],
                    effect="allow",
                ),
                PolicyRule(
                    resource_type=ResourceType.STREAM,
                    actions=[
                        ActionType.READ,
                        ActionType.CREATE,
                        ActionType.UPDATE,
                        ActionType.DELETE,
                    ],
                    effect="allow",
                ),
            ],
        )

        # 서비스 정책 (서비스 간 통신용)
        service_policy = Policy(
            policy_id="service",
            name="Service Policy",
            description="내부 서비스 간 통신을 위한 정책",
            roles=["service"],
            rules=[
                PolicyRule(
                    resource_type=ResourceType.STRATEGY,
                    actions=[
                        ActionType.READ,
                        ActionType.CREATE,
                        ActionType.UPDATE,
                        ActionType.EXECUTE,
                    ],
                    effect="allow",
                ),
                PolicyRule(
                    resource_type=ResourceType.NODE,
                    actions=[ActionType.READ, ActionType.CREATE, ActionType.UPDATE],
                    effect="allow",
                ),
                PolicyRule(
                    resource_type=ResourceType.CALLBACK,
                    actions=[ActionType.READ, ActionType.CREATE],
                    effect="allow",
                ),
                PolicyRule(
                    resource_type=ResourceType.EVENT,
                    actions=[ActionType.READ, ActionType.CREATE],
                    effect="allow",
                ),
            ],
        )

        # 정책 등록
        self.policies = {
            read_only_policy.policy_id: read_only_policy,
            admin_policy.policy_id: admin_policy,
            service_policy.policy_id: service_policy,
        }

    def evaluate_access(
        self,
        user_roles: List[str],
        resource_type: ResourceType,
        action: ActionType,
        resource_id: Optional[str] = None,
    ) -> bool:
        """사용자 역할이 특정 리소스에 대한 작업을 수행할 수 있는지 평가합니다.

        Args:
            user_roles: 사용자 역할 목록
            resource_type: 리소스 유형
            action: 수행할 작업
            resource_id: 리소스 ID (옵션)

        Returns:
            접근 허용 여부
        """
        # 기본적으로 접근 거부
        allowed = False

        # 사용자 역할에 적용 가능한 모든 정책 검사
        for policy in self.policies.values():
            if not any(role in policy.roles for role in user_roles):
                continue

            # 정책 규칙 검사
            for rule in policy.rules:
                # 리소스 유형 일치 확인
                if rule.resource_type != resource_type:
                    continue

                # 리소스 ID 일치 확인 (rule.resource_id가 None이면 모든 ID에 적용)
                if rule.resource_id and rule.resource_id != resource_id:
                    continue

                # 작업 허용 여부 확인
                if action in rule.actions:
                    if rule.effect == "allow":
                        allowed = True
                    else:  # "deny"
                        return False  # 명시적 거부는 즉시 거부로 처리

        return allowed
