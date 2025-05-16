# QMTL 사용자 가이드

## 1. 소개 및 개요
QMTL은 전략 기반 데이터 파이프라인 및 분석 시스템을 쉽고 일관되게 구축할 수 있는 SDK 및 서비스입니다. 본 가이드는 QMTL SDK의 설치, 사용법, 전략 작성, 실전 예제 등을 안내합니다.

## 2. 설치 및 환경설정

### 2.1 의존성 설치
```bash
uv pip install qmtl-sdk
```

### 2.2 환경 변수 설정 예시
```bash
export QMTL_ENV=dev
export NEO4J_URI=bolt://localhost:7687
export REDIS_HOST=localhost
export REDIS_PORT=6379
```

## 3. SDK 기본 사용법

### 3.1 파이프라인/노드 기본 구조
```python
from qmtl.sdk import Pipeline, Node

# 노드 함수 정의
def my_node_func(x: int) -> int:
    return x + 1

# 노드 등록
node = Node(func=my_node_func, name="increment")

# 파이프라인 생성
pipeline = Pipeline(nodes=[node])

# 실행
result = pipeline.execute(inputs={"increment": 1})
print(result)
```

## 4. 전략/노드 작성 가이드

### 4.1 Pydantic v2 스타일 모델 사용
- 모든 데이터 구조는 Pydantic 모델로 정의
- BaseModel 내장 속성과 충돌하는 필드명 사용 금지(예: schema → data_format)

### 4.2 노드 데코레이터 활용
```python
from qmtl.sdk import node

@node(tags=["feature"])
def feature_node(data: list[int]) -> int:
    return sum(data)
```

### 4.3 태그/인터벌/스트림 설정 예시
```python
from qmtl.models import IntervalSettings

@node(tags=["signal"], interval_settings=IntervalSettings(interval="1h", period="1d"))
def signal_node(data: list[int]) -> float:
    return max(data)
```

> ⚠️ 모든 Node, SourceNode, DataNode는 반드시 하나 이상의 interval(주기) 설정이 필요합니다. interval이 누락된 경우 예외가 발생합니다.

## 5. 실전 예제/튜토리얼

### 5.1 전략 전체 예제
```python
from qmtl.sdk import Pipeline, node
from qmtl.models import IntervalSettings

@node(tags=["feature"], interval_settings=IntervalSettings(interval="1d"))
def feature(data: list[int]) -> int:
    return sum(data)

@node(tags=["signal"], interval_settings=IntervalSettings(interval="1h", period="1d"))
def signal(x: int) -> float:
    return float(x) / 10

pipeline = Pipeline(nodes=[feature, signal])
result = pipeline.execute(inputs={"feature": [1,2,3]})
print(result)
```

## 6. FAQ 및 문제해결
- Q: Pydantic 모델 필드명 충돌 오류가 발생합니다.
  - A: schema, model 등 내장 속성과 충돌하지 않는 이름을 사용하세요.
- Q: Redis/Neo4j 연결 오류가 발생합니다.
  - A: 환경변수 및 컨테이너 상태를 점검하세요.
- Q: Node/SourceNode/파이프라인 생성 시 interval이 없다는 오류가 발생합니다.
  - A: 모든 노드에는 반드시 stream_settings 또는 interval_settings에 interval을 명시해야 합니다.

## 7. 참고 자료/링크
- [공식 문서](https://github.com/your-org/qmtl)
- [API 문서](./generated/api.md)
- [SDK 가이드](./sdk_guide.md)
- [분석기 가이드](./analyzer_guide.md) 