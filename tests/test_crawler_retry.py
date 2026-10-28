import unittest
import aiohttp
from unittest.mock import AsyncMock, MagicMock, patch

from src.crawler import AsyncCrawler
from src.exceptions import (
    TransientError,
    PermanentError,
    NetworkError,
)


class TestCrawlerRetry(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.crawler = AsyncCrawler.__new__(AsyncCrawler)

        self.crawler.semaphore_manager = MagicMock()
        self.crawler.semaphore_manager.acquire = AsyncMock()
        self.crawler.semaphore_manager.release = MagicMock()

        self.crawler.rate_limiter = MagicMock()
        self.crawler.rate_limiter.acquire = AsyncMock()

        self.crawler.robots_parser = None
        self.crawler.user_agent = "TestBot/1.0"
        self.crawler.jitter = 0
        self.crawler.min_delay = 0

        self.crawler.connect_timeout = 10.0
        self.crawler.read_timeout = 10.0
        self.crawler.total_timeout = 20.0

        self.crawler._wait_for_domain = AsyncMock()

        self.crawler.session = MagicMock()
        self.crawler.retry_strategy = MagicMock()

    async def test_fetch_url_uses_retry_strategy(self):
        self.crawler.retry_strategy.execute_with_retry = AsyncMock(
            return_value="<html>success</html>"
        )

        result = await self.crawler.fetch_url(
            "https://example.com"
        )

        self.assertEqual(result, "<html>success</html>")
        self.crawler.retry_strategy.execute_with_retry.assert_awaited_once()

    async def test_fetch_url_returns_empty_on_permanent_error(self):
        self.crawler.retry_strategy.execute_with_retry = AsyncMock(
            side_effect=PermanentError("HTTP 404")
        )

        result = await self.crawler.fetch_url(
            "https://example.com/missing"
        )

        self.assertEqual(result, "")

    async def test_fetch_url_returns_empty_after_transient_error(self):
        self.crawler.retry_strategy.execute_with_retry = AsyncMock(
            side_effect=TransientError("HTTP 503")
        )

        result = await self.crawler.fetch_url(
            "https://example.com"
        )

        self.assertEqual(result, "")

    async def test_http_503_becomes_transient_error(self):
        response = MagicMock()
        response.raise_for_status.side_effect = aiohttp.ClientResponseError(
            request_info=MagicMock(),
            history=(),
            status=503,
            message="Service Unavailable",
        )

        self.crawler.session.get.return_value.__aenter__ = AsyncMock(
            return_value=response
        )

        with self.assertRaises(TransientError):
            await self.crawler._fetch_url_once("https://example.com")

        self.crawler.semaphore_manager.release.assert_called_once()


    async def test_http_404_becomes_permanent_error(self):
        response = MagicMock()
        response.raise_for_status.side_effect = aiohttp.ClientResponseError(
            request_info=MagicMock(),
            history=(),
            status=404,
            message="Not Found",
        )

        self.crawler.session.get.return_value.__aenter__ = AsyncMock(
            return_value=response
        )

        with self.assertRaises(PermanentError):
            await self.crawler._fetch_url_once(
                "https://example.com/missing"
            )

        self.crawler.semaphore_manager.release.assert_called_once()

    async def test_timeout_increases_on_retry(self):
        from unittest.mock import AsyncMock, MagicMock, patch

        self.crawler.connect_timeout = 5
        self.crawler.read_timeout = 10
        self.crawler.total_timeout = 20

        self.crawler.session.get = MagicMock()

        response = MagicMock()
        response.raise_for_status = MagicMock()
        response.text = AsyncMock(return_value="<html>ok</html>")

        context_manager = MagicMock()
        context_manager.__aenter__ = AsyncMock(return_value=response)
        context_manager.__aexit__ = AsyncMock(return_value=False)

        self.crawler.session.get.return_value = context_manager

        with patch("src.crawler.aiohttp.ClientTimeout") as timeout_mock:
            await self.crawler._fetch_url_once(
                "https://example.com",
                _retry_attempt=1,
            )

        timeout_mock.assert_called_once_with(
            total=40,
            connect=10,
            sock_read=20,
        )

if __name__ == "__main__":
    unittest.main()