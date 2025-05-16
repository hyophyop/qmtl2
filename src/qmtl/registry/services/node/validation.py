from qmtl.common.errors.exceptions import ValidationError
from qmtl.models.datanode import DataNode


def validate_node_model(node: DataNode) -> None:
    """
    DataNode 모델의 유효성 검증을 수행한다.
    - Pydantic 모델 검증 (자동)
    - 도메인 추가 검증: dependencies, tags, interval_settings 등
    - 실패 시 ValidationError 발생
    """
    # Pydantic validation은 이미 생성 시 수행됨
    # 추가 도메인 검증
    if not node.node_id or len(node.node_id) != 32:
        raise ValidationError("node_id must be a 32-character hex string")
    if node.dependencies:
        if not isinstance(node.dependencies, list):
            raise ValidationError("dependencies must be a list")
        for dep in node.dependencies:
            if not isinstance(dep, str) or len(dep) != 32:
                raise ValidationError(f"dependency '{dep}' must be a 32-character hex string")
    if node.tags:
        if node.tags.predefined:
            for tag in node.tags.predefined:
                if not isinstance(tag, str):
                    raise ValidationError("predefined tags must be strings")
        if node.tags.custom:
            for tag in node.tags.custom:
                if not isinstance(tag, str):
                    raise ValidationError("custom tags must be strings")
    if node.interval_settings:
        if not isinstance(node.interval_settings.interval, str):
            raise ValidationError("interval must be a string")
    # 기타 도메인 규칙 추가 가능
