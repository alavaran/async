
import unittest
from unittest.mock import AsyncMock, MagicMock

import aiohttp

from src.robots_parser import RobotsParser


class TestRobotsParser(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.session = MagicMock()
        self.robots = RobotsParser(self.session)

    async def test_disallow_rule(self):
        response = MagicMock()
        response.status = 200
        response.text = AsyncMock(
            return_value=(
                "User-agent: *\n"
                "Disallow: /private\n"
                "Allow: /private/public\n"
                "Crawl-delay: 3\n"
            )
        )

        context = MagicMock()
        context.__aenter__ = AsyncMock(return_value=response)
        context.__aexit__ = AsyncMock(return_value=False)
        self.session.get.return_value = context

        await self.robots.fetch_robots("https://example.com")

        self.assertFalse(
            self.robots.can_fetch("https://example.com/private", "*")
        )
        self.assertTrue(
            self.robots.can_fetch("https://example.com/public", "*")
        )
        self.assertEqual(self.robots.get_crawl_delay("*"), 3.0)

    async def test_crawl_delay(self):
        response = MagicMock()
        response.status = 200
        response.text = AsyncMock(
            return_value="User-agent: *\nCrawl-delay: 3"
        )

        context = MagicMock()
        context.__aenter__ = AsyncMock(return_value=response)
        context.__aexit__ = AsyncMock(return_value=False)
        self.session.get.return_value = context

        await self.robots.fetch_robots("https://example.com")

        self.assertEqual(self.robots.get_crawl_delay("*"), 3.0)

    async def test_rules_are_cached(self):
        response = MagicMock()
        response.status = 200
        response.text = AsyncMock(return_value="User-agent: *\nAllow: /")

        context = MagicMock()
        context.__aenter__ = AsyncMock(return_value=response)
        context.__aexit__ = AsyncMock(return_value=False)
        self.session.get.return_value = context

        await self.robots.fetch_robots("https://example.com")
        await self.robots.fetch_robots("https://example.com")

        self.session.get.assert_called_once()

    async def test_unloaded_domain_raises(self):
        with self.assertRaises(RuntimeError):
            self.robots.can_fetch("https://example.com/page")


if __name__ == "__main__":
    unittest.main()
