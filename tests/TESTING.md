# QMTL2 테스트 가이드

이 문서는 QMTL2 프로젝트의 테스트 환경 설정, 픽스처 사용법, 팩토리 클래스에 대한 가이드를 제공합니다.

## 목차
1. [테스트 환경 설정](#테스트-환경-설정)
2. [테스트 픽스처](#테스트-픽스처)
3. [팩토리 클래스](#팩토리-클래스)
4. [테스트 실행 방법](#테스트-실행-방법)
5. [테스트 작성 가이드라인](#테스트-작성-가이드라인)

## 테스트 환경 설정

### 사전 요구사항
- Python 3.8+
- Docker 및 Docker Compose
- 프로젝트 의존성 설치: `pip install -r requirements-dev.txt`

### 환경 변수 설정
`.env.test` 파일을 생성하여 필요한 환경 변수를 설정할 수 있습니다.

## 테스트 픽스처

### 데이터베이스 픽스처

#### `neo4j_session`
- **범위**: 세션
- **용도**: Neo4j 데이터베이스 클라이언트 제공
- **사용 예시**:
  ```python
  def test_neo4j_query(neo4j_session):
      result = neo4j_session.execute_query("RETURN 1 AS x")
      assert result[0]["x"] == 1
  ```

#### `neo4j_clean`
- **범위**: 함수
- **용도**: 각 테스트 전후 Neo4j 데이터 정리
- **의존성**: `neo4j_session`

#### `redis_session`
- **범위**: 세션
- **용도**: Redis 클라이언트 제공
- **사용 예시**:
  ```python
  def test_redis_operations(redis_session):
      redis_session.set('key', 'value')
      assert redis_session.get('key') == b'value'
  ```

#### `redis_clean`
- **범위**: 함수
- **용도**: 각 테스트 전후 Redis 데이터 정리
- **의존성**: `redis_session`

### 메시지 브로커 픽스처

#### `redpanda_session`
- **범위**: 세션
- **용도**: Redpanda (Kafka 호환) 브로커 주소 제공
- **사용 예시**:
  ```python
  from kafka import KafkaProducer
  
  def test_kafka_producer(redpanda_session):
      producer = KafkaProducer(bootstrap_servers=redpanda_session)
      # 테스트 코드...
  ```

#### `redpanda_clean`
- **범위**: 함수
- **용도**: 각 테스트 전후 Redpanda 토픽 정리
- **의존성**: `redpanda_session`

### Gateway 픽스처

#### `gateway_session`
- **범위**: 세션
- **용도**: Gateway 서비스 기본 URL 제공
- **사용 예시**:
  ```python
  import requests
  
  def test_gateway_health(gateway_session):
      response = requests.get(f"{gateway_session}/health")
      assert response.status_code == 200
  ```

#### `gateway_client`
- **범위**: 함수
- **용도**: Gateway API 요청을 위한 HTTP 클라이언트 제공
- **의존성**: `gateway_session`

#### `authenticated_gateway_client`
- **범위**: 함수
- **용도**: 인증된 Gateway API 클라이언트 제공
- **의존성**: `gateway_client`

## 팩토리 클래스

### 데이터 생성 팩토리

테스트 데이터 생성을 위한 팩토리 함수들은 `tests/factories.py`에 정의되어 있습니다.

#### `create_datanode`
```python
def create_datanode(
    node_id: str = None,
    node_type: str = "RAW",
    tags: List[str] = None,
    interval: IntervalEnum = IntervalEnum.MINUTE,
    period: int = 5,
    max_history: int = 100
) -> DataNode:
    """
    DataNode 생성 팩토리 함수
    
    Args:
        node_id: 노드 ID (기본값: 랜덤 UUID)
        node_type: 노드 유형 (기본값: "RAW")
        tags: 노드 태그 목록
        interval: 데이터 수집 주기
        period: 주기 간격
        max_history: 최대 보관 기간
        
    Returns:
        생성된 DataNode 인스턴스
    """
    # 구현 내용...
```

## 테스트 실행 방법

### 전체 테스트 실행
```bash
pytest
```

### 특정 테스트 모듈 실행
```bash
pytest tests/unit/core/test_node_management.py
```

### 테스트 커버리지 리포트 생성
```bash
pytest --cov=qmtl --cov-report=html
```

## 테스트 작성 가이드라인

1. **테스트 명명 규칙**:
   - 테스트 함수명은 `test_`로 시작
   - 테스트 클래스는 `Test` 접두사 사용

2. **픽스처 사용 권장사항**:
   - 데이터베이스 의존적인 테스트는 반드시 `neo4j_clean` 또는 `redis_clean` 픽스처 사용
   - 외부 서비스 연동 테스트는 `gateway_session`과 같은 픽스처 활용

3. **테스트 격리**:
   - 각 테스트는 독립적으로 실행 가능해야 함
   - 테스트 간 상태 공유 지양

4. **테스트 데이터 관리**:
   - 테스트 데이터는 팩토리 함수를 사용하여 생성
   - 반복되는 데이터 생성 로직은 픽스처로 분리

5. **성능 고려사항**:
   - 데이터베이스 픽스처는 세션 범위로 사용하여 테스트 실행 시간 단축
   - 대용량 데이터 테스트는 별도의 테스트 모듈로 분리

## DAG Manager 테스트 픽스처/팩토리

DAG Manager 관련 테스트에서 주로 사용하는 pytest fixture와 팩토리 함수는 아래와 같습니다.

| 이름                  | 범위   | 계층      | 주요 사용처                | 설명/반환 타입                      |
|----------------------|--------|-----------|---------------------------|-------------------------------------|
| `neo4j_session`      | session| 통합/E2E  | tests/conftest.py, e2e    | Neo4j Docker 컨테이너 기반 클라이언트 (proto 기반 서비스 테스트)
| `neo4j_clean`        | function| 단위/통합 | tests/conftest.py, unit   | 테스트 전후 Neo4j DB 정리           |
| `create_datanode_metadata` | function | 단위/통합 | tests/e2e/factories.py   | DataNode proto 객체 생성 팩토리     |
| `create_pipeline_definition` | function | 단위/통합 | tests/e2e/factories.py   | PipelineDefinition proto 객체 생성  |

### 예시: DataNode proto 팩토리 사용
```python
from tests.e2e.factories import create_datanode_metadata

def test_create_node(neo4j_session):
    node = create_datanode_metadata(node_type="RAW")
    # proto 기반 서비스에 node 전달 및 검증
```

### 예시: Neo4j DB 픽스처 사용
```python
def test_neo4j_query(neo4j_session, neo4j_clean):
    neo4j_session.execute_query("CREATE (:TestNode {foo: 1})")
    result = neo4j_session.execute_query("MATCH (n:TestNode) RETURN n.foo AS foo")
    assert result[0]["foo"] == 1
```

> **참고:**
> - 모든 proto 기반 팩토리 함수는 실제 서비스/테스트에서 protobuf 메시지 객체를 직접 반환합니다.
> - fixture/factory는 테스트 계층(단위/통합/E2E)에 따라 적절히 선택하여 사용하세요.
> - 추가 팩토리 함수 및 fixture는 `tests/e2e/factories.py`, `tests/conftest.py` 참고.

## Gateway 테스트 픽스처/팩토리

Gateway 서비스 관련 테스트에서 주로 사용하는 pytest fixture와 팩토리 함수는 아래와 같습니다.

| 이름                        | 범위     | 계층      | 주요 사용처                   | 설명/반환 타입                                |
|----------------------------|----------|-----------|------------------------------|---------------------------------------------|
| `gateway_session`          | session  | 통합/E2E  | tests/conftest.py, e2e       | Gateway 서비스 기본 URL                      |
| `gateway_client`           | function | 통합/E2E  | tests/conftest.py, e2e       | 인증되지 않은 Gateway API 클라이언트          |
| `authenticated_gateway_client` | function | 통합/E2E | tests/conftest.py, e2e    | 인증된 Gateway API 클라이언트                |
| `create_strategy_metadata` | function | 단위/통합 | tests/e2e/factories.py      | StrategyMetadata proto 객체 생성 팩토리      |
| `create_datanode_metadata` | function | 단위/통합 | tests/e2e/factories.py      | DataNode proto 객체 생성 팩토리              |
| `create_pipeline_definition` | function | 단위/통합 | tests/e2e/factories.py    | PipelineDefinition proto 객체 생성 팩토리    |

### 예시: Gateway 클라이언트 픽스처 사용
```python
def test_gateway_api(authenticated_gateway_client):
    # 인증된 클라이언트로 API 요청
    response = authenticated_gateway_client.get("/api/v1/health")
    assert response.status_code == 200
```

### 예시: 전략 팩토리 사용
```python
from tests.e2e.factories import create_strategy_metadata

def test_strategy_registration(authenticated_gateway_client):
    # 전략 객체 생성
    strategy = create_strategy_metadata(
        strategy_name="test_strategy", 
        description="Test strategy",
        version="1.0.0"
    )
    
    # Gateway API에 전략 등록
    response = authenticated_gateway_client.post(
        "/api/v1/strategies",
        data=strategy.SerializeToString(),
        headers={"Content-Type": "application/x-protobuf"}
    )
    assert response.status_code == 200
```

### Gateway 테스트 템플릿 사용

Gateway 서비스는 라운드트립 테스트 및 Golden 테스트를 위한 재사용 가능한 템플릿을 제공합니다.

#### 라운드트립 템플릿
`tests/templates/gateway_roundtrip_template.py`에 정의된 함수들을 사용하여 Protobuf 메시지의 라운드트립 테스트를 수행할 수 있습니다.

```python
from tests.templates.gateway_roundtrip_template import basic_roundtrip_test

def test_roundtrip(authenticated_gateway_client):
    # Protobuf 메시지 생성
    strategy = create_strategy_metadata(strategy_name="roundtrip_test")
    
    # 라운드트립 테스트 수행
    response = basic_roundtrip_test(
        message_obj=strategy,
        client_fixture=authenticated_gateway_client,
        endpoint="/api/v1/strategies",
        response_cls=strategy_pb2.StrategyRegistrationResponse
    )
    assert response.success
```

#### Golden 파일 템플릿
`tests/templates/gateway_golden_template.py`에 정의된 클래스와 함수들을 사용하여 Protobuf 메시지의 Golden 테스트를 수행할 수 있습니다.

```python
from tests.templates.gateway_golden_template import GoldenFileHandler, verify_golden_file

def test_golden(authenticated_gateway_client):
    # Golden 파일 핸들러 생성
    golden_handler = GoldenFileHandler()
    
    # Protobuf 메시지 생성
    strategy = create_strategy_metadata(strategy_name="golden_test")
    
    # Golden 파일 비교
    is_match = verify_golden_file(
        proto_obj=strategy,
        name="test_strategy",
        golden_handler=golden_handler,
        update_mode=os.environ.get("UPDATE_GOLDEN_FILES") == "1"
    )
    assert is_match, "Golden 파일과 일치하지 않음"
```
