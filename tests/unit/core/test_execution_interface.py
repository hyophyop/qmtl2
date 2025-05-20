import pytest
from qmtl.dag_manager.execution.execution_interface import ExecutionServiceInterface

# 추상클래스 구현 강제 및 NotImplementedError 확인
class DummyExecutionService(ExecutionServiceInterface):
    def trigger_pipeline(self, strategy_version_id: str, params: dict):
        return f"triggered:{strategy_version_id}"
    def track_status(self, pipeline_id: str):
        return f"status:{pipeline_id}"

def test_execution_service_interface_abstract():
    # 추상 메서드 미구현 시 인스턴스화 불가
    with pytest.raises(TypeError):
        ExecutionServiceInterface()

def test_execution_service_interface_impl():
    # 구현체는 정상적으로 동작해야 함
    svc = DummyExecutionService()
    assert svc.trigger_pipeline("ver1", {}) == "triggered:ver1"
    assert svc.track_status("pipe1") == "status:pipe1"
