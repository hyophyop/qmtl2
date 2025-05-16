from qmtl.models.analyzer import AnalyzerActivateRequest, AnalyzerDefinition
from qmtl.orchestrator.services.analyzer import AnalyzerService


def test_register_and_get_analyzer():
    definition = AnalyzerDefinition(
        name="test-analyzer",
        description="unit test analyzer",
        tags=["ANALYZER", "TEST"],
        source="print('hello')",
        parameters={"foo": "bar"},
    )
    meta = AnalyzerService.register_analyzer(definition)
    assert meta.analyzer_id
    assert meta.name == "test-analyzer"
    fetched = AnalyzerService.get_analyzer(meta.analyzer_id)
    assert fetched is not None
    assert fetched.analyzer_id == meta.analyzer_id


def test_activate_analyzer_and_get_results():
    definition = AnalyzerDefinition(
        name="activate-analyzer",
        description="activate test",
        tags=["ANALYZER"],
        source="print('activate')",
        parameters={},
    )
    meta = AnalyzerService.register_analyzer(definition)
    req = AnalyzerActivateRequest(mode="LIVE", parameters={})
    activated = AnalyzerService.activate_analyzer(meta.analyzer_id, req)
    assert activated.status == "ACTIVE"
    result = AnalyzerService.get_results(meta.analyzer_id)
    assert result is not None
    assert result.status == "SUCCESS"
    assert result.analyzer_id == meta.analyzer_id
