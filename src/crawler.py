
import asyncio
import logging
import re
import time
import aiohttp
import random

from src.rate_limiter import RateLimiter
from src.robots_parser import RobotsParser
from urllib.parse import urlparse
from src.queue import CrawlerQueue
from src.parser import HTMLParser
from src.semaphore_manager import SemaphoreManager


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class AsyncCrawler:
    def __init__(
        self,
        max_concurrent: int = 5,
        max_per_domain: int = 3,
        requests_per_second: float = 1.0,
        respect_robots: bool = True,
        min_delay: float = 0.5,
        jitter: float = 0.0,
        user_agent: str = "MyBot/1.0",
    ):
        self.max_concurrent = max_concurrent
        self.respect_robots = respect_robots
        self.min_delay = min_delay
        self.jitter = jitter
        self.user_agent = user_agent

        timeout = aiohttp.ClientTimeout(
            total=20,
            connect=10,
            sock_read=10,
        )

        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={"User-Agent": user_agent},
        )

        self.semaphore_manager = SemaphoreManager(
            max_concurrent=max_concurrent,
            max_per_domain=max_per_domain,
        )

        self.rate_limiter = RateLimiter(
            requests_per_second=requests_per_second,
            per_domain=True,
        )

        self.robots_parser = RobotsParser(
            self.session,
            user_agent=user_agent,
        ) if respect_robots else None

        self.parser = HTMLParser()

        self.visited_urls: set[str] = set()
        self.failed_urls: dict[str, str] = {}
        self.processed_urls: dict[str, dict] = {}
        self.url_depths: dict[str, int] = {}

        self.blocked_urls: set[str] = set()
        self.request_timestamps: list[float] = []
        self.request_delays: list[float] = []
        self._last_request_time: dict[str, float] = {}
        self._delay_locks: dict[str, asyncio.Lock] = {}

    async def _wait_for_domain(
        self,
        domain: str,
        crawl_delay: float = 0.0,
    ) -> None:
        lock = self._delay_locks.setdefault(domain, asyncio.Lock())

        async with lock:
            now = time.monotonic()
            last_request = self._last_request_time.get(domain)

            delay = max(self.min_delay, crawl_delay)
            delay += random.uniform(0, self.jitter)

            if last_request is not None:
                wait_time = delay - (now - last_request)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)

            actual_time = time.monotonic()

            if last_request is not None:
                self.request_delays.append(actual_time - last_request)

            self._last_request_time[domain] = actual_time
            self.request_timestamps.append(actual_time)

    async def fetch_url(self, url: str) -> str:
        domain = urlparse(url).netloc
        await self.semaphore_manager.acquire(domain)

        try:
            if self.robots_parser is not None:
                await self.robots_parser.fetch_robots(url)

                if not self.robots_parser.can_fetch(url, self.user_agent):
                    logging.warning("Blocked by robots.txt: %s", url)
                    self.blocked_urls.add(url)
                    return ""

                crawl_delay = self.robots_parser.get_crawl_delay(
                    self.user_agent,
                    base_url=url,
                )
            else:
                crawl_delay = 0.0

            await self.rate_limiter.acquire(domain)
            await self._wait_for_domain(domain, crawl_delay)

            logging.info("Fetching: %s", url)

            async with self.session.get(url) as response:
                response.raise_for_status()
                content = await response.text()

                logging.info(
                    "Fetched %s (status=%s)",
                    url,
                    response.status,
                )
                return content

        except aiohttp.ClientResponseError as exc:
            logging.error("HTTP error for %s: %s", url, exc.status)
            return ""

        except asyncio.TimeoutError:
            logging.error("Timeout for %s", url)
            return ""

        except aiohttp.ClientError as exc:
            logging.error("Network error for %s: %s", url, exc)
            return ""

        finally:
            self.semaphore_manager.release(domain)

    def mark_visited(self, url: str, depth: int = 0) -> bool:
        if url in self.visited_urls:
            return False

        self.visited_urls.add(url)
        self.url_depths[url] = depth
        return True

    async def fetch_urls(self, urls: list[str]) -> dict[str, str]:
        tasks = [self.fetch_url(url) for url in urls]
        results = await asyncio.gather(*tasks)

        return dict(zip(urls, results))

    async def fetch_and_parse(self, url: str) -> dict:
        html = await self.fetch_url(url)

        if not html:
            return {
                "url": url,
                "title": "",
                "text": "",
                "links": [],
                "metadata": {
                    "title": "",
                    "description": "",
                    "keywords": "",
                },
                "images": [],
                "headings": [],
                "tables": [],
                "lists": [],
            }

        return await self.parser.parse_html(html, url)

    async def close(self):
        await self.session.close()
    
    def should_crawl(
        self,
        url: str,
        start_domain: str,
        same_domain_only: bool = True,
        include_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
    ) -> bool:
        parsed_url = urlparse(url)

        if parsed_url.scheme not in ("http", "https") or not parsed_url.netloc:
            return False

        if same_domain_only and parsed_url.netloc != start_domain:
            return False

        if include_patterns and not any(
            re.search(pattern, url) for pattern in include_patterns
        ):
            return False

        if exclude_patterns and any(
            re.search(pattern, url) for pattern in exclude_patterns
        ):
            return False

        return True

    
    async def crawl(
        self,
        start_urls: list[str],
        max_pages: int = 100,
        max_depth: int = 2,
        same_domain_only: bool = True,
        include_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
    ) -> dict[str, dict]:
        queue = CrawlerQueue()
        started_at = time.monotonic()
        start_domains = {}

        for url in start_urls:
            if self.mark_visited(url, depth=0):
                queue.add_url(url)
                start_domains[url] = urlparse(url).netloc

        results = {}

        while queue.get_stats()["queued"] > 0 and len(results) < max_pages:
            url = await queue.get_next()

            if url is None:
                break

            depth = self.url_depths[url]

            try:
                page = await self.fetch_and_parse(url)

                if not page["title"] and not page["text"]:
                    error = "Failed to fetch or parse page"
                    self.failed_urls[url] = error
                    queue.mark_failed(url, error)
                    continue

                results[url] = page
                self.processed_urls[url] = page
                queue.mark_processed(url)

                if depth >= max_depth:
                    continue

                start_domain = start_domains.get(
                    url,
                    urlparse(url).netloc,
                )

                for link in page["links"]:
                    if not self.should_crawl(
                        link,
                        start_domain=start_domain,
                        same_domain_only=same_domain_only,
                        include_patterns=include_patterns,
                        exclude_patterns=exclude_patterns,
                    ):
                        continue

                    if link in self.visited_urls:
                        continue

                    if self.mark_visited(link, depth=depth + 1):
                        start_domains[link] = start_domain
                        queue.add_url(link)

            except Exception as e:
                logging.exception("Unexpected error crawling %s", url)
                self.failed_urls[url] = str(e)
                queue.mark_failed(url, str(e))

            finally:
                logging.info("Crawl progress: %s", self.get_progress(started_at, queue))

        return results

    def get_progress(
        self,
        started_at: float,
        queue: CrawlerQueue,
    ) -> dict:
        elapsed = max(time.monotonic() - started_at, 0.001)
        processed = len(self.processed_urls)
        errors = len(self.failed_urls)

        return {
            "pages_processed": processed,
            "queue_size": queue.get_stats()["queued"],
            "errors": errors,
            "pages_per_second": round(processed / elapsed, 2),
        }

