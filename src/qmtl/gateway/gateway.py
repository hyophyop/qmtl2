from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

from qmtl.gateway.middlewares.auth import JWTAuthMiddleware, JWTConfig
from qmtl.gateway.middlewares.acl import ACLMiddleware, ACLConfig, default_acl_rules
from qmtl.gateway.middlewares.logging import LoggingMiddleware
from qmtl.gateway.middlewares.error import ErrorHandlingMiddleware
from qmtl.gateway.services.policy import PolicyService, ResourceType, ActionType

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gateway")

# FastAPI 앱 생성
app = FastAPI(title="QMTL Gateway", description="API Gateway for QMTL System")

# 정책 서비스 인스턴스 생성
policy_service = PolicyService()

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 운영 환경에서는 특정 출처만 허용하도록 변경
    allow_credentials=True,
    allow_methods=["GET"],  # 읽기 전용 API이므로 GET만 허용
    allow_headers=["*"],
)

# 오류 처리 미들웨어 추가
app.middleware("http")(ErrorHandlingMiddleware())

# 로깅 미들웨어 추가
app.middleware("http")(LoggingMiddleware())

# JWT 인증 미들웨어 설정
jwt_config = JWTConfig(
    secret_key=os.environ.get("JWT_SECRET_KEY", "development_secret_key"),
    exclude_paths=["/health", "/", "/docs", "/openapi.json"],
)
app.middleware("http")(JWTAuthMiddleware(jwt_config))

# ACL 미들웨어 설정
acl_config = ACLConfig(
    rules=default_acl_rules,
    default_deny=True,
    exclude_paths=["/health", "/", "/docs", "/openapi.json"],
)
app.middleware("http")(ACLMiddleware(acl_config))


@app.get("/")
def root():
    """서비스 루트 엔드포인트."""
    return JSONResponse(content={"status": "ok", "service": "QMTL Gateway"})


@app.get("/health")
def health():
    """서비스 상태 확인 엔드포인트."""
    return JSONResponse(content={"status": "healthy", "service": "QMTL Gateway"})


# 전략 제출 (read-only 정책: POST는 405)
@app.post("/v1/gateway/strategies")
def submit_strategy():
    """전략 제출 엔드포인트 (read-only 정책으로 405 Method Not Allowed)."""
    return Response(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)


# 전략 목록 조회
@app.get("/v1/gateway/strategies")
def list_strategies(request: Request):
    """전략 목록 조회 엔드포인트."""
    # 사용자 역할 기반 권한 확인
    user = request.state.user
    user_roles = user.get("roles", [])

    if not policy_service.evaluate_access(user_roles, ResourceType.STRATEGY, ActionType.READ):
        return Response(status_code=status.HTTP_403_FORBIDDEN)

    # 실제 구현에서는 DB에서 전략 목록 조회
    # 현재는 스텁 응답
    return JSONResponse(content={"strategies": []})


# 전략 상태 조회
@app.get("/v1/gateway/strategies/{strategy_id}/status")
def strategy_status(strategy_id: str, request: Request):
    """전략 상태 조회 엔드포인트."""
    # 사용자 역할 기반 권한 확인
    user = request.state.user
    user_roles = user.get("roles", [])

    if not policy_service.evaluate_access(
        user_roles, ResourceType.STRATEGY, ActionType.READ, strategy_id
    ):
        return Response(status_code=status.HTTP_403_FORBIDDEN)

    # 테스트용: test-strategy-1만 존재한다고 가정
    if strategy_id != "test-strategy-1":
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    # 정상 응답 (protobuf 바이너리 대신 JSON)
    return Response(
        content=b"\x0a\x0ftest-strategy-1\x12\x02ok", media_type="application/x-protobuf"
    )


# 콜백 목록 조회
@app.get("/v1/gateway/callbacks")
def list_callbacks(request: Request):
    """콜백 목록 조회 엔드포인트."""
    # 사용자 역할 기반 권한 확인
    user = request.state.user
    user_roles = user.get("roles", [])

    if not policy_service.evaluate_access(user_roles, ResourceType.CALLBACK, ActionType.READ):
        return Response(status_code=status.HTTP_403_FORBIDDEN)

    # 실제 구현에서는 콜백 목록 조회
    # 현재는 스텁 응답
    return JSONResponse(content={"callbacks": []})


# 노드 목록 조회
@app.get("/v1/gateway/nodes")
def list_nodes(request: Request):
    """노드 목록 조회 엔드포인트."""
    # 사용자 역할 기반 권한 확인
    user = request.state.user
    user_roles = user.get("roles", [])

    if not policy_service.evaluate_access(user_roles, ResourceType.NODE, ActionType.READ):
        return Response(status_code=status.HTTP_403_FORBIDDEN)

    # 실제 구현에서는 노드 목록 조회
    # 현재는 스텁 응답
    return JSONResponse(content={"nodes": []})


# 이벤트 목록 조회
@app.get("/v1/gateway/events")
def list_events(request: Request):
    """이벤트 목록 조회 엔드포인트."""
    # 사용자 역할 기반 권한 확인
    user = request.state.user
    user_roles = user.get("roles", [])

    if not policy_service.evaluate_access(user_roles, ResourceType.EVENT, ActionType.READ):
        return Response(status_code=status.HTTP_403_FORBIDDEN)

    # 실제 구현에서는 이벤트 목록 조회
    # 현재는 스텁 응답
    return JSONResponse(content={"events": []})


# read-only 보장: GET 외의 메서드는 405
@app.post("/v1/gateway/strategies/{strategy_id}/status")
@app.put("/v1/gateway/strategies/{strategy_id}/status")
@app.delete("/v1/gateway/strategies/{strategy_id}/status")
@app.post("/v1/gateway/callbacks")
@app.put("/v1/gateway/callbacks")
@app.delete("/v1/gateway/callbacks")
@app.post("/v1/gateway/nodes")
@app.put("/v1/gateway/nodes")
@app.delete("/v1/gateway/nodes")
@app.post("/v1/gateway/events")
@app.put("/v1/gateway/events")
@app.delete("/v1/gateway/events")
def method_not_allowed(*args, **kwargs):
    """읽기 전용 API에 대한 변경 메서드 접근 시 메서드 불허 응답."""
    return Response(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)


if __name__ == "__main__":
    import uvicorn

    print("=== FastAPI 라우트 목록 ===")
    for route in app.routes:
        print(f"{route.path} {route.methods}")

    uvicorn.run(app, host="0.0.0.0", port=8000)
