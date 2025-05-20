"""
Gateway 서비스 Protobuf 직렬화/역직렬화 테스트

이 모듈은 Gateway 서비스의 Protobuf 직렬화/역직렬화 일관성을 검증하는 테스트를 포함합니다.
round-trip 테스트를 통해 데이터 손실 없이 직렬화와 역직렬화가 수행되는지 확인합니다.
"""

import pytest
from google.protobuf import json_format
import json

from qmtl.models.generated import (
    qmtl_common_pb2 as common_pb2,
    qmtl_strategy_pb2 as strategy_pb2,
    qmtl_datanode_pb2 as datanode_pb2,
    qmtl_pipeline_pb2 as pipeline_pb2,
)

from tests.e2e import factories
from tests.e2e.test_config import get_endpoint, TIMEOUTS

# Test markers
pytestmark = [pytest.mark.protobuf, pytest.mark.gateway, pytest.mark.e2e]


class TestProtobufSerialization:
    """Protobuf 직렬화 테스트 클래스"""

    def test_strategy_serialization_roundtrip(self, authenticated_gateway_client):
        """전략 Protobuf 직렬화/역직렬화 round-trip 테스트"""
        # 1. 테스트용 전략 생성
        strategy_data = {
            "strategy_name": "serialization_test_strategy",
            "description": "Strategy for serialization test",
            "author": "tester",
            "version": "1.0.0",
            "tags": ["serialization", "test"],
            "source": "pytest",
        }
        strategy_metadata = factories.create_strategy_metadata(**strategy_data)

        # 2. Gateway에 전략 등록
        url = get_endpoint("strategies", "base")
        response = authenticated_gateway_client.post(
            url,
            data=strategy_metadata.SerializeToString(),
            headers={"Content-Type": "application/x-protobuf"},
            timeout=TIMEOUTS["medium"],
        )

        # 3. 응답 확인
        assert response.status_code == 200
        response_msg = strategy_pb2.StrategyRegistrationResponse()
        response_msg.ParseFromString(response.content)
        strategy_id = response_msg.strategy_id

        # 4. 등록된 전략 조회
        get_url = get_endpoint("strategies", "by_id", strategy_id=strategy_id)
        get_response = authenticated_gateway_client.get(
            get_url, headers={"Accept": "application/x-protobuf"}, timeout=TIMEOUTS["short"]
        )

        # 5. 직렬화/역직렬화 결과 비교
        assert get_response.status_code == 200
        retrieved_strategy = strategy_pb2.StrategyMetadata()
        retrieved_strategy.ParseFromString(get_response.content)

        # 6. 필드별 일치 여부 검증
        assert retrieved_strategy.strategy_name == strategy_metadata.strategy_name
        assert retrieved_strategy.description == strategy_metadata.description
        assert retrieved_strategy.author == strategy_metadata.author
        assert retrieved_strategy.version == strategy_metadata.version
        assert list(retrieved_strategy.tags) == list(strategy_metadata.tags)
        assert retrieved_strategy.source == strategy_metadata.source

    def test_datanode_serialization_roundtrip(self, authenticated_gateway_client):
        """데이터 노드 Protobuf 직렬화/역직렬화 round-trip 테스트"""
        # 1. 테스트용 데이터 노드 생성
        datanode_data = {
            "node_id": "serialization_test_datanode",
            "node_type": "SOURCE",
            "data_schema": {"field1": "string", "field2": "int32"},
            "tags": ["serialization", "test"],
            "description": "Data node for serialization test",
            "owner": "tester",
        }
        datanode_metadata = factories.create_datanode_metadata(**datanode_data)

        # 2. Gateway에 데이터 노드 등록
        url = get_endpoint("datanodes", "base")
        response = authenticated_gateway_client.post(
            url,
            data=datanode_metadata.SerializeToString(),
            headers={"Content-Type": "application/x-protobuf"},
            timeout=TIMEOUTS["medium"],
        )

        # 3. 응답 확인
        assert response.status_code == 200
        response_msg = datanode_pb2.DataNodeResponse()
        response_msg.ParseFromString(response.content)
        assert response_msg.success is True

        # 4. 등록된 데이터 노드 조회
        get_url = get_endpoint("datanodes", "by_id", datanode_id=datanode_data["node_id"])
        get_response = authenticated_gateway_client.get(
            get_url, headers={"Accept": "application/x-protobuf"}, timeout=TIMEOUTS["short"]
        )

        # 5. 직렬화/역직렬화 결과 비교
        assert get_response.status_code == 200
        retrieved_datanode = datanode_pb2.DataNode()
        retrieved_datanode.ParseFromString(get_response.content)

        # 6. 필드별 일치 여부 검증
        assert retrieved_datanode.node_id == datanode_metadata.node_id
        assert retrieved_datanode.type == datanode_metadata.type


class TestProtobufVersionCompatibility:
    """Protobuf 버전 호환성 테스트 클래스"""

    def test_protobuf_field_defaults(self, authenticated_gateway_client):
        """Protobuf 필드 기본값 처리 테스트"""
        # 1. 최소 필드만 포함된 전략 생성
        minimal_strategy = strategy_pb2.StrategyMetadata(
            strategy_name="minimal_strategy", version="1.0.0"
        )
        # 나머지 필드는 기본값 사용

        # 2. Gateway에 전략 등록
        url = get_endpoint("strategies", "base")
        response = authenticated_gateway_client.post(
            url,
            data=minimal_strategy.SerializeToString(),
            headers={"Content-Type": "application/x-protobuf"},
            timeout=TIMEOUTS["medium"],
        )

        # 3. 응답 확인
        assert response.status_code == 200
        response_msg = strategy_pb2.StrategyRegistrationResponse()
        response_msg.ParseFromString(response.content)
        strategy_id = response_msg.strategy_id

        # 4. 등록된 전략 조회
        get_url = get_endpoint("strategies", "by_id", strategy_id=strategy_id)
        get_response = authenticated_gateway_client.get(
            get_url, headers={"Accept": "application/x-protobuf"}, timeout=TIMEOUTS["short"]
        )

        # 5. 직렬화/역직렬화 결과 비교
        assert get_response.status_code == 200
        retrieved_strategy = strategy_pb2.StrategyMetadata()
        retrieved_strategy.ParseFromString(get_response.content)

        # 6. 필수 필드 및 기본값 필드 검증
        assert retrieved_strategy.strategy_name == "minimal_strategy"
        assert retrieved_strategy.version == "1.0.0"
        # 기본 문자열 필드는 빈 문자열이어야 함
        assert retrieved_strategy.description == ""
        # 기본 반복 필드는 빈 리스트여야 함
        assert len(retrieved_strategy.tags) == 0

    def test_unknown_fields_handling(self, authenticated_gateway_client):
        """알 수 없는 필드 처리 테스트"""
        # 이 테스트는 실제로 프로토콜 버퍼 정의가 변경되었을 때만 의미가 있음
        # 여기서는 기본 deserialize 동작만 검증

        # 1. 표준 전략 생성
        strategy_data = {
            "strategy_name": "unknown_fields_test_strategy",
            "description": "Strategy for unknown fields test",
            "version": "1.0.0",
        }
        strategy_metadata = factories.create_strategy_metadata(**strategy_data)

        # 2. 직렬화 및 등록
        url = get_endpoint("strategies", "base")
        response = authenticated_gateway_client.post(
            url,
            data=strategy_metadata.SerializeToString(),
            headers={"Content-Type": "application/x-protobuf"},
            timeout=TIMEOUTS["medium"],
        )

        # 3. 응답 검증
        assert response.status_code == 200
        response_msg = strategy_pb2.StrategyRegistrationResponse()
        response_msg.ParseFromString(response.content)

        # 알 수 없는 필드가 있어도 기본 deserialize가 성공해야 함
        assert response_msg.success is True


class TestProtobufMessageConversion:
    """Protobuf 메시지 변환 테스트 클래스"""

    def test_json_proto_conversion(self):
        """JSON-Protobuf 변환 테스트"""
        # 1. JSON 형식 데이터
        strategy_json = {
            "strategy_name": "json_convert_strategy",
            "description": "Strategy for JSON conversion test",
            "author": "tester",
            "version": "1.0.0",
            "tags": ["json", "conversion"],
            "source": "pytest",
        }

        # 2. JSON -> Protobuf 변환
        strategy_proto = strategy_pb2.StrategyMetadata()
        json_format.Parse(json.dumps(strategy_json), strategy_proto)

        # 3. Protobuf -> JSON 변환
        strategy_json_roundtrip = json_format.MessageToDict(strategy_proto)

        # 4. 변환 결과 비교
        assert strategy_json_roundtrip["strategy_name"] == strategy_json["strategy_name"]
        assert strategy_json_roundtrip["description"] == strategy_json["description"]
        assert strategy_json_roundtrip["author"] == strategy_json["author"]
        assert strategy_json_roundtrip["version"] == strategy_json["version"]
        assert strategy_json_roundtrip["tags"] == strategy_json["tags"]
        assert strategy_json_roundtrip["source"] == strategy_json["source"]

    def test_binary_proto_conversion(self):
        """바이너리-Protobuf 변환 테스트"""
        # 1. 원본 Protobuf 메시지 생성
        original_strategy = strategy_pb2.StrategyMetadata(
            strategy_name="binary_convert_strategy",
            description="Strategy for binary conversion test",
            author="tester",
            version="1.0.0",
            tags=["binary", "conversion"],
            source="pytest",
        )

        # 2. Protobuf -> 바이너리 직렬화
        binary_data = original_strategy.SerializeToString()

        # 3. 바이너리 -> Protobuf 역직렬화
        deserialized_strategy = strategy_pb2.StrategyMetadata()
        deserialized_strategy.ParseFromString(binary_data)

        # 4. 변환 결과 비교
        assert deserialized_strategy.strategy_name == original_strategy.strategy_name
        assert deserialized_strategy.description == original_strategy.description
        assert deserialized_strategy.author == original_strategy.author
        assert deserialized_strategy.version == original_strategy.version
        assert list(deserialized_strategy.tags) == list(original_strategy.tags)
        assert deserialized_strategy.source == original_strategy.source
