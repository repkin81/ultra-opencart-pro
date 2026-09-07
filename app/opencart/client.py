from typing import Any

import httpx


class OpenCartError(RuntimeError):
    pass


class OpenCartClient:
    """HTTP client for the Ultra OpenCart PRO Connector for OpenCart 3.x."""

    def __init__(self, base_url: str, api_key: str, timeout: float = 30.0, api_route: str = 'extension/module/ultra_opencart_api'):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.api_route = api_route.strip('/')

    def _headers(self) -> dict[str, str]:
        return {
            'Authorization': f'Bearer {self.api_key}',
            'X-Ultra-Api-Key': self.api_key,
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

    def _url(self, path: str) -> str:
        if path.startswith('http://') or path.startswith('https://'):
            return path
        if path.startswith('?'):
            return f'{self.base_url}/index.php{path}'
        if path.startswith('index.php?'):
            return f'{self.base_url}/{path}'
        if path.startswith('api/'):
            path = path[4:]
        return f'{self.base_url}/index.php?route={self.api_route}/{path.lstrip("/")}'

    def request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = self._url(path)
        headers = {**self._headers(), **kwargs.pop('headers', {})}
        response = httpx.request(method, url, headers=headers, timeout=self.timeout, **kwargs)
        if response.is_error:
            raise OpenCartError(f'OpenCart API {response.status_code}: {response.text[:500]}')
        if not response.content:
            return None
        return response.json()

    def get(self, path: str, **kwargs: Any) -> Any:
        return self.request('GET', path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> Any:
        return self.request('POST', path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> Any:
        return self.request('PUT', path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> Any:
        return self.request('DELETE', path, **kwargs)
