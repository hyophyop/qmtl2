# QMTL 사용자 가이드

## 소개

QMTL(Quantitative Machine Trading Library)은 데이터 기반 트레이딩 전략을 쉽게 개발하고 배포할 수 있는 프레임워크입니다. 데이터 노드, 파이프라인, 전략 등의 개념을 중심으로 확장 가능한 데이터 처리 시스템을 구축할 수 있습니다.

이 가이드는 QMTL을 처음 사용하는 사용자를 위한 기본 개념 및 사용법을 안내합니다.

## 설치 및 설정

### 요구 사항
- Python 3.10 이상
- Docker 및 docker-compose
- uv (Python 패키지 관리자)

### 설치 과정

```bash
# uv 설치
pip install uv

# 프로젝트 클론
git clone https://github.com/your-org/qmtl.git
cd qmtl

# 의존성 설치
uv pip install -e .

# 개발용 컨테이너 실행
make dev-up

# 서비스 시작
make start-registry
make start-orchestrator
```

## 핵심 개념

### 데이터 노드 (DataNode)

데이터 노드는 QMTL의 기본 단위로, 하나의 데이터 처리 함수와 그 결과를 나타냅니다. 각 노드는 다음과 같은 특성을 가집니다:

- 고유한 `node_id`
- 노드 유형 및 태그 (FEATURE, SIGNAL 등)
- 데이터 형식 정보
- 다른 노드에 대한 의존성
- 인터벌 설정 (시계열 데이터의 경우)

예시:
```python
from qmtl.sdk import node

@node(tags=["FEATURE"])
def calculate_sma(prices: list) -> float:
    """단순 이동 평균 계산"""
    return sum(prices) / len(prices)
```

### 파이프라인 (Pipeline)

파이프라인은 여러 데이터 노드를 연결하여 데이터 흐름을 정의합니다. 노드 간의 의존성을 기반으로 실행 순서가 자동으로 결정됩니다.

예시:
```python
from qmtl.sdk import Pipeline

# 노드 함수 정의
# ...

# 파이프라인 생성
pipeline = Pipeline(nodes=[fetch_data, calculate_sma, generate_signal])

# 실행
result = pipeline.execute()
print(result)
```

### 전략 (Strategy)

전략은 노드 집합으로 구성된 코드로, 특정 목적을 위한 데이터 처리 로직을 포함합니다.

전략 코드 예시:
```python
# my_strategy.py
from qmtl.sdk import node

@node(tags=["data"])
def fetch_prices() -> list:
    # 가격 데이터 가져오기
    return [100, 101, 102, 103, 104]

@node(tags=["feature"])
def calculate_sma(prices: list) -> float:
    # 이동 평균 계산
    return sum(prices) / len(prices)

@node(tags=["feature"])
def calculate_volatility(prices: list) -> float:
    # 변동성 계산
    mean = sum(prices) / len(prices)
    return (sum((p - mean) ** 2 for p in prices) / len(prices)) ** 0.5

@node(tags=["signal"])
def generate_signal(sma: float, volatility: float) -> dict:
    # 시그널 생성
    if sma > 102 and volatility < 2:
        return {"action": "BUY", "confidence": 0.8}
    elif sma < 101:
        return {"action": "SELL", "confidence": 0.7}
    else:
        return {"action": "HOLD", "confidence": 0.5}
```

## 기본 사용법

### 1. 노드 정의

`@node` 데코레이터를 사용하여 함수를 데이터 노드로 정의합니다:

```python
from qmtl.sdk import node
from qmtl.models import IntervalSettings

# 기본 노드
@node(tags=["data"])
def fetch_data() -> list:
    return [1, 2, 3, 4, 5]

# 태그가 있는 노드
@node(tags=["feature", "price"])
def calculate_average(data: list) -> float:
    return sum(data) / len(data)

# 인터벌 설정이 있는 노드
@node(
    tags=["feature"], 
    interval_settings=IntervalSettings(interval="1h", period="7d")
)
def hourly_feature(data: list) -> float:
    return sum(data) / len(data)
```

### 2. 파이프라인 생성 및 실행

```python
from qmtl.sdk import Pipeline

# 노드 함수들 정의
# ...

# 파이프라인 생성
pipeline = Pipeline(nodes=[fetch_data, calculate_average, hourly_feature, generate_signal])

# 로컬에서 실행
result = pipeline.execute()
print("결과:", result)

# 분산 실행 (Redpanda/Kafka 기반)
result = pipeline.execute(parallel=True)
print("분산 실행 결과:", result)
```

### 3. 파이프라인 실행 트리거

```python
from qmtl.sdk import OrchestratorClient

# 클라이언트 생성
client = OrchestratorClient(base_url="http://localhost:8001")

# 시그널 노드 ID 찾기 (실제 ID는 파이프라인 정의 후 확인 가능)
signal_node_id = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"

# 파이프라인 실행 트리거
execution_id = client.trigger_pipeline(
    node_ids=[signal_node_id],
    inputs={},  # 입력 데이터 (필요한 경우)
    execution_params={"timeout": 60}
)

# 상태 확인
status = client.get_pipeline_status(execution_id)
print("실행 상태:", status)
```

## 고급 기능

### 태그 기반 노드 검색 및 분석

QueryNode를 사용하여 태그 기반으로 노드를 동적으로 검색하고 분석할 수 있습니다:

```python
from qmtl.sdk.node import QueryNode
from qmtl.sdk import Pipeline

# 태그 기반 쿼리 노드 생성 (PRICE 태그를 가진 노드 검색)
price_query = QueryNode(name="price_query", tags=["PRICE"])

# 쿼리 결과를 처리하는 노드
@node(tags=["analyzer"])
def analyze_prices(price_query):
    # price_query는 태그에 맞는 노드들의 결과를 포함한 dict
    price_nodes = list(price_query.values())
    
    # 분석 로직
    avg_price = sum(sum(node) / len(node) for node in price_nodes) / len(price_nodes)
    return {"average_price": avg_price}

# 파이프라인에 쿼리 노드 포함
pipeline = Pipeline(nodes=[fetch_price1, fetch_price2, price_query, analyze_prices])
result = pipeline.execute()
```

### 히스토리 데이터 관리

인터벌 설정이 있는 노드의 히스토리 데이터를 관리하고 접근할 수 있습니다:

```python
from qmtl.sdk import Pipeline, node
from qmtl.models import IntervalSettings

@node(tags=["price"], interval_settings=IntervalSettings(interval="1h", period="7d"))
def hourly_price() -> float:
    return 100.0

# 파이프라인 생성 및 실행
pipeline = Pipeline(nodes=[hourly_price])

# 여러 번 실행하여 히스토리 데이터 생성
for i in range(5):
    pipeline.execute()

# 히스토리 데이터 접근
history = pipeline.get_history("hourly_price", "1h", 5)
print("히스토리 데이터:", history)
```

### 분석기 구현

분석기는 QueryNode를 활용하여 여러 데이터 노드를 분석하는 특별한 형태의 전략입니다:

```python
from qmtl.sdk.analyzer import Analyzer
from qmtl.sdk.node import QueryNode, Node

# 분석기 생성
analyzer = Analyzer(name="price_analyzer")

# 쿼리 노드 생성 및 추가
price_query = QueryNode(name="price_query", tags=["PRICE"], interval="1d")
analyzer.query_nodes[price_query.name] = price_query

# 분석 노드 추가
@Node(name="price_stats")
def calculate_stats(price_query):
    price_data = list(price_query.values())
    return {
        "count": len(price_data),
        "mean": sum(sum(data) / len(data) for data in price_data) / len(price_data),
        "min": min(min(data) for data in price_data),
        "max": max(max(data) for data in price_data)
    }

analyzer.add_node(calculate_stats)

# 분석기 실행
results = analyzer.execute(local=True)
print("분석 결과:", results)
```

## 모범 사례 및 팁

1. **함수 파라미터 명명**: 노드 함수의 파라미터 이름은 의존하는 노드 함수의 이름과 일치해야 합니다.

2. **태그 활용**: 태그를 사용하여 노드의 역할과 기능을 명확하게 표시하세요.

3. **인터벌 설정**: 시계열 데이터의 경우 적절한 인터벌과 피리어드를 설정하여 히스토리 데이터를 효율적으로 관리하세요.

4. **환경별 전략 관리**: 개발, 테스트, 운영 환경을 분리하여 전략을 안전하게 테스트하고 배포하세요.

5. **노드 ID 관리**: 디버깅 및 모니터링을 위해 노드 ID와 함수 이름 매핑을 기록해두세요.

6. **히스토리 데이터 최적화**: 대용량 데이터의 경우 적절한 TTL 및 max_items 설정으로 메모리 사용량을 최적화하세요.

## 문제 해결

### 일반적인 문제

1. **노드 실행 오류**
   - 의존성 노드가 올바르게 선언되었는지 확인
   - 파라미터 이름이 의존하는 노드 함수 이름과 일치하는지 확인
   - 데이터 타입이 호환되는지 확인

2. **연결 오류**
   - Neo4j, Redis, Redpanda 등 서비스가 실행 중인지 확인
   - 환경 변수 설정 확인
   - 네트워크 연결 및 방화벽 설정 확인

3. **전략 제출 오류**
   - (삭제) 전략 제출/등록/활성화/비활성화 관련 오류 안내는 더 이상 필요하지 않음

### 로그 확인

문제 해결을 위해 로그를 확인하세요:

```bash
# Registry 로그 확인
make logs-registry

# Orchestrator 로그 확인
make logs-orchestrator

# Neo4j 로그 확인
make logs-neo4j

# Redis 로그 확인
make logs-redis

# Redpanda 로그 확인
make logs-redpanda
```

## 추가 자료

- [API 문서](../generated/api.md)
- [개발자 가이드](../developer_guide.md)
- [아키텍처 개요](../architecture.md)
- [용어 사전](../glossary.md)
- [전체 워크플로우 예제](../e2e_workflow.md)

더 자세한 정보가 필요하시면 공식 문서 또는 GitHub 저장소를 참조하세요. 