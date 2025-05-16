# QMTL의 핵심 개념 및 시각화 자료

이 문서는 QMTL의 핵심 개념과 아키텍처를 시각 자료와 함께 설명합니다.

## 1. QMTL의 핵심 가치

QMTL은 다음과 같은 핵심 가치를 기반으로 설계되었습니다:

1. **선언적 파이프라인 구성**: 데이터 노드와 의존성을 선언하면 플랫폼이 실행을 관리
2. **라이프사이클 자동화**: 노드 생성, 등록, 실행, 가비지 컬렉션 등을 자동으로 관리
3. **확장성**: 로컬 개발부터 분산 환경까지 동일한 코드로 확장 가능
4. **유연한 노드 분류**: 태그 기반의 동적 노드 검색 및 조회
5. **상태 추적**: 실행 상태와 히스토리를 투명하게 관리

## 2. 시스템 구성 요소 및 관계

```mermaid
flowchart TD
    StratDev[Strategy Developer] --> StratNodes[Strategy & Nodes]
    StratNodes --> Registry[Registry Service]
    Registry --> QA[Query & Analysis]
    Registry --> Orchestrator[Orchestrator Service]
    Orchestrator --> Engine[Execution Engine]
    Engine --> StateDB[State & History DB]
    StateDB --> Client[Client Applications]
    Client --> Orchestrator
```

## 3. 개념 계층 구조

```mermaid
classDiagram
    Strategy *-- Pipeline : contains
    Pipeline *-- DataNode : contains
    Pipeline *-- QueryNode : contains
    Pipeline *-- AnalyzerNode : contains
    
    class Strategy {
        +id
        +version
        +metadata
    }
    class Pipeline {
        +nodes
        +execute()
        +get_history()
    }
    class DataNode {
        +id
        +tags
        +function
        +interval_settings
    }
    class QueryNode {
        +tags
        +match_mode
        +query()
    }
    class AnalyzerNode {
        +query_nodes
        +analyze()
    }
```

## 4. 데이터 흐름 개념도

```mermaid
flowchart TD
    ExtData[외부 데이터 소스] --> RawNode[Raw 데이터 노드]
    RawNode --> FeatureNode[특성 추출 노드]
    History[히스토리 데이터] --> FeatureNode
    FeatureNode --> SignalNode[시그널 생성 노드]
    SignalNode --> History
    SignalNode --> Result[실행 결과 저장]
    Result --> State[상태 갱신 및 이벤트 발행]
```

## 5. 노드 유형 및 관계

```mermaid
flowchart TD
    RawNode[RAW 노드] --> FeatureNode[FEATURE 노드]
    HistNode[HISTORICAL 노드] --> FeatureNode
    FeatureNode --> SignalNode[SIGNAL 노드]
    DepNode[DEPENDENT 노드] --> FeatureNode
    SignalNode --> OutputNode[OUTPUT 노드]
    HistNode --> OutputNode
    DepNode --> OutputNode
```

## 6. 전략 실행 흐름

```mermaid
flowchart LR
    Write[전략 작성] --> Submit[전략 제출]
    Submit --> Parse[전략 파싱]
    Parse --> Register[노드 등록]
    Register --> Activate[전략 활성화]
    Activate --> History[이력 관리]
    Register --> Engine[실행 엔진]
    Engine --> Return[결과 반환]
    Return --> History
```

## 7. 노드 라이프사이클

```mermaid
stateDiagram-v2
    [*] --> Create: 생성
    Create --> Register: 등록
    Register --> Activate: 활성화
    Create --> Activate: 직접 활성화
    Activate --> Execute: 실행
    Execute --> Deactivate: 비활성화
    Deactivate --> Delete: 삭제
    Execute --> GC: GC 수집
    GC --> Delete
    Delete --> [*]
```

## 8. 태그 기반 노드 분류 시스템

```mermaid
classDiagram
    class TagNamespace {
        +Predefined_Tags
        +Custom_Tags
        +Interval_Tags
        +Period_Tags
    }
    class Predefined_Tags {
        RAW
        FEATURE
        SIGNAL
        ANALYZER
        OUTPUT
    }
    class Custom_Tags {
        price
        volume
        volatility
        momentum
        correlation
    }
    class Interval_Tags {
        1m
        5m
        15m
        1h
        4h
        1d
    }
    class Period_Tags {
        1d
        1w
        1m
        3m
        6m
        1y
    }
    
    TagNamespace *-- Predefined_Tags
    TagNamespace *-- Custom_Tags
    TagNamespace *-- Interval_Tags
    TagNamespace *-- Period_Tags
```

## 9. 분석기와 쿼리 노드 관계

```mermaid
flowchart TD
    subgraph Analyzer[분석기]
        QN1[QueryNode 태그:PRICE] --> RD1[결과 데이터 노드 집합]
        QN2[QueryNode 태그:VOLUME] --> RD2[결과 데이터 노드 집합]
        QN3[QueryNode 태그:CUSTOM] --> RD3[결과 데이터 노드 집합]
        
        RD1 --> AN[분석 노드들]
        RD2 --> AN
        RD3 --> AN
        
        AN --> Result[분석 결과]
    end
```

## 10. 인터벌 데이터 관리 개념

```mermaid
gantt
    title 시간 범위
    dateFormat  YYYY-MM-DD
    axisFormat %m/%d
    
    section 인터벌 단위
    now - period          :done, period, 2025-01-01, 2025-01-14
    현재                   :milestone, now, 2025-01-14, 0d
    
```

```mermaid
flowchart LR
    subgraph 히스토리 데이터 관리
        TTL[TTL 이후 자동 삭제] --> Data[과거 ---- 데이터 타임라인 ---- 최신]
        MaxHistory[Max History 제한] --> Data
    end
```

## 11. QMTL 기능별 컴포넌트 맵

```mermaid
classDiagram
    class QMTL_System {
        +데이터_관리
        +전략_관리
        +실행_엔진
        +분석_도구
    }
    class 데이터_관리 {
        +노드 등록
        +노드 검색
        +태그 관리
        +GC
    }
    class 전략_관리 {
        +전략 제출
        +활성화
        +버전 관리
        +환경 관리
    }
    class 실행_엔진 {
        +로컬 실행
        +분산 실행
        +상태 추적
        +재시도 로직
    }
    class 분석_도구 {
        +쿼리
        +분석기
        +결과
        +시각화
    }
    
    QMTL_System *-- 데이터_관리
    QMTL_System *-- 전략_관리
    QMTL_System *-- 실행_엔진
    QMTL_System *-- 분석_도구
```

## 12. 확장 및 통합 아키텍처

```mermaid
flowchart TD
    External[외부 데이터소스 연동] <--> Core[QMTL 코어 시스템]
    Core <--> Integration[외부 시스템 연동]
    Adapter[데이터 변환 어댑터] <--> Monitoring[모니터링 및 알림 시스템]
    Monitoring <--> Deployment[K8s 배포 엔진]
    
    External --> Core
    Core --> Integration
    Adapter --> Core
    Core --> Monitoring
    Monitoring --> Deployment
```

이 다이어그램과 설명을 통해 QMTL 시스템의 주요 개념과 아키텍처를 시각적으로 이해할 수 있습니다. 자세한 내용은 다음 문서를 참조하세요:

- [아키텍처 다이어그램](architecture_diagram.md)
- [용어 사전](glossary.md)
- [E2E 워크플로우 예제](e2e_workflow.md)
- [개발자 가이드](developer_guide.md) 