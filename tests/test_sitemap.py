
import unittest
from unittest.mock import AsyncMock, MagicMock

import aiohttp

from src.sitemap import SitemapParser


class TestSitemapParser(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.session = MagicMock()
        self.parser = SitemapParser(self.session)

    def mock_response(self, content, status=200):
        response = MagicMock()
        response.status = status
        response.read = AsyncMock(return_value=content)
        response.raise_for_status = MagicMock()

        context_manager = MagicMock()
        context_manager.__aenter__ = AsyncMock(
            return_value=response
        )
        context_manager.__aexit__ = AsyncMock(
            return_value=None
        )

        self.session.get.return_value = context_manager

        return response

    async def test_regular_sitemap(self):
        """Парсер извлекает URL из обычного sitemap."""
        xml = b"""
        <urlset>
            <url><loc>https://example.com/</loc></url>
            <url><loc>https://example.com/about</loc></url>
        </urlset>
        """

        self.mock_response(xml)

        result = await self.parser.fetch_sitemap(
            "https://example.com/sitemap.xml"
        )

        self.assertEqual(
            result,
            [
                "https://example.com/",
                "https://example.com/about",
            ],
        )

    async def test_sitemap_with_namespace(self):
        """Парсер поддерживает XML namespace."""
        xml = b"""
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url><loc>https://example.com/</loc></url>
            <url><loc>https://example.com/blog</loc></url>
        </urlset>
        """

        self.mock_response(xml)

        result = await self.parser.fetch_sitemap(
            "https://example.com/sitemap.xml"
        )

        self.assertEqual(len(result), 2)
        self.assertIn("https://example.com/blog", result)

    async def test_sitemap_index(self):
        """Парсер рекурсивно загружает вложенные sitemap."""
        index_xml = b"""
        <sitemapindex>
            <sitemap>
                <loc>https://example.com/sitemap1.xml</loc>
            </sitemap>
            <sitemap>
                <loc>https://example.com/sitemap2.xml</loc>
            </sitemap>
        </sitemapindex>
        """

        sitemap1 = b"""
        <urlset>
            <url><loc>https://example.com/page1</loc></url>
        </urlset>
        """

        sitemap2 = b"""
        <urlset>
            <url><loc>https://example.com/page2</loc></url>
        </urlset>
        """

        responses = {
            "https://example.com/sitemap-index.xml": index_xml,
            "https://example.com/sitemap1.xml": sitemap1,
            "https://example.com/sitemap2.xml": sitemap2,
        }

        def get_response(url):
            self.mock_response(responses[url])
            return self.session.get.return_value

        self.session.get.side_effect = get_response

        result = await self.parser.fetch_sitemap(
            "https://example.com/sitemap-index.xml"
        )

        self.assertEqual(
            result,
            [
                "https://example.com/page1",
                "https://example.com/page2",
            ],
        )

    async def test_duplicate_urls(self):
        """Дубликаты URL удаляются."""
        xml = b"""
        <urlset>
            <url><loc>https://example.com/page</loc></url>
            <url><loc>https://example.com/page</loc></url>
        </urlset>
        """

        self.mock_response(xml)

        result = await self.parser.fetch_sitemap(
            "https://example.com/sitemap.xml"
        )

        self.assertEqual(
            result,
            ["https://example.com/page"],
        )

    async def test_circular_sitemap_reference(self):
        """Циклические ссылки между sitemap не вызывают бесконечную рекурсию."""
        sitemap_a = b"""
        <sitemapindex>
            <sitemap>
                <loc>https://example.com/sitemap-b.xml</loc>
            </sitemap>
        </sitemapindex>
        """

        sitemap_b = b"""
        <sitemapindex>
            <sitemap>
                <loc>https://example.com/sitemap-a.xml</loc>
            </sitemap>
        </sitemapindex>
        """

        responses = {
            "https://example.com/sitemap-a.xml": sitemap_a,
            "https://example.com/sitemap-b.xml": sitemap_b,
        }

        def get_response(url):
            self.mock_response(responses[url])
            return self.session.get.return_value

        self.session.get.side_effect = get_response

        result = await self.parser.fetch_sitemap(
            "https://example.com/sitemap-a.xml"
        )

        self.assertEqual(result, [])
        self.assertEqual(self.session.get.call_count, 2)

    async def test_invalid_xml(self):
        """Некорректный XML вызывает ValueError."""
        self.mock_response(b"<urlset><url>")

        with self.assertRaises(ValueError):
            await self.parser.fetch_sitemap(
                "https://example.com/sitemap.xml"
            )

    async def test_http_error(self):
        """HTTP-ошибки пробрасываются вызывающему коду."""
        response = self.mock_response(b"", status=404)
        response.raise_for_status.side_effect = (
            aiohttp.ClientResponseError(
                request_info=MagicMock(),
                history=(),
                status=404,
                message="Not Found",
            )
        )

        with self.assertRaises(aiohttp.ClientResponseError):
            await self.parser.fetch_sitemap(
                "https://example.com/sitemap.xml"
            )


if __name__ == "__main__":
    unittest.main()
