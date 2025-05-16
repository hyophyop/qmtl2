from typing import Any, Dict, Optional, Type, TypeVar, Union

import httpx
from pydantic import BaseModel, field_validator

from qmtl.common.errors.exceptions import QMTLError
from qmtl.common.http.retry import with_retry

T = TypeVar("T", bound=BaseModel)


class HTTPRequest(BaseModel):
    url: str
    method: str = "GET"
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, Any]] = None
    data: Optional[Any] = None
    json: Optional[Any] = None
    timeout: Optional[float] = 10.0
    auth: Optional[Any] = None

    @field_validator("method", mode="before")
    def method_upper(cls, v):
        return v.upper()

    model_config = {"extra": "forbid"}


class HTTPResponse(BaseModel):
    status_code: int
    headers: Dict[str, str]
    body: Any

    model_config = {"extra": "forbid"}


class HTTPClient:
    """Pydantic 기반 동기/비동기 HTTP 클라이언트 (httpx 래퍼)"""

    def __init__(
        self, base_url: Optional[str] = None, default_headers: Optional[Dict[str, str]] = None
    ):
        self.base_url = base_url
        self.default_headers = default_headers or {}
        client_kwargs = {"headers": self.default_headers}
        if base_url is not None:
            client_kwargs["base_url"] = base_url
        self._client = httpx.Client(**client_kwargs)
        self._async_client = httpx.AsyncClient(**client_kwargs)

    @with_retry
    def request(
        self, req: HTTPRequest, response_model: Optional[Type[T]] = None
    ) -> Union[HTTPResponse, T]:
        try:
            resp = self._client.request(
                method=req.method,
                url=req.url,
                headers=req.headers,
                params=req.params,
                data=req.data,
                json=req.json,  # json_content -> json으로 매개변수 이름 수정
                timeout=req.timeout,
                auth=req.auth,
            )
            http_resp = HTTPResponse(
                status_code=resp.status_code,
                headers=dict(resp.headers),
                body=(
                    resp.json()
                    if "application/json" in resp.headers.get("content-type", "")
                    else resp.text
                ),
            )
            if response_model:
                return response_model.model_validate(http_resp.body)
            return http_resp
        except Exception as e:
            raise QMTLError(f"HTTP 요청 실패: {str(e)}")

    @with_retry
    async def arequest(
        self, req: HTTPRequest, response_model: Optional[Type[T]] = None
    ) -> Union[HTTPResponse, T]:
        try:
            resp = await self._async_client.request(
                method=req.method,
                url=req.url,
                headers=req.headers,
                params=req.params,
                data=req.data,
                json=req.json,
                timeout=req.timeout,
                auth=req.auth,
            )
            http_resp = HTTPResponse(
                status_code=resp.status_code,
                headers=dict(resp.headers),
                body=(
                    resp.json()
                    if "application/json" in resp.headers.get("content-type", "")
                    else resp.text
                ),
            )
            if response_model:
                return response_model.model_validate(http_resp.body)
            return http_resp
        except Exception as e:
            raise QMTLError(f"HTTP 요청 실패: {str(e)}")

    def close(self):
        self._client.close()
        import asyncio

        if not self._async_client.is_closed:
            asyncio.get_event_loop().run_until_complete(self._async_client.aclose())

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
