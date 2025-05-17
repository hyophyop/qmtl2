from fastapi.testclient import TestClient

from qmtl.dag_manager.api import app

client = TestClient(app)


def test_list_nodes_not_implemented():
    resp = client.get("/v1/dag-manager/nodes")
    assert resp.status_code == 501
    assert resp.json()["detail"] == "NotImplemented"


def test_list_node_dependencies_not_implemented():
    resp = client.get("/v1/dag-manager/nodes/n1/dependencies")
    assert resp.status_code == 501
    assert resp.json()["detail"] == "NotImplemented"


def test_list_nodes_by_tags_not_implemented():
    resp = client.get("/v1/dag-manager/nodes/by-tags", params={"tags": ["a"]})
    assert resp.status_code == 501
    assert resp.json()["detail"] == "NotImplemented"


def test_list_streams_not_implemented():
    resp = client.get("/v1/dag-manager/streams")
    assert resp.status_code == 501
    assert resp.json()["detail"] == "NotImplemented"


def test_list_events_not_implemented():
    resp = client.get("/v1/dag-manager/events")
    assert resp.status_code == 501
    assert resp.json()["detail"] == "NotImplemented"


def test_list_callbacks_not_implemented():
    resp = client.get("/v1/dag-manager/nodes/n1/callbacks")
    assert resp.status_code == 501
    assert resp.json()["detail"] == "NotImplemented"
