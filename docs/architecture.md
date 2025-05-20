### [외부/내부 API 라우터 분리 정책 및 예시]

#### 정책 요약
- 외부 API는 GET(조회)만 허용, 등록/수정/삭제 등 조작은 불가
- 내부 API(조작)는 Gateway/Orchestrator 등 신뢰된 서비스에서만 접근 가능, 인증/ACL 필수
- FastAPI 라우터를 public_router(GET 전용), internal_router(조작 전용)로 분리

#### FastAPI 라우터 설정 예시 (dependencies, ACL 포함)
```python
from fastapi import FastAPI, APIRouter, Depends, Request

def dummy_acl_middleware(request: Request):
    # TODO: 실제 인증/ACL 로직 구현 필요
    pass

public_router = APIRouter(prefix="/v1/registry/public", tags=["public"])
internal_router = APIRouter(prefix="/v1/registry/internal", tags=["internal"], dependencies=[Depends(dummy_acl_middleware)])

@public_router.get("/nodes/{node_id}")
async def get_node_public(...):
    ...

@internal_router.post("/nodes")
async def create_node_internal(...):
    ...

app = FastAPI()
app.include_router(public_router)
app.include_router(internal_router)
```

#### 인증/ACL 미들웨어 플로우 다이어그램 (mermaid)
```mermaid
flowchart TD
    Client-->|GET|PublicAPI[public_router]
    Client-->|POST/PUT/DELETE|InternalAPI[internal_router]
    InternalAPI-->|Depends(dummy_acl_middleware)|ACL[인증/ACL 미들웨어]
    ACL-->|성공|Service[조작 처리]
    ACL-->|실패|Error[401/403 반환]
``` 