# QMTL NextGen Migration TODO

이 파일은 기존 프로젝트를 NextGen 아키텍처로 전환하기 위한 주요 작업 항목을 서비스별로 정리한 것입니다.

---

## [공통] 아키텍처/플랫폼 레벨 작업
- [x] [NG-공통-1] 데이터 모델(proto/pydantic) 및 API 계약 우선 확정
      - 목적: 서비스 간 데이터 교환의 일관성, 타입 안전성, 자동 문서화 및 테스트 신뢰도 확보
      - 배경: QMTL 아키텍처는 모든 서비스가 protobuf 기반 contract로만 데이터를 주고받으며, 외부 REST API는 조회(read)만 허용, 내부 조작용 API는 아예 생성하지 않음. **Pydantic 모델은 REST API 관련 request/response 모델에만 사용하며, 내부 데이터 교환 및 비즈니스 로직에는 사용하지 않음**
      - 범위: 각 서비스의 주요 모델(proto/pydantic) 정의, API 스펙 문서화, contract 변경 시 영향도 분석, REST API는 조회용만 설계/구현, **pydantic은 REST API request/response 모델에만 한정하여 사용**
      - 완료 기준: 모든 서비스의 데이터 모델/스키마가 protobuf 기반으로 통일되고, API 계약 문서가 최신화됨. 외부 REST API는 조회(read)만 제공되고, 조작용 API는 없음. **pydantic 모델은 REST API 관련 request/response에만 사용됨**
- [x] [NG-COMMON-1] 데이터 모델 protobuf contract 기반으로 통일
- [x] [NG-COMMON-2] 콜백/이벤트/내부 데이터 교환 protobuf 바이너리 통일
- [x] [NG-COMMON-3] 기존 Pydantic model_dump, model_validate 등 코드 제거
- [ ] [NG-COMMON-4] 문서화 자동화 및 최신화
- [ ] [NG-COMMON-5] 운영/모니터링/알림 연동 설계 및 구현

---

## [DAG Manager]
- [x] [NG-DAG-1] Gateway와의 연동 플로우/통합 테스트: 데이터 교환, API 직렬화/역직렬화, 인증/ACL 검증
- [x] [NG-DAG-2] 핵심 비즈니스 로직(노드/에지/ 관리, 작업 큐 등) 개발 및 리팩토링
- [x] [NG-DAG-3] 내부 단위 테스트 및 E2E 시나리오 작성
- [x] [NG-DAG-4] golden/round-trip/integration 등 모든 테스트를 protobuf 직렬화 기반으로 작성 (완료, 2025-05-20)
    - registry/integration 테스트, enum/interval 변환, in-memory 서비스 전면 protobuf화, API 계층 dict→proto 변환, 검증 통과
- [ ] [NG-DAG-5] 테스트 커버리지 80% 이상 유지
- [x] [NG-DAG-6] golden/round-trip 테스트 템플릿 예시 파일 생성 (tests/templates/)
- [x] [NG-DAG-7] pytest fixtures 및 factory 클래스 문서화
- [x] [NG-DAG-8] Neo4j 인덱스 생성 쿼리 및 마이그레이션 스크립트 작성
    - scripts/neo4j_migration.py: 인덱스/제약조건 자동 생성 스크립트 작성
    - docs/neo4j_index_migration.md: 적용 가이드 문서화
    - src/qmtl/dag_manager/registry/services/node/neo4j_schema.py: 인덱스/제약조건 정의 활용
- [x] [NG-DAG-9] 인덱스 마이그레이션 스크립트 테스트용 데이터 샘플 정의
- [ ] [NG-DAG-10] 서비스 기동 시 인덱스 자동 점검/생성 코드 추가
- [ ] [NG-DAG-11] 인덱스 미존재 시 경고/오류 로깅 및 운영 가이드 문서화
- [ ] [NG-DAG-12] 아키텍처 기반 주요 테스트 흐름에 대한 테스트 시나리오 작성 및 커버리지 강화
    - [ ] [NG-DAG-12-1] 노드 생성/조회/메타데이터/참조 카운트 일관성 검증
    - [ ] [NG-DAG-12-2] 의존성 추가/삭제 및 DAG 구조 일관성 검증
    - [ ] [NG-DAG-12-3] TAG 기반 노드 조회 및 인덱싱 성능 검증
    - [ ] [NG-DAG-12-4] 스트림(토픽) 생성/삭제 및 메타데이터 검증
    - [ ] [NG-DAG-12-5] 이벤트/콜백 발행 및 구독 정상 동작 검증

---

## [SDK]
- [x] [NG-SDK-1] Gateway와의 연동 플로우/통합 테스트: 데이터 교환, API 직렬화/역직렬화, 인증/ACL 검증
      - 목적: SDK와 Gateway 간 실제 데이터 교환 및 직렬화/역직렬화가 정상 동작하는지 검증
      - 배경: SDK는 Gateway와만 직접 통신하며, DAG Manager/DB와 직접 통신하지 않음. 외부 REST API는 조회(read)만 허용, 내부 조작용 REST API는 아예 만들지 않음
      - 재배치 이유: 사용자 전략 실행 결과가 Gateway를 통해서만 DAG Manager로 전달되므로, 데이터 교환 신뢰성 확보가 선행
      - 범위: 전략 제출, 상태 조회, 콜백 등 주요 API 연동, protobuf 직렬화/역직렬화, 인증/ACL 예외 처리, REST API는 조회(read)만 구현
      - 완료 기준: SDK↔Gateway 간 통합 테스트 코드 작성 및 통과, 데이터 포맷/권한 이슈 없음. 외부 REST API는 조회(read)만 제공되고, 조작용 API는 없음
- [x] [NG-SDK-2] 핵심 비즈니스 로직(모델 직렬화, 데이터 변환 등) 개발 및 리팩토링
      - protobuf 기반 직렬화/역직렬화 일원화, Pydantic model_dump 등 제거, 내부 데이터 변환 로직 리팩토링 (2025-05-20 완료)
- [x] [NG-SDK-3] 내부 단위 테스트 및 E2E 시나리오 작성
      - tests/sdk/test_sdk_core.py: SDK 내부 단위 테스트 템플릿 추가
      - tests/e2e/test_sdk_gateway_e2e.py: SDK-Gateway 연동 E2E 테스트 템플릿 추가
      - pytest로 테스트 수집 및 실행 정상 확인 (테스트 코드 실제 구현 필요)
      - 2025-05-20: 1차 템플릿 작업 완료 (실제 테스트 케이스 구현 필요)
      - 2025-05-25: StateManager.clear() 메서드 구현 및 단위 테스트 통과, 관련 AttributeError 해결
- [x] [NG-SDK-4] golden/round-trip/integration 등 모든 테스트를 protobuf 직렬화 기반으로 작성 (2025-05-20 완료)
- [x] [NG-SDK-5] 테스트 커버리지 80% 이상 유지 (2025-05-24 완료)
- [x] [NG-SDK-6] golden/round-trip 테스트 템플릿 예시 파일 생성 (tests/templates/)
- [x] [NG-SDK-7] pytest fixtures 및 factory 클래스 문서화 (2025-05-21 완료, [/tests/TESTING.md](tests/TESTING.md) 참조)
- [ ] [NG-SDK-12] 아키텍처 기반 주요 테스트 흐름에 대한 테스트 시나리오 작성 및 커버리지 강화
    - [ ] [NG-SDK-12-1] 외부 API read-only 보장 테스트 (GET만 허용, 조작 불가 검증)
    - [ ] [NG-SDK-12-2] 내부 조작 엔드포인트 분리 및 ACL/인증 검증
    - [ ] [NG-SDK-12-3] 데이터 모델(Protobuf) 직렬화/역직렬화 round-trip 일관성 검증
    - [ ] [NG-SDK-12-9] 스키마 호환성(Version Sentinel) 검증


---

## [Gateway]
- [x] [NG-GW-1] DAG Manager, SDK와의 연동 플로우/통합 테스트: 데이터 교환, API 직렬화/역직렬화, 인증/ACL 검증 (2025-05-26 완료)
      - 목적: Gateway가 SDK와 DAG Manager 사이에서 데이터 중계/조율 역할을 제대로 수행하는지 검증
      - 배경: Gateway는 모든 데이터 흐름의 중간 계층으로, 데이터 포맷/권한/상태 추적의 일관성이 핵심. 외부 REST API는 조회(read)만 허용, 내부 조작용 REST API는 아예 만들지 않음
      - 재배치 이유: Gateway의 비즈니스 로직 개선보다, 실제 데이터 흐름의 신뢰성 확보가 우선
      - 범위: 전략 실행, 작업 큐 처리, 콜백/이벤트 전달 등 주요 연동 시나리오, protobuf 직렬화/역직렬화, 인증/ACL, REST API는 조회(read)만 구현
      - 완료 기준: Gateway↔SDK, Gateway↔DAG Manager 간 통합 테스트 코드 작성 및 통과, 외부 REST API는 조회(read)만 제공되고, 조작용 API는 없음
      - 완료 내용: Gateway-DAG Manager 간 통합 테스트 구현 (전략 등록, 데이터노드 생성, ACL 검증, 직렬화 일관성)
- [x] [NG-GW-2] Gateway 비즈니스 로직/정책/ACL/인증 개선 및 고도화 (2025-05-30 완료)
      - 목적: Gateway의 정책, 인증, ACL, 라우팅 등 고유 비즈니스 로직을 강화
      - 배경: 데이터 연동 플로우가 정상화된 후, 정책/보안/예외 처리 등 Gateway의 고유 책임을 명확히. 외부 REST API는 조회(read)만 허용, 내부 조작용 REST API는 아예 만들지 않음
      - 재배치 이유: 실제 데이터 흐름이 검증된 후 정책을 구체화해야, 불필요한 중복/오류를 방지
      - 범위: 인증/ACL 미들웨어, 정책 기반 라우팅, 예외 처리, 보안 강화, REST API는 조회(read)만 구현
      - 완료 기준: 정책/ACL/인증 관련 테스트 코드 작성 및 통과, 보안/정책 문서화, 외부 REST API는 조회(read)만 제공되고, 조작용 API는 없음
      - 완료 내용: JWT 인증 미들웨어, ACL 미들웨어, 정책 서비스, 로깅 및 오류 처리 미들웨어 구현, API 엔드포인트 권한 기반 접근 제어 적용, 읽기 전용 API 보장
- [x] [NG-GW-3] 전체 워크플로우 E2E 테스트 및 예외 처리 강화 (2025-06-01 완료)
      - 목적: Gateway 서비스의 전체 워크플로우에 대한 E2E 테스트와 예외 처리 강화
      - 범위: 전체 작업 흐름(인증, 전략 등록, 데이터 노드 관리, 파이프라인 처리) 테스트, 오류 상황 처리, 장애 대응, 프로토콜 검증
      - 완료 내용: 전체 워크플로우 테스트, 예외 처리 테스트, Protobuf 직렬화/역직렬화 라운드트립 테스트 구현, 장애 상황 대응 및 읽기 전용 API 제한 검증
- [x] [NG-GW-4] golden/round-trip/integration 등 모든 테스트를 protobuf 직렬화 기반으로 작성 (2025-06-02 완료)
      - 목적: Gateway 서비스의 모든 테스트를 protobuf 직렬화 기반으로 구현
      - 범위: 전략, 데이터 노드, 파이프라인 등 주요 리소스에 대한 Golden 파일 생성, 라운드트립 테스트, 통합 테스트
      - 완료 내용: Golden 테스트, 라운드트립 테스트, 통합 테스트 모두 protobuf 직렬화 기반으로 구현, 버전 호환성 및 형식 일관성 검증
- [x] [NG-GW-5] 테스트 커버리지 80% 이상 유지 (2025-06-03 완료)
      - 목적: Gateway 서비스의 코드 신뢰성 및 품질 보장
      - 범위: 핵심 비즈니스 로직, 오류 처리, 예외 상황에 대한 테스트 커버리지 확보
      - 완료 내용: 단위 테스트 작성 및 리팩토링을 통해 전체 테스트 커버리지 95% 달성 (acl.py 94%, error.py 91%, policy.py 100%)
- [x] [NG-GW-6] golden/round-trip 테스트 템플릿 예시 파일 생성 (tests/templates/) (2025-06-02 완료)
      - 목적: Gateway 서비스의 테스트 코드 재사용성 및 일관성 유지
      - 범위: Golden 테스트 및 라운드트립 테스트를 위한 템플릿 파일 생성
      - 완료 내용: `gateway_roundtrip_template.py` 및 `gateway_golden_template.py` 템플릿 파일 구현, 재사용 가능한 유틸리티 함수 및 클래스 제공
- [x] [NG-GW-7] pytest fixtures 및 factory 클래스 문서화 (2025-06-02 완료)
      - 목적: Gateway 서비스의 테스트 코드 이해 및 재사용성 향상
      - 범위: Gateway 관련 pytest fixtures, 팩토리 클래스 및 테스트 템플릿 문서화
      - 완료 내용: 테스트 픽스처 및 팩토리 클래스 설명, 사용 예시, 템플릿 활용법 등을 TESTING.md 파일에 문서화

---

## [통합 테스트/운영 환경에서만 검증]
- [ ] [NG-DAG-8] Neo4j 인덱스 생성 쿼리 및 마이그레이션 스크립트 작성 (원래: DAG Manager)
- [ ] [NG-DAG-9] 인덱스 마이그레이션 스크립트 테스트용 데이터 샘플 정의 (원래: DAG Manager)
- [ ] [NG-DAG-10] 서비스 기동 시 인덱스 자동 점검/생성 코드 추가 (원래: DAG Manager)
- [ ] [NG-DAG-11] 인덱스 미존재 시 경고/오류 로깅 및 운영 가이드 문서화 (원래: DAG Manager)
- [ ] [NG-DAG-12-6] 인덱스 자동 점검/생성/마이그레이션 로직 테스트 (원래: DAG Manager)
- [ ] [NG-DAG-12-7] 외부 API read-only 보장 및 내부 조작 ACL/인증 검증 (원래: DAG Manager)
- [ ] [NG-DAG-16] Neo4j 장애 시 fallback(inmemory) 허용 구조로 인해 xfail 처리된 테스트 존재 (원래: DAG Manager)
- [ ] [NG-GW-8] Neo4j 인덱스 생성 쿼리 및 마이그레이션 스크립트 작성 (원래: Gateway, 기존 NG-SDK-8)
- [ ] [NG-GW-9] 인덱스 마이그레이션 스크립트 테스트용 데이터 샘플 정의 (원래: Gateway, 기존 NG-SDK-9)
- [ ] [NG-GW-10] 서비스 기동 시 인덱스 자동 점검/생성 코드 추가 (원래: Gateway, 기존 NG-SDK-10)
- [ ] [NG-GW-11] 인덱스 미존재 시 경고/오류 로깅 및 운영 가이드 문서화 (원래: Gateway, 기존 NG-SDK-11)
    - [ ] [NG-GW-12-4] Neo4j TAG 인덱싱 및 노드/관계 일관성 검증 (원래: Gateway, 기존 NG-SDK-12-4)
    - [ ] [NG-GW-12-5] DAG 구조 및 의존성 관리(노드/에지 추가·삭제, 순환성 등) 검증 (원래: Gateway, 기존 NG-SDK-12-5)
    - [ ] [NG-GW-12-6] 작업 큐(Redis) 내구성/멱등성/복구 시나리오 검증 (원래: Gateway, 기존 NG-SDK-12-6)
    - [ ] [NG-GW-12-7] 서비스 기동 시 복구 루틴(외부 시스템 상태 점검, 미완료 작업/이벤트 복구) 검증 (원래: Gateway, 기존 NG-SDK-12-7)
    - [ ] [NG-GW-12-8] 전체 워크플로우 E2E 시나리오(노드 생성→DAG 연결→작업 큐 처리→상태 추적→결과 조회) 검증 (원래: Gateway, 기존 NG-SDK-12-8)

---

## [Sentinel 연동 및 장애 복구 아키텍처 적용 계획]
- [ ] [NG-SEN-1] Redis Sentinel 환경 구성 및 연결 URI 표준화
    - Redis 기본 설정과 Sentinel 구성 비교, 운영환경 전환시 failover 자동 인식 테스트
- [ ] [NG-SEN-2] 서비스별 Redis 클라이언트에서 Sentinel 연결 지원 코드 적용
    - python-redis, aioredis 등에서 Sentinel 모드 지원, 연결 예외/장애 감지 로직 추가
- [ ] [NG-SEN-3] 장애 발생 시 Sentinel 기반 자동 failover 및 재연결 시나리오 검증
    - 서비스 재기동 없이 장애 감지 및 마스터 재선정 후 정상 처리 검증
- [ ] [NG-SEN-4] Sentinel 장애/복구 테스트 자동화 시나리오 작성 및 운영 가이드 문서화
    - 장애유발 스크립트, failover/복구 로그 검증, 운영자 대응 매뉴얼 작성
- [ ] [NG-SEN-5] 서비스 상태 모니터링 및 알림(Slack/Email 등) 연동
    - Sentinel 상태, failover 이벤트, 서비스 연결 실패 등 실시간 알림 구현
- [ ] [NG-SEN-6] 전체 워크플로우(큐 작업, 상태 추적 등) Sentinel 장애/복구 하에서의 내구성/멱등성/E2E 통합 테스트

---

> 각 서비스별로 연동 플로우/통합 테스트, 내부 로직, 정책 개선, 단위/E2E 테스트 등 단계별로 구분하여 관리하세요.
> 공통 작업은 맨 위에 [공통] 섹션으로 관리하면 됩니다.
요약: 병렬/선행/후행 관계
| 단계 | 주요 이슈(예시) | 병렬 가능 여부 | 선행 조건 |
|------|----------------|---------------|-----------|
| 1 | NG-공통-1 | X | - |
| 2 | NG-DAG-1, NG-SDK-1, NG-GW-1 | O | 1단계 완료 |
| 3 | NG-DAG-2, NG-SDK-2, NG-GW-2 | O | 2단계 완료(또는 병행) |
| 4 | NG-DAG-3~7, NG-SDK-3~7, NG-GW-3~7 | O | 3단계 병행 가능 |
| 5 | NG-DAG-8~15, NG-SDK-8~15, NG-GW-8~15 | O | 3~4단계 병행 가능 |
| 6 | NG-DAG-12, NG-SDK-12, NG-GW-12 | O | 5단계 병행 가능 |

---

## [기타]
- [x] [MULTI-8] 모든 서비스 Python 3.11로 통일 및 orchestrator qmtl==0.1.0 호환성 문제 해결
    - orchestrator.Dockerfile: python:3.10-slim → python:3.11-slim으로 변경
    - registry.Dockerfile: python:3.11-slim으로 이미 변경됨(이전 작업)
    - docker-compose.dev.yml로 전체 서비스 재빌드 및 재기동
    - 모든 컨테이너 정상 기동 및 orchestrator qmtl==0.1.0 의존성 문제 해결됨
    - todo.md → backlog.md, CHANGELOG.md 반영
