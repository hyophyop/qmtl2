import pytest

pytestmark = pytest.mark.usefixtures("docker_compose_up_down")
from fastapi.testclient import TestClient
from qmtl.registry.api import app
from qmtl.models.callback import NodeCallbackType

client = TestClient(app)

NODE_ID = "1234567890abcdef1234567890abcdef"
CALLBACK_URL = "http://localhost:9000/callback"


def test_register_and_list_callback():
    req = {
        "node_id": NODE_ID,
        "callback_type": "on_refcount_zero",
        "url": CALLBACK_URL,
        "metadata": {"foo": "bar"}
    }
    resp = client.post(f"/v1/registry/nodes/{NODE_ID}/callbacks", json=req)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"]

    # 리스트 확인
    resp2 = client.get(f"/v1/registry/nodes/{NODE_ID}/callbacks")
    assert resp2.status_code == 200
    callbacks = resp2.json()
    assert "on_refcount_zero" in callbacks
    assert any(cb["url"] == CALLBACK_URL for cb in callbacks["on_refcount_zero"])

def test_trigger_callback():
    event = {
        "node_id": NODE_ID,
        "callback_type": "on_refcount_zero",
        "event_payload": {"reason": "test"}
    }
    resp = client.post(f"/v1/registry/nodes/{NODE_ID}/callbacks/trigger", json=event)
    assert resp.status_code == 200
    results = resp.json()
    assert any("triggered" in r["message"] for r in results)

def test_unregister_callback():
    resp = client.delete(f"/v1/registry/nodes/{NODE_ID}/callbacks?callback_type=on_refcount_zero&url={CALLBACK_URL}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"]
    # 삭제 후 리스트 확인
    resp2 = client.get(f"/v1/registry/nodes/{NODE_ID}/callbacks")
    callbacks = resp2.json()
    assert not callbacks["on_refcount_zero"]
