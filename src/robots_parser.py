
import asyncio
import logging
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import aiohttp


logger = logging.getLogger(__name__)


class RobotsParser:
    def __init__(
        self,
        session: aiohttp.ClientSession,
        user_agent: str = "*",
    ):
        self.session = session
        self.user_agent = user_agent
        self._cache = {}
        self._locks = {}

    async def fetch_robots(self, base_url: str) -> dict:
        parsed = urlparse(base_url)

        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError(f"Invalid base URL: {base_url}")

        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        domain = f"{parsed.scheme}://{parsed.netloc}"

        if domain in self._cache:
            return self._cache[domain]

        lock = self._locks.setdefault(domain, asyncio.Lock())

        async with lock:
            if domain in self._cache:
                return self._cache[domain]

            parser = RobotFileParser()
            parser.set_url(robots_url)

            try:
                async with self.session.get(robots_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        parser.parse(content.splitlines())

                    elif 400 <= response.status < 500:
                        # A missing robots.txt (404) does not prohibit crawling.
                        logger.info(
                            "robots.txt unavailable (HTTP %s): %s",
                            response.status,
                            robots_url,
                        )
                        parser.parse([])

                    else:
                        # Server errors: fail closed and avoid crawling.
                        logger.warning(
                            "robots.txt returned HTTP %s for %s",
                            response.status,
                            robots_url,
                        )
                        parser.parse(["User-agent: *", "Disallow: /"])

            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                logger.warning("Could not fetch %s: %s", robots_url, exc)
                # Fail closed on network errors.
                parser.parse(["User-agent: *", "Disallow: /"])

            self._cache[domain] = {
                "parser": parser,
                "robots_url": robots_url,
            }

            return self._cache[domain]

    def can_fetch(self, url: str, user_agent: str = "*") -> bool:
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        cached = self._cache.get(domain)

        if cached is None:
            raise RuntimeError(
                f"robots.txt not loaded for {domain}; call fetch_robots first"
            )

        return cached["parser"].can_fetch(user_agent, url)

    def get_crawl_delay(
        self,
        user_agent: str = "*",
        base_url: str | None = None,
    ) -> float:
        if base_url is not None:
            parsed = urlparse(base_url)
            domain = f"{parsed.scheme}://{parsed.netloc}"
            cached = self._cache.get(domain)

            if cached is None:
                return 0.0

            delay = cached["parser"].crawl_delay(user_agent)
            return float(delay) if delay is not None else 0.0

        for cached in self._cache.values():
            delay = cached["parser"].crawl_delay(user_agent)
            if delay is not None:
                return float(delay)

        return 0.0
