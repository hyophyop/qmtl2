"""
[NG-SDK-6] Golden/Round-trip 테스트 템플릿 예시 파일
이 파일은 protobuf 직렬화/역직렬화 기반의 golden 및 round-trip 테스트 표준 패턴을 제공합니다.

- 실제 테스트 구현 시, 이 템플릿을 복사하여 각 도메인에 맞게 수정하세요.
- golden: 기준(golden) 파일과의 비교를 통한 회귀 테스트
- round-trip: 직렬화→역직렬화→재직렬화의 데이터 일관성 검증
"""

import os
import pytest
from google.protobuf.json_format import MessageToJson, Parse
from qmtl.models.generated.qmtl_datanode_pb2 import DataNode
from qmtl.models.generated.qmtl_strategy_pb2 import Strategy
from qmtl.models.generated.qmtl_common_pb2 import NodeTags, IntervalSettings, IntervalEnum

# [필수] golden 데이터 저장 경로
GOLDEN_DATA_DIR = os.path.join(os.path.dirname(__file__), "../data/golden")
os.makedirs(GOLDEN_DATA_DIR, exist_ok=True)

# [유틸] golden 파일 저장/로드 함수
def save_golden_data(obj, filename):
    filepath = os.path.join(GOLDEN_DATA_DIR, filename)
    with open(filepath, "w") as f:
        f.write(MessageToJson(obj))
    return filepath

def load_golden_data(proto_class, filename):
    filepath = os.path.join(GOLDEN_DATA_DIR, filename)
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r") as f:
        data = f.read()
        obj = proto_class()
        Parse(data, obj)
        return obj

class TestGoldenAndRoundTripTemplate:
    """
    Golden & Round-trip 테스트 템플릿 클래스
    - golden: 기준 파일과의 비교
    - round-trip: 직렬화/역직렬화 일관성 검증
    """

    def test_datanode_golden(self):
        """[golden] DataNode 직렬화/역직렬화 결과를 golden 파일과 비교"""
        node = DataNode(
            id="test_node_1",
            name="Test Node",
            description="Test node for golden test",
            tags=NodeTags(predefined=["DATA", "TEST"], custom=["example", "golden"]),
            interval_settings=IntervalSettings(
                interval=IntervalEnum.MINUTE, period=5, max_history=100
            ),
        )
        golden_file = "datanode_golden.json"
        golden_node = load_golden_data(DataNode, golden_file)
        if golden_node is None:
            # 최초 실행 시 golden 파일 생성
            save_golden_data(node, golden_file)
            golden_node = node
        # 비교: 주요 필드 값이 golden과 동일한지 검증
        assert node.id == golden_node.id
        assert node.name == golden_node.name
        assert node.description == golden_node.description
        assert list(node.tags.predefined) == list(golden_node.tags.predefined)
        assert list(node.tags.custom) == list(golden_node.tags.custom)
        assert node.interval_settings.interval == golden_node.interval_settings.interval
        assert node.interval_settings.period == golden_node.interval_settings.period
        assert node.interval_settings.max_history == golden_node.interval_settings.max_history

    def test_datanode_roundtrip(self):
        """[round-trip] DataNode 직렬화→역직렬화→재직렬화 일관성 검증"""
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
        # 재직렬화
        reserialized = deserialized.SerializeToString()
        # 검증: 원본과 재직렬화 결과가 동일한지
        assert serialized == reserialized
        # 주요 필드 값도 동일한지
        assert original.id == deserialized.id
        assert original.name == deserialized.name
        assert original.description == deserialized.description
        assert list(original.tags.predefined) == list(deserialized.tags.predefined)
        assert list(original.tags.custom) == list(deserialized.tags.custom)
        assert original.interval_settings.interval == deserialized.interval_settings.interval
        assert original.interval_settings.period == deserialized.interval_settings.period
        assert original.interval_settings.max_history == deserialized.interval_settings.max_history

# [가이드]
# - 실제 golden/round-trip 테스트 구현 시, 위 템플릿을 복사하여
#   도메인별 메시지/필드에 맞게 수정하세요.
# - golden 파일이 변경되면 반드시 코드/스펙 변경 이력을 남기세요.
# - 템플릿 파일 자체는 테스트 수집 대상에서 제외하거나, 예시 데이터로만 유지하세요.

        # Golden 데이터와 현재 구현 비교
        assert node.id == golden_node.id
        assert node.name == golden_node.name
        assert node.description == golden_node.description
        assert list(node.tags.predefined) == list(golden_node.tags.predefined)
        assert list(node.tags.custom) == list(golden_node.tags.custom)

    def test_strategy_roundtrip_golden(self):
        """Strategy protobuf 직렬화/역직렬화 round-trip 테스트"""
        # 테스트 데이터 생성
        strategy = Strategy(
            id="test_strategy_1",
            name="Test Strategy",
            description="Test strategy for golden/round-trip test",
            nodes=["node1", "node2", "node3"],
            version="1.0.0",
        )

        # Protobuf 직렬화
        serialized = strategy.SerializeToString()

        # Protobuf 역직렬화
        deserialized = Strategy()
        deserialized.ParseFromString(serialized)

        # 직렬화/역직렬화 후 일치 여부 확인
        assert strategy.id == deserialized.id
        assert strategy.name == deserialized.name
        assert strategy.description == deserialized.description
        assert list(strategy.nodes) == list(deserialized.nodes)
        assert strategy.version == deserialized.version


if __name__ == "__main__":
    # 파일 단독 실행 시 golden 파일 생성 모드로 동작
    test = TestGoldenExample()

    # DataNode golden 테스트
    node = DataNode(
        id="test_node_1",
        name="Test Node",
        description="Test node for golden test",
        tags=NodeTags(predefined=["DATA", "TEST"], custom=["example", "golden"]),
    )
    save_golden_data(node, "datanode_golden.json")
    print(f"Created golden file for DataNode")

    # Strategy golden 테스트
    strategy = Strategy(
        id="test_strategy_1",
        name="Test Strategy",
        description="Test strategy for golden/round-trip test",
        nodes=["node1", "node2", "node3"],
        version="1.0.0",
    )
    save_golden_data(strategy, "strategy_golden.json")
    print(f"Created golden file for Strategy")
