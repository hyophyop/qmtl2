# __main__.py: gateway.py의 엔트리포인트를 그대로 복사
from .gateway import app

if __name__ == "__main__":
    import uvicorn

    print("=== FastAPI 라우트 목록 ===")
    for route in app.routes:
        print(f"{route.path} {route.methods}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
