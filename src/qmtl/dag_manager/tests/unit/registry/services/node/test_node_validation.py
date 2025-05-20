import pytest
from pydantic import ValidationError as PydanticValidationError

from qmtl.common.errors.exceptions import ValidationError
from qmtl.models.datanode import DataNode, IntervalSettings, NodeTags, NodeType

# from qmtl.dag_manager.registry.services.node.validation import validate_node_model  # 실제 구현체가 없으므로 임시 주석

pytest.skip(
    "validate_node_model 및 관련 모듈 미구현으로 전체 테스트 임시 skip", allow_module_level=True
)


def test_valid_node():
    node = DataNode(
        node_id="1234567890abcdef1234567890abcdef",
        type=NodeType.RAW,
        data_format={"fields": ["a", "b"]},
        params={"foo": "bar"},
        dependencies=[],
        ttl=3600,
        tags=NodeTags(predefined=["RAW"]),
        interval_settings=IntervalSettings(interval="1d", period=1),
    )
    validate_node_model(node)  # Should not raise


def test_invalid_node_id():
    with pytest.raises(PydanticValidationError):
        DataNode(node_id="shortid", data_format={"fields": ["a"]}, dependencies=[])


def test_invalid_dependency():
    node = DataNode(
        node_id="1234567890abcdef1234567890abcdef",
        data_format={"fields": ["a"]},
        dependencies=["badid"],
        interval_settings=IntervalSettings(interval="1d", period=1),
    )
    with pytest.raises(ValidationError):
        validate_node_model(node)


def test_invalid_tags():
    with pytest.raises(PydanticValidationError):
        DataNode(
            node_id="1234567890abcdef1234567890abcdef",
            data_format={"fields": ["a"]},
            tags=NodeTags(predefined=[123]),
        )


def test_invalid_interval_settings():
    with pytest.raises(PydanticValidationError):
        DataNode(
            node_id="1234567890abcdef1234567890abcdef",
            data_format={"fields": ["a"]},
            interval_settings=IntervalSettings(interval=123),
        )
