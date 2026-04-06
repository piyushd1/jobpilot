"""Proxy pool manager with BrightData (primary) and SmartProxy (secondary).

Provides proxy rotation, health tracking, and geo-targeting for India job boards.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass

from src.config.settings import settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ProxyConfig:
    host: str
    port: int
    username: str = ""
    password: str = ""
    protocol: str = "http"
    geo: str = ""
    provider: str = ""

    @property
    def url(self) -> str:
        if self.username:
            return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.protocol}://{self.host}:{self.port}"


@dataclass
class ProxyHealth:
    proxy: ProxyConfig
    is_healthy: bool = True
    last_failure: float = 0.0
    failure_count: int = 0
    cooldown_seconds: float = 600.0  # 10 min

    def mark_failed(self) -> None:
        self.failure_count += 1
        self.last_failure = time.monotonic()
        self.is_healthy = False

    def check_recovery(self) -> bool:
        if not self.is_healthy and (time.monotonic() - self.last_failure) > self.cooldown_seconds:
            self.is_healthy = True
            self.failure_count = 0
        return self.is_healthy


INDIA_DOMAINS = {"naukri.com", "iimjobs.com", "hirist.com", "instahyre.com", "foundit.in"}


class ProxyPoolManager:
    def __init__(self) -> None:
        self._pools: dict[str, list[ProxyHealth]] = {"primary": [], "secondary": []}
        self._domain_index: dict[str, int] = {}
        self._init_pools()

    def _init_pools(self) -> None:
        # BrightData (primary) - configured via settings
        if settings.brightdata_username:
            for _i in range(5):
                self._pools["primary"].append(
                    ProxyHealth(
                        proxy=ProxyConfig(
                            host="brd.superproxy.io",
                            port=22225,
                            username=f"{settings.brightdata_username}-session-{random.randint(10000, 99999)}",
                            password=settings.brightdata_password,
                            provider="brightdata",
                            geo="in",
                        )
                    )
                )
        # SmartProxy (secondary) - placeholder
        self._pools["secondary"].append(
            ProxyHealth(
                proxy=ProxyConfig(
                    host="gate.smartproxy.com", port=7000, provider="smartproxy", geo="in"
                )
            )
        )

    def get_proxy(self, domain: str = "") -> ProxyConfig | None:
        needs_india = any(d in domain.lower() for d in INDIA_DOMAINS)

        for pool_name in ["primary", "secondary"]:
            pool = self._pools[pool_name]
            healthy = [ph for ph in pool if ph.check_recovery()]
            if needs_india:
                healthy = [ph for ph in healthy if ph.proxy.geo == "in"] or healthy
            if not healthy:
                continue
            # Round-robin per domain
            key = f"{pool_name}:{domain}"
            idx = self._domain_index.get(key, 0) % len(healthy)
            self._domain_index[key] = idx + 1
            return healthy[idx].proxy

        logger.warning("No healthy proxies available", domain=domain)
        return None

    def mark_failed(self, proxy: ProxyConfig) -> None:
        for pool in self._pools.values():
            for ph in pool:
                if ph.proxy.host == proxy.host and ph.proxy.port == proxy.port:
                    ph.mark_failed()
                    logger.info("Proxy marked unhealthy", host=proxy.host, provider=proxy.provider)
                    return


proxy_pool = ProxyPoolManager()
