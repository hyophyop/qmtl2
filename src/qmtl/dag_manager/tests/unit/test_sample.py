from pydantic import BaseModel


def test_pytest_and_pydantic():
    class Foo(BaseModel):
        x: int

    m = Foo(x=1)
    assert m.x == 1
