from typing import List, Optional
from qmtl.models.generated.qmtl_strategy_pb2 import StrategySnapshot


class StrategySnapshotService:
    """전략별 DAG 스냅샷/버전 관리/롤백 서비스 (Neo4j 연동)"""

    def __init__(self, neo4j_pool, database: str):
        self.neo4j_pool = neo4j_pool
        self.database = database

    def create_snapshot(self, snapshot: StrategySnapshot) -> str:
        """스냅샷 저장 (Neo4j에 영구 저장)"""
        # snapshot_id는 pipeline_id+created_at 조합(고유)
        snapshot_id = f"{snapshot.pipeline_id}_{snapshot.created_at}"
        with self.neo4j_pool.client() as client:
            cypher = """
            CREATE (s:StrategySnapshot {
                snapshot_id: $snapshot_id,
                pipeline_id: $pipeline_id,
                created_at: $created_at,
                snapshot_bin: $snapshot_bin
            })
            WITH s
            RETURN s.snapshot_id AS snapshot_id
            """
            params = {
                "snapshot_id": snapshot_id,
                "pipeline_id": snapshot.pipeline_id,
                "created_at": snapshot.created_at,
                "snapshot_bin": snapshot.SerializeToString(),
            }
            result = client.execute_query(cypher, params, self.database)
            if not result:
                raise Exception("스냅샷 저장 실패")
            return snapshot_id

    def get_snapshots(self, pipeline_id: str) -> List[StrategySnapshot]:
        """특정 파이프라인의 모든 스냅샷 조회"""
        with self.neo4j_pool.client() as client:
            cypher = """
            MATCH (s:StrategySnapshot {pipeline_id: $pipeline_id})
            RETURN s ORDER BY s.created_at DESC
            """
            result = client.execute_query(cypher, {"pipeline_id": pipeline_id}, self.database)
            snapshots = []
            for row in result:
                s = row["s"]
                try:
                    snapshot = StrategySnapshot()
                    snapshot.ParseFromString(s["snapshot_bin"])
                    snapshots.append(snapshot)
                except Exception:
                    continue
            return snapshots

    def rollback_to_snapshot(
        self, pipeline_id: str, snapshot_id: str
    ) -> Optional[StrategySnapshot]:
        """특정 스냅샷으로 롤백 (스냅샷 구조 반환)"""
        with self.neo4j_pool.client() as client:
            cypher = """
            MATCH (s:StrategySnapshot {snapshot_id: $snapshot_id, pipeline_id: $pipeline_id})
            RETURN s LIMIT 1
            """
            result = client.execute_query(
                cypher, {"snapshot_id": snapshot_id, "pipeline_id": pipeline_id}, self.database
            )
            if not result:
                return None
            s = result[0]["s"]
            try:
                snapshot = StrategySnapshot()
                snapshot.ParseFromString(s["snapshot_bin"])
                return snapshot
            except Exception:
                return None
