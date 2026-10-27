
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp

from src.crawler import AsyncCrawler


class TestBackoff(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.crawler = AsyncCrawler.__new__(AsyncCrawler)

        self.crawler.max_retries = 3
        self.crawler.backoff_base = 1.0
        self.crawler.jitter = 0.0
        self.crawler.user_agent = "TestBot/1.0"
        self.crawler.robots_parser = None
        self.crawler.rate_limiter = MagicMock()
        self.crawler.rate_limiter.acquire = AsyncMock()
        self.crawler._wait_for_domain = AsyncMock()

        self.crawler.semaphore_manager = MagicMock()
        self.crawler.semaphore_manager.acquire = AsyncMock()
        self.crawler.semaphore_manager.release = MagicMock()

        self.crawler.session = MagicMock()
        self.crawler.blocked_urls = set()

    async def test_retries_server_error(self):
        response = MagicMock()
        response.raise_for_status.side_effect = [
            aiohttp.ClientResponseError(
                request_info=MagicMock(),
                history=(),
                status=503,
                message="Service Unavailable",
            ),
            None,
        ]
        response.text = AsyncMock(return_value="<html>OK</html>")

        context = MagicMock()
        context.__aenter__ = AsyncMock(return_value=response)
        context.__aexit__ = AsyncMock(return_value=False)
        self.crawler.session.get.return_value = context

        with patch("src.crawler.asyncio.sleep", new_callable=AsyncMock) as sleep:
            result = await self.crawler.fetch_url("https://example.com/")

        self.assertEqual(result, "<html>OK</html>")
        self.assertEqual(self.crawler.session.get.call_count, 2)
        sleep.assert_awaited_once_with(1.0)

    async def test_does_not_retry_404(self):
        response = MagicMock()
        response.raise_for_status.side_effect = aiohttp.ClientResponseError(
            request_info=MagicMock(),
            history=(),
            status=404,
            message="Not Found",
        )

        context = MagicMock()
        context.__aenter__ = AsyncMock(return_value=response)
        context.__aexit__ = AsyncMock(return_value=False)
        self.crawler.session.get.return_value = context

        with patch("src.crawler.asyncio.sleep", new_callable=AsyncMock) as sleep:
            result = await self.crawler.fetch_url("https://example.com/missing")

        self.assertEqual(result, "")
        self.assertEqual(self.crawler.session.get.call_count, 1)
        sleep.assert_not_awaited()

    async def test_exponential_delay(self):
        response = MagicMock()
        response.raise_for_status.side_effect = [
            aiohttp.ClientResponseError(
                request_info=MagicMock(),
                history=(),
                status=503,
                message="Service Unavailable",
            ),
            aiohttp.ClientResponseError(
                request_info=MagicMock(),
                history=(),
                status=503,
                message="Service Unavailable",
            ),
            None,
        ]
        response.text = AsyncMock(return_value="OK")

        context = MagicMock()
        context.__aenter__ = AsyncMock(return_value=response)
        context.__aexit__ = AsyncMock(return_value=False)
        self.crawler.session.get.return_value = context

        with patch("src.crawler.asyncio.sleep", new_callable=AsyncMock) as sleep:
            result = await self.crawler.fetch_url("https://example.com/")

        self.assertEqual(result, "OK")
        self.assertEqual(
            [call.args[0] for call in sleep.await_args_list],
            [1.0, 2.0],
        )


if __name__ == "__main__":
    unittest.main()
