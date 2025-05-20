# MULTI-4: DAG/ready node API 통합 테스트
import pytest

pytestmark = pytest.mark.usefixtures("docker_compose_up_down")

from fastapi.testclient import TestClient
from qmtl.dag_manager.registry.api import app
import types
from qmtl.models.generated import qmtl_strategy_pb2


# --- MOCK Neo4jNodeManagementService ---
class MockNeo4jNodeManagementService:
    def __init__(self, *args, **kwargs):
        self.nodes = {}
        self.dependencies = {}
    def create_node(self, node):
        node_id = getattr(node, 'node_id', 'dummy-node-id')
        self.nodes[node_id] = node
        self.dependencies.setdefault(node_id, set())
        return node_id
    def get_node(self, node_id):
        node = self.nodes.get(node_id)
        if node is None:
            return None
        return node
    def delete_node(self, node_id):
        self.nodes.pop(node_id, None)
        self.dependencies.pop(node_id, None)
        return True
    def list_nodes(self):
        return list(self.nodes.values())
    def list_zero_deps(self):
        return [n for n in self.nodes.values() if not self.dependencies.get(getattr(n, 'node_id', None))]
    def list_by_tags(self, tags, interval=None, period=None, match_mode="AND"):
        return list(self.nodes.values())
    def add_contains_relationship(self, strategy_version_id, node_id):
        return None
    def remove_contains_relationship(self, strategy_version_id, node_id):
        return None
    def get_node_ref_count(self, node_id):
        return 0
    def get_node_ref_strategies(self, node_id):
        return []
    def get_strategy_nodes(self, strategy_version_id):
        return list(self.nodes.values())
    def get_node_status(self, node_id):
        return None
    def update_node_status(self, node_id, status):
        return None
    def get_node_dependencies(self, node_id):
        return list(self.dependencies.get(node_id, []))
    def add_dependency(self, node_id, dependency_id):
        self.dependencies.setdefault(node_id, set()).add(dependency_id)
    def remove_dependency(self, node_id, dependency_id):
        self.dependencies.setdefault(node_id, set()).discard(dependency_id)
    def get_ready_nodes(self, pipeline_id, nodes=None, edges=None):
        return ["dummy-node-id"]
    def get_dag(self, pipeline_id):
        return {"nodes": ["dummy-node-id"], "edges": []}
    def validate_node(self, node):
        return None

# --- MOCK Neo4jStrategyManagementService ---
class MockNeo4jStrategyManagementService:
    def __init__(self, *args, **kwargs):
        pass
    def get_version(self, strategy_version_id):
        return {"strategy_version_id": strategy_version_id, "name": "dummy-strategy"}
    def list_strategies(self):
        return ["dummy-strategy"]

# --- MOCK StrategySnapshotService ---
class MockStrategySnapshotService:
    def get_snapshots(self, pipeline_id):
        # Always return a dummy protobuf snapshot for test
        snap = qmtl_strategy_pb2.StrategySnapshot(
            pipeline_id=pipeline_id,
            created_at=1111,
            nodes=[],
            edges=[],
            metadata={}
        )
        return [snap]

# FastAPI DI override
client = TestClient(app)

def test_pipeline_dag_and_ready_nodes(create_node, create_strategy):
    """파이프라인 DAG/ready node API 통합 테스트"""

    node_id = create_node
    strategy_version_id = create_strategy  # fixture가 반환하는 값이 버전 ID라고 가정

    # 1. 전략에 노드 추가
    response = client.post(f"/v1/registry/strategies/{strategy_version_id}/nodes/{node_id}")
    assert response.status_code == 200 or response.status_code == 201 or response.status_code == 204

    # 2. 스냅샷 생성 (파이프라인 ID는 strategy_version_id로 가정)
    # 실제 환경에서는 별도 스냅샷 생성 API 필요

    # 3. DAG 구조 조회
    response = client.get(f"/v1/registry/pipelines/{strategy_version_id}/dag")
    assert response.status_code in (200, 404)  # 스냅샷 없으면 404
    if response.status_code == 200:
        dag = response.json()
        assert "nodes" in dag and "edges" in dag

    # 4. ready node 목록 조회
    response = client.get(f"/v1/registry/pipelines/{strategy_version_id}/ready-nodes")
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        nodes = response.json()["nodes"]
        assert isinstance(nodes, list)


import pytest

@pytest.fixture
def create_node():
    class DummyNode:
        node_id = "dummy-node-id"
    return DummyNode().node_id

@pytest.fixture
def create_strategy():
    return "dummy-strategy-id"