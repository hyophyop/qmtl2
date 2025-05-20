import pytest
from qmtl.dag_manager.execution.status_service import StatusService
from google.protobuf.timestamp_pb2 import Timestamp

class DummyNode:
    def __init__(self, node_id):
        self.node_id = node_id

def test_status_service_singleton():
    s1 = StatusService()
    s2 = StatusService()
    assert s1 is s2
    assert hasattr(s1, "pipelines")
    assert hasattr(s1, "nodes")

def test_initialize_and_update_pipeline_status():
    service = StatusService()
    # 파이프라인 초기화 (params 없이)
    node = DummyNode("n1")
    service.initialize_pipeline("p1", [node])
    # 상태 업데이트
    service.update_pipeline_status("p1", status="RUNNING")
    # 상태 조회
    status = service.get_pipeline_status("p1")
    assert status is not None
    # 노드 상태 업데이트
    service.update_node_status("p1", "n1", status="COMPLETED")
    node_status = service.get_node_status("p1", "n1")
    assert node_status is not None
    # 전체 노드 상태 조회
    all_nodes = service.get_all_node_statuses("p1")
    assert "n1" in all_nodes
    # 파이프라인 정리
    service.cleanup_pipeline("p1")
    assert service.get_pipeline_status("p1") is None

def test_timestamp_type_debug():
    now = Timestamp()
    from datetime import datetime
    now.FromDatetime(datetime.now())
    print("[DEBUG] now type:", type(now))
    service = StatusService()
    node = DummyNode("n1")
    service.initialize_pipeline("p1", [node])
    ps = service.get_pipeline_status("p1")
    print("[DEBUG] ps type:", type(ps))
    print("[DEBUG] ps.start_time type:", type(ps.start_time))
    print("[DEBUG] ps.start_time:", ps.start_time)
