import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp

from src.crawler import AsyncCrawler


class TestAsyncCrawler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.crawler = AsyncCrawler(max_concurrent=5)

    async def asyncTearDown(self):
        await self.crawler.close()

    async def test_fetch_valid_url(self):
        response = MagicMock()
        response.status = 200
        response.text = AsyncMock(return_value="<html>test</html>")
        response.raise_for_status = MagicMock()

        response_context = MagicMock()
        response_context.__aenter__ = AsyncMock(return_value=response)
        response_context.__aexit__ = AsyncMock(return_value=None)

        with patch.object(
            self.crawler.session,
            "get",
            return_value=response_context,
        ):
            result = await self.crawler.fetch_url(
                "http://example.com"
            )

        self.assertEqual(result, "<html>test</html>")

    async def test_fetch_http_error(self):
        response = MagicMock()

        error = aiohttp.ClientResponseError(
            request_info=MagicMock(),
            history=(),
            status=404,
            message="Not Found",
        )

        response.raise_for_status = MagicMock(
            side_effect=error
        )

        response_context = MagicMock()
        response_context.__aenter__ = AsyncMock(return_value=response)
        response_context.__aexit__ = AsyncMock(return_value=None)

        with patch.object(
            self.crawler.session,
            "get",
            return_value=response_context,
        ):
            result = await self.crawler.fetch_url(
                "http://example.com/not-found"
            )

        self.assertEqual(result, "")

    async def test_fetch_timeout(self):
        response_context = MagicMock()
        response_context.__aenter__ = AsyncMock(
            side_effect=asyncio.TimeoutError()
        )
        response_context.__aexit__ = AsyncMock(return_value=None)

        with patch.object(
            self.crawler.session,
            "get",
            return_value=response_context,
        ):
            result = await self.crawler.fetch_url(
                "http://example.com/timeout"
            )

        self.assertEqual(result, "")

    async def test_fetch_urls(self):
        async def fake_fetch(url):
            return f"HTML: {url}"

        with patch.object(
            self.crawler,
            "fetch_url",
            side_effect=fake_fetch,
        ):
            urls = [
                "http://example.com/1",
                "http://example.com/2",
                "http://example.com/3",
            ]

            results = await self.crawler.fetch_urls(urls)

        self.assertEqual(len(results), 3)

        self.assertEqual(
            results["http://example.com/1"],
            "HTML: http://example.com/1",
        )

        self.assertEqual(
            results["http://example.com/2"],
            "HTML: http://example.com/2",
        )

        self.assertEqual(
            results["http://example.com/3"],
            "HTML: http://example.com/3",
        )


if __name__ == "__main__":
    unittest.main()