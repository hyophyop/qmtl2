## 🔔 실시간 모니터링/알림 시스템 연동 (MULTI-7)

QMTL은 실시간 파이프라인/노드 상태 변화 이벤트를 Pub/Sub(예: Redis) 기반으로 발행/구독할 수 있습니다.

- Registry: 상태 변화 이벤트 발행/구독 API(`/v1/registry/events/node-status` 등), EventPublisher/EventSubscriber 서비스 제공
- Orchestrator: 이벤트 구독 클라이언트(EventClient) 및 대시보드/알림 시스템 연동 샘플 제공
- 모든 이벤트/상태/알림 모델은 Pydantic v2 스타일(`models/event.py`)로 정의
- 단위 테스트 및 모킹 기반 검증(tests/unit/models/test_event.py 등)

예시:
```python
from qmtl.models.event import NodeStatusEvent
from qmtl.registry.services.event import EventPublisher

# 노드 상태 변화 이벤트 발행
event = NodeStatusEvent(node_id="n1", status="RUNNING")
EventPublisher().publish_node_status(event)

# Orchestrator에서 구독 및 대시보드 연동
from qmtl.orchestrator.services.event_client import EventClient
def dashboard_callback(msg):
    print("이벤트 수신:", msg)
EventClient().subscribe_node_status("n1", dashboard_callback)
```

자세한 정책 및 예시는 `docs/developer_guide.md`, `docs/generated/api.md` 참고.
# QMTL (Quantitative Machine Trading Library) 2.0

> **QMTL**은 전략 기반 데이터 파이프라인과 분석 시스템을 쉽고 일관되게 구축할 수 있는 프레임워크입니다.

## 📋 개요

QMTL은 "전략이 DataNode DAG를 선언하면 플랫폼이 파이프라인 라이프사이클을 관리한다"는 비전을 실현하기 위한 시스템입니다. 전략 개발부터 배포, 관리까지 통합적으로 지원하며 태그 기반 노드 분류 및 자동 분석기 기능도 제공합니다.

## 🚀 주요 기능

- **전략 기반 데이터 파이프라인**: 데코레이터를 활용한 간결한 전략 코드 작성
- **노드 라이프사이클 자동화**: 생성, 등록, 실행, 가비지 컬렉션 자동 관리
- **분산 실행 환경**: Kafka/Redpanda 기반 병렬 실행 엔진 지원
- **의존성 기반 동적 스케줄링 및 리소스 최적화**: DAG 기반 파이프라인 구조 및 ready node API 제공, 실행 가능한 노드만 선별 실행, 리소스 상황에 따라 동적 스케줄링 지원
- **태그 기반 노드 분류**: NodeTag를 활용한 유연한 노드 분류 및 조회
- **인터벌 데이터 관리**: 다양한 시간 단위 데이터의 효율적인 저장 및 관리
- **분석기 지원**: QueryNode 기반의 자동 분석 시스템
- **Redis 기반 상태 관리**: 분산 환경에서의 상태 및 히스토리 데이터 관리
- **K8s 배포 지원**: 컨테이너 빌드 및 Kubernetes Job 템플릿 자동 생성

## 🔧 설치 방법

### 필수 요구사항
- Python 3.10 이상
- Docker 및 docker-compose
- uv (Python 패키지 관리 도구)

### 패키지 설치
```bash
# uv 설치
pip install uv

# 프로젝트 클론
git clone https://github.com/your-org/qmtl.git
cd qmtl

# 의존성 설치
uv pip install -e .
```

### 개발 환경 설정
```bash
# 개발용 컨테이너 실행
make dev-up

# 서비스 시작
make start-registry
make start-orchestrator
```

## 🏃‍♂️ 빠른 시작 가이드

### 1. 간단한 전략 작성
```python
from qmtl.sdk import Pipeline, node, IntervalSettings

@node(tags=["feature"])
def feature(data: list[int]) -> int:
    return sum(data)

@node(tags=["signal"], interval_settings=IntervalSettings(interval="1d"))
def signal(x: int) -> float:
    return float(x) / 10

pipeline = Pipeline(nodes=[feature, signal])
result = pipeline.execute(inputs={"feature": [1,2,3]})
print(result)  # {'signal': 0.6}
```

### 2. 파이프라인 실행 트리거
```python
from qmtl.sdk import OrchestratorClient

client = OrchestratorClient()
execution_id = client.trigger_pipeline(["node_id1", "node_id2"], 
                                       inputs={"node_id1": {"price": 100}})
status = client.get_pipeline_status(execution_id)
print(status)
```

## 📚 문서

자세한 사용법과 가이드는 다음 문서를 참조하세요:

[👉 사용자 가이드 바로가기](docs/user_guide.md)
[👉 개발자 가이드 바로가기](docs/developer_guide.md)
[👉 SDK 가이드 바로가기](docs/sdk_guide.md)
[👉 분석기 가이드 바로가기](docs/analyzer_guide.md)
[👉 API 문서 바로가기](docs/generated/api.md)

## 📊 아키텍처 개요

QMTL은 다음과 같은 주요 구성 요소로 이루어져 있습니다:

- **Registry**: 노드/전략 메타데이터 중앙 저장소 (Neo4j 기반), 전체 DAG 구조/의존성/ready node API 제공
- **Orchestrator**: 전략 코드 파싱/실행 조율 (FastAPI 기반), Registry에서 DAG/ready node 정보 조회 후 실행
- **SDK**: 파이프라인/노드/분석기/상태 관리 (Pydantic v2 모델 기반)
- **실행 엔진**: 로컬/병렬 실행 환경 (Kafka/Redpanda 기반)
### MULTI-4 관련 API 예시

#### DAG 구조 조회
```
GET /v1/registry/pipelines/{pipeline_id}/dag
```
#### Ready Node 목록 조회
```
GET /v1/registry/pipelines/{pipeline_id}/ready-nodes
```
각 API는 파이프라인의 전체 DAG 구조 및 현재 실행 가능한 노드 목록을 반환합니다. 자세한 예시는 docs/generated/api.md 참고.

QMTL의 모든 노드/소스노드는 반드시 interval(주기) 설정이 필요하며, interval이 없는 경우 예외가 발생합니다. (설정 예시는 위 참조)

## 🧪 테스트 실행

```bash
# 모든 테스트 실행
make test

# 특정 테스트 실행
make unit-test       # 단위 테스트만 실행
make integration-test # 통합 테스트만 실행
make e2e-test        # E2E 테스트만 실행
```

## 🤝 기여 가이드

기여는 언제나 환영합니다! 다음 과정을 따라 기여해 주세요:

1. 이슈를 먼저 확인하거나 새로운 이슈를 생성합니다
2. 필요한 경우 기능/버그 수정 브랜치를 생성합니다
3. 테스트가 통과하는지 확인합니다 (`make test`)
4. Pull Request를 제출합니다

## 📄 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요. 

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

## 전략별 DAG 스냅샷/버전 관리 및 롤백 기능

QMTL Registry는 전략 제출/변경 시점의 전체 DAG(노드/의존성/파라미터/설정 등)을 스냅샷으로 영구 저장하고, 언제든 롤백/비교/재실행이 가능합니다.

- 스냅샷은 Neo4j의 `StrategySnapshot` 노드로 관리되며, 모든 데이터는 JSON 직렬화로 저장됩니다.
- 각 스냅샷은 `version_id`, `created_at`(timestamp)로 고유 식별되며, 정책 Node ID(32자리 해시)만을 사용합니다.
- 주요 API:
    - 스냅샷 저장: `POST /v1/registry/strategies/{version_id}/snapshots`
    - 스냅샷 조회: `GET /v1/registry/strategies/{version_id}/snapshots`
    - 롤백: `POST /v1/registry/strategies/{version_id}/rollback?snapshot_id=...`
- 데이터 구조(Pydantic v2):
    - `StrategySnapshot`, `NodeSnapshot` 모델 직렬화/역직렬화
- 사용 예시:
    1. 전략 제출/변경 시점마다 스냅샷 자동 저장
    2. 과거 스냅샷 목록 조회 및 특정 시점으로 롤백
    3. 스냅샷 간 DAG/노드/파라미터 차이 비교 및 분석
- 모든 스냅샷/롤백/비교/이벤트의 기준은 정책 Node ID(32자리 해시)로 통일됩니다.

자세한 정책 및 예시는 `architecture.md`의 8.4절을 참고하세요.

## Registry 메타데이터 통합 진입점(MetadataService) 정책
- Registry의 모든 메타데이터(노드/전략/DAG/의존성/이력) 접근은 반드시 MetadataService(파사드)만을 통해서 이루어집니다.
- 기존 도메인별 서비스(NodeManagementService, StrategyManagementService 등)는 MetadataService 내부에서만 DI/호출하며, 외부 계층(API, 테스트 등)에서는 직접 접근하지 않습니다.
- API, 테스트, 문서 등 모든 계층에서 MetadataService만을 사용하도록 구조를 일원화하였습니다.
- 예시는 tests/unit/registry/services/test_metadata_service.py, src/qmtl/registry/api.py 참조