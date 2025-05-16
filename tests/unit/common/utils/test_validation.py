import pytest
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from qmtl.common.utils.validation import assert_valid_model, is_valid_model, validate_model


class BarModel(BaseModel):
    foo: int
    bar: str
    model_config = {"extra": "forbid"}


def test_validate_model_success():
    data = {"foo": 1, "bar": "a"}
    m = validate_model(BarModel, data)
    assert m.foo == 1 and m.bar == "a"


def test_is_valid_model():
    assert is_valid_model(BarModel, {"foo": 1, "bar": "b"})
    assert not is_valid_model(BarModel, {"foo": "x", "bar": 2})


def test_assert_valid_model_success():
    assert_valid_model(BarModel, {"foo": 2, "bar": "c"})


def test_assert_valid_model_fail():
    with pytest.raises(PydanticValidationError):
        assert_valid_model(BarModel, {"foo": "bad", "bar": 1})
