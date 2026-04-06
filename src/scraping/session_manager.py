"""Lightweight HTTP session pool using httpx.AsyncClient with per-domain connection limits."""
from __future__ import annotations

from typing import Any

import httpx

from src.scraping.proxy_pool import ProxyPoolManager, proxy_pool
from src.utils.logging import get_logger

logger = get_logger(__name__)

DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}

class SessionManager:
    def __init__(self, proxy_pool_mgr: ProxyPoolManager | None = None, max_connections_per_domain: int = 5) -> None:
        self._proxy_pool = proxy_pool_mgr or proxy_pool
        self._clients: dict[str, httpx.AsyncClient] = {}
        self._max_connections = max_connections_per_domain

    async def get_client(self, domain: str, use_proxy: bool = True) -> httpx.AsyncClient:
        if domain in self._clients:
            return self._clients[domain]

        proxy_url = None
        if use_proxy:
            proxy_config = self._proxy_pool.get_proxy(domain)
            if proxy_config:
                proxy_url = proxy_config.url

        limits = httpx.Limits(max_connections=self._max_connections, max_keepalive_connections=2)
        client = httpx.AsyncClient(
            headers=DEFAULT_HEADERS,
            proxy=proxy_url,
            limits=limits,
            timeout=httpx.Timeout(30.0),
            follow_redirects=True,
        )
        self._clients[domain] = client
        return client

    async def request(self, method: str, url: str, domain: str = "", **kwargs: Any) -> httpx.Response:
        if not domain:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
        client = await self.get_client(domain)
        return await client.request(method, url, **kwargs)

    async def close_all(self) -> None:
        for client in self._clients.values():
            await client.aclose()
        self._clients.clear()

session_manager = SessionManager()
