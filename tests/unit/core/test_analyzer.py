import pytest
from qmtl.dag_manager import analyzer
from qmtl.models.analyzer import AnalyzerDefinition, AnalyzerActivateRequest


def test_analyzer_service_smoke():
    # Smoke test: AnalyzerService의 주요 메서드 정상 동작 확인
    definition = AnalyzerDefinition(
        name="test-analyzer",
        description="desc",
        tags=["t1"],
        parameters={"p": 1},
    )
    meta = analyzer.AnalyzerService.register_analyzer(definition)
    assert meta.name == "test-analyzer"
    fetched = analyzer.AnalyzerService.get_analyzer(meta.analyzer_id)
    assert fetched is not None
    req = AnalyzerActivateRequest()
    activated = analyzer.AnalyzerService.activate_analyzer(meta.analyzer_id, req)
    assert activated.status == "ACTIVE"
    result = analyzer.AnalyzerService.get_results(meta.analyzer_id)
    assert result is not None
