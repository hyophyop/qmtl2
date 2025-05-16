"""
Registry API 통합 테스트: 노드-전략 참조 관계 관리 기능 테스트
"""

from typing import Dict

import pytest

pytestmark = pytest.mark.usefixtures("docker_compose_up_down")
from fastapi.testclient import TestClient

from qmtl.models.datanode import DataNode, IntervalSettings, NodeTags, NodeType
from qmtl.registry.api import app

# 테스트 클라이언트 초기화
client = TestClient(app)


@pytest.fixture
def sample_node() -> Dict:
    """샘플 DataNode 생성 Fixture"""
    node = DataNode(
        node_id="1234567890abcdef1234567890abcdef",
        type=NodeType.RAW,
        data_format={"fields": ["a", "b"]},
        params={"foo": "bar"},
        dependencies=[],
        ttl=3600,
        tags=NodeTags(predefined=[NodeType.RAW]),
        interval_settings=IntervalSettings(interval="1d", period=7),
    )
    return node.model_dump()


def test_node_dependency_management():
    """노드 의존성(DEPENDS_ON) 관리 기능 테스트"""
    # 노드 1 생성
    node1 = DataNode(
        node_id="1234567890abcdef1234567890abcdef",
        type=NodeType.RAW,
        data_format={"fields": ["a", "b"]},
        params={"foo": "bar"},
        dependencies=[],
        ttl=3600,
        tags=NodeTags(predefined=[NodeType.RAW]),
        interval_settings=IntervalSettings(interval="1d", period=7),
    )
    client.post("/v1/registry/nodes", json={"node": node1.model_dump()})
    # 새 노드 2개 생성
    node2 = DataNode(
        node_id="abcdefabcdefabcdefabcdefabcdefab",
        type=NodeType.RAW,
        data_format={"fields": ["x", "y"]},
        params={"foo": "baz"},
        dependencies=[],
        ttl=3600,
        tags=NodeTags(predefined=[NodeType.RAW]),
        interval_settings=IntervalSettings(interval="1d", period=7),
    )
    node3 = DataNode(
        node_id="fedcbafedcbafedcbafedcbafedcbafe",
        type=NodeType.RAW,
        data_format={"fields": ["z"]},
        params={"foo": "qux"},
        dependencies=[],
        ttl=3600,
        tags=NodeTags(predefined=[NodeType.RAW]),
        interval_settings=IntervalSettings(interval="1d", period=7),
    )
    client.post("/v1/registry/nodes", json={"node": node2.model_dump()})
    client.post("/v1/registry/nodes", json={"node": node3.model_dump()})

    # 의존성 추가
    resp = client.post(f"/v1/registry/nodes/{node1.node_id}/dependencies/{node2.node_id}")
    assert resp.status_code == 200
    resp = client.post(f"/v1/registry/nodes/{node1.node_id}/dependencies/{node3.node_id}")
    assert resp.status_code == 200

    # 의존성 조회
    resp = client.get(f"/v1/registry/nodes/{node1.node_id}/dependencies")
    assert resp.status_code == 200
    deps = resp.json()["dependencies"]
    assert node2.node_id in deps and node3.node_id in deps

    # 의존성 삭제
    resp = client.delete(f"/v1/registry/nodes/{node1.node_id}/dependencies/{node2.node_id}")
    assert resp.status_code == 200
    resp = client.get(f"/v1/registry/nodes/{node1.node_id}/dependencies")
    deps = resp.json()["dependencies"]
    assert node2.node_id not in deps and node3.node_id in deps

    # 남은 의존성 모두 삭제
    resp = client.delete(f"/v1/registry/nodes/{node1.node_id}/dependencies/{node3.node_id}")
    assert resp.status_code == 200
    resp = client.get(f"/v1/registry/nodes/{node1.node_id}/dependencies")
    deps = resp.json()["dependencies"]
    assert deps == []
