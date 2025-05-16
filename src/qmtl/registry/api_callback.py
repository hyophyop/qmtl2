from fastapi import APIRouter, Depends, HTTPException
from qmtl.models.callback import NodeCallbackRequest, NodeCallbackResponse, NodeCallbackEvent
from qmtl.registry.services.node.callback import NodeCallbackService

router = APIRouter()

# 임시 인메모리 서비스 인스턴스 (실제 환경에선 DI/싱글턴/DB 연동 필요)
callback_service = NodeCallbackService()

@router.post("/v1/registry/nodes/{node_id}/callbacks", response_model=NodeCallbackResponse)
def register_callback(node_id: str, req: NodeCallbackRequest):
    if node_id != req.node_id:
        raise HTTPException(status_code=400, detail="Node ID mismatch")
    return callback_service.register_callback(req)

@router.delete("/v1/registry/nodes/{node_id}/callbacks", response_model=NodeCallbackResponse)
def unregister_callback(node_id: str, callback_type: str, url: str):
    return callback_service.unregister_callback(node_id, callback_type, url)

@router.get("/v1/registry/nodes/{node_id}/callbacks")
def list_callbacks(node_id: str):
    return callback_service.list_callbacks(node_id)

@router.post("/v1/registry/nodes/{node_id}/callbacks/trigger", response_model=list[NodeCallbackResponse])
def trigger_callbacks(node_id: str, event: NodeCallbackEvent):
    if node_id != event.node_id:
        raise HTTPException(status_code=400, detail="Node ID mismatch")
    return callback_service.trigger_callbacks(event)
