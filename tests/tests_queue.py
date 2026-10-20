
import unittest
import asyncio

from src.queue import CrawlerQueue


class TestCrawlerQueue(unittest.TestCase):
    def setUp(self):
        self.queue = CrawlerQueue()

    def test_priority_order(self):
        self.queue.add_url("https://example.com/low", priority=5)
        self.queue.add_url("https://example.com/high", priority=1)
        self.queue.add_url("https://example.com/medium", priority=3)

        self.assertEqual(
            asyncio.run(self.queue.get_next()),
            "https://example.com/high",
        )

    def test_duplicate_urls(self):
        self.queue.add_url("https://example.com")
        self.queue.add_url("https://example.com")

        self.assertEqual(self.queue.get_stats()["queued"], 1)

    def test_mark_processed(self):
        url = "https://example.com"
        self.queue.add_url(url)
        self.queue.mark_processed(url)

        self.assertEqual(self.queue.get_stats()["processed"], 1)

    def test_mark_failed(self):
        url = "https://example.com"
        self.queue.mark_failed(url, "Timeout")

        self.assertEqual(
            self.queue.failed_urls[url],
            "Timeout",
        )

    def test_empty_queue(self):
        self.assertIsNone(asyncio.run(self.queue.get_next()))


if __name__ == "__main__":
    unittest.main()
