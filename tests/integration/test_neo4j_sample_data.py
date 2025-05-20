import pytest
import os

@pytest.mark.usefixtures("neo4j_clean")
def test_load_sample_data(neo4j_session):
    """
    샘플 데이터 Cypher 파일을 Neo4j에 로드하고, 노드/관계가 정상 생성되는지 검증
    """
    cypher_path = os.path.join(os.path.dirname(__file__), "../data/neo4j_sample_data.cypher")
    with open(cypher_path, "r") as f:
        cypher = f.read()
    # 여러 쿼리 실행
    # 노드 생성 쿼리만 먼저 실행 (관계 생성 전 노드가 모두 존재해야 함)
    node_stmts = []
    rel_stmts = []
    for stmt in cypher.split(";"):
        stmt = stmt.strip()
        if not stmt:
            continue
        if "-[:DEPENDS_ON]->" in stmt:
            rel_stmts.append(stmt)
        else:
            node_stmts.append(stmt)
    for stmt in node_stmts:
        neo4j_session.execute_query(stmt)
    for stmt in rel_stmts:
        neo4j_session.execute_query(stmt)
    # 샘플 노드/관계 존재 여부 검증
    result = neo4j_session.execute_query("MATCH (n:DataNode) RETURN count(n) AS cnt")
    assert result[0]["cnt"] >= 5
    rel_result = neo4j_session.execute_query("MATCH (:DataNode)-[r:DEPENDS_ON]->(:DataNode) RETURN count(r) AS rel_cnt")
    assert rel_result[0]["rel_cnt"] >= 3
