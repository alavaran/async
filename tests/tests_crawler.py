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

    
    async def test_fetch_and_parse(self):
        html = """
        <html>
            <head>
                <title>Test Page</title>
                <meta name="description" content="Test description">
            </head>
            <body>
                <h1>Hello</h1>
                <a href="/books/">Books</a>
                <img src="book.jpg" alt="Book">
            </body>
        </html>
        """

        async def mock_fetch_url(url):
            return html

        self.crawler.fetch_url = mock_fetch_url

        result = await self.crawler.fetch_and_parse(
            "https://example.com/catalog/"
        )

        self.assertEqual(
            result["url"],
            "https://example.com/catalog/",
        )
        self.assertEqual(result["title"], "Test Page")
        self.assertIn("Hello", result["text"])
        self.assertIn(
            "https://example.com/books/",
            result["links"],
        )
        self.assertEqual(
            result["metadata"]["description"],
            "Test description",
        )
        self.assertEqual(
            result["images"],
            [{"src": "book.jpg", "alt": "Book"}],
        )
        self.assertEqual(
            result["headings"],
            [{"tag": "h1", "text": "Hello"}],
        )

    
    async def test_fetch_and_parse_failed_download(self):
        async def mock_fetch_url(url):
            return ""

        self.crawler.fetch_url = mock_fetch_url

        result = await self.crawler.fetch_and_parse(
            "https://example.com/unavailable"
        )

        self.assertEqual(result["url"], "https://example.com/unavailable")
        self.assertEqual(result["title"], "")
        self.assertEqual(result["links"], [])
        self.assertEqual(result["images"], [])
        self.assertEqual(result["headings"], [])
        self.assertEqual(result["tables"], [])
        self.assertEqual(result["lists"], [])
        self.assertEqual(result["metadata"]["description"], "")



if __name__ == "__main__":
    unittest.main()