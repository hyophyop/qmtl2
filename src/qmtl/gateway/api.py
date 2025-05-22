from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from qmtl.common.errors.handlers import add_exception_handlers
from qmtl.orchestrator.services.execution.status_service import StatusService

app = FastAPI(title="QMTL Gateway API", description="Gateway API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
add_exception_handlers(app)

status_service = StatusService()


@app.get("/")
async def health() -> dict:
    return {"status": "ok", "service": "gateway"}


@app.get("/v1/gateway/strategies")
async def list_strategies() -> dict:
    """Return currently known strategy(pipeline) identifiers."""
    strategy_ids = list(status_service.pipelines.keys())
    return {"strategies": strategy_ids}


@app.get("/v1/gateway/strategies/{strategy_id}/status")
async def get_strategy_status(strategy_id: str) -> dict:
    """Return status information for a given strategy."""
    status = status_service.get_pipeline_status(strategy_id)
    if not status:
        raise HTTPException(status_code=404, detail="strategy not found")
    return {"status": status}
