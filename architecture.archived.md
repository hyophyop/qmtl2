## Redis 히스토리 데이터 구조 및 TTL/최대 항목수 관리 (INTERVAL-3)

- 노드별/인터벌별 히스토리 데이터는 `node:{node_id}:history:{interval}` 패턴의 Redis 리스트로 저장
- 데이터 추가 시 lpush, ltrim(max_items), expire(TTL) 조합으로 관리
- TTL은 인터벌/period/설정값에 따라 동적으로 부여, max_items는 NodeStreamSettings 등에서 제어
- 삭제는 delete(key), 조회는 lrange(key, 0, count-1)
- 단위 테스트에서 실제 Redis 컨테이너 기반으로 데이터 저장/만료/최대 개수 보장 검증
## Redis 클라이언트 및 테스트 전략 (INTERVAL-3)

- `src/qmtl/common/redis/redis_client.py`에 Pydantic v2 기반 환경설정 연동 싱글턴 RedisClient 구현
- `src/qmtl/models/config.py`에 공식 RedisSettings 모델 정의, 서비스/테스트에서 일관 사용
- 테스트는 `tests/conftest.py`의 docker-compose 기반 Redis 컨테이너 fixture로 신뢰성 보장
- 단위 테스트(`tests/unit/common/redis/test_redis_client.py`)에서 실제 Redis 연결/입출력/예외 처리/싱글턴 리셋 등 실환경과 동일하게 검증
- CI 및 로컬 환경 모두에서 일관된 Redis 상태 관리 및 테스트 자동화 구조 확립
# QMTL 2.0 아키텍처 설계 문서

**문서 버전**: 1.1  
**최종 수정일**: 2025-05-05  
**작성자**: AI 설계 지원 시스템

## 0. 프로젝트 디렉토리 및 개발 환경 표준

- src/qmtl/ 하위에 모든 서비스/공통 모듈/모델/도메인 계층을 구성한다.
- pyproject.toml로 의존성 및 빌드/테스트/포맷팅 도구를 관리한다(uv 사용 권장).
- Makefile로 lint, test, build, run, docker 등 개발 명령을 표준화한다.
- .gitignore, .editorconfig로 코드 스타일과 불필요 파일을 관리한다.
- tests/ 하위에 unit, integration, e2e 계층별 테스트 디렉토리를 분리한다.
- 샘플 단위 테스트 파일을 포함해 pytest, Pydantic v2 스타일 테스트가 기본이다.

## 테스트 프레임워크 및 컨테이너 관리 전략
- tests/unit, tests/integration, tests/e2e 계층별 디렉토리 분리
- tests/conftest.py에서 pytest fixture로 docker-compose 컨테이너를 자동 기동/정리(포트 충돌 방지)
- E2E 테스트는 서비스 기동 대기(health check, 최대 30초 재시도) 후 워크플로우 검증
- 모든 API 엔드포인트 및 주요 비즈니스 로직에 대한 테스트 필수, 커버리지 80% 이상 목표
- Makefile test, integration-test, e2e-test, coverage 명령으로 테스트 일관성 보장

## 1. 개요

### 1.1 비전 및 목표

QMTL(Quantitative Machine Trading Library)은 "전략이 DataNode DAG를 선언하면 플랫폼이 파이프라인 라이프사이클을 관리한다"는 비전을 실현하기 위한 시스템입니다. 주요 목표는 다음과 같습니다:

- 전략 개발자가 쉽게 데이터 파이프라인을 구성하고 관리할 수 있는 환경 제공
- 데이터 노드의 라이프사이클 자동 관리 (생성, 등록, 실행, 가비지 컬렉션)
- 확장 가능하고 안정적인 분산 실행 환경 지원
- 테스트, 검증, 배포 프로세스 자동화
- 다양한 백엔드 시스템과의 통합 지원
- 태그 기반 노드 분류 및 자동 분석기 지원

### 1.2 시스템 구성 요소

QMTL은 다음과 같은 주요 구성 요소로 이루어져 있습니다:

1. **Registry**: 데이터 노드와 전략 메타데이터를 저장하고 관리하는 서비스
2. **Orchestrator**: 전략 코드를 파싱하고 실행을 조율하는 서비스
3. **SDK**: 전략 개발자를 위한 파이썬 클라이언트 라이브러리
4. **Execution Engine**: 파이프라인 실행 엔진(Kafka/Redpanda)
5. **Common Modules**: 여러 서비스에서 공통으로 사용하는 기능 모듈

## 2. 아키텍처 개요

### 2.1 시스템 아키텍처

```
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│  QMTL SDK     │       │ Orchestrator  │       │   Registry    │
│ (클라이언트)   ├──────▶│   Service     │◀──────▶│   Service     │
└───────┬───────┘       └───────┬───────┘       └───────┬───────┘
        │                       │                       │
        │                       ▼                       │
        │               ┌───────────────┐               │
        └──────────────▶│  Execution    │◀──────────────┘
                        │   Engine      │
                        └───────────────┘
```

### 2.2 데이터 흐름

1. **로컬 전략 개발**: SDK를 사용하여 개발자 환경에서 전략을 개발하고 테스트합니다.
2. **전략 컨테이너화**: 검증된 전략은 Docker 컨테이너로 패키징됩니다.
3. **컨테이너 배포**: 전략 컨테이너는 배포 환경에 등록됩니다.
4. **노드 등록**: 컨테이너에서 추출된 DataNode는 Registry에 등록됩니다.
5. **전략 활성화**: 전략이 활성화되면 Orchestrator가 실행 엔진에 파이프라인을 배포합니다.
6. **실행 및 모니터링**: 실행 엔진에서 파이프라인이 실행되고 결과가 모니터링됩니다.
7. **가비지 컬렉션**: 더 이상 필요하지 않은 데이터 노드는 Registry에서 자동으로 제거됩니다.

## 3. 주요 컴포넌트 상세 설계

### 3.1 Registry 서비스 (역할 명확화)

Registry는 QMTL 시스템의 **중앙 메타데이터 저장소**로서, 다음과 같은 역할을 담당합니다:

#### 주요 기능 및 구조 (Registry)
- DataNode, Strategy, DAG 구조, 의존성, 활성화 이력 등 메타데이터의 등록/조회/삭제/관리
- 전략 버전 관리, 활성화/비활성화 상태 추적, 가비지 컬렉션(GC), 노드 상태 모니터링
- 참조 카운트, 의존성, 상태(활성/비활성/에러 등) 관리
- Neo4j 그래프DB 기반으로 노드 간 관계(DEPENDS_ON, CONTAINS, ACTIVATED_BY 등) 저장
- TTL, zero-dep 노드 관리 등 데이터 수명주기 관리

##### 디렉토리 구조 예시
```
src/qmtl/registry/
    api.py                  # FastAPI 엔드포인트 정의
    config.py               # 설정 관리
    utils.py                # 유틸리티 함수
    gc.py                   # 가비지 컬렉션 엔진
    services/
        node/               # 노드 관리 서비스
            management.py   # 노드 생성, 조회, 삭제
            validation.py   # 노드 유효성 검증
        strategy/           # 전략 관리 서비스
            management.py   # 전략 등록, 버전 관리
            activation.py   # 전략 활성화/비활성화
        gc/                 # 가비지 컬렉션 서비스
            service.py      # GC 로직
```

##### 데이터 저장소 구조
- **엔티티**: DataNode, StrategyVersion, ActivationHistory
- **관계**: DEPENDS_ON, CONTAINS, ACTIVATED_BY

---

### 3.2 Orchestrator 서비스 (역할 명확화)

Orchestrator는 QMTL 시스템의 **실행/오케스트레이션 엔진**으로서, 다음과 같은 역할을 담당합니다:

#### 주요 기능 및 구조 (Orchestrator)
- 전략 코드 파싱 및 컨테이너화, DAG 추출 및 파이프라인 실행 트리거
- Registry와의 통신을 통한 노드/전략 등록 및 관리
- 전략 활성화/비활성화, 파이프라인 실행/정지, 상태 추적, 콜백/이벤트 관리
- 활성 전략 상태는 환경별로 Redis에 영속화(컨테이너/프로세스 재시작 시 일관성 보장)
- 장애 감지/복구, 실시간 모니터링, 대시보드/알림 연동 등 운영 기능

##### 디렉토리 구조 예시
```
src/qmtl/orchestrator/
    api.py                  # FastAPI 엔드포인트 정의
    config.py               # 설정 관리
    utils.py                # 유틸리티 함수
    services/
        strategy/
            container.py    # 컨테이너 관리 및 DAG 추출
            activation.py   # 전략 활성화/비활성화
            dag.py          # DAG 구성 및 분석
        execution/
            pipeline.py     # 파이프라인 실행
            status.py       # 상태 관리
```

##### 상태/운영 데이터 저장소
- **활성 전략 상태**: Redis 기반 환경별 영속화(복구/장애 대응)
- **실행 상태/결과**: Orchestrator 내부 또는 외부 모니터링 시스템과 연동 가능

---

## 4. API 설계

### 4.1 Registry API

| 엔드포인트 | 메서드 | 설명 |
|----------|-------|------|
| `/v1/registry/nodes` | POST | 새 노드 등록 |
| `/v1/registry/nodes/{id}` | GET | 노드 메타데이터 조회 |
| `/v1/registry/nodes/{id}` | DELETE | 노드 삭제 |
| `/v1/registry/nodes:leaf` | GET | 의존성 없는 노드 조회 |
| `/v1/registry/strategies` | POST | 새 전략 버전 등록 |
| `/v1/registry/strategies/{version_id}` | GET | 전략 버전 조회 |
| `/v1/registry/strategies/{version_id}/activate` | POST | 전략 버전 활성화 |
| `/v1/registry/strategies/{version_id}/deactivate` | POST | 전략 버전 비활성화 |
| `/v1/registry/strategies` | GET | 활성 전략 목록 조회 |
| `/v1/registry/strategies/{version_id}/activation-history` | GET | 전략 활성화 이력 조회 |
| `/v1/registry/gc/run` | POST | 가비지 컬렉션 실행 |
| `/v1/registry/status` | GET | 시스템 상태 조회 |

### 4.2 Orchestrator API

| 엔드포인트 | 메서드 | 설명 |
|----------|-------|------|
| `/v1/orchestrator/containers` | POST | 전략 컨테이너 등록 |
| `/v1/orchestrator/containers/{container_id}/nodes` | GET | 컨테이너에서 추출된 DataNode DAG 조회 |
| `/v1/orchestrator/strategies/{version_id}/dag` | GET | 전략 버전의 DAG 조회 |
| `/v1/orchestrator/strategies` | GET | 전략 목록 조회 |
| `/v1/orchestrator/trigger` | POST | 파이프라인 실행 트리거 |
| `/v1/orchestrator/pipeline/{pipeline_id}/status` | GET | 파이프라인 상태 조회 |
| `/v1/orchestrator/executions` | GET | 실행 이력 조회 |
| `/v1/orchestrator/executions/{execution_id}` | GET | 실행 상세 정보 조회 |

## 5. 데이터 모델 및 엔티티/필드 흐름 (Orchestrator ↔ Registry)

### 5.1 DataNode 모델

```python
class NodeTag(str, Enum):
    """Enumeration for predefined node tags"""
    RAW = "RAW"
    CANDLE = "CANDLE"
    FEATURE = "FEATURE"
    ORDERBOOK = "ORDERBOOK"
    RISK = "RISK"
    SIGNAL = "SIGNAL"
    ML_PRED = "ML_PRED"
    ANALYZER = "ANALYZER"
    CORRELATION = "CORRELATION"
    VOLATILITY = "VOLATILITY"
    TREND = "TREND"
    ANOMALY = "ANOMALY"

class NodeTags(BaseModel):
    """Node tags model with support for custom tags"""
    predefined: Optional[List[NodeTag]] = Field(default_factory=list)
    custom: Optional[List[str]] = Field(default_factory=list)

class IntervalSettings(BaseModel):
    """Settings for data interval management"""
    interval: str = Field(default="1d")
    period: Optional[str] = Field(default=None)
    max_history: Optional[int] = Field(default=None)

class DataNode(BaseModel):
    node_id: str = Field(..., pattern=r"^[a-f0-9]{32}$")
    type: Optional[NodeType] = None  # 하위 호환성 유지
    tags: Optional[NodeTags] = Field(default_factory=NodeTags)
    data_format: Dict[str, Any] = Field(...)
    params: Optional[Dict[str, Any]] = None
    dependencies: List[str] = Field(default_factory=list)
    ttl: Optional[int] = None
    interval_settings: Optional[IntervalSettings] = None
```


### 5.2 파이프라인(Pipeline) 식별 및 데이터 흐름 정책

#### [핵심 정책: Pipeline ID]
- QMTL 시스템에서 파이프라인(전략)은 **Pipeline ID**로 글로벌하게 유일하게 식별됩니다.
- Pipeline ID는 파이프라인의 클래스명/함수명, 소스코드, 노드 목록, 노드 간 의존성, 파라미터, stream_settings 등 결정적 정보를 직렬화하여 해시(32자리 hex)로 생성합니다.
- 파이프라인 코드/구성/입력/설정이 동일하면 언제 어디서나 동일 Pipeline ID가 생성되며, 다르면 Pipeline ID도 달라집니다.
- Registry, Orchestrator, SDK, 테스트 등 모든 계층에서 Pipeline ID를 기준으로 파이프라인을 등록/조회/실행/스냅샷/롤백/비교합니다.

#### [Pipeline ID 생성 예시 코드]
```python
import inspect, ast, hashlib, json

def generate_pipeline_id(pipeline_cls, nodes, edges, params, stream_settings):
    try:
        source = inspect.getsource(pipeline_cls)
        source = inspect.cleandoc(source)
        tree = ast.parse(source)
        cls_ast = ast.dump(tree, annotate_fields=True, include_attributes=False)
    except Exception:
        cls_ast = str(pipeline_cls)
    node_ids = [n.node_id for n in nodes]
    signature_dict = {
        "qualname": pipeline_cls.__qualname__,
        "ast": cls_ast,
        "nodes": node_ids,
        "edges": edges,
        "params": params,
        "stream_settings": stream_settings,
    }
    signature_str = json.dumps(signature_dict, sort_keys=True)
    return hashlib.md5(signature_str.encode("utf-8")).hexdigest()
```

#### [파이프라인 데이터 흐름 및 API 설계]
- 파이프라인 등록/조회/실행/스냅샷/롤백 등 모든 기능에서 Pipeline ID를 기준으로 동작합니다.
- Registry/Orchestrator/SDK/테스트 등 모든 계층에서 Pipeline ID를 일관되게 사용해야 하며, 이름/id/순번/객체id/hash 등은 금지합니다.
- 파이프라인의 버전/변경 이력 관리도 Pipeline ID 기반으로 추적합니다.

#### [Pydantic 모델 예시]
```python
class PipelineSnapshot(BaseModel):
    pipeline_id: str  # 정책 Pipeline ID(32자리 해시)
    created_at: int
    nodes: List[NodeSnapshot]
    edges: List[Dict[str, str]]  # {source, target}
    metadata: Optional[Dict[str, Any]]
```

#### [API 계약 예시]
| 엔드포인트 | 입력 | 출력 |
|-----------|------|------|
| /v1/registry/pipelines/{pipeline_id}/snapshots (POST) | PipelineSnapshot | PipelineSnapshotResponse |
| /v1/registry/pipelines/{pipeline_id}/snapshots (GET) | - | List[PipelineSnapshot] |
| /v1/registry/pipelines/{pipeline_id}/rollback (POST) | snapshot_id | PipelineSnapshot |

#### [설계 원칙 보완]
- Pipeline ID는 파이프라인의 결정적 정보 기반 해시로 생성하며, 시스템 전체에서 유일성과 일관성을 보장합니다.
- Registry, Orchestrator, SDK, 테스트 등 모든 계층에서 Pipeline ID만을 기준으로 파이프라인을 식별/참조/비교/스냅샷/롤백/이력 관리합니다.
- 기존 version_id, strategy_id 등은 더 이상 사용하지 않으며, 관련 필드/로직/문서는 모두 Pipeline ID 정책으로 대체합니다.

### 5.3 실행 관련 모델

```python
class ExecutionDetails(BaseModel):
    execution_id: str
    strategy_id: str
    status: ExecutionStatus
    start_time: Optional[Union[datetime, str]] = None
    end_time: Optional[Union[datetime, str]] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    results: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None

class NodeExecutionStatus(BaseModel):
    node_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
```

### 5.4 인터벌 데이터 관리 모델

```python
class IntervalSettings(BaseModel):
    period: str = Field(default="1h")
    max_items: Optional[int] = Field(default=None)
    
class NodeStreamSettings(BaseModel):
    intervals: Dict[str, IntervalSettings] = Field(default_factory=dict)
    
class NodeDefinition(BaseModel):
    # 기존 필드
    stream_settings: Dict[str, NodeStreamSettings] = Field(default_factory=dict)
```

## 6. SDK 설계

### 6.1 PyTorch 스타일 SDK 인터페이스

```python
from qmtl.sdk.pipeline import Pipeline, Node, QueryNode, Analyzer

# 일반 전략 파이프라인 예시
class MyStrategy(Pipeline):
    def __init__(self, symbol: str):
        super().__init__(name="MyStrategy", symbol=symbol)
        
        # RAW 데이터 노드
        self.add_node(
            Node("raw_data", 
                 tags=["RAW"], 
                 fn=self._fetch_data,
                 key_params=["symbol"])
        )
        
        # 특성 엔지니어링 노드
        self.add_node(
            Node("features", 
                 tags=["FEATURE"], 
                 fn=self._calculate_features,
                 upstreams=["raw_data"])
        )
        
        # 신호 생성 노드
        self.add_node(
            Node("signal", 
                 tags=["SIGNAL"], 
                 fn=self._generate_signal,
                 upstreams=["features"],
                 interval_settings=IntervalSettings(
                     interval="1d", 
                     period="14d"
                 ))
        )
    
    def _fetch_data(self, symbol):
        # 데이터 가져오기 로직
        pass
        
    def _calculate_features(self, raw_data):
        # 특성 계산 로직
        pass
        
    def _generate_signal(self, features):
        # 신호 생성 로직
        # 인터벌 히스토리 데이터 접근
        history = self.get_history("features", interval="1d", count=10)
        pass

# 태그 기반 자동 분석기 예시
class CorrelationAnalyzer(Analyzer):
    def __init__(self):
        super().__init__(name="feature_correlation")
        
        # 타겟 태그와 인터벌로 노드 쿼리 정의
        feature_nodes = self.add_query_node(
            QueryNode(
                name="feature_inputs",
                tags=["FEATURE"],
                interval="1d",
                period="14d"
            )
        )
        
        # 분석 결과 노드 정의
        self.add_node(
            Node(
                name="correlation_matrix",
                tags=["ANALYZER", "CORRELATION"],
                fn=self._calculate_correlation,
                upstreams=[feature_nodes]
            )
        )
    
    def _calculate_correlation(self, feature_data_dict):
        """모든 feature 노드 간의 상관관계 계산"""
        import pandas as pd
        
        # 각 feature 노드의 데이터를 하나의 DataFrame으로 병합
        all_data = pd.DataFrame()
        for node_id, data in feature_data_dict.items():
            all_data[node_id] = data['value']
        
        # 상관관계 계산
        correlation_matrix = all_data.corr()
        
        return {
            "correlation_matrix": correlation_matrix.to_dict(),
            "feature_count": len(feature_data_dict),
            "period": "14d"
        }
```

### 6.2 로컬 실행 및 컨테이너화

```python
# 일반 전략 로컬 실행
strategy = MyStrategy(symbol="AAPL")
results = strategy.execute(local=True)

# 전략 컨테이너화 및 배포
strategy = MyStrategy(symbol="AAPL")
container_id = strategy.containerize(
    name="my-strategy",
    version="1.0.0",
    description="My first trading strategy"
)

# 컨테이너화된 전략 활성화
client = OrchestratorClient()
client.activate_container(container_id, mode="LIVE")

# 분석기 컨테이너화 및 활성화
analyzer = CorrelationAnalyzer()
analyzer_container_id = analyzer.containerize(
    name="feature-correlation",
    version="1.0.0"
)
client.activate_container(analyzer_container_id, mode="LIVE")
```

## 7. 배포 아키텍처

### 7.1 개발 환경

```yaml
# docker-compose.dev.yml
version: '3'

services:
  neo4j:
    image: neo4j:5
    environment:
      - NEO4J_AUTH=neo4j/password
    ports:
      - "7474:7474"
      - "7687:7687"
    volumes:
      - neo4j_data:/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  redpanda:
    image: redpandadata/redpanda:latest
    ports:
      - "9092:9092"
      - "19092:19092"
    environment:
      - REDPANDA_RPC_SERVER_LISTEN_ADDR=0.0.0.0
      - REDPANDA_SEED_SERVERS=redpanda:33145

  registry:
    build:
      context: .
      dockerfile: registry.Dockerfile
    depends_on:
      - neo4j
      - redis
    environment:
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=password
      - REDIS_URI=redis://redis:6379
    ports:
      - "8000:8000"

  orchestrator:
    build:
      context: .
      dockerfile: orchestrator.Dockerfile
    depends_on:
      - registry
      - redpanda
    environment:
      - REGISTRY_URI=http://registry:8000
      - REDPANDA_BROKERS=redpanda:9092
      - REDIS_URI=redis://redis:6379
    ports:
      - "8080:8080"

volumes:
  neo4j_data:
```

### 7.2 프로덕션 아키텍처

프로덕션 환경에서는 다음과 같은 구성으로 배포합니다:

- **Registry**: Neo4j 클러스터를 백엔드로 사용하는 K8s Deployment
- **Orchestrator**: HPA(Horizontal Pod Autoscaler)를 통한 자동 스케일링을 지원하는 K8s Deployment
- **Redis**: 고가용성 Redis 클러스터
- **Kafka/Redpanda**: 분산 메시징 시스템

## 8. 개발 로드맵 및 리팩터링 TODO (2025-05-09 설계 보완)

개발은 다음과 같은 단계로 진행됩니다:

### 8.1 현재 단계 (Phase 1 - 스켈레톤)

- Registry 및 Orchestrator 서비스 기본 구현
- Neo4j 기반 데이터 노드 저장소 구현
- 전략 코드 파싱 및 DAG 추출 기능 구현
- 기본적인 활성화/비활성화 기능 구현
- 공통 모듈 추출 및 표준화

### 8.1.1 (2025-05-09) 설계/구현 리팩터링 TODO
- [ ] Orchestrator와 Registry 간 version_id, strategy_id, strategy_code 등 엔티티/필드 정의 및 데이터 흐름 일치화
- [ ] StrategyRegisterRequest, StrategyVersion 등 Pydantic 모델 구조/필드/타입 일관성 보장
- [ ] API/서비스/도메인/테스트 계층에서 동일한 필드명/타입/값 사용 보장
- [ ] 기존 코드 내 version_id, strategy_id, strategy_code 혼재 구간 전수 점검 및 리팩터링
- [ ] 테스트(E2E/통합/단위)에서 실제 서비스와 동일한 데이터 흐름/값 사용 보장

### 8.2 다음 단계 (Phase 2 - Orchestrator Core)

- 전략 코드에서 DataNode 목록 및 DAG 차이 분석
- 빌드/드롭 스케줄러 구현
- 파이프라인 실행 메커니즘 개선
- 다중 전략 지원 기능 강화

### 8.3 향후 단계

- DataNode SDK + DSL 개발 (Phase 3)
- Kafka Adapter 구현 (Phase 4)
- 신호 라우터 및 ML 서빙 구현 (Phase 5)
- CI/CD 및 모니터링 구현 (Phase 6)

## 9. 설계 원칙

QMTL 프로젝트는 다음과 같은 설계 원칙을 따릅니다:

1. **도메인 중심 모듈화**: 기술적 관점이 아닌 비즈니스 도메인에 따른 모듈 분리
2. **인터페이스 추상화**: 각 서비스에 대한 명확한 인터페이스 정의로 테스트 용이성 향상
3. **Pydantic 일관성**: 모든 데이터 구조를 Pydantic 모델로 정의하여 타입 안전성 확보
4. **관심사 분리**: API 레이어와 비즈니스 로직 레이어의 명확한 분리
5. **테스트 용이성**: 모든 컴포넌트는 독립적으로 테스트 가능하도록 설계
6. **코드 재사용**: 공통 모듈을 통한 코드 중복 최소화
7. **확장성**: 새로운 기능을 쉽게 추가할 수 있는 모듈식 설계
8. **Pydantic v2 스타일**: 모든 모델에 Pydantic v2 스타일 적용

## 10. 결론

QMTL은 현대적인 아키텍처 원칙과 패턴을 적용한 전략 파이프라인 관리 시스템입니다. 도메인 중심 모듈화, 인터페이스 추상화, Pydantic 모델 활용 등을 통해 유지보수성, 확장성, 테스트 용이성을 높였습니다.

이 설계 문서는 QMTL 프로젝트의 아키텍처와 구현 방향을 제시하며, 향후 개발 과정에서 세부 사항은 변경될 수 있습니다.

## 11. 태그 기반 분석 시스템

### 11.1 개요

태그 기반 분석 시스템은 NodeType을 확장하여 더 유연한 노드 분류와 자동 분석을 지원합니다. 주요 개념은 다음과 같습니다:

1. **NodeTag vs NodeType**: 
   - NodeType은 고정된 Enum으로 제한된 유형만 지원
   - NodeTag는 미리 정의된 태그와 사용자 정의 태그를 모두 지원
   
2. **다중 태그 지원**:
   - 하나의 노드에 여러 태그 적용 가능
   - 더 세밀한 노드 분류 및 검색 지원

3. **태그 기반 쿼리**:
   - 특정 태그를 가진 노드들을 자동으로 찾아 처리
   - 인터벌/피리어드 설정과 결합하여 데이터 분석 자동화

### 11.2 자동 분석기

자동 분석기는 태그 기반 쿼리를 통해 시스템 내 노드들을 자동으로 분석하는 특별한 형태의 파이프라인입니다. 주요 구조는 다음과 같습니다:

1. **QueryNode**: 
   - 직접적인 업스트림 노드 참조 대신 태그 기반 쿼리 사용
   - 런타임에 조건에 맞는 실제 노드들이 자동 매핑됨 (find_nodes_by_query)

2. **Analyzer 클래스**:
   - 전략 작성과 유사한 PyTorch 스타일 API 제공
   - 태그 기반 QueryNode 매핑 및 실행 로직을 SoC 원칙에 따라 분리
   - 분석 결과는 AnalyzerResult(Pydantic 모델) 및 results_cache/analyzer_results로 일관 저장
   - selector(중간 API) 체이닝을 통한 결과 가공 지원
   - 정기 실행/모니터링 훅 및 상태 저장 구조 내장

3. **사용 사례**:
   - 모든 Feature 노드의 상관관계 분석
   - 특정 태그 노드들의 성능 모니터링
   - 이상 감지 및 경고 시스템

### 11.4 구현 계획

1. **Phase 1: 모델 확장**
   - NodeType → NodeTag 전환 (하위 호환성 유지)
   - NodeTags 및 IntervalSettings 모델 구현
   - DataNode 모델 확장

2. **Phase 2: SDK 확장**
   - QueryNode 및 Analyzer 클래스 구현
   - 태그 기반 쿼리 처리 로직 개발
   - 인터벌/피리어드 관리와 통합

3. **Phase 3: 분석 파이프라인 통합**
   - 분석 결과 저장 및 조회 API 개발
   - 시각화 및 모니터링 도구 연동
   - 알림 시스템 통합

태그 기반 분석 시스템은 기존 전략 개발 환경과 완벽하게 통합되며, 개발자는 동일한 SDK를 사용하여 전략과 분석기를 모두 개발할 수 있습니다.

## 12. 병렬 실행 아키텍처

QMTL 2.0은 기본적으로 병렬 실행을 지원하며, 이는 시스템의 핵심 설계 원칙 중 하나입니다.

### 12.1 병렬 실행 모델

각 노드는 병렬적으로 독립 실행되는 독립적인 처리 단위입니다:

1. **독립적인 실행 환경**:
   - 각 노드는 자체 Kafka/Redpanda 스트림을 가짐
   - 각 노드는 자체 Redis 메모리 저장소를 사용
   - 노드 간 직접 함수 호출이 아닌 메시지 기반 통신

2. **이벤트 기반 실행**:
   - 노드는 업스트림 노드의 출력이 준비되는 즉시 실행
   - 의존성 없는 노드는 완전히 병렬로 실행
   - 다운스트림 노드는 필요한 모든 입력이 준비되면 즉시 실행

3. **메시지 브로커 기반 통신**:
   - 노드 간 통신은 Kafka/Redpanda 토픽을 통해 이루어짐
   - 각 노드는 고유한 입력/출력 토픽을 가짐
   - 토픽 기반 구독 모델로 느슨한 결합 구현

### 12.2 병렬 실행 엔진

SDK 내에서 병렬 실행을 지원하는 핵심 구성 요소:

1. **ParallelExecutionEngine**: 
   - 파이프라인 노드의 병렬 실행 조율
   - 노드-토픽 매핑 관리
   - 의존성 기반 실행 순서 보장
   - 실행 결과 수집 및 관리

2. **StreamProcessor**:
   - Kafka/Redpanda 연결 관리
   - 메시지 발행 및 구독 처리
   - 직렬화/역직렬화 자동화

3. **StateManager**:
   - Redis 기반 상태 및 히스토리 관리
   - 노드 실행 결과의 인터벌별 저장
   - 히스토리 데이터 조회 API 제공

### 12.3 구현 특징

병렬 실행은 QMTL 2.0의 유일한 실행 모드입니다:

1. **데이터 흐름**:
   - 업스트림 노드는 출력을 메시지 브로커에 발행
   - 다운스트림 노드는 필요한 토픽을 구독
   - 의존성 DAG는 토픽 구독 패턴으로 변환

2. **백그라운드 실행**:
   - 컨텍스트 매니저를 통한 백그라운드 실행 지원
   - 비동기 실행 모니터링 및 결과 수집
   - 명시적 종료 또는 타임아웃 기반 실행 제어

3. **확장성**:
   - 단일 머신에서 분산 클러스터까지 동일한 모델 적용
   - 노드별 독립 스케일링 가능
   - 장애 복구 및 재시도 메커니즘 내장

## 13. QueryNode 결과 가공/선택(Selector) 아키텍처

### 13.1 개요

QueryNode는 태그, interval, period 등 조건에 맞는 여러 노드의 출력 스트림(토픽) 리스트를 반환합니다. Downstream 노드는 이 리스트를 입력으로 받아 처리할 수 있습니다. 이때, 단순히 전체 리스트를 받는 것뿐만 아니라, 다양한 방식(배치, 샘플링, 메타데이터 기반 필터 등)으로 입력을 가공/선택할 수 있도록 중간 API(Selector)를 제공합니다.

### 13.2 Selector(중간 API) 설계

- QueryNode는 쿼리 조건만 담당하며, 결과 가공/선택은 별도의 Selector를 통해 처리합니다.
- Selector는 downstream 노드 또는 전략 파일에서 QueryNode 결과에 적용할 수 있습니다.
- 주요 Selector 모드 예시:
    - list: 전체 노드 리스트 반환(기본)
    - batch: n개씩 묶어서 반환
    - random: m개 랜덤 샘플 반환
    - filter: 메타데이터(예: interval, period, tags 등) 기반 추가 필터링

#### Pydantic 모델 예시 (src/qmtl/sdk/models.py)

```python
class QueryNodeResultSelector(BaseModel):
    mode: Literal["list", "batch", "random", "filter"] = "list"
    batch_size: Optional[int] = None
    sample_size: Optional[int] = None
    filter_meta: Optional[Dict[str, Any]] = None
```

#### 전략 파일 사용 예시

```python
qnode = QueryNode(name="q1", tags=["FEATURE"])

# downstream에서 selector 적용
selected_streams = apply_selector(
    query_result=pipeline.find_nodes_by_query(qnode),
    mode="batch",
    batch_size=2
)
# downstream 노드에 selected_streams를 입력으로 사용
```

### 13.3 장점 및 설계 원칙

- QueryNode와 Selector의 역할 분리(SoC)
- 전략 파일에서 데이터 흐름을 명확하게 제어 가능
- 다양한 입력 가공 방식 지원으로 확장성 및 재사용성 향상
- 테스트 및 유지보수 용이

### 13.4 향후 확장 방향

- Selector의 모드 및 옵션 확장(예: 시간 윈도우, 조건부 집계 등)
- 전략/분석기에서 selector 조합 활용 사례 문서화
- SDK 및 Orchestrator에서 selector 지원 API 제공

### 13.5 Selector 체이닝(Chaining) 지원

- Selector는 단일 객체뿐 아니라 리스트(List[Selector])로도 지정할 수 있으며, 여러 개의 selector를 순차적으로(체이닝) 적용할 수 있습니다.
- 각 selector는 입력 리스트를 받아 가공 후 반환하며, 다음 selector가 그 결과를 입력으로 받습니다.
- apply_selectors(query_result, selectors: List[Selector])와 같이 구현하여, filter → batch → random 등 다양한 조합으로 결과를 가공할 수 있습니다.

#### 체이닝 예시

```python
selectors = [
    QueryNodeResultSelector(mode="filter", filter_meta={"interval": "1d"}),
    QueryNodeResultSelector(mode="batch", batch_size=3),
    QueryNodeResultSelector(mode="random", sample_size=1)
]
selected_streams = pipeline.apply_selectors(query_result, selectors)
```

- 위 예시에서 filter → batch → random 순으로 결과가 가공됩니다.
- 이 구조는 확장성과 유연성을 모두 보장하며, 전략 파일/분석기에서 다양한 데이터 흐름 제어가 가능합니다.

## 8. SDK 기반 K8s Job 템플릿 자동 생성 기능

- SDK는 파이프라인(PipelineDefinition) 객체로부터 쿠버네티스 Job YAML을 자동 생성하는 기능을 제공한다.
- K8sJobGenerator 클래스는 파이프라인 이름, 컨테이너 이미지, 환경 변수, 리소스, 명령어 등을 입력받아 JobSpec을 생성한다.
- JobSpec은 Pydantic v2 모델(models/k8s.py)로 정의되어 있으며, model_dump_yaml() 메서드로 YAML 변환이 가능하다.
- 환경 변수(예: Redis, Kafka, Registry 등)는 자동으로 주입되며, 커스텀 값도 지원한다.
- 생성된 Job YAML은 kubectl, Argo, Airflow 등 외부 오케스트레이션 도구와 연동 가능하다.
- 단위 테스트(test_k8s.py) 및 문서화(README)로 신뢰성 검증 및 예제 제공.

## 시각화 및 알림 기능의 위치

- **시각화 및 알림 기능은 QMTL SDK의 내장 기능이 아닙니다.**
    - QMTL은 데이터/분석 결과(값)만 생성하며, 시각화 및 알림은 외부 플랫폼(예: Grafana, Prometheus Alertmanager 등)에서 처리하는 것이 원칙입니다.
    - QMTL SDK는 결과를 외부 시스템과 연동하기 위한 포맷 변환(예: to_grafana_format) 또는 export 유틸리티만 선택적으로 제공합니다.
    - 분석기(Analyzer) 코드에서는 시각화/알림을 직접 호출하지 않으며, 결과를 저장/반환하는 것에 집중합니다.
    - 시각화/알림 연동 예시는 사용자 가이드/예제 문서에서 별도로 안내합니다.

## 시각화 및 알림 기능 활용 예시 (외부 연동)

- QMTL은 분석 결과를 반환/저장만 하며, 시각화 및 알림은 외부 플랫폼에서 처리합니다.
- 분석기(Analyzer) 코드에서의 활용법은 [사용자 가이드](docs/analyzer_guide.md) 및 예제 코드에서 확인할 수 있습니다.

### 예시: 분석기 코드에서 결과 반환 (시각화/알림 없음)

```python
from qmtl.sdk import QueryNode

class MyCorrelationAnalyzer(QueryNode):
    def run(self, inputs):
        # ...분석 로직...
        result = self.calculate_correlation(inputs)
        # 시각화/알림은 호출하지 않음
        return result
```

- 위 예시처럼, 분석기 코드에서는 결과만 반환/저장하며, 시각화/알림은 외부 시스템에서 처리합니다.
- 일반 전략 코드도 동일하게 적용됩니다.

### 참고

- 시각화/알림 연동 및 활용법은 [SDK 사용자 가이드](sdk_guide.md)와 외부 플랫폼 연동 예제를 참고하세요.

## 분석기(Analyzer) 아키텍처

- **분석기는 QueryNode 기반 전략 코드의 한 형태**입니다.
    - 별도의 엔티티나 서비스가 아니라, QueryNode/AnalyzerNode를 활용한 전략 코드로 구현합니다.
    - 분석기용 추상 클래스/헬퍼/데코레이터 등은 SDK에서 선택적으로 제공하며, 일반 전략 코드와 구조적으로 동일한 방식으로 작성·등록·실행·테스트가 가능합니다.
    - 분석기 코드에서는 시각화/알림 등 외부 연동 기능을 직접 호출하지 않으며, 결과 반환/저장에 집중합니다.

# [INTERVAL-6] 원격 실행 엔진 확장 아키텍처 보강
# - 분산 실행 엔진(ParallelExecutionEngine)에서 각 노드의 stream_settings/interval_settings를 포함한 임시 파이프라인 객체를 생성하여 전달
# - 분산 환경에서 Redis 기반 히스토리 데이터 공유 및 TTL/최대 항목수 관리 최적화
# - Orchestrator → ExecutionEngine → Redis 간 데이터 흐름 및 상태 일관성 보장
# - 관련 단위/통합 테스트 및 문서화 완료 (2025-05-10)

### [중요 정책] 인터벌/피리어드 및 노드 구조

QMTL 파이프라인의 데이터 일관성, 타입 안전성, 예측 가능한 동작을 보장하기 위한 핵심 규칙입니다.

#### 1. Interval/Period/Stream Settings 기본 정책
- 모든 ProcessingNode/SourceNode는 최소 1개 이상의 interval(예: DAY, HOUR 등) 설정이 필요하다.
- interval 설정은 반드시 Pydantic Enum(IntervalEnum)과 IntervalSettings(period: int)로 구성되어야 한다.
- period는 int 타입으로, None/빈값/문자열 등은 허용하지 않는다.
- stream_settings가 없는 경우, 파이프라인의 default_intervals가 자동으로 적용된다.
- stream_settings와 default_intervals 모두 없는 경우, 노드 추가 시 ValueError가 발생한다.

#### 2. default_intervals 적용 및 오버라이드
- Pipeline/Analyzer 생성 시 default_intervals를 지정할 수 있다.
- 노드의 stream_settings에 없는 interval/period는 default_intervals로 보완된다.
- 노드에 period가 명시되어 있으면 default_intervals의 period를 오버라이드한다.
- default_intervals와 노드의 intervals를 합쳐, 모든 interval에 대해 period가 반드시 존재해야 한다.

#### 3. 예외 처리 정책
- stream_settings/intervals가 1개도 없으면 노드 추가 시 ValueError 발생
- period가 없는 interval이 있으면 노드 추가 시 ValueError 발생
- NodeStreamSettings(intervals={})와 같이 빈 dict는 생성 시점에서 ValidationError 발생 (Pydantic min_items=1)
- period=None 등은 IntervalSettings 생성 시점에서 ValidationError 발생 (Pydantic int 타입 강제)

#### 4. 테스트/코드 일관성
- 모든 테스트/비즈니스 로직에서 Enum, int 타입, 예외 처리 정책을 일관되게 적용한다.
- stream_settings=None, default_intervals={}인 경우 예외가 발생하는지 테스트로 검증한다.
- period가 어디에도 없을 때도 예외가 발생하는지 테스트로 검증한다.

#### 예시
```python
from qmtl.sdk.models import IntervalSettings, NodeStreamSettings, IntervalEnum
from qmtl.sdk.pipeline import Pipeline, ProcessingNode

default_intervals = {
    IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=14),
    IntervalEnum.HOUR: IntervalSettings(interval=IntervalEnum.HOUR, period=7),
}
pipeline = Pipeline(name="my_pipeline", default_intervals=default_intervals)

node1 = ProcessingNode(
    fn=lambda x: x,
    upstreams=[...],
    stream_settings=NodeStreamSettings(intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)})
)
pipeline.add_node(node1)
assert node1.stream_settings.intervals[IntervalEnum.DAY].period == 14  # default_intervals 적용

node2 = ProcessingNode(
    fn=lambda x: x,
    upstreams=[...],
    stream_settings=NodeStreamSettings(intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=30)})
)
pipeline.add_node(node2)
assert node2.stream_settings.intervals[IntervalEnum.DAY].period == 30  # 오버라이드
```

### 8.4 다중 전략 DAG/노드 공유/생명주기 고도화 (제안)

#### 8.4.1 개요
- 여러 전략이 동시에 제출될 때, 모든 전략의 노드와 의존성을 통합하여 하나의 커다란 DAG(Directed Acyclic Graph)로 관리
- 동일한 노드(이름, 인터벌, 업스트림 식별자 조합)는 단일 인스턴스로만 실행/관리하며, 여러 전략에서 참조 가능
- 각 노드의 실행/정지 신호는 콜백(Event Hook)으로 관리하며, 참조 중인 전략이 하나라도 남아 있으면 노드는 계속 실행됨
- 노드-전략 참조 관계, 노드 생명주기, 콜백 등록/실행, 업스트림 스트림 공유 등은 Registry/Orchestrator에서 통합 관리

#### 8.4.2 주요 기능
- 노드-전략 참조 카운트 및 맵 관리
- 노드별 상태(대기, 실행, 정지, 에러 등) 및 메타데이터 관리
- 전략별 DAG 스냅샷/버전 관리 및 롤백 지원
    - **[구현 정책]**
        - 전략 제출/변경 시점의 전체 DAG(노드/의존성/파라미터/설정 등)를 스냅샷으로 영구 저장
        - 스냅샷은 Neo4j의 `StrategySnapshot` 노드로 관리하며, `nodes`, `edges`, `metadata`는 JSON 직렬화하여 속성에 저장
        - 각 스냅샷은 `version_id`, `created_at`(timestamp)로 고유 식별, `SNAPSHOT_OF` 관계로 StrategyVersion과 연결
        - API: `/v1/registry/strategies/{version_id}/snapshots` (POST/GET), `/v1/registry/strategies/{version_id}/rollback` (POST)
        - 롤백 시 해당 시점의 DAG/노드/파라미터/설정 구조를 복원하여 파이프라인 재구성 가능
        - 스냅샷 데이터 구조는 Pydantic v2 모델(StrategySnapshot, NodeSnapshot)로 직렬화/역직렬화
        - 모든 노드/의존성/파라미터/설정/이벤트의 식별자는 정책 Node ID(32자리 해시)만 사용
    - **[API 예시]**
        - 스냅샷 저장: `POST /v1/registry/strategies/{version_id}/snapshots` (StrategySnapshot 모델)
        - 스냅샷 조회: `GET /v1/registry/strategies/{version_id}/snapshots`
        - 롤백: `POST /v1/registry/strategies/{version_id}/rollback?snapshot_id=...`
    - **[데이터 구조 예시]**
        ```python
        class NodeSnapshot(BaseModel):
            node_id: str  # 정책 Node ID(32자리 해시)
            data: Dict[str, Any]  # DataNode/DAGNode 직렬화 데이터
        class StrategySnapshot(BaseModel):
            version_id: str
            created_at: int
            nodes: List[NodeSnapshot]
            edges: List[Dict[str, str]]  # {source, target}
            metadata: Optional[Dict[str, Any]]
        ```
    - **[롤백/비교/재실행 시나리오]**
        1. 사용자는 특정 시점의 스냅샷을 선택하여 롤백 요청
        2. Registry는 해당 스냅샷의 DAG/노드/파라미터/설정 구조를 반환
        3. Orchestrator는 이 구조로 파이프라인을 재구성/재실행
        4. 스냅샷 간 비교/분석도 가능(예: 노드/의존성/파라미터 차이)
    - **[주의사항]**
        - 스냅샷/롤백/비교의 모든 기준은 정책 Node ID(32자리 해시)로 통일
        - 스냅샷 데이터는 JSON 직렬화로 저장하므로, 모델 변경 시 역직렬화 호환성에 주의
        - 롤백 시 기존 파이프라인과의 차이(노드 추가/삭제/변경 등)는 별도 비교 API/로직으로 확장 가능

### 8.4.3 향후 확장 방향
- 전략/노드 동적 추가/삭제/수정 지원
- 템플릿/재사용성 강화, 권한 관리, API/운영성 개선 등

---

(상세 설계 및 구현 방안은 todo.md에 세부 태스크로 분리)

### [중요 정책] 글로벌 Node ID(노드 식별자) 설계 및 생성 규칙

QMTL의 모든 노드는 글로벌 유일 Node ID를 가져야 하며, 이 Node ID는 함수 객체, 함수 코드, 업스트림, stream_settings, key_params 등 결정적 요소의 해시로 생성됩니다. 

#### 1. Node ID 생성 원칙
- **함수 이름(name) 파라미터는 제거**: 노드 생성 시 별도의 이름 지정 없이, 함수 객체 자체가 노드의 식별자가 됨
- **Node ID는 다음 요소의 해시로 생성**
  1. 함수 객체의 `__qualname__` (클래스 메서드 구분 포함)
  2. 함수 소스코드(AST 파싱/문자열)
  3. 업스트림 함수들의 `__qualname__` 리스트(업스트림도 함수 객체로만 지정, 문자열/이름 지정 불가)
  4. stream_settings (interval/period 등 모든 설정 포함)
  5. key_params 및 그 값(파라미터 값이 다르면 Node ID도 다름)
- **람다 함수**: 이름 대신 소스코드+업스트림+stream_settings+key_params의 해시로 Node ID 생성(객체 id/hash 사용 금지)
- **클래스 메서드**: `__qualname__`으로 구분(동일 함수명이라도 클래스가 다르면 Node ID 다름)
- **사이클(순환 참조)만 없으면 함수 이름 충돌 허용**: 파이프라인 내에서 함수 이름이 중복되어도, Node ID는 코드/입력/설정이 다르면 다르게 생성됨(사이클 검증은 DAG 생성 시 자동 수행)
- **객체 id/hash 사용 금지**: Node ID는 영속적/결정적이어야 하므로, 파이썬 객체 id/hash 등 런타임 의존 정보는 사용하지 않음

#### 2. Node ID 생성 예시 코드
```python
import inspect, ast, hashlib, json

def generate_node_id(fn, upstreams, stream_settings, key_params):
    try:
        source = inspect.getsource(fn)
        source = inspect.cleandoc(source)
        tree = ast.parse(source)
        fn_ast = ast.dump(tree, annotate_fields=True, include_attributes=False)
    except Exception:
        fn_ast = str(fn)
    upstream_names = [u.__qualname__ for u in upstreams]
    signature_dict = {
        "qualname": fn.__qualname__,
        "ast": fn_ast,
        "upstreams": upstream_names,
        "stream_settings": stream_settings.model_dump() if hasattr(stream_settings, "model_dump") else str(stream_settings),
        "key_params": key_params,
    }
    signature_str = json.dumps(signature_dict, sort_keys=True)
    return hashlib.md5(signature_str.encode("utf-8")).hexdigest()
```

#### 3. 정책 적용 범위
- SDK, Registry, Orchestrator, 테스트, 모델 직렬화/역직렬화 등 전체 계층에 동일하게 적용
- DataNode, ProcessingNode, SourceNode, QueryNode 등 모든 노드 추상화에 일관 적용
- Node ID는 32자리 hex 문자열로 관리

#### 4. 주의사항 및 가이드
- **람다 함수**: 소스코드 추출이 불가능한 환경(인터프리터 등)에서는 명시적 함수 사용 권장
- **함수 이름 충돌**: 허용(사이클만 없으면 됨), 실제 구분은 Node ID로 이루어짐
- **업스트림**: 반드시 함수 객체로만 지정(문자열/이름 지정 불가)
- **Node ID 생성 정책**: SDK 내부에서 자동 처리, 사용자는 함수 객체만으로 DAG을 구성하면 됨
- **사이클 검증**: 파이프라인/DAG 생성 시 자동 수행(ValidationError)

#### 5. 예시
```python
def fetch_raw(...): ...
def make_feature(...): ...
def make_signal(...): ...

node1 = ProcessingNode(fn=fetch_raw, ...)
node2 = ProcessingNode(fn=make_feature, upstreams=[fetch_raw], ...)
node3 = ProcessingNode(fn=make_signal, upstreams=[make_feature], ...)
# node1, node2, node3의 Node ID는 각 함수/업스트림/설정/파라미터에 따라 자동 생성됨
```

**이 정책은 nodeID.md, todo.md, 사용자 가이드, 예제 코드, 테스트 코드에 모두 반영되어 있습니다.**

기존 요약 문구와 '자세한 정책, 예시, 주의사항 등은 [nodeID.md](./nodeID.md)를 참조하세요.' 안내는 유지하되, 위 상세 정책을 본문에 직접 포함합니다.

## [2025-05-13] Registry 메타데이터 통합 진입점 구조(파사드) 적용
- Registry의 모든 메타데이터(노드/전략/DAG/의존성/이력) 접근은 반드시 MetadataService(파사드)만을 통해서 이루어져야 한다.
- 기존 도메인별 서비스(NodeManagementService, StrategyManagementService 등)는 MetadataService 내부에서만 DI/호출하며, 외부 계층(API, 테스트 등)에서는 직접 접근을 금지한다.
- API, 테스트, 문서 등 모든 계층에서 MetadataService만을 사용하도록 구조를 일원화한다.
- 단순 CRUD/조회도 MetadataService를 통해 위임 호출하며, 복합 트랜잭션/오케스트레이션/비즈니스 로직도 이 계층에서 일관되게 처리한다.
- 구조적 장점: 외부 일관성, 정책 강제, 트랜잭션/로깅/정책 적용, 확장성, 테스트 용이성 등
- 예시/가이드/DI 구조는 developer_guide.md, README.md, tests/unit/registry/services/test_metadata_service.py 참조