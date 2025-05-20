from qmtl.common.errors.exceptions import ValidationError
from qmtl.models.datanode import DataNode
from qmtl.models.generated import qmtl_datanode_pb2


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


def validate_proto_node(node) -> None:
    """
    Validate a protobuf DataNode object (or dict from MessageToDict) for required fields and domain constraints.
    Raise ValidationError on failure.
    """
    # Support both proto and dict (for test/MessageToDict round-trip)
    if hasattr(node, 'DESCRIPTOR'):
        # Protobuf object
        node_id = getattr(node, 'node_id', None)
        dependencies = getattr(node, 'dependencies', [])
        tags = getattr(node, 'tags', None)
        interval_settings = getattr(node, 'interval_settings', None)
    elif isinstance(node, dict):
        node_id = node.get('node_id')
        dependencies = node.get('dependencies', [])
        tags = node.get('tags')
        interval_settings = node.get('interval_settings')
    else:
        raise ValidationError('Unsupported node type for validation')

    if not node_id or len(node_id) != 32:
        raise ValidationError("node_id must be a 32-character hex string")
    if dependencies:
        if not isinstance(dependencies, (list, tuple)):
            raise ValidationError("dependencies must be a list")
        for dep in dependencies:
            if not isinstance(dep, str) or len(dep) != 32:
                raise ValidationError(f"dependency '{dep}' must be a 32-character hex string")
    if tags:
        predefined = getattr(tags, 'predefined', None) if hasattr(tags, 'predefined') else tags.get('predefined', [])
        custom = getattr(tags, 'custom', None) if hasattr(tags, 'custom') else tags.get('custom', [])
        if predefined:
            for tag in predefined:
                if not isinstance(tag, str):
                    raise ValidationError("predefined tags must be strings")
        if custom:
            for tag in custom:
                if not isinstance(tag, str):
                    raise ValidationError("custom tags must be strings")
    if interval_settings:
        if hasattr(interval_settings, 'interval'):
            # protobuf: interval is int (enum value)
            interval = getattr(interval_settings, 'interval', None)
            if interval is not None and not isinstance(interval, int):
                raise ValidationError("interval must be an enum (int) in protobuf")
        else:
            # dict: interval should be string (enum label)
            interval = interval_settings.get('interval')
            if interval is not None and not isinstance(interval, str):
                raise ValidationError("interval must be a string")
    # 기타 도메인 규칙 추가 가능
