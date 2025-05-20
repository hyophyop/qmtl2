from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

from qmtl.common.db.neo4j_client import Neo4jClient
from qmtl.common.errors.exceptions import DatabaseError


class DummyModel(BaseModel):
    foo: int
    bar: str
    model_config = {"extra": "forbid"}


def test_init_success():
    with patch("qmtl.common.db.neo4j_client.GraphDatabase.driver") as mock_driver:
        client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")
        assert hasattr(client, "_driver")
        client.close()


def test_init_fail():
    with patch("qmtl.common.db.neo4j_client.GraphDatabase.driver", side_effect=Exception("fail")):
        with pytest.raises(DatabaseError):
            Neo4jClient("bolt://localhost:7687", "neo4j", "password")


def test_execute_query_success():
    client = Neo4jClient.__new__(Neo4jClient)
    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_result = [MagicMock(data=lambda: {"foo": 1, "bar": "a"})]
    mock_session.run.return_value = mock_result
    mock_driver.session.return_value.__enter__.return_value = mock_session
    client._driver = mock_driver
    result = client.execute_query("MATCH (n)")
    assert result == [{"foo": 1, "bar": "a"}]


def test_execute_query_fail():
    client = Neo4jClient.__new__(Neo4jClient)
    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_session.run.side_effect = Exception("fail")
    mock_driver.session.return_value.__enter__.return_value = mock_session
    client._driver = mock_driver
    with pytest.raises(DatabaseError):
        client.execute_query("MATCH (n)")


def test_execute_with_model_success():
    client = Neo4jClient.__new__(Neo4jClient)
    client.execute_query = MagicMock(return_value=[{"foo": 1, "bar": "a"}])
    result = client.execute_with_model("MATCH (n)", DummyModel)
    assert isinstance(result[0], DummyModel)
    assert result[0].foo == 1
    assert result[0].bar == "a"


def test_execute_with_model_fail():
    client = Neo4jClient.__new__(Neo4jClient)
    client.execute_query = MagicMock(return_value=[{"foo": "bad", "bar": 1}])
    with pytest.raises(DatabaseError):
        client.execute_with_model("MATCH (n)", DummyModel)


def test_execute_transaction_success():
    client = Neo4jClient.__new__(Neo4jClient)
    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_session.execute_write.return_value = [{"foo": 1, "bar": "a"}]
    mock_driver.session.return_value.__enter__.return_value = mock_session
    client._driver = mock_driver

    def work(tx):
        return [{"foo": 1, "bar": "a"}]

    result = client.execute_transaction(work)
    assert result == [{"foo": 1, "bar": "a"}]


def test_execute_transaction_fail():
    client = Neo4jClient.__new__(Neo4jClient)
    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_session.execute_write.side_effect = Exception("fail")
    mock_driver.session.return_value.__enter__.return_value = mock_session
    client._driver = mock_driver

    def work(tx):
        raise Exception("fail")

    with pytest.raises(DatabaseError):
        client.execute_transaction(work)
