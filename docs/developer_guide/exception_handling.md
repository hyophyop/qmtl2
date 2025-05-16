# FastAPI 예외 처리 패턴 가이드

## 예외 유형 구분

| 구분 | 언제 발생? | 권장 처리 방법 | HTTP 응답 |
|-----|----------|--------------|----------|
| 예상 가능한 오류 | 비즈니스 로직에서 "정상적"으로 탐지한 오류(입력값 오류, 리소스 없음 등) | `raise HTTPException(status_code=4xx, detail="...")` | 4xx |
| 예상 불가 오류 | 코드에서 미처 잡지 못한 예외(버그, 외부 서비스 장애 등) | 전역 Exception 핸들러에서 처리 | 500 |

## 권장 패턴

### 1. 단순 케이스 - HTTPException만으로 충분한 경우

입력값 검증, 리소스 존재 여부 등 예상 가능한 오류는 즉시 4xx 응답으로 처리합니다:

```python
from fastapi import FastAPI, HTTPException, status, Body

app = FastAPI()

@app.post("/items", status_code=status.HTTP_201_CREATED)
async def create_item(item: Item = Body(...)):
    if db.exists(item.id):
        # "예상 가능한" 오류 → 곧바로 HTTPException
        raise HTTPException(status_code=409, detail="Item already exists")
    db.save(item)
    return {"id": item.id}
```

**장점**:
- 코드가 간결하고, 실패 경로가 테스트하기 쉽다.
- 반환값을 섞어 쓰지 않아 Starlette가 예외를 명확히 감지할 수 있다.

### 2. 서비스 계층의 커스텀 예외 + 전역 핸들러

FastAPI는 `@app.exception_handler(MyError)` 데코레이터로 특정 예외를 잡아 JSON 응답으로 변환할 수 있습니다:

```python
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

class RegistryServiceError(Exception):
    """서비스 계층 공통 예외"""

@app.exception_handler(RegistryServiceError)
async def registry_error_handler(request, exc: RegistryServiceError):
    logger.error("Registry error: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )
```

라우트나 dependency 안에서는 단순히 `raise RegistryServiceError(...)` 하면 됩니다. Starlette가 위 핸들러를 호출해 500 JSON 응답을 만들어 주므로, 테스트 클라이언트는 절대 hang 되지 않습니다.

### 3. try/except 블록을 써야 할 때의 주의점

여러 종류의 예외를 구분하려고 try/except를 둘러싸는 경우, 이미 HTTPException으로 변환된 예외는 절대로 삼키지 말고 재-raise 해야 테스트가 멈추지 않습니다:

```python
try:
    node_service.validate_node(node)
    node_id = node_service.create_node(node)
    return {"node_id": node_id}
except ValidationError as e:
    # ValidationError → 422
    raise HTTPException(status_code=422, detail=str(e))
except HTTPException:
    # 이미 FastAPI가 처리할 예외는 그대로 통과
    raise
except Exception as e:
    # 예측 못 한 오류는 서비스 전용 예외나 HTTP 500으로 래핑
    logger.exception("Unexpected error")
    raise HTTPException(status_code=500, detail="Internal Server Error")
```

### 흔한 실수

```python
except Exception as e:
    logger.error(...)
    # ❌ "return {"error": ...}" 로 응답을 만들어 버림
```

- JSON은 돌려주지만 상태코드가 200이라서 클라이언트(테스트)가 성공으로 착각 → 나중에 assertion에서 실패
- 테스트가 hang 된다면, 내부에서 await 하지 않은 blocking I/O나 무한루프일 가능성이 더 크다. 예외만 제대로 raise 하면 hang은 거의 없다.

## 테스트 코드에서 오류 응답을 검증할 때 팁

```python
resp = client.post("/v1/registry/nodes", json={"node": ...})
assert resp.status_code == 201      # 성공
# 또는
assert resp.status_code == 422      # 입력값 오류
```

- 응답이 없는 채로 멈추면 → 라우트 내부에서 await 중 타임아웃이거나 except 블록에서 return 해버려 프레임워크가 응답을 못 만든 경우가 대부분이다.
- pytest -s -vv --log-cli-level=INFO로 서버-측 로그를 확인하면 어디에서 멈췄는지 바로 보인다.

## 정리 – FastAPI 예외 처리 체크리스트

1. 예상 가능한 실패 → 즉시 raise HTTPException(4xx)
2. 서비스 공통 오류 → 커스텀 예외 + 전역 @exception_handler
3. try/except 사용 시
   - 이미 HTTPException인 예외는 except HTTPException: raise
   - 나머지는 500으로 변환 후 raise
4. 절대 except ...: return {...} 패턴을 쓰지 않는다 (200 응답 + 테스트 혼란).
5. 테스트가 멈춘다면 로그 확인 → 의존 서비스 연결·deadlock 등을 먼저 의심.

이 패턴을 따르면 TestClient는 항상 HTTP 응답을 받으므로, assert resp.status_code ... 단계에서만 실패하고 hang 되지는 않습니다.
