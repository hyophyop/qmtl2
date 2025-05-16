from fastapi import FastAPI
from fastapi.testclient import TestClient

from qmtl.common.errors.exceptions import (
    AuthError,
    DatabaseError,
    HTTPError,
    NotFoundError,
    QMTLError,
    ValidationError,
)
from qmtl.common.errors.handlers import register_qmtl_exception_handlers


def test_qmtl_exception_hierarchy():
    assert issubclass(DatabaseError, QMTLError)
    assert issubclass(ValidationError, QMTLError)
    assert issubclass(NotFoundError, QMTLError)
    assert issubclass(AuthError, QMTLError)
    assert issubclass(HTTPError, QMTLError)


def test_http_error_fields():
    err = HTTPError(detail="fail", status_code=400)
    assert err.detail == "fail"
    assert err.status_code == 400


def test_fastapi_exception_handler():
    app = FastAPI()
    register_qmtl_exception_handlers(app)

    @app.get("/err")
    def err():
        raise HTTPError("bad", 418)

    client = TestClient(app)
    resp = client.get("/err")
    assert resp.status_code == 418
    assert resp.json()["detail"] == "bad"
