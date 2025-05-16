# QMTL API 문서 (자동 생성)

**마지막 업데이트:** 2025-05-12
**문서 버전:** 1.1.0
**QMTL 버전:** 2.0.0

> 이 문서는 QMTL 2.0 Registry 및 Orchestrator API 엔드포인트에 대한 상세 정보를 제공합니다. 각 엔드포인트의 목적, 파라미터, 요청/응답 형식과 예시를 포함합니다.

# Registry API 문서

Registry API는 노드, 전략, 활성화 상태 등의 중앙 저장소 역할을 하는 Registry 서비스의 인터페이스입니다.

**기본 URL:** `http://localhost:8000`
**버전:** 0.1.0

## `GET /`

- **설명**: 서비스 헬스 체크
- **응답**: 200 OK
- **응답 예시**:
  ```json
  {
    "status": "healthy",
    "version": "0.1.0"
  }
  ```

## `POST /v1/registry/nodes`

- **설명**: 데이터 노드 등록 - 파이프라인 내 노드를 Registry에 등록합니다
- **RequestBody**: 있음 (필수)
- **응답**: 200 OK, 422 Unprocessable Entity

**요청 예시**:
```json
{
  "node": {
    "node_id": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
    "type": "FEATURE",
    "data_format": {"type": "csv"},
    "params": {"window": 5},
    "dependencies": ["f1e2d3c4b5a6f1e2d3c4b5a6f1e2d3c4"],
    "ttl": 3600,
    "tags": {
      "predefined": ["FEATURE", "ANALYZER"],
      "custom": ["price", "indicator"]
    },
    "interval_settings": {
      "interval": "1h", 
      "period": "7d",
      "max_history": 100
    }
  }
}
```

**응답 예시**:
```json
{
  "node_id": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"
}
```

**오류 응답 예시** (422):
```json
{
  "detail": "Invalid node_id format. Expected 32 character hex string."
}
```

## `GET /v1/registry/nodes/leaf-nodes`

- **설명**: 의존성이 없는(Zero-dep) 노드 목록 조회
- **응답**: 200 OK

**응답 예시**:
```json
{
  "nodes": [
    {
      "node_id": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
      "type": "RAW",
      "data_format": {"type": "csv"},
      "dependencies": [],
      "tags": {
        "predefined": ["RAW"],
        "custom": ["price"]
      }
    }
  ]
}
```

## `GET /v1/registry/nodes/by-tags`

- **설명**: 태그 및 인터벌 기준으로 노드 필터링 조회
- **파라미터**:
  - `tags`: 필터링할 태그 목록 (쉼표로 구분, 예: FEATURE,SIGNAL)
  - `interval`: 필터링할 인터벌 (예: 1h, 1d)
  - `period`: 필터링할 피리어드 (예: 7d, 1m)
  - `match_mode`: 태그 일치 모드 (AND, OR, 기본값: OR)
- **응답**: 200 OK, 422 Unprocessable Entity

**요청 예시**:
```
GET /v1/registry/nodes/by-tags?tags=FEATURE,price&interval=1h&match_mode=AND
```

**응답 예시**:
```json
{
  "nodes": [
    {
      "node_id": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
      "type": "FEATURE",
      "data_format": {"type": "csv"},
      "dependencies": ["f1e2d3c4b5a6f1e2d3c4b5a6f1e2d3c4"],
      "tags": {
        "predefined": ["FEATURE"],
        "custom": ["price"]
      },
      "interval_settings": {
        "interval": "1h", 
        "period": "7d"
      }
    }
  ]
}
```

## `GET /v1/registry/nodes/{node_id}`

- **설명**: 특정 노드 조회
- **파라미터**: 
  - `node_id`: 조회할 노드 ID (필수)
- **응답**: 200 OK, 422 Unprocessable Entity

**응답 예시**:
```json
{
  "node": {
    "node_id": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
    "type": "FEATURE",
    "data_format": {"type": "csv"},
    "params": {"window": 5},
    "dependencies": ["f1e2d3c4b5a6f1e2d3c4b5a6f1e2d3c4"],
    "tags": {
      "predefined": ["FEATURE"],
      "custom": ["price"]
    },
    "interval_settings": {
      "interval": "1h", 
      "period": "7d"
    }
  }
}
```

## `DELETE /v1/registry/nodes/{node_id}`

- **설명**: 특정 노드 삭제
- **파라미터**: 
  - `node_id`: 삭제할 노드 ID (필수)
- **응답**: 200 OK, 422 Unprocessable Entity

**응답 예시**:
```json
{
  "success": true,
  "message": "Node deleted successfully"
}
```

## `GET /v1/registry/strategies`

- 설명: List Strategies
- 응답: 200

## `POST /v1/registry/strategies`

- 설명: Register Strategy
- RequestBody: 있음
- 응답: 200, 422

## `GET /v1/registry/strategies/{version_id}`

- 설명: Get Strategy
- 파라미터: ['version_id']
- 응답: 200, 422

## `POST /v1/registry/strategies/{version_id}/activate`

- 설명: Activate Strategy
- 파라미터: ['version_id']
- 응답: 200, 422

## `POST /v1/registry/strategies/{version_id}/deactivate`

- 설명: Deactivate Strategy
- 파라미터: ['version_id']
- 응답: 200, 422

## `GET /v1/registry/strategies/{version_id}/activation-history`

- 설명: Get Activation History
- 파라미터: ['version_id']
- 응답: 200, 422

## `POST /v1/registry/gc/run`

- 설명: Run Gc
- 응답: 200

## `GET /v1/registry/status`

- 설명: Get Status
- 응답: 200

---

# Orchestrator API 문서

Orchestrator API는 전략 제출, 활성화, 파이프라인 실행을 관리하는 Orchestrator 서비스의 인터페이스입니다.

**기본 URL:** `http://localhost:8001`
**버전:** 0.1.0

## `GET /`

- 설명: Health
- 응답: 200

## `GET /v1/orchestrator/strategies`

- 설명: Get Strategies
- 응답: 200

## `POST /v1/orchestrator/strategies`

- **설명**: 전략 코드 등록 (삭제 예정, 실제로는 파이프라인 실행만 지원)
- **RequestBody**: 있음 (필수)
- **응답**: 200 OK, 422 Unprocessable Entity

## `GET /v1/orchestrator/strategies/{version_id}/dag`

- 설명: Get Strategy Dag
- 파라미터: ['version_id']
- 응답: 200, 422

## `POST /v1/orchestrator/trigger`

- **설명**: 파이프라인 실행 트리거
- **RequestBody**: 있음 (필수)
- **응답**: 200 OK, 422 Unprocessable Entity

## `GET /v1/orchestrator/pipeline/{pipeline_id}/status`

- **설명**: 파이프라인 실행 상태 조회
- **파라미터**: 
  - `pipeline_id`: 조회할 파이프라인 ID (필수)
- **응답**: 200 OK, 422 Unprocessable Entity

**응답 예시**:
```json
{
  "status": "COMPLETED",
  "result": {
    "node_a1b2c3d4": {
      "output": 42,
      "execution_time": 0.35
    },
    "node_f1e2d3c4": {
      "output": true,
      "execution_time": 0.12
    }
  }
}
```

## `GET /v1/orchestrator/executions`

- 설명: Get Executions
- 파라미터: ['limit']
- 응답: 200, 422

## `GET /v1/orchestrator/executions/{execution_id}`

- 설명: Get Execution
- 파라미터: ['execution_id']
- 응답: 200, 422

## `GET /v1/orchestrator/strategies`

- 설명: Get Strategies
- 응답: 200

## `POST /v1/orchestrator/strategies`

- **설명**: 전략 코드 제출
- **RequestBody**: 있음 (필수)
- **응답**: 200 OK, 422 Unprocessable Entity

**요청 예시**:
```json
{
  "strategy_id": "my_awesome_strategy",
  "version_id": "strategy_v1_202505120001",
  "strategy_code": "from qmtl.sdk import node\n\n@node(tags=['FEATURE'])\ndef feature():\n    return 42\n\n@node(tags=['SIGNAL'])\ndef signal(x):\n    return x > 40"
}
```

**응답 예시**:
```json
{
  "version_id": "strategy_v1_202505120001",
  "nodes": [
    {
      "node_id": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
      "type": "FEATURE",
      "function_name": "feature"
    },
    {
      "node_id": "f1e2d3c4b5a6f1e2d3c4b5a6f1e2d3c4",
      "type": "SIGNAL",
      "function_name": "signal"
    }
  ]
}
```

## `GET /v1/orchestrator/strategies/{version_id}/dag`

- 설명: Get Strategy Dag
- 파라미터: ['version_id']
- 응답: 200, 422

## `POST /v1/orchestrator/strategies/{version_id}/activate`

- **설명**: 전략 활성화
- **파라미터**: 
  - `version_id`: 활성화할 전략 버전 ID (필수)
- **RequestBody**: 있음 (필수)
- **응답**: 200 OK, 422 Unprocessable Entity

**요청 예시**:
```json
{
  "environment": "production"
}
```

**응답 예시**:
```json
{
  "success": true,
  "message": "Strategy activated successfully",
  "environment": "production",
  "version_id": "strategy_v1_202505120001"
}
```

## `POST /v1/orchestrator/strategies/{version_id}/deactivate`

- 설명: Deactivate Strategy
- 파라미터: ['version_id']
- RequestBody: 있음
- 응답: 200, 422

## `GET /v1/orchestrator/strategies/{version_id}/activation-history`

- 설명: Get Activation History
- 파라미터: ['version_id']
- 응답: 200, 422

## `POST /v1/orchestrator/analyzers`

- **설명**: 분석기 등록
- **RequestBody**: 있음 (필수)
- **응답**: 200 OK, 422 Unprocessable Entity

**요청 예시**:
```json
{
  "analyzer_id": "correlation_analyzer_v1",
  "analyzer_code": "from qmtl.sdk.analyzer import Analyzer\nfrom qmtl.sdk.node import QueryNode\n\nanalyzer = Analyzer(name='correlation')\nqn = QueryNode(name='q1', tags=['PRICE'])\nanalyzer.query_nodes['q1'] = qn"
}
```

**응답 예시**:
```json
{
  "analyzer_id": "correlation_analyzer_v1",
  "query_nodes": ["q1"]
}
```

## `GET /v1/orchestrator/analyzers/{analyzer_id}`

- 설명: Get Analyzer
- 파라미터: ['analyzer_id']
- 응답: 200, 422

## `POST /v1/orchestrator/analyzers/{analyzer_id}/activate`

- 설명: Activate Analyzer
- 파라미터: ['analyzer_id']
- RequestBody: 있음
- 응답: 200, 422

## `GET /v1/orchestrator/analyzers/{analyzer_id}/results`

- 설명: Get Analyzer Results
- 파라미터: ['analyzer_id']
- 응답: 200, 422
