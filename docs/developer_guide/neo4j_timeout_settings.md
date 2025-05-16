# Neo4j 클라이언트 설정 가이드

## 타임아웃 및 재시도 설정

Neo4j 드라이버를 사용할 때는 적절한 타임아웃과 재시도 설정이 중요합니다. 특히 테스트 환경에서는 더욱 중요합니다.

### 권장 설정

```python
from neo4j import GraphDatabase

# 권장 설정값
# 1. connection_timeout: 연결 타임아웃 (기본값: 30초)
# 2. max_transaction_retry_time: 트랜잭션 재시도 최대 시간 (기본값: 30초)
# 3. connection_acquisition_timeout: 연결 획득 타임아웃 (기본값: 60초)

driver = GraphDatabase.driver(
    uri, 
    auth=(username, password),
    connection_timeout=5,                # 5초로 줄임
    max_transaction_retry_time=10000,    # 10초로 줄임 (밀리초 단위)
    connection_acquisition_timeout=10.0  # 10초로 줄임
)
```

### 테스트 환경 권장 설정

테스트 환경에서는 더 짧은 타임아웃을 설정하는 것이 hang을 방지하는 데 도움이 됩니다:

```python
driver = GraphDatabase.driver(
    uri, 
    auth=(username, password),
    connection_timeout=3,               # 3초
    max_transaction_retry_time=5000,    # 5초 (밀리초 단위)
    connection_acquisition_timeout=5.0   # 5초
)
```

### 세션과 트랜잭션 타임아웃

세션과 트랜잭션 레벨에서도 타임아웃을 설정할 수 있습니다:

```python
# 세션 타임아웃 설정
with driver.session(connection_timeout=5) as session:
    # 트랜잭션 타임아웃 설정
    with session.begin_transaction(timeout=5000) as tx:
        # 트랜잭션 작업 수행
        pass
```

## 재시도 전략

### 기본 제공 재시도 전략

Neo4j 드라이버는 일시적인 오류에 대해 자동으로 재시도합니다:

```python
from neo4j.exceptions import ServiceUnavailable

def run_with_retry(driver, cypher, params=None):
    with driver.session() as session:
        try:
            return session.run(cypher, params)
        except ServiceUnavailable:
            # Neo4j 드라이버가 자동으로 재시도 처리
            pass
```

### 수동 재시도 구현 (테스트용)

테스트에서는 명시적인 재시도 로직을 구현하는 것이 도움이 될 수 있습니다:

```python
import time
from neo4j.exceptions import ServiceUnavailable

def execute_with_retry(driver, cypher, params=None, max_retries=3, retry_delay=1):
    retries = 0
    while retries < max_retries:
        try:
            with driver.session() as session:
                return session.run(cypher, params).data()
        except ServiceUnavailable:
            retries += 1
            if retries == max_retries:
                raise
            time.sleep(retry_delay)
```

## QMTL2 프로젝트에서의 구현

QMTL2 프로젝트에서는 다음과 같이 Neo4j 클라이언트를 설정하는 것이 좋습니다:

```python
# src/qmtl/common/db/neo4j_client.py

from neo4j import GraphDatabase
import os
from typing import Optional

class Neo4jClient:
    def __init__(
        self, 
        uri: str, 
        username: str, 
        password: str,
        connection_timeout: int = 5,
        max_transaction_retry_time: int = 10000,
        connection_acquisition_timeout: float = 10.0
    ):
        self._driver = GraphDatabase.driver(
            uri, 
            auth=(username, password),
            connection_timeout=connection_timeout,
            max_transaction_retry_time=max_transaction_retry_time,
            connection_acquisition_timeout=connection_acquisition_timeout
        )
        
    # ...나머지 메서드...
```

### 환경에 따른 타임아웃 설정

환경에 따라 다른 타임아웃 설정을 사용할 수 있습니다:

```python
# 환경 변수를 사용한 타임아웃 설정
connection_timeout = int(os.getenv("NEO4J_CONNECTION_TIMEOUT", 5))
max_transaction_retry_time = int(os.getenv("NEO4J_MAX_TRANSACTION_RETRY_TIME", 10000))
connection_acquisition_timeout = float(os.getenv("NEO4J_CONNECTION_ACQUISITION_TIMEOUT", 10.0))

client = Neo4jClient(
    uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    username=os.getenv("NEO4J_USER", "neo4j"),
    password=os.getenv("NEO4J_PASSWORD", "password"),
    connection_timeout=connection_timeout,
    max_transaction_retry_time=max_transaction_retry_time,
    connection_acquisition_timeout=connection_acquisition_timeout
)
```

## 테스트에서의 타임아웃 설정 가이드

### conftest.py에서의 설정

테스트 환경에서는 `conftest.py`를 통해 짧은 타임아웃을 갖는 Neo4j 클라이언트를 설정할 수 있습니다:

```python
# tests/conftest.py

@pytest.fixture
def neo4j_client():
    client = Neo4jClient(
        uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        username=os.getenv("NEO4J_USER", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "password"),
        connection_timeout=3,  # 짧은 타임아웃 설정
        max_transaction_retry_time=5000,
        connection_acquisition_timeout=5.0
    )
    yield client
    client.close()
```

### pytest-timeout 사용

테스트 자체에 타임아웃을 설정하는 것도 테스트 실행이 중단되는 것을 방지하는 데 도움이 됩니다:

```python
# tests/integration/test_neo4j.py

@pytest.mark.timeout(10)  # 10초 타임아웃 설정
def test_neo4j_connection(neo4j_client):
    # 테스트 코드
    pass
```

## 문제 해결 및 모범 사례

### 타임아웃 문제 해결 체크리스트

Neo4j 타임아웃 관련 문제가 발생했을 때 확인해야 할 사항:

1. Neo4j 컨테이너가 정상적으로 실행 중인지 확인
2. 네트워크 설정 확인 (특히 Docker 네트워크)
3. 리소스 사용량 확인 (메모리, CPU)
4. 로그 확인으로 구체적인 오류 메시지 확인
5. 타임아웃 값이 환경에 적합한지 확인 (개발 환경과 테스트 환경 구분)

### 모범 사례

1. **적절한 타임아웃 값 설정**: 환경에 따라 다른 값 사용
2. **명시적인 예외 처리**: Neo4j 관련 예외를 명확하게 처리
3. **로깅**: 타임아웃과 재시도 관련 로그 기록
4. **헬스체크**: Neo4j 연결을 주기적으로 확인하는 헬스체크 구현
5. **풀링**: 필요한 경우 Neo4j 연결 풀 사용 고려
6. **테스트 환경 분리**: 테스트 전용 Neo4j 인스턴스 사용
7. **모니터링**: 프로덕션 환경에서 Neo4j 연결 모니터링

## 결론

적절한 타임아웃 설정은 Neo4j를 사용하는 애플리케이션의 안정성과 견고성을 높이는 데 중요합니다. 특히 테스트 환경에서는 짧은 타임아웃을 설정하여 테스트가 불필요하게 오래 실행되는 것을 방지할 수 있습니다.
