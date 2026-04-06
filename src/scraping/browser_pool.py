"""Playwright browser pool for allowlisted employer ATS/career pages.

Provides isolated Chromium contexts for rendering SPA-based career pages
(Lever, Greenhouse, Workday). Enforces domain allowlist and auto-stops
on challenge detection.
"""

from __future__ import annotations

import asyncio
import random
import re
from contextlib import suppress
from dataclasses import dataclass
from typing import Any

from src.utils.logging import get_logger

logger = get_logger(__name__)


class ChallengeDetectedError(Exception):
    """Raised when a login wall, CAPTCHA, or bot challenge is detected."""

    def __init__(self, domain: str, screenshot_path: str | None = None):
        self.domain = domain
        self.screenshot_path = screenshot_path
        super().__init__(f"Challenge detected on {domain}")


class DomainNotAllowedError(Exception):
    """Raised when attempting to browse a non-allowlisted domain."""

    def __init__(self, domain: str):
        self.domain = domain
        super().__init__(f"Domain not in allowlist: {domain}")


# Allowlisted ATS/career page domains
ALLOWED_DOMAIN_PATTERNS = [
    r".*\.lever\.co$",
    r".*\.greenhouse\.io$",
    r".*\.workday\.com$",
    r".*\.ashbyhq\.com$",
    r".*\.smartrecruiters\.com$",
    r"boards\.eu\.greenhouse\.io$",
    # Employer-direct career pages (added dynamically)
]

# Challenge detection patterns
CHALLENGE_INDICATORS = [
    "captcha",
    "recaptcha",
    "hcaptcha",
    "challenge",
    "verify you are human",
    "please verify",
    "access denied",
    "bot detection",
    "automated access",
    "unusual traffic",
    "sign in to continue",
    "login required",
    "please log in",
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]

VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1440, "height": 900},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
]


@dataclass
class BrowserContext:
    context: Any  # playwright BrowserContext
    domain: str
    created_at: float = 0.0


class PlaywrightBrowserPool:
    """Async pool of Playwright Chromium contexts for ATS page rendering."""

    def __init__(
        self,
        max_concurrent: int = 3,
        extra_allowed_domains: list[str] | None = None,
    ) -> None:
        self._max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._browser: Any = None  # playwright Browser
        self._playwright: Any = None
        self._allowed_patterns = list(ALLOWED_DOMAIN_PATTERNS)
        if extra_allowed_domains:
            self._allowed_patterns.extend(extra_allowed_domains)

    def is_domain_allowed(self, domain: str) -> bool:
        domain = domain.lower().strip()
        return any(re.match(pattern, domain) for pattern in self._allowed_patterns)

    async def start(self) -> None:
        from playwright.async_api import async_playwright

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=True)
        logger.info("Browser pool started", max_concurrent=self._max_concurrent)

    async def stop(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Browser pool stopped")

    async def get_context(self, domain: str) -> Any:
        """Create an isolated browser context for the given domain."""
        if not self.is_domain_allowed(domain):
            raise DomainNotAllowedError(domain)

        if not self._browser:
            await self.start()

        viewport = random.choice(VIEWPORTS)
        user_agent = random.choice(USER_AGENTS)

        context = await self._browser.new_context(
            viewport=viewport,
            user_agent=user_agent,
            locale="en-IN",
            timezone_id="Asia/Kolkata",
        )
        return context

    async def fetch_page(self, url: str, domain: str = "") -> dict[str, Any]:
        """Fetch a page with challenge detection and XHR interception.

        Returns: {"html": str, "api_responses": list, "screenshot": bytes | None}
        """
        from urllib.parse import urlparse

        if not domain:
            domain = urlparse(url).netloc

        if not self.is_domain_allowed(domain):
            raise DomainNotAllowedError(domain)

        api_responses: list[dict] = []

        async with self._semaphore:
            context = await self.get_context(domain)
            page = await context.new_page()

            # Intercept XHR/API calls for job data
            async def handle_response(response):
                ct = response.headers.get("content-type", "")
                if "application/json" in ct and any(
                    kw in response.url for kw in ["jobs", "positions", "careers", "openings", "api"]
                ):
                    try:
                        body = await response.json()
                        api_responses.append({"url": response.url, "data": body})
                    except Exception:
                        pass

            page.on("response", handle_response)

            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)

                # Scroll to trigger lazy loading
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000)

                # Check for challenges
                content = await page.content()
                content_lower = content.lower()
                for indicator in CHALLENGE_INDICATORS:
                    if indicator in content_lower:
                        await page.screenshot()
                        await context.close()
                        raise ChallengeDetectedError(domain, screenshot_path=None)

                html = await page.content()
                await context.close()

                return {
                    "html": html,
                    "api_responses": api_responses,
                    "screenshot": None,
                }

            except ChallengeDetectedError:
                raise
            except Exception as e:
                # Screenshot + close on any error
                with suppress(Exception):
                    await page.screenshot()
                await context.close()
                logger.error("Browser fetch failed", url=url, error=str(e))
                raise


browser_pool = PlaywrightBrowserPool()
