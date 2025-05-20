# Neo4j 인덱스/제약조건 마이그레이션 가이드 (DAG Manager)

## 목적
- DAG Manager 서비스의 성능 및 일관성 보장을 위해 Neo4j 인덱스/제약조건을 자동 생성합니다.
- QueryNode, 태그 기반 조회, 의존성 탐색 등 주요 쿼리의 성능을 보장합니다.

## 적용 방법
1. Neo4j 인스턴스가 기동된 상태에서 아래 스크립트를 실행하세요.

```bash
python scripts/neo4j_migration.py [NEO4J_URI] [USER] [PASSWORD] [DATABASE]
```
- 예시: `python scripts/neo4j_migration.py bolt://localhost:7687 neo4j test`
- DATABASE는 Neo4j 4.x 이상에서만 필요(기본값 None)

2. 서비스 기동 전/중에 반복 실행해도 안전합니다. (IF NOT EXISTS 사용)

## 생성되는 인덱스/제약조건 목록
- DataNode.node_id UNIQUE 제약조건
- StrategyVersion.version_id UNIQUE 제약조건
- ActivationHistory (복합 UNIQUE)
- DEPENDS_ON, CONTAINS, ACTIVATED_BY 관계 인덱스
- DataNode.tags.predefined/custom, interval_settings.interval/period 인덱스

## 참고
- 인덱스/제약조건 정의는 `src/qmtl/dag_manager/registry/services/node/neo4j_schema.py` 참고
- QueryNode, 태그 기반 쿼리, DAG 탐색 등 모든 주요 쿼리는 인덱스 활용을 전제로 구현됨
- 운영 환경에서는 서비스 기동 스크립트/CI 파이프라인에 포함 권장
