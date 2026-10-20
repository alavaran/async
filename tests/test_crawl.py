
import unittest
from unittest.mock import AsyncMock

from src.crawler import AsyncCrawler


class TestCrawl(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.crawler = AsyncCrawler.__new__(AsyncCrawler)

        self.crawler.visited_urls = set()
        self.crawler.failed_urls = {}
        self.crawler.processed_urls = {}
        self.crawler.url_depths = {}

        self.crawler.fetch_and_parse = AsyncMock(
            side_effect=[
                {
                    "url": "https://example.com",
                    "title": "Home",
                    "text": "Home page",
                    "links": ["https://example.com/page1"],
                },
                {
                    "url": "https://example.com/page1",
                    "title": "Page 1",
                    "text": "Page one",
                    "links": ["https://example.com/page2"],
                },
            ]
        )

    async def test_max_depth(self):
        results = await self.crawler.crawl(
            ["https://example.com"],
            max_pages=10,
            max_depth=1,
        )

        self.assertEqual(len(results), 2)
        self.assertNotIn(
            "https://example.com/page2",
            self.crawler.visited_urls,
        )

    async def test_no_duplicate_visited_urls(self):
        self.crawler.fetch_and_parse = AsyncMock(
            return_value={
                "url": "https://example.com",
                "title": "Home",
                "text": "Home page",
                "links": [
                    "https://example.com/page1",
                    "https://example.com/page1",
                ],
            }
        )

        await self.crawler.crawl(
            ["https://example.com"],
            max_pages=10,
            max_depth=2,
        )

        self.assertEqual(
            len(self.crawler.visited_urls),
            2,
        )
        self.assertEqual(
            self.crawler.fetch_and_parse.await_count,
            2,
        )


if __name__ == "__main__":
    unittest.main()
