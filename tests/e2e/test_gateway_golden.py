"""
Gateway 서비스 Golden 테스트

이 모듈은 Gateway 서비스의 Protobuf 직렬화 결과를 Golden 파일과 비교하는 테스트를 포함합니다.
Golden 테스트는 API의 안정성과 직렬화 형식의 일관성을 보장하는데 유용합니다.
"""

import pytest
import json
import os
import base64
from pathlib import Path
from google.protobuf import json_format

from qmtl.models.generated import (
    qmtl_common_pb2 as common_pb2,
    qmtl_strategy_pb2 as strategy_pb2,
    qmtl_datanode_pb2 as datanode_pb2,
    qmtl_pipeline_pb2 as pipeline_pb2,
)

from tests.e2e import factories
from tests.e2e.test_config import get_endpoint, TIMEOUTS

# Test markers
pytestmark = [pytest.mark.golden, pytest.mark.gateway, pytest.mark.e2e]

# Golden 파일 디렉토리 경로
GOLDEN_DIR = Path(__file__).parent / ".." / "golden_files" / "gateway"


def create_golden_dir():
    """Golden 파일 디렉토리 생성"""
    os.makedirs(GOLDEN_DIR, exist_ok=True)


def save_golden_file(name, data, binary=False):
    """Golden 파일 저장"""
    create_golden_dir()
    if binary:
        with open(GOLDEN_DIR / f"{name}.bin", "wb") as f:
            f.write(data)

        # 디버깅용 JSON 파일도 저장
        try:
            if isinstance(data, bytes):
                json_data = {"binary_base64": base64.b64encode(data).decode("utf-8")}
                with open(GOLDEN_DIR / f"{name}.json", "w") as f:
                    json.dump(json_data, f, indent=2)
        except Exception:
            pass  # JSON 변환 실패 시 무시
    else:
        with open(GOLDEN_DIR / f"{name}.json", "w") as f:
            json.dump(data, f, indent=2)


def load_golden_file(name, binary=False):
    """Golden 파일 로드"""
    if binary:
        with open(GOLDEN_DIR / f"{name}.bin", "rb") as f:
            return f.read()
    else:
        with open(GOLDEN_DIR / f"{name}.json", "r") as f:
            return json.load(f)


def proto_to_json(proto_obj):
    """Protobuf 객체를 JSON으로 변환"""
    return json.loads(json_format.MessageToJson(proto_obj, preserving_proto_field_name=True))


class TestGoldenProtobufSerialization:
    """Protobuf 직렬화 Golden 테스트 클래스"""

    def test_strategy_golden_serialization(self, authenticated_gateway_client):
        """전략 Protobuf Golden 테스트"""
        # 1. 테스트용 전략 생성
        strategy_data = {
            "strategy_name": "golden_test_strategy",
            "description": "Strategy for golden test",
            "author": "tester",
            "version": "1.0.0",
            "tags": ["golden", "test"],
            "source": "pytest",
        }
        strategy = factories.create_strategy_metadata(**strategy_data)

        # 2. 전략 직렬화
        serialized_strategy = strategy.SerializeToString()

        # 3. Golden 파일 생성 모드인 경우 (환경 변수 또는 커맨드 라인 옵션으로 제어)
        if os.environ.get("UPDATE_GOLDEN_FILES") == "1":
            # Golden 파일 저장
            save_golden_file("strategy_metadata", proto_to_json(strategy))
            save_golden_file("strategy_serialized", serialized_strategy, binary=True)
            pytest.skip("Golden 파일 생성 모드")

        # 4. Golden 파일과 비교
        try:
            golden_json = load_golden_file("strategy_metadata")
            golden_binary = load_golden_file("strategy_serialized", binary=True)

            # JSON 형식 비교
            current_json = proto_to_json(strategy)
            assert current_json == golden_json, "전략 JSON 구조가 Golden 파일과 다름"

            # 바이너리 형식 비교
            assert serialized_strategy == golden_binary, "전략 바이너리가 Golden 파일과 다름"
        except FileNotFoundError:
            pytest.skip(
                "Golden 파일이 없습니다. UPDATE_GOLDEN_FILES=1 환경 변수로 테스트를 실행하여 생성하세요."
            )

    def test_datanode_golden_serialization(self, authenticated_gateway_client):
        """데이터 노드 Protobuf Golden 테스트"""
        # 1. 테스트용 데이터 노드 생성
        datanode_data = {
            "node_id": "golden_test_datanode",
            "node_type": "SOURCE",
            "data_schema": {"field1": "string", "field2": "int32"},
            "tags": ["golden", "test"],
            "description": "Data node for golden test",
            "owner": "tester",
        }
        datanode = factories.create_datanode_metadata(**datanode_data)

        # 2. 데이터 노드 직렬화
        serialized_datanode = datanode.SerializeToString()

        # 3. Golden 파일 생성 모드인 경우
        if os.environ.get("UPDATE_GOLDEN_FILES") == "1":
            # Golden 파일 저장
            save_golden_file("datanode_metadata", proto_to_json(datanode))
            save_golden_file("datanode_serialized", serialized_datanode, binary=True)
            pytest.skip("Golden 파일 생성 모드")

        # 4. Golden 파일과 비교
        try:
            golden_json = load_golden_file("datanode_metadata")
            golden_binary = load_golden_file("datanode_serialized", binary=True)

            # JSON 형식 비교
            current_json = proto_to_json(datanode)
            assert current_json == golden_json, "데이터 노드 JSON 구조가 Golden 파일과 다름"

            # 바이너리 형식 비교
            assert serialized_datanode == golden_binary, "데이터 노드 바이너리가 Golden 파일과 다름"
        except FileNotFoundError:
            pytest.skip(
                "Golden 파일이 없습니다. UPDATE_GOLDEN_FILES=1 환경 변수로 테스트를 실행하여 생성하세요."
            )

    def test_gateway_api_response_golden(self, authenticated_gateway_client):
        """Gateway API 응답 Golden 테스트"""
        # 1. 전략 생성 및 등록
        strategy_data = {
            "strategy_name": "golden_api_test_strategy",
            "description": "Strategy for golden API test",
            "author": "tester",
            "version": "1.0.0",
            "tags": ["golden", "api", "test"],
            "source": "pytest",
        }
        strategy = factories.create_strategy_metadata(**strategy_data)

        # 2. Gateway API 호출
        url = get_endpoint("strategies", "base")
        response = authenticated_gateway_client.post(
            url,
            data=strategy.SerializeToString(),
            headers={"Content-Type": "application/x-protobuf"},
            timeout=TIMEOUTS["medium"],
        )

        # 3. 응답 검증
        assert response.status_code == 200

        # 4. 응답 Protobuf 파싱
        response_proto = strategy_pb2.StrategyRegistrationResponse()
        response_proto.ParseFromString(response.content)

        # 5. Golden 파일 생성 모드인 경우
        if os.environ.get("UPDATE_GOLDEN_FILES") == "1":
            # Golden 파일 저장
            save_golden_file("strategy_registration_response", proto_to_json(response_proto))
            save_golden_file("strategy_registration_response_raw", response.content, binary=True)
            pytest.skip("Golden 파일 생성 모드")

        # 6. Golden 파일과 비교
        try:
            golden_json = load_golden_file("strategy_registration_response")
            golden_binary = load_golden_file("strategy_registration_response_raw", binary=True)

            # JSON 형식으로 변환하여 비교 (필드 구조와 타입)
            current_json = proto_to_json(response_proto)

            # 응답의 strategy_id는 매번 달라지므로 비교에서 제외
            if "strategy_id" in current_json:
                del current_json["strategy_id"]
            if "strategy_id" in golden_json:
                del golden_json["strategy_id"]

            assert current_json == golden_json, "API 응답 JSON 구조가 Golden 파일과 다름"

            # 바이너리 비교는 strategy_id가 매번 달라지므로 건너뜀
        except FileNotFoundError:
            pytest.skip(
                "Golden 파일이 없습니다. UPDATE_GOLDEN_FILES=1 환경 변수로 테스트를 실행하여 생성하세요."
            )


class TestProtoFieldVersionCompatibility:
    """Protobuf 필드 버전 호환성 Golden 테스트 클래스"""

    def test_proto_field_version_compatibility(self):
        """Protobuf 필드 버전 호환성 테스트"""
        # 1. 현재 버전의 Protobuf 메시지 생성
        current_proto = strategy_pb2.StrategyMetadata(
            strategy_name="version_test",
            description="Version compatibility test",
            version="1.0.0",
            tags=["version", "test"],
        )

        # 2. JSON으로 직렬화
        current_json = proto_to_json(current_proto)

        # 3. Golden 파일 생성 모드인 경우
        if os.environ.get("UPDATE_GOLDEN_FILES") == "1":
            # Golden 파일 저장
            save_golden_file("strategy_proto_version", current_json)
            pytest.skip("Golden 파일 생성 모드")

        # 4. Golden 파일과 비교
        try:
            golden_json = load_golden_file("strategy_proto_version")

            # 기존 필드 존재 여부 및 타입 검증
            for field in golden_json:
                assert field in current_json, f"기존 필드 {field}가 현재 버전에 없음"
                assert type(golden_json[field]) == type(
                    current_json[field]
                ), f"필드 {field}의 타입이 변경됨"

            # 새로 추가된 필드 로깅 (호환성 깨지지 않음)
            new_fields = set(current_json.keys()) - set(golden_json.keys())
            if new_fields:
                print(f"새로 추가된 필드: {new_fields}")
        except FileNotFoundError:
            pytest.skip(
                "Golden 파일이 없습니다. UPDATE_GOLDEN_FILES=1 환경 변수로 테스트를 실행하여 생성하세요."
            )
