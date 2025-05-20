# Golden 및 Round-trip 테스트 가이드

이 디렉토리는 QMTL 프로젝트에서 golden 및 round-trip 테스트를 위한 템플릿과 예시를 제공합니다.

## 개요

QMTL NextGen 아키텍처에서는 모든 서비스가 protobuf 기반 contract로 데이터를 교환합니다. 이러한 직렬화/역직렬화 과정에서 데이터 일관성을 보장하기 위해 두 가지 테스트 패턴을 활용합니다:

1. **Golden 테스트**: "알려진 좋은 상태"의 참조 데이터와 현재 구현을 비교
2. **Round-trip 테스트**: 직렬화 후 역직렬화한 데이터가 원본과 일치하는지 검증

## Golden 테스트

Golden 테스트는 사전에 저장된 "golden" 파일(JSON 형식)과 현재 코드에서 생성되는 결과를 비교하는 방식입니다.

### 특징

- 구현 변경에 따른 출력 변화를 감지
- 의도하지 않은 변경 방지
- API 계약 일관성 보장
- 직렬화 형식 변화 모니터링

### 사용 방법

1. Golden 파일 생성 모드로 실행:
   ```python
   python -m tests.templates.golden_test_example
   ```

2. 테스트 실행:
   ```python
   pytest tests/templates/golden_test_example.py
   ```

### 구현 패턴

```python
def test_datanode_serialization_golden(self):
    # 데이터 생성
    node = DataNode(...)
    
    # Golden 파일 로드 (없으면 생성)
    golden_node = load_golden_data(DataNode, "datanode_golden.json")
    if golden_node is None:
        save_golden_data(node, "datanode_golden.json")
        golden_node = node
    
    # 비교 검증
    assert node.id == golden_node.id
    assert node.name == golden_node.name
    # ...
```

## Round-trip 테스트

Round-trip 테스트는 protobuf 객체의 직렬화 후 역직렬화 과정에서 데이터 손실이나 변형이 없는지 검증합니다.

### 특징

- 직렬화/역직렬화 일관성 보장
- 호환성 문제 조기 발견
- 다양한 필드 조합 테스트 가능

### 사용 방법

```python
pytest tests/templates/roundtrip_test_example.py
```

### 구현 패턴

```python
def test_strategy_roundtrip(self):
    # 원본 데이터 생성
    original = Strategy(...)
    
    # 직렬화
    serialized = original.SerializeToString()
    
    # 역직렬화
    deserialized = Strategy()
    deserialized.ParseFromString(serialized)
    
    # 비교 검증
    assert original.id == deserialized.id
    assert original.name == deserialized.name
    # ...
```

## 매개변수화된 테스트

다양한 데이터 조합을 효율적으로 테스트하기 위해 `pytest.mark.parametrize`를 활용합니다:

```python
@pytest.mark.parametrize("node_id,name,tags_pred,tags_custom", [
    ("node_1", "Node 1", ["DATA"], ["test"]),
    ("node_2", "Node 2", ["STREAM"], ["production"]),
    # ...
])
def test_datanode_parametrized_roundtrip(self, node_id, name, tags_pred, tags_custom):
    # ...
```

## 테스트 파일 위치

- Golden 테스트 참조 데이터: `tests/data/golden/*.json`
- Golden 테스트 예시: `tests/templates/golden_test_example.py`
- Round-trip 테스트 예시: `tests/templates/roundtrip_test_example.py`

## 테스트 작성 지침

1. 모든 protobuf 모델에 대해 round-trip 테스트 작성
2. 주요 모델 및 API 응답에 대해 golden 테스트 작성
3. 경계 조건 및 특수 케이스에 대한 매개변수화된 테스트 추가
4. 변경 가능성이 높은 필드는 golden 테스트에서 제외 고려
5. CI/CD 파이프라인에 테스트 통합

## 참고사항

- Golden 파일은 버전 관리에 포함되어야 함
- API 변경 시 golden 파일 업데이트 필요
- 직렬화 형식(JSON, binary 등)에 따라 결과가 달라질 수 있음
- 대규모 객체의 경우 필요한 필드만 선택적으로 비교 가능 