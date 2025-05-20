from __future__ import annotations

"""QueueWorker
==============
ReadyNodeSelector 결과를 큐에 enqueue 하고,
작업 완료 시 상태 및 큐 결과를 갱신하는 유틸리티.

(실제 환경에서는 분리된 consumer 가 노드 실행을 담당하겠지만
여기서는 간단한 헬퍼 클래스로 구현한다.)
"""

from typing import List, Any, Callable
from qmtl.models.datanode import DataNode


class QueueWorker:
    def __init__(
        self,
        push_fn: Callable[[str], None],
        update_status_fn: Callable[[str, str], None],
        complete_fn: Callable[[str, Any], bool],
    ):
        self.push_fn = push_fn
        self.update_status_fn = update_status_fn
        self.complete_fn = complete_fn

    def enqueue_ready_nodes(self, ready_nodes: List[DataNode]) -> List[DataNode]:
        """ready 상태 노드를 큐에 등록하고 리스트 반환"""
        for node in ready_nodes:
            self.push_fn(node.node_id)
            self.update_status_fn(node.node_id, "READY")
        return ready_nodes

    def complete_node(self, node_id: str, result: Any = None) -> bool:
        """노드 실행 완료 처리 (상태, 큐 결과)"""
        self.update_status_fn(node_id, "COMPLETED")
        return self.complete_fn(node_id, result)
