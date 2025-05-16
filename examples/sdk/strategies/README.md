# QMTL 전략 예제

이 디렉토리에는 QMTL SDK를 사용하여 개발한 전략(Strategy) 예제들이 포함되어 있습니다. 각 예제는 QMTL의 다양한 기능과 패턴을 보여줍니다.

## 예제 목록

### 1. Simple Strategy (simple_strategy.py)

가장 기본적인 QMTL 전략 예제입니다. 단순 이동 평균(SMA)과 변동성 계산을 통해 매수 신호를 생성하는 간단한 전략을 구현했습니다.

**주요 개념**:
- `@node` 데코레이터를 사용한 기본 데이터 노드 구현
- 노드 간 의존성 관리 (`upstreams` 파라미터)
- 태그 기반 노드 분류 (`FEATURE`, `SIGNAL`)

**실행 방법**:
```bash
python simple_strategy.py
```

### 2. Momentum Strategy (momentum_strategy.py)

여러 기술적 지표를 결합한 모멘텀 기반 전략 예제입니다. RSI, 볼린저 밴드, 모멘텀 지표를 종합적으로 분석하여 매수/매도 신호를 생성합니다.

**주요 개념**:
- 복잡한 파이프라인 구성 (여러 노드 간 의존성)
- 다양한 기술적 지표 계산 방법
- 인터벌 설정 (`interval_settings` 활용)
- 데이터 흐름과 신호 생성 로직 분리

**실행 방법**:
```bash
python momentum_strategy.py
```

### 3. PyTorch 스타일 파이프라인 (pipeline_style_example.py)

Pipeline 객체를 직접 생성하고, 노드를 등록한 뒤 execute()로 전체 전략을 실행하는 예제입니다.

**주요 개념**:
- 파이프라인 객체 직접 생성 및 노드 등록
- 명시적 실행 순서 관리
- PyTorch의 nn.Module 스타일과 유사한 워크플로우

**실행 방법**:
```bash
python pipeline_style_example.py
```

### 4. 클래스 상속 방식 파이프라인 (class_style_example.py)

Pipeline 클래스를 상속받아 파이프라인을 객체지향적으로 정의하는 예제입니다.

**주요 개념**:
- 파이프라인을 클래스로 캡슐화하여 재사용성/확장성 강화
- 여러 파이프라인 버전을 클래스 단위로 관리 가능
- 테스트 및 다양한 환경에서 인스턴스화하여 실행 가능

**실행 방법**:
```bash
python class_style_example.py
```

## 전략 개발 가이드

QMTL을 사용한 전략 개발 시 다음 패턴을 참고하세요:

1. **노드 분류**: 적절한 태그를 사용하여 노드의 역할을 명확히 구분하세요.
   - `DATA`: 원본 데이터를 가져오는 노드
   - `FEATURE`: 특성/지표를 계산하는 노드
   - `SIGNAL`: 매매 신호를 생성하는 노드

2. **인터벌 설정**: 데이터 주기와 보관 기간을 명시적으로 설정하세요.
   ```python
   @node(tags=["FEATURE"], 
         interval_settings=IntervalSettings(interval="1d", period="7d"))
   ```

3. **의존성 관리**: 노드 간 의존성을 명확히 정의하세요.
   ```python
   @node(tags=["SIGNAL"], upstreams=["feature_node_1", "feature_node_2"])
   ```

4. **로컬 테스트**: `if __name__ == "__main__"` 블록을 활용하여 전략을 로컬에서 쉽게 테스트할 수 있도록 구성하세요.

## Orchestrator 서비스 연동

개발한 전략을 Orchestrator 서비스에 등록하고 실행하는 방법은 다음과 같습니다:

1. **전략 코드 제출**:
```bash
curl -X POST http://localhost:8001/v1/orchestrator/strategies \
  -H "Content-Type: application/json" \
  -d '{"strategy_id": "my_strategy", "version_id": "v1", "strategy_code": "..."}'
```

2. **전략 활성화**:
```bash
curl -X POST http://localhost:8001/v1/orchestrator/strategies/v1/activate \
  -H "Content-Type: application/json" \
  -d '{"environment": "production"}'
```

자세한 API 문서는 `docs/generated/api.md`를 참조하세요. 