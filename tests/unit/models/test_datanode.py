import pytest
from pydantic import ValidationError

from qmtl.models.datanode import (
    DataNode,
    IntervalSettings,
    NodeStreamSettings,
    NodeTag,
    NodeTags,
    NodeType,
    IntervalEnum,
)


def test_datanode_minimal():
    node = DataNode(
        node_id="a" * 32,
        data_format={"type": "csv"},
        stream_settings=NodeStreamSettings(
            intervals={"1d": IntervalSettings(interval="1d", period=1)}
        ),
    )
    assert node.node_id == "a" * 32
    assert node.data_format["type"] == "csv"
    assert node.dependencies == []
    assert isinstance(node.tags, NodeTags)


def test_datanode_full():
    node = DataNode(
        node_id="b" * 32,
        type=NodeType.FEATURE,
        data_format={"type": "parquet"},
        params={"window": 5},
        dependencies=["c" * 32],
        ttl=3600,
        tags=NodeTags(predefined=[NodeType.FEATURE], custom=["custom1"]),
        interval_settings=IntervalSettings(interval="1h", period=7, max_history=100),
    )
    assert node.type == NodeType.FEATURE
    assert node.tags.predefined == [NodeType.FEATURE]
    assert node.interval_settings.interval == "1h"
    assert node.ttl == 3600


def test_datanode_invalid_node_id():
    with pytest.raises(ValidationError):
        DataNode(node_id="short", data_format={"type": "csv"})


def test_datanode_invalid_type():
    with pytest.raises(ValidationError):
        DataNode(node_id="c" * 32, type="NOTYPE", data_format={"type": "csv"})


def test_tags_and_intervalsettings_extra_forbid():
    with pytest.raises(ValidationError):
        NodeTags(predefined=[NodeType.RAW], custom=["x"], extra_field=1)
    with pytest.raises(ValidationError):
        IntervalSettings(interval="1d", extra_field=2)


def test_datanode_primary_tag_predefined():
    node = DataNode(
        node_id="d" * 32,
        data_format={"type": "csv"},
        tags=NodeTags(predefined=[NodeTag.FEATURE, NodeTag.RAW], custom=["customA"]),
        stream_settings=NodeStreamSettings(
            intervals={"1d": IntervalSettings(interval="1d", period=1)}
        ),
    )
    assert node.primary_tag == "FEATURE"


def test_datanode_primary_tag_type():
    node = DataNode(
        node_id="e" * 32,
        data_format={"type": "csv"},
        type=NodeType.RISK,
        tags=NodeTags(predefined=[], custom=["customB"]),
        stream_settings=NodeStreamSettings(
            intervals={"1d": IntervalSettings(interval="1d", period=1)}
        ),
    )
    assert node.primary_tag == "RISK"


def test_datanode_primary_tag_custom():
    node = DataNode(
        node_id="f" * 32,
        data_format={"type": "csv"},
        tags=NodeTags(predefined=[], custom=["customC"]),
        stream_settings=NodeStreamSettings(
            intervals={"1d": IntervalSettings(interval="1d", period=1)}
        ),
    )
    assert node.primary_tag == "customC"


def test_datanode_primary_tag_none():
    node = DataNode(
        node_id="a" * 32,
        data_format={"type": "csv"},
        tags=NodeTags(predefined=[], custom=[]),
        stream_settings=NodeStreamSettings(
            intervals={"1d": IntervalSettings(interval="1d", period=1)}
        ),
    )
    assert node.primary_tag is None


def test_intervalsettings_validation():
    i = IntervalSettings(interval=IntervalEnum.MINUTE, period=1, max_history=10)
    assert i.interval == "1m"
    assert i.period == 1
    assert i.max_history == 10
    # interval이 str이 아니면 예외
    import pytest

    with pytest.raises(ValueError):
        IntervalSettings(interval=123)


def test_nodestreamsettings():
    s = NodeStreamSettings(
        intervals={
            "1m": IntervalSettings(interval=IntervalEnum.MINUTE, period=1),
            "1h": IntervalSettings(interval=IntervalEnum.HOUR, period=7, max_history=100),
        }
    )
    assert "1m" in s.intervals
    assert s.intervals["1h"].max_history == 100
    # extra 필드 금지
    import pytest

    with pytest.raises(Exception):
        NodeStreamSettings(intervals={}, extra_field=1)


def test_datanode_with_intervalsettings():
    node = DataNode(
        node_id="a" * 32,
        data_format={"type": "csv"},
        interval_settings=IntervalSettings(interval=IntervalEnum.HOUR, period=7, max_history=50),
    )
    assert node.interval_settings.interval == "1h"
    assert node.interval_settings.max_history == 50


def test_intervalsettings_missing_interval():
    import pytest

    with pytest.raises(Exception):
        IntervalSettings()
    with pytest.raises(Exception):
        IntervalSettings(period="1d")


def test_nodestreamsettings_missing_interval():
    import pytest

    # intervals dict 자체가 비어있을 때
    with pytest.raises(Exception):
        NodeStreamSettings(intervals={})
    # intervals에 interval 필드가 없는 경우
    with pytest.raises(Exception):
        NodeStreamSettings(intervals={"no_interval": {"period": "1d"}})


def test_datanode_missing_interval():
    import pytest

    # stream_settings/interval_settings 모두 없는 경우
    with pytest.raises(Exception):
        DataNode(node_id="a" * 32, data_format={"type": "csv"})
    # stream_settings에 interval 없는 경우
    with pytest.raises(Exception):
        DataNode(
            node_id="a" * 32,
            data_format={"type": "csv"},
            stream_settings=NodeStreamSettings(intervals={}),
        )
    # interval_settings에 interval 없는 경우
    with pytest.raises(Exception):
        DataNode(
            node_id="a" * 32,
            data_format={"type": "csv"},
            interval_settings=IntervalSettings(period="1d"),
        )
