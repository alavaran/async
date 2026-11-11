
import asyncio
import json
import logging

from src.advanced_crawler import AdvancedCrawler
from src.cli import parse_args
from src.config import CrawlerConfig
from src.logging_config import setup_logging


async def main():
    args = parse_args()
    config = CrawlerConfig.from_file(args.config)

    # Переопределяем настройки только при передаче аргументов.
    if args.urls is not None:
        config.start_urls = args.urls

    if args.max_pages is not None:
        config.max_pages = args.max_pages

    if args.max_depth is not None:
        config.max_depth = args.max_depth

    if args.respect_robots is not None:
        config.respect_robots = args.respect_robots

    if args.rate_limit is not None:
        config.requests_per_second = args.rate_limit

    async with AdvancedCrawler(config) as crawler:
        results = await crawler.crawl()

        print("\n=== Crawl Summary ===")
        print(f"Pages processed: {len(results)}")
        print(f"Failed URLs: {len(crawler.crawler.failed_urls)}")
        print(f"Visited URLs: {len(crawler.crawler.visited_urls)}")

        print("\n=== Rate Limiting Statistics ===")
        print(crawler.get_rate_stats())

        print("\n=== Crawler Statistics ===")
        print(json.dumps(
            crawler.get_stats(),
            ensure_ascii=False,
            indent=4,
        ))

        print("\n=== Monitoring ===")
        print(json.dumps(
            crawler.get_monitoring(),
            ensure_ascii=False,
            indent=4,
        ))

        if args.output:
            crawler.export_to_json(args.output)
            print(f"\nJSON exported to {args.output}")

        crawler.export_reports(args.output_dir)
        print(f"\nReports exported to {args.output_dir}/")

if __name__ == "__main__":
    setup_logging(
        log_file="logs/crawler.log",
        level=logging.INFO,
        max_bytes=5 * 1024 * 1024,
        backup_count=3,
    )

    asyncio.run(main())
