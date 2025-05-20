# NodeManagementService의 메서드가 아닌, 클래스 내부에 정의되어야 하므로 아래로 이동
from abc import ABC, abstractmethod
from typing import List, Optional

from qmtl.common.db.neo4j_client import Neo4jClient
from qmtl.common.errors.exceptions import DatabaseError
from qmtl.models.datanode import DataNode
from qmtl.models.generated.qmtl_status_pb2 import NodeStatus

from .validation import validate_node_model
from qmtl.dag_manager.core.graph_builder import GraphBuilder
from qmtl.dag_manager.core.ready_node_selector import ReadyNodeSelector
from qmtl.dag_manager.core.queue_worker import QueueWorker


class NodeManagementService(ABC):
    @abstractmethod
    def create_node(self, node: DataNode) -> str:
        """DataNode를 등록하고 node_id를 반환한다."""

    @abstractmethod
    def get_node(self, node_id: str) -> Optional[DataNode]:
        """node_id로 DataNode를 조회한다."""

    @abstractmethod
    def delete_node(self, node_id: str) -> bool:
        """node_id로 DataNode를 삭제한다."""

    @abstractmethod
    def list_nodes(self) -> List[DataNode]:
        """모든 DataNode 목록을 반환한다."""

    @abstractmethod
    def list_zero_deps(self) -> List[DataNode]:
        """의존성이 없는(leaf) DataNode 목록을 반환한다."""

    @abstractmethod
    def list_by_tags(
        self, tags: list[str], interval: str = None, period: str = None, match_mode: str = "AND"
    ) -> List[DataNode]:
        """태그/인터벌/피리어드 기반 노드 목록 반환 (AND/OR 지원)"""

    @abstractmethod
    def add_contains_relationship(self, strategy_version_id: str, node_id: str) -> None:
        """StrategyVersion과 DataNode 간 CONTAINS 관계를 생성한다."""

    @abstractmethod
    def remove_contains_relationship(self, strategy_version_id: str, node_id: str) -> None:
        """StrategyVersion과 DataNode 간 CONTAINS 관계를 삭제한다."""

    @abstractmethod
    def get_node_ref_count(self, node_id: str) -> int:
        """해당 DataNode를 참조하는 StrategyVersion 개수를 반환한다."""

    @abstractmethod
    def get_node_ref_strategies(self, node_id: str) -> list[str]:
        """해당 DataNode를 참조하는 모든 StrategyVersion(version_id) 목록을 반환한다."""

    @abstractmethod
    def get_strategy_nodes(self, strategy_version_id: str) -> List[DataNode]:
        """특정 전략 버전에 포함된 모든 노드 목록을 반환한다."""

    @abstractmethod
    def get_node_status(self, node_id: str) -> Optional[NodeStatus]:
        """해당 DataNode의 상태/메타데이터를 조회한다."""

    @abstractmethod
    def update_node_status(self, node_id: str, status: NodeStatus) -> None:
        """해당 DataNode의 상태/메타데이터를 저장/갱신한다."""

    @abstractmethod
    def get_node_dependencies(self, node_id: str) -> list[str]:
        """해당 DataNode가 의존하는 노드 ID 목록을 반환한다."""

    @abstractmethod
    def add_dependency(self, node_id: str, dependency_id: str) -> None:
        """DataNode 간 DEPENDS_ON 관계를 생성한다."""

    @abstractmethod
    def remove_dependency(self, node_id: str, dependency_id: str) -> None:
        """DataNode 간 DEPENDS_ON 관계를 삭제한다."""

    @abstractmethod
    def validate_node(self, node: DataNode) -> None:
        """DataNode 유효성 검증. 실패 시 ValidationError 발생."""


class Neo4jNodeManagementService(NodeManagementService):
    def __init__(self, neo4j_client: Neo4jClient, database: str = None):
        self.neo4j_client = neo4j_client
        self.database = database

    def create_node(self, node: DataNode) -> str:
        """DataNode를 Neo4j에 등록하고 node_id를 반환한다."""
        # 이미 존재하는지 확인
        check_query = """
        MATCH (n:DataNode {node_id: $node_id}) RETURN n LIMIT 1
        """
        exists = self.neo4j_client.execute_query(
            check_query, {"node_id": node.node_id}, self.database
        )
        if exists:
            raise DatabaseError(f"DataNode already exists: {node.node_id}")
        # 저장
        create_query = """
        CREATE (n:DataNode {
            node_id: $node_id,
            type: $type,
            data_format: $data_format,
            params: $params,
            dependencies: $dependencies,
            ttl: $ttl,
            tags: $tags,
            interval_settings: $interval_settings,
            stream_settings: $stream_settings
        })
        RETURN n.node_id AS node_id
        """
        # 복잡한 객체를 JSON 문자열로 직렬화
        import json

        tags_dict = json.dumps(node.tags.model_dump() if node.tags else {})
        interval_settings_dict = json.dumps(
            node.interval_settings.model_dump() if node.interval_settings else None
        )
        stream_settings_dict = json.dumps(
            node.stream_settings.model_dump() if node.stream_settings else None
        )
        params = {
            "node_id": node.node_id,
            "type": node.type.value if node.type else None,
            "data_format": json.dumps(node.data_format) if node.data_format else None,
            "params": json.dumps(node.params) if node.params else None,
            "dependencies": node.dependencies,
            "ttl": node.ttl,
            "tags": tags_dict,
            "interval_settings": interval_settings_dict,
            "stream_settings": stream_settings_dict,
        }
        result = self.neo4j_client.execute_query(create_query, params, self.database)
        if not result:
            raise DatabaseError("Failed to create DataNode")
        return result[0]["node_id"]

    def get_node(self, node_id: str) -> Optional[DataNode]:
        """node_id로 DataNode를 조회한다."""
        query = """
        MATCH (n:DataNode {node_id: $node_id}) RETURN n LIMIT 1
        """
        result = self.neo4j_client.execute_query(query, {"node_id": node_id}, self.database)
        if not result:
            return None
        node_data = result[0]["n"]

        # JSON 문자열로 저장된 필드들을 다시 파싱
        import json

        try:
            # 데이터 포맷, 파라미터, 태그, 인터벌 설정을 JSON에서 파싱
            if isinstance(node_data.get("data_format"), str):
                node_data["data_format"] = json.loads(node_data["data_format"])
            if isinstance(node_data.get("params"), str):
                node_data["params"] = json.loads(node_data["params"])
            if isinstance(node_data.get("tags"), str):
                node_data["tags"] = json.loads(node_data["tags"])
            if isinstance(node_data.get("interval_settings"), str):
                node_data["interval_settings"] = json.loads(node_data["interval_settings"])
            if isinstance(node_data.get("stream_settings"), str):
                node_data["stream_settings"] = json.loads(node_data["stream_settings"])

            return DataNode.model_validate(node_data)
        except Exception as e:
            raise DatabaseError(f"Invalid DataNode format: {e}")

    def delete_node(self, node_id: str) -> bool:
        """node_id로 DataNode를 삭제한다."""
        query = """
        MATCH (n:DataNode {node_id: $node_id}) DETACH DELETE n RETURN COUNT(n) AS deleted
        """
        result = self.neo4j_client.execute_query(query, {"node_id": node_id}, self.database)
        return result and result[0].get("deleted", 0) > 0

    def list_nodes(self) -> List[DataNode]:
        """모든 DataNode 목록을 반환한다."""
        query = """
        MATCH (n:DataNode) RETURN n
        """
        result = self.neo4j_client.execute_query(query, {}, self.database)
        nodes = []
        import json

        for row in result:
            try:
                node_data = row["n"]
                # JSON 문자열로 저장된 필드들을 다시 파싱
                if isinstance(node_data.get("data_format"), str):
                    node_data["data_format"] = json.loads(node_data["data_format"])
                if isinstance(node_data.get("params"), str):
                    node_data["params"] = json.loads(node_data["params"])
                if isinstance(node_data.get("tags"), str):
                    node_data["tags"] = json.loads(node_data["tags"])
                if isinstance(node_data.get("interval_settings"), str):
                    node_data["interval_settings"] = json.loads(node_data["interval_settings"])
                if isinstance(node_data.get("stream_settings"), str):
                    node_data["stream_settings"] = json.loads(node_data["stream_settings"])

                nodes.append(DataNode.model_validate(node_data))
            except Exception:
                continue
        return nodes

    def list_zero_deps(self) -> List[DataNode]:
        """의존성이 없는(leaf) DataNode 목록을 반환한다."""
        query = """
        MATCH (n:DataNode) WHERE size(n.dependencies) = 0 RETURN n
        """
        result = self.neo4j_client.execute_query(query, {}, self.database)
        nodes = []
        import json

        for row in result:
            try:
                node_data = row["n"]
                # JSON 문자열로 저장된 필드들을 다시 파싱
                if isinstance(node_data.get("data_format"), str):
                    node_data["data_format"] = json.loads(node_data["data_format"])
                if isinstance(node_data.get("params"), str):
                    node_data["params"] = json.loads(node_data["params"])
                if isinstance(node_data.get("tags"), str):
                    node_data["tags"] = json.loads(node_data["tags"])
                if isinstance(node_data.get("interval_settings"), str):
                    node_data["interval_settings"] = json.loads(node_data["interval_settings"])
                if isinstance(node_data.get("stream_settings"), str):
                    node_data["stream_settings"] = json.loads(node_data["stream_settings"])

                nodes.append(DataNode.model_validate(node_data))
            except Exception:
                continue
        return nodes

    def list_by_tags(
        self, tags: list[str], interval: str = None, period: str = None, match_mode: str = "AND"
    ) -> List[DataNode]:
        """태그/인터벌/피리어드 기반 노드 목록 반환 (AND/OR 지원)"""
        # 로컬에서 TagFilterParams를 정의하여 import 오류 방지
        from pydantic import BaseModel, Field
        from typing import List, Optional, Literal

        class TagFilterParams(BaseModel):
            tags: List[str] = Field(default_factory=list)
            interval: Optional[str] = None
            period: Optional[str] = None
            match_mode: Literal["AND", "OR"] = "AND"
            model_config = {"extra": "forbid"}

        # Pydantic 모델로 매개변수 유효성 검증
        filter_params = TagFilterParams(
            tags=tags,
            interval=interval,
            period=period,
            match_mode=match_mode,
        )

        # 태그 필터 Cypher
        tag_cond = ""
        if filter_params.tags:
            if filter_params.match_mode == "AND":
                tag_cond = " AND ".join(
                    [
                        f"$tag{i} IN n.tags.predefined OR $tag{i} IN n.tags.custom"
                        for i in range(len(filter_params.tags))
                    ]
                )
            else:
                tag_cond = " OR ".join(
                    [
                        f"$tag{i} IN n.tags.predefined OR $tag{i} IN n.tags.custom"
                        for i in range(len(filter_params.tags))
                    ]
                )

        interval_cond = ""
        if filter_params.interval:
            interval_cond = "n.interval_settings.interval = $interval"

        period_cond = ""
        if filter_params.period:
            period_cond = "n.interval_settings.period = $period"

        conds = [c for c in [tag_cond, interval_cond, period_cond] if c]
        where_clause = f"WHERE {' AND '.join(conds)}" if conds else ""

        query = f"""
        MATCH (n:DataNode)
        {where_clause}
        RETURN n
        """

        params = {f"tag{i}": t for i, t in enumerate(filter_params.tags)}
        if filter_params.interval:
            params["interval"] = filter_params.interval
        if filter_params.period:
            params["period"] = filter_params.period

        result = self.neo4j_client.execute_query(
            query,
            params,
            self.database,
        )

        nodes = []
        import json

        for row in result:
            try:
                node_data = row["n"]
                # JSON 문자열로 저장된 필드들을 다시 파싱
                if isinstance(node_data.get("data_format"), str):
                    node_data["data_format"] = json.loads(node_data["data_format"])
                if isinstance(node_data.get("params"), str):
                    node_data["params"] = json.loads(node_data["params"])
                if isinstance(node_data.get("tags"), str):
                    node_data["tags"] = json.loads(node_data["tags"])
                if isinstance(node_data.get("interval_settings"), str):
                    node_data["interval_settings"] = json.loads(node_data["interval_settings"])
                if isinstance(node_data.get("stream_settings"), str):
                    node_data["stream_settings"] = json.loads(node_data["stream_settings"])

                nodes.append(DataNode.model_validate(node_data))
            except Exception:
                continue

        return nodes

    def validate_node(self, node: DataNode) -> None:
        """DataNode 유효성 검증. 실패 시 ValidationError 발생."""
        validate_node_model(node)

    def add_contains_relationship(self, strategy_version_id: str, node_id: str) -> None:
        """
        StrategyVersion과 DataNode 간 CONTAINS 관계를 생성한다.
        (파이프라인 등록/활성화 시 호출)
        """
        query = (
            "MATCH (s:StrategyVersion {version_id: $strategy_version_id}), "
            "(n:DataNode {node_id: $node_id}) "
            "MERGE (s)-[:CONTAINS]->(n)"
        )
        self.neo4j_client.execute_query(
            query,
            {"strategy_version_id": strategy_version_id, "node_id": node_id},
            self.database,
        )

    def remove_contains_relationship(self, strategy_version_id: str, node_id: str) -> None:
        """
        StrategyVersion과 DataNode 간 CONTAINS 관계를 삭제한다.
        (파이프라인 비활성화/삭제 시 호출)
        """
        query = (
            "MATCH (s:StrategyVersion {version_id: $strategy_version_id})-"
            "[r:CONTAINS]->(n:DataNode {node_id: $node_id}) "
            "DELETE r"
        )
        self.neo4j_client.execute_query(
            query,
            {"strategy_version_id": strategy_version_id, "node_id": node_id},
            self.database,
        )

    def get_node_ref_count(self, node_id: str) -> int:
        """
        해당 DataNode를 참조하는 StrategyVersion(CONTAINS 관계) 개수를 반환한다.
        """
        query = """
        MATCH (s:StrategyVersion)-[:CONTAINS]->(n:DataNode {node_id: $node_id})
        RETURN COUNT(s) AS ref_count
        """
        result = self.neo4j_client.execute_query(query, {"node_id": node_id}, self.database)
        if not result:
            return 0
        return result[0].get("ref_count", 0)

    def get_node_ref_strategies(self, node_id: str) -> list[str]:
        """
        해당 DataNode를 참조하는 모든 StrategyVersion(version_id) 목록을 반환한다.
        """
        query = """
        MATCH (s:StrategyVersion)-[:CONTAINS]->(n:DataNode {node_id: $node_id})
        RETURN s.version_id AS version_id
        """
        result = self.neo4j_client.execute_query(query, {"node_id": node_id}, self.database)
        return [row["version_id"] for row in result] if result else []

    def get_strategy_nodes(self, strategy_version_id: str) -> List[DataNode]:
        """
        특정 전략 버전에 포함된 모든 노드 목록을 반환한다.
        """
        query = """
        MATCH (s:StrategyVersion {version_id: $strategy_version_id})-[:CONTAINS]->(n:DataNode)
        RETURN n
        """
        result = self.neo4j_client.execute_query(
            query, {"strategy_version_id": strategy_version_id}, self.database
        )
        nodes = []
        import json

        for row in result:
            try:
                node_data = row["n"]
                # JSON 문자열로 저장된 필드들을 다시 파싱
                if isinstance(node_data.get("data_format"), str):
                    node_data["data_format"] = json.loads(node_data["data_format"])
                if isinstance(node_data.get("params"), str):
                    node_data["params"] = json.loads(node_data["params"])
                if isinstance(node_data.get("tags"), str):
                    node_data["tags"] = json.loads(node_data["tags"])
                if isinstance(node_data.get("interval_settings"), str):
                    node_data["interval_settings"] = json.loads(node_data["interval_settings"])
                if isinstance(node_data.get("stream_settings"), str):
                    node_data["stream_settings"] = json.loads(node_data["stream_settings"])

                nodes.append(DataNode.model_validate(node_data))
            except Exception:
                continue
        return nodes

    def get_node_status(self, node_id: str) -> Optional[NodeStatus]:
        """해당 DataNode의 상태/메타데이터를 조회한다."""
        query = """
        MATCH (s:NodeStatus {node_id: $node_id}) RETURN s LIMIT 1
        """
        try:
            result = self.neo4j_client.execute_query(query, {"node_id": node_id}, self.database)
            if not result:
                return None
            status_data = result[0]["s"]
            return NodeStatus.model_validate(status_data)
        except Exception as e:
            raise DatabaseError(f"NodeStatus 조회 실패: {e}")

    def update_node_status(self, node_id: str, status: NodeStatus) -> None:
        """해당 DataNode의 상태/메타데이터를 저장/갱신한다."""
        query = """
        MERGE (s:NodeStatus {node_id: $node_id})
        SET s.status = $status,
            s.start_time = $start_time,
            s.end_time = $end_time,
            s.result = $result,
            s.resource = $resource,
            s.meta = $meta
        RETURN s
        """
        data = status.model_dump()
        params = {
            "node_id": node_id,
            "status": data.get("status"),
            "start_time": data.get("start_time"),
            "end_time": data.get("end_time"),
            "result": data.get("result"),
            "resource": data.get("resource"),
            "meta": data.get("meta"),
        }
        try:
            self.neo4j_client.execute_query(query, params, self.database)
        except Exception as e:
            raise DatabaseError(f"NodeStatus 저장/갱신 실패: {e}")

    def get_node_dependencies(self, node_id: str) -> list[str]:
        """
        해당 DataNode가 의존하는 노드 ID 목록을 반환한다.
        """
        query = """
        MATCH (n:DataNode {node_id: $node_id})-[:DEPENDS_ON]->(dep:DataNode)
        RETURN dep.node_id AS dependency_id
        """
        result = self.neo4j_client.execute_query(query, {"node_id": node_id}, self.database)
        return [row["dependency_id"] for row in result] if result else []

    def add_dependency(self, node_id: str, dependency_id: str) -> None:
        """
        DataNode 간 DEPENDS_ON 관계를 생성한다.
        """
        query = (
            "MATCH (n:DataNode {node_id: $node_id}), (dep:DataNode {node_id: $dependency_id}) "
            "MERGE (n)-[:DEPENDS_ON]->(dep)"
        )
        self.neo4j_client.execute_query(
            query, {"node_id": node_id, "dependency_id": dependency_id}, self.database
        )

    def remove_dependency(self, node_id: str, dependency_id: str) -> None:
        """
        DataNode 간 DEPENDS_ON 관계를 삭제한다.
        """
        query = (
            "MATCH (n:DataNode {node_id: $node_id})-[r:DEPENDS_ON]->(dep:DataNode {node_id: $dependency_id}) "
            "DELETE r"
        )
        self.neo4j_client.execute_query(
            query, {"node_id": node_id, "dependency_id": dependency_id}, self.database
        )

    def get_strategy_dag(self, strategy_version_id: str):
        """특정 전략 버전의 노드 리스트로 DAG 빌드/검증 결과 반환"""
        nodes = self.get_strategy_nodes(strategy_version_id)
        builder = GraphBuilder(nodes)
        node_map, topo_result = builder.build_dag()
        return node_map, topo_result

    def get_ready_nodes(
        self, strategy_version_id: str, node_status_map: dict[str, str]
    ) -> list[DataNode]:
        """core ReadyNodeSelector를 활용해 ready 노드 반환"""
        nodes = self.get_strategy_nodes(strategy_version_id)
        selector = ReadyNodeSelector(nodes, node_status_map)
        return selector.get_ready_nodes()

    def enqueue_ready_nodes(self, ready_nodes: list[DataNode], queue_repo, status_service):
        """core QueueWorker를 활용해 ready 노드 큐 등록 및 상태 갱신"""
        worker = QueueWorker(
            push_fn=queue_repo.push,
            update_status_fn=status_service.update_node_status,
            complete_fn=queue_repo.complete,
        )
        return worker.enqueue_ready_nodes(ready_nodes)
