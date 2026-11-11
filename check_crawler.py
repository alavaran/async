import asyncio

from src.crawler import AsyncCrawler


async def main():
    crawler = AsyncCrawler()
    print("saved_pages:", hasattr(crawler, "saved_pages"))
    print("storage_errors:", hasattr(crawler, "storage_errors"))
    await crawler.close()


if __name__ == "__main__":
    asyncio.run(main())