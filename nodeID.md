# QMTL Node ID(글로벌 노드 식별자) 상세 설계

## 1. 목적
- **Node ID**는 QMTL 시스템 전체(Registry, Orchestrator, SDK, 테스트 등)에서 노드를 글로벌하게 유일하게 식별하기 위한 32자리 해시(hex) 문자열입니다.
- 파이프라인/전략 코드가 동일하면 언제 어디서나 동일 Node ID가 생성되어야 하며, 코드/입력/설정이 다르면 Node ID도 달라집니다.

---

## 2. Node ID 생성 원칙

- **함수 이름(name) 파라미터는 제거**  
  → 노드 생성 시 별도의 이름 지정 없이, 함수 객체 자체가 노드의 식별자가 됨

- **Node ID는 다음 요소의 해시로 생성**
  1. **함수 객체의 `__qualname__`**  
     - 클래스 메서드 구분 포함(예: `MyClass.feature`)
  2. **함수 소스코드(AST 파싱/문자열)**  
     - 함수 코드가 다르면 Node ID도 다름
  3. **업스트림 함수들의 `__qualname__` 리스트**  
     - 업스트림도 함수 객체로만 지정(문자열/이름 지정 불가)
  4. **stream_settings**  
     - interval/period 등 모든 설정 포함
  5. **key_params 및 그 값**  
     - 파라미터 값이 다르면 Node ID도 다름

- **람다 함수**  
  - 이름 대신 소스코드+업스트림+stream_settings+key_params의 해시로 Node ID 생성  
  - 객체 id/hash 사용 금지(런타임마다 달라짐)

- **클래스 메서드**  
  - `__qualname__`으로 구분(동일 함수명이라도 클래스가 다르면 Node ID 다름)

- **사이클(순환 참조)만 없으면 함수 이름 충돌 허용**  
  - 파이프라인 내에서 함수 이름이 중복되어도, Node ID는 코드/입력/설정이 다르면 다르게 생성됨  
  - 사이클 검증은 DAG 생성 시 자동 수행(ValidationError)

- **객체 id/hash 사용 금지**  
  - Node ID는 영속적/결정적이어야 하므로, 파이썬 객체 id/hash 등 런타임 의존 정보는 사용하지 않음

---

## 3. Node ID 생성 예시 코드

```python
import inspect, ast, hashlib, json

def generate_node_id(fn, upstreams, stream_settings, key_params):
    try:
        source = inspect.getsource(fn)
        source = inspect.cleandoc(source)
        tree = ast.parse(source)
        fn_ast = ast.dump(tree, annotate_fields=True, include_attributes=False)
    except Exception:
        fn_ast = str(fn)
    upstream_names = [u.__qualname__ for u in upstreams]
    signature_dict = {
        "qualname": fn.__qualname__,
        "ast": fn_ast,
        "upstreams": upstream_names,
        "stream_settings": stream_settings.model_dump() if hasattr(stream_settings, "model_dump") else str(stream_settings),
        "key_params": key_params,
    }
    signature_str = json.dumps(signature_dict, sort_keys=True)
    return hashlib.md5(signature_str.encode("utf-8")).hexdigest()
```

---

## 4. 정책 적용 범위

- SDK, Registry, Orchestrator, 테스트, 모델 직렬화/역직렬화 등 전체 계층에 동일하게 적용
- DataNode, ProcessingNode, SourceNode, QueryNode 등 모든 노드 추상화에 일관 적용
- Node ID는 32자리 hex 문자열로 관리

---

## 5. 주의사항 및 가이드

- **람다 함수**: 소스코드 추출이 불가능한 환경(인터프리터 등)에서는 명시적 함수 사용 권장
- **함수 이름 충돌**: 허용(사이클만 없으면 됨), 실제 구분은 Node ID로 이루어짐
- **업스트림**: 반드시 함수 객체로만 지정(문자열/이름 지정 불가)
- **Node ID 생성 정책**: SDK 내부에서 자동 처리, 사용자는 함수 객체만으로 DAG을 구성하면 됨
- **사이클 검증**: 파이프라인/DAG 생성 시 자동 수행(ValidationError)

---

## 6. 예시

```python
def fetch_raw(...): ...
def make_feature(...): ...
def make_signal(...): ...

node1 = ProcessingNode(fn=fetch_raw, ...)
node2 = ProcessingNode(fn=make_feature, upstreams=[fetch_raw], ...)
node3 = ProcessingNode(fn=make_signal, upstreams=[make_feature], ...)
# node1, node2, node3의 Node ID는 각 함수/업스트림/설정/파라미터에 따라 자동 생성됨
```

---

이 정책은 architecture.md, todo.md, 사용자 가이드, 예제 코드, 테스트 코드에 모두 반영되어 있습니다.  
추가로 궁금한 점이나 세부 구현/테스트/문서화가 필요하면 언제든 말씀해 주세요! 