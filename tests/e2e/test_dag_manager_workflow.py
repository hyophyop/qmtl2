from unittest.mock import MagicMock
from qmtl.dag_manager.registry.services.node.management import Neo4jNodeManagementService


def test_dag_manager_workflow(monkeypatch):
    service = Neo4jNodeManagementService(neo4j_client=MagicMock())
    # 1. 노드 생성 및 전략 노드 목록 반환
    dummy_nodes = [
        MagicMock(node_id="n1", dependencies=[]),
        MagicMock(node_id="n2", dependencies=["n1"]),
    ]
    monkeypatch.setattr(service, "get_strategy_nodes", lambda x: dummy_nodes)
    # 2. DAG 빌드/검증
    node_map, topo_result = service.get_strategy_dag("dummy_strategy")
    assert set(node_map.keys()) == {"n1", "n2"}
    # 3. ready 노드 선별
    node_status_map = {"n1": "READY", "n2": "PENDING"}
    ready_nodes = service.get_ready_nodes("dummy_strategy", node_status_map)
    assert any(n.node_id == "n1" for n in ready_nodes)
    # 4. 큐 등록 및 상태 갱신
    queue_repo = MagicMock()
    status_service = MagicMock()
    result = service.enqueue_ready_nodes(ready_nodes, queue_repo, status_service)
    queue_repo.push.assert_called_with("n1")
    status_service.update_node_status.assert_called_with("n1", "READY")
    assert result == ready_nodes
