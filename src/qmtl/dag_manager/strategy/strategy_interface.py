from abc import ABC, abstractmethod


class StrategyServiceInterface(ABC):
    """Orchestrator 전략 도메인 서비스 인터페이스"""

    @abstractmethod
    def parse_strategy(self, strategy_code: str):
        pass

    @abstractmethod
    def extract_decorators(self, strategy_code: str):
        pass

    @abstractmethod
    def get_strategy_dag(self, version_id: str):
        pass
