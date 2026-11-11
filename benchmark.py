
import asyncio
import time

from src.advanced_crawler import AdvancedCrawler
from src.config import CrawlerConfig


async def run_benchmark():
    config = CrawlerConfig.from_file("config.yaml")

    # Ограничиваем тест, чтобы не нагружать сайт.
    config.max_pages = 30
    config.max_depth = 2

    started_at = time.perf_counter()

    async with AdvancedCrawler(config) as crawler:
        results = await crawler.crawl()
        stats = crawler.get_stats()

    elapsed = time.perf_counter() - started_at

    pages = len(results)
    speed = pages / elapsed if elapsed > 0 else 0

    print("\n=== Benchmark Results ===")
    print(f"Pages processed: {pages}")
    print(f"Elapsed time: {elapsed:.2f} sec")
    print(f"Average speed: {speed:.2f} pages/sec")
    print(f"Successful pages: {stats.get('successful_pages', 0)}")
    print(f"Failed pages: {stats.get('failed_pages', 0)}")


if __name__ == "__main__":
    asyncio.run(run_benchmark())
