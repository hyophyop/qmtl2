from abc import ABC, abstractmethod


class ExecutionServiceInterface(ABC):
    """Orchestrator 실행 도메인 서비스 인터페이스"""

    @abstractmethod
    def trigger_pipeline(self, strategy_version_id: str, params: dict):
        pass

    @abstractmethod
    def track_status(self, pipeline_id: str):
        pass
