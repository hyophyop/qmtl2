# QMTL Pydantic 모델 목록 및 protobuf 변환 대상 선정 (NG-2-1)

## 1. Pydantic 모델 전체 목록 (src/qmtl/models/)

- **datanode.py**
  - NodeTags
  - IntervalSettings
  - NodeStreamSettings
  - DataNode
  - TopoSortResult
  - DAGNodeDependency
  - DAGNode
  - DAGEdge

- **strategy.py**
  - StrategyMetadata
  - SharedStrategyModel
  - StrategyVersion
  - NodeSnapshot
  - StrategySnapshot

- **k8s.py**
  - K8sEnvVar
  - K8sContainerSpec
  - K8sJobSpec
  - K8sJobTemplate

- **analyzer.py**
  - AnalyzerDefinition
  - AnalyzerMetadata
  - AnalyzerActivateRequest
  - AnalyzerResult

- **callback.py** (DEPRECATED, 이미 protobuf 대체)
  - NodeCallbackRequest
  - NodeCallbackResponse
  - NodeCallbackEvent

- **event.py** (DEPRECATED, 이미 protobuf 대체)
  - NodeStatusEvent
  - PipelineStatusEvent
  - AlertEvent

- **status.py**
  - NodeErrorDetail
  - NodeStatus
  - PipelineStatus
  - ExecutionDetail

- **template.py**
  - TemplateMetadata
  - NodeTemplate
  - StrategyTemplate
  - DAGTemplate
  - TemplatePermission

- **config.py**
  - RedisSettings
  - EnvConfig
  - Settings

---

## 2. protobuf 변환 우선 대상 선정

### 최우선 변환 대상 (API/브로커/테스트 등에서 직렬화 필요)
- DataNode, NodeTags, IntervalSettings, NodeStreamSettings, TopoSortResult, DAGNode, DAGEdge, DAGNodeDependency
- StrategyMetadata, StrategyVersion, NodeSnapshot, StrategySnapshot
- NodeStatus, PipelineStatus, NodeErrorDetail, ExecutionDetail
- AnalyzerDefinition, AnalyzerMetadata, AnalyzerResult
- NodeCallbackRequest, NodeCallbackResponse, NodeCallbackEvent (이미 protobuf 존재)
- NodeStatusEvent, PipelineStatusEvent, AlertEvent (이미 protobuf 존재)
- TemplateMetadata, NodeTemplate, StrategyTemplate, DAGTemplate

### 내부 설정/환경 관련(변환 필요성 낮음)
- RedisSettings, EnvConfig, Settings, K8s* (내부 infra/설정용)

---

> NG-2-1: 기존 models/ 내 Pydantic 모델 목록화 및 protobuf로 변환 대상 선정 완료 (2025-05-20)
