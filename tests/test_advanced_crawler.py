
import unittest
from unittest.mock import AsyncMock, patch

from src.advanced_crawler import AdvancedCrawler
from src.config import CrawlerConfig


class TestAdvancedCrawler(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.config = CrawlerConfig(
            start_urls=["https://example.com"],
            max_pages=10,
            max_depth=2,
        )

    @patch("src.advanced_crawler.AsyncCrawler")
    def test_initialization(self, mock_crawler):
        advanced = AdvancedCrawler(self.config)

        self.assertIsNotNone(advanced.crawler)
        mock_crawler.assert_called_once()

    @patch("src.advanced_crawler.AsyncCrawler")
    async def test_crawl(self, mock_crawler):
        mock_instance = mock_crawler.return_value
        mock_instance.crawl = AsyncMock(
            return_value={"https://example.com": {"title": "Example"}}
        )

        advanced = AdvancedCrawler(self.config)

        results = await advanced.crawl()

        self.assertIn("https://example.com", results)
        mock_instance.crawl.assert_awaited_once()

    @patch("src.advanced_crawler.AsyncCrawler")
    def test_get_stats(self, mock_crawler):
        mock_instance = mock_crawler.return_value
        mock_instance.get_stats.return_value = {
            "pages_processed": 10,
        }

        advanced = AdvancedCrawler(self.config)

        self.assertEqual(
            advanced.get_stats()["pages_processed"],
            10,
        )

    @patch("src.advanced_crawler.AsyncCrawler")
    def test_get_monitoring(self, mock_crawler):
        mock_instance = mock_crawler.return_value
        mock_instance.get_monitoring.return_value = {
            "progress_percent": 50,
        }

        advanced = AdvancedCrawler(self.config)

        self.assertEqual(
            advanced.get_monitoring()["progress_percent"],
            50,
        )

    @patch("src.advanced_crawler.AsyncCrawler")
    def test_get_rate_stats(self, mock_crawler):
        mock_instance = mock_crawler.return_value
        mock_instance.get_rate_stats.return_value = {
            "requests_last_minute": 20,
        }

        advanced = AdvancedCrawler(self.config)

        self.assertEqual(
            advanced.get_rate_stats()["requests_last_minute"],
            20,
        )

    @patch("src.advanced_crawler.AsyncCrawler")
    def test_get_error_stats(self, mock_crawler):
        mock_instance = mock_crawler.return_value
        mock_instance.get_error_stats.return_value = {
            "failed_urls": [],
        }

        advanced = AdvancedCrawler(self.config)

        self.assertEqual(
            advanced.get_error_stats()["failed_urls"],
            [],
        )
        
    @patch("src.advanced_crawler.AsyncCrawler")
    @patch("src.advanced_crawler.ReportExporter")
    def test_export_reports(self, mock_exporter, mock_crawler):
        advanced = AdvancedCrawler(self.config)

        advanced.results = {
            "https://example.com": {"title": "Example"}
        }

        advanced.export_reports("test_reports")

        self.assertEqual(mock_exporter.export_json.call_count, 3)
        mock_exporter.export_html.assert_called_once()

    @patch("src.advanced_crawler.AsyncCrawler")
    @patch("src.advanced_crawler.ReportExporter")
    def test_export_reports_creates_directory(
        self,
        mock_exporter,
        mock_crawler,
    ):
        import tempfile
        from pathlib import Path

        advanced = AdvancedCrawler(self.config)

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "reports"

            advanced.export_reports(str(output_dir))

            self.assertTrue(output_dir.exists())

    @patch("src.advanced_crawler.AsyncCrawler")
    async def test_close(self, mock_crawler):
        mock_instance = mock_crawler.return_value
        mock_instance.close = AsyncMock()

        advanced = AdvancedCrawler(self.config)

        await advanced.close()

        mock_instance.close.assert_awaited_once()

    @patch("src.advanced_crawler.AsyncCrawler")
    async def test_async_context_manager(self, mock_crawler):
        mock_instance = mock_crawler.return_value
        mock_instance.close = AsyncMock()

        async with AdvancedCrawler(self.config) as advanced:
            self.assertIsNotNone(advanced.crawler)

        mock_instance.close.assert_awaited_once()

    @patch("src.advanced_crawler.AsyncCrawler")
    async def test_crawl_passes_sitemap_urls(self, mock_crawler):
        self.config.sitemap_urls = [
            "https://example.com/sitemap.xml"
        ]

        mock_instance = mock_crawler.return_value
        mock_instance.crawl = AsyncMock(return_value={})

        advanced = AdvancedCrawler(self.config)

        await advanced.crawl()

        kwargs = mock_instance.crawl.await_args.kwargs

        self.assertEqual(
            kwargs["sitemap_urls"],
            ["https://example.com/sitemap.xml"],
        )


if __name__ == "__main__":
    unittest.main()
