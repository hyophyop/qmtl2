from fastapi import APIRouter, HTTPException, Request
from qmtl.models.generated.qmtl_callback_pb2 import NodeCallbackRequest, NodeCallbackEvent
from qmtl.dag_manager.registry.services.node.callback import NodeCallbackService

router = APIRouter()

# 임시 인메모리 서비스 인스턴스 (실제 환경에선 DI/싱글턴/DB 연동 필요)
callback_service = NodeCallbackService()


# FastAPI의 response_model은 Pydantic만 허용하므로, 실제 운영에서는 별도 변환 필요
@router.post("/v1/registry/nodes/{node_id}/callbacks")
async def register_callback(node_id: str, req: Request):
    data = await req.json()
    if "callback_type" in data:
        data["callback_type"] = data["callback_type"].upper()
    pb_req = NodeCallbackRequest(**data)
    if node_id != pb_req.node_id:
        raise HTTPException(status_code=400, detail="Node ID mismatch")
    result = callback_service.register_callback(pb_req)
    return {"success": result.success, "message": result.message}


@router.delete("/v1/registry/nodes/{node_id}/callbacks")
def unregister_callback(node_id: str, callback_type: str, url: str):
    # callback_type을 enum int로 변환
    callback_type_enum = callback_type.upper()
    from qmtl.models.generated.qmtl_callback_pb2 import NodeCallbackType
    callback_type_value = NodeCallbackType.Value(callback_type_enum)
    result = callback_service.unregister_callback(node_id, callback_type_value, url)
    return {"success": result.success, "message": result.message}


@router.get("/v1/registry/nodes/{node_id}/callbacks")
def list_callbacks(node_id: str):
    return callback_service.list_callbacks(node_id)


@router.post("/v1/registry/nodes/{node_id}/callbacks/trigger")
async def trigger_callbacks(node_id: str, req: Request):
    data = await req.json()
    if "callback_type" in data:
        data["callback_type"] = data["callback_type"].upper()
    pb_event = NodeCallbackEvent(**data)
    if node_id != pb_event.node_id:
        raise HTTPException(status_code=400, detail="Node ID mismatch")
    results = callback_service.trigger_callbacks(pb_event)
    return [{"success": r.success, "message": r.message} for r in results]
