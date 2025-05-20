````markdown
### Neo4j DI/테스트 환경 정책 (FIXTURE-REGISTRY-ORCH)

- 서비스/핸들러/DI에서는 반드시 `Neo4jClient` 인스턴스만 주입해야 하며, `Neo4jConnectionPool` 자체를 직접 주입하지 않는다.
- 테스트(mock) 환경에서도 mock pool의 `.client()`가 Neo4jClient와 동일한 인터페이스를 가진 mock client를 반환해야 한다.
- 이 정책을 위반하면 DI-1과 같은 오류(메서드 미존재 등)가 발생할 수 있으므로, fixture/테스트/서비스 코드를 항상 점검한다.
- FIXTURE-REGISTRY-ORCH 정책에 따라, 테스트와 서비스가 항상 동일한 컨테이너/환경변수/포트에 연결됨을 보장한다.
## Registry/Orchestrator Docker fixture 구조 및 테스트 환경 일관성

Registry/Orchestrator 서비스는 Neo4j/Redis/Redpanda와 함께 docker-compose로 일괄 기동/정리되며, `tests/conftest.py`의 `docker_compose_up_down` fixture가 health check로 준비 상태를 보장합니다.
모든 E2E/통합 테스트는 해당 fixture 이후에만 FastAPI TestClient(app) 인스턴스를 생성하도록 구조화되어 있습니다.
환경변수/포트/네트워크 일치, race condition, 연결 실패 등 문제를 원천적으로 차단합니다.
fixture 구조 및 사용법은 tests/README.md, tests/e2e/README.md, 본 파일에 안내되어 있습니다.
# QMTL 개발자 가이드

## 1. 아키텍처 개요
QMTL은 전략 기반 데이터 파이프라인, 분석, 상태 관리, 분산 실행을 지원하는 모듈형 시스템입니다. 주요 구성요소는 Registry, Orchestrator, SDK, 공통 모듈(Neo4j/Redis/Redpanda 연동)로 이루어져 있습니다.

- Registry: 노드/전략/활성화/GC 관리, Neo4j 기반
- Orchestrator: 전략 제출/활성화/파이프라인 실행, 상태 추적, FastAPI 기반
- SDK: 파이프라인/노드/분석기/실행엔진/상태관리, Pydantic v2 모델 일관성
- 공통: DB/메시지/환경설정/유틸리티/로깅/예외 등

### 데이터 흐름
1. 전략 제출 → Orchestrator에서 파싱/등록
2. Registry에 노드/전략 등록 및 활성화
3. 파이프라인 실행 트리거 → 실행엔진(Local/Parallel)
4. 결과/상태/히스토리 관리(Neo4j/Redis)

## 2. 모듈별 설계 결정 및 SoC
- 각 모듈은 단일 책임 원칙(SoC)을 엄격히 준수
- 인터페이스 기반 의존성 관리, Pydantic v2 모델 일관성
- Registry/Orchestrator/SDK/공통 모듈 간 명확한 경계
- 데이터 계층(Neo4j/Redis), 서비스 계층, API 계층 분리
- 모든 모델은 models/ 디렉토리에 정의, BaseModel 내장 속성과 충돌 금지

### 예시: 서비스/데이터/모델 계층 분리
```
src/qmtl/registry/services/node.py   # 서비스 계층
src/qmtl/registry/db/neo4j.py        # 데이터 계층
src/qmtl/models/datanode.py          # Pydantic 모델
```

## 3. 개발/확장/기여 가이드

### 3.1 신규 기능 개발 절차

신규 기능을 개발할 때는 다음 과정을 단계별로 수행해야 합니다:

1. **모델 정의** (src/qmtl/models/)
   - Pydantic v2 스타일의 모델 정의 (BaseModel 상속)
   - 필드 타입, 검증 로직, 기본값 등 정의
   - 모델 간 관계 및 변환 로직 구현

2. **서비스 인터페이스 정의** (src/qmtl/[registry|orchestrator]/services/)
   - 서비스 인터페이스(클래스 또는 프로토콜) 정의
   - 메서드 시그니처, 파라미터, 반환 타입 명시
   - 필요한 의존성 명시적 선언 (DI 패턴)

3. **서비스 구현체 개발**
   - 인터페이스 기반 구현체 개발
   - 비즈니스 로직 구현 및 테스트
   - 외부 의존성(DB, 메시지 큐 등) 통합

4. **데이터 접근 계층 개발** (필요시)
   - Neo4j, Redis 등 저장소 관련 로직 구현
   - 모델 변환 및 쿼리 최적화
   - 트랜잭션 관리 및 오류 처리

5. **API 엔드포인트 추가** (src/qmtl/[registry|orchestrator]/api.py)
   - FastAPI 라우터에 엔드포인트 추가
   - 요청/응답 모델 연결 및 검증
   - 엔드포인트 문서화 (description, tags 등)

6. **테스트 작성**
   - 단위 테스트: 각 컴포넌트별 테스트 (tests/unit/)
   - 통합 테스트: 여러 컴포넌트 연동 테스트 (tests/integration/)
   - E2E 테스트: 전체 시스템 흐름 테스트 (tests/e2e/)

7. **문서화 및 정리**
   - 코드 주석 및 타입 힌트 추가
   - README, 가이드 문서 업데이트
   - CHANGELOG 및 todo.md 업데이트
   - PR 제출 및 리뷰 요청

### 3.2 신규 기능 개발 예시: 새로운 분석기 타입 추가

다음은 새로운 분석기 타입을 추가하는 과정의 예시입니다:

#### 1. 모델 정의
```python
# src/qmtl/models/analyzer.py
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class AnalyzerType(str, Enum):
    CORRELATION = "CORRELATION"
    ANOMALY = "ANOMALY"
    TREND = "TREND"
    CUSTOM = "CUSTOM"  # 새로운 타입 추가

class AnalyzerSettings(BaseModel):
    type: AnalyzerType
    params: Optional[dict] = Field(default_factory=dict)
    target_tags: List[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}
```

#### 2. 서비스 인터페이스 확장
```python
# src/qmtl/orchestrator/services/analyzer/interface.py
from typing import List, Dict, Any
from qmtl.models.analyzer import AnalyzerSettings

class AnalyzerService:
    async def register_analyzer(self, analyzer_id: str, code: str, settings: AnalyzerSettings) -> str:
        """분석기 등록"""
        pass
    
    async def get_analyzer(self, analyzer_id: str) -> Dict[str, Any]:
        """특정 분석기 조회"""
        pass

    async def activate_analyzer(self, analyzer_id: str, environment: str) -> bool:
        """분석기 활성화"""
        pass
    
    # 새로운 메서드 추가
    async def get_analyzer_by_type(self, analyzer_type: str) -> List[Dict[str, Any]]:
        """특정 타입의 분석기 목록 조회"""
        pass
```

#### 3. 서비스 구현체 개발
```python
# src/qmtl/orchestrator/services/analyzer/service.py
from typing import List, Dict, Any
from qmtl.models.analyzer import AnalyzerSettings, AnalyzerType
from qmtl.common.errors import NotFoundError
from qmtl.orchestrator.services.analyzer.interface import AnalyzerService

class AnalyzerServiceImpl(AnalyzerService):
    # 기존 메서드 구현...
    
    async def get_analyzer_by_type(self, analyzer_type: str) -> List[Dict[str, Any]]:
        """특정 타입의 분석기 목록 조회"""
        try:
            # 비즈니스 로직 구현
            analyzers = await self._db.get_analyzers_by_type(analyzer_type)
            return [analyzer.model_dump() for analyzer in analyzers]
        except Exception as e:
            raise NotFoundError(f"Failed to get analyzers by type: {e}")
```

#### 4. API 엔드포인트 추가
```python
# src/qmtl/orchestrator/api.py
from fastapi import APIRouter, Depends, Query
from typing import List
from qmtl.models.api_orchestrator import AnalyzerListResponse
from qmtl.orchestrator.services.analyzer import AnalyzerService, get_analyzer_service

router = APIRouter()

@router.get("/v1/orchestrator/analyzers/by-type/{analyzer_type}", 
            response_model=AnalyzerListResponse,
            summary="Get Analyzers By Type",
            description="특정 타입의 분석기 목록을 조회합니다.")
async def get_analyzers_by_type(
    analyzer_type: str, 
    analyzer_service: AnalyzerService = Depends(get_analyzer_service)
):
    analyzers = await analyzer_service.get_analyzer_by_type(analyzer_type)
    return {"analyzers": analyzers}
```

#### 5. 테스트 작성
```python
# tests/unit/orchestrator/services/analyzer/test_analyzer_service.py
import pytest
from unittest.mock import MagicMock, patch
from qmtl.models.analyzer import AnalyzerType
from qmtl.orchestrator.services.analyzer.service import AnalyzerServiceImpl

@pytest.mark.asyncio
async def test_get_analyzer_by_type():
    # Given
    mock_db = MagicMock()
    mock_db.get_analyzers_by_type.return_value = [...]  # 테스트 데이터
    service = AnalyzerServiceImpl(db=mock_db)
    
    # When
    result = await service.get_analyzer_by_type(AnalyzerType.CUSTOM)
    
    # Then
    assert len(result) > 0
    mock_db.get_analyzers_by_type.assert_called_once_with(AnalyzerType.CUSTOM)
```

### 3.3 개발 시 주의사항

1. **Pydantic 모델 정의 시 주의사항**
   - BaseModel의 내장 속성(`schema`, `model`, `json` 등)과 충돌하는 필드명 사용 금지
   - 충돌 시 다른 이름(`data_schema`, `model_type` 등)으로 대체
   - alias 사용 금지 (필드명 직접 변경)

2. **Neo4j/Redis 연결 시 주의사항**
   - 연결 풀 관리 및 세션 범위 고려
   - 트랜잭션 처리 및 롤백 로직 구현
   - 예외 처리 및 로깅 필수

3. **분산 환경 고려사항**
   - 상태 일관성 보장 메커니즘 구현
   - 레이스 컨디션 및 동시성 이슈 처리
   - 장애 복구 및 재시도 전략 구현

4. **테스트 작성 시 주의사항**
   - 외부 의존성 모킹 또는 실제 컨테이너 사용 결정
   - fixture 스코프 설정 (function, module, session)
   - 데이터 초기화 및 정리 로직 구현

## 4. 테스트/품질/CI 가이드
- 테스트 계층: 단위 → 통합 → E2E 분리, 커버리지 80% 이상 목표
- 모든 API/비즈니스 로직 엣지 케이스 테스트 필수
- pytest fixture로 외부 리소스 컨테이너 관리, 포트 충돌/데이터 일관성 보장
- CI: GitHub Actions, Makefile test/integration-test/e2e-test, pytest-html 리포트 자동화
- linter(black, isort, flake8) 및 코드 스타일 자동화

### 4.1 외부 리소스 연결 가이드

#### Neo4j 연결 설정
```python
from qmtl.common.db.neo4j_client import Neo4jClient
from qmtl.models.config import Neo4jSettings

# 연결 설정
settings = Neo4jSettings(
    uri="bolt://localhost:7687",
    username="neo4j",
    password="password"
)
client = Neo4jClient(settings)

# 세션 사용
async with client.session() as session:
    result = await session.run("MATCH (n) RETURN n LIMIT 5")
    records = await result.records()
```

#### Redis 연결 설정
```python
from qmtl.common.redis.redis_client import RedisClient
from qmtl.models.config import RedisSettings

# 연결 설정
settings = RedisSettings(
    host="localhost",
    port=6379,
    db=0
)
client = RedisClient(settings)

# 데이터 저장/조회
await client.set("key", "value", ex=3600)  # TTL 1시간
value = await client.get("key")
```

#### Redpanda/Kafka 연결 설정
```python
from qmtl.common.kafka.kafka_client import KafkaClient
from qmtl.models.config import KafkaSettings

# 연결 설정
settings = KafkaSettings(
    bootstrap_servers="localhost:9092",
    client_id="qmtl-client"
)
client = KafkaClient(settings)

# 토픽 생성
await client.create_topic("my-topic", partitions=3, replication_factor=1)

# 메시지 생성/소비
await client.produce("my-topic", {"key": "value"})
messages = await client.consume("my-topic", group_id="my-group", timeout=10)
```

## 5. 실전 개발/운영 팁
- Pydantic v2 스타일 강제(import, validator, model_config 등)
- BaseModel 내장 속성과 충돌하는 필드명 사용 금지(예: schema → data_format)
- Redis/Neo4j/Redpanda 컨테이너 환경변수/포트 일치 여부 항상 점검
- 테스트 중간에 컨테이너 재시작/flush 정책 명확히 관리
- 전략/노드/분석기 예제는 docs/user_guide.md, sdk_guide.md, analyzer_guide.md 참고

## 6. 참고 자료/링크
- [아키텍처 문서](../architecture.md)
- [사용자 가이드](./user_guide.md)
- [SDK 가이드](./sdk_guide.md)
- [분석기 가이드](./analyzer_guide.md)
- [API 문서](./generated/api.md)

## [2025-05-18] NG-4: 데이터 교환 정책 변경
- 모든 서비스/테스트/브로커/이벤트/콜백 계층에서 protobuf 메시지(SerializeToString/FromString) 기반 데이터 교환을 표준으로 사용합니다.
- Pydantic/JSON 직렬화는 완전히 제거되었습니다.
- protobuf 메시지 예시, 직렬화/역직렬화 방법, 주요 정책은 tests/README.md 및 예제 코드를 참고하세요.
````