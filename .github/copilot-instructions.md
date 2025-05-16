# Development Cycle Reminder

**Always follow this cycle:**
1.  **Plan:** Refer architecture.md, todo.md, and backlog.md for the task.
    - Purpose: To understand the task and its context before implementation. So that you can minimize the time spent on implementation.(e.g. minimize numbers of tool calls)
2.  **Implement:** Write or modify the code.
3.  **Test:** Add or update tests and ensure they pass.
4.  **Update Docs:** Update relevant documentation (READMEs, ADRs, etc.).
5.  **Update Todo:** Mark the corresponding task as complete in `todo.md` and move completed tasks to `backlog.md` and update `CHANGELOG.md`.

# Architecture Overview

architecture.md 파일을 참조하여 시스템 아키텍처를 이해합니다. 이 문서는 시스템의 주요 구성 요소와 그 상호작용을 설명합니다.

# 기본 개발 가이드
## Soc (Separation of Concerns)
- 각 모듈은 단일 책임 원칙을 준수해야 합니다.
- 각 모듈은 명확한 책임을 가지고 있으며, 다른 모듈과의 의존성을 최소화해야 합니다.
- 모듈 간의 의존성은 인터페이스를 통해 관리해야 합니다.
- 각 모듈은 독립적으로 테스트 가능해야 합니다.
- 모든 모듈은 문서화되어야 하며, 변경 사항은 즉시 반영해야 합니다.
- 작업 중 기존 코드베이스에서 SoC를 위반하는 부분을 발견하면, 해당 부분을 리팩토링하여 SoC를 준수하도록 수정하는 것을 우선시해야 합니다.

# 테스트 개발 가이드

## 테스트 계층 분리
- **단위 테스트**: 개별 함수/클래스 동작 검증, 모킹 활용
- **통합 테스트**: 모듈 간 상호작용 검증, DB/HTTP 연결 포함
- **E2E 테스트**: 전체 워크플로우 검증, 실제 환경과 유사하게 구성

## 테스트 모킹 전략
- HTTP 클라이언트 모킹: 공통 패턴 사용
- Pydantic 모델 기반 응답 팩토리 활용
- Pytest fixture 계층화 및 공유

## 테스트 커버리지 목표
- 코드 커버리지: 최소 80%
- 모든 API 엔드포인트에 대한 통합 테스트 필수
- 주요 비즈니스 로직에 대한 엣지 케이스 테스트 필수


# Pydantic Model Implementation Guidelines

모든 구현에서 다음 지침을 준수해야 합니다:

- 모든 데이터 구조는 **Pydantic 모델**을 통해 정의합니다
- API 엔드포인트는 반드시 **request/response Pydantic 모델**을 사용합니다
 - 내부 로직 모델도 Pydantic 모델을 사용하여 정의합니다.
- Neo4j 드라이버 코드를 포함한 모든 데이터 접근 계층에서 **Pydantic 모델**을 활용합니다
- 새로운 기능 구현 시, 먼저 Pydantic 모델을 정의한 후 비즈니스 로직을 구현합니다
- 모든 Pydantic 모델은 **`models`** 디렉토리에 정의합니다
- 목킹 테스트 시 Pydantic 모델을 활용하여 테스트 신뢰도를 높입니다
- 모든 모델은 `models` 디렉토리에 명확히 구성하여 정의합니다
- 특히 Neo4j 드라이버 관련 코드에서 일관된 Pydantic 모델 사용을 통해 테스트 신뢰도를 높입니다

## BaseModel 속성 충돌 방지

Pydantic BaseModel은 `schema`, `model_dump`, `model_json_schema` 등 내장 속성과 메서드를 가지고 있습니다. 이와 충돌하는 필드명은 사용하지 않아야 합니다:

- **충돌하는 필드명 예시**: `schema`, `model`, `json`, `dict`, `copy`, `parse_obj`, `parse_raw`, `from_orm` 등
- **해결책**: 충돌하는 필드명을 사용하지 말고 더 명확한 이름으로 대체합니다:
  - `schema` → `data_schema` 또는 `schema_definition` 사용
  - `model` → `model_type` 또는 `model_definition` 사용
  - `json` → `json_data` 또는 `json_content` 사용
- **절대 alias 사용하지 않기**: 충돌 해결을 위해 alias 사용 대신 명확한 필드명 사용
- 충돌 확인 방법: 모델 정의 후 발생하는 경고 메시지 주의 깊게 확인

## Pydantic v2 스타일 강제

반드시 Pydantic v2 스타일을 따라야 합니다:

- import 시 **`validator`, `root_validator` 대신 `field_validator`, `model_validator` 사용**
- 유효성 검사기 정의: **`@root_validator(pre=True)`** → **`@model_validator(mode='before')`**
- 필드 검증: **`@validator('field_name', always=True)`** → **`@field_validator('field_name', mode='before')`**
- v2 스타일의 모델 설정: `Config` 클래스 대신 `model_config` 딕셔너리 사용
- 모델 변환 메서드: `dict()` 대신 `model_dump()` 사용, `json()` 대신 `model_dump_json()` 사용

위 가이드라인을 따르지 않을 경우 DeprecationWarning이 발생하며, 향후 코드 리팩토링이 필요할 수 있습니다.

이 지침을 따르면 다음과 같은 이점이 있습니다:
- 런타임 오류 감소 및 타입 안전성 확보
- 테스트 용이성 및 신뢰성 향상
- 자동화된 문서화 및 스키마 검증
- API 계층과 데이터 접근 계층 간의 일관성 유지

# Dependency Management Guideline

- 프로젝트의 모든 패키지 설치 및 의존성 관리는 반드시 uv(uv pip, uv venv 등)를 사용한다.
- pyproject.toml에 필요한 패키지를 추가한 뒤, 설치가 필요할 때는 uv 명령어로 진행한다.

# Docker Port 충돌 방지
- Default port 사용이 기본이고, 포트 충돌 시 컨테이너를 재시작하여 해결한다.
- 재시작은 pytest fixture를 통해 테스트 과정에서 컨테이너를 지우고 다시 시작하는 걸 보장하는 방식으로 작업을 진행한다.
- 포트 충돌이 발생할 경우, pytest fixture를 통해 컨테이너를 지우고 다시 시작하는 방식으로 해결한다.