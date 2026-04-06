"""Redis-backed token bucket rate limiter per domain.

Uses Redis atomic operations for distributed rate limiting.
Supports halving rate on 429 responses and Retry-After header respect.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from src.services.cache import cache
from src.utils.logging import get_logger

logger = get_logger(__name__)

class RateLimitExceeded(Exception):
    def __init__(self, domain: str, retry_after: float = 0):
        self.domain = domain
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded for {domain}, retry after {retry_after}s")

# Default rate configs per Section 11.3
DEFAULT_RATE_CONFIGS: dict[str, dict] = {
    "serpapi": {"max_rpm": 30, "burst": 10},
    "rapidapi_linkedin": {"max_rpm": 10, "burst": 3},
    "apify": {"max_rpm": 20, "burst": 5},
    "employer_ats": {"max_rpm": 15, "burst": 5},
    "naukri": {"max_rpm": 20, "burst": 5},
    "indeed": {"max_rpm": 10, "burst": 3},
    "linkedin": {"max_rpm": 5, "burst": 2},
    "iimjobs": {"max_rpm": 15, "burst": 4},
    "default": {"max_rpm": 10, "burst": 3},
}

@dataclass
class RateConfig:
    max_rpm: int = 10
    burst: int = 3

class RedisTokenBucket:
    def __init__(self, configs: dict[str, dict] | None = None) -> None:
        self._configs = configs or DEFAULT_RATE_CONFIGS
        self._halved: dict[str, float] = {}  # domain -> expiry time

    def _get_config(self, domain: str) -> RateConfig:
        cfg = self._configs.get(domain, self._configs["default"])
        rc = RateConfig(max_rpm=cfg["max_rpm"], burst=cfg["burst"])
        # Check if rate is halved
        if domain in self._halved:
            if time.monotonic() < self._halved[domain]:
                rc.max_rpm = max(1, rc.max_rpm // 2)
                rc.burst = max(1, rc.burst // 2)
            else:
                del self._halved[domain]
        return rc

    async def acquire(self, domain: str, cost: int = 1) -> bool:
        config = self._get_config(domain)
        key = f"ratelimit:{domain}"

        try:
            # Simple sliding window counter in Redis
            now = int(time.time())
            window_key = f"{key}:{now // 60}"  # per-minute window

            count = await cache.incr(window_key)
            if count == 1:
                await cache.expire(window_key, 120)  # TTL 2 min

            if count > config.max_rpm:
                raise RateLimitExceeded(domain, retry_after=60 - (now % 60))

            return True
        except RateLimitExceeded:
            raise
        except Exception:
            # If Redis is down, allow the request (fail-open)
            logger.warning("Rate limiter Redis error, allowing request", domain=domain)
            return True

    def halve_rate(self, domain: str, duration_seconds: float = 600) -> None:
        self._halved[domain] = time.monotonic() + duration_seconds
        logger.info("Rate halved", domain=domain, duration=duration_seconds)

    def respect_retry_after(self, domain: str, retry_after_seconds: float) -> None:
        self.halve_rate(domain, retry_after_seconds)

rate_limiter = RedisTokenBucket()
