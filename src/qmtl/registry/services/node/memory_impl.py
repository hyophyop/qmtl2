from threading import Lock
from typing import Dict, List, Optional

from qmtl.models.datanode import DataNode, NodeTags
from qmtl.models.status import NodeStatus

from .management import NodeManagementService


class InMemoryNodeService(NodeManagementService):
    def __init__(self):
        self._nodes: Dict[str, DataNode] = {}
        self._lock = Lock()
        # 노드-전략 참조 관계 저장용 Dictionary
        self._node_strategy_map: Dict[str, List[str]] = {}  # node_id -> [strategy_version_id]
        self._strategy_node_map: Dict[str, List[str]] = {}  # strategy_version_id -> [node_id]
        # 노드 상태 저장용 Dictionary
        self._node_statuses: Dict[str, NodeStatus] = {}

    def create_node(self, node: DataNode) -> str:
        """
        Create a node in the registry.
        Ensures that the node object is properly handled as a Pydantic v2 model.
        """
        with self._lock:
            # Ensure we're using proper Pydantic v2 model with standardized tags
            if node.tags is None:
                node.tags = NodeTags()
            self._nodes[node.node_id] = node
            return node.node_id

    def get_node(self, node_id: str) -> Optional[DataNode]:
        """Get a node by ID."""
        return self._nodes.get(node_id)

    def delete_node(self, node_id: str) -> bool:
        """Delete a node by ID."""
        with self._lock:
            if node_id in self._nodes:
                del self._nodes[node_id]
                # 노드-전략 매핑에서도 삭제
                if node_id in self._node_strategy_map:
                    # 이 노드를 참조하는 전략들의 맵에서도 삭제
                    for strategy_id in self._node_strategy_map[node_id]:
                        if strategy_id in self._strategy_node_map:
                            if node_id in self._strategy_node_map[strategy_id]:
                                self._strategy_node_map[strategy_id].remove(node_id)
                    del self._node_strategy_map[node_id]
                return True
            return False

    def list_nodes(self) -> List[DataNode]:
        """List all nodes."""
        return list(self._nodes.values())

    def list_zero_deps(self) -> List[DataNode]:
        """List nodes with no dependencies (leaf nodes)."""
        return [n for n in self._nodes.values() if not n.dependencies]

    def list_by_tags(
        self,
        tags: List[str],
        interval: Optional[str] = None,
        period: Optional[str] = None,
        match_mode: str = "AND",
    ) -> List[DataNode]:
        """
        List nodes filtered by tags, interval and period.
        Ensures proper handling of Pydantic v2 models and null values.
        """
        nodes = list(self._nodes.values())
        if tags:
            filtered_nodes = []
            for n in nodes:
                # Handle potential None values in tags properly
                predefined_tags = getattr(n.tags, "predefined", []) or []
                custom_tags = getattr(n.tags, "custom", []) or []

                # Convert predefined tags from enum to string if needed
                predefined_tag_values = [
                    t.value if hasattr(t, "value") else t for t in predefined_tags
                ]

                # Check if node matches the tags based on match_mode
                if match_mode == "AND":
                    if all(t in predefined_tag_values or t in custom_tags for t in tags):
                        filtered_nodes.append(n)
                else:  # OR mode
                    if any(t in predefined_tag_values or t in custom_tags for t in tags):
                        filtered_nodes.append(n)
            nodes = filtered_nodes

        # Filter by interval if specified
        if interval and nodes:
            nodes = [
                n
                for n in nodes
                if n.interval_settings
                and getattr(n.interval_settings, "interval", None) == interval
            ]

        # Filter by period if specified
        if period and nodes:
            nodes = [
                n
                for n in nodes
                if n.interval_settings and getattr(n.interval_settings, "period", None) == period
            ]

        return nodes

    def validate_node(self, node: DataNode) -> None:
        """Validate DataNode. Will raise ValidationError on failure."""
        from .validation import validate_node_model

        validate_node_model(node)

    def add_contains_relationship(self, strategy_version_id: str, node_id: str) -> None:
        """
        StrategyVersion과 DataNode 간 CONTAINS 관계를 생성한다.
        (파이프라인 등록/활성화 시 호출)
        """
        with self._lock:
            # 노드가 존재하는지 확인
            if node_id not in self._nodes:
                return

            # 노드->전략 매핑 업데이트
            if node_id not in self._node_strategy_map:
                self._node_strategy_map[node_id] = []
            if strategy_version_id not in self._node_strategy_map[node_id]:
                self._node_strategy_map[node_id].append(strategy_version_id)

            # 전략->노드 매핑 업데이트
            if strategy_version_id not in self._strategy_node_map:
                self._strategy_node_map[strategy_version_id] = []
            if node_id not in self._strategy_node_map[strategy_version_id]:
                self._strategy_node_map[strategy_version_id].append(node_id)

    def remove_contains_relationship(self, strategy_version_id: str, node_id: str) -> None:
        """
        StrategyVersion과 DataNode 간 CONTAINS 관계를 삭제한다.
        (파이프라인 비활성화/삭제 시 호출)
        """
        with self._lock:
            # 노드->전략 매핑에서 삭제
            if node_id in self._node_strategy_map:
                if strategy_version_id in self._node_strategy_map[node_id]:
                    self._node_strategy_map[node_id].remove(strategy_version_id)
                    # 빈 리스트가 되면 키 자체를 삭제
                    if not self._node_strategy_map[node_id]:
                        del self._node_strategy_map[node_id]

            # 전략->노드 매핑에서 삭제
            if strategy_version_id in self._strategy_node_map:
                if node_id in self._strategy_node_map[strategy_version_id]:
                    self._strategy_node_map[strategy_version_id].remove(node_id)
                    # 빈 리스트가 되면 키 자체를 삭제
                    if not self._strategy_node_map[strategy_version_id]:
                        del self._strategy_node_map[strategy_version_id]

    def get_node_ref_count(self, node_id: str) -> int:
        """
        해당 DataNode를 참조하는 StrategyVersion(CONTAINS 관계) 개수를 반환한다.
        """
        with self._lock:
            if node_id not in self._node_strategy_map:
                return 0
            return len(self._node_strategy_map[node_id])

    def get_node_ref_strategies(self, node_id: str) -> list[str]:
        """
        해당 DataNode를 참조하는 모든 StrategyVersion(version_id) 목록을 반환한다.
        """
        with self._lock:
            if node_id not in self._node_strategy_map:
                return []
            return self._node_strategy_map[node_id].copy()

    def get_strategy_nodes(self, strategy_version_id: str) -> List[DataNode]:
        """
        특정 전략 버전에 포함된 모든 노드 목록을 반환한다.
        """
        with self._lock:
            if strategy_version_id not in self._strategy_node_map:
                return []
            return [
                self._nodes[node_id]
                for node_id in self._strategy_node_map[strategy_version_id]
                if node_id in self._nodes
            ]

    def get_node_status(self, node_id: str) -> Optional[NodeStatus]:
        """해당 DataNode의 상태/메타데이터를 조회한다."""
        with self._lock:
            return self._node_statuses.get(node_id)

    def update_node_status(self, node_id: str, status: NodeStatus) -> None:
        """해당 DataNode의 상태/메타데이터를 저장/갱신한다."""
        with self._lock:
            self._node_statuses[node_id] = status
