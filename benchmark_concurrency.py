
import asyncio
import time

from src.advanced_crawler import AdvancedCrawler
from src.config import CrawlerConfig


async def run_test(concurrency: int):
    config = CrawlerConfig.from_file("config.yaml")

    config.max_pages = 30
    config.max_depth = 2
    config.max_concurrent = concurrency

    started_at = time.perf_counter()

    async with AdvancedCrawler(config) as crawler:
        results = await crawler.crawl()
        stats = crawler.get_stats()

    elapsed = time.perf_counter() - started_at
    pages = len(results)
    speed = pages / elapsed if elapsed > 0 else 0

    return {
        "concurrency": concurrency,
        "pages": pages,
        "successful": stats.get("successful_pages", 0),
        "failed": stats.get("failed_pages", 0),
        "elapsed": round(elapsed, 2),
        "speed": round(speed, 2),
    }


async def main():
    results = []

    for concurrency in [1, 5, 10, 20]:
        print(f"\nTesting concurrency={concurrency}...")
        result = await run_test(concurrency)
        results.append(result)

    print("\n=== Concurrency Benchmark ===")
    print(
        f"{'Workers':<10}"
        f"{'Pages':<10}"
        f"{'Success':<10}"
        f"{'Failed':<10}"
        f"{'Time':<12}"
        f"{'Pages/sec':<12}"
    )

    for result in results:
        print(
            f"{result['concurrency']:<10}"
            f"{result['pages']:<10}"
            f"{result['successful']:<10}"
            f"{result['failed']:<10}"
            f"{result['elapsed']:<12}"
            f"{result['speed']:<12}"
        )


if __name__ == "__main__":
    asyncio.run(main())
