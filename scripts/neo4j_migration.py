"""
Neo4j 인덱스 및 제약조건 마이그레이션 스크립트 (DAG Manager)
- 서비스 기동 전/중에 Neo4j 인덱스 자동 생성
- 운영/테스트 환경 모두 사용 가능
"""
import sys
from qmtl.common.db.neo4j_client import Neo4jClient
from qmtl.dag_manager.registry.services.node.neo4j_schema import get_schema_cypher


def main():
    # 환경변수 또는 인자에서 Neo4j 접속 정보 획득 (예시)
    uri = sys.argv[1] if len(sys.argv) > 1 else "bolt://localhost:7687"
    user = sys.argv[2] if len(sys.argv) > 2 else "neo4j"
    password = sys.argv[3] if len(sys.argv) > 3 else "test"
    database = sys.argv[4] if len(sys.argv) > 4 else None

    client = Neo4jClient(uri=uri, user=user, password=password, database=database)
    for cypher in get_schema_cypher():
        print(f"[Neo4j] Executing: {cypher.strip().splitlines()[0]} ...", flush=True)
        client.execute_query(cypher)
    print("[Neo4j] All schema/index migrations applied.")

if __name__ == "__main__":
    main()
