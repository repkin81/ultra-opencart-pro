from typing import Any

import httpx


class OpenCartError(RuntimeError):
    pass


class OpenCartClient:
    """Small JSON API client for an OpenCart-compatible API endpoint."""

    def __init__(self, base_url: str, api_key: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"}

    def request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        headers = {**self._headers(), **kwargs.pop("headers", {})}
        response = httpx.request(method, url, headers=headers, timeout=self.timeout, **kwargs)
        if response.is_error:
            raise OpenCartError(f"OpenCart API {response.status_code}: {response.text[:500]}")
        if not response.content:
            return None
        return response.json()

    def get(self, path: str, **kwargs: Any) -> Any:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> Any:
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> Any:
        return self.request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> Any:
        return self.request("DELETE", path, **kwargs)
