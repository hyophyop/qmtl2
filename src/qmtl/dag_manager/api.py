"""FastAPI skeleton for the DAG Manager service."""

import logging
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .services.metadata_service import MetadataService
from .services.node_service import NodeService
from .services.stream_service import StreamService
from .services.dependency_service import DependencyService


app = FastAPI(title="QMTL DAG Manager API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)


def get_metadata_service() -> MetadataService:
    node_service = NodeService()
    stream_service = StreamService()
    dependency_service = DependencyService()
    return MetadataService(node_service, stream_service, dependency_service)


# ----------------------- API Endpoints -----------------------


@app.get("/v1/dag-manager/nodes")
async def list_nodes(service: MetadataService = Depends(get_metadata_service)):
    try:
        return {"nodes": service.list_nodes()}
    except NotImplementedError:
        logger.debug("list_nodes not implemented")
        raise HTTPException(status_code=501, detail="NotImplemented")


@app.get("/v1/dag-manager/nodes/{node_id}/dependencies")
async def list_node_dependencies(
    node_id: str, service: MetadataService = Depends(get_metadata_service)
):
    try:
        return {"dependencies": service.get_node_dependencies(node_id)}
    except NotImplementedError:
        logger.debug("get_node_dependencies not implemented")
        raise HTTPException(status_code=501, detail="NotImplemented")


@app.get("/v1/dag-manager/nodes/by-tags")
async def list_nodes_by_tags(
    tags: List[str] = Query(...), service: MetadataService = Depends(get_metadata_service)
):
    try:
        return {"nodes": service.list_nodes_by_tags(tags)}
    except NotImplementedError:
        logger.debug("list_nodes_by_tags not implemented")
        raise HTTPException(status_code=501, detail="NotImplemented")


@app.get("/v1/dag-manager/streams")
async def list_streams(service: MetadataService = Depends(get_metadata_service)):
    try:
        return {"streams": service.list_streams()}
    except NotImplementedError:
        logger.debug("list_streams not implemented")
        raise HTTPException(status_code=501, detail="NotImplemented")


@app.get("/v1/dag-manager/events")
async def list_events():
    raise HTTPException(status_code=501, detail="NotImplemented")


@app.get("/v1/dag-manager/nodes/{node_id}/callbacks")
async def list_callbacks(node_id: str, service: MetadataService = Depends(get_metadata_service)):
    try:
        return {"callbacks": service.list_callbacks(node_id)}
    except NotImplementedError:
        logger.debug("list_callbacks not implemented")
        raise HTTPException(status_code=501, detail="NotImplemented")
