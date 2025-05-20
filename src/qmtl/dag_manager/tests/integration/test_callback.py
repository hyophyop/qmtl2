import pytest
from fastapi.testclient import TestClient
from qmtl.dag_manager.registry.api import app
from qmtl.models.generated import qmtl_callback_pb2

client = TestClient(app)

NODE_ID = "1234567890abcdef1234567890abcdef"
CALLBACK_URL = "http://localhost:9000/callback"


def test_register_and_list_callback():
    req = qmtl_callback_pb2.NodeCallbackRequest(
        node_id=NODE_ID,
        callback_type=qmtl_callback_pb2.NodeCallbackType.ON_REFCOUNT_ZERO,
        url=CALLBACK_URL,
    )
    # FastAPI 테스트 클라이언트는 json만 지원하므로, 내부 서비스 계층 mock에서 protobuf round-trip 검증 필요
    resp = client.post(f"/v1/registry/nodes/{NODE_ID}/callbacks", json={
        "node_id": req.node_id,
        "callback_type": "on_refcount_zero",
        "url": req.url,
        "metadata": {},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"]

    # 리스트 확인
    resp2 = client.get(f"/v1/registry/nodes/{NODE_ID}/callbacks")
    assert resp2.status_code == 200
    callbacks = resp2.json()
    assert "on_refcount_zero" in callbacks
    assert any(cb["url"] == CALLBACK_URL for cb in callbacks["on_refcount_zero"])

    # Protobuf round-trip 검증 (등록 요청)
    round_trip = qmtl_callback_pb2.NodeCallbackRequest()
    round_trip.ParseFromString(req.SerializeToString())
    assert round_trip == req

def test_trigger_callback():
    event = qmtl_callback_pb2.NodeCallbackEvent(
        node_id=NODE_ID,
        callback_type=qmtl_callback_pb2.NodeCallbackType.ON_REFCOUNT_ZERO,
    )
    # FastAPI 테스트 클라이언트는 json만 지원하므로, 내부 서비스 계층 mock에서 protobuf round-trip 검증 필요
    resp = client.post(f"/v1/registry/nodes/{NODE_ID}/callbacks/trigger", json={
        "node_id": event.node_id,
        "callback_type": "on_refcount_zero",
        "event_payload": {"reason": "test"},
    })
    assert resp.status_code == 200
    results = resp.json()
    assert any("triggered" in r["message"] for r in results)

    # Protobuf round-trip 검증 (이벤트)
    round_trip = qmtl_callback_pb2.NodeCallbackEvent()
    round_trip.ParseFromString(event.SerializeToString())
    assert round_trip == event

def test_unregister_callback():
    resp = client.delete(f"/v1/registry/nodes/{NODE_ID}/callbacks?callback_type=on_refcount_zero&url={CALLBACK_URL}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"]
    # 삭제 후 리스트 확인
    resp2 = client.get(f"/v1/registry/nodes/{NODE_ID}/callbacks")
    callbacks = resp2.json()
    assert not callbacks["on_refcount_zero"]
