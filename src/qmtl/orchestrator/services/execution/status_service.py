import logging
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, MutableMapping, Optional, Union

from qmtl.common.errors.exceptions import StatusServiceError
from qmtl.models.datanode import DataNode
from qmtl.models.status import NodeStatus, PipelineStatus, StatusType

logger = logging.getLogger(__name__)

# Global singleton instance
_instance = None
_instance_lock = threading.Lock()


class StatusService:
    """파이프라인 상태 관리 서비스"""

    def __new__(cls):
        """싱글톤 패턴 구현"""
        global _instance
        with _instance_lock:
            if _instance is None:
                _instance = super(StatusService, cls).__new__(cls)
                # 초기화가 필요한 속성들
                _instance.pipelines = {}
                _instance.nodes = {}
                _instance._lock = threading.RLock()
                logger.info("StatusService singleton instance created")
            return _instance

    def __init__(self):
        """상태 서비스 초기화"""
        # __new__에서 이미 초기화된 경우 중복 초기화 방지
        if not hasattr(self, "pipelines"):
            # 타입 힌트를 명확히 함
            self.pipelines: MutableMapping[str, PipelineStatus] = (
                {}
            )  # 파이프라인 상태 저장 (실제 구현에서는 Redis 등 활용)
            self.nodes: MutableMapping[str, MutableMapping[str, NodeStatus]] = (
                {}
            )  # 노드별 상태 저장
            self._lock = threading.RLock()  # 스레드 안전성을 위한 락
            logger.info("StatusService instance initialized")

    def initialize_pipeline(
        self,
        pipeline_id: str,
        nodes: List[DataNode],
        params: Optional[Dict[str, Any]] = None,
    ) -> None:
        """파이프라인 상태 초기화

        Args:
            pipeline_id: 파이프라인 ID
            nodes: 노드 목록
            params: 파이프라인 파라미터

        Raises:
            StatusServiceError: 상태 초기화 실패 시
        """
        try:
            with self._lock:
                # 파이프라인 상태 초기화
                now = datetime.now()
                self.pipelines[pipeline_id] = PipelineStatus(
                    pipeline_id=pipeline_id,
                    status=StatusType.PENDING,
                    params=params or {},
                    start_time=now,
                    last_update=now,
                    progress=0.0,
                )

                # 노드별 상태 초기화
                self.nodes[pipeline_id] = {}
                for node in nodes:
                    self.nodes[pipeline_id][node.node_id] = NodeStatus(
                        node_id=node.node_id,
                        status=StatusType.PENDING,
                    )

                logger.info(f"Pipeline {pipeline_id} status initialized with {len(nodes)} nodes")

        except Exception as e:
            logger.error(f"Failed to initialize pipeline status: {e}")
            raise StatusServiceError(f"Failed to initialize pipeline status: {e}")

    def update_pipeline_status(
        self,
        pipeline_id: str,
        status: Union[str, StatusType],
        result: Optional[Dict[str, Any]] = None,
    ) -> None:
        """파이프라인 상태 업데이트

        Args:
            pipeline_id: 파이프라인 ID
            status: 상태 (PENDING, RUNNING, COMPLETED, FAILED)
            result: 결과 데이터

        Raises:
            ValueError: 파이프라인 ID가 유효하지 않은 경우
            StatusServiceError: 상태 업데이트 실패 시
        """
        try:
            with self._lock:
                if pipeline_id not in self.pipelines:
                    raise ValueError(f"Pipeline {pipeline_id} not found")

                pipeline = self.pipelines[pipeline_id]
                # 문자열 상태를 StatusType으로 변환
                status_enum = status if isinstance(status, StatusType) else StatusType(status)

                # Pydantic 모델 업데이트
                update_data = {"status": status_enum, "last_update": datetime.now()}

                if status_enum in (StatusType.COMPLETED, StatusType.FAILED):
                    update_data["end_time"] = datetime.now()
                    if status_enum == StatusType.COMPLETED:
                        update_data["progress"] = 100.0

                if result is not None:
                    update_data["result"] = result

                # 모델 업데이트
                pipeline_dict = pipeline.model_dump()
                pipeline_dict.update(update_data)
                self.pipelines[pipeline_id] = PipelineStatus.model_validate(pipeline_dict)

                logger.info(f"Pipeline {pipeline_id} status updated to {status}")

        except ValueError as e:
            logger.error(f"Pipeline not found: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to update pipeline status: {e}")
            raise StatusServiceError(f"Failed to update pipeline status: {e}")

    def update_node_status(
        self,
        pipeline_id: str,
        node_id: str,
        status: Union[str, StatusType],
        result: Optional[Dict[str, Any]] = None,
    ) -> None:
        """노드 상태 업데이트

        Args:
            pipeline_id: 파이프라인 ID
            node_id: 노드 ID
            status: 상태 (PENDING, RUNNING, COMPLETED, FAILED)
            result: 결과 데이터

        Raises:
            ValueError: 파이프라인 ID나 노드 ID가 유효하지 않은 경우
            StatusServiceError: 상태 업데이트 실패 시
        """
        try:
            with self._lock:
                if pipeline_id not in self.nodes:
                    raise ValueError(f"Pipeline {pipeline_id} not found")
                pipeline_nodes = self.nodes[pipeline_id]
                if node_id not in pipeline_nodes:
                    raise ValueError(f"Node {node_id} not found in pipeline {pipeline_id}")
                node = pipeline_nodes[node_id]
                status_enum = status if isinstance(status, StatusType) else StatusType(status)
                update_data = {"status": status_enum}
                if status_enum == StatusType.RUNNING and node.start_time is None:
                    update_data["start_time"] = datetime.now()
                if (
                    status_enum in (StatusType.COMPLETED, StatusType.FAILED)
                    and node.end_time is None
                ):
                    update_data["end_time"] = datetime.now()
                node_dict = node.model_dump()
                # 디버깅: 노드 상태 갱신 전 정보 출력
                logger.debug(
                    f"[update_node_status] pipeline_id={pipeline_id}, node_id={node_id}, status={status_enum}, function_name={node_dict.get('function_name','')}, tags={node_dict.get('tags',[])} result={result}"
                )
                if hasattr(node, "function_name") or "function_name" in node_dict:
                    update_data["function_name"] = node_dict.get("function_name", "")
                if result is not None:
                    update_data["result"] = result
                    if pipeline_id in self.pipelines:
                        pipeline = self.pipelines[pipeline_id]
                        pipeline_dict = pipeline.model_dump()
                        if "result" not in pipeline_dict or pipeline_dict["result"] is None:
                            pipeline_dict["result"] = {}
                        if not isinstance(pipeline_dict["result"], dict):
                            pipeline_dict["result"] = {}
                        # 모든 노드 결과를 항상 저장
                        pipeline_dict["result"][node_id] = result
                        self.pipelines[pipeline_id] = PipelineStatus.model_validate(pipeline_dict)
                node_dict.update(update_data)
                pipeline_nodes[node_id] = NodeStatus.model_validate(node_dict)
                self._update_pipeline_progress(pipeline_id)

                logger.info(f"Node {node_id} in pipeline {pipeline_id} status updated to {status}")
                if (
                    status_enum == StatusType.COMPLETED
                    and isinstance(result, dict)
                    and "recovery" in result
                ):
                    logger.info(
                        f"Node {node_id} completed with recovery flag: {result['recovery']}"
                    )

        except ValueError as e:
            logger.error(f"Invalid pipeline or node: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to update node status: {e}")
            raise StatusServiceError(f"Failed to update node status: {e}")

    def get_pipeline_status(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        """파이프라인 상태 조회

        Args:
            pipeline_id: 파이프라인 ID

        Returns:
            파이프라인 상태 정보 또는 None (존재하지 않는 경우)
        """
        with self._lock:
            pipeline = self.pipelines.get(pipeline_id)
            return pipeline.model_dump() if pipeline else None

    def get_node_status(self, pipeline_id: str, node_id: str) -> Optional[Dict[str, Any]]:
        """노드 상태 조회

        Args:
            pipeline_id: 파이프라인 ID
            node_id: 노드 ID

        Returns:
            노드 상태 정보 또는 None (존재하지 않는 경우)
        """
        with self._lock:
            pipeline_nodes = self.nodes.get(pipeline_id, {})
            node = pipeline_nodes.get(node_id)
            return node.model_dump() if node else None

    def get_all_node_statuses(self, pipeline_id: str) -> Dict[str, Dict[str, Any]]:
        """파이프라인의 모든 노드 상태 조회

        Args:
            pipeline_id: 파이프라인 ID

        Returns:
            노드 ID를 키로 하는 상태 정보 딕셔너리
        """
        with self._lock:
            if pipeline_id not in self.nodes:
                return {}
            return {node_id: node.model_dump() for node_id, node in self.nodes[pipeline_id].items()}

    def _update_pipeline_progress(self, pipeline_id: str) -> None:
        """파이프라인 진행 상황 업데이트

        Args:
            pipeline_id: 파이프라인 ID
        """
        if pipeline_id not in self.nodes or pipeline_id not in self.pipelines:
            return

        pipeline_nodes = self.nodes[pipeline_id]
        total_nodes = len(pipeline_nodes)

        if total_nodes == 0:
            return

        # 완료된 노드 수 계산
        completed_nodes = sum(
            1
            for node in pipeline_nodes.values()
            if node.status in (StatusType.COMPLETED, StatusType.FAILED)
        )

        # 진행 중인 노드 수 (부분 진행으로 계산)
        running_nodes = sum(
            0.5 for node in pipeline_nodes.values() if node.status == StatusType.RUNNING
        )

        # 진행률 계산 및 업데이트
        progress = (completed_nodes + running_nodes) / total_nodes * 100

        # Pydantic 모델 업데이트
        pipeline = self.pipelines[pipeline_id]
        pipeline_dict = pipeline.model_dump()
        pipeline_dict.update({"progress": round(progress, 1), "last_update": datetime.now()})

        self.pipelines[pipeline_id] = PipelineStatus.model_validate(pipeline_dict)

    def cleanup_pipeline(self, pipeline_id: str) -> None:
        """파이프라인 상태 정보 삭제 (리소스 정리)

        Args:
            pipeline_id: 파이프라인 ID
        """
        with self._lock:
            if pipeline_id in self.pipelines:
                del self.pipelines[pipeline_id]

            if pipeline_id in self.nodes:
                del self.nodes[pipeline_id]

            logger.info(f"Pipeline {pipeline_id} status data cleaned up")

    def cleanup_old_pipelines(self, max_age_hours: int = 24) -> int:
        """오래된 파이프라인 상태 정보 정리

        Args:
            max_age_hours: 최대 보관 시간 (시간)

        Returns:
            삭제된 파이프라인 수
        """
        with self._lock:
            now = datetime.now()
            cutoff = now - timedelta(hours=max_age_hours)

            pipelines_to_remove = []

            for pipeline_id, pipeline in self.pipelines.items():
                # Pydantic 모델의 last_update는 이미 datetime 객체
                if pipeline.last_update < cutoff:
                    pipelines_to_remove.append(pipeline_id)

            for pipeline_id in pipelines_to_remove:
                self.cleanup_pipeline(pipeline_id)

            logger.info(f"Cleaned up {len(pipelines_to_remove)} old pipelines")
            return len(pipelines_to_remove)
