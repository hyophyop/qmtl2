"""
Neo4j 데이터 스키마 및 마이그레이션 스크립트
- DataNode, StrategyVersion, ActivationHistory 노드 및 관계 정의
- 인덱스 및 제약조건 생성
"""

from qmtl.common.db.neo4j_client import Neo4jClient


def get_schema_cypher():
    return [
        # DataNode 노드
        """
        CREATE CONSTRAINT IF NOT EXISTS FOR (n:DataNode)
        REQUIRE n.node_id IS UNIQUE;
        """,
        # StrategyVersion 노드
        """
        CREATE CONSTRAINT IF NOT EXISTS FOR (s:StrategyVersion)
        REQUIRE s.version_id IS UNIQUE;
        """,
        # ActivationHistory 노드
        """
        CREATE CONSTRAINT IF NOT EXISTS FOR (a:ActivationHistory)
        REQUIRE (a.strategy_id, a.version_id, a.activated_at) IS UNIQUE;
        """,
        # DEPENDS_ON 관계 인덱스 (빠른 탐색)
        """
        CREATE INDEX IF NOT EXISTS FOR ()-[r:DEPENDS_ON]-() ON (r);
        """,
        # CONTAINS 관계 인덱스
        """
        CREATE INDEX IF NOT EXISTS FOR ()-[r:CONTAINS]-() ON (r);
        """,
        # ACTIVATED_BY 관계 인덱스
        """
        CREATE INDEX IF NOT EXISTS FOR ()-[r:ACTIVATED_BY]-() ON (r);
        """,
        # 태그/인터벌/피리어드 인덱스 (태그 기반 쿼리 최적화)
        """
        CREATE INDEX IF NOT EXISTS FOR (n:DataNode) ON (n.tags.predefined);
        """,
        """
        CREATE INDEX IF NOT EXISTS FOR (n:DataNode) ON (n.tags.custom);
        """,
        """
        CREATE INDEX IF NOT EXISTS FOR (n:DataNode) ON (n.interval_settings.interval);
        """,
        """
        CREATE INDEX IF NOT EXISTS FOR (n:DataNode) ON (n.interval_settings.period);
        """,
    ]


def init_neo4j_schema(client: Neo4jClient):
    """
    Neo4j에 스키마(제약조건/인덱스) 적용
    """
    for cypher in get_schema_cypher():
        client.execute_query(cypher)
