
import asyncio
import csv
import json
import logging
from pathlib import Path

from src.crawler import AsyncCrawler
from src.storage import CSVStorage, JSONStorage, SQLiteStorage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


START_URLS = ["https://books.toscrape.com/"]


async def run_with_storage(storage, storage_name):
    """Run crawler with a selected storage backend."""
    crawler = AsyncCrawler(storage=storage)

    try:
        await crawler.crawl(start_urls=START_URLS)

        print(f"\n{storage_name}:")
        print(f"Saved pages: {crawler.saved_pages}")
        print(f"Storage errors: {len(crawler.storage_errors)}")

        if crawler.storage_errors:
            print("First storage error:", crawler.storage_errors[0])

    finally:
        await crawler.close()


def read_json(filepath):
    """Read JSON Lines file."""
    records = []

    if not Path(filepath).exists():
        return records

    with open(filepath, encoding="utf-8") as file:
        for line in file:
            if line.strip():
                records.append(json.loads(line))

    return records


def read_csv(filepath):
    """Read CSV file."""
    if not Path(filepath).exists():
        return []

    with open(
        filepath,
        encoding="utf-8-sig",
        newline="",
    ) as file:
        return list(csv.DictReader(file))


async def read_sqlite(filepath):
    """Read records from SQLite."""
    storage = SQLiteStorage(filepath)

    try:
        return await storage.fetch_all()
    finally:
        await storage.close()


async def main():
    # JSON
    await run_with_storage(
        JSONStorage("results.jsonl"),
        "JSON",
    )

    # CSV
    await run_with_storage(
        CSVStorage("results.csv"),
        "CSV",
    )

    # SQLite
    await run_with_storage(
        SQLiteStorage("crawler.db", batch_size=20),
        "SQLite",
    )

    # Read saved data
    json_records = read_json("results.jsonl")
    csv_records = read_csv("results.csv")
    sqlite_records = await read_sqlite("crawler.db")

    print("\n=== STORAGE STATISTICS ===")
    print(f"JSON records: {len(json_records)}")
    print(f"CSV records: {len(csv_records)}")
    print(f"SQLite records: {len(sqlite_records)}")

    if json_records:
        print("\nExample JSON record:")
        print(json.dumps(
            json_records[0],
            ensure_ascii=False,
            indent=2,
        ))

    if sqlite_records:
        print("\nExample SQLite record:")
        print(json.dumps(
            sqlite_records[0],
            ensure_ascii=False,
            indent=2,
        ))


if __name__ == "__main__":
    asyncio.run(main())
