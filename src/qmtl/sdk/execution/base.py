from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseExecutionEngine(ABC):
    """
    실행 엔진 공통 인터페이스 (추상 클래스)
    모든 실행 엔진(Local, Parallel, Mock 등)은 이 클래스를 상속해야 함
    """

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.results = {}
        self.node_execution_times = {}

    @abstractmethod
    def execute_pipeline(
        self, pipeline, inputs: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        파이프라인 실행 메서드 (구현 필수)
        """

    def get_execution_stats(self) -> Dict[str, Any]:
        """
        실행 통계 정보 조회 (선택 구현)
        """
        return {
            "node_execution_times": self.node_execution_times.copy(),
            "total_nodes": len(self.node_execution_times),
            "total_time": sum(self.node_execution_times.values()),
        }
