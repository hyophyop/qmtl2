import logging
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, MutableMapping, Optional
from enum import Enum

from qmtl.common.errors.exceptions import StatusServiceError
from qmtl.models.datanode import DataNode
from qmtl.models.generated.qmtl_status_pb2 import NodeStatus, PipelineStatus
from google.protobuf.json_format import MessageToDict, ParseDict
from google.protobuf.timestamp_pb2 import Timestamp

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

    def _to_str(self, v):
        if isinstance(v, Enum):
            return v.value
        return str(v) if v is not None else ""

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
                now_dt = datetime.now()
                now = Timestamp()
                now.FromDatetime(now_dt)
                safe_params = dict(params or {}).copy()
                params_dict = {str(k): self._to_str(v) for k, v in safe_params.items()}
                params_dict = dict(params_dict)  # dict로 강제 변환
                print(f"[DEBUG] params_dict for PipelineStatus: {params_dict}")
                print(f"[DEBUG] param types: {[type(v) for v in params_dict.values()]}")
                ps = PipelineStatus(
                    pipeline_id=pipeline_id,
                    status="PENDING",
                    progress=0.0,
                )
                ps.start_time.CopyFrom(now)
                ps.last_update.CopyFrom(now)
                ps.params.update(params_dict)
                self.pipelines[pipeline_id] = ps
                self.nodes[pipeline_id] = {}
                for node in nodes:
                    self.nodes[pipeline_id][node.node_id] = NodeStatus(
                        node_id=node.node_id,
                        status="PENDING",
                    )
                logger.info(f"Pipeline {pipeline_id} status initialized with {len(nodes)} nodes")
        except Exception as e:
            logger.error(f"Failed to initialize pipeline status: {e}")
            raise StatusServiceError(f"Failed to initialize pipeline status: {e}")

    def update_pipeline_status(
        self,
        pipeline_id: str,
        status: str,
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
                update_dict = MessageToDict(pipeline)
                update_dict["status"] = status
                now = Timestamp()
                now.FromDatetime(datetime.now())
                update_dict["last_update"] = now.ToJsonString()
                if status in ("COMPLETED", "FAILED"):
                    end_ts = Timestamp()
                    end_ts.FromDatetime(datetime.now())
                    update_dict["end_time"] = end_ts.ToJsonString()
                    if status == "COMPLETED":
                        update_dict["progress"] = 100.0
                if result is not None:
                    if isinstance(result, dict):
                        safe_result = dict(result).copy()
                        update_dict["result"] = {
                            str(k): str(v) if v is not None else "" for k, v in safe_result.items()
                        }
                    else:
                        update_dict["result"] = str(result)
                self.pipelines[pipeline_id] = ParseDict(update_dict, PipelineStatus())
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
        status: str,
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
                update_dict = MessageToDict(node)
                update_dict["status"] = status
                if status == "RUNNING" and not update_dict.get("start_time"):
                    ts = Timestamp()
                    ts.FromDatetime(datetime.now())
                    update_dict["start_time"] = ts.ToJsonString()
                if status in ("COMPLETED", "FAILED") and not update_dict.get("end_time"):
                    ts = Timestamp()
                    ts.FromDatetime(datetime.now())
                    update_dict["end_time"] = ts.ToJsonString()
                if hasattr(node, "function_name"):
                    update_dict["function_name"] = getattr(node, "function_name", "")
                if hasattr(node, "tags"):
                    update_dict["tags"] = getattr(node, "tags", [])
                if result is not None:
                    if isinstance(result, dict):
                        safe_result = dict(result).copy()
                        update_dict["result"] = {
                            str(k): str(v) if v is not None else "" for k, v in safe_result.items()
                        }
                    else:
                        update_dict["result"] = str(result)
                    if pipeline_id in self.pipelines:
                        pipeline = self.pipelines[pipeline_id]
                        pipeline_dict = MessageToDict(pipeline)
                        if "result" not in pipeline_dict or pipeline_dict["result"] is None:
                            pipeline_dict["result"] = {}
                        if not isinstance(pipeline_dict["result"], dict):
                            pipeline_dict["result"] = {}
                        pipeline_dict["result"][node_id] = result
                        self.pipelines[pipeline_id] = ParseDict(pipeline_dict, PipelineStatus())
                pipeline_nodes[node_id] = ParseDict(update_dict, NodeStatus())
                self._update_pipeline_progress(pipeline_id)
                logger.info(f"Node {node_id} in pipeline {pipeline_id} status updated to {status}")
                if status == "COMPLETED" and isinstance(result, dict) and "recovery" in result:
                    logger.info(
                        f"Node {node_id} in pipeline {pipeline_id} recovery info: "
                        f"{result['recovery']}"
                    )
        except ValueError as e:
            logger.error(f"Invalid pipeline or node: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to update node status: {e}")
            raise StatusServiceError(f"Failed to update node status: {e}")

    def get_pipeline_status(self, pipeline_id: str) -> Optional[PipelineStatus]:
        """파이프라인 상태 조회

        Args:
            pipeline_id: 파이프라인 ID

        Returns:
            파이프라인 상태 정보 또는 None (존재하지 않는 경우)
        """
        with self._lock:
            return self.pipelines.get(pipeline_id)

    def get_node_status(self, pipeline_id: str, node_id: str) -> Optional[NodeStatus]:
        """노드 상태 조회

        Args:
            pipeline_id: 파이프라인 ID
            node_id: 노드 ID

        Returns:
            노드 상태 정보 또는 None (존재하지 않는 경우)
        """
        with self._lock:
            pipeline_nodes = self.nodes.get(pipeline_id, {})
            return pipeline_nodes.get(node_id)

    def get_all_node_statuses(self, pipeline_id: str) -> Dict[str, NodeStatus]:
        """파이프라인의 모든 노드 상태 조회

        Args:
            pipeline_id: 파이프라인 ID

        Returns:
            노드 ID를 키로 하는 상태 정보 딕셔너리
        """
        with self._lock:
            if pipeline_id not in self.nodes:
                return {}
            return {node_id: node for node_id, node in self.nodes[pipeline_id].items()}

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
            1 for node in pipeline_nodes.values() if node.status in ("COMPLETED", "FAILED")
        )

        # 진행 중인 노드 수 (부분 진행으로 계산)
        running_nodes = sum(0.5 for node in pipeline_nodes.values() if node.status == "RUNNING")

        # 진행률 계산 및 업데이트
        progress = (completed_nodes + running_nodes) / total_nodes * 100

        # Pydantic 모델 업데이트
        pipeline = self.pipelines[pipeline_id]
        pipeline_dict = MessageToDict(pipeline)
        now = Timestamp()
        now.FromDatetime(datetime.now())
        pipeline_dict["progress"] = round(progress, 1)
        pipeline_dict["last_update"] = now.ToJsonString()
        self.pipelines[pipeline_id] = ParseDict(pipeline_dict, PipelineStatus())

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
