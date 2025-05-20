from unittest.mock import MagicMock

from qmtl.dag_manager.registry.services.node.neo4j_schema import get_schema_cypher, init_neo4j_schema


def test_get_schema_cypher_returns_cypher_list():
    cyphers = get_schema_cypher()
    assert isinstance(cyphers, list)
    assert any("DataNode" in c for c in cyphers)
    assert any("StrategyVersion" in c for c in cyphers)
    assert any("ActivationHistory" in c for c in cyphers)
    assert any("DEPENDS_ON" in c for c in cyphers)
    assert any("CONTAINS" in c for c in cyphers)
    assert any("ACTIVATED_BY" in c for c in cyphers)


def test_init_neo4j_schema_calls_execute_query_for_each_cypher():
    mock_client = MagicMock()
    cyphers = get_schema_cypher()
    init_neo4j_schema(mock_client)
    # 각 쿼리가 한 번씩 호출되는지 확인
    [((c,),) for c in cyphers]
    actual_calls = [call[0][0].strip() for call in mock_client.execute_query.call_args_list]
    for c in cyphers:
        assert any(c.strip() == ac for ac in actual_calls)
