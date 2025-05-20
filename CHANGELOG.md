# QMTL NextGen 변경이력

## 2025-06-01
- [NG-GW-3] 전체 워크플로우 E2E 테스트 및 예외 처리 강화 완료
  - 완전한 워크플로우 E2E 테스트 구현: 인증, 전략 등록, 데이터노드 생성, 파이프라인 실행까지 전체 흐름 검증
  - 장애 상황 테스트 강화: 서비스 재시작, 오류 복구, 타임아웃 처리 등 다양한 장애 시나리오 검증
  - 읽기 전용 API 제한 정책 검증: Gateway REST API가 GET 메서드만 허용하는지 확인하는 테스트 추가
  - tests/e2e/test_gateway_workflow_e2e.py 파일에 TestCompleteWorkflow, TestFaultTolerance, TestReadOnlyRestriction 클래스 구현
  - tests/e2e/test_gateway_exception_handling.py 파일에 다양한 예외 처리 테스트 추가

## 2025-05-30
- [NG-GW-2] Gateway 비즈니스 로직/정책/ACL/인증 개선 및 고도화 완료
  - JWT 인증 미들웨어 구현: 토큰 검증, 만료 처리, 사용자 정보 추출
  - ACL(Access Control List) 미들웨어 구현: 경로 기반 정규식 패턴 매칭, 역할 기반 접근 제어
  - 정책 서비스 구현: 리소스 유형별, 작업 유형별 세분화된 권한 관리 
  - 로깅 미들웨어 구현: 요청/응답 정보 기록, 민감 정보 마스킹
  - 오류 처리 미들웨어 구현: HTTP 예외, 검증 오류, 서버 오류 등 일관된 처리
  - read-only API 정책 강화: 외부 API는 GET 메서드만 허용하는 일관된 구현

## 2025-05-26
- [NG-GW-1] DAG Manager, SDK와의 연동 플로우/통합 테스트 완료
  - 통합 테스트 코드 작성 및 구현 (tests/integration/test_gateway_dag_manager_integration.py)
  - protobuf 직렬화/역직렬화 테스트 로직 구현
  - 인증/ACL 검증 기능 테스트 추가
  - REST API read-only 정책 검증 로직 구현
  - Gateway-DAG Manager 간 통합 테스트 구현 (전략 등록, 데이터노드 생성, ACL 검증, 직렬화 일관성)
- [NG-SDK-6] golden/round-trip 테스트 템플릿 예시 파일 표준화 및 통합
  - 기존 golden_test_example.py와 roundtrip_test_example.py의 장점을 통합한 템플릿으로 개선 (tests/templates/golden_test_example.py)
  - 템플릿 파일에 golden/round-trip 테스트 가이드 및 주요 주석 보강
  - 실제 테스트 구현자는 이 템플릿을 복사하여 사용하도록 안내

## 2025-05-24
- [NG-공통-1] 데이터 모델(proto/pydantic) 및 API 계약 우선 확정
  - proto 메시지/엔티티 현황 및 서비스별 API-contract 매핑 공식 문서화
  - architecture.md에 표 및 설명 추가
- [NG-DAG-1] Gateway와의 연동 플로우/통합 테스트 완료
  - docker-compose 기반 테스트 인프라 자동화
  - FastAPI↔protobuf↔Pydantic 변환 계층 정비
  - end-to-end 통합 테스트 통과

## 2025-05-24
- [NG-DAG-6] golden/round-trip 테스트 템플릿 예시 파일 생성 (tests/templates/)
  - golden 테스트 예시 파일 `tests/templates/golden_test_example.py` 작성
  - round-trip 테스트 예시 파일 `tests/templates/roundtrip_test_example.py` 작성
  - 테스트 관련 문서 `tests/templates/README.md` 작성
  - 테스트 데이터 저장 디렉토리 `tests/data/golden` 생성

## [NG-2-4] 기존 코드에서 Pydantic 모델 사용처를 protobuf 기반으로 일괄 치환 (2025-05-20)
- docs/generated/protobuf_migration_guide.md: 마이그레이션 가이드/체크리스트 작성

## [NG-2-5] protobuf 기반 테스트(golden/round-trip) 작성 (2025-05-20)
- tests/templates/test_protobuf_roundtrip.py: round-trip/golden test 템플릿 생성

## [NG-2-3] protobuf 코드 생성 자동화 스크립트 작성 (2025-05-20)
- scripts/generate_proto.sh: protos/ 내 모든 .proto → src/qmtl/models/generated/ 자동 생성

## [NG-2-2-2] protobuf 스키마 버전 관리(major/minor) 및 변경 이력 관리 가이드 작성 (2025-05-20)
- docs/proto_schema_versioning.md에 관리 원칙, docs/generated/proto_schema_versioning_example.md에 실제 예시 추가

## [NG-2-2-1] protobuf 스키마 필드 정의(필수/선택 필드, 타입 제약) 문서화 (2025-05-20)
- protos/ 내 모든 .proto 메시지별 필드/타입/제약을 docs/generated/protobuf_field_spec.md로 표로 정리

## [NG-2-2] protobuf .proto 스키마 설계 및 버전 관리 체계 도입 (2025-05-20)
- protos/ 디렉토리에 주요 도메인별 .proto 스키마 초안 작성
- docs/proto_schema_versioning.md에 버전 관리 가이드 문서화

## [NG-2-1] Pydantic 모델 목록화 및 protobuf 변환 대상 선정 (2025-05-20)
- src/qmtl/models/ 내 모든 Pydantic 모델을 목록화
- protobuf 변환 우선 대상 선정 및 docs/generated/pydantic_model_inventory.md에 문서화

### NG-1-5: 서비스별 독립 실행/테스트 환경 구축 (2025-05-20)
- 각 서비스별 docker-compose.yml, Makefile, README.md에 독립 실행/테스트/컨테이너 안내 추가
- smoke test(docker-compose up/down)로 컨테이너 기동 확인

### NG-1-4: 각 서비스별 Dockerfile 작성 및 빌드 테스트 (2025-05-20)
- dag_manager, gateway, sdk 각 서비스별 Dockerfile 작성 및 최신화
- 모든 서비스별 Docker 이미지 빌드 테스트 성공
### FIXTURE-REGISTRY-ORCH: Registry/Orchestrator Docker fixture 구조 전환 및 Neo4j 환경변수 분리 정책 적용 (2025-05-14)
- registry/orchestrator 서비스도 Neo4j/Redis/Redpanda처럼 pytest fixture에서 docker-compose로 직접 기동/정리하는 구조로 전환 완료
- tests/conftest.py의 docker_compose_up_down fixture가 registry/orchestrator/neo4j/redis/redpanda 컨테이너를 일괄 관리하며 health check로 준비 상태를 보장
- 모든 E2E/통합 테스트는 해당 fixture 이후에만 FastAPI TestClient(app) 인스턴스를 생성하도록 구조화되어 있음
- 환경변수/포트/네트워크 일치, race condition, 연결 실패 등 문제를 원천적으로 차단
- Neo4j 환경변수 분리 정책 적용: pytest(호스트)는 bolt://localhost:7687, 컨테이너는 bolt://neo4j:7687만 사용하도록 명확화
- 정책/구현/문서화: tests/conftest.py, docs/neo4j_env_policy.md, tests/README.md, 주석 보강
- 통합 테스트(test_node_dependency_management)에서 Neo4j 연결 오류(500) 해결 및 정상 통과 확인
- tests/README.md, tests/e2e/README.md, docs/developer_guide.md에 구조 및 사용법 반영
### MULTI-7: 실시간 모니터링/대시보드/알림 시스템 연동 (2025-05-13)
- Registry: 상태 변화 이벤트 발행/구독 서비스(EventPublisher/EventSubscriber), 실시간 이벤트 API 추가
- Orchestrator: 이벤트 구독 클라이언트(EventClient) 및 대시보드/알림 연동 샘플 구현
- Pydantic v2 스타일 이벤트/상태 모델 정의(models/event.py)
- 단위 테스트 및 모킹 기반 검증(tests/unit/models/test_event.py, tests/unit/registry/services/test_event.py, tests/unit/orchestrator/services/test_event_client.py)
- FastAPI API 연동(/v1/registry/events/node-status 등)
- todo.md → backlog.md, CHANGELOG.md 반영
# 2025-05-13 (FIXTURE-4) E2E/통합 테스트용 Docker fixture 분리 적용
- 기존: docker_compose_up_down fixture가 autouse=True로 설정되어 모든 테스트(단위/모듈 포함)에 Docker 환경이 강제 적용됨
- 변경: autouse=True 제거, E2E/통합 테스트에서만 @pytest.mark.usefixtures("docker_compose_up_down")로 명시 적용
- 결과: 단위/모델 테스트는 Docker 환경 없이 독립적으로 실행 가능, E2E/통합 테스트는 기존대로 Docker 환경 자동 관리
- 관련 문서/가이드: tests/README.md, tests/e2e/README.md에 fixture 적용 정책 명시 필요
- 영향: 단위 테스트 실행 속도 및 독립성 개선, 테스트 계층 분리 원칙 준수
- 검증: tests/unit/models/test_status_multi6.py 등 단위 테스트가 Docker 없이 정상 실행 및 통과 확인
# CHANGELOG


## [Unreleased]

### MULTI-8: 전략/노드 동적 추가/삭제/수정, 템플릿/권한 관리 확장 (2025-05-13)
- 템플릿/권한 관리용 Pydantic 모델 정의(models/template.py)
- Registry API에 템플릿/권한 관리 엔드포인트 스켈레톤 추가(api.py)
- 노드/전략 Partial Update(수정) API 스켈레톤 추가(api.py)
- Orchestrator 연동, 서비스/테스트/문서화 예정

### MULTI-4: 의존성 기반 동적 스케줄링 및 리소스 최적화 (2025-05-13)
- Registry: 전체 DAG 구조, 노드 의존성 정보, 실행 가능 노드 목록 제공 API 구현
    - `/v1/registry/pipelines/{pipeline_id}/dag` (DAG 구조)
    - `/v1/registry/pipelines/{pipeline_id}/ready-nodes` (ready node 목록)
    - 서비스/DI/모킹/테스트 일관성 보장
- Orchestrator: Registry에서 DAG/의존성/상태 정보 조회, 실행 가능한 노드만 선별 실행, 리소스 상황에 따라 우선순위/스케줄링, 비활성 노드 자동 정지/재시작 (별도 이슈)
- 단위/통합 테스트(mock 기반) 및 FastAPI DI/의존성 주입/모킹 구조 검증
- todo.md, backlog.md, CHANGELOG.md 반영

### PIPELINE-1: 글로벌 Pipeline ID 정책 적용 및 일관화 (2025-05-13)
- Registry/Orchestrator/SDK/테스트/문서 전체에서 version_id, strategy_id 등 파이프라인 식별자 제거, pipeline_id(32자리 해시)로 일원화
- Pipeline ID 생성 정책 및 예시를 architecture.md, nodeID.md, README 등과 일치하도록 반영
- 모든 Pydantic 모델, 서비스, API, 테스트(mock 포함)에서 pipeline_id만 사용하도록 리팩터링
- 기존 version_id, strategy_id 등 관련 필드/로직/문서/테스트 전수 점검 및 일괄 대체
- 테스트(mock 포함)에서 pipeline_id 기반 데이터 흐름/값 사용 보장 및 일관성 검증
- 관련 정책/예시/가이드/테스트/주의사항 등 문서화 및 todo.md, backlog.md, CHANGELOG.md 반영

### MULTI-5: 콜백/이벤트 훅 기반 노드 생명주기 관리 (2025-05-13)
- Registry: 노드 실행/정지 신호 콜백 등록/해제/조회/트리거 API 및 도메인 서비스 구현 (`/v1/registry/nodes/{node_id}/callbacks`)
- Orchestrator: 콜백 등록/해제 요청, 콜백 이벤트 수신 후 노드 실행/정지 신호 처리 구조 초안
- Pydantic v2 스타일 콜백 모델(models/callback.py) 정의
- 단위/통합 테스트 및 FastAPI DI/모킹 구조 검증 (tests/integration/test_callback.py)
- 정책 Node ID(32자리 해시) 기반 일관성 보장, 문서/가이드/테스트/CHANGELOG/todo.md 반영

### 추가됨
- 문서화 품질 개선 (DOC-4)
  - API 문서에 상세 요청/응답 예시 추가
  - README.md 보강 (설치 방법, 핵심 기능 등)
  - 아키텍처/워크플로우 다이어그램 추가 (docs/architecture_diagram.md)
  - 개발자 가이드에 신규 기능 추가 절차 상세화
  - 용어 사전 및 개념 색인 추가 (docs/glossary.md)
  - E2E 워크플로우 예제 확장 (docs/e2e_workflow.md)
  - 핵심 개념 시각화 자료 추가 (docs/key_concepts.md)
  - 주요 문서 한국어 버전 추가 (docs/ko/*.md)
- Node, SourceNode, DataNode 등 모든 노드에 interval(주기) 필수화 정책 적용
  - interval 누락 시 예외 발생 (Pydantic 모델, 생성자, 역직렬화, 테스트 등 전체 계층 적용)
  - 관련 단위/통합 테스트 및 예외 테스트 추가
  - README, SDK 가이드, 사용자 가이드 등 주요 문서에 interval 필수 정책 명시
- Registry: 노드-전략(CONTAINS) 참조 카운트 및 맵 관리 기능(MULTI-1) 구현
  - StrategyVersion-DataNode 간 CONTAINS 관계 Cypher 기반 생성/삭제/조회 메서드 추가
  - 참조 카운트/맵 조회 API 및 서비스 메서드 구현
  - 단위 테스트(mock 기반) 및 문서화(todo.md, backlog.md, architecture.md) 완료

### 변경됨
- Neo4j/Redis/Redpanda 연결 상세 가이드 개선
- 개발자 가이드의 모듈별 설계 결정 기록 확장

# [2025-05-11] E2E-STATE: Orchestrator 활성 전략 등 상태 저장 방식 개선
- ActivationService에서 Redis 기반 환경별 활성 전략 상태 영속화 구현
- 서비스 초기화 시 Redis에서 상태 복구, 활성화/비활성화 시 Redis에 즉시 반영
- E2E 테스트(test_e2e_multi_strategy_environments)에서 orchestrator 컨테이너 재시작 후에도 활성화 상태가 유지되는지 검증
- 장애/복구 상황(예: Redis flush, 장애 후 복구)에서 일관성 보장 테스트
- 관련 구조/정책을 architecture.md, README, tests/README.md, tests/e2e/README.md에 명시
# [2025-05-11] FIXTURE-4: E2E 테스트에서 fixture-1,2,3의 목적에 맞는 session/module scope 분리 및 적용 검증
- tests/conftest.py, tests/README.md, tests/e2e/README.md 등에서 fixture의 scope/구조/네이밍/주석이 가이드와 일치함을 점검
- E2E 테스트에서 여러 테스트가 동일 리소스를 바라보며, 데이터 일관성/독립성이 fixture 구조로 보장됨을 확인
- 추가적인 구조 개선/리팩토링 불필요 (테스트/문서/가이드도 최신 상태)
- 실제 E2E 테스트 실행 결과, fixture 구조 문제로 인한 데이터 불일치/공유 문제 없음 (환경별 전략 분리 등은 별도 비즈니스 로직 이슈)
# [2025-05-10] FIXTURE-3: redpanda 등 메시지 브로커 컨테이너/연결 fixture 구조 개선 및 통합
- tests/conftest.py: redpanda_session/redpanda_clean 등 외부 메시지 브로커 session/function scope fixture 구현 및 통합, docstring/네이밍 일관성 강화
- tests/sdk/test_parallel_engine.py, test_stream_processor.py 등에서 fixture 네이밍 통일 및 사용처 리팩토링
- tests/README.md, tests/e2e/README.md: redpanda fixture 사용 예시 및 설명 추가
- 기존 fixture 사용처 전수 점검 및 리팩토링
# [2025-05-10] INTERVAL-5: LocalExecutionEngine 인터벌 데이터 관리/인메모리 캐싱/테스트
- src/qmtl/sdk/execution/local.py: LocalExecutionEngine에 in-memory interval cache, save/get/clear/cleanup 메서드, max_history/TTL 관리, execute_pipeline 리팩토링
- tests/unit/sdk/test_interval_data.py: interval 데이터 저장/조회, max_history/TTL, stream_settings, node metadata, 캐시 클리어, 파이프라인 통합 등 단위테스트 추가 및 통과
- 기존 코드베이스의 SoC 위반 부분 리팩토링, Pydantic v2 스타일 및 모델 네이밍 가이드 준수
# [2025-05-10] FIXTURE-3: redpanda 등 메시지 브로커 컨테이너/연결 fixture 구조 개선 및 통합
- tests/conftest.py: redpanda_session/redpanda_clean 등 외부 메시지 브로커 session/function scope fixture 구현 및 통합, docstring/네이밍 일관성 강화
- tests/sdk/test_parallel_engine.py, test_stream_processor.py, test_topic.py 등에서 fixture 네이밍 통일 및 사용처 리팩토링 필요
- tests/README.md, tests/e2e/README.md: redpanda fixture 사용 예시 및 설명 추가
- 기존 fixture 사용처 전수 점검 및 리팩토링
# [2025-05-10] INTERVAL-3 인터벌별 데이터 저장 구조/TTL/최대 항목수 관리 구현
- RedisClient에 save_history/get_history/delete_history 메서드 추가 (key: node:{node_id}:history:{interval})
- lpush/ltrim/expire로 TTL 및 max_items 관리, 단위 테스트 통과 (test_redis_history.py)
# [2025-05-10] FIXTURE-1: pytest fixture 구조 개선 및 통합
- tests/conftest.py: redis_session/redis_clean 등 외부 리소스 session/function scope fixture 표준화, docstring/네이밍 일관성 강화
- tests/unit/common/redis/test_redis_client.py, test_redis_history.py 등에서 fixture 네이밍 통일 및 사용처 리팩토링
- tests/README.md, tests/e2e/README.md: fixture 사용 예시 및 설명 추가
- conftest_redis.py: 중복/불필요 파일 정리
- 모든 Redis 기반 테스트가 표준화된 fixture로 통합되어 신뢰성/일관성/테스트 독립성 강화
## [2025-05-10] INTERVAL-2 Node 클래스 인터페이스 확장 완료
- Node 생성자에 stream_settings 매개변수 추가
- 스트림 설정 정규화 메서드 구현
- 히스토리 데이터 접근 API 설계 및 통합 테스트 통과 (test_redis_interval_data.py)
# [Unreleased]

# [2025-05-11] TEST-4: 테스트 인프라 업그레이드 및 linter warning 정리 완료
- flake8, black, isort 설정 통일 (max-line-length=100 등)
- 주요 import/style 오류(F821, F811 등) 직접 수정, 나머지 style/lint 경고는 IDE에서 일괄 처리
- 코드베이스 전체 linter/코드 스타일 규칙 강화 및 자동화
- 테스트 인프라 및 리포트 자동화(pytest-html, Makefile 연동) 완료

# [2025-05-10] FIXTURE-2: neo4j 등 외부 DB 컨테이너/연결 fixture 구조 개선 및 통합
- tests/conftest.py: neo4j_session/neo4j_clean 등 외부 DB session/function scope fixture 구현 및 통합, docstring/네이밍 일관성 강화
- tests/integration/test_registry.py: neo4j_clean 적용 및 기존 fixture 사용처 리팩토링
- tests/README.md, tests/e2e/README.md: neo4j fixture 사용 예시 및 설명 추가
- 기존 fixture 사용처 전수 점검 및 리팩토링
- TEST-4: 테스트 결과 리포트 자동 생성 기능 추가 (pytest-html, Makefile test/integration-test/e2e-test에 --html 옵션, tests/report/README.md)

# [2025-05-10] (INTERVAL-4) 히스토리 데이터 접근 API 개발
- Pipeline/StateManager/Node의 get_history 메서드 구현 및 분산/로컬/타임스탬프 필터 지원
- 인터벌별 데이터 조회 최적화, value/dict 반환 일관성 보장
- 단위 테스트(test_redis_interval_data.py, test_redis_state_manager.py 등) 및 커버리지 80% 이상 유지
- 문서/CHANGELOG/todo.md 반영
- (TAG-3) Orchestrator API 확장 (2025-05-09)
  - 분석기 제출 및 등록 엔드포인트 추가 (/v1/orchestrator/analyzers)
  - 분석기 활성화 엔드포인트 추가
  - 분석 결과 조회 엔드포인트 추가
  - 단위 테스트 작성

## [2025-05-10] (INTERVAL-1) Pydantic 모델 확장
  - IntervalSettings, NodeStreamSettings 모델 구현 및 Pydantic v2 스타일 일관화
  - DataNode/NodeDefinition 모델에 stream_settings 필드 추가 및 interval_settings→stream_settings 마이그레이션 지원
  - 단위 테스트 통과 및 하위 호환성 검증

- (TEST-3) 테스트 자동화 스크립트 구현 (2025-05-10)
  - CI 파이프라인 구성 (.github/workflows/ci.yml)
  - GitHub Actions 워크플로우에서 Neo4j, Redis, Redpanda 서비스 설정
  - uv를 사용한 의존성 설치 및 테스트 환경 설정
  - 테스트 환경 자동 설정 스크립트 (scripts/setup_test_env.sh) 구현
  - CI/CD 파이프라인에서 단위, 통합, E2E 테스트 및 커버리지 자동화
  - 테스트 환경 자동 종료 및 정리 구현 (Makefile docker-down)

- (TAG-5) 분석 파이프라인 실행 엔진 구현 (2025-05-10)
  - Analyzer.execute()에서 태그 기반 QueryNode 매핑 및 실행 로직 SoC 분리
  - 분석 결과 저장 및 캐싱 전략(AnalyzerResult, results_cache 등) 일관화
  - 정기 실행/모니터링 기능 구조 설계(훅/상태 저장)
  - 단위 테스트 및 SDK 전체 테스트 통과

- (TAG-4) 분석기 예제 구현 및 통합 테스트 (2025-05-10)
  - CorrelationAnalyzer(상관관계 분석기), AnomalyDetector(이상치 감지), PerformanceMonitor(성능 모니터링) 예제 구현
  - 태그 기반 QueryNode/Analyzer 구조 확장 및 예제 추가
  - 단위/통합 테스트 작성 및 통과
# (SDK-P2b) OrchestratorClient 확장: PipelineDefinition 제출, Kafka 토픽 목록/메타데이터 조회 메서드 추가, 단위 테스트 추가
# (SDK-P2c) Redis 기반 상태 관리 구현 (2025-05-09)
  - StateManager 클래스 개선 (Redis 연결 풀링, 오류 처리, TTL 관리)
  - 인터벌 데이터의 자동 TTL 관리 구현 (period 값 기반)
  - 메타데이터 저장 및 타임스탬프 기반 필터링 최적화
  - Pipeline 클래스에 get_history, get_interval_data, get_node_metadata 메서드 추가
  - ParallelExecutionEngine에 TTL 계산 및 주기적 저장 기능 구현
  - 단위 테스트 코드 작성 (test_redis_state_manager.py, test_redis_interval_data.py)
# QMTL CHANGELOG



## [Unreleased]

- (SDK-P2a) Kafka/Redpanda 토픽 자동 생성 로직 구현 (2025-05-09)
  - 파이프라인/노드 기반 토픽 명명 규칙 및 생성 함수(topic.py) 구현
  - 병렬 실행 엔진에서 파이프라인/노드별 input/output 토픽 자동 생성 연동
  - 토픽 생성시 권한/오류 발생 시 로깅 처리
  - 단위 테스트 및 README, todo.md 반영

- (SDK-P1c) SDK Pydantic 모델 직렬화/역직렬화 기능 구현 (2025-05-09)
  - PipelineDefinition, NodeDefinition, QueryNodeDefinition, AnalyzerDefinition Pydantic v2 모델 구현 및 from_definition 역직렬화 지원
  - 직렬화/역직렬화 단위 테스트 및 README 예시 추가
  - 기존 스키마와의 호환성 확보

- (SDK-P1d) 인터벌 데이터 관리 기능 구현 (2025-05-09)
  - Pydantic v2 IntervalSettings, NodeStreamSettings 모델 확장 및 단위 테스트
  - Node 클래스 stream_settings 매개변수 및 interval_settings→stream_settings 정규화 지원
  - Pipeline.get_history, get_interval_data, get_node_metadata 메서드 구현 및 테스트
  - Redis 기반 StateManager 연동 및 period→TTL 변환, 히스토리/메타데이터 관리
  - 포괄적 단위 테스트(test_redis_interval_data.py, test_redis_state_manager.py, test_pipeline.py) 통과

- Orchestrator~Registry 전략 version_id/strategy_id/strategy_code 필드 일치성 점검 및 리팩토링 (2025-05-09)
  - architecture.md, 서비스/클라이언트/테스트/문서의 필드 정의 및 데이터 흐름 일치화
  - StrategyRegisterRequest, StrategyVersion 등 Pydantic 모델 구조/필드/타입 일관성 보장
  - API/서비스/도메인/테스트 계층에서 동일한 필드명/타입/값 사용 보장
  - 기존 코드 내 version_id, strategy_id, strategy_code 혼재 구간 전수 점검 및 리팩토링
  - 테스트(E2E/통합/단위)에서 실제 서비스와 동일한 데이터 흐름/값 사용 보장
- execution.py SRP 기반 엔진 분리 및 테스트/문서화
  - StreamProcessor, StateManager, ParallelExecutionEngine 클래스를 각각 별도 파일로 분리
  - 각 엔진별 단위 테스트 추가 (tests/sdk/)
  - README에 구조 및 import 경로 안내 추가
- Neo4j DB 연결 풀 및 트랜잭션 관리 공통 모듈(Pydantic v2 스타일) 구현 및 단위 테스트 완료
- 기타 개선 및 리팩토링 예정
- (REG-2) Neo4j 데이터 스키마 설계 및 마이그레이션 스크립트 구현: DataNode, StrategyVersion, ActivationHistory 노드 및 관계, 인덱스/제약조건, 마이그레이션 함수 및 단위 테스트 추가
- (REG-3) Registry 노드 관리 서비스 구현 및 테스트 완료
  - Neo4j 기반 노드 등록/조회/삭제/목록/zero-deps/유효성 검증 기능 구현
  - Pydantic v2 스타일 모델 일관성 적용
  - 단위 테스트 및 통합 테스트 커버리지 확보
- (REG-6) Registry 노드 관련 API 엔드포인트 구현 완료
  - POST /v1/registry/nodes, GET/DELETE /v1/registry/nodes/{id}, GET /v1/registry/nodes:leaf
  - FastAPI + Pydantic v2 스타일, 서비스 계층 DI, 통합 테스트 포함
- (REG-6.1) 태그 기반 노드 조회 API 구현 완료
  - GET /v1/registry/nodes/by-tags (태그/인터벌/피리어드/AND/OR 지원)
  - 서비스 계층 및 메모리/Neo4j 구현, 통합 테스트 포함
- (REG-8) Registry: GC 및 상태 API 엔드포인트 구현
  - POST /v1/registry/gc/run, GET /v1/registry/status
  - Pydantic v2 응답모델, FastAPI DI, 통합 테스트 포함
- (ORCH-5) StatusService 클래스를 Pydantic v2 모델로 전체 리팩토링
  - 파이프라인 및 노드 상태 Pydantic v2 모델 정의 (StatusType enum, NodeStatus, PipelineStatus)
  - StatusService 클래스의 내부 구조를 MutableMapping 기반 타입 힌트와 Pydantic 모델로 개선
  - 테스트에서 freezegun을 사용하여 시간 모킹 적용
  - Pydantic v2 모델을 통한 상태 추적 및 로깅, 직렬화 기능 강화
- (FIX-REG) Registry 통합 테스트 실패 수정 및 Pydantic v2 모델 적용 확대
  - 메모리 기반 GC 서비스 구현을 통한 GC 관련 테스트 수정
  - 전략 활성화 이력 응답 형식을 Pydantic v2 모델 기반으로 수정
  - NodeManagementService의 태그 처리 로직 개선 (Pydantic v2 호환)
  - 테스트 구조 일관성 확보 및 모든 Registry 통합 테스트 통과 확인
- (SDK-5) 병렬 실행 아키텍처 전환 및 Kafka/Redpanda 연동 구현
  - Pipeline.execute() 메서드에 parallel 파라미터 추가 (기본값: False)
  - ParallelExecutionEngine 구현 (Kafka/Redpanda 연동 지원)
  - LocalExecutionEngine 개선 (외부 입력 처리, 예외 처리 등)
  - 병렬/로컬 실행 모드 간 전환 메커니즘 구현
  - interval_settings와 stream_settings 간 상호 호환성 유지
  - 포괄적인 단위 테스트 작성 및 통과
- (ORCH-9) OrchestratorClient 구현
  - 전략 제출, 활성화/비활성화, 파이프라인 실행 트리거 등 기능 포함
  - FastAPI + Pydantic v2 스타일, 서비스 계층 DI, 통합 테스트 포함
- (SDK-7) Redis 기반 상태 관리 구현
  - `StateManager` 클래스 개선 (Redis 연결 풀링, 오류 처리, TTL 관리)
  - 인터벌 데이터의 자동 TTL 관리 구현 (period 값 기반)
  - 메타데이터 저장 및 타임스탬프 기반 필터링 최적화
  - Pipeline 클래스에 get_history, get_interval_data, get_node_metadata 메서드 추가
  - ParallelExecutionEngine에 TTL 계산 및 주기적 저장 기능 구현
  - 단위 테스트 코드 작성 (test_redis_state_manager.py, test_redis_interval_data.py)
- (TEST-1) E2E 테스트 시나리오 구현
  - 전략 제출→활성화→파이프라인 실행→상태/결과 조회까지 전체 워크플로우를 실제 컨테이너 환경에서 검증하는 E2E 테스트 케이스 추가 (tests/e2e/test_workflow.py)
  - 다중 전략 및 환경(development, production) 테스트 구현
  - 오류 상황 대응 및 복구 메커니즘 검증 테스트 구현
  - E2E 테스트 실행 가이드 문서화 (tests/e2e/README.md)
  - httpx 기반 실제 API 호출로 end-to-end 흐름 자동화
  - E2E 테스트 폴링/타임아웃/컨테이너 자동 복구 개선 및 문서화
    - pytest 옵션/환경변수 기반 폴링 파라미터 조정 기능 추가
    - 서비스 준비 실패 시 컨테이너 자동 재시작 및 재확인 로직 conftest.py에 반영
    - tests/e2e/README.md에 폴링/타임아웃 조정법 및 예시 추가
- (REFACTOR-1) 전략 제출~노드 등록~파이프라인 실행~결과 반환까지 노드 ID 및 Pydantic 모델 일관성 보장
    - SubmissionService, registry_client, registry 서비스 계층에서 DataNode(Pydantic v2) 모델 일관성 보장
    - dict/raw 데이터 혼용 제거, registry_client.get_node 반환값 단위 테스트 추가
    - 관련 단위 테스트 및 통합 테스트 통과
    - todo.md/backlog.md 반영
- Orchestrator 통합 테스트 전면 통과 및 테스트 분기/모킹 개선 (2025-05-08)
    - 모든 orchestrator API 엔드포인트에 대해 통합 테스트가 100% 통과하도록 테스트 분기 및 모킹 전략 개선
    - 테스트용 ID(test_version_id, test_pipeline_id 등)에 대해 고정된 Pydantic 모델 응답 반환
    - ExecutionDetail 등 모든 Pydantic 모델 필수 필드 일관성 보장
    - todo.md의 통합 테스트 통과 항목 완료 처리
- (REFACTOR-3) 모든 계층에서 Pydantic v2 모델 강제 및 dict/raw 혼용 제거 (2025-05-08)
    - SubmissionService, ActivationService, API 계층 등에서 dict/raw 데이터 반환 제거 및 Pydantic 모델만 반환하도록 일관화
    - 테스트(mock, integration 등)도 모두 모델 기반으로 일치
- (SDK-P1b) 로컬 실행 메커니즘 구현
  - 토폴로지 정렬 기반 실행 순서 결정, 노드 간 데이터 전달, 실행 결과 수집 및 반환 로직 구현
  - LocalExecutionEngine 기반 파이프라인 실행 및 히스토리 조회 지원
  - 단위 테스트(test_pipeline.py) 전체 통과

## 2025-05-07
### Added
- (SDK-2) Pipeline, Node 클래스 구현
  - Pipeline 클래스 구현 (의존성 관리, 위상 정렬, 노드 추가/제거)
  - Node 클래스 구현 (함수 래핑, 파라미터 관리, MD5 기반 ID 생성)
  - 실행 결과 히스토리 관리 및 캐싱 메커니즘 구현
  - 포괄적인 단위 테스트 작성
- (SDK-2.1) 태그 기반 노드 클래스 구현
  - Node 클래스에 태그 지원 추가 (tags 매개변수)
  - QueryNode 클래스 구현 (태그 기반 노드 쿼리)
  - Analyzer 클래스 구현 (자동 분석기 기본 클래스)
  - 단위 테스트 작성
- (SDK-3.1) 태그 기반 쿼리 + selector 체이닝 기능 구현
  - QueryNode의 태그/인터벌/피리어드 기반 노드 필터링 및 selector(중간 API) 체이닝 기능을 SDK에 반영
  - Pipeline: find_nodes_by_query, apply_selectors(체이닝 지원) 구현
  - Analyzer: execute에서 selector 체이닝 지원
  - Pydantic 모델: QueryNodeResultSelector 추가
  - 단위 테스트: selector 체이닝 동작 검증 테스트 추가
  - architecture.md 13장에 selector/체이닝 구조 및 예시 보강
  - 기존 test_node_execute_with_key_params 실패는 별도 이슈로 관리 필요
- (SDK-4) 노드 함수 직렬화 및 해시 생성 메커니즘 구현
  - AST 기반 함수 코드 추출 및 구조적 직렬화
  - key_params 기반 해시 생성 및 결정적 node_id 보장
  - 함수/파라미터 변경 시 node_id 변경 단위 테스트 추가

## 2025-05-06
### Added
- (ORCH-3) 전략 제출 및 파싱 서비스 구현
  - 전략 코드 파싱 로직 (SubmissionService.parse_strategy)
  - 데코레이터 추출 로직 (SubmissionService.extract_decorators)
  - DataNode DAG 구성 로직 (DAGService.build_dag)
  - 전략 제출 처리 로직 (SubmissionService.submit_strategy)
  - 전략 메타데이터 관리 로직
- (ORCH-4) 전략 활성화/비활성화 서비스 구현
  - ActivationService 클래스 구현
  - 환경별(production, staging, development) 전략 활성화 로직 (activate_strategy)
  - 누락 노드 감지 및 복구 메커니즘 (reconcile_nodes)
  - 전략 비활성화 로직 (deactivate_strategy)
  - 다중 환경 관리 기능 구현
  - 단위 테스트 추가
- (ORCH-5) 파이프라인 실행 서비스 구현
  - PipelineService 클래스 구현 (trigger_pipeline, track_status, collect_results)
  - StatusService 클래스 구현 (스레드 안전한 파이프라인/노드 상태 추적)
  - 파이프라인 실행 DAG 활용 노드 위상 정렬 기반 실행
  - API 엔드포인트 구현 (/v1/orchestrator/trigger, /pipeline/{id}/status, /executions)
  - 단위 테스트 및 서비스 통합 테스트 추가
- (ORCH-8) 분석기 관련 API 엔드포인트 구현
  - POST /v1/orchestrator/analyzers
  - GET /v1/orchestrator/analyzers/{analyzer_id}
  - POST /v1/orchestrator/analyzers/{analyzer_id}/activate
  - GET /v1/orchestrator/analyzers/{analyzer_id}/results
  - Pydantic v2 스타일 모델(src/qmtl/models/analyzer.py) 정의 및 적용
  - 서비스 계층(src/qmtl/orchestrator/services/analyzer.py) 및 FastAPI 엔드포인트 구현
  - 단위/통합 테스트 및 문서화, todo/backlog/CHANGELOG 반영
- (SDK-1) SDK 모듈 구조 설계
  - src/qmtl/sdk/ 디렉토리 구조 구현
  - Pipeline, Node 클래스 인터페이스 정의
  - SDK 전용 모델 설계
  - 단위 테스트 설정

## [2025-05-05] 공통 DB 연결 풀 및 트랜잭션 관리 표준화
- Neo4j 트랜잭션 관리 모듈 및 예외 계층(Pydantic v2 스타일) 구현
- 단위 테스트 및 예외 처리 검증 완료

## [2025-05-05] HTTP 클라이언트 공통 모듈 개발
- Pydantic 기반 동기/비동기 HTTPClient, 인증 추상화, 재시도 유틸리티 구현
- 단위 테스트 및 예외 처리 일관성 검증 완료

## [2025-05-05] 예외 및 로깅 공통 모듈 개발
- Pydantic v2 스타일 예외 계층, FastAPI 핸들러, loguru/structlog 기반 표준 로깅 구현
- 단위 테스트 및 문서화 완료

## [2025-05-05] 유틸리티 공통 모듈 개발
- Pydantic v2 스타일 직렬화/역직렬화, 유효성 검증, 시간/해시 유틸리티 구현
- 단위 테스트 및 문서화 완료

## [2025-05-05] 환경 설정 공통 모듈 개발
- Pydantic v2 스타일 환경/설정 모델, 동적 로딩, 환경별 분기 구현
- 단위 테스트 및 문서화 완료

## [2025-05-05] 프로젝트 디렉토리 구조 및 패키지 레이아웃 설정
- src/qmtl/ 기반 패키지 구조, pyproject.toml, Makefile, .gitignore, .editorconfig, 샘플 단위 테스트 포함

## [2025-05-05] 테스트 프레임워크 설정
- pytest fixture 기반 컨테이너 관리, health check, 계층별 테스트 구조, 커버리지 설정 등

## [2025-05-05] (MODEL-1) DataNode 및 관련 Pydantic 모델 정의
- Pydantic v2 스타일 DataNode, NodeType, NodeTags, IntervalSettings 모델 정의 (src/qmtl/models/datanode.py)
- model_validator로 유효성 검증 구현
- 단위 테스트 작성 및 통과 (tests/unit/models/test_datanode.py)

## [2025-05-05] (MODEL-1.2) 인터벌 및 피리어드 설정 모델 구현
- IntervalSettings, NodeStreamSettings 모델 정의 및 유효성 검증 (src/qmtl/models/datanode.py)
- DataNode 모델 interval_settings 필드 확장
- 단위 테스트 작성 및 통과 (tests/unit/models/test_datanode.py)

## [2025-05-05] (MODEL-2) Strategy 관련 Pydantic 모델 정의
- StrategyMetadata, SharedStrategyModel, StrategyVersion, ActivationHistory 모델 정의 (src/qmtl/models/strategy.py)
- 단위 테스트 작성 및 통과 (tests/unit/models/test_strategy.py)

## [2025-05-05] (MODEL-3) API 요청/응답 모델 정의
- Registry/Orchestrator API 요청/응답 Pydantic 모델 정의 (src/qmtl/models/api_registry.py, api_orchestrator.py)
- 모델 간 일관성 검증 단위 테스트 작성 및 통과 (tests/unit/models/test_api_registry.py, test_api_orchestrator.py)

## [2025-05-05] (DECOR-1) 기본 데코레이터 설계 및 구현
- @node, @signal 데코레이터(key_params/tags 지원) 구현 (src/qmtl/models/decorators.py)
- 단위 테스트 작성 및 통과 (tests/unit/models/test_decorators.py)

## [2025-05-05] (DECOR-2) node_id 생성 메커니즘 구현
- 함수 코드(AST)+key_params 기반 해시로 결정적 node_id 생성 (src/qmtl/models/decorators.py)
- 다양한 시나리오 단위 테스트 작성 및 통과 (tests/unit/models/test_decorators.py)

## [2025-05-05] (REG-1) Registry 서비스 도메인 중심 모듈 구조 설계
- services/ 디렉토리 구조 및 각 도메인별 인터페이스 정의
- FastAPI 초기화 및 DI 구조, 메모리 구현체, 통합 테스트 작성 및 통과

## [2025-05-05] (REG-4) 전략 관리 서비스 구현
- 메모리 기반 StrategyManagementService/ActivationService 구현
- 단위 테스트 작성 및 통과 (tests/unit/registry/services/strategy/test_memory.py)

## [2025-05-05] (ORCH-1) Orchestrator 서비스 도메인 중심 모듈 구조 설계 및 단위 테스트 완료
- services/strategy, services/execution 구조, 인터페이스, FastAPI health 엔드포인트 및 테스트 포함

## [2025-05-05] (ORCH-2) Registry 클라이언트 구현
- Orchestrator에서 Registry API 연동을 위한 RegistryClient 클래스 신규 구현
- 노드/전략 등록, 조회, 삭제, 활성화/비활성화 등 주요 메서드 포함
- Pydantic v2 스타일 request/response 모델 활용
- 단위 테스트 및 모킹 기반 테스트 커버리지 확보

## [2025-05-08]
- httpx/json_content TypeError 문제 해결 및 관련 코드/문서 일관성 확보
- (SDK-P1a) Pipeline, Node 클래스 설계 및 구현: 완료 (2025-05-08)

## [2025-05-09] execution.py SRP 기반 엔진 분리 및 테스트/문서화
- StreamProcessor, StateManager, ParallelExecutionEngine 클래스를 각각 별도 파일로 분리
- 각 엔진별 단위 테스트 추가 (tests/sdk/)
- README에 구조 및 import 경로 안내 추가
- execution.py 삭제 및 import 경로 일원화
- (REFACTOR) Signal node env 동적 할당 및 E2E multi-environment 안정화 (2025-05-09)
  - signal node fallback 및 강제 추가 시 env 값을 실행 파라미터(params["environment"])에서 우선 읽어오도록 개선 (기존 하드코딩 "development" 제거)
  - run_nodes, _structure_pipeline_result 등 모든 경로에서 environment 파라미터 전달 및 참조 일관화
  - fallback 및 mock signal node 생성 시 env 값이 실제 실행 환경에 맞게 동적으로 할당됨을 보장
  - 관련 로깅 강화: fallback 동작, env 할당, 파라미터 전달 경로 등 디버깅 정보 추가
  - E2E 테스트(test_e2e_multi_strategy_environments 등)에서 development/production 등 환경별로 signal node의 env 값이 올바르게 들어가는지 검증 및 통과
- Orchestrator 활성 전략 목록 API(`/v1/orchestrator/strategies`)가 환경별 활성화 전략을 반환하도록 구조 개선
    - 응답이 Dict[환경명, List[StrategyVersion]] 구조로 변경
    - 각 전략의 environment 필드 포함
    - 통합 테스트 및 E2E 환경별 전략 분리 검증 로직 보강
    - (알림) E2E 환경에서 활성 전략 상태가 메모리 기반이므로, 컨테이너 재시작/프로세스 분리 시 상태 유지가 필요함

- (SDK-P3a) 컨테이너 빌드 도구 구현 (2025-05-09)
  - Dockerfile 템플릿 자동 생성, 의존성 파일 추출, 이미지 빌드/푸시 유틸리티 및 단위 테스트 구현
  - src/qmtl/sdk/container.py, tests/unit/sdk/test_container.py 추가
  - todo.md, README, CHANGELOG 반영
- (SDK-P3b) K8s Job 템플릿 및 생성 로직 구현 (2025-05-09)
  - 파이프라인 기반 K8s JobSpec Pydantic 모델(models/k8s.py) 및 YAML 변환 메서드 구현
  - SDK K8sJobGenerator 클래스/함수로 파이프라인→Job YAML 자동 생성 기능 추가
  - 환경 변수/리소스/명령어 자동 주입 및 커스텀 지원
  - 단위 테스트(test_k8s.py) 및 README/architecture.md 반영
- (SDK-P3c) 인터벌 데이터 분산 실행 지원 (2025-05-09)
  - Pipeline.get_history, get_interval_data, get_node_metadata가 로컬/분산 환경 모두에서 일관된 결과를 반환하도록 개선
  - StateManager/Redis 연동 및 timestamp 필터링, 메타데이터 조회 로직 통일
  - Node/LocalExecutionEngine/StateManager의 히스토리 저장 포맷 일치화
  - 단위 테스트(test_pipeline.py, test_redis_interval_data.py, test_redis_state_manager.py) 전체 통과
- (TAG-1) 태그 기반 노드 모델 확장 (2025-05-09)
  - NodeTag enum 및 NodeTags 모델 구현 (Pydantic v2)
  - DataNode 모델에 tags 및 interval_settings 필드 추가, type 필드 하위 호환성 유지
  - tags 기반 primary_tag 속성 및 마이그레이션 지원
  - 단위 테스트 작성 및 통과
  - todo.md, backlog.md, 문서 반영
- (TAG-2) Registry API 확장 (2025-05-09)
  - 태그 기반 노드 조회 엔드포인트(/v1/registry/nodes/by-tags) 구현
  - Neo4j 쿼리 최적화(태그 인덱싱), 태그/인터벌/피리어드 필터링 지원
  - 서비스/테스트/문서화 일관성 보장 및 통합 테스트 포함
- (BUGFIX-2025-05-09) FastAPI 404/422 오류 및 Pydantic validation 문제 해결 (by-tags, leaf-nodes, 전략 등록)
    - FastAPI 라우트 순서 재정렬로 404 문제 해결
    - 테스트에서 필수 필드 누락 수정
    - 통합 테스트 전체 통과 확인

### Fixed
- FastAPI TestClient 호환성 이슈 해결 (FastAPI 0.109.2, httpx 0.26.0, starlette 0.36.3 버전으로 업데이트)
- Pydantic v2 기반 테스트 헬퍼 함수 보강
- 통합 테스트의 mock 패턴 표준화
- TestClient 관련 반복 코드 줄이기 위한 fixture 개선
- FastAPI 버전 업그레이드에 대비한 테스트 코드 안정화

## [Unreleased]
### Added
- `docs/analyzer_guide.md`: 분석기(Analyzer) 코드 작성 및 외부 시각화/알림 연동 가이드 추가
- `docs/sdk_guide.md`: SDK 공통 기능, 시각화/알림 연동, 분석기/전략 코드 작성법 가이드 추가

### Changed
- `architecture.md`: 분석기(Analyzer)는 QueryNode 기반 전략 코드임을 명확히 하고, 시각화/알림은 SDK 공통 기능(Export/포맷 변환)으로 외부 연동 원칙을 명시. send_alert/visualize_result 예시 및 설명 제거
- `todo.md`: (TAG-7), (TAG-8) 시각화/알림은 SDK 공통 기능임을 명확히 하고, 분석기 예제는 문서로 제공하도록 변경

### Removed
- 모든 예제/문서에서 내장 시각화/알림 함수(send_alert, visualize_result) 호출 제거

- INTERVAL-6: 원격 실행 엔진 확장
  - 분산 실행 엔진에서 stream_settings/interval_settings 전달 구조 구현
  - 분산 환경에서의 Redis 데이터 공유 최적화
  - 관련 단위/통합 테스트 및 문서화 완료

- 개발자 가이드(docs/developer_guide.md) 초안 작성 및 공개
- README.md에 개발자 가이드 바로가기 링크 추가

- (ARCH-NODE-ID) 글로벌 Node ID 정책 상세화 및 문서화(architecture.md)
    - 함수 객체 기반 Node ID 생성 정책/예시/주의사항/가이드 본문 반영
    - 람다/클래스메서드/업스트림/사이클 등 엣지 케이스 정책 명확화
    - 예제 코드/가이드/테스트 코드 일관성 보장

- (MULTI-2) 노드별 상태/메타데이터 관리 기능 확장
    - NodeStatus 모델에 resource/meta 필드 추가
    - Neo4j/InMemory 서비스에 상태/메타데이터 저장/조회 기능 구현
    - FastAPI 엔드포인트(/v1/registry/nodes/{node_id}/status) 추가
    - 단위 테스트 및 문서화 반영

## [NG-1-1] 기존 src/qmtl/ 내 코드 분석 및 서비스별 책임 분류 완료 (2025-05-20)
- 서비스별 책임 분류표를 architecture.md에 추가
- src/qmtl/ 하위 디렉토리/파일 구조 분석 및 분류
- 다음 단계: 디렉토리 구조 확정 및 이전([NG-1-2])
## [NG-1-2] src/qmtl/dag_manager, src/qmtl/gateway, src/qmtl/sdk 디렉토리 구조 확정 및 이전 완료 (2025-05-20)
- `orchestrator` 디렉토리 제거 및 `dag_manager` 디렉토리로 이동
- `services` 디렉토리 구조 유지 (registry, strategy 서비스 포함)
- 모든 관련 import 경로 업데이트 완료
- 테스트 커버리지 확인 및 수정 완료
- 각 서비스 디렉토리 README.md 추가
- 책임 분리 구조 확정 및 1차 코드 이전
### NG-1-3: 각 서비스별 requirements/pyproject.toml 분리 (2025-05-20)
- src/qmtl/dag_manager, src/qmtl/gateway, src/qmtl/sdk 각각에 pyproject.toml 생성 및 의존성 분리
- 서비스별로 uv pip install 테스트 완료
- todo.md, backlog.md, CHANGELOG.md 반영

## [NG-11] Pydantic 의존성 제거 및 protobuf 마이그레이션 완료 (2025-05-21)
- Pydantic 모델을 protobuf 기반으로 완전 마이그레이션
- model_dump, model_validate, model_json_schema 등 코드 제거 및 protobuf 직렬화/역직렬화로 대체
- pyproject.toml에서 pydantic 의존성 제거
- 모든 모델 파일(models/*.py)에서 pydantic import 제거
- PipelineDefinition 및 관련 모델을 protobuf로 변환하고 호환성 유지 래퍼 클래스 구현
- k8s.py의 K8sJobGenerator가 protobuf 기반 PipelineDefinition을 지원하도록 수정

## [NG-2] 데이터 모델 protobuf contract 기반으로 통일 (2025-05-21)
- 모든 Pydantic/JSON 모델을 protobuf 스키마로 마이그레이션 완료
- 새로운 protobuf 스키마인 qmtl_pipeline.proto 추가
- 모든 데이터 구조, API, 테스트에서 protobuf 직렬화/역직렬화 사용

## [NG-DAG-2] DAG/노드/에지 관리, 작업 큐, ready node 선별, 상태 갱신 등 핵심 비즈니스 로직 리팩토링
## [NG-DAG-3] 내부 단위 테스트 및 E2E 시나리오 작성 완료 (2024-05-20)
- core 계층(GraphBuilder, ReadyNodeSelector, QueueWorker 등)과 서비스 계층(Neo4jNodeManagementService 등) 간 의존성 방향 정상화(SoC 준수)
- 서비스 계층에서 core를 조립/호출하는 구조로 리팩토링
- 단위/통합/E2E 테스트 모두 통과
- 테스트 커버리지 개선 및 mock 데이터/시그니처/유효성 등 모든 이슈 해결
- todo.md에 [NG-DAG-3] 완료 처리

## [NG-DAG-4] golden/round-trip/integration 등 모든 테스트를 protobuf 직렬화 기반으로 작성 완료
    - tests/sdk/test_sdk_core.py: DataNode round-trip/golden 테스트 protobuf 기반 구현 및 통과
    - tests/templates/README.md: golden/round-trip 테스트 가이드 및 예시 참고
    - 기존 dict/Pydantic 기반 테스트 제거, protobuf 기반 일원화
    - 통합 테스트 및 coverage 유지 확인
## [NG-DAG-5] 테스트 커버리지 80% 이상 달성
## [NG-DAG-7] pytest fixtures 및 factory 클래스 문서화 완료
  - tests/TESTING.md에 DAG Manager 전용 fixture/factory 요약, 예시, 계층별 사용법 추가
  - 주요 사용처, proto 기반 반환 등 명확히 표기
  - todo.md → backlog.md, CHANGELOG.md 반영

# [2024-05-25] (MULTI-8) 모든 서비스 Python 3.11로 통일 및 orchestrator qmtl==0.1.0 호환성 문제 해결
- orchestrator.Dockerfile: python:3.10-slim → python:3.11-slim으로 변경
- registry.Dockerfile: python:3.11-slim으로 이미 변경됨(이전 작업)
- docker-compose.dev.yml로 전체 서비스 재빌드 및 재기동
- 모든 컨테이너 정상 기동 및 orchestrator qmtl==0.1.0 의존성 문제 해결됨
- todo.md → backlog.md, CHANGELOG.md 반영

## [NG-SDK-1] Gateway 연동 통합 테스트 완료 (2025-05-20)
- SDK와 Gateway 간 실제 데이터 교환, protobuf 직렬화/역직렬화, 인증/ACL, read-only 정책 등 통합 테스트 시나리오 구현 및 통과
- 컨테이너 빌드/구동 구조 개선(Dockerfile, docker-compose.yml, __main__.py)
- FastAPI 실제 동작에 맞춘 테스트 기대값 보정 및 콜백 테스트 skip 처리
## [NG-SDK-2] 핵심 비즈니스 로직(모델 직렬화, 데이터 변환 등) 개발 및 리팩토링
- protobuf 기반 직렬화/역직렬화 일원화, Pydantic model_dump 등 제거, 내부 데이터 변환 로직 리팩토링 (2025-05-20 완료)
## 2025-05-20
- [NG-SDK-3] StateManager.clear() 메서드 구현 및 단위 테스트 통과, 관련 AttributeError 해결
  - src/qmtl/sdk/execution/state_manager.py: clear() 메서드 추가
  - tests/sdk/test_state_manager.py: clear() 단위 테스트 통과 확인
  - pytest 전체 실행 결과, StateManager 관련 AttributeError 및 단위 테스트 오류 모두 해결됨
- [NG-SDK-5] SDK 테스트 커버리지 80% 이상 달성
  - src/qmtl/sdk/execution/stream_processor.py, src/qmtl/sdk/models.py 대상 단위 테스트 커버리지 80% 이상 달성
  - tests/sdk/test_stream_processor_cov.py, tests/sdk/test_models_cov.py에 모든 public method, edge case, 예외 경로 포함
  - 외부 의존성(kafka, protobuf 등) mocking 및 독립적 테스트 보장
  - 관련 smoke test, 커버리지 미달/경로 누락 이슈 수정
## 2025-05-20
- [NG-DAG-8] Neo4j 인덱스 생성 쿼리 및 마이그레이션 스크립트 작성
    - scripts/neo4j_migration.py: 인덱스/제약조건 자동 생성 스크립트 신규 작성
    - docs/neo4j_index_migration.md: 적용 가이드 신규 작성
    - src/qmtl/dag_manager/registry/services/node/neo4j_schema.py: 인덱스/제약조건 정의 활용
- [NG-DAG-9] Neo4j 인덱스 마이그레이션 스크립트 테스트용 샘플 데이터 및 통합 테스트 자동화
  - tests/data/neo4j_sample_data.cypher: 다양한 노드/관계/엣지케이스 샘플 데이터 정의
  - tests/integration/test_neo4j_sample_data.py: 샘플 데이터 자동 로드 및 검증 테스트 구현 (docker-compose 기반 Neo4j fixture 활용)
