
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

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

    @patch("src.crawler.SitemapParser")
    async def test_crawl_processes_sitemap_urls(self, mock_sitemap):
        sitemap_url = "https://example.com/sitemap.xml"
        page_url = "https://example.com/from-sitemap"

        mock_sitemap.return_value.fetch_sitemap = AsyncMock(
            return_value=[page_url]
        )

        self.crawler.session = MagicMock()
        self.crawler.fetch_and_parse = AsyncMock(
            side_effect=[
                {
                    "url": "https://example.com",
                    "title": "Home",
                    "text": "Home page",
                    "links": [],
                },
                {
                    "url": page_url,
                    "title": "Sitemap page",
                    "text": "Found through sitemap",
                    "links": [],
                },
            ]
        )

        results = await self.crawler.crawl(
            ["https://example.com"],
            max_pages=10,
            max_depth=2,
            sitemap_urls=[sitemap_url],
        )

        self.assertIn(page_url, results)
        self.assertEqual(
            self.crawler.fetch_and_parse.await_count,
            2,
        )
        mock_sitemap.return_value.fetch_sitemap.assert_awaited_once_with(
            sitemap_url
        )

    async def test_crawler_can_run_twice(self):
        self.crawler.fetch_and_parse = AsyncMock(
            side_effect=[
                {
                    "url": "https://example.com",
                    "title": "First",
                    "text": "First page",
                    "links": [],
                },
                {
                    "url": "https://example.org",
                    "title": "Second",
                    "text": "Second page",
                    "links": [],
                },
            ]
        )

        first_results = await self.crawler.crawl(
            ["https://example.com"],
            max_pages=10,
            max_depth=0,
        )

        second_results = await self.crawler.crawl(
            ["https://example.org"],
            max_pages=10,
            max_depth=0,
        )

        self.assertEqual(len(first_results), 1)
        self.assertEqual(len(second_results), 1)

        self.assertIn("https://example.org", second_results)
        self.assertNotIn("https://example.com", second_results)

        self.assertEqual(self.crawler.fetch_and_parse.await_count, 2)
        self.assertEqual(len(self.crawler.visited_urls), 1)

if __name__ == "__main__":
    unittest.main()
