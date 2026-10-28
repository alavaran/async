
import asyncio
import json
import logging

from src.retry_strategy import RetryStrategy
from src.crawler import AsyncCrawler


async def main():
    retry_strategy = RetryStrategy(
        max_retries=3,
        backoff_factor=1.0,
    )

    crawler = AsyncCrawler(
        max_concurrent=5,
        max_per_domain=3,
        requests_per_second=1.0,
        respect_robots=True,
        min_delay=0.5,
        retry_strategy=retry_strategy,
    )

    start_urls = [
        "https://books.toscrape.com/",
        "http://books.toscrape.com/catalogue/category/books/travel_2/index.html",
        "http://books.toscrape.com/catalogue/category/books/mystery_3/index.html",
    ]

    try:
        results = await crawler.crawl(
            start_urls=start_urls,
            max_pages=50,
            max_depth=2,
            same_domain_only=True,
            exclude_patterns=[
                r"\.pdf$",
            ],
        )

        with open("crawl_results.json", "w", encoding="utf-8") as file:
            json.dump(
                results,
                file,
                ensure_ascii=False,
                indent=4,
            )

        print("\n=== Crawl Summary ===")
        print(f"Pages processed: {len(results)}")
        print(f"Failed URLs: {len(crawler.failed_urls)}")
        print(f"Visited URLs: {len(crawler.visited_urls)}")
        print("Results saved to crawl_results.json")
        print("\n=== Rate Limiting Statistics ===")
        print(crawler.get_rate_stats())
        print(f"Blocked URLs: {sorted(crawler.blocked_urls)}")
        with open("error_report.json", "w", encoding="utf-8") as file:
            json.dump(
                crawler.get_error_stats(),
                file,
                ensure_ascii=False,
                indent=4,
            )

    finally:
        await crawler.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
