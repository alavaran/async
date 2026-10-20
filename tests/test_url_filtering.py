
import unittest

from src.crawler import AsyncCrawler


class TestURLFiltering(unittest.TestCase):
    def setUp(self):
        # Avoid creating a ClientSession just to test URL filtering.
        self.crawler = object.__new__(AsyncCrawler)

    def test_same_domain_allowed(self):
        self.assertTrue(
            self.crawler.should_crawl(
                "https://example.com/page",
                "example.com",
            )
        )

    def test_external_domain_rejected(self):
        self.assertFalse(
            self.crawler.should_crawl(
                "https://other.com/page",
                "example.com",
            )
        )

    def test_include_pattern(self):
        self.assertTrue(
            self.crawler.should_crawl(
                "https://example.com/products/1",
                "example.com",
                include_patterns=[r"/products/"],
            )
        )

        self.assertFalse(
            self.crawler.should_crawl(
                "https://example.com/about",
                "example.com",
                include_patterns=[r"/products/"],
            )
        )

    def test_exclude_pattern(self):
        self.assertFalse(
            self.crawler.should_crawl(
                "https://example.com/login",
                "example.com",
                exclude_patterns=[r"/login"],
            )
        )

    def test_invalid_scheme(self):
        self.assertFalse(
            self.crawler.should_crawl(
                "javascript:alert(1)",
                "example.com",
            )
        )


if __name__ == "__main__":
    unittest.main()
