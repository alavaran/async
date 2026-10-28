import unittest
from unittest.mock import patch

from src.crawler import AsyncCrawler


class TestCrawlerTimeouts(unittest.TestCase):
    @patch("src.crawler.aiohttp.ClientSession")
    def test_custom_timeouts(self, mock_session):
        crawler = AsyncCrawler(
            connect_timeout=5,
            read_timeout=15,
            total_timeout=30,
        )

        timeout = mock_session.call_args.kwargs["timeout"]

        self.assertEqual(timeout.connect, 5)
        self.assertEqual(timeout.sock_read, 15)
        self.assertEqual(timeout.total, 30)

    @patch("src.crawler.aiohttp.ClientSession")
    def test_default_timeouts(self, mock_session):
        crawler = AsyncCrawler()

        timeout = mock_session.call_args.kwargs["timeout"]

        self.assertEqual(timeout.connect, 10)
        self.assertEqual(timeout.sock_read, 10)
        self.assertEqual(timeout.total, 20)