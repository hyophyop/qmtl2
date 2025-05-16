# QMTL E2E 워크플로우 예제

이 문서는 QMTL을 사용하여 전략을 개발하고, 제출하고, 활성화하고, 실행하는 전체 워크플로우를 단계별로 안내합니다.

## 1. 개발 환경 설정

### 1.1 프로젝트 클론 및 의존성 설치

```bash
# 프로젝트 클론
git clone https://github.com/your-org/qmtl.git
cd qmtl

# uv로 의존성 설치
uv pip install -e .

# 개발 환경 컨테이너 실행
make dev-up
```

### 1.2 서비스 실행

```bash
# 터미널 1: Registry 서비스 실행
make start-registry

# 터미널 2: Orchestrator 서비스 실행
make start-orchestrator
```

## 2. 전략 개발

### 2.1 간단한 전략 예제 (로컬 실행)

```python
# examples/simple_strategy.py
from qmtl.sdk import Pipeline, node

@node(tags=["data"])
def fetch_data() -> list:
    # 실제로는 외부 데이터 소스에서 데이터를 가져오는 로직
    return [10, 20, 30, 40, 50]

@node(tags=["feature"])
def calculate_average(data: list) -> float:
    return sum(data) / len(data)

@node(tags=["feature"])
def calculate_volatility(data: list) -> float:
    avg = sum(data) / len(data)
    return sum((x - avg) ** 2 for x in data) ** 0.5

@node(tags=["signal"])
def generate_signal(avg: float, vol: float) -> bool:
    return avg > 30 and vol < 20

# 파이프라인 생성 및 로컬 실행
if __name__ == "__main__":
    pipeline = Pipeline(nodes=[fetch_data, calculate_average, calculate_volatility, generate_signal])
    
    # 로컬 실행
    result = pipeline.execute()
    print("실행 결과:", result)
    
    # 파이프라인 정보 출력
    print("노드 목록:", [node.name for node in pipeline.nodes])
    print("DAG 정보:", pipeline.get_dag_info())
```

### 2.2 태그 및 인터벌 설정 활용

```python
# examples/interval_strategy.py
from qmtl.sdk import Pipeline, node
from qmtl.models import IntervalSettings

@node(tags=["price"], interval_settings=IntervalSettings(interval="1h", period="7d"))
def fetch_hourly_prices() -> list:
    # 시간별 가격 데이터 반환
    return [100, 101, 102, 103, 104]

@node(tags=["price"], interval_settings=IntervalSettings(interval="1d", period="30d"))
def fetch_daily_prices() -> list:
    # 일별 가격 데이터 반환
    return [100, 102, 98, 105, 110]

@node(tags=["feature"])
def calculate_momentum(hourly_prices: list, daily_prices: list) -> float:
    # 두 시간대의 가격 데이터를 활용한 모멘텀 계산
    short_term = hourly_prices[-1] / hourly_prices[0] - 1
    long_term = daily_prices[-1] / daily_prices[0] - 1
    return short_term - long_term

@node(tags=["signal"])
def momentum_signal(momentum: float) -> dict:
    # 모멘텀 기반 시그널 생성
    if momentum > 0.05:
        return {"action": "BUY", "strength": momentum}
    elif momentum < -0.05:
        return {"action": "SELL", "strength": abs(momentum)}
    else:
        return {"action": "HOLD", "strength": 0}

# 파이프라인 생성 및 로컬 실행
if __name__ == "__main__":
    pipeline = Pipeline(nodes=[
        fetch_hourly_prices, 
        fetch_daily_prices, 
        calculate_momentum, 
        momentum_signal
    ])
    
    # 로컬 실행
    result = pipeline.execute()
    print("실행 결과:", result)
    print("히스토리 데이터:", pipeline.get_history("fetch_hourly_prices", "1h", 5))
```

## 3. 파이프라인 실행 (최신 정책)

### 3.1 SDK 클라이언트를 통한 실행

```python
from qmtl.sdk import OrchestratorClient
import time

if __name__ == "__main__":
    client = OrchestratorClient(base_url="http://localhost:8001")
    # 노드 목록 조회 및 시그널 노드 ID 추출
    nodes = client.get_nodes()
    signal_nodes = [node for node in nodes if "SIGNAL" in node.get("tags", {}).get("predefined", [])]
    signal_node_ids = [node["node_id"] for node in signal_nodes]
    print(f"시그널 노드: {signal_node_ids}")
    # 파이프라인 실행 트리거
    execution_result = client.trigger_pipeline(
        node_ids=signal_node_ids,
        inputs={},
        execution_params={"timeout": 60}
    )
    pipeline_id = execution_result["execution_id"]
    print(f"파이프라인 실행 ID: {pipeline_id}")
    # 실행 상태 확인 (폴링)
    max_retries = 10
    for i in range(max_retries):
        status = client.get_pipeline_status(pipeline_id)
        print(f"실행 상태: {status['status']}")
        if status["status"] in ["COMPLETED", "FAILED"]:
            if "result" in status:
                print(f"실행 결과: {status['result']}")
            break
        time.sleep(1)
```

## 4. 분석기 구현 및 활용

### 4.1 분석기 구현

```python
# examples/analyzer_example.py
from qmtl.sdk.analyzer import Analyzer
from qmtl.sdk.node import Node, QueryNode
import pandas as pd
import numpy as np

# 데이터 노드 생성
@Node(name="price_data", tags=["PRICE"])
def generate_price_data():
    # 가격 데이터 생성
    dates = pd.date_range('2025-01-01', periods=30)
    prices = np.random.normal(100, 5, 30)
    return pd.DataFrame({'date': dates, 'price': prices})

@Node(name="volume_data", tags=["VOLUME"])
def generate_volume_data():
    # 거래량 데이터 생성
    dates = pd.date_range('2025-01-01', periods=30)
    volumes = np.random.normal(1000, 200, 30)
    return pd.DataFrame({'date': dates, 'volume': volumes})

# 상관관계 분석기 구현
def run_correlation_analyzer():
    # 분석기 객체 생성
    analyzer = Analyzer(name="correlation_analyzer")
    
    # 데이터 노드 추가
    analyzer.add_node(generate_price_data)
    analyzer.add_node(generate_volume_data)
    
    # 쿼리 노드 생성 및 추가 (PRICE 또는 VOLUME 태그를 가진 노드 검색)
    price_volume_qn = QueryNode(name="price_volume_query", tags=["PRICE", "VOLUME"], match_mode="OR")
    analyzer.query_nodes[price_volume_qn.name] = price_volume_qn
    
    # 상관관계 계산 노드
    @Node(name="correlation_calc")
    def calculate_correlation(price_volume_query):
        data_nodes = list(price_volume_query.values())
        
        # 데이터 합치기
        price_df = [df for df in data_nodes if 'price' in df.columns][0]
        volume_df = [df for df in data_nodes if 'volume' in df.columns][0]
        
        merged_df = pd.merge(price_df, volume_df, on='date')
        
        # 상관관계 계산
        correlation = merged_df['price'].corr(merged_df['volume'])
        return {
            'correlation': correlation,
            'p_value': 0.05,  # 간단한 예제이므로 고정값 사용
            'data_points': len(merged_df)
        }
    
    analyzer.add_node(calculate_correlation)
    
    # 분석기 실행 (로컬 모드)
    results = analyzer.execute(local=True)
    return results

if __name__ == "__main__":
    results = run_correlation_analyzer()
    print("분석 결과:", results)
    
    # 결과를 CSV로 내보내기 (외부 시각화 도구용)
    import pandas as pd
    pd.DataFrame([results]).to_csv("correlation_results.csv", index=False)
```

### 4.2 분석기 제출 및 활성화

```python
# examples/submit_analyzer.py
from qmtl.sdk import OrchestratorClient
import os

def read_analyzer_code(file_path):
    with open(file_path, "r") as f:
        return f.read()

if __name__ == "__main__":
    # Orchestrator 클라이언트 생성
    client = OrchestratorClient(
        base_url="http://localhost:8001",
    )
    
    # 분석기 코드 읽기
    analyzer_code = read_analyzer_code("examples/analyzer_example.py")
    
    # 분석기 제출
    analyzer_id = f"correlation_analyzer_v1_{os.getenv('USER', 'user')}"
    
    result = client.register_analyzer(
        analyzer_id=analyzer_id,
        analyzer_code=analyzer_code
    )
    
    print(f"분석기 제출 완료: {result['analyzer_id']}")
    print(f"쿼리 노드: {result['query_nodes']}")
    
    # 분석기 활성화
    activation_result = client.activate_analyzer(
        analyzer_id=analyzer_id,
        environment="production"
    )
    
    print(f"활성화 결과: {activation_result['success']}")
    
    # 분석 결과 조회
    time.sleep(5)  # 분석기 실행 대기
    results = client.get_analyzer_results(analyzer_id)
    print(f"분석 결과: {results['results']}")
```

## 5. Redis 히스토리 데이터 관리

### 5.1 히스토리 데이터 저장 및 조회

```python
# examples/redis_history.py
from qmtl.common.redis.redis_client import RedisClient
from qmtl.models.config import RedisSettings
import json
import time
import datetime

def timestamp():
    return datetime.datetime.now().isoformat()

async def run_redis_example():
    # Redis 클라이언트 생성
    settings = RedisSettings(
        host="localhost",
        port=6379,
        db=0
    )
    client = RedisClient(settings)
    
    # 노드 ID (예시)
    node_id = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"
    interval = "1h"
    
    # 히스토리 데이터 저장 (5개)
    for i in range(5):
        data = {
            "value": 100 + i * 10,
            "timestamp": timestamp(),
            "metadata": {"iteration": i}
        }
        key = f"node:{node_id}:history:{interval}"
        await client.lpush(key, json.dumps(data))
        await client.ltrim(key, 0, 99)  # 최대 100개 유지
        await client.expire(key, 3600 * 24 * 7)  # 7일 TTL
        time.sleep(1)
    
    # 히스토리 데이터 조회
    key = f"node:{node_id}:history:{interval}"
    data = await client.lrange(key, 0, -1)
    
    print(f"저장된 히스토리 데이터 ({len(data)}개):")
    for item in data:
        parsed = json.loads(item)
        print(f"  - 값: {parsed['value']}, 시간: {parsed['timestamp']}")
    
    # 특정 시간 범위 필터링 (클라이언트 측 필터링)
    one_hour_ago = (datetime.datetime.now() - datetime.timedelta(hours=1)).isoformat()
    filtered_data = [
        json.loads(item) for item in data
        if json.loads(item)["timestamp"] > one_hour_ago
    ]
    
    print(f"최근 1시간 데이터 ({len(filtered_data)}개):")
    for item in filtered_data:
        print(f"  - 값: {item['value']}, 시간: {item['timestamp']}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_redis_example())
```

## 6. 전체 워크플로우 통합 스크립트

아래는 설치부터 전략 개발, 제출, 활성화, 실행까지의 전체 워크플로우를 통합한 스크립트입니다.

```python
# examples/e2e_workflow.py
import os
import time
import asyncio
from qmtl.sdk import Pipeline, node, OrchestratorClient
from qmtl.models import IntervalSettings

# 1. 전략 정의
@node(tags=["data"])
def fetch_data() -> list:
    return [10, 20, 30, 40, 50]

@node(tags=["feature"])
def calculate_average(data: list) -> float:
    return sum(data) / len(data)

@node(tags=["signal"], interval_settings=IntervalSettings(interval="1h", period="1d"))
def generate_signal(avg: float) -> dict:
    return {"signal": avg > 30, "value": avg}

# 2. 로컬 실행 함수
def run_local():
    print("\n===== 로컬 실행 =====")
    pipeline = Pipeline(nodes=[fetch_data, calculate_average, generate_signal])
    result = pipeline.execute()
    print(f"로컬 실행 결과: {result}")
    return pipeline

# 3. 제출 및 활성화 함수
async def submit_and_activate(strategy_code):
    print("\n===== 전략 제출 및 활성화 =====")
    client = OrchestratorClient(base_url="http://localhost:8001")
    
    # 전략 제출
    strategy_id = "e2e_demo_strategy"
    version_id = f"{strategy_id}_v1_{int(time.time())}"
    
    result = await client.submit_strategy(
        strategy_id=strategy_id,
        version_id=version_id,
        strategy_code=strategy_code
    )
    
    print(f"전략 제출 완료: {result['version_id']}")
    print(f"등록된 노드: {[node['function_name'] for node in result['nodes']]}")
    
    # 전략 활성화
    activation_result = await client.activate_strategy(
        version_id=version_id,
        environment="production"
    )
    
    print(f"활성화 결과: {activation_result['success']}")
    
    return client, result['nodes']

# 4. 파이프라인 실행 함수
async def run_pipeline(client, nodes):
    print("\n===== 파이프라인 실행 =====")
    
    # 시그널 노드 ID 찾기
    signal_nodes = [node for node in nodes if node['function_name'] == 'generate_signal']
    if not signal_nodes:
        print("시그널 노드를 찾을 수 없습니다.")
        return
    
    signal_node_id = signal_nodes[0]['node_id']
    
    # 파이프라인 실행 트리거
    execution_result = await client.trigger_pipeline(
        node_ids=[signal_node_id],
        inputs={},
        execution_params={"timeout": 60}
    )
    
    pipeline_id = execution_result["execution_id"]
    print(f"파이프라인 실행 ID: {pipeline_id}")
    
    # 실행 상태 확인 (폴링)
    max_retries = 10
    for i in range(max_retries):
        status = await client.get_pipeline_status(pipeline_id)
        print(f"실행 상태: {status['status']}")
        
        if status["status"] in ["COMPLETED", "FAILED"]:
            if "result" in status:
                print(f"실행 결과: {status['result']}")
            break
            
        time.sleep(1)  # 1초 대기

# 5. 메인 함수
async def main():
    print("===== QMTL E2E 워크플로우 예제 =====")
    
    # 현재 파일의 코드 읽기
    with open(__file__, "r") as f:
        strategy_code = f.read()
    
    # 1. 로컬 실행
    pipeline = run_local()
    
    # 2. 전략 제출 및 활성화
    client, nodes = await submit_and_activate(strategy_code)
    
    # 3. 파이프라인 실행
    await run_pipeline(client, nodes)
    
    print("\n===== 워크플로우 완료 =====")

if __name__ == "__main__":
    asyncio.run(main())
```

## 7. 문제 해결 및 팁

### 7.1 일반적인 문제 해결

- **Neo4j 연결 오류**
  - 환경 변수(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)가 올바르게 설정되었는지 확인
  - `docker ps`로 Neo4j 컨테이너가 실행 중인지 확인
  - `make logs-neo4j`로 컨테이너 로그 확인

- **Redis 연결 오류**
  - 환경 변수(REDIS_HOST, REDIS_PORT, REDIS_DB)가 올바르게 설정되었는지 확인
  - Redis 컨테이너 상태 확인: `docker ps | grep redis`

- **전략 제출 오류**
  - 전략 코드 구문 오류 확인
  - Pydantic 모델 필드 충돌 확인 (schema, model 등)
  - 필요한 import 문이 포함되어 있는지 확인

### 7.2 개발 팁

- **노드 ID 디버깅**
  - 함수 코드가 변경되면 노드 ID도 변경됩니다. 디버깅 시 노드 ID 추적에 주의하세요.
  - 전략 제출 응답에서 노드 ID와 함수명 매핑을 저장해두면 유용합니다.

- **히스토리 데이터 관리**
  - 대용량 데이터의 경우 적절한 TTL과 max_items 설정이 중요합니다.
  - 자주 접근하는 데이터는 적절한 인덱싱이나 캐싱을 고려하세요.

- **환경별 전략 관리**
  - 개발/검증/운영 환경을 분리하여 안전하게 전략을 테스트하세요.
  - 각 환경마다 별도의 전략 버전을 활성화하는 것이 좋습니다. 