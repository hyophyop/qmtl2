# QMTL 아키텍처 다이어그램

## 1. 시스템 아키텍처 개요

QMTL 시스템의 전체 아키텍처는 다음과 같이 구성됩니다:

```mermaid
flowchart TD
    subgraph QMTL["QMTL Architecture"]
        SDK["Strategy Development\n(SDK/Local)"]
        Orchestrator["Orchestrator\nService"]
        Registry["Registry\nService"]
        Redis["Redis\n(State & History)"]
        Engine["Execution Engine\n(Redpanda/Kafka)"]
        Neo4j["Neo4j\n(Graph DB)"]
        
        SDK --> Orchestrator
        Orchestrator <--> Registry
        Registry <--> Redis
        Orchestrator --> Engine
        Registry --> Neo4j
    end
```

## 2. 컴포넌트 역할

* **Strategy Development (SDK/Local)**: 개발자가 전략을 작성하고 로컬에서 테스트하는 환경
* **Orchestrator Service**: 전략 제출, 파싱, 활성화 및 파이프라인 실행을 관리
* **Registry Service**: 데이터 노드, 전략 메타데이터, 활성화 상태 등을 저장하고 관리
* **Redis**: 상태 정보와 히스토리 데이터를 관리하는 인메모리 데이터베이스
* **Neo4j**: 노드 간 관계와 의존성을 저장하는 그래프 데이터베이스
* **Execution Engine**: 파이프라인 실행을 담당하는 Redpanda/Kafka 기반 실행 엔진

## 3. 데이터 흐름 워크플로우

전략의 개발부터 실행까지의 전체 워크플로우는 다음과 같습니다:

```mermaid
flowchart LR
    S1["1. 전략 개발\n(SDK/Local)"] --> S2["2. 전략 제출\n(Orchestrator)"]
    S2 --> S3["3. 노드 등록\n(Registry)"]
    S3 --> S4["4. 전략 활성화\n(Orchestrator)"]
    S4 --> S5["5. 파이프라인 실행\n(Execution)"]
    S5 --> S6["6. 결과 수집\n(Redis/Neo4j)"]
```

## 4. 모듈 구조 다이어그램

QMTL 코드베이스의 모듈 구조는 다음과 같이 구성됩니다:

```mermaid
classDiagram
    class Models {
        +datanode.py
        +strategy.py
        +api_registry.py
        +api_orchestrator.py
    }
    class Common {
        +db/
        +redis/
        +errors/
        +utils/
    }
    class Registry {
        +api.py
        +services/
        +db/
    }
    class Orchestrator {
        +api.py
        +services/
        +execution/
    }
    class SDK {
        +pipeline.py
        +node.py
        +analyzer.py
        +execution.py
    }
```

## 5. 전략 실행 시퀀스 다이어그램

전략 제출부터 실행까지의 시퀀스 다이어그램은 다음과 같습니다:

```mermaid
sequenceDiagram
    participant Client
    participant Orchestrator
    participant Registry
    participant Engine
    participant Redis
    
    Client->>Orchestrator: submit_strategy
    Orchestrator->>Orchestrator: parse_strategy
    Orchestrator->>Registry: register_node
    Registry->>Registry: store_node
    Orchestrator->>Registry: register_strategy
    Registry->>Registry: store_strategy
    Orchestrator->>Client: response
    
    Client->>Orchestrator: activate_strategy
    Orchestrator->>Registry: activate_strategy
    Registry->>Redis: update_state
    Orchestrator->>Client: response
    
    Client->>Orchestrator: trigger_pipeline
    Orchestrator->>Registry: get_nodes
    Registry->>Orchestrator: nodes
    Orchestrator->>Engine: execute_pipeline
    Engine->>Redis: store_results
    Orchestrator->>Client: execution_id
    
    Client->>Orchestrator: get_status
    Orchestrator->>Redis: get_results
    Redis->>Orchestrator: results
    Orchestrator->>Client: results
``` 