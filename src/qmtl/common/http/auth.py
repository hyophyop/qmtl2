import httpx
from pydantic import BaseModel


class BearerAuth(BaseModel):
    token: str

    def as_httpx(self) -> httpx.Auth:
        class _BearerAuth(httpx.Auth):
            def auth(self, request):
                request.headers["Authorization"] = f"Bearer {self.token}"
                return request

        return _BearerAuth()


class BasicAuth(BaseModel):
    username: str
    password: str

    def as_httpx(self) -> httpx.Auth:
        return httpx.BasicAuth(self.username, self.password)
