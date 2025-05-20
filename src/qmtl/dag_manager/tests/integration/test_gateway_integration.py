from fastapi.testclient import TestClient
from qmtl.dag_manager.registry.api import app

import pytest

# 통합 테스트: Gateway 역할을 시뮬레이션하여 DAG Manager 내부 및 외부 API 호출 흐름 검증


def create_test_node_payload(node_id: str):
    return {
        "node": {
            "node_id": node_id,
            "data_format": {"format_type": "json"},
            "stream_settings": {"intervals": {"1m": {"interval": "MINUTE", "period": 1}}},
        }
    }


def test_gateway_node_lifecycle_json():
    client = TestClient(app)
    test_node_id = "a" * 32  # 32자리 hex 문자열

    # 1. Gateway(신뢰된 서비스) -> DAG Manager internal endpoint로 노드 생성 요청
    payload = create_test_node_payload(test_node_id)
    response = client.post(
        "/v1/registry/internal/nodes",
        json=payload,
    )
    assert response.status_code == 201, f"Internal create node failed: {response.text}"
    result = response.json()
    assert result.get("node_id") == test_node_id

    # 2. Gateway -> DAG Manager public endpoint에서 노드 조회
    response = client.get(f"/v1/registry/public/nodes/{test_node_id}")
    assert response.status_code == 200, f"Public get node failed: {response.text}"
    data = response.json()
    node = data["node"]
    # 생성된 노드의 필수 필드 검증
    assert node["node_id"] == test_node_id
    assert node["data_format"]["format_type"] == "json"
    assert "stream_settings" in node
    assert "intervals" in node["stream_settings"]


def test_gateway_node_lifecycle_protobuf_roundtrip():
    client = TestClient(app)
    test_node_id = "b" * 32
    payload = create_test_node_payload(test_node_id)
    response = client.post(
        "/v1/registry/internal/nodes",
        json=payload,
    )
    assert response.status_code == 201 or response.status_code == 200
    # public endpoint에서 노드 조회
    response = client.get(f"/v1/registry/public/nodes/{test_node_id}")
    assert response.status_code == 200
    data = response.json()["node"]
    # dict -> protobuf 역직렬화
    from qmtl.models.generated.qmtl_datanode_pb2 import DataNode
    from google.protobuf.json_format import ParseDict
    node_pb = DataNode()
    ParseDict(data, node_pb)
    # golden/round-trip 검증
    assert node_pb.node_id == test_node_id
    assert node_pb.data_format["format_type"] == "json"
    assert "stream_settings" in data
    assert "intervals" in data["stream_settings"]


@pytest.mark.parametrize("bad_id", ["z" * 32, "123", ""])
def test_gateway_node_creation_invalid_id(bad_id):
    client = TestClient(app)
    payload = create_test_node_payload(bad_id)
    response = client.post(
        "/v1/registry/internal/nodes",
        json=payload,
    )
    # node_id 패턴 불일치로 422 응답 예상
    assert response.status_code == 422
