"""
Round-trip 테스트 예시 파일
이 파일은 protobuf 직렬화/역직렬화 기반의 round-trip 테스트 패턴을 보여줍니다.
"""

import pytest
from qmtl.models.generated.qmtl_datanode_pb2 import DataNode
from qmtl.models.generated.qmtl_strategy_pb2 import Strategy
from qmtl.models.generated.qmtl_common_pb2 import NodeTags, IntervalSettings, IntervalEnum
from qmtl.models.generated.qmtl_callback_pb2 import Callback, CallbackType
from qmtl.models.generated.qmtl_events_pb2 import Event, EventType


class TestRoundTripSerialization:
    """
    Round-trip 직렬화/역직렬화 테스트 클래스

    이 테스트는 Protobuf 모델이 직렬화와 역직렬화 과정에서
    데이터 손실 없이 정확하게 변환되는지 검증합니다.
    """

    def test_datanode_roundtrip(self):
        """DataNode protobuf 직렬화/역직렬화 round-trip 테스트"""
        # 테스트 데이터 생성
        original = DataNode(
            id="test_node_1",
            name="Test Node",
            description="Test node for round-trip test",
            tags=NodeTags(predefined=["DATA", "TEST"], custom=["example", "round-trip"]),
            interval_settings=IntervalSettings(
                interval=IntervalEnum.MINUTE, period=5, max_history=100
            ),
        )

        # 직렬화
        serialized = original.SerializeToString()

        # 역직렬화
        deserialized = DataNode()
        deserialized.ParseFromString(serialized)

        # 검증
        assert original.id == deserialized.id
        assert original.name == deserialized.name
        assert original.description == deserialized.description
        assert list(original.tags.predefined) == list(deserialized.tags.predefined)
        assert list(original.tags.custom) == list(deserialized.tags.custom)
        assert original.interval_settings.interval == deserialized.interval_settings.interval
        assert original.interval_settings.period == deserialized.interval_settings.period
        assert original.interval_settings.max_history == deserialized.interval_settings.max_history

    def test_strategy_roundtrip(self):
        """Strategy protobuf 직렬화/역직렬화 round-trip 테스트"""
        # 테스트 데이터 생성
        original = Strategy(
            id="test_strategy_1",
            name="Test Strategy",
            description="Test strategy for round-trip test",
            nodes=["node1", "node2", "node3"],
            version="1.0.0",
        )

        # 직렬화
        serialized = original.SerializeToString()

        # 역직렬화
        deserialized = Strategy()
        deserialized.ParseFromString(serialized)

        # 검증
        assert original.id == deserialized.id
        assert original.name == deserialized.name
        assert original.description == deserialized.description
        assert list(original.nodes) == list(deserialized.nodes)
        assert original.version == deserialized.version

    def test_callback_roundtrip(self):
        """Callback protobuf 직렬화/역직렬화 round-trip 테스트"""
        # 테스트 데이터 생성
        original = Callback(
            id="callback_123",
            type=CallbackType.NODE_COMPLETED,
            node_id="node_456",
            url="https://example.com/callback",
            payload=b'{"status": "success", "data": {"id": "123"}}',
        )

        # 직렬화
        serialized = original.SerializeToString()

        # 역직렬화
        deserialized = Callback()
        deserialized.ParseFromString(serialized)

        # 검증
        assert original.id == deserialized.id
        assert original.type == deserialized.type
        assert original.node_id == deserialized.node_id
        assert original.url == deserialized.url
        assert original.payload == deserialized.payload

    def test_event_roundtrip(self):
        """Event protobuf 직렬화/역직렬화 round-trip 테스트"""
        # 테스트 데이터 생성
        original = Event(
            id="event_789",
            type=EventType.NODE_STATUS_CHANGED,
            source="node_service",
            node_id="node_456",
            timestamp=1641803054,
            payload=b'{"old_status": "PENDING", "new_status": "RUNNING"}',
        )

        # 직렬화
        serialized = original.SerializeToString()

        # 역직렬화
        deserialized = Event()
        deserialized.ParseFromString(serialized)

        # 검증
        assert original.id == deserialized.id
        assert original.type == deserialized.type
        assert original.source == deserialized.source
        assert original.node_id == deserialized.node_id
        assert original.timestamp == deserialized.timestamp
        assert original.payload == deserialized.payload

    # 매개변수화된 테스트로 여러 경우의 다양한 데이터 조합 테스트
    @pytest.mark.parametrize(
        "node_id,name,tags_pred,tags_custom",
        [
            ("node_1", "Node 1", ["DATA"], ["test"]),
            ("node_2", "Node 2", ["STREAM"], ["production"]),
            ("node_3", "Node 3", ["DATA", "STREAM"], ["test", "experimental"]),
            ("node_4", "Node 4", [], []),
        ],
    )
    def test_datanode_parametrized_roundtrip(self, node_id, name, tags_pred, tags_custom):
        """다양한 케이스에 대한 DataNode 직렬화/역직렬화 테스트"""
        # 테스트 데이터 생성
        original = DataNode(
            id=node_id, name=name, tags=NodeTags(predefined=tags_pred, custom=tags_custom)
        )

        # 직렬화
        serialized = original.SerializeToString()

        # 역직렬화
        deserialized = DataNode()
        deserialized.ParseFromString(serialized)

        # 검증
        assert original.id == deserialized.id
        assert original.name == deserialized.name
        assert list(original.tags.predefined) == list(deserialized.tags.predefined)
        assert list(original.tags.custom) == list(deserialized.tags.custom)
