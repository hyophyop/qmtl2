from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel, field_validator

from qmtl.common.db.transaction import run_in_transaction
from qmtl.common.errors.exceptions import DatabaseError


class DummyModel(BaseModel):
    id: int
    name: str

    @field_validator("id", mode="before")
    def id_positive(cls, v):
        if v <= 0:
            raise ValueError("id must be positive")
        return v

    model_config = {"extra": "forbid"}


def test_run_in_transaction_success():
    # Arrange
    tx = MagicMock()

    def work(tx):
        return [{"id": 1, "name": "test"}]

    # Act
    result = run_in_transaction(tx, work)
    # Assert
    assert result == [{"id": 1, "name": "test"}]


def test_run_in_transaction_exception():
    # Arrange
    tx = MagicMock()

    def work(tx):
        raise RuntimeError("fail")

    # Act & Assert
    with pytest.raises(DatabaseError) as exc:
        run_in_transaction(tx, work)
    assert "트랜잭션 작업 실패" in str(exc.value)
