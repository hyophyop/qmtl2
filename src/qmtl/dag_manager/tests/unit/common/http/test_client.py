from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

from qmtl.common.errors.exceptions import QMTLError
from qmtl.common.http.auth import BasicAuth, BearerAuth
from qmtl.common.http.client import HTTPClient, HTTPRequest


class DummyResponseModel(BaseModel):
    foo: str
    bar: int
    model_config = {"extra": "forbid"}


def test_http_client_request_json(monkeypatch):
    client = HTTPClient()
    req = HTTPRequest(url="https://api.test.com/data", method="POST", json={"foo": "abc", "bar": 1})
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"content-type": "application/json"}
    mock_resp.json.return_value = {"foo": "abc", "bar": 1}
    with patch("httpx.Client.request", return_value=mock_resp):
        resp = client.request(req, response_model=DummyResponseModel)
        assert isinstance(resp, DummyResponseModel)
        assert resp.foo == "abc"
        assert resp.bar == 1


def test_http_client_request_text(monkeypatch):
    client = HTTPClient()
    req = HTTPRequest(url="https://api.test.com/ping", method="GET")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"content-type": "text/plain"}
    mock_resp.text = "pong"
    with patch("httpx.Client.request", return_value=mock_resp):
        resp = client.request(req)
        assert resp.status_code == 200
        assert resp.body == "pong"


def test_http_client_auth_bearer(monkeypatch):
    client = HTTPClient()
    req = HTTPRequest(
        url="https://api.test.com/secure", method="GET", auth=BearerAuth(token="abc123").as_httpx()
    )
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"content-type": "application/json"}
    mock_resp.json.return_value = {"foo": "bar", "bar": 2}
    with patch("httpx.Client.request", return_value=mock_resp) as mock_request:
        client.request(req)
        called_args = mock_request.call_args[1]
        assert isinstance(called_args["auth"], object)


def test_http_client_auth_basic(monkeypatch):
    client = HTTPClient()
    req = HTTPRequest(
        url="https://api.test.com/secure",
        method="GET",
        auth=BasicAuth(username="u", password="p").as_httpx(),
    )
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"content-type": "application/json"}
    mock_resp.json.return_value = {"foo": "bar", "bar": 2}
    with patch("httpx.Client.request", return_value=mock_resp) as mock_request:
        client.request(req)
        called_args = mock_request.call_args[1]
        assert isinstance(called_args["auth"], object)


def test_http_client_http_error(monkeypatch):
    client = HTTPClient()
    req = HTTPRequest(url="https://api.test.com/fail", method="GET")
    with patch("httpx.Client.request", side_effect=Exception("fail")):
        with pytest.raises(QMTLError):
            client.request(req)


def test_with_retry_success():
    from qmtl.common.http.retry import with_retry

    calls = []

    @with_retry
    def fn():
        calls.append(1)
        return 42

    assert fn() == 42
    assert len(calls) == 1


def test_with_retry_retry(monkeypatch):
    from qmtl.common.http.retry import with_retry

    calls = []

    @with_retry
    def fn():
        calls.append(1)
        if len(calls) < 3:
            raise ValueError("fail")
        return 99

    assert fn(max_retries=3, backoff=0) == 99
    assert len(calls) == 3
