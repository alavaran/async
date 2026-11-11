
import logging
import xml.etree.ElementTree as ET

import aiohttp

logger = logging.getLogger(__name__)


class SitemapParser:
    def __init__(self, session: aiohttp.ClientSession):
        """
        Использует существующую HTTP-сессию crawler.
        Сессию не закрывает — за её жизненный цикл отвечает crawler.
        """
        self.session = session
        self._visited_sitemaps: set[str] = set()
        self._collected_urls: list[str] = []
        self._collected_urls_set: set[str] = set()

    async def fetch_sitemap(self, sitemap_url: str) -> list[str]:
        """
        Загружает sitemap и возвращает все найденные URL.

        Поддерживает:
        - обычный sitemap (urlset);
        - индекс sitemap (sitemapindex);
        - рекурсивную обработку вложенных sitemap.
        """
        self._visited_sitemaps.clear()
        self._collected_urls.clear()
        self._collected_urls_set.clear()

        await self._parse_sitemap(sitemap_url)

        return self._collected_urls.copy()

    async def _parse_sitemap(self, sitemap_url: str) -> None:
        # Защита от циклических ссылок между sitemap.
        if sitemap_url in self._visited_sitemaps:
            return

        self._visited_sitemaps.add(sitemap_url)

        try:
            async with self.session.get(sitemap_url) as response:
                response.raise_for_status()
                content = await response.read()

        except aiohttp.ClientError:
            logger.exception("Failed to fetch sitemap: %s", sitemap_url)
            raise

        try:
            root = ET.fromstring(content)

        except ET.ParseError as exc:
            raise ValueError(
                f"Invalid XML in sitemap: {sitemap_url}"
            ) from exc

        # Namespace может присутствовать, а может отсутствовать.
        tag = root.tag.split("}")[-1]

        if tag == "urlset":
            self._extract_urls(root)

        elif tag == "sitemapindex":
            sitemap_urls = self._extract_locations(root)

            for nested_url in sitemap_urls:
                await self._parse_sitemap(nested_url)

        else:
            logger.warning(
                "Unknown sitemap root element '%s': %s",
                tag,
                sitemap_url,
            )

    def _extract_locations(self, root: ET.Element) -> list[str]:
        """Извлекает значения loc из XML."""
        locations = []

        for element in root.iter():
            if element.tag.split("}")[-1] == "loc" and element.text:
                location = element.text.strip()

                if location:
                    locations.append(location)

        return locations

    def _extract_urls(self, root: ET.Element) -> None:
        """Извлекает URL из обычного sitemap."""
        for url in self._extract_locations(root):
            if url not in self._collected_urls_set:
                self._collected_urls_set.add(url)
                self._collected_urls.append(url)
