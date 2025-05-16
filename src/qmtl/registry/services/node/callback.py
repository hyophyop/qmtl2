from typing import List, Optional
from qmtl.models.callback import NodeCallbackType, NodeCallbackRequest, NodeCallbackResponse, NodeCallbackEvent

class NodeCallbackService:
    """
    노드 콜백 등록/해제/조회/트리거 도메인 서비스 (Registry)
    실제 구현은 Neo4j/Memory 등으로 분리 가능
    """
    def __init__(self):
        # {node_id: {callback_type: [callback_info, ...]}}
        self._callbacks = {}

    def register_callback(self, req: NodeCallbackRequest) -> NodeCallbackResponse:
        node_cbs = self._callbacks.setdefault(req.node_id, {})
        cb_list = node_cbs.setdefault(req.callback_type, [])
        cb_info = {
            "url": req.url,
            "metadata": req.metadata,
        }
        cb_list.append(cb_info)
        return NodeCallbackResponse(success=True, message="Callback registered.")

    def unregister_callback(self, node_id: str, callback_type: NodeCallbackType, url: str) -> NodeCallbackResponse:
        node_cbs = self._callbacks.get(node_id, {})
        cb_list = node_cbs.get(callback_type, [])
        before = len(cb_list)
        cb_list = [cb for cb in cb_list if cb["url"] != url]
        node_cbs[callback_type] = cb_list
        after = len(cb_list)
        return NodeCallbackResponse(success=before != after, message="Callback unregistered." if before != after else "Not found.")

    def list_callbacks(self, node_id: str) -> List[dict]:
        return self._callbacks.get(node_id, {})

    def trigger_callbacks(self, event: NodeCallbackEvent) -> List[NodeCallbackResponse]:
        node_cbs = self._callbacks.get(event.node_id, {})
        cb_list = node_cbs.get(event.callback_type, [])
        # 실제로는 HTTP POST 등으로 콜백 호출해야 함 (여기선 단순히 응답만)
        responses = []
        for cb in cb_list:
            responses.append(NodeCallbackResponse(success=True, message=f"Callback to {cb['url']} triggered."))
        return responses
