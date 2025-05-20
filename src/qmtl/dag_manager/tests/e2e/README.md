
# [2025-05-14] (FIXTURE-REGISTRY-ORCH) Registry/Orchestrator 서비스도 Neo4j/Redis/Redpanda처럼 pytest fixture에서 docker-compose로 직접 기동/정리하는 구조로 전환 완료

## Registry/Orchestrator Docker fixture 구조 및 사용법

- Registry/Orchestrator 서비스는 Neo4j/Redis/Redpanda와 함께 docker-compose로 일괄 기동/정리되며, `tests/conftest.py`의 `docker_compose_up_down` fixture가 health check로 준비 상태를 보장합니다.
- 모든 E2E/통합 테스트는 해당 fixture 이후에만 FastAPI TestClient(app) 인스턴스를 생성하도록 구조화되어 있습니다.
- 환경변수/포트/네트워크 일치, race condition, 연결 실패 등 문제를 원천적으로 차단합니다.
- fixture 구조 및 사용법은 본 파일, `tests/README.md`, `docs/developer_guide.md`에 안내되어 있습니다.

## Docker fixture 적용 정책 (2025-05-13)

- **E2E 테스트**는 반드시 Docker 기반 서비스 환경에서 실행되어야 하며, `docker_compose_up_down` fixture가 명시적으로 적용됨(`@pytest.mark.usefixtures("docker_compose_up_down")`).
- `docker_compose_up_down` fixture는 autouse가 아니므로, E2E 테스트 파일/클래스/함수에 직접 마크해야 함.
- 단위/모델 테스트는 Docker 환경에 의존하지 않으며, 어떤 Docker fixture도 자동 적용되지 않음.
- fixture 분리 정책에 따라, 테스트 계층별로 실행 환경이 명확히 분리되어 신뢰성과 속도가 모두 보장됨.
- 자세한 정책 및 예시는 `tests/conftest.py`와 각 테스트 파일 상단을 참고.
# [2025-05-11] [FIXTURE-4] E2E 테스트에서 fixture-1,2,3의 목적에 맞는 session/module scope 분리 및 적용 검증: fixture 구조/네이밍/scope/주석/가이드 모두 가이드라인에 부합하며, E2E 테스트에서도 session-scoped fixture로 리소스 공유 및 데이터 일관성 구조가 보장됨. 추가 개선/리팩토링 불필요.
# E2E 테스트 가이드

## 코드 스타일 및 Linter 규칙 강화 안내 (2025-05-11)
전체 코드베이스에 대해 flake8, black, isort 규칙이 통일 적용됩니다 (max-line-length=100 등).
주요 linter 오류(F821, F811 등)는 직접 수정되었으며, 나머지 style/lint 경고는 IDE에서 일괄 처리하여 코드 스타일이 일관화되었습니다.
테스트 인프라 및 리포트 자동화(pytest-html, Makefile 연동)도 강화되었습니다.

## 개요

이 디렉토리에는 QMTL의 End-to-End 테스트 시나리오가 포함되어 있습니다. 
E2E 테스트는 실제 애플리케이션 환경과 유사한 조건에서 전체 워크플로우가 정상적으로 동작하는지 검증합니다.

## 테스트 환경 설정

1. Docker 컨테이너 실행 (Registry, Orchestrator, Neo4j, Redis, Redpanda)

## Orchestrator 활성 전략 상태 영속화 정책

- Orchestrator의 활성 전략 상태는 Redis에 환경별로 영속화됩니다.
- 서비스(ActivationService) 초기화 시 Redis에서 활성 전략 상태를 복구하며, 활성화/비활성화 시 즉시 Redis에 반영됩니다.
- E2E 테스트(test_e2e_multi_strategy_environments)에서 orchestrator 컨테이너 재시작 후에도 활성화 상태가 유지되는지 검증합니다.
   ```bash
   # 프로젝트 루트 디렉토리에서 실행
   docker-compose -f docker-compose.dev.yml up -d
   ```

2. 서비스 시작 확인
   - Registry 서비스: http://localhost:8000/
   - Orchestrator 서비스: http://localhost:8080/

## 테스트 시나리오

### test_e2e_registry_orchestrator
기본 헬스 체크 테스트로, Registry와 Orchestrator 서비스가 실행 중인지 확인합니다.

### test_e2e_full_workflow
전략 제출부터 실행 결과 조회까지의 전체 워크플로우를 검증하는 테스트입니다:
1. 전략 코드 제출 (POST /v1/orchestrator/strategies)
2. 전략 활성화 (POST /v1/orchestrator/strategies/{version_id}/activate)
3. 파이프라인 실행 트리거 (POST /v1/orchestrator/trigger)
4. 실행 상태 및 결과 조회 (GET /v1/orchestrator/pipeline/{pipeline_id}/status)

### test_e2e_multi_strategy_environments
다중 전략 및 환경(development, production) 테스트입니다:
1. 서로 다른 두 개의 전략 코드 제출 (각각 development 및 production 환경용)
2. 각 전략을 해당 환경에 활성화
3. 각 환경별 전략 실행 및 결과 검증
4. 환경별 전략 분리 및 격리 확인

### test_e2e_error_handling_recovery
오류 상황 대응 및 복구 메커니즘을 검증하는 테스트입니다:
1. 잘못된 문법의 전략 코드 제출 (오류 응답 검증)
2. 존재하지 않는 전략 ID 활성화 시도 (오류 응답 검증)
3. 잘못된 파라미터로 파이프라인 실행 시도 (오류 응답 검증)
4. 오류 발생 후 정상적인 전략 제출 및 실행 (복구 검증)
5. 시스템 상태 확인 (전체 시스템이 정상 상태인지 검증)

## 테스트 실행 방법

```bash
# 프로젝트 루트 디렉토리에서 실행
pytest tests/e2e/test_workflow.py -v
```

### 특정 테스트만 실행
```bash
pytest tests/e2e/test_workflow.py::test_e2e_full_workflow -v
pytest tests/e2e/test_workflow.py::test_e2e_multi_strategy_environments -v
pytest tests/e2e/test_workflow.py::test_e2e_error_handling_recovery -v
```

### 로그 레벨 조정하여 실행 (더 자세한 로그 출력)
```bash
pytest tests/e2e/test_workflow.py -v --log-cli-level=INFO
```

---

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

```python
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

- `redis_session`: Docker 기반 Redis 컨테이너와 연결된 session-scoped fixture. 테스트 세션 전체에서 공유.
- `redis_clean`: 각 테스트 함수 실행 전후로 Redis DB를 비워주는 function-scoped fixture. 테스트 독립성 보장.
- `neo4j_session`: Docker 기반 Neo4j 컨테이너와 연결된 session-scoped fixture. 테스트 세션 전체에서 공유.
- `neo4j_clean`: 각 테스트 함수 실행 전후로 Neo4j DB를 비워주는 function-scoped fixture. 테스트 독립성 보장.
- `redpanda_session`: Docker 기반 Redpanda(Kafka) 컨테이너와 연결된 session-scoped fixture. 테스트 세션 전체에서 공유. (brokers 주소 반환)
- `redpanda_clean`: 각 테스트 함수 실행 전후로 Redpanda 토픽/상태를 정리하는 function-scoped fixture. (기본 no-op, 필요시 확장)

자세한 fixture 정의는 `tests/conftest.py`를 참고하세요.

## 폴링 파라미터(대기 시간/재시도 횟수) 조정 방법

E2E 테스트의 파이프라인 상태 폴링 최대 시도 횟수와 간격은 환경변수 또는 pytest 옵션으로 조정할 수 있습니다.

- 환경변수 사용:
  - `E2E_POLL_MAX_ATTEMPTS`: 폴링 최대 시도 횟수 (기본값: 30)
  - `E2E_POLL_DELAY_SEC`: 폴링 간격(초) (기본값: 1)

- pytest 옵션 사용:
  - `--poll-max-attempts=<횟수>`: 폴링 최대 시도 횟수 지정
  - `--poll-delay-sec=<초>`: 폴링 간격(초) 지정

예시:
```bash
# 환경변수로 조정
E2E_POLL_MAX_ATTEMPTS=60 E2E_POLL_DELAY_SEC=2 pytest tests/e2e/test_workflow.py -v

# pytest 옵션으로 조정
pytest tests/e2e/test_workflow.py -v --poll-max-attempts=60 --poll-delay-sec=2
```

테스트 환경이나 서비스 준비 속도에 따라 위 파라미터를 조정하면 타임아웃 문제를 완화할 수 있습니다.

## 서비스 준비 상태 확인 및 안정성 개선

E2E 테스트는 실제 서비스가 완전히 실행되어야 정확한 테스트가 가능합니다. 이를 위해 다음과 같은 안정성 개선이 적용되었습니다:

1. **개선된 서비스 준비 확인 메커니즘**: 
   - `conftest.py`에서 모든 테스트 시작 전 각 서비스가 준비될 때까지 자동으로 대기
   - 최대 60초(2초 간격, 30회 시도) 동안 서비스 준비 상태를 확인
   - 준비되지 않으면 Docker 로그 출력 및 명확한 오류 메시지와 함께 테스트 실패

2. **로깅 기능 강화**:
   - 모든 API 요청 및 응답에 대한 상세한 로깅 추가
   - 서비스 준비 상태, 전략 제출/활성화, 파이프라인 실행/상태 등 각 단계별 로깅
   - 오류 발생 시 명확한 원인 파악을 위한 상세 정보 로깅

3. **오류 처리 개선**:
   - 모든 API 호출에 타임아웃 설정 (연결이 오래 걸릴 경우 대비)
   - 오류 발생 시에도 필요한 경우 재시도 로직 적용
   - 명확한 오류 메시지 및 상태 코드 검증

## 주의사항

1. E2E 테스트는 실제 서비스 컨테이너가 실행 중인 상태에서만 성공합니다. `conftest.py`에서 자동으로 서비스 준비 상태를 확인하지만, 간혹 시스템 리소스에 따라 서비스 시작이 지연될 수 있습니다.

2. 테스트가 실패하는 경우 다음을 확인하세요:
   - Docker 컨테이너가 모두 실행 중인지 확인: `docker ps`
   - 컨테이너 로그 확인: `docker-compose -f docker-compose.dev.yml logs`
   - 서비스 직접 접근 가능 여부 확인: `curl http://localhost:8000/` 및 `curl http://localhost:8080/`

3. 포트 충돌 발생 시 테스트는 자동으로 실패하므로, 기존 컨테이너를 정리 후 재시작하세요:
   ```bash
   docker-compose -f docker-compose.dev.yml down
   docker-compose -f docker-compose.dev.yml up -d
   ```

4. 로컬 테스트 중 발생할 수 있는 문제:
   - 네트워크 타임아웃: 로컬 Docker 네트워크 연결 확인
   - 메모리 부족: 다른 Docker 컨테이너 종료 또는 시스템 리소스 확보
   - 데이터베이스 초기화 문제: Neo4j 로그 확인 및 볼륨 초기화 고려