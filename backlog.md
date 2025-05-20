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
  - docs/generated/pydantic_model_inventory.md의 최우선 변환 대상 모델을 기반으로 .proto 스키마 초안 설계
  - protos/ 디렉토리에 도메인별 .proto 파일 작성
  - docs/proto_schema_versioning.md에 버전 관리 가이드 문서화

## [NG-2-1] 기존 models/ 내 Pydantic 모델 목록화 및 protobuf로 변환 대상 선정 (2025-05-20)
  - src/qmtl/models/ 내 모든 Pydantic 모델을 목록화하고, protobuf 변환 우선 대상을 선정함
  - docs/generated/pydantic_model_inventory.md에 결과 문서화
# [2025-05-20] (NG-1-5) 서비스별 독립 실행/테스트 환경 구축 완료
- 각 서비스별 docker-compose.yml, Makefile, README.md에 독립 실행/테스트/컨테이너 안내 추가
- smoke test(docker-compose up/down)로 컨테이너 기동 확인
# [2025-05-20] (NG-1-4) 각 서비스별 Dockerfile 작성 및 빌드 테스트 완료
- dag_manager, gateway, sdk 각 서비스별 Dockerfile 작성 및 최신화
- 모든 서비스별 Docker 이미지 빌드 테스트 성공
# [2025-05-14] (FIXTURE-REGISTRY-ORCH) registry/orchestrator 서비스도 Neo4j/Redis/Redpanda처럼 pytest fixture에서 docker-compose로 직접 기동/정리하는 구조(docker fixture)로 전환 완료
  - tests/conftest.py의 docker_compose_up_down fixture가 registry/orchestrator/neo4j/redis/redpanda 컨테이너를 일괄 관리하며 health check로 준비 상태를 보장
  - 모든 E2E/통합 테스트는 해당 fixture 이후에만 FastAPI TestClient(app) 인스턴스를 생성하도록 구조화되어 있음
  - 환경변수/포트/네트워크 일치, race condition, 연결 실패 등 문제를 원천적으로 차단
  - Neo4j 환경변수 분리 정책 적용: pytest(호스트)는 bolt://localhost:7687, 컨테이너는 bolt://neo4j:7687만 사용하도록 명확화
  - 정책/구현/문서화: tests/conftest.py, docs/neo4j_env_policy.md, tests/README.md, 주석 보강
  - 통합 테스트(test_node_dependency_management)에서 Neo4j 연결 오류(500) 해결 및 정상 통과 확인
  - tests/README.md, tests/e2e/README.md, docs/developer_guide.md, CHANGELOG.md에 구조 및 사용법 반영
# [2025-05-13] (MULTI-7) 실시간 모니터링/대시보드/알림 시스템 연동
  - Registry: 상태 변화 이벤트 발행/구독 서비스(EventPublisher/EventSubscriber), 실시간 이벤트 API 추가
  - Orchestrator: 이벤트 구독 클라이언트(EventClient) 및 대시보드/알림 연동 샘플 구현
  - Pydantic v2 스타일 이벤트/상태 모델 정의(models/event.py)
  - 단위 테스트 및 모킹 기반 검증(tests/unit/models/test_event.py, tests/unit/registry/services/test_event.py, tests/unit/orchestrator/services/test_event_client.py)
  - FastAPI API 연동(/v1/registry/events/node-status 등)
# [2025-05-13] (MULTI-5) 콜백/이벤트 훅 기반 노드 생명주기 관리
- Registry: 노드 실행/정지 신호 콜백 등록/해제/조회/트리거 API 및 도메인 서비스 구현 (`/v1/registry/nodes/{node_id}/callbacks`)
- Orchestrator: 콜백 등록/해제 요청, 콜백 이벤트 수신 후 노드 실행/정지 신호 처리 구조 초안
- Pydantic v2 스타일 콜백 모델(models/callback.py) 정의
- 단위/통합 테스트 및 FastAPI DI/모킹 구조 검증 (tests/integration/test_callback.py)
- 정책 Node ID(32자리 해시) 기반 일관성 보장, 문서/가이드/테스트/CHANGELOG/todo.md 반영

# [2025-05-13] (MULTI-4) 의존성 기반 동적 스케줄링 및 리소스 최적화
- Registry: 전체 DAG 구조, 노드 의존성 정보, 실행 가능 노드 목록 제공 API 구현
    - `/v1/registry/pipelines/{pipeline_id}/dag` (DAG 구조)
    - `/v1/registry/pipelines/{pipeline_id}/ready-nodes` (ready node 목록)
    - 서비스/DI/모킹/테스트 일관성 보장
- Orchestrator: Registry에서 DAG/의존성/상태 정보 조회, 실행 가능한 노드만 선별 실행, 리소스 상황에 따라 우선순위/스케줄링, 비활성 노드 자동 정지/재시작 (별도 이슈)
- 단위/통합 테스트(mock 기반) 및 FastAPI DI/의존성 주입/모킹 구조 검증
- todo.md, backlog.md, CHANGELOG.md 반영
# [2025-05-13] (PIPELINE-1) 글로벌 Pipeline ID 정책 적용 및 일관화
  - Registry/Orchestrator/SDK/테스트/문서 전체에서 version_id, strategy_id 등 파이프라인 식별자 제거, pipeline_id(32자리 해시)로 일원화
  - Pipeline ID 생성 정책 및 예시를 architecture.md, nodeID.md, README 등과 일치하도록 반영
  - 모든 Pydantic 모델, 서비스, API, 테스트(mock 포함)에서 pipeline_id만 사용하도록 리팩터링
  - 기존 version_id, strategy_id 등 관련 필드/로직/문서/테스트 전수 점검 및 일괄 대체
  - 테스트(mock 포함)에서 pipeline_id 기반 데이터 흐름/값 사용 보장 및 일관성 검증
  - 관련 정책/예시/가이드/테스트/주의사항 등 문서화 및 todo.md, backlog.md, CHANGELOG.md 반영
# [2025-05-11] (E2E-STATE) Orchestrator 활성 전략 등 상태 저장 방식 개선
  - Redis 기반 환경별 활성 전략 상태 영속화 구현 (ActivationService)
  - 서비스 초기화 시 Redis에서 상태 복구, 활성화/비활성화 시 Redis에 즉시 반영
  - E2E 테스트(test_e2e_multi_strategy_environments)에서 orchestrator 컨테이너 재시작 후에도 활성화 상태가 유지되는지 검증
  - 장애/복구 상황(예: Redis flush, 장애 후 복구)에서 일관성 보장 테스트
  - 관련 구조/정책을 architecture.md, README, tests/README.md, tests/e2e/README.md에 명시
  - todo.md → backlog.md, CHANGELOG.md 반영
# [2025-05-11] (FIXTURE-4) E2E 테스트에서 fixture-1,2,3의 목적에 맞는 session/module scope 분리 및 적용 검증
  - Redis/Neo4j/Redpanda 등 외부 리소스 컨테이너/연결 fixture가 E2E 테스트에서 일관되게 session/function scope로 분리되어 있음
  - tests/conftest.py, tests/README.md, tests/e2e/README.md 등에서 fixture의 scope/구조/네이밍/주석이 가이드와 일치함을 확인
  - E2E 테스트에서 여러 테스트가 동일 리소스를 바라보며, 데이터 일관성/독립성이 fixture 구조로 보장됨
  - 추가적인 구조 개선/리팩토링 불필요 (테스트/문서/가이드도 최신 상태)
  - 실제 E2E 테스트 실행 결과, fixture 구조 문제로 인한 데이터 불일치/공유 문제 없음 (환경별 전략 분리 등은 별도 비즈니스 로직 이슈)
  - 관련 점검 결과를 backlog.md, CHANGELOG.md, tests/README.md, tests/e2e/README.md에 반영
# [2025-05-10] (FIXTURE-3) redpanda 등 메시지 브로커 컨테이너/연결 fixture 구조 개선 및 통합
  - redpanda 등 메시지 브로커 컨테이너/연결용 session scope fixture를 conftest.py에 통합
  - 각 테스트의 상태 초기화(clean)용 function/module scope fixture 별도 정의
  - E2E/통합 테스트에서는 session fixture만 사용하거나, 필요에 따라 상태 일부만 초기화
  - 단위/모듈 테스트에서는 clean fixture를 사용해 테스트 독립성 보장
  - fixture 네이밍 및 docstring 일관성 강화
  - 테스트/문서/가이드에 fixture 사용 예시 추가
  - 기존 fixture 사용처 전수 점검 및 리팩토링
# [2025-05-10] (INTERVAL-5) 로컬 실행 엔진 확장
  - 인터벌 데이터 관리 기능 통합
  - 인메모리 캐싱 구현 (Redis 없이 테스트 가능)
  - 테스트 시나리오 및 단위 테스트 작성
# [2025-05-10] (FIXTURE-3) redpanda 등 메시지 브로커 컨테이너/연결 fixture 구조 개선 및 통합
  - redpanda 등 메시지 브로커 컨테이너/연결용 session scope fixture를 conftest.py에 통합
  - 각 테스트의 상태 초기화(clean)용 function/module scope fixture 별도 정의
  - E2E/통합 테스트에서는 session fixture만 사용하거나, 필요에 따라 상태 일부만 초기화
  - 단위/모듈 테스트에서는 clean fixture를 사용해 테스트 독립성 보장
  - fixture 네이밍 및 docstring 일관성 강화
  - 테스트/문서/가이드에 fixture 사용 예시 추가
  - 기존 fixture 사용처 전수 점검 및 리팩토링
# [2025-05-10] (FIXTURE-2) neo4j 등 외부 DB 컨테이너/연결 fixture 구조 개선 및 통합
  - neo4j_session/neo4j_clean 등 session/function scope fixture 구현 및 통합
  - 기존 fixture 사용처 전수 점검 및 리팩토링
  - tests/README.md, tests/e2e/README.md: fixture 사용 예시 및 설명 추가
  - fixture 네이밍/docstring 일관성 강화
  - 테스트/문서/가이드에 fixture 사용 예시 추가
  - 기존 fixture 사용처 전수 점검 및 리팩토링
# [2025-05-10] (FIXTURE-1) pytest fixture 구조 개선 및 통합
  - 외부 리소스(Docker, Redis, DB 등) 컨테이너/연결용 session scope fixture를 conftest.py에 통합
  - 각 테스트의 상태 초기화(clean)용 function/module scope fixture 별도 정의
  - E2E/통합 테스트에서는 session fixture만 사용하거나, 필요에 따라 상태 일부만 초기화
  - 단위/모듈 테스트에서는 clean fixture를 사용해 테스트 독립성 보장
  - fixture 네이밍 및 docstring 일관성 강화
  - 테스트/문서/가이드에 fixture 사용 예시 추가
  - 기존 fixture 사용처 전수 점검 및 리팩토링
# [2025-05-10] (INTERVAL-4) 히스토리 데이터 접근 API 개발
  - Pipeline/StateManager/Node의 get_history 메서드 구현 및 분산/로컬/타임스탬프 필터 지원
  - 인터벌별 데이터 조회 최적화, value/dict 반환 일관성 보장
  - 단위 테스트(test_redis_interval_data.py, test_redis_state_manager.py 등) 및 커버리지 80% 이상 유지
  - 문서/CHANGELOG/todo.md 반영
# [2025-05-10] (INTERVAL-3) 인터벌별 데이터 저장 구조/TTL/최대 항목수 관리 구현
  - RedisClient에 save_history/get_history/delete_history 메서드 추가 (key: node:{node_id}:history:{interval})
  - lpush/ltrim/expire로 TTL 및 max_items 관리, 단위 테스트 통과 (test_redis_history.py)
# [2025-05-10] (INTERVAL-3) Redis 연결 및 데이터 관리 로직 구현
  - Redis 클라이언트 및 연결 관리 모듈 개발 (테스트 자동화 포함)
# (TAG-4) 분석기 예제 구현을 통한 태그 기반 분석기 검증 및 테스트 (2025-05-10)
  - 상관관계 분석기(CorrelationAnalyzer) 구현
  - 이상치 감지 분석기(AnomalyDetector) 구현
  - 성능 모니터링 분석기(PerformanceMonitor) 구현
  - 통합 테스트 작성 및 통과

# [2025-05-11] TEST-4 테스트 인프라 업그레이드 및 linter warning 정리 완료
- 테스트 결과를 기반으로 한 리포트 생성 기능 추가 (pytest-html, Makefile 연동, tests/report/README.md)
  - pytest-html 플러그인 설치 및 Makefile test, integration-test, e2e-test에 --html 옵션 추가
  - tests/report/ 디렉토리 및 README.md 생성, 리포트 파일 관리 체계화
  - CI/CD 및 로컬 개발 환경에서 시각적 테스트 결과 확인 가능
- linter warning 정리 (flake8, black, isort 설정 통일, 주요 import/style 오류 수정, 나머지 IDE로 일괄 처리)
  - .flake8, pyproject.toml 설정 통일, 미사용 import/변수/중복 import 등 주요 오류 직접 수정
  - 나머지 style/lint 경고는 IDE에서 일괄 처리하여 코드베이스 정리 완료
- [2025-05-10] (TEST-3) 테스트 자동화 스크립트 구현
  - CI 파이프라인용 테스트 스크립트 작성 (.github/workflows/ci.yml)
  - 테스트 환경 자동 설정 스크립트 작성 (scripts/setup_test_env.sh)
  - Makefile 테스트 명령 표준화 (test, integration-test, e2e-test, coverage)
  - CI 파이프라인용 Docker 환경 설정 및 테스트 자동화

- [2025-05-09] (TAG-4) 분석기 기본 클래스 구현
  - Analyzer 클래스 구현 (Pipeline 상속)
  - QueryNode 클래스 구현 (태그 기반 노드 쿼리)
  - 태그 기반 필터링 로직 구현
  - 단위 테스트 작성
# [2025-05-09] (TAG-3) Orchestrator API 확장
  - 분석기 제출 및 등록 엔드포인트 추가 (/v1/orchestrator/analyzers)
  - 분석기 활성화 엔드포인트 추가
  - 분석 결과 조회 엔드포인트 추가
  - 단위 테스트 작성
# [2025-05-09] (SDK-P1c) Pydantic 모델 정의
  - PipelineDefinition, NodeDefinition 모델 구현
  - 모델 직렬화/역직렬화 기능 구현
  - 기존 스키마와의 호환성 확보

# [2025-05-09] (SDK-P1d) 인터벌 데이터 관리 기능 구현
  - Pydantic v2 IntervalSettings, NodeStreamSettings 모델 확장 및 단위 테스트
  - Node 클래스 stream_settings 매개변수 및 interval_settings→stream_settings 정규화 지원
  - Pipeline.get_history, get_interval_data, get_node_metadata 메서드 구현 및 테스트
  - Redis 기반 StateManager 연동 및 period→TTL 변환, 히스토리/메타데이터 관리
  - 포괄적 단위 테스트(test_redis_interval_data.py, test_redis_state_manager.py, test_pipeline.py) 통과

# [2025-05-10] (INTERVAL-2) Node 클래스 인터페이스 확장
  - Node 생성자에 stream_settings 매개변수 추가
  - 스트림 설정 정규화 메서드 구현
  - 히스토리 데이터 접근 API 설계
# [2025-05-09] (SDK-P2c) Redis 기반 상태 관리 구현
  - StateManager 클래스 개선 (Redis 연결 풀링, 오류 처리, TTL 관리)
  - 인터벌 데이터의 자동 TTL 관리 구현 (period 값 기반)
  - 메타데이터 저장 및 타임스탬프 기반 필터링 최적화
  - Pipeline 클래스에 get_history, get_interval_data, get_node_metadata 메서드 추가
  - ParallelExecutionEngine에 TTL 계산 및 주기적 저장 기능 구현
  - 단위 테스트 코드 작성 (test_redis_state_manager.py, test_redis_interval_data.py)
- [2025-05-09] Orchestrator~Registry 전략 version_id/strategy_id/strategy_code 필드 일치성 점검 및 리팩터링 완료
  - architecture.md, 서비스/클라이언트/테스트/문서의 필드 정의 및 데이터 흐름 일치화
  - StrategyRegisterRequest, StrategyVersion 등 Pydantic 모델 구조/필드/타입 일관성 보장
  - API/서비스/도메인/테스트 계층에서 동일한 필드명/타입/값 사용 보장
  - 기존 코드 내 version_id, strategy_id, strategy_code 혼재 구간 전수 점검 및 리팩터링
  - 테스트(E2E/통합/단위)에서 실제 서비스와 동일한 데이터 흐름/값 사용 보장
# [완료] QMTL 2.0 아키텍처/문서 정비 (분석기/SDK/시각화/알림)
- 분석기는 QueryNode 기반 전략 코드임을 명확히 문서화 (별도 엔티티 아님)
- 시각화/알림은 SDK 공통 기능(Export/포맷 변환)으로 외부 연동 원칙 명시
- send_alert/visualize_result 등 내장 함수 예시/설명 제거
- analyzer_guide.md, sdk_guide.md 등 사용자 가이드 추가
- [x] [NG-DAG-4] golden/round-trip/integration 등 모든 테스트를 protobuf 직렬화 기반으로 작성 (완료, 2025-05-20)
    - registry/integration 테스트, enum/interval 변환, in-memory 서비스 전면 protobuf화, API 계층 dict→proto 변환, 검증 통과
- [x] [NG-공통-1] 데이터 모델(proto/pydantic) 및 API 계약 우선 확정

- [x] [NG-DAG-1] Gateway와의 연동 플로우/통합 테스트: 데이터 교환, API 직렬화/역직렬화, 인증/ACL 검증
# [2024-05-25] (MULTI-8) 모든 서비스 Python 3.11로 통일 및 orchestrator qmtl==0.1.0 호환성 문제 해결
- orchestrator.Dockerfile: python:3.10-slim → python:3.11-slim으로 변경
- registry.Dockerfile: python:3.11-slim으로 이미 변경됨(이전 작업)
- docker-compose.dev.yml로 전체 서비스 재빌드 및 재기동
- 모든 컨테이너 정상 기동 및 orchestrator qmtl==0.1.0 의존성 문제 해결됨
# [2025-05-25] (NG-SDK-3) 내부 단위 테스트 및 E2E 시나리오 작성
- tests/sdk/test_sdk_core.py: SDK 내부 단위 테스트 템플릿 추가
- tests/e2e/test_sdk_gateway_e2e.py: SDK-Gateway 연동 E2E 테스트 템플릿 추가
- pytest로 테스트 수집 및 실행 정상 확인 (테스트 코드 실제 구현 필요)
- StateManager.clear() 메서드 구현 및 단위 테스트 통과, 관련 AttributeError 해결
- todo.md → backlog.md, CHANGELOG.md 반영
- [2025-05-24] (NG-SDK-5) 테스트 커버리지 80% 이상 유지 (2025-05-24 완료)
- src/qmtl/sdk/execution/stream_processor.py, src/qmtl/sdk/models.py 대상 단위 테스트 커버리지 80% 이상 달성
- tests/sdk/test_stream_processor_cov.py, tests/sdk/test_models_cov.py에 모든 public method, edge case, 예외 경로 포함
- 외부 의존성(kafka, protobuf 등) mocking 및 독립적 테스트 보장
- 관련 smoke test, 커버리지 미달/경로 누락 이슈 수정
- todo.md → backlog.md, CHANGELOG.md 반영

# [2025-05-20] (NG-DAG-7) pytest fixtures 및 factory 클래스 문서화
- tests/TESTING.md: DAG Manager 전용 fixture/factory 요약 및 예시 추가
- 주요 사용처, 계층, proto 기반 반환 등 명확히 표기
- todo.md → backlog.md, CHANGELOG.md 반영
- [x] [NG-DAG-8] Neo4j 인덱스 생성 쿼리 및 마이그레이션 스크립트 작성 (2025-05-20)
    - scripts/neo4j_migration.py: 인덱스/제약조건 자동 생성 스크립트 작성
    - docs/neo4j_index_migration.md: 적용 가이드 문서화
    - src/qmtl/dag_manager/registry/services/node/neo4j_schema.py: 인덱스/제약조건 정의 활용
# [2025-05-20] (NG-DAG-9) 인덱스 마이그레이션 스크립트 테스트용 데이터 샘플 정의 및 통합 테스트 자동화 완료
- tests/data/neo4j_sample_data.cypher: 다양한 노드/관계/엣지케이스 샘플 데이터 정의
- tests/integration/test_neo4j_sample_data.py: 샘플 데이터 자동 로드 및 검증 테스트 구현 (docker-compose 기반 Neo4j fixture 활용)
- todo.md → backlog.md, CHANGELOG.md 반영

# [2025-06-01] (NG-GW-3) 전체 워크플로우 E2E 테스트 및 예외 처리 강화 완료
- 완전한 워크플로우 E2E 테스트 구현: 인증, 전략 등록, 데이터노드 생성, 파이프라인 실행까지 전체 흐름 검증
- 장애 상황 테스트 강화: 서비스 재시작, 오류 복구, 타임아웃 처리 등 다양한 장애 시나리오 검증
- 읽기 전용 API 제한 정책 검증: Gateway REST API가 GET 메서드만 허용하는지 확인하는 테스트 추가
- tests/e2e/test_gateway_workflow_e2e.py 파일에 TestCompleteWorkflow, TestFaultTolerance, TestReadOnlyRestriction 클래스 구현
- tests/e2e/test_gateway_exception_handling.py 파일에 다양한 예외 처리 테스트 추가
- todo.md → backlog.md, CHANGELOG.md 반영
