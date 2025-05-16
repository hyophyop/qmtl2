from pydantic import BaseModel, field_validator

from qmtl.common.utils.serialization import (
    dict_to_model,
    json_to_model,
    model_to_dict,
    model_to_json,
)


class FooModel(BaseModel):
    foo: str
    bar: int

    @field_validator("foo", mode="before")
    def foo_upper(cls, v):
        return v.upper()

    model_config = {"extra": "forbid"}


def test_model_to_dict_and_back():
    m = FooModel(foo="abc", bar=1)
    d = model_to_dict(m)
    assert d == {"foo": "ABC", "bar": 1}
    m2 = dict_to_model(FooModel, d)
    assert m2.foo == "ABC"
    assert m2.bar == 1


def test_model_to_json_and_back():
    m = FooModel(foo="xyz", bar=2)
    s = model_to_json(m)
    m2 = json_to_model(FooModel, s)
    assert m2.foo == "XYZ"
    assert m2.bar == 2
