from unittest.mock import MagicMock, patch

import pytest

from qmtl.common.db.connection_pool import Neo4jConnectionPool
from qmtl.common.errors.exceptions import DatabaseError


def test_singleton():
    pool1 = Neo4jConnectionPool("bolt://localhost:7687", "neo4j", "password")
    pool2 = Neo4jConnectionPool()
    assert pool1 is pool2


def test_get_and_release_client():
    with patch(
        "qmtl.common.db.connection_pool.Neo4jClient", side_effect=lambda *a, **kw: MagicMock()
    ) as MockClient:
        pool = Neo4jConnectionPool("bolt://localhost:7687", "neo4j", "password", max_size=2)
        client = pool.get_client()
        assert hasattr(client, "close")
        pool.release_client(client)
        client2 = pool.get_client()
        assert hasattr(client2, "close")
        pool.release_client(client2)
        pool.close_all()


def test_client_context_manager():
    with patch(
        "qmtl.common.db.connection_pool.Neo4jClient", side_effect=lambda *a, **kw: MagicMock()
    ) as MockClient:
        pool = Neo4jConnectionPool("bolt://localhost:7687", "neo4j", "password", max_size=1)
        with pool.client() as client:
            assert hasattr(client, "close")
        pool.close_all()


def test_get_client_exception():
    with patch("qmtl.common.db.connection_pool.Neo4jClient", side_effect=Exception("fail")):
        pool = Neo4jConnectionPool("bolt://localhost:7687", "neo4j", "password", max_size=1)
        with pytest.raises(DatabaseError):
            pool.get_client()
        pool.close_all()
