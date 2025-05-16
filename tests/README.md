
# [2025-05-14] (FIXTURE-REGISTRY-ORCH) Registry/Orchestrator 서비스도 Neo4j/Redis/Redpanda처럼 pytest fixture에서 docker-compose로 직접 기동/정리하는 구조로 전환 완료

## Registry/Orchestrator Docker fixture 구조 및 사용법

- Registry/Orchestrator 서비스는 Neo4j/Redis/Redpanda와 함께 docker-compose로 일괄 기동/정리되며, `tests/conftest.py`의 `docker_compose_up_down` fixture가 health check로 준비 상태를 보장합니다.
- 모든 E2E/통합 테스트는 해당 fixture 이후에만 FastAPI TestClient(app) 인스턴스를 생성하도록 구조화되어 있습니다.
- 환경변수/포트/네트워크 일치, race condition, 연결 실패 등 문제를 원천적으로 차단합니다.
- fixture 구조 및 사용법은 본 파일, `tests/e2e/README.md`, `docs/developer_guide.md`에 안내되어 있습니다.

## Docker fixture 적용 정책 (2025-05-13)

- **단위/모델 테스트**: 외부 Docker 환경에 의존하지 않으며, 어떤 Docker fixture도 자동 적용되지 않음.
- **E2E/통합 테스트**: Docker 기반 서비스 환경이 반드시 필요하며, `docker_compose_up_down` fixture가 명시적으로 적용됨(`@pytest.mark.usefixtures("docker_compose_up_down")`).
- `docker_compose_up_down` fixture는 autouse가 아니므로, E2E/통합 테스트 파일/클래스/함수에 직접 마크해야 함.
- fixture 분리 정책에 따라, 단위 테스트는 빠르고 독립적으로 실행되며, 통합/E2E 테스트는 실제 환경에서 신뢰성 있게 동작함.
- 자세한 정책 및 예시는 `tests/conftest.py`와 각 테스트 파일 상단을 참고.
# [2025-05-11] [FIXTURE-4] E2E 테스트에서 fixture-1,2,3의 목적에 맞는 session/module scope 분리 및 적용 검증: fixture 구조/네이밍/scope/주석/가이드 모두 가이드라인에 부합하며, E2E 테스트에서도 session-scoped fixture로 리소스 공유 및 데이터 일관성 구조가 보장됨. 추가 개선/리팩토링 불필요.
# QMTL 테스트 가이드

## 코드 스타일 및 Linter 규칙 강화 안내 (2025-05-11)
전체 코드베이스에 대해 flake8, black, isort 규칙이 통일 적용됩니다 (max-line-length=100 등).
주요 linter 오류(F821, F811 등)는 직접 수정되었으며, 나머지 style/lint 경고는 IDE에서 일괄 처리하여 코드 스타일이 일관화되었습니다.
테스트 인프라 및 리포트 자동화(pytest-html, Makefile 연동)도 강화되었습니다.

## Orchestrator 활성 전략 상태 영속화 정책

- Orchestrator의 활성 전략 상태는 Redis에 환경별로 영속화됩니다.
- 서비스(ActivationService) 초기화 시 Redis에서 활성 전략 상태를 복구하며, 활성화/비활성화 시 즉시 Redis에 반영됩니다.
- E2E 테스트(test_e2e_multi_strategy_environments)에서 orchestrator 컨테이너 재시작 후에도 활성화 상태가 유지되는지 검증합니다.

이 디렉토리는 QMTL의 단위/통합/시스템 테스트를 포함합니다.

## 주요 fixture 사용 예시

### Redis 연동 테스트

```python
import pytest

def test_redis_session_and_clean(redis_clean, redis_session):
    """
    [FIXTURE-1] 실제 Redis 컨테이너와 연동되는 기본 동작 테스트
    """
    redis_session.set('foo', 'bar')
    assert redis_session.get('foo') == b'bar'
    redis_session.set('num', 123)
    assert int(redis_session.get('num')) == 123
    # clean fixture가 동작하면 다음 테스트에서 DB가 비워짐을 보장
```


### Neo4j 연동 테스트

def test_neo4j_session_and_clean(neo4j_clean, neo4j_session):
    """
    [FIXTURE-2] 실제 Neo4j 컨테이너와 연동되는 기본 동작 테스트
    """
    neo4j_session.execute_query("CREATE (:TestNode {foo: 1})")
    result = neo4j_session.execute_query("MATCH (n:TestNode) RETURN count(n) AS cnt")
    assert result[0]["cnt"] == 1
    # clean fixture가 동작하면 다음 테스트에서 DB가 비워짐을 보장

```
import pytest

def test_neo4j_session_and_clean(neo4j_clean, neo4j_session):
    """
    [FIXTURE-2] 실제 Neo4j 컨테이너와 연동되는 기본 동작 테스트
    """
    neo4j_session.execute_query("CREATE (:TestNode {foo: 1})")
    result = neo4j_session.execute_query("MATCH (n:TestNode) RETURN count(n) AS cnt")
    assert result[0]["cnt"] == 1
    # clean fixture가 동작하면 다음 테스트에서 DB가 비워짐을 보장
```


### Neo4j 환경변수 분리 정책 (테스트/서비스)

- **호스트(테스트 러너, pytest 등)**: `NEO4J_URI=bolt://localhost:7687` (테스트 코드에서만 사용)
- **Registry/Orchestrator 컨테이너**: `NEO4J_URI=bolt://neo4j:7687` (docker-compose.dev.yml에서 지정)
- 테스트 코드의 환경변수 오염이 컨테이너에 전달되면 안 됨 (컨테이너는 항상 서비스명 기반 URI 사용)
- 자세한 정책 및 예시는 `docs/neo4j_env_policy.md` 참조

테스트/서비스 환경 모두에서 위 값이 분리되어야 데이터 불일치, 연결 오류가 발생하지 않습니다. (docker-compose.dev.yml, pytest, FastAPI 등에서 일관성 유지)

자세한 fixture 정의 및 정책은 `tests/conftest.py`를 참고하세요.

- `redis_session`: Docker 기반 Redis 컨테이너와 연결된 session-scoped fixture. 테스트 세션 전체에서 공유.
- `redis_clean`: 각 테스트 함수 실행 전후로 Redis DB를 비워주는 function-scoped fixture. 테스트 독립성 보장.
- `neo4j_session`: Docker 기반 Neo4j 컨테이너와 연결된 session-scoped fixture. 테스트 세션 전체에서 공유.
- `neo4j_clean`: 각 테스트 함수 실행 전후로 Neo4j DB를 비워주는 function-scoped fixture. 테스트 독립성 보장.
- `redpanda_session`: Docker 기반 Redpanda(Kafka) 컨테이너와 연결된 session-scoped fixture. 테스트 세션 전체에서 공유. (brokers 주소 반환)
- `redpanda_clean`: 각 테스트 함수 실행 전후로 Redpanda 토픽/상태를 정리하는 function-scoped fixture. (기본 no-op, 필요시 확장)

## 기타
- 모든 외부 리소스(Docker, DB 등)는 session-scoped fixture로 관리하며, 상태 초기화는 별도 clean fixture로 분리합니다.
- fixture 네이밍 및 docstring은 일관성을 유지합니다.
- 자세한 fixture 정의는 `tests/conftest.py`를 참고하세요.
