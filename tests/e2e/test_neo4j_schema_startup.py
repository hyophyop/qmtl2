import pytest
from qmtl.common.db.connection_pool import get_neo4j_pool
from qmtl.dag_manager.registry.services.node.neo4j_schema import get_schema_cypher

def test_neo4j_schema_startup_applies_indexes(monkeypatch):
    """
    [NG-DAG-10] 서비스 기동 시 인덱스/제약조건 자동 점검/생성 테스트
    실제 쿼리 실행 대신 쿼리 호출 여부만 검증 (통합테스트 환경)
    """
    pool = get_neo4j_pool()
    client = pool.get_client()
    executed = []
    
    def fake_execute_query(cypher):
        executed.append(cypher.strip())
    monkeypatch.setattr(client, "execute_query", fake_execute_query)

    # 실제 init_neo4j_schema 호출
    from qmtl.dag_manager.registry.services.node.neo4j_schema import init_neo4j_schema
    init_neo4j_schema(client)

    # 모든 쿼리가 정상적으로 호출되었는지 확인
    expected = [c.strip() for c in get_schema_cypher()]
    for cypher in expected:
        assert cypher in executed
    assert len(executed) == len(expected)
