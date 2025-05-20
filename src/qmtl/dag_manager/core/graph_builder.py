from __future__ import annotations

"""GraphBuilder
================
DataNode 리스트를 받아 메모리 DAG를 구성·검증하는 유틸리티.

- DataNode.dependencies 필드를 기반으로 위상정렬·사이클 검증 수행
- 결과로 DAG 인접리스트 및 정렬 결과를 반환
"""

from typing import List, Dict, Tuple
from qmtl.models.datanode import DataNode, TopoSortResult


class GraphBuilder:
    """글로벌 DAG(또는 전략 단위 DAG) 빌드를 담당하는 헬퍼 클래스."""

    def __init__(self, nodes: List[DataNode]):
        self.nodes = nodes

    # ---------------------------------------------------------------------
    # Public helpers
    # ---------------------------------------------------------------------
    def build_dag(self) -> Tuple[Dict[str, DataNode], TopoSortResult]:
        """DataNode 리스트를 기반으로 DAG를 구축·검증한다.

        Returns:
            (node_map, topo_sort_result)
        """
        node_map = {n.node_id: n for n in self.nodes}
        topo_result = self.get_topological_sort_result()
        return node_map, topo_result

    def get_topological_sort_result(self) -> TopoSortResult:
        """DataNode 리스트를 기반으로 위상정렬 결과를 반환한다."""
        # 실제 위상정렬 알고리즘 구현 (예시)
        order = []
        visited = set()
        temp_mark = set()
        node_map = {n.node_id: n for n in self.nodes}

        def visit(nid):
            if nid in visited:
                return
            if nid in temp_mark:
                raise ValueError("Cycle detected")
            temp_mark.add(nid)
            for dep in node_map[nid].dependencies:
                visit(dep)
            temp_mark.remove(nid)
            visited.add(nid)
            order.append(nid)

        for n in self.nodes:
            visit(n.node_id)
        return TopoSortResult(order=order)

    # ------------------------------------------------------------------
    # Static helpers
    # ------------------------------------------------------------------
    @staticmethod
    def derive_edges(nodes: List[DataNode]) -> List[Dict[str, str]]:
        """DataNode.dependencies 를 edge 형태로 변환한다."""
        edges: List[Dict[str, str]] = []
        for node in nodes:
            for dep in node.dependencies:
                edges.append({"source": dep, "target": node.node_id})
        return edges
