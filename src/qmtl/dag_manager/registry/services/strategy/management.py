from abc import ABC, abstractmethod
from typing import List, Optional

from qmtl.models.generated.qmtl_strategy_pb2 import StrategyMetadata, StrategyVersion


from qmtl.common.db.neo4j_client import Neo4jClient
from qmtl.common.errors.exceptions import DatabaseError


class StrategyManagementService(ABC):
    @abstractmethod
    def get_version(self, version_id: str) -> Optional[StrategyVersion]:
        pass

    @abstractmethod
    def list_strategies(self) -> List[StrategyVersion]:
        pass


# MULTI-4: Neo4j 구현체 (스텁)
class Neo4jStrategyManagementService(StrategyManagementService):
    def __init__(self, neo4j_client: Neo4jClient, database: str = None):
        self.neo4j_client = neo4j_client
        self.database = database

    def get_version(self, version_id: str) -> Optional[StrategyVersion]:
        # 실제 구현에서는 Cypher 쿼리로 조회
        # 여기서는 None 반환 (스텁)
        return None

    def list_strategies(self) -> List[StrategyVersion]:
        # 실제 구현에서는 Cypher 쿼리로 전체 조회
        # 여기서는 빈 리스트 반환 (스텁)
        return []
