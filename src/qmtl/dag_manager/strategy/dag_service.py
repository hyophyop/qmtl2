from collections import defaultdict, deque
from typing import Dict, List, Optional

from qmtl.common.errors.exceptions import CyclicDependencyError
from qmtl.models.datanode import DataNode, TopoSortResult


class DAGService:
    """DataNode DAG 구성 및 관리를 위한 서비스"""

    def __init__(self):
        self.reset()

    def reset(self):
        """DAG 상태 초기화"""
        self.nodes: Dict[str, DataNode] = {}
        self.adjacency_list: Dict[str, List[str]] = defaultdict(list)
        self.reverse_adjacency_list: Dict[str, List[str]] = defaultdict(list)
        self.verified = False

    def add_node(self, node: DataNode) -> None:
        """DAG에 노드 추가

        Args:
            node: 추가할 DataNode
        """
        self.nodes[node.node_id] = node
        # 노드의 의존성 기반으로 adjacency list 업데이트
        for dep_id in node.dependencies:
            self.reverse_adjacency_list[node.node_id].append(dep_id)
            self.adjacency_list[dep_id].append(node.node_id)

        # 의존성이 없는 노드의 경우 빈 리스트로 초기화
        if not node.dependencies:
            self.reverse_adjacency_list[node.node_id] = []

        # 어떤 노드의 의존 대상이 아닌 노드의 경우 빈 리스트로 초기화
        if node.node_id not in self.adjacency_list:
            self.adjacency_list[node.node_id] = []

        # 변경으로 인해 사이클 검증 상태 무효화
        self.verified = False

    def build_dag(self, nodes: List[DataNode]) -> None:
        """노드 리스트로부터 DAG 구성

        Args:
            nodes: DataNode 리스트
        """
        self.reset()
        for node in nodes:
            self.add_node(node)
        self.verify_acyclic()

    def verify_acyclic(self) -> bool:
        """DAG에 사이클이 없는지 확인

        Returns:
            True if no cycles, otherwise raises CyclicDependencyError

        Raises:
            CyclicDependencyError: DAG에 사이클이 있는 경우
        """
        visited = set()
        temp_stack = set()

        def dfs_detect_cycle(node_id: str) -> None:
            if node_id in temp_stack:
                # 이미 현재 경로에 있는 노드를 다시 방문하는 경우 (사이클 발견)
                cycle_path = self._find_cycle_path(node_id)
                raise CyclicDependencyError(
                    f"Cyclic dependency detected: {' -> '.join(cycle_path)}"
                )

            if node_id in visited:
                # 이미 검증된 노드는 건너뜀
                return

            temp_stack.add(node_id)
            visited.add(node_id)

            for dep_id in self.reverse_adjacency_list[node_id]:
                dfs_detect_cycle(dep_id)

            temp_stack.remove(node_id)

        # 모든 노드에 대해 DFS 순회
        for node_id in self.nodes:
            if node_id not in visited:
                dfs_detect_cycle(node_id)

        self.verified = True
        return True

    def _find_cycle_path(self, start_node_id: str) -> List[str]:
        """사이클을 찾아 경로 반환

        Args:
            start_node_id: 사이클 시작점

        Returns:
            사이클 경로 리스트
        """
        # BFS로 사이클 찾기
        visited = {start_node_id: None}
        queue = deque([(start_node_id, None)])

        while queue:
            current, parent = queue.popleft()

            for neighbor in self.reverse_adjacency_list[current]:
                if neighbor == start_node_id:
                    # 사이클 발견
                    path = [start_node_id]
                    while current != start_node_id:
                        path.append(current)
                        current = visited[current]
                    path.append(start_node_id)
                    return list(reversed(path))

                if neighbor not in visited:
                    visited[neighbor] = current
                    queue.append((neighbor, current))

        return []  # Should not reach here if cycle exists

    def get_topological_order(self) -> List[str]:
        """노드의 위상 정렬 순서 반환

        Returns:
            위상 정렬된 노드 ID 리스트
        """
        if not self.verified:
            self.verify_acyclic()

        # 각 노드의 진입 차수 계산
        in_degree = {node_id: 0 for node_id in self.nodes}

        # 각 노드가 가진 의존성을 기반으로 진입 차수 계산
        for node_id in self.nodes:
            for dep_id in self.reverse_adjacency_list[node_id]:
                # node_id는 dep_id에 의존하므로, dep_id에서 node_id로 간선이 존재
                # 따라서 node_id의 진입 차수를 증가
                in_degree[node_id] += 1

        # 진입 차수가 0인 노드 큐에 추가 (의존성이 없는 노드)
        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        topological_order = []

        while queue:
            current = queue.popleft()
            topological_order.append(current)

            # current 노드에 의존하는 노드들의 진입 차수 감소
            for dependent in self.adjacency_list[current]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # 모든 노드가 처리되었는지 확인
        if len(topological_order) != len(self.nodes):
            raise CyclicDependencyError("DAG contains a cycle")

        return topological_order

    def get_topological_sort_result(self) -> TopoSortResult:
        """노드의 위상 정렬 결과를 TopoSortResult 모델로 반환

        Returns:
            TopoSortResult 모델
        """
        order = self.get_topological_order()
        return TopoSortResult(
            order=order, node_map={node_id: self.nodes[node_id] for node_id in order}
        )

    def get_root_nodes(self) -> List[str]:
        """의존성이 없는 루트 노드 반환

        Returns:
            루트 노드 ID 리스트
        """
        return [node_id for node_id, deps in self.reverse_adjacency_list.items() if not deps]

    def get_leaf_nodes(self) -> List[str]:
        """의존하는 노드가 없는 리프 노드 반환

        Returns:
            리프 노드 ID 리스트
        """
        return [node_id for node_id, deps in self.adjacency_list.items() if not deps]

    def get_node(self, node_id: str) -> Optional[DataNode]:
        """노드 ID로 노드 반환

        Args:
            node_id: 조회할 노드 ID

        Returns:
            노드 또는 None (존재하지 않는 경우)
        """
        return self.nodes.get(node_id)

    def get_all_nodes(self) -> List[DataNode]:
        """모든 노드 반환

        Returns:
            모든 노드 리스트
        """
        return list(self.nodes.values())

    def get_dependencies(self, node_id: str) -> List[DataNode]:
        """노드의 직접 의존성 반환

        Args:
            node_id: 노드 ID

        Returns:
            의존하는 노드 리스트
        """
        if node_id not in self.reverse_adjacency_list:
            return []

        return [
            self.nodes[dep_id]
            for dep_id in self.reverse_adjacency_list[node_id]
            if dep_id in self.nodes
        ]

    def get_dependents(self, node_id: str) -> List[DataNode]:
        """노드에 의존하는 노드 반환

        Args:
            node_id: 노드 ID

        Returns:
            의존하는 노드 리스트
        """
        if node_id not in self.adjacency_list:
            return []

        return [
            self.nodes[dep_id] for dep_id in self.adjacency_list[node_id] if dep_id in self.nodes
        ]
