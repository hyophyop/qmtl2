# Neo4j 환경변수 분리 정책 (테스트/서비스)

## 목적
- 통합/엔드투엔드 테스트에서 Neo4j 연결 오류를 방지하고, 호스트 테스트 코드와 컨테이너 서비스가 올바른 URI로 DB에 연결하도록 보장합니다.

## 정책 요약
- **호스트(테스트 러너, pytest 등)**: `NEO4J_URI=bolt://localhost:7687` (테스트 코드에서만 사용)
- **Registry/Orchestrator 컨테이너**: `NEO4J_URI=bolt://neo4j:7687` (docker-compose.dev.yml에서 지정)
- 테스트 코드의 환경변수 오염이 컨테이너에 전달되면 안 됨 (컨테이너는 항상 서비스명 기반 URI 사용)

## 적용 방법
- `tests/conftest.py`에서 pytest로 실행될 때만 `os.environ["NEO4J_URI"] = "bolt://localhost:7687"`를 설정합니다.
- docker-compose.dev.yml의 registry/orchestrator 서비스에는 반드시 `NEO4J_URI=bolt://neo4j:7687`를 명시합니다.
- 컨테이너 환경에서 테스트 환경변수가 전달되지 않도록 주의합니다.

## 예시
- 테스트 실행: pytest/tests/conftest.py → localhost:7687
- 서비스 컨테이너: docker-compose.dev.yml → neo4j:7687

## 참고
- tests/README.md, docs/developer_guide.md, tests/conftest.py 상단 주석 참조
- 정책 위반 시 Registry/Orchestrator 컨테이너가 Neo4j에 연결하지 못해 500 오류 발생
