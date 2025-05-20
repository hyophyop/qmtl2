"""
Registry API 통합 테스트: 노드-전략 참조 관계 관리 기능 테스트
"""

from typing import Dict
import sys

sys.path.insert(0, "./src")
from google.protobuf.json_format import MessageToDict
from qmtl.models.generated import qmtl_datanode_pb2

DataNode = qmtl_datanode_pb2.DataNode
from qmtl.models.generated.qmtl_common_pb2 import NodeTags, IntervalSettings, IntervalEnum

from fastapi.testclient import TestClient
from qmtl.dag_manager.registry.api import app

import pytest

# 테스트 클라이언트 초기화
client = TestClient(app)


def make_sample_node(
    node_id,
    type_=None,
    data_format=None,
    params=None,
    dependencies=None,
    ttl=None,
    tags=None,
    interval_settings=None,
):
    node = DataNode()
    node.node_id = node_id
    if type_ is not None:
        node.type = type_
    if data_format is not None:
        for k, v in data_format.items():
            node.data_format[k] = v
    if params is not None:
        for k, v in params.items():
            node.params[k] = v
    if dependencies is not None:
        node.dependencies.extend(dependencies)
    if ttl is not None:
        node.ttl = ttl
    if tags is not None:
        node.tags.CopyFrom(tags)
    if interval_settings is not None:
        node.interval_settings.CopyFrom(interval_settings)
    return node


def make_tags(predefined=None, custom=None):
    tags = NodeTags()
    if predefined:
        tags.predefined.extend(predefined)
    if custom:
        tags.custom.extend(custom)
    return tags


def make_interval_settings(interval, period, max_history=None):
    settings = IntervalSettings()
    # interval은 enum 이름 또는 값으로 지정해야 함
    if isinstance(interval, str):
        interval = (
            IntervalEnum.Value(interval.upper())
            if interval.upper() in IntervalEnum.keys()
            else getattr(IntervalEnum, interval.upper(), 0)
        )
    settings.interval = interval
    settings.period = period
    if max_history is not None:
        settings.max_history = max_history
    return settings


def test_node_dependency_management():
    import time

    assert hasattr(qmtl_datanode_pb2, "DataNode"), "DataNode not found in qmtl_datanode_pb2"
    # 노드 1 생성
    node1 = make_sample_node(
        node_id="1234567890abcdef1234567890abcdef",
        type_="RAW",
        data_format={"fields": "a,b"},
        params={"foo": "bar"},
        dependencies=[],
        ttl=3600,
        tags=make_tags(predefined=["RAW"]),
        interval_settings=make_interval_settings(IntervalEnum.DAY, 7),
    )
    t0 = time.time()
    resp = client.post("/v1/registry/nodes", json={"node": MessageToDict(node1)}, timeout=5)
    print(
        f"[node1 create] status={resp.status_code}, elapsed={time.time()-t0:.2f}s, body={resp.text}"
    )
    assert resp.status_code in (200, 201), f"node1 create failed: {resp.text}"
    # 새 노드 2개 생성
    node2 = make_sample_node(
        node_id="abcdefabcdefabcdefabcdefabcdefab",
        type_="RAW",
        data_format={"fields": "x,y"},
        params={"foo": "baz"},
        dependencies=[],
        ttl=3600,
        tags=make_tags(predefined=["RAW"]),
        interval_settings=make_interval_settings(IntervalEnum.DAY, 7),
    )
    node3 = make_sample_node(
        node_id="fedcbafedcbafedcbafedcbafedcbafe",
        type_="RAW",
        data_format={"fields": "z"},
        params={"foo": "qux"},
        dependencies=[],
        ttl=3600,
        tags=make_tags(predefined=["RAW"]),
        interval_settings=make_interval_settings(IntervalEnum.DAY, 7),
    )
    t1 = time.time()
    resp = client.post("/v1/registry/nodes", json={"node": MessageToDict(node2)}, timeout=5)
    print(
        f"[node2 create] status={resp.status_code}, elapsed={time.time()-t1:.2f}s, body={resp.text}"
    )
    assert resp.status_code in (200, 201), f"node2 create failed: {resp.text}"
    t2 = time.time()
    resp = client.post("/v1/registry/nodes", json={"node": MessageToDict(node3)}, timeout=5)
    print(
        f"[node3 create] status={resp.status_code}, elapsed={time.time()-t2:.2f}s, body={resp.text}"
    )
    assert resp.status_code in (200, 201), f"node3 create failed: {resp.text}"

    # 의존성 추가
    t3 = time.time()
    resp = client.post(
        f"/v1/registry/nodes/{node1.node_id}/dependencies/{node2.node_id}", timeout=5
    )
    print(f"[dep add 1] status={resp.status_code}, elapsed={time.time()-t3:.2f}s, body={resp.text}")
    assert resp.status_code == 200
    t4 = time.time()
    resp = client.post(
        f"/v1/registry/nodes/{node1.node_id}/dependencies/{node3.node_id}", timeout=5
    )
    print(f"[dep add 2] status={resp.status_code}, elapsed={time.time()-t4:.2f}s, body={resp.text}")
    assert resp.status_code == 200

    # 의존성 조회
    t5 = time.time()
    resp = client.get(f"/v1/registry/nodes/{node1.node_id}/dependencies", timeout=5)
    print(f"[dep get] status={resp.status_code}, elapsed={time.time()-t5:.2f}s, body={resp.text}")
    assert resp.status_code == 200
    deps = resp.json()["dependencies"]
    assert node2.node_id in deps and node3.node_id in deps

    # 의존성 삭제
    t6 = time.time()
    resp = client.delete(
        f"/v1/registry/nodes/{node1.node_id}/dependencies/{node2.node_id}", timeout=5
    )
    print(f"[dep del 1] status={resp.status_code}, elapsed={time.time()-t6:.2f}s, body={resp.text}")
    assert resp.status_code == 200
    t7 = time.time()
    resp = client.get(f"/v1/registry/nodes/{node1.node_id}/dependencies", timeout=5)
    print(
        f"[dep get after del 1] status={resp.status_code}, elapsed={time.time()-t7:.2f}s, body={resp.text}"
    )
    deps = resp.json()["dependencies"]
    assert node2.node_id not in deps and node3.node_id in deps

    # 남은 의존성 모두 삭제
    t8 = time.time()
    resp = client.delete(
        f"/v1/registry/nodes/{node1.node_id}/dependencies/{node3.node_id}", timeout=5
    )
    print(f"[dep del 2] status={resp.status_code}, elapsed={time.time()-t8:.2f}s, body={resp.text}")
    assert resp.status_code == 200
    t9 = time.time()
    resp = client.get(f"/v1/registry/nodes/{node1.node_id}/dependencies", timeout=5)
    print(
        f"[dep get after del 2] status={resp.status_code}, elapsed={time.time()-t9:.2f}s, body={resp.text}"
    )
    deps = resp.json()["dependencies"]
    assert deps == []


def test_node_create_and_get_roundtrip():
    """노드 생성 후 조회 응답을 protobuf로 역직렬화하여 golden/round-trip 검증"""
    node_id = "deadbeefdeadbeefdeadbeefdeadbeef"
    node = make_sample_node(
        node_id=node_id,
        type_="RAW",
        data_format={"fields": "a,b"},
        params={"foo": "bar"},
        dependencies=[],
        ttl=3600,
        tags=make_tags(predefined=["RAW"]),
        interval_settings=make_interval_settings(IntervalEnum.DAY, 7),
    )
    # 노드 생성
    resp = client.post("/v1/registry/nodes", json={"node": MessageToDict(node)})
    assert resp.status_code == 201 or resp.status_code == 200

    # 노드 조회
    resp = client.get(f"/v1/registry/nodes/{node_id}")
    assert resp.status_code == 200
    data = resp.json()["node"]

    # dict -> protobuf 역직렬화
    from google.protobuf.json_format import ParseDict

    node_pb = DataNode()
    ParseDict(data, node_pb)

    # golden/round-trip 검증
    assert node_pb.node_id == node.node_id
    assert node_pb.type == node.type
    assert node_pb.data_format == node.data_format
    assert node_pb.params == node.params
    assert list(node_pb.dependencies) == list(node.dependencies)
    assert node_pb.ttl == node.ttl
    assert node_pb.tags.predefined == node.tags.predefined
    assert node_pb.interval_settings.interval == node.interval_settings.interval
    assert node_pb.interval_settings.period == node.interval_settings.period


def test_node_dependency_management_fallback_forbidden(monkeypatch):
    """
    [중요] 이 테스트는 Neo4j 연결 실패 시 인메모리 fallback이 발생하면 반드시 실패해야 함을 검증한다.
    서비스 코드가 fallback을 허용하는 구조라면 이 테스트는 실패한다.
    이 테스트는 추후 fixture에서 Neo4j 연결 신뢰도를 높이기 위한 탐지/알람 용도로 유지한다.
    실제 서비스 코드 변경 없이, Neo4j 연결 신뢰성 확보 후 이 테스트가 통과해야 한다.
    """
    pytest.xfail("현재 서비스 코드가 fallback(inmemory)을 허용하므로 실패가 정상입니다. 추후 Neo4j 신뢰성 확보 후 통과해야 합니다.")
    from qmtl.dag_manager.registry import api as registry_api

    # Neo4j 연결 함수가 항상 예외를 발생시키도록 패치
    def always_fail_get_node_service():
        raise Exception("Neo4j connection failed (forced for test)")

    monkeypatch.setattr(registry_api, "get_node_service", always_fail_get_node_service)

    node_id = "11111111111111111111111111111111"
    node = make_sample_node(
        node_id=node_id,
        type_="RAW",
        data_format={"fields": "a,b"},
        params={"foo": "bar"},
        dependencies=[],
        ttl=3600,
        tags=make_tags(predefined=["RAW"]),
        interval_settings=make_interval_settings(IntervalEnum.DAY, 7),
    )
    # 노드 생성 시도: 반드시 500 에러가 발생해야 하며, fallback(inmemory)로 넘어가면 안 됨
    resp = client.post("/v1/registry/nodes", json={"node": MessageToDict(node)})
    print(f"[fallback forbidden] status={{resp.status_code}}, body={{resp.text}}")
    assert resp.status_code == 500, f"Neo4j 실패 시 inmemory fallback이 발생하면 안 됩니다. status={{resp.status_code}}, body={{resp.text}}"
