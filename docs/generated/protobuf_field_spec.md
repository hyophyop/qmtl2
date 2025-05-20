# QMTL Protobuf 스키마 필드 정의 및 타입 제약 (NG-2-2-1)

아래 표는 protos/ 내 주요 .proto 파일의 메시지별 필드, 타입, 필수/선택/반복/맵 여부, 주요 제약조건을 정리한 것입니다.

---

## qmtl_analyzer.proto
| Message              | Field           | Type                | Rule         | Description/Constraint |
|----------------------|-----------------|---------------------|--------------|-----------------------|
| AnalyzerDefinition   | name            | string              | required     |                       |
|                      | description     | string              | optional     |                       |
|                      | tags            | string              | repeated     |                       |
|                      | source          | string              | required     |                       |
|                      | parameters      | map<string, string> | required     |                       |
| AnalyzerMetadata     | analyzer_id     | string              | required     |                       |
|                      | name            | string              | required     |                       |
|                      | description     | string              | optional     |                       |
|                      | tags            | string              | repeated     |                       |
|                      | created_at      | int64               | required     | UNIX timestamp        |
|                      | status          | string              | required     |                       |
|                      | parameters      | map<string, string> | required     |                       |
| AnalyzerResult       | analyzer_id     | string              | required     |                       |
|                      | result          | map<string, string> | required     |                       |
|                      | generated_at    | int64               | required     | UNIX timestamp        |
|                      | status          | string              | required     |                       |
|                      | error           | string              | optional     |                       |

---

## qmtl_callback.proto
| Message              | Field           | Type                | Rule         | Description/Constraint |
|----------------------|-----------------|---------------------|--------------|-----------------------|
| NodeCallbackRequest  | node_id         | string              | required     |                       |
|                      | callback_type   | NodeCallbackType    | required     | enum                  |
|                      | url             | string              | required     |                       |
|                      | metadata        | map<string, string> | required     |                       |
| NodeCallbackResponse | success         | bool                | required     |                       |
|                      | message         | string              | required     |                       |
|                      | callback_id     | string              | required     |                       |
| NodeCallbackEvent    | node_id         | string              | required     |                       |
|                      | callback_type   | NodeCallbackType    | required     | enum                  |
|                      | event_payload   | map<string, string> | required     |                       |
|                      | triggered_at    | int64               | required     | UNIX timestamp        |

---

## qmtl_datanode.proto
| Message              | Field           | Type                | Rule         | Description/Constraint |
|----------------------|-----------------|---------------------|--------------|-----------------------|
| NodeTags             | predefined      | string              | repeated     |                       |
|                      | custom          | string              | repeated     |                       |
| IntervalSettings     | interval        | string              | required     |                       |
|                      | period          | int32               | required     |                       |
|                      | max_history     | int32               | optional     |                       |
| NodeStreamSettings   | intervals       | map<string,IntervalSettings> | required | 최소 1개 이상 |
| DataNode             | node_id         | string              | required     | 32자리 해시           |
|                      | type            | string              | required     |                       |
|                      | data_format     | map<string, string> | required     |                       |
|                      | params          | map<string, string> | required     |                       |
|                      | dependencies    | string              | repeated     |                       |
|                      | ttl             | int32               | optional     |                       |
|                      | tags            | NodeTags            | required     |                       |
|                      | stream_settings | NodeStreamSettings  | required     |                       |
|                      | interval_settings| IntervalSettings    | required     |                       |
| TopoSortResult       | order           | string              | repeated     |                       |
|                      | node_map        | map<string,DataNode>| required     |                       |
| DAGNodeDependency    | id              | string              | required     |                       |
|                      | type            | string              | required     |                       |
| DAGNode              | id              | string              | required     |                       |
|                      | type            | string              | required     |                       |
|                      | dependencies    | DAGNodeDependency   | repeated     |                       |
|                      | params          | map<string, string> | required     |                       |
|                      | metadata        | map<string, string> | required     |                       |
| DAGEdge              | source          | string              | required     |                       |
|                      | target          | string              | required     |                       |

---

## qmtl_events.proto
| Message              | Field           | Type                | Rule         | Description/Constraint |
|----------------------|-----------------|---------------------|--------------|-----------------------|
| NodeStatusEvent      | event_type      | EventType           | required     | enum                  |
|                      | node_id         | string              | required     |                       |
|                      | status          | string              | required     |                       |
|                      | timestamp       | int64               | required     | UNIX timestamp        |
|                      | meta            | map<string, string> | required     |                       |
| PipelineStatusEvent  | event_type      | EventType           | required     | enum                  |
|                      | pipeline_id     | string              | required     |                       |
|                      | status          | string              | required     |                       |
|                      | timestamp       | int64               | required     | UNIX timestamp        |
|                      | meta            | map<string, string> | required     |                       |
| AlertEvent           | event_type      | EventType           | required     | enum                  |
|                      | target_id       | string              | required     |                       |
|                      | level           | string              | required     |                       |
|                      | message         | string              | required     |                       |
|                      | timestamp       | int64               | required     | UNIX timestamp        |
|                      | meta            | map<string, string> | required     |                       |

---

## qmtl_status.proto
| Message              | Field           | Type                | Rule         | Description/Constraint |
|----------------------|-----------------|---------------------|--------------|-----------------------|
| NodeErrorDetail      | code            | string              | optional     |                       |
|                      | message         | string              | optional     |                       |
|                      | occurred_at     | string              | optional     | ISO8601               |
|                      | recovered_at    | string              | optional     | ISO8601               |
|                      | recovery_count  | int32               | required     |                       |
|                      | extra           | map<string, string> | required     |                       |
| NodeStatus           | node_id         | string              | required     |                       |
|                      | status          | string              | required     |                       |
|                      | start_time      | string              | optional     | ISO8601               |
|                      | end_time        | string              | optional     | ISO8601               |
|                      | result          | map<string, string> | required     |                       |
|                      | resource        | map<string, string> | required     |                       |
|                      | meta            | map<string, string> | required     |                       |
|                      | error_detail    | NodeErrorDetail     | required     |                       |
|                      | last_recovered_at| string             | optional     | ISO8601               |
|                      | recovery_count  | int32               | required     |                       |
| PipelineStatus       | pipeline_id     | string              | required     |                       |
|                      | status          | string              | required     |                       |
|                      | params          | map<string, string> | required     |                       |
|                      | start_time      | string              | required     | ISO8601               |
|                      | last_update     | string              | required     | ISO8601               |
|                      | end_time        | string              | optional     | ISO8601               |
|                      | progress        | float               | required     |                       |
|                      | result          | map<string, string> | required     |                       |
|                      | error_detail    | NodeErrorDetail     | required     |                       |
|                      | last_recovered_at| string             | optional     | ISO8601               |
|                      | recovery_count  | int32               | required     |                       |
| ExecutionDetail      | execution_id    | string              | required     |                       |
|                      | strategy_id     | string              | required     |                       |
|                      | version_id      | string              | required     |                       |
|                      | status          | string              | required     |                       |
|                      | start_time      | int64               | optional     | UNIX timestamp        |
|                      | end_time        | int64               | optional     | UNIX timestamp        |
|                      | parameters      | map<string, string> | required     |                       |
|                      | result          | map<string, string> | required     |                       |

---

## qmtl_strategy.proto
| Message              | Field           | Type                | Rule         | Description/Constraint |
|----------------------|-----------------|---------------------|--------------|-----------------------|
| StrategyMetadata     | strategy_name   | string              | optional     |                       |
|                      | submitted_at    | int64               | optional     | UNIX timestamp        |
|                      | description     | string              | optional     |                       |
|                      | author          | string              | optional     |                       |
|                      | tags            | string              | repeated     |                       |
|                      | version         | string              | optional     |                       |
|                      | source          | string              | optional     |                       |
|                      | extra_data      | map<string, string> | required     |                       |
| StrategyVersion      | strategy_code   | string              | required     |                       |
|                      | created_at      | int64               | required     | UNIX timestamp        |
|                      | metadata        | StrategyMetadata    | required     |                       |
| NodeSnapshot         | node_id         | string              | required     |                       |
|                      | data            | map<string, string> | required     |                       |
| StrategySnapshot     | pipeline_id     | string              | required     |                       |
|                      | created_at      | int64               | required     | UNIX timestamp        |
|                      | nodes           | NodeSnapshot        | repeated     |                       |
|                      | edges           | DAGEdge             | repeated     |                       |
|                      | metadata        | map<string, string> | required     |                       |

---

## qmtl_template.proto
| Message              | Field           | Type                | Rule         | Description/Constraint |
|----------------------|-----------------|---------------------|--------------|-----------------------|
| TemplateMetadata     | name            | string              | required     |                       |
|                      | description     | string              | optional     |                       |
|                      | owner           | string              | required     |                       |
|                      | is_public       | bool                | required     |                       |
|                      | tags            | string              | repeated     |                       |
|                      | created_at      | int64               | required     | UNIX timestamp        |
|                      | updated_at      | int64               | optional     | UNIX timestamp        |
|                      | extra           | map<string, string> | required     |                       |
| NodeTemplate         | template_id     | string              | required     |                       |
|                      | type            | string              | required     |                       |
|                      | metadata        | TemplateMetadata    | required     |                       |
|                      | node            | map<string, string> | required     |                       |
| StrategyTemplate     | template_id     | string              | required     |                       |
|                      | type            | string              | required     |                       |
|                      | metadata        | TemplateMetadata    | required     |                       |
|                      | strategy        | map<string, string> | required     |                       |
| DAGTemplate          | template_id     | string              | required     |                       |
|                      | type            | string              | required     |                       |
|                      | metadata        | TemplateMetadata    | required     |                       |
|                      | dag             | map<string, string> | required     |                       |
| TemplatePermission   | template_id     | string              | required     |                       |
|                      | user_id         | string              | required     |                       |
|                      | level           | string              | required     |                       |
|                      | granted_at      | int64               | required     | UNIX timestamp        |

---

> NG-2-2-1: protobuf 스키마 필드 정의(필수/선택 필드, 타입 제약) 문서화 완료 (2025-05-20)
