from __future__ import annotations

"""ReadyNodeSelector
====================
실행 가능한(ready) 노드 선별 로직.

기준
-----
1. 노드 상태는 node_status_map[node_id]로 전달받음
   - status 가 None 또는 "PENDING" 또는 "READY" 여야 대기 상태로 간주
2. 노드의 모든 upstream(dependencies) 이 COMPLETED 여야 현재 노드 ready
3. 결과는 위상정렬 순서(앞 노드 우선)를 유지한 DataNode 리스트로 반환
"""

from typing import List, Dict
from qmtl.models.datanode import DataNode
from .graph_builder import GraphBuilder

_PENDING_STATES = {None, "PENDING", "READY"}
_COMPLETED_STATES = {"COMPLETED"}


class ReadyNodeSelector:
    """위상정렬 + 상태 기반 실행 가능 노드 계산"""

    def __init__(self, nodes: List[DataNode], node_status_map: Dict[str, str]):
        self.nodes = nodes
        self.node_status_map = node_status_map  # node_id -> status(str)
        self.graph_builder = GraphBuilder(nodes)

    def get_ready_nodes(self) -> List[DataNode]:
        """ready 상태 노드 목록을 반환한다."""
        node_map, topo = self.graph_builder.build_dag()
        edges_map = self._reverse_adjacency_list()

        ready_nodes: List[DataNode] = []
        for node_id in topo.order:
            state = self.node_status_map.get(node_id)
            if state not in _PENDING_STATES:
                continue
            deps = edges_map.get(node_id, [])
            if all(self.node_status_map.get(dep_id) in _COMPLETED_STATES for dep_id in deps):
                ready_nodes.append(node_map[node_id])
        return ready_nodes

    def _reverse_adjacency_list(self) -> Dict[str, List[str]]:
        """노드별로 upstream(dependencies) 목록을 반환한다."""
        edges_map: Dict[str, List[str]] = {n.node_id: [] for n in self.nodes}
        for node in self.nodes:
            for dep in node.dependencies:
                edges_map[node.node_id].append(dep)
        return edges_map
