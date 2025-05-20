# QMTL NextGen Migration TODO

이 파일은 기존 프로젝트를 NextGen 아키텍처로 전환하기 위한 주요 작업 항목을 이슈 번호와 함께 정리한 것입니다.

---

## [NG-1] 3대 서비스 분리 및 디렉토리 구조 개편
- [ ] QMTL DAG Manager, Gateway, SDK를 독립 서비스로 분리
- [ ] 각 서비스별 Dockerfile, 의존성, 실행 환경 분리
- **세부 계획:**
  - [ ] [NG-1-1] 기존 src/qmtl/ 내 코드 분석 및 서비스별 책임 분류
  - [ ] [NG-1-2] src/qmtl/dag_manager, src/qmtl/gateway, src/qmtl/sdk 디렉토리 구조 확정 및 이전
  - [ ] [NG-1-3] 각 서비스별 requirements/pyproject.toml 분리
  - [ ] [NG-1-4] 각 서비스별 Dockerfile 작성 및 빌드 테스트
  - [ ] [NG-1-5] 서비스별 독립 실행/테스트 환경 구축

## [NG-2] 데이터 모델 protobuf contract 기반으로 통일
- [ ] 기존 Pydantic/JSON 모델 제거 및 protobuf 스키마 설계
- [ ] 모든 데이터 구조, API, 큐, 브로커, 테스트 등에서 protobuf 직렬화/역직렬화 사용
- **세부 계획:**
  - [ ] [NG-2-1] 기존 models/ 내 Pydantic 모델 목록화 및 protobuf로 변환 대상 선정
  - [ ] [NG-2-2] protobuf .proto 스키마 설계 및 버전 관리 체계 도입
  - [ ] [NG-2-2-1] protobuf 스키마 필드 정의(필수/선택 필드, 타입 제약) 문서화  
  - [ ] [NG-2-2-2] protobuf 스키마 버전 관리(major/minor) 및 변경 이력 관리 가이드 작성
  - [ ] [NG-2-3] protobuf 코드 생성 자동화 스크립트 작성 (Makefile/generate script)
  - [ ] [NG-2-4] 기존 코드에서 Pydantic 모델 사용처를 protobuf 기반으로 일괄 치환
  - [ ] [NG-2-5] protobuf 기반 테스트(golden/round-trip) 작성

## [NG-3] 외부 API read-only화 및 내부 조작 분리
- [ ] 외부 API는 조회(GET)만 허용, 생성/수정/삭제는 내부 서비스에서만 처리
- [ ] API 명세 및 엔드포인트 리팩토링
- **세부 계획:**
  - [ ] [NG-3-1] 기존 API 엔드포인트 목록화 및 read/write 구분
  - [ ] [NG-3-2] 외부 노출 API는 GET만 허용하도록 FastAPI/Flask 등 라우팅 수정
  - [ ] [NG-3-2-1] FastAPI/Flask 라우터 설정 예시 코드 스니펫 작성 (dependencies, ACL 포함)
  - [ ] [NG-3-2-2] 인증/ACL 미들웨어 적용 플로우 다이어그램 추가
  - [ ] [NG-3-3] 내부 서비스 간 조작용 엔드포인트 분리 및 인증/ACL 적용
  - [ ] [NG-3-4] API 문서/스펙 최신화

## [NG-4] 콜백/이벤트/내부 데이터 교환 protobuf 바이너리 통일
- [ ] 콜백, 이벤트, 내부 큐, 브로커, 테스트 등에서 protobuf SerializeToString/FromString 사용
- **세부 계획:**
  - [ ] [NG-4-1] 콜백/이벤트/큐/브로커 데이터 구조 protobuf로 통일
  - [ ] [NG-4-2] 기존 json 기반 통신 코드 일괄 치환
  - [ ] [NG-4-3] 테스트 코드(golden/round-trip)에서 protobuf 직렬화 검증

## [NG-5] 테스트 코드 전면 리팩토링
- [ ] golden/round-trip/integration 등 모든 테스트를 protobuf 직렬화 기반으로 작성
- **세부 계획:**
  - [ ] [NG-5-1] 기존 unit/integration/e2e 테스트에서 Pydantic/json 기반 검증 제거
  - [ ] [NG-5-2] protobuf 기반 round-trip/golden test 템플릿 작성 및 적용
  - [ ] [NG-5-3] 테스트 커버리지 80% 이상 유지
  - [ ] [NG-5-4] golden/round-trip 테스트 템플릿 예시 파일 생성 (tests/templates/)
  - [ ] [NG-5-5] pytest fixtures 및 factory 클래스 문서화

## [NG-6] Neo4j TAG 인덱싱 및 마이그레이션 적용
- [ ] QueryNode의 TAG 기반 조회 성능을 위해 Neo4j 인덱스 생성 및 초기화 코드 반영
- **세부 계획:**
  - [ ] [NG-6-1] Neo4j 인덱스 생성 쿼리 및 마이그레이션 스크립트 작성
  - [ ] [NG-6-1-1] 인덱스 마이그레이션 스크립트 위치: scripts/migrations/neo4j_index_migration.py
  - [ ] [NG-6-1-2] 마이그레이션 스크립트 테스트용 데이터 샘플 정의
  - [ ] [NG-6-2] 서비스 기동 시 인덱스 자동 점검/생성 코드 추가
  - [ ] [NG-6-3] 인덱스 미존재 시 경고/오류 로깅 및 운영 가이드 문서화

## [NG-7] 서비스 stateless화 및 외부 DB/브로커 일원화
- [ ] 모든 상태/메타데이터는 Neo4j, Kafka, Redis 등 외부 시스템에만 저장
- [ ] 서비스 자체는 stateless하게 설계
- **세부 계획:**
  - [ ] [NG-7-1] 서비스 내 임시/로컬 상태 저장 코드 제거
  - [ ] [NG-7-2] 외부 DB/브로커 연동 일원화 및 장애 복구 시나리오 점검
  - [ ] [NG-7-3] 서비스 재기동/스케일아웃 테스트

## [NG-8] Redis 작업 큐 내구성/멱등성/복구 루틴 구현
- [ ] Redis durability 옵션(AOF/RDB) 활성화
- [ ] 미처리 작업 자동 복구, 중복 실행 방지, 상태 기반 알림/모니터링 연동
- **세부 계획:**
  - [ ] [NG-8-1] Redis 설정(AOF/RDB) 적용 및 운영 정책 문서화
  - [ ] [NG-8-2] 작업 큐 push/pop/complete 멱등성 보장 로직 구현
  - [ ] [NG-8-3] 미처리 작업 복구 루틴 및 상태 기반 알림 연동
  - [ ] [NG-8-4] 장애/재기동 시 데이터 유실/중복 실행 방지 테스트

## [NG-9] 서비스 기동 시 복구 루틴 구현
- [ ] DAG Manager, Gateway, SDK 서비스 기동 시 인덱스/토픽/큐/미완료 작업/이벤트 재처리 등 복구 루틴 구현
- **세부 계획:**
  - [ ] [NG-9-1] 서비스별 boot/initialize_and_recover 함수 설계 및 구현
  - [ ] [NG-9-2] Neo4j/Kafka/Redis 등 외부 시스템 상태 점검 코드 추가
  - [ ] [NG-9-3] 미완료 작업/이벤트 재처리 및 운영자 알림 연동

## [NG-10] 문서화 자동화 및 최신화
- [ ] protobuf 스키마 → json schema/OpenAPI 문서 자동 생성 파이프라인 구축
- [ ] CHANGELOG, README, 개발가이드 등 문서 최신화
- **세부 계획:**
  - [ ] [NG-10-1] protobuf → json schema/OpenAPI 변환 스크립트 작성
  - [ ] [NG-10-2] 문서 자동화 파이프라인(CI/CD) 구축
  - [ ] [NG-10-3] 주요 변경점 CHANGELOG, README, 개발가이드 반영

## [NG-11] 기존 Pydantic model_dump, model_validate 등 코드 제거
- [ ] 기존 Python 모델 패키지 방식 완전 대체
- **세부 계획:**
  - [ ] [NG-11-1] model_dump/model_validate/model_json_schema 등 호출부 일괄 검색 및 제거
  - [ ] [NG-11-2] Pydantic 의존성 pyproject.toml/requirements.txt에서 제거

## [NG-12] 운영/모니터링/알림 연동 설계 및 구현
- [ ] 장애/재기동/작업 실패 등 주요 이벤트 실시간 알림 연동
- **세부 계획:**
  - [ ] [NG-12-1] 장애/재기동/작업 실패 이벤트 정의 및 로그 표준화
  - [ ] [NG-12-2] Slack/Email/대시보드 등 알림 연동 구현
  - [ ] [NG-12-3] 운영자 가이드 및 모니터링 대시보드 문서화

---

> 각 이슈는 세부 Task로 분해하여 진행하며, 완료 시 backlog.md로 이동합니다.
