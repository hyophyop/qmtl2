# QMTL SDK 모듈

이 디렉토리는 전략 개발자를 위한 PyTorch 스타일 파이프라인 SDK의 핵심 구현을 포함합니다.


## 구조
- `pipeline.py`: Pipeline, Node, QueryNode, Analyzer 클래스 정의
- `models.py`: SDK 전용 Pydantic 모델 정의 (직렬화/역직렬화)
- `node.py`: 파이프라인의 기본 구성 요소인 Node와 QueryNode 클래스 구현
- `execution/`: 각 실행 엔진별 구현 파일 (local.py, parallel_engine.py, state_manager.py, stream_processor.py 등) 위치
- `visualization.py`: 파이프라인 시각화 기능 제공
- `__init__.py`: 패키지 초기화

## 직렬화/역직렬화 예시

모든 파이프라인/노드/쿼리노드는 Pydantic 모델 기반 직렬화/역직렬화가 가능합니다.

```python
from qmtl.sdk.models import PipelineDefinition, NodeDefinition, QueryNodeDefinition

# 파이프라인/노드 → dict (직렬화)
pipeline = Pipeline(name="my_pipeline")
node = Node(name="A", fn=lambda: 1, tags=["RAW"])
pipeline.add_node(node)
definition = pipeline.to_definition()  # dict

# dict → 모델 (역직렬화)
pipeline_def = PipelineDefinition.from_definition(definition)
assert pipeline_def.name == "my_pipeline"
assert pipeline_def.nodes[0].name == "A"

# 노드 단위도 동일하게 지원
node_def = NodeDefinition.from_definition(node.to_definition())
assert node_def.name == "A"
```

## 주요 클래스
- **Pipeline**: 전략 파이프라인의 추상 베이스 클래스
- **Node**: 개별 연산 노드의 추상 클래스
- **QueryNode**: 태그 기반 쿼리 노드 추상 클래스
- **Analyzer**: 태그 기반 자동 분석기 파이프라인 추상 클래스 (QueryNode 기반 태그 매핑/실행, 분석 결과 캐싱/상태 관리)

## 독립 실행/테스트 환경 안내

### 로컬 가상환경 실행
```sh
make run
```

### 단위 테스트
```sh
make test
```

### 도커/컨테이너 실행 (smoke test)
```sh
docker-compose up --build -d
docker-compose down
```
- **LocalExecutionEngine**: 로컬 환경에서 파이프라인을 순차적으로 실행하는 엔진
- **ParallelExecutionEngine**: Kafka/Redpanda와 Redis를 활용한 분산 병렬 실행 엔진
- **StateManager**: Redis 기반 상태 관리 클래스 (인터벌 데이터 저장 및 조회)
- **MockExecutionEngine**: 단위 테스트용 간소화된 실행 엔진

## 실행 엔진
SDK는 태그 기반 자동 분석기(Analyzer) 실행을 포함해 세 가지 유형의 실행 엔진을 지원합니다:
## 태그 기반 자동 분석기(Analyzer) 실행 예시

```python
from qmtl.sdk.analyzer import Analyzer
from qmtl.sdk.node import Node, QueryNode
from qmtl.sdk.models import QueryNodeResultSelector

# 노드 정의
n1 = Node(name="n1", fn=lambda: 1, tags=["A", "B"])
n2 = Node(name="n2", fn=lambda: 2, tags=["A", "C"])
n3 = Node(name="n3", fn=lambda: 3, tags=["B", "C"])

# 분석기 생성 및 노드 등록
analyzer = Analyzer(name="test-analyzer")
analyzer.add_node(n1)
analyzer.add_node(n2)
analyzer.add_node(n3)

# QueryNode: 태그 A+B 모두 가진 노드만
qn = QueryNode(name="q1", tags=["A", "B"])
analyzer.query_nodes[qn.name] = qn

# selector 체이닝 예시: interval=1d로 filter, random 1개 샘플
selectors = {
    "q1": [
        QueryNodeResultSelector(mode="filter", filter_meta={"stream_settings": {"intervals": {"1d": {"interval": "1d"}}}}),
        QueryNodeResultSelector(mode="random", sample_size=1)
    ]
}
results = analyzer.execute(local=True, selectors=selectors)
print(results)
```

분석 결과는 analyzer.results_cache, analyzer.analyzer_results(AnalyzerResult 리스트)로도 접근할 수 있습니다.

### 1. 로컬 실행 엔진 (LocalExecutionEngine)
- 토폴로지 정렬을 통한 노드 의존성 기반 실행 순서 결정
- 노드 간 데이터 전송 자동화
- 히스토리 추적 및 결과 수집 기능
- 타임아웃 처리 및 오류 처리 메커니즘
- 외부 의존성 없이 단일 프로세스에서 동작

```python
from qmtl.sdk.pipeline import Pipeline
from qmtl.sdk.node import Node
from qmtl.sdk.execution import LocalExecutionEngine

# 파이프라인 생성
pipeline = Pipeline(name="my_pipeline")

# 노드 추가
node_a = Node(name="A", fn=lambda: 42)
node_b = Node(name="B", fn=lambda a: a * 2, upstreams=["A"])
pipeline.add_node(node_a)
pipeline.add_node(node_b)

# 로컬 엔진으로 실행
results = pipeline.execute(test_mode=True)
print(results)  # {'A': 42, 'B': 84}
```


### 2. 병렬 실행 엔진 (ParallelExecutionEngine)
- `from qmtl.sdk.execution import ParallelExecutionEngine` 사용
- Kafka/Redpanda를 통한 노드 간 메시지 전달
- Redis를 활용한 상태 및 히스토리 관리
- 비동기 및 병렬 실행 지원
- 확장성 있는 분산 실행 환경 제공
- **파이프라인/노드 기반 토픽 자동 생성 지원** (명명 규칙: `qmtl.input.{pipeline}.{node}`, `qmtl.output.{pipeline}.{node}`)
- 토픽이 없으면 자동 생성, 이미 있으면 무시 (권한/오류 발생 시 로깅)

```python
from qmtl.sdk.pipeline import Pipeline
from qmtl.sdk.node import Node

# 파이프라인 생성
pipeline = Pipeline(name="my_parallel_pipeline")

# 인터벌 설정을 포함한 노드 추가
node_a = Node(
    name="price_source", 
    fn=lambda: {"price": 100.5},
    interval_settings={
        "1d": {"interval": "1d", "period": "7d", "max_history": 100},
        "1h": {"interval": "1h", "period": "2d", "max_history": 50}
    }
)
pipeline.add_node(node_a)

# 병렬 모드로 실행
results = pipeline.execute(
    parallel=True,
    brokers="localhost:9092",  # Kafka/Redpanda 브로커 주소
    redis_uri="redis://localhost:6379/0"  # Redis 연결 URI
)
```

### 3. 상태 관리 (StateManager)
- `from qmtl.sdk.execution import StateManager` 사용
- Redis 기반 인터벌별 데이터 저장/조회/TTL 관리
- 파이프라인 실행 중 상태 스냅샷 및 히스토리 관리

```python
# 히스토리 데이터 조회
history = pipeline.get_history(
    node_name="price_source",
    interval="1d",
    count=5,
    start_ts=1714000000,  # 시작 타임스탬프 (선택 사항)
    end_ts=1714100000     # 종료 타임스탬프 (선택 사항)
)

# 값만 조회 (타임스탬프 없이)
values = pipeline.get_interval_data(
    node_name="price_source",
    interval="1h",
    count=10
)

# 노드 메타데이터 조회
metadata = pipeline.get_node_metadata(
    node_name="price_source",
    interval="1d"
)
print(metadata)  # {'count': 42, 'max_items': 100, 'ttl': 604800, ...}
```

### 4. 스트림 프로세서 (StreamProcessor)
- `from qmtl.sdk.execution import StreamProcessor` 사용
- 실시간 데이터 스트림 처리 및 이벤트 기반 트리거 지원

## 엔진별 import 예시
```python
from qmtl.sdk.execution import LocalExecutionEngine, ParallelExecutionEngine, StateManager, StreamProcessor
```

> ⚠️ 기존 `execution.py`는 SRP 원칙에 따라 분리되었으며, 각 엔진별 구현은 `execution/` 디렉토리에서 관리됩니다.

## 실행 엔진 구조 분리 안내

QMTL SDK의 실행 엔진은 다음과 같이 관심사 분리(SRP)에 따라 파일이 분리되어 있습니다:

- `execution/stream_processor.py`: Kafka/Redpanda 기반 메시지 스트림 처리
- `execution/state_manager.py`: Redis 기반 상태 및 히스토리 관리
- `execution/parallel_engine.py`: 병렬 파이프라인 실행 엔진 (Kafka/Redis 연동)
- `execution/local.py`: 로컬 파이프라인 실행 엔진

각 엔진은 다음과 같이 import하여 사용할 수 있습니다:

```python
from qmtl.sdk.execution import StreamProcessor, StateManager, ParallelExecutionEngine, LocalExecutionEngine
```

각 엔진별 책임과 사용법은 각 파일 상단 docstring 및 본 README를 참고하세요.

## 개발 및 테스트
- 파이프라인 테스트: `tests/unit/sdk/test_pipeline.py` 참고
- 로컬 실행 메커니즘 테스트: `tests/unit/sdk/test_local_execution.py` 참고
- Redis 상태 관리 테스트: `tests/unit/sdk/test_redis_state_manager.py` 참고
- 인터벌 데이터 조회 테스트: `tests/unit/sdk/test_redis_interval_data.py` 참고
- 모든 데이터 구조는 Pydantic v2 스타일로 정의

## 컨테이너 빌드 유틸리티 사용법

QMTL 전략/파이프라인을 컨테이너 이미지로 패키징할 때 아래 유틸리티를 활용할 수 있습니다.

```python
from qmtl.sdk import container

# 1. Dockerfile 템플릿 생성
container.write_dockerfile(target_dir=".", dependency_file="requirements.txt")

# 2. 의존성 파일 자동 추출
dep_file = container.extract_dependencies(project_dir=".")

# 3. Docker 이미지 빌드
container.build_docker_image(context_dir=".", tag="my-strategy:latest")

# 4. Docker 이미지 레지스트리 푸시
container.push_docker_image(tag="my-strategy:latest", registry="myrepo")
```

- Dockerfile 템플릿은 Python 3.11-slim 기반, main.py 실행을 기본으로 합니다.
- pyproject.toml/requirements.txt 자동 인식 및 설치 명령 삽입
- 실제 빌드/푸시에는 Docker가 필요합니다.
- 상세 옵션 및 확장은 container.py 소스 참고

## K8s Job 템플릿 자동 생성 예시

QMTL SDK는 파이프라인 정의(PipelineDefinition)로부터 쿠버네티스 Job YAML을 자동 생성할 수 있습니다.

```python
from qmtl.sdk import K8sJobGenerator, PipelineDefinition

pipeline = PipelineDefinition(name="my-pipeline", nodes=[])
image = "myrepo/pipeline:latest"
env_vars = {"REDIS_URL": "redis://localhost:6379", "KAFKA_BROKER": "kafka:9092"}

job = K8sJobGenerator.generate_job(pipeline, image, env_vars=env_vars)
yaml_str = K8sJobGenerator.to_yaml(job)
print(yaml_str)
```

- 환경 변수, 리소스, 명령어 등은 generate_job 파라미터로 커스텀 지정 가능
- 생성된 YAML은 kubectl, Argo, Airflow 등에서 바로 사용 가능
- 내부적으로 Pydantic v2 모델(models/k8s.py) 기반으로 JobSpec을 생성하며, model_dump_yaml() 메서드로 YAML 변환
- 단위 테스트: tests/sdk/test_k8s.py 참고

## ⚠️ 인터벌(interval)/피리어드(period) 정책 및 Pydantic v2 모델 안내

- 모든 Node, SourceNode, DataNode는 반드시 하나 이상의 interval(주기, Enum)과 period(보관 기간, int) 설정이 필요합니다.
- interval은 반드시 `IntervalEnum`(예: "1d", "1h", "1m" 등) 값만 허용하며, period는 반드시 int(정수)여야 합니다.
- period에 문자열("7d" 등) 입력 시 자동 변환되지만, 내부적으로는 int로 저장/처리됩니다.
- 파이프라인 전체에 공용 interval/period(default_intervals)를 지정할 수 있으며, 노드별로 오버라이드 가능합니다.
- 모든 interval별로 period가 누락되면 예외가 발생합니다.
- Pydantic v2 스타일(BaseModel, field_validator/model_validator, model_config 등)만 허용하며, v1 스타일/alias 사용 금지.
- 전략 제출/활성화/비활성화/버전 관리/이력 관리 등 Orchestrator/Registry 기반 코드는 완전히 제거되었습니다. SDK 기반 워크플로우만 지원합니다.
- Node 추상화 구조는 ProcessingNode(업스트림/stream_settings 필수), SourceNode(외부 입력), QueryNode(태그 기반 쿼리, 업스트림/stream_settings 강제 없음)로 분리되어 있습니다.
- 테스트/코드/문서/모델은 SoC, 테스트 계층 분리, 커버리지 80% 이상, 문서화 등 프로젝트 개발 가이드라인을 철저히 준수합니다.

### 예시 (최신 정책)
```python
from qmtl.sdk.models import IntervalSettings, NodeStreamSettings, IntervalEnum
from qmtl.sdk.pipeline import Pipeline, ProcessingNode

default_intervals = {
    IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=14),
    IntervalEnum.HOUR: IntervalSettings(interval=IntervalEnum.HOUR, period=7),
}
pipeline = Pipeline(name="my_pipeline", default_intervals=default_intervals)

node1 = ProcessingNode(
    name="n1",
    fn=lambda x: x,
    upstreams=["up"],
    stream_settings=NodeStreamSettings(intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)})
)
pipeline.add_node(node1)
assert node1.stream_settings.intervals[IntervalEnum.DAY].period == 14  # default_intervals 적용

node2 = ProcessingNode(
    name="n2",
    fn=lambda x: x,
    upstreams=["up"],
    stream_settings=NodeStreamSettings(intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=30)})
)
pipeline.add_node(node2)
assert node2.stream_settings.intervals[IntervalEnum.DAY].period == 30  # 오버라이드
```
