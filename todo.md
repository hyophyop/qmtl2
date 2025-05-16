# [2025-05-14] (FIXTURE-REGISTRY-ORCH) Neo4j 환경변수 분리 정책 적용 및 통합 테스트 Neo4j 연결 오류 해결
- [x] tests/conftest.py에서 NEO4J_URI=bolt://localhost:7687 강제 지정이 pytest(호스트)에서만 적용되도록 명확화
- [x] Registry/Orchestrator 컨테이너는 docker-compose.dev.yml의 NEO4J_URI=bolt://neo4j:7687만 사용하도록 정책/주석/문서화
- [x] 정책 문서화: docs/neo4j_env_policy.md, tests/README.md, 주석 보강
- [x] 통합 테스트(test_node_dependency_management)에서 Neo4j 연결 오류(500) 해결 및 정상 통과 확인
# 2025-05-09 설계/구현 리팩터링 TODO (architecture.md 연동)

- [x] (PIPELINE-1) version_id, strategy_id 등 전략 버전 관리 정책 제거 및 Pipeline ID 기반 파이프라인 식별/관리 정책으로 전환 (2025-05-13, architecture.md 반영)
    - Pipeline ID 생성/활용 정책 및 관련 Pydantic 모델 구조/필드/타입 일관성 보장
    - API/서비스/도메인/테스트 계층에서 Pipeline ID만을 기준으로 파이프라인을 등록/조회/실행/스냅샷/롤백/비교하도록 리팩터링
    - 기존 version_id, strategy_id 등 관련 필드/로직/문서/테스트 전수 점검 및 Pipeline ID 정책으로 일괄 대체
    - 테스트(E2E/통합/단위)에서 Pipeline ID 기반 데이터 흐름/값 사용 보장 및 일관성 검증
    - 정책/예시/가이드/테스트/주의사항 등 문서화 및 todo.md, backlog.md, CHANGELOG.md 반영
# QMTL 프로젝트 재구성 작업 계획

> **최종 수정**: 2025-05-07
> **작성자**: AI 설계 지원 시스템

이 문서는 QMTL 프로젝트를 처음부터 다시 구현하는 경우의 작업 계획을 담고 있습니다. 기존 설계 결정을 바탕으로 단계적으로 구현을 진행합니다.

## Phase 0 — DAG Registry MVP 출구 기준

- [x] 모든 예정된 작업 완료
- [x] 통합 테스트 통과 (`make ci`) 
- [x] 성능 목표 달성 (specs/perf.md 참조)
- [x] CHANGELOG 항목 추가 (*Unreleased* 섹션)
- [x] 문서 업데이트 (roadmap, ADRs, README)

# 구조적 개선 및 신뢰성 확보를 위한 우선 할 일 (2025-05-08 추가)


# [2025-05-11] [FIXTURE-4] E2E 테스트에서 fixture-1,2,3의 목적에 맞는 session/module scope 분리 및 적용 검증 (완료)
    - Redis/Neo4j/Redpanda 등 외부 리소스 컨테이너/연결 fixture가 E2E 테스트에서 일관되게 session/function scope로 분리되어 있음
    - tests/conftest.py, tests/README.md, tests/e2e/README.md 등에서 fixture의 scope/구조/네이밍/주석이 가이드와 일치함을 확인
    - E2E 테스트에서 여러 테스트가 동일 리소스를 바라보며, 데이터 일관성/독립성이 fixture 구조로 보장됨
    - 추가적인 구조 개선/리팩토링 불필요 (테스트/문서/가이드도 최신 상태)
    - 실제 E2E 테스트 실행 결과, fixture 구조 문제로 인한 데이터 불일치/공유 문제 없음 (환경별 전략 분리 등은 별도 비즈니스 로직 이슈)
    - 관련 점검 결과를 backlog.md, CHANGELOG.md, tests/README.md, tests/e2e/README.md에 반영

## 0. 구조적 개선 선행 과제
- [x] [REFACTOR-1] 전략 제출~노드 등록~파이프라인 실행~결과 반환까지 **노드 ID 및 Pydantic 모델 일관성** 보장 (2025-05-08 완료)
    - [x] 전략 제출 시 registry에 노드가 Pydantic 모델로 정확히 등록되는지 검증 및 보강
    - [x] node_id 생성/저장/조회가 registry와 orchestrator에서 완전히 일치하도록 인터페이스/로직 점검 및 리팩토링
    - [x] registry_client.get_node가 항상 Pydantic DataNode 모델을 반환하도록 강제 및 테스트
- [x] [REFACTOR-2] **모듈 간 SoC(관심사 분리) 및 인터페이스 명확화** (2025-05-08 완료)
    - [x] 전략 파싱, 노드 등록, DAG 구성, 파이프라인 실행, 상태 관리 등 각 단계별 책임과 인터페이스 명확화
    - [x] 각 단계별 단위/통합 테스트 및 로깅 강화
- [x] [REFACTOR-3] **Pydantic 모델 강제 및 타입 일관성** (2025-05-08 완료)
    - [x] dict/raw 데이터와 모델 객체 혼용 구간 제거, 모든 계층에서 Pydantic v2 스타일 강제
    - [x] Neo4j/Registry/Orchestrator 간 데이터 교환 시 모델 일관성 검증 및 테스트
- [x] [REFACTOR-4] **테스트/로깅 강화**
    - [x] 전략 제출~노드 등록~파이프라인 실행~결과 반환까지 각 단계별 입력/출력/상태를 명확히 검증하는 단위/통합 테스트 및 로깅 추가 (2025-05-09 signal node env fallback/로깅 개선 포함)
    - [x] E2E 테스트 실패 시 원인 추적을 위한 상세 로그 및 mock/factory 보강 (2025-05-09 signal node env 동적 할당 및 로깅 개선 포함)
    - [ ] 테스트 결과를 기반으로 한 리포트 생성 기능 추가
- [x] [REFACTOR-5] **신뢰성 확보**
    - [x] E2E 테스트에서 발생하는 오류를 분석하고, 각 오류에 대한 해결 방법을 문서화 (2025-05-09 signal node env 동적 할당 및 E2E multi-environment 안정화 포함)
    - [x] 각 오류에 대한 해결 방법을 코드로 구현하여 재발 방지 (2025-05-09 signal node env 동적 할당 및 E2E multi-environment 안정화 포함)
    - [x] E2E 테스트의 신뢰성을 높이기 위한 추가적인 테스트 케이스 및 시나리오 작성 (2025-05-09 signal node env 동적 할당 및 E2E multi-environment 안정화 포함)
- [x] [REFACTOR-6] execution.py SRP 기반 엔진 분리 및 테스트/문서화 (2025-05-09 완료)
    - [x] StreamProcessor, StateManager, ParallelExecutionEngine 클래스를 각각 별도 파일로 분리
    - [x] 각 엔진별 단위 테스트 추가 (tests/sdk/)
    - [x] README에 구조 및 import 경로 안내 추가
    - [x] todo.md → backlog.md, CHANGELOG.md 반영

## 1. 구조 개선 이후 테스트 안정화
- [ ] 구조 개선 후 E2E/통합 테스트(특히 signal 노드 결과 구조, 노드 누락, Pydantic 모델 불일치 등) 재점검 및 안정화
- [ ] 테스트 커버리지 80% 이상 유지 및 주요 API/비즈니스 로직 엣지 케이스 보강



## 1. 프로젝트 기반 구조 구축

### 1.1 모노레포 구조 및 개발 환경 설정
- [x] (INFRA-1) 프로젝트 디렉토리 구조 및 패키지 레이아웃 설정
  - [x] src 기반 패키지 구조 구현 (src/qmtl/)
  - [x] pyproject.toml 작성 및 기본 의존성 정의
  - [x] Makefile 생성 (lint, test, build, run 명령 지원)
  - [x] .gitignore 및 .editorconfig 설정
  - [x] 샘플 단위 테스트 추가
- [x] (INFRA-2) Docker 컨테이너 환경 구성
  - [x] docker-compose.dev.yml 작성 (Neo4j, Redis, Redpanda 포함)
  - [x] registry.Dockerfile 작성
  - [x] orchestrator.Dockerfile 작성
  - [x] 환경 변수 및 설정 파일 구성
- [x] (INFRA-3) 테스트 프레임워크 설정
  - [x] pytest 기본 설정(conftest.py, health check, fixture)
  - [x] 테스트 디렉토리 구조(unit, integration, e2e) 보강
  - [x] 테스트용 Docker 컨테이너 관리(포트 충돌 방지, fixture 활용)
  - [x] 샘플 통합/이2이 테스트 추가 및 health check 적용
  - [x] Makefile test, integration-test, e2e-test 명령 정상화
  - [x] 커버리지 설정 및 문서화

### 1.2 공통 모듈 개발
- [x] (COMMON-1) Neo4j DB 연결 및 세션 관리 공통 모듈 개발
  - [x] 인터페이스 및 구현체 설계 (src/qmtl/common/db/)
  - [x] 연결 풀 및 트랜잭션 관리 표준화
  - [x] 테스트 도구 및 단위 테스트 작성
- [x] (COMMON-2) HTTP 클라이언트 공통 모듈 개발
  - [x] 인터페이스 및 구현체 설계 (src/qmtl/common/http/)
  - [x] 재시도 전략 및 오류 처리 표준화
  - [x] 테스트 유틸리티 및 단위 테스트 작성
- [x] (COMMON-3) 예외 및 로깅 공통 모듈 개발
  - [x] 공통 예외 클래스 계층 정의 (src/qmtl/common/errors/exceptions.py)
  - [x] 예외 처리 및 변환 유틸리티 구현 (src/qmtl/common/errors/handlers.py)
  - [x] 로깅 설정 및 표준화 (src/qmtl/common/logging/)
  - [x] 단위 테스트 작성 (tests/unit/common/errors, tests/unit/common/logging)
- [x] (COMMON-4) 유틸리티 공통 모듈 개발
  - [x] 직렬화/역직렬화 유틸리티 구현 (serialization.py)
  - [x] 데이터 유효성 검증 유틸리티 구현 (validation.py)
  - [x] 시간 변환/계산 유틸리티 구현 (time_utils.py)
  - [x] 해시 생성 유틸리티 구현 (hash_utils.py)
  - [x] 단위 테스트 작성 (tests/unit/common/utils)
- [x] (COMMON-5) 환경 설정 공통 모듈 개발
  - [x] 환경 변수 관리 및 설정 로딩 표준화 (src/qmtl/common/config/)
  - [x] Pydantic v2 스타일 환경/설정 모델 정의 (models/config.py)
  - [x] 환경별(dev, prod, test) 설정 분리 및 동적 로딩 지원
  - [x] 단위 테스트 작성 (tests/unit/common/config)

## 2. 핵심 모델 및 데코레이터 개발

### 2.1 데이터 모델 정의
- [x] (MODEL-1) DataNode 및 관련 Pydantic 모델 정의
  - [x] Pydantic BaseModel 기반 DataNode 모델 구현
  - [x] node_id, type, data_format, params, dependencies, ttl 필드 정의
  - [x] 유효성 검증 로직 구현 (model_validator 사용)
  - [x] 단위 테스트 작성
- [x] (MODEL-1.1) 태그 기반 노드 분류 모델 확장
  - [x] NodeTag enum 정의 (기존 NodeType 대체)
  - [x] NodeTags 모델 구현 (predefined, custom 태그 지원)
  - [x] DataNode 모델 확장 (tags 필드 추가)
  - [x] DataNode.primary_tag 속성 추가 (하위 호환성)
  - [x] 단위 테스트 작성
- [x] (MODEL-1.2) 인터벌 및 피리어드 설정 모델 구현
  - [x] IntervalSettings 모델 구현 (interval, period, max_history)
  - [x] DataNode 모델 확장 (interval_settings 필드 추가)
  - [x] 유효성 검증 로직 구현
  - [x] 단위 테스트 작성
- [x] (MODEL-2) Strategy 관련 Pydantic 모델 정의
  - [x] StrategyMetadata, SharedStrategyModel 구현
  - [x] StrategyVersion, ActivationHistory 모델 구현
  - [x] 단위 테스트 작성
- [x] (MODEL-3) API 요청/응답 모델 정의
  - [x] Registry API 요청/응답 모델 구현
  - [x] Orchestrator API 요청/응답 모델 구현
  - [x] 모델 간 일관성 검증 테스트 작성

### 2.2 전략 데코레이터 구현
- [x] (DECOR-1) 기본 데코레이터 설계 및 구현
  - [x] @node 데코레이터 구현
  - [x] @signal 데코레이터 구현
  - [x] key_params 지원 로직 구현
  - [x] 단위 테스트 작성
- [x] (DECOR-2) node_id 생성 메커니즘 구현
  - [x] AST 기반 함수 코드 추출 로직 구현
  - [x] 해시 생성 및 관리 로직 구현
  - [x] 다양한 시나리오에 대한 테스트 작성

## 3. Registry 서비스 개발

### 3.1 Registry 서비스 기본 구조
- [x] (REG-1) Registry 서비스 도메인 중심 모듈 구조 설계
  - [x] services/ 디렉토리 구조 생성 (node/, strategy/, gc/)
  - [x] 각 도메인별 인터페이스 정의
  - [x] FastAPI 애플리케이션 초기화 코드 작성
  - [x] 메모리 구현체 및 DI, 통합 테스트 작성
- [x] (REG-2) Neo4j 데이터 스키마 설계 및 구현
  - [x] DataNode, Strategy, Activation 관련 Cypher 쿼리 작성
  - [x] 초기화 및 마이그레이션 스크립트 작성
  - [x] 인덱스 및 제약 조건 설정

### 3.2 Registry 서비스 핵심 기능 구현
- [x] (REG-3) 노드 관리 서비스 구현
  - [x] 노드 등록 기능 구현 (NodeService.create_node)
  - [x] 노드 조회 기능 구현 (NodeService.get_node)
  - [x] 노드 삭제 기능 구현 (NodeService.delete_node)
  - [x] 노드 목록 조회 기능 구현 (NodeService.list_nodes)
  - [x] Zero-dep 노드 조회 기능 구현 (NodeService.list_zero_deps)
  - [x] 노드 유효성 검증 로직 구현 (NodeService.validate_node)
  - [x] 단위 테스트 및 통합 테스트 작성
- [x] (REG-4) 전략 관리 서비스 구현
  - [x] 전략 버전 등록 기능 구현 (StrategyService.register_version)
  - [x] 전략 버전 조회 기능 구현 (StrategyService.get_version)
  - [x] 전략 목록 조회 기능 구현 (StrategyService.list_strategies)
  - [x] 전략 활성화 기능 구현 (ActivationService.activate_strategy)
  - [x] 전략 비활성화 기능 구현 (ActivationService.deactivate_strategy)
  - [x] 전략 활성화 이력 조회 기능 구현 (ActivationService.get_activation_history)
  - [x] 단위 테스트 및 통합 테스트 작성
- [x] (REG-5) 가비지 컬렉션 서비스 구현
  - [x] TTL 기반 노드 삭제 로직 구현 (GCService.collect_ttl_expired)
  - [x] Zero-dep 노드 삭제 로직 구현 (GCService.collect_zero_deps)
  - [x] GC 데몬 스레드 구현 (gc_daemon.py)
  - [x] 상태 모니터링 기능 구현 (GCService.get_status)
  - [x] 단위 테스트 및 통합 테스트 작성

### 3.3 Registry API 구현
- [x] (REG-6) 노드 관련 API 엔드포인트 구현
  - [x] POST /v1/registry/nodes
  - [x] GET /v1/registry/nodes/{id}
  - [x] DELETE /v1/registry/nodes/{id}
  - [x] GET /v1/registry/nodes:leaf
  - [x] 인터페이스 테스트 작성
- [x] (REG-6.1) 태그 기반 노드 조회 API 구현
  - [x] GET /v1/registry/nodes/by-tags
  - [x] 태그 및 인터벌 필터링 지원
  - [x] 다중 태그 조건 지원 (AND/OR 연산)
  - [x] 인터페이스 테스트 작성
- [x] (REG-7) 전략 관련 API 엔드포인트 구현
  - [x] POST /v1/registry/strategies (삭제 예정)
  - [x] GET /v1/registry/strategies/{version_id}
  - [x] GET /v1/registry/strategies
  - [x] 인터페이스 테스트 작성
- [x] (REG-8) GC 및 상태 관련 API 엔드포인트 구현
  - [x] POST /v1/registry/gc/run
  - [x] GET /v1/registry/status
  - [x] 인터페이스 테스트 작성

## 4. Orchestrator 서비스 개발

### 4.1 Orchestrator 서비스 기본 구조
- [x] (ORCH-1) Orchestrator 서비스 도메인 중심 모듈 구조 설계
  - [x] services/ 디렉토리 구조 생성 (strategy/, execution/)
  - [x] 각 도메인별 인터페이스 정의
  - [x] FastAPI 애플리케이션 초기화 코드 작성
- [x] (ORCH-2) Registry 클라이언트 구현
  - [x] RegistryClient 클래스 구현
  - [x] 노드 등록/조회/삭제 메서드 구현
  - [x] 전략 등록/활성화/비활성화 메서드 구현
  - [x] 단위 테스트 작성

### 4.2 Orchestrator 서비스 핵심 기능 구현
- [x] (ORCH-3) 전략 제출 및 파싱 서비스 구현
  - [x] 전략 코드 파싱 로직 구현 (SubmissionService.parse_strategy)
  - [x] 데코레이터 추출 로직 구현 (SubmissionService.extract_decorators)
  - [x] DataNode DAG 구성 로직 구현 (DAGService.build_dag)
  - [x] 전략 제출 처리 로직 구현 (SubmissionService.submit_strategy)
  - [x] 전략 메타데이터 관리 로직 구현
  - [x] 단위 테스트 및 통합 테스트 작성
- [x] (ORCH-4) 전략 활성화/비활성화 서비스 구현
  - [x] 전략 활성화 로직 구현 (ActivationService.activate_strategy)
  - [x] 누락 노드 처리 로직 구현 (ActivationService.reconcile_nodes)
  - [x] 전략 비활성화 로직 구현 (ActivationService.deactivate_strategy)
  - [x] 환경별 활성화 관리 로직 구현
  - [x] 단위 테스트 및 통합 테스트 작성
- [x] (ORCH-5) 파이프라인 실행 서비스 구현
  - [x] 파이프라인 실행 트리거 로직 구현 (PipelineService.trigger_pipeline)
  - [x] 파이프라인 상태 관리 로직 구현 (StatusService.track_status)
  - [x] 실행 결과 수집 로직 구현 (PipelineService.collect_results)
  - [x] 단위 테스트 및 통합 테스트 작성

### 4.3 Orchestrator API 구현
- [x] (ORCH-6) 전략 관련 API 엔드포인트 구현
  - [x] POST /v1/orchestrator/strategies
  - [x] GET /v1/orchestrator/strategies/{version_id}/dag
  - [x] POST /v1/orchestrator/strategies/{version_id}/activate
  - [x] POST /v1/orchestrator/strategies/{version_id}/deactivate
  - [x] GET /v1/orchestrator/strategies/{version_id}/activation-history
  - [x] GET /v1/orchestrator/strategies
  - [x] 인터페이스 테스트 작성
- [x] (ORCH-7) 파이프라인 관련 API 엔드포인트 구현
  - [x] POST /v1/orchestrator/trigger
  - [x] GET /v1/orchestrator/pipeline/{pipeline_id}/status
  - [x] GET /v1/orchestrator/executions
  - [x] GET /v1/orchestrator/executions/{execution_id}
  - [x] 인터페이스 테스트 작성
- [x] (ORCH-8) 분석기 관련 API 엔드포인트 구현
  - [x] POST /v1/orchestrator/analyzers
  - [x] GET /v1/orchestrator/analyzers/{analyzer_id}
  - [x] POST /v1/orchestrator/analyzers/{analyzer_id}/activate
  - [x] GET /v1/orchestrator/analyzers/{analyzer_id}/results
  - Pydantic v2 모델, 서비스/비즈니스 로직, FastAPI 엔드포인트, 단위/통합 테스트, 문서화, todo/CHANGELOG 반영 완료

## 5. SDK 개발

### 5.1 SDK 기본 구조
- [x] (SDK-1) SDK 모듈 구조 설계
  - [x] src/qmtl/sdk/ 디렉토리 구조 생성
  - [x] Pipeline, Node 클래스 인터페이스 정의
  - [x] SDK 전용 모델 설계

### 5.2 로컬 실행 SDK 구현 (Phase 1)
- [x] (SDK-2) Pipeline, Node 클래스 구현
  - [x] Pipeline 클래스 구현
  - [x] Node 클래스 구현
  - [x] 노드 간 의존성 관리 메커니즘 구현
  - [x] 단위 테스트 작성
- [x] (SDK-2.1) 태그 기반 노드 클래스 구현
  - [x] Node 클래스에 태그 지원 추가 (tags 매개변수)
  - [x] QueryNode 클래스 구현 (태그 기반 노드 쿼리)
  - [x] Analyzer 클래스 구현 (자동 분석기 기본 클래스)
  - [x] 단위 테스트 작성
- [x] (SDK-3) 로컬 실행 메커니즘 구현
  - [x] 토폴로지 정렬 기반 실행 순서 결정 로직 구현
  - [x] 노드 간 데이터 전달 메커니즘 구현
  - [x] 실행 결과 수집 및 반환 로직 구현
  - [x] 단위 테스트 작성
- [x] (SDK-3.1) 태그 기반 쿼리 실행 메커니즘 구현 (Pipeline/Analyzer/QueryNode selector 체이닝 포함)
  - QueryNode의 태그/인터벌/피리어드 기반 노드 필터링 및 selector(중간 API) 체이닝 기능 구현
  - Pipeline, Analyzer, models.py, 단위 테스트, 문서(architecture.md) 반영
  - 기존 test_node_execute_with_key_params 실패는 별도 이슈로 관리 필요
- [x] (SDK-4) 노드 함수 직렬화 및 해시 생성 메커니즘 구현
  - [x] AST 기반 함수 코드 추출 로직 구현
  - [x] key_params 기반 해시 생성 로직 구현
  - [x] 재현 가능한 노드 ID 생성 보장
  - [x] 단위 테스트 작성
- [x] (SDK-5) 병렬 실행 아키텍처 전환 및 Kafka/Redpanda 연동 구현
  - [x] Pipeline.execute() 메서드에 parallel 파라미터 추가 (기본값: False)
  - [x] ParallelExecutionEngine 구현 (Kafka/Redpanda 연동 지원)
  - [x] LocalExecutionEngine 개선 (외부 입력 처리, 예외 처리 등)
  - [x] 병렬/로컬 실행 모드 간 전환 메커니즘 구현
  - [x] interval_settings와 stream_settings 간 상호 호환성 유지
  - [x] 포괄적인 단위 테스트 작성 및 통과

### 5.3 원격 통합 SDK 구현 (Phase 2)
- [x] (SDK-6) OrchestratorClient 확장
  - [x] 전략 제출 메서드 구현
  - [x] 전략 활성화/비활성화 메서드 구현
  - [x] 파이프라인 실행 트리거 메서드 구현
  - [x] 단위 테스트 작성
- [x] (SDK-7) Redis 기반 상태 관리 구현
  - [x] Redis 연결 및 설정 관리 모듈 개발
  - [x] 인터벌별 데이터 저장 및 TTL 관리 로직 구현
  - [x] 히스토리 데이터 조회 최적화
  - [x] 단위 테스트 작성
- [x] (SDK-P3c) 인터벌 데이터 분산 실행 지원: Pipeline.get_history, get_interval_data, get_node_metadata가 로컬/분산 환경 모두에서 일관된 결과를 반환하도록 개선, StateManager/Redis 연동 및 테스트 통과

## 6. 통합 테스트 및 문서화

### 6.1 통합 테스트
- [x] (TEST-1) E2E 테스트 시나리오 구현
  - [x] 전략 제출부터 실행까지 전체 흐름 테스트
  - [x] 다중 전략 및 환경 테스트
  - [x] 오류 상황 및 복구 테스트
- [x] (TEST-1.1) E2E 테스트 "No lowest priority node found" 오류 해결 (2025-05-09 signal node env 동적 할당 및 multi-environment 안정화 포함)
    - [x] 파이프라인 실행 시 노드 우선순위 처리 로직 버그 수정 (2025-05-09)
    - [x] PipelineStatusResponse 모델 및 결과 처리 개선 (2025-05-09)
    - [x] 노드 우선순위 결정 로직에 대한 디버깅 로그 추가 (2025-05-09)
    - [x] test_e2e_full_workflow, test_e2e_multi_strategy_environments 테스트 안정화 (2025-05-09 signal node env 동적 할당 및 multi-environment 안정화 포함)
- [x] (TEST-2) 성능 테스트 구현
  - [x] 대규모 노드 처리 성능 테스트
  - [x] 동시 요청 처리 성능 테스트
  - [x] 메모리 사용량 모니터링 테스트
- [x] (TEST-3) 테스트 자동화 스크립트 구현
  - [x] CI 파이프라인용 테스트 스크립트 작성
  - [x] 테스트 환경 자동 설정 스크립트 작성
- [ ] (TEST-4) 테스트 인프라 업그레이드
  - [x] 테스트 결과를 기반으로 한 리포트 생성 기능 추가 (pytest-html, Makefile 연동, tests/report/README.md)
  - [x] linter warning 정리 (flake8, black, isort, import/style 오류, 나머지 IDE 일괄 처리)

### 6.2 문서화
- [x] (DOC-1) API 문서 자동화 구현
  - [x] OpenAPI 스키마 생성 및 관리
  - [x] API 문서 자동 생성 스크립트 작성
  - [x] docs/generated/api.md 생성 체계 구축 (pytest fixture 기반 자동화, 실제 문서 생성 확인)
- [x] (DOC-2) 사용자 가이드 작성
  - [x] SDK 사용 방법 문서화
  - [x] 전략 작성 가이드 문서화
  - [x] 예제 코드 및 튜토리얼 작성
- [x] (DOC-3) 개발자 가이드 작성
  - [x] 아키텍처 개요 문서화
  - [x] 모듈별 설계 결정 기록
  - [x] 확장 및 기여 가이드 작성
- [x] (DOC-4) 문서 품질 개선 및 보강
  - [x] API 문서(api.md)에 요청/응답 예시 및 필드 설명 추가
  - [x] README.md 보강 (프로젝트 개요, 설치 방법, 핵심 기능 소개)
  - [x] 개발자 가이드에 신규 기능 추가 절차 상세화
  - [x] 아키텍처/워크플로우 설명에 다이어그램 등 시각 자료 추가
  - [x] 버전 관리 정보 및 변경 사항 참조 추가
  - [x] Neo4j/Redis/Redpanda 연결 상세 가이드 작성
  - [x] 주요 용어/개념 색인 또는 검색 키워드 목록 추가
  - [x] E2E 관점의 전체 워크플로우 예제 확장
  - [x] 주요 문서의 다국어(한국어/영어) 버전 제공

## Phase 1 — E2E Orchestrator-Registry 출구 기준

- [ ] 모든 예정된 작업 완료
- [ ] 통합 테스트 통과 (`make ci`)
- [ ] 성능 목표 달성 (specs/perf.md 참조)
- [ ] CHANGELOG 항목 추가 (*Unreleased* 섹션)
- [ ] 문서 업데이트 (roadmap, ADRs, README)

## [SDK 개발] PyTorch 스타일 전략 SDK 구현

### Phase 1: 로컬 실행 SDK 개발
- [x] (SDK-P1a) Pipeline, Node 클래스 설계 및 구현
  - [x] 파이프라인 초기화 및 노드 등록 인터페이스 구현
  - [x] 노드 간 의존성 관리 메커니즘 구현
  - [x] 노드 함수 래핑 및 파라미터 관리 구현
- [x] (SDK-P1b) 로컬 실행 메커니즘 구현
  - [x] 토폴로지 정렬 기반 실행 순서 결정 로직
  - [x] 노드 간 데이터 전달 메커니즘 구현
  - [x] 실행 결과 수집 및 반환 로직
  - [x] 단위 테스트 작성
- [x] (SDK-P1c) Pydantic 모델 정의
  - [x] PipelineDefinition, NodeDefinition 모델 구현
  - [x] 모델 직렬화/역직렬화 기능 구현
  - [x] 기존 스키마와의 호환성 확보
- [x] (SDK-P1d) 인터벌 데이터 관리 기능 구현
  - [x] Pydantic 모델 확장 (IntervalSettings, NodeStreamSettings)
  - [x] Node 클래스에 stream_settings 매개변수 추가
  - [x] 업스트림 노드별 인터벌 설정 정규화 메서드 구현
  - [x] 히스토리 데이터 접근 메서드(get_history) 개발

### Phase 2: 원격 토픽 통합 구현
- [x] (SDK-P2a) Kafka/Redpanda 토픽 자동 생성 로직 (2025-05-09)
  - [x] 파이프라인/노드 기반 토픽 명명 규칙 정의 및 함수 구현
  - [x] 토픽 생성 및 구성 API 래핑 (confluent-kafka AdminClient)
  - [x] 병렬 실행 엔진에서 파이프라인/노드별 토픽 자동 생성 연동
  - [x] 토픽 생성 권한 관리 및 오류 처리 (로깅)
  - [x] 단위 테스트 및 문서화
- [x] (SDK-P2b) OrchestratorClient 확장
  - [x] PipelineDefinition 전송 API 추가
  - [x] 토픽 목록 조회 및 모니터링 API 추가
  - [x] 파이프라인 활성화/비활성화 API 확장
- [x] (SDK-P2c) Redis 기반 상태 관리 구현 (2025-05-09)
  - [x] Redis 연결 및 설정 관리 모듈 개발
  - [x] 인터벌별 데이터 저장 및 TTL 관리 로직 구현
  - [x] 히스토리 데이터 조회 최적화
  - [x] 단위 테스트 작성

### Phase 3: 컨테이너 및 K8s 배포 지원
- [x] (SDK-P3a) 컨테이너 빌드 도구 구현
  - [x] Dockerfile 템플릿 자동 생성
  - [x] 의존성 파일 자동 추출 및 설치
  - [x] 이미지 빌드 및 레지스트리 푸시 유틸리티
- [x] (SDK-P3b) K8s Job 템플릿 및 생성 로직
  - [x] 파이프라인 기반 K8s Job 스펙 생성
  - [x] 환경 변수 및 설정 자동 구성
  - [x] 실행 모니터링 및 로그 수집 연동
- [x] (SDK-P3c) 인터벌 데이터 분산 실행 지원
  - [x] 원격 실행 시 인터벌 설정 전달 메커니즘
  - [x] Kubernetes 환경에서 Redis 연결 설정
  - [x] 다중 컨테이너 간 Redis 데이터 공유 최적화

## 태그 기반 분석 시스템 구현

### 모델 및 API 확장
- [x] (TAG-1) 태그 기반 노드 모델 확장
  - [x] NodeTag enum 및 NodeTags 모델 구현 
  - [x] DataNode 모델에 tags 및 interval_settings 필드 추가
  - [x] type 필드 유지하면서 tags로 점진적 마이그레이션 지원
  - [x] 단위 테스트 작성
- [x] (TAG-2) Registry API 확장
  - [x] 태그 기반 노드 조회 엔드포인트 추가 (/v1/registry/nodes/by-tags)
  - [x] Neo4j 쿼리 최적화 (태그 인덱싱)
  - [x] 태그 필터링 및 인터벌 필터링 지원
  - [x] 단위 테스트 작성
- [x] (TAG-3) Orchestrator API 확장 (2025-05-09)
  - [x] 분석기 제출 및 등록 엔드포인트 추가 (/v1/orchestrator/analyzers)
  - [x] 분석기 활성화 엔드포인트 추가
  - [x] 분석 결과 조회 엔드포인트 추가
  - [x] 단위 테스트 작성
- [x] (TAG-4) 분석기 예제 구현을 통한 태그 기반 분석기 검증 및 테스트 (분석기는 QueryNode 기반 전략 코드임)
  - [x] 상관관계 분석기 (CorrelationAnalyzer) 구현
  - [x] 이상치 감지 분석기 (AnomalyDetector) 구현
  - [x] 성능 모니터링 분석기 (PerformanceMonitor) 구현
  - [x] 통합 테스트 작성

## 멀티 인터벌 데이터 관리

### 데이터 모델 및 인터페이스 확장
- [x] (INTERVAL-1) Pydantic 모델 확장 (2025-05-10)
  - [x] IntervalSettings 모델 구현
  - [x] NodeStreamSettings 모델 구현
  - [x] DataNode/NodeDefinition 모델에 stream_settings 필드 추가 및 interval_settings→stream_settings 마이그레이션 지원
- [x] (INTERVAL-2) Node 클래스 인터페이스 확장
  - [x] Node 생성자에 stream_settings 매개변수 추가
  - [x] 스트림 설정 정규화 메서드 구현
  - [x] 히스토리 데이터 접근 API 설계

### Redis 통합 및 상태 관리
- [x] (INTERVAL-3) Redis 연결 및 데이터 관리 로직 구현
  - [x] Redis 클라이언트 및 연결 관리 모듈 개발 (테스트 자동화 포함)
  - [x] 인터벌별 데이터 저장 구조 설계 (key: node:{node_id}:history:{interval}, 리스트+TTL/ltrim)
  - [x] TTL 및 최대 항목 수 관리 로직 구현 (save_history, get_history, delete_history, ltrim, expire)
- [x] (INTERVAL-4) 히스토리 데이터 접근 API 개발
  - [x] get_history 메서드 구현
  - [x] 인터벌별 데이터 조회 최적화
  - [x] 시간대별 데이터 필터링 기능 구현

### 실행 엔진 통합
- [x] [FIXTURE-1] pytest fixture 구조 개선 및 통합 (2025-05-10 완료)
    - 실제 원인 분석:
        - 외부 리소스 컨테이너/연결 fixture가 function scope 등으로 분리되어 테스트 간 데이터가 공유되지 않거나, 매번 초기화되어 상태가 유지되지 않음
        - 여러 테스트/세션/모듈 scope로 컨테이너를 재시작하거나, flushall 등으로 데이터가 삭제되어 테스트 간 데이터가 공유되지 않음
    - 해결 방법:
        - 외부 리소스 fixture의 scope를 session/module로 통일
        - 테스트와 서비스가 동일한 리소스/환경변수를 사용하도록 강제
        - 테스트 중간에 데이터가 삭제/초기화되는 구간을 명확히 관리
- [x] [FIXTURE-2] neo4j 등 외부 DB 컨테이너/연결 fixture 구조 개선 및 통합 (2025-05-10 완료)
    - 실제 원인 분석:
        - 테스트와 서비스가 서로 다른 DB 인스턴스/포트/DB를 바라보거나, fixture에서 DB를 flush/초기화하여 데이터가 사라지는 현상
        - 컨테이너 네트워크 분리, 환경변수 불일치, DI 문제 등으로 인한 데이터 불일치
    - 해결 방법:
        - DB 컨테이너/연결 fixture의 scope를 session/module로 통일하여 테스트 간 데이터 일관성 유지
        - 환경변수 및 네트워크 설정 일치화
        - 테스트 setup/teardown에서 flush/초기화 정책을 명확히 관리
- [x] [FIXTURE-3] redpanda 등 메시지 브로커 컨테이너/연결 fixture 구조 개선 및 통합 (2025-05-10 완료)
    - 실제 원인 분석:
        - 테스트 컨테이너/프로세스 분리로 인해 서비스와 테스트 코드가 서로 다른 Redis/Redpanda 인스턴스 또는 DB를 바라봄
        - fixture에서 각 테스트/세션/모듈 scope로 컨테이너를 재시작하거나, flushall 등으로 데이터가 삭제되어 테스트 간 데이터가 공유되지 않음
        - 환경변수(REDIS_HOST, REDIS_PORT, REDIS_DB 등) 불일치로 인해 실제 서비스와 테스트가 다른 인스턴스를 바라봄
        - 싱글턴 DI 문제로 set/get이 서로 다른 커넥션을 사용할 수 있음
    - 해결 방법:
        - pytest/서비스/컨테이너 모두 동일한 환경변수(REDIS_HOST, REDIS_PORT, REDIS_DB 등) 사용 강제
        - fixture의 scope(function/module/session) 일관성 유지 및 필요시 session scope로 통일
        - 테스트 setup/teardown에서 flushall, 컨테이너 재시작 등 데이터 삭제/초기화 정책을 명확히 관리
        - docker-compose, pytest, FastAPI 등에서 네트워크/포트/DB 일치 여부 점검
        - 테스트 중간에 Redis/Redpanda에 실제로 저장된 데이터가 유지되는지 직접 확인 및 로깅 추가

**참고**: 
1. 완료된 작업 항목은 개발 가이드라인에 따라 backlog.md로 이동해야 합니다.
2. 각 항목은 GitHub 이슈로 등록하여 관리해야 합니다.
3. Pydantic v2 스타일 가이드라인을 따를 때 BaseModel의 속성과 충돌하는 이름(예: `schema`)은 `data_format`과 같이 변경하고, alias는 사용하지 않는 것이 원칙입니다.

# [NOTE] signal node env 동적 할당 정책 및 전달 경로는 architecture.md/README에 명확히 기술 필요 (2025-05-09)

- [x] [ORCH-STRATEGY-LIST] Orchestrator 활성 전략 목록 API가 환경별 활성화 전략을 반환하도록 구현 (E2E 환경별 전략 분리 검증 통과 목적)
    - 전략 활성화/비활성화 시 환경별로 관리되는 구조 보장
    - /v1/orchestrator/strategies 응답에 각 전략의 environment 필드 포함 및 환경별 필터링/분리 반환
    - E2E test_e2e_multi_strategy_environments의 마지막 검증(환경별 전략 분리) 통과 확인 (※ E2E 환경 상태 저장 개선 필요)
 - [x] [E2E-STATE] Orchestrator 활성 전략 등 상태 저장 방식 개선 (2025-05-11 완료)
    - Redis 기반 환경별 활성 전략 상태 영속화 구현 (ActivationService)
    - 서비스 초기화 시 Redis에서 상태 복구, 활성화/비활성화 시 Redis에 즉시 반영
    - E2E 테스트(test_e2e_multi_strategy_environments)에서 orchestrator 컨테이너 재시작 후에도 활성화 상태가 유지되는지 검증
    - 장애/복구 상황(예: Redis flush, 장애 후 복구)에서 일관성 보장 테스트
    - 관련 구조/정책을 architecture.md, README, tests/README.md, tests/e2e/README.md에 명시
    - todo.md → backlog.md, CHANGELOG.md 반영

# [완료] QMTL 2.0 아키텍처/문서 정비 (분석기/SDK/시각화/알림)
- 분석기는 QueryNode 기반 전략 코드임을 명확히 문서화 (별도 엔티티 아님)
- 시각화/알림은 SDK 공통 기능(Export/포맷 변환)으로 외부 연동 원칙 명시
- send_alert/visualize_result 등 내장 함수 예시/설명 제거
- analyzer_guide.md, sdk_guide.md 등 사용자 가이드 추가
- [x] (INTERVAL-필수) Node/SourceNode/DataNode interval 필수화 및 문서/테스트/역직렬화/예외처리 보완 (2025-05-11)
- [x] interval/period Enum(Int) 기반 리팩토링 및 테스트/문서 반영


## 4. 다중 전략 DAG/노드/파이프라인 공유/생명주기 고도화 (architecture.md 8.4 및 Pipeline ID 정책 연동)

- [x] (MULTI-1) 노드-전략 참조 카운트 및 맵 관리 기능 설계/구현
    - Registry 구현 책임: 파이프라인 실행/종료 시점의 노드-파이프라인(전략) 참조 카운트/맵을 Neo4j에 저장/관리, 참조 카운트 증감/조회/초기화 API 제공, 파이프라인 종료 시 참조 해제 처리
    - Orchestrator 구현 책임: SDK 기반 전략 실행/종료 시 Registry에 참조 카운트 갱신 요청, 전략 제출/종료 시 참조 관계 동기화, 상태 변화 이벤트 감지 및 후속 처리
    - **모든 참조/맵/관계의 key는 반드시 정책 Node ID(32자리 해시)만 사용. 이름/id/순번/객체id/hash 등 금지.**
- [x] (PIPELINE-1) 글로벌 Pipeline ID 정책 적용 및 파이프라인 참조/식별/관계/스냅샷/상태 관리 일원화
    - Registry/Orchestrator/SDK 모든 계층에서 파이프라인 식별자는 반드시 정책 Pipeline ID(32자리 해시)만 사용
    - Pipeline ID는 파이프라인을 결정짓는 요소(구성 노드, 의존성, 파라미터, 설정 등)의 해시로 생성하며, 예시/정의/주의사항은 architecture.md 5.2 참조
    - 파이프라인 등록/조회/실행/스냅샷/롤백/비교/상태/이벤트/맵/관계 등 모든 참조의 key는 Pipeline ID만 허용 (이름/id/순번/객체id/hash 등 금지)
    - Pipeline ID 생성 정책/예시/가이드/테스트/문서화는 architecture.md, nodeID.md, README 등과 일관성 유지
    - 기존 version_id, strategy_id 등 파이프라인 식별/참조/관계/상태/이벤트/맵/스냅샷/API/테스트/문서에서 Pipeline ID로 일괄 대체
    - Pipeline ID 정책 적용 범위 및 예외/주의사항은 todo.md, backlog.md, CHANGELOG.md에 명확히 기록
- [x] (MULTI-2) 노드별 상태/메타데이터 관리 기능 확장
    - Registry 구현 책임: 노드별 상태(대기, 실행, 정지, 에러 등) 및 리소스 사용량/메타데이터를 Neo4j에 저장/관리, 상태 변경 API 제공
    - Orchestrator 구현 책임: 노드 실행/정지/에러 등 상태 변화 발생 시 Registry에 상태 갱신 요청, 상태 변화 이벤트 구독 및 운영 대시보드 연동
    - **상태/메타데이터의 key, 조회/갱신/이벤트 모두 정책 Node ID 기준.**
- [x] (MULTI-3) 전략별 DAG 스냅샷/버전 관리 및 롤백 지원
    - Registry 구현 책임: 전략 제출 시점의 DAG 구조/노드 버전/파라미터 스냅샷을 영구 저장, 롤백/재실행/비교 분석 기능 설계
    - Orchestrator 구현 책임: 전략 제출/활성화/비활성화 시 Registry에 스냅샷 저장/조회/롤백 요청, 실행 시점에 스냅샷 기반 파이프라인 구성
    - **DAG/스냅샷/버전 관리의 노드 식별자는 반드시 정책 Node ID.**
- [x] (MULTI-4) 의존성 기반 동적 스케줄링 및 리소스 최적화 (2025-05-13 완료, backlog.md/CHANGELOG.md 반영)
    - Registry 구현 책임: 전체 DAG 구조, 노드 의존성 정보, 실행 가능 노드 목록 제공 API 구현
    - Orchestrator 구현 책임: Registry에서 DAG/의존성/상태 정보를 조회하여 실행 가능한 노드만 선별 실행, 리소스 상황에 따라 우선순위/스케줄링, 비활성 노드 자동 정지/재시작
    - **DAG/의존성/실행 가능 노드 목록의 모든 노드 참조는 Node ID 기준.**
 - [x] (MULTI-5) 콜백/이벤트 훅 기반 노드 생명주기 관리 (2025-05-13)
    - Registry: 노드 실행/정지 신호 콜백 등록/해제/조회/트리거 API 및 도메인 서비스 구현 (`/v1/registry/nodes/{node_id}/callbacks`)
    - Orchestrator: 콜백 등록/해제 요청, 콜백 이벤트 수신 후 노드 실행/정지 신호 처리 구조 초안
    - Pydantic v2 스타일 콜백 모델(models/callback.py) 정의
    - 단위/통합 테스트 및 FastAPI DI/모킹 구조 검증 (tests/integration/test_callback.py)
    - 정책 Node ID(32자리 해시) 기반 일관성 보장, 문서/가이드/테스트/CHANGELOG/todo.md 반영
- [x] (MULTI-6) 장애 복구 및 데이터 일관성 보장
    - Registry 구현 책임: 노드 장애/에러 상태 기록, 데이터 흐름 정합성 검증, 중복 실행/손실 방지 정책 관리
    - Orchestrator 구현 책임: 장애 감지/자동 복구 로직, 장애 발생 시 Registry에 상태 갱신 및 복구 요청, 장애 알림/로깅/재시도 처리
    - **장애/에러 상태 기록, 데이터 흐름 검증, 중복 실행/손실 방지 정책의 기준이 Node ID.**
- [x] (MULTI-7) 실시간 모니터링/대시보드/알림 시스템 연동 (2025-05-13)
    - Registry: 상태 변화 이벤트 발행/구독 서비스(EventPublisher/EventSubscriber), 실시간 이벤트 API 추가
    - Orchestrator: 이벤트 구독 클라이언트(EventClient) 및 대시보드/알림 연동 샘플 구현
    - Pydantic v2 스타일 이벤트/상태 모델 정의(models/event.py)
    - 단위 테스트 및 모킹 기반 검증(tests/unit/models/test_event.py, tests/unit/registry/services/test_event.py, tests/unit/orchestrator/services/test_event_client.py)
    - FastAPI API 연동(/v1/registry/events/node-status 등)
    - todo.md → backlog.md, CHANGELOG.md 반영
    - Registry 구현 책임: 노드/파이프라인(전략) 상태 실시간 구독/모니터링 API, 상태 변화 이벤트 발행, 메타데이터 제공
    - Orchestrator 구현 책임: 실시간 상태 구독, 대시보드/알림 시스템 연동, 운영자/사용자 알림 트리거
    - **실시간 상태 구독, 이벤트 발행, 메타데이터 제공의 기준이 Node ID.**
- [x] (MULTI-8) 전략/노드 동적 추가/삭제/수정 지원 및 템플릿/권한 관리 등 확장 (2025-05-13)
    - [1차] 템플릿/권한 관리용 Pydantic 모델 정의(models/template.py)
    - [1차] Registry API에 템플릿/권한 관리 엔드포인트 스켈레톤 추가(api.py)
    - [2차] 노드/전략 Partial Update(수정) API 스켈레톤 추가(api.py)
    - [3차] Orchestrator 연동, 서비스/테스트/문서화 예정
    - Registry 구현 책임: 실행 중인 DAG에 전략/노드 동적 반영, 템플릿/재사용성/권한 관리 등 메타데이터 구조/API 제공
    - Orchestrator 구현 책임: 동적 추가/삭제/수정 요청 처리, 템플릿/권한 정책 적용, 실행 중 파이프라인에 실시간 반영
    - **실행 중인 DAG에 노드 추가/삭제/수정, 템플릿/재사용/권한 관리 등도 Node ID로만 구분.**

# (공통) 모든 노드 및 파이프라인 식별/참조/관계/상태/이벤트/맵/스냅샷/API/테스트/문서에서 반드시 정책 Node ID(32자리 해시) 및 Pipeline ID(32자리 해시)만 사용해야 하며, 이름/id/순번/객체id/hash 등은 절대 사용하지 않는다. Node ID 및 Pipeline ID 생성 정책은 architecture.md, nodeID.md, README 등 참조.

## 7. Registry/Orchestrator 역할 명확화 및 구조 보완 태스크

### Registry
- [x] (REG-ROLE-1) 메타데이터(노드/전략/DAG/의존성/이력) 관리 로직 설계 및 구현 (2025-05-13, MetadataService 파사드 구조로 통합, API/테스트/문서 일원화, architecture.md/README.md 반영)
- [ ] (REG-ROLE-2) 참조 카운트, 의존성, 상태(활성/비활성/에러 등) 관리 기능 보강
- [ ] (REG-ROLE-3) Neo4j 기반 엔티티/관계(DEPENDS_ON, CONTAINS, ACTIVATED_BY 등) 설계/테스트
- [ ] (REG-ROLE-4) 가비지 컬렉션(GC), TTL, zero-dep 노드 관리 로직 점검 및 개선
- [ ] (REG-ROLE-5) API/서비스/도메인 계층 구조 일치화 및 문서화
- [ ] (REG-ROLE-6) 단위/통합 테스트 및 커버리지 보강

### Orchestrator
- [ ] (ORCH-ROLE-1) SDK 기반 파이프라인 실행, DAG 실행/상태 관리, 실행 엔진 연동 로직 설계/구현
    - Orchestrator는 SDK에서 정의된 파이프라인(DAG)을 받아 실행하고, 실행 상태를 관리하며, 실행 엔진(Kafka/
    Redpanda 등)과 연동하는 책임만 가짐
- [ ] (ORCH-ROLE-2) Registry 연동 통한 노드/전략 등록 및 관리 로직 보강
- [ ] (ORCH-ROLE-3) 파이프라인 실행 트리거, 상태 추적, 콜백/이벤트 관리 기능 구현
- [ ] (ORCH-ROLE-4) Redis 기반 활성 전략 상태 영속화 및 복구 로직 강화
- [ ] (ORCH-ROLE-5) 장애 감지/복구, 실시간 모니터링, 대시보드/알림 연동 기능 설계/구현
- [ ] (ORCH-ROLE-6) 단위/통합 테스트 및 커버리지 보강

- [x] [ARCH-NODE-ID] 글로벌 Node ID 정책 문서화 및 구현 (2025-05-11 완료, architecture.md/예제/가이드 
반영)
    - 함수 이름(name) 파라미터 제거, 함수 객체 기반 Node ID 생성 정책 확정
    - Node ID는 함수의 __qualname__, 소스코드, 업스트림(__qualname__), stream_settings, key_params 
    등 결정적 요소의 해시로 생성
    - 람다 함수는 소스코드+입력+설정의 해시로 Node ID 생성(객체 id/hash 사용 금지)
    - 클래스 메서드는 __qualname__으로 구분
    - 업스트림은 함수 객체만 지원(문자열/이름 지정 불필요)
    - 사이클(순환 참조)만 없으면 함수 이름 충돌 허용, 사이클 검증은 DAG 생성 시 자동 수행
    - Node ID 생성 정책/예시/주의사항/가이드 등 architecture.md에 상세 문서화
    - 사용자 가이드/예제에 함수 객체 기반 DAG 구성, 클래스 메서드/람다 사용 예시 포함
    - todo.md → backlog.md, CHANGELOG.md 반영 예정

---

## [2025-05-13] validate_node 관련 통합 테스트 실패 이슈 (AttributeError)

- [x] [VALID-1] 통합 테스트에서 mock 서비스(`MockNeo4jNodeManagementService`)에 `validate_node` 메서드가 없어 AttributeError 발생
    - 원인: 실제 서비스 인터페이스(NodeManagementService)에는 `validate_node`가 정의되어 있으나, mock/stub 클래스에는 누락되어 있음
    - 영향: `/v1/registry/nodes` 등 노드 등록 API 테스트에서 실패
    - 조치 필요: mock/stub 서비스에 실제 서비스와 동일한 시그니처의 `validate_node` 메서드 추가 필요

---

# (공통) 모든 노드 식별/참조/관계/상태/이벤트/맵/스냅샷/API/테스트/문서에서 반드시 정책 Node ID(32자리 해시)만 사용해야 하며, 이름/id/순번/객체id/hash 등은 절대 사용하지 않는다. Node ID 생성 정책은 architecture.md, nodeID.md, README 등 참조.

# [2025-05-13] REG-ROLE-2 진행상황 및 DI/Neo4jClient 주입 이슈
- [x] (REG-ROLE-2) 노드 참조 카운트, 의존성, 상태(활성/비활성/에러 등) 관리 기능 서비스/엔드포인트/테스트 반영
    - NodeManagementService/Neo4jNodeManagementService에 의존성 관리 메서드 및 Cypher 쿼리 구현
    - FastAPI API에 의존성 관리(조회/추가/삭제) 엔드포인트 추가
    - 통합 테스트(test_registry.py)에서 의존성 관리 end-to-end 검증 코드 작성
    - register_version(전략 등록) 기능 및 관련 API/테스트/코드 일괄 제거
- [ ] [DI-1] DI/Mock 환경에서 get_neo4j_pool()이 Neo4jClient가 아닌 Neo4jConnectionPool을 주입하여 실제 쿼리 실행 불가 (execute_query 미존재)
    - FastAPI DI/테스트 환경에서 Neo4jClient가 올바르게 주입되도록 구조 점검 및 수정 필요
    - 이슈 해결 후 통합 테스트 정상화 필요
    - 관련 내용 backlog.md, CHANGELOG.md, docs/generated/api.md, README.md에 반영

# [2025-05-15] (ARCH-NEXTGEN) QMTL 차세대 아키텍처 설계 및 문서화
- QMTL을 DAG Manager, Gateway, SDK 세 개의 독립 컴포넌트로 분리 설계
- 모든 데이터 계약, API, 이벤트를 bebop 기반 스키마 관리로 전환
- 모든 외부 API는 bebop contract 모델 기준 조회 전용(read-only)으로 설계, 변이(mutation)는 내부 로직에서만 허용
- Neo4j TAG 인덱싱 설계 및 Cypher 예시 추가
- DAG Manager stateless 설계, durability, idempotency, robust recovery/initialization routines 문서화
- 워크플로우, 콜백, 테스트 코드 예시를 bebop encode/decode 기반으로 변경
- 장애 복구, 캐시 손실, 이벤트/큐 동기화, 트랜잭션 일관성, 복구 방안 등 리스크 및 대응책 추가
- qmtl_architecture_nextgen.md에 모든 설계/예시/정책/코드/워크플로우 반영
- todo.md → backlog.md, CHANGELOG.md 반영 필요
