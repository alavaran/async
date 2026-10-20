
import asyncio
import json
import logging

from src.crawler import AsyncCrawler


async def main():
    crawler = AsyncCrawler(
        max_concurrent=10,
        max_per_domain=3,
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

    finally:
        await crawler.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
