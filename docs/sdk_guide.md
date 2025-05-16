# QMTL SDK Guide

이 문서는 QMTL 2.0 SDK의 공통 기능, 시각화/알림 연동, 분석기(Analyzer) 및 일반 전략 코드 작성법을 안내합니다.

## 1. SDK 공통 기능
- 파이프라인, 노드, QueryNode, Analyzer 등은 모두 Pydantic v2 스타일 모델로 정의
- 직렬화/역직렬화, 실행 엔진(Local/Parallel), 상태 관리, 컨테이너 빌드, K8s Job 템플릿 등 지원

## 2. 시각화/알림 연동 원칙
- QMTL SDK는 시각화/알림 기능을 내장하지 않음
- 결과를 외부 시스템(Grafana, Alertmanager 등)과 연동하여 처리
- SDK는 결과 포맷 변환/Export 유틸리티만 제공 (예: to_grafana_format, model_dump_json 등)

## 3. 결과 Export/포맷 변환 예시

### 3.1 Grafana 연동용 포맷 변환
```python
from qmtl.sdk.models import QueryNodeResult
results = analyzer.execute(local=True)
# 예시: Grafana에서 읽을 수 있는 JSON/CSV로 변환
import pandas as pd
df = pd.DataFrame(results)
df.to_csv("results.csv", index=False)
```

### 3.2 Alertmanager/Webhook 연동
```python
import requests
results = analyzer.execute(local=True)
for row in results:
    if row["score"] > 0.9:
        requests.post("http://alertmanager/api/alert", json=row)
```

## 4. 분석기(Analyzer)와 일반 전략 코드의 차이
- 분석기는 QueryNode 기반 전략 코드의 한 형태 (별도 엔티티 아님)
- 시각화/알림은 분석기/일반 전략 코드 모두에서 외부 연동 방식으로 동일하게 처리
- SDK 공통 기능(Export, 포맷 변환 등)은 모든 전략 코드에서 사용 가능

## 5. 참고
- 자세한 예제 및 연동법은 [analyzer_guide.md](analyzer_guide.md) 참고
- 모든 모델/헬퍼는 Pydantic v2 스타일로 작성되어야 하며, BaseModel 내장 속성과 충돌하지 않도록 주의

## 6. 노드/쿼리노드/소스노드/셀렉터 아키텍처 및 사용법

### 6.1 Node/SourceNode 아키텍처 원칙
- **모든 Node, SourceNode, DataNode는 반드시 하나 이상의 interval(주기) 설정이 필요합니다.**
  - interval이 누락된 경우 예외가 발생하며, stream_settings 또는 interval_settings에 interval을 명시해야 합니다.
- **모든 Node는 반드시 하나 이상의 업스트림(upstreams)을 가져야 합니다.**
  - 외부 입력, 원천 데이터(파일/DB/API 등)는 일반 Node로 직접 구현하지 않고 **SourceNode**로 추상화해야 합니다.
- **SourceNode**는 SourceProcessor(예: fetch 메서드 구현 객체)를 받아 파이프라인에 데이터 소스처럼 추가할 수 있습니다.
- 일반 Node는 반드시 upstreams를 지정해야 하며, 업스트림이 없는 경우 ValueError가 발생합니다.

#### 예시: SourceNode 사용법 (interval 필수)
```python
from qmtl.sdk.node import SourceNode, SourceProcessor
from qmtl.models import IntervalSettings, NodeStreamSettings

class MyFileSource(SourceProcessor):
    def fetch(self):
        return [1, 2, 3]

source = MyFileSource()
source_node = SourceNode(
    name="file_source",
    source=source,
    stream_settings=NodeStreamSettings(intervals={"1d": IntervalSettings(interval="1d")})
)
```

### 6.2 QueryNode와 selector 체이닝/샘플링
- **QueryNode**는 태그, 인터벌, 피리어드 등 조건에 따라 실제 노드 집합을 동적으로 선택하는 특수 노드입니다.
- QueryNode는 **result_selectors** 필드에 여러 개의 QueryNodeResultSelector를 지정할 수 있습니다.
- Pipeline.execute에서 별도의 selectors 인자를 넘기지 않아도, QueryNode에 직접 지정한 selector가 자동으로 적용됩니다.
- selector는 체이닝/샘플링/필터링 등 다양한 모드를 지원합니다.

#### QueryNodeResultSelector 주요 mode
- `list`: 필터링된 노드 전체 반환(기본값)
- `batch`: 지정한 batch_size만큼 묶어서 반환
- `random`: sample_size만큼 무작위 샘플링
- `filter`: filter_meta 조건에 맞는 노드만 반환

#### 예시: QueryNode + selector 체이닝/샘플링
```python
from qmtl.sdk.node import QueryNode
from qmtl.sdk.models import QueryNodeResultSelector

# FEATURE 태그 + 1d interval 노드 중 1개만 무작위 샘플링
qnode = QueryNode(
    name="q1",
    tags=["FEATURE"],
    interval="1d",
    result_selectors=[
        QueryNodeResultSelector(mode="random", sample_size=1),
        QueryNodeResultSelector(mode="filter", filter_meta={"stream_settings": {"intervals": {"1d": {}}}}),
    ],
    upstreams=["_dummy"],
)
```

### 6.3 Node/QueryNode/SourceNode 생성 예시 및 차이점
- **일반 Node**: 반드시 upstreams 지정 필요
- **SourceNode**: 업스트림 없이 데이터 소스 역할
- **QueryNode**: 태그/조건 기반 동적 노드 선택 + selector 체이닝 지원

#### 예시 코드
```python
from qmtl.sdk.node import Node, SourceNode, QueryNode, SourceProcessor
from qmtl.sdk.models import QueryNodeResultSelector

# SourceNode 예시
class MySource(SourceProcessor):
    def fetch(self):
        return 100
source_node = SourceNode(name="src", source=MySource())

# 일반 Node 예시
node = Node(name="n1", fn=lambda x: x + 1, upstreams=["src"])

# QueryNode + selector 예시
qnode = QueryNode(
    name="q1",
    tags=["FEATURE"],
    interval="1d",
    result_selectors=[QueryNodeResultSelector(mode="random", sample_size=1)],
    upstreams=["_dummy"],
)
```

### 6.4 아키텍처 일관성 및 테스트/실전 적용
- 모든 파이프라인/분석기/테스트 코드에서 **업스트림 없는 데이터 소스는 반드시 SourceNode로 구현**해야 하며, 일반 Node는 업스트림 필수입니다.
- QueryNode의 selector는 쿼리노드에 직접 지정하면 자동 적용되어, 파이프라인/분석기/테스트에서 일관된 방식으로 동작합니다.
- selector 체이닝/샘플링/필터링은 QueryNodeResultSelector의 mode 조합으로 자유롭게 확장 가능합니다.

---

이 구조를 따르면, 실전 파이프라인/분석기/테스트 코드 모두에서 아키텍처 원칙과 일관성을 유지할 수 있습니다.
