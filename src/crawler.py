import asyncio
import logging
import aiohttp

from src.parser import HTMLParser

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class AsyncCrawler:
    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent

        timeout = aiohttp.ClientTimeout(
            connect=1,
            sock_read=1,
        )

        self.session = aiohttp.ClientSession(
            timeout=timeout,
        )

        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_url(self, url: str) -> str:
        async with self.semaphore:
            logging.info(f"Начало загрузки: {url}")

            try:
                async with self.session.get(url) as response:
                    response.raise_for_status()

                    content = await response.text()

                    logging.info(
                        f"Успешно загружено: {url} "
                        f"(status={response.status})"
                    )

                    return content

            except aiohttp.ClientResponseError as e:
                logging.error(
                    f"HTTP ошибка для {url}: "
                    f"{e.status} {e.message}"
                )
                return ""

            except asyncio.TimeoutError:
                logging.error(
                    f"Timeout для {url}"
                )
                return ""

            except aiohttp.ClientError as e:
                logging.error(
                    f"Сетевая ошибка для {url}: "
                    f"{type(e).__name__}: {e!r}"
                )
                return ""

    async def fetch_urls(self, urls: list[str]) -> dict[str, str]:
        tasks = [
            self.fetch_url(url)
            for url in urls
        ]

        results = await asyncio.gather(*tasks)

        return dict(zip(urls, results))

    
    async def fetch_and_parse(self, url: str) -> dict:
        html = await self.fetch_url(url)

        if not html:
            return {
                "url": url,
                "title": "",
                "text": "",
                "links": [],
                "metadata": {
                    "title": "",
                    "description": "",
                    "keywords": "",
                },
                "images": [],
                "headings": [],
                "tables": [],
                "lists": [],
            }

        parser = HTMLParser()
        return await parser.parse_html(html, url)


    async def close(self):
        await self.session.close()