# QMTL Analyzer Guide

이 문서는 QMTL 2.0에서 분석기(Analyzer) 코드를 작성하고, 결과를 외부 시각화/알림 플랫폼과 연동하는 방법을 안내합니다.

## 1. 분석기(Analyzer)란?
- 분석기는 QueryNode 기반 전략 코드의 한 형태입니다.
- 별도의 엔티티가 아니라, QueryNode/AnalyzerNode를 활용한 전략 코드로 구현합니다.
- 분석기 코드에서는 시각화/알림을 직접 호출하지 않고, 결과 반환/저장에 집중합니다.

## 2. 분석기 코드 예시 (시각화/알림 없음)

```python
from qmtl.sdk.analyzer import Analyzer
from qmtl.sdk.node import Node, QueryNode

n1 = Node(name="n1", fn=lambda: 1, tags=["A", "B"])
n2 = Node(name="n2", fn=lambda: 2, tags=["A", "C"])
n3 = Node(name="n3", fn=lambda: 3, tags=["B", "C"])

analyzer = Analyzer(name="test-analyzer")
analyzer.add_node(n1)
analyzer.add_node(n2)
analyzer.add_node(n3)

qn = QueryNode(name="q1", tags=["A", "B"])
analyzer.query_nodes[qn.name] = qn

results = analyzer.execute(local=True)
print(results)
```

- 분석기 코드는 결과만 반환/저장하며, 시각화/알림은 외부 시스템에서 처리합니다.

## 3. 외부 시각화/알림 연동 예시

QMTL은 시각화/알림 기능을 내장하지 않으며, 결과를 외부 플랫폼(Grafana, Prometheus 등)과 연동하여 처리합니다.

### 3.1 Grafana 연동 예시
- QMTL 분석 결과를 파일/DB/메시지 큐 등으로 Export
- Grafana에서 해당 데이터를 데이터 소스로 연결하여 시각화

```python
# 예시: 분석 결과를 CSV로 저장
import pandas as pd
results = analyzer.execute(local=True)
df = pd.DataFrame(results)
df.to_csv("analyzer_results.csv", index=False)
# Grafana에서 CSV/DB를 데이터 소스로 연결
```

### 3.2 Alertmanager 연동 예시
- QMTL 결과를 HTTP/Webhook 등으로 외부 알림 시스템에 전달

```python
import requests
results = analyzer.execute(local=True)
for row in results:
    if row["score"] > 0.9:
        requests.post("http://alertmanager/api/alert", json=row)
```

## 4. 참고
- 시각화/알림 연동은 QMTL 외부에서 처리하며, QMTL SDK는 결과 포맷 변환/Export 유틸리티만 제공합니다.
- 자세한 연동 방법은 각 플랫폼(Grafana, Prometheus 등) 공식 문서를 참고하세요.
