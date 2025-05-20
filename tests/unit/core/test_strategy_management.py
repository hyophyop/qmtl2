import pytest
from unittest.mock import MagicMock
from qmtl.dag_manager.registry.services.strategy.management import Neo4jStrategyManagementService
from qmtl.common.errors.exceptions import DatabaseError


def test_get_version_returns_none():
    service = Neo4jStrategyManagementService(neo4j_client=MagicMock())
    assert service.get_version("dummy_id") is None


def test_list_strategies_returns_empty_list():
    service = Neo4jStrategyManagementService(neo4j_client=MagicMock())
    assert service.list_strategies() == []


def test_get_version_database_error(monkeypatch):
    service = Neo4jStrategyManagementService(neo4j_client=MagicMock())
    monkeypatch.setattr(
        service, "get_version", lambda x: (_ for _ in ()).throw(DatabaseError("db error"))
    )
    with pytest.raises(DatabaseError):
        service.get_version("dummy_id")


def test_list_strategies_database_error(monkeypatch):
    service = Neo4jStrategyManagementService(neo4j_client=MagicMock())
    monkeypatch.setattr(
        service, "list_strategies", lambda: (_ for _ in ()).throw(DatabaseError("db error"))
    )
    with pytest.raises(DatabaseError):
        service.list_strategies()
