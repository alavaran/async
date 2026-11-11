
import asyncio
import statistics
import time
import tracemalloc

import requests
from aiohttp import web
from bs4 import BeautifulSoup

from src.advanced_crawler import AdvancedCrawler
from src.config import CrawlerConfig


async def create_server(page_count: int):
    async def index(request):
        links = "".join(
            f'<a href="/page/{i}">Page {i}</a>'
            for i in range(1, page_count)
        )
        return web.Response(
            text=f"<html><head><title>Index</title></head>"
                 f"<body>{links}</body></html>",
            content_type="text/html",
        )

    async def page(request):
        page_id = request.match_info["page_id"]
        return web.Response(
            text=f"<html><head><title>Page {page_id}</title></head>"
                 f"<body>Content of page {page_id}</body></html>",
            content_type="text/html",
        )

    app = web.Application()
    app.router.add_get("/", index)
    app.router.add_get("/page/{page_id}", page)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()

    port = site._server.sockets[0].getsockname()[1]
    return runner, f"http://127.0.0.1:{port}/"


def sync_crawl(start_url: str, max_pages: int) -> int:
    """Последовательный синхронный обход."""
    visited = set()
    queue = [start_url]

    with requests.Session() as session:
        while queue and len(visited) < max_pages:
            url = queue.pop(0)

            if url in visited:
                continue

            response = session.get(url, timeout=10)
            response.raise_for_status()
            visited.add(url)

            soup = BeautifulSoup(response.text, "lxml")

            for link in soup.find_all("a", href=True):
                next_url = requests.compat.urljoin(
                    url,
                    link["href"],
                )
                if next_url not in visited:
                    queue.append(next_url)

    return len(visited)

async def measure_sync(url: str, page_count: int) -> dict:
    tracemalloc.start()
    tracemalloc.reset_peak()

    started = time.perf_counter()

    pages = await asyncio.to_thread(
        sync_crawl,
        url,
        page_count,
    )

    elapsed = time.perf_counter() - started
    _, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "pages": pages,
        "elapsed": elapsed,
        "speed": pages / elapsed if elapsed else 0,
        "memory_mb": peak_memory / 1024 / 1024,
    }

async def measure_async(
    url: str,
    page_count: int,
    concurrency: int,
) -> dict:
    config = CrawlerConfig.from_file("config.yaml")

    config.start_urls = [url]
    config.max_pages = page_count
    config.max_depth = 1
    config.same_domain_only = True

    config.max_concurrent = concurrency
    config.max_per_domain = concurrency
    config.requests_per_second = 100000
    config.min_delay = 0
    config.jitter = 0
    config.respect_robots = False

    tracemalloc.start()
    tracemalloc.reset_peak()

    started = time.perf_counter()

    async with AdvancedCrawler(config) as crawler:
        results = await crawler.crawl()
        stats = crawler.get_stats()

    elapsed = time.perf_counter() - started
    _, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "pages": len(results),
        "successful": stats["successful_pages"],
        "failed": stats["failed_pages"],
        "elapsed": elapsed,
        "speed": len(results) / elapsed if elapsed else 0,
        "memory_mb": peak_memory / 1024 / 1024,
    }

async def main():
    repetitions = 5
    concurrency_levels = [1, 5, 10, 20]
    all_results = []

    for page_count in [100, 500, 1000]:
        print(f"\n{'=' * 65}")
        print(f"Benchmark: {page_count} pages")
        print("=" * 65)

        runner, url = await create_server(page_count)

        try:
            sync_times = []
            sync_speeds = []
            sync_memories = []

            for run in range(repetitions):
                result = await measure_sync(url, page_count)
                sync_times.append(result["elapsed"])
                sync_speeds.append(result["speed"])
                sync_memories.append(result["memory_mb"])
                print(f"Sync: {run + 1}/{repetitions}")

            sync_time = statistics.median(sync_times)

            all_results.append({
                "pages": page_count,
                "mode": "Sync",
                "workers": 1,
                "time": sync_time,
                "speed": statistics.median(sync_speeds),
                "memory": statistics.median(sync_memories),
                "success": page_count,
                "failed": 0,
                "speedup": 1.0,
            })

            for concurrency in concurrency_levels:
                times = []
                speeds = []
                memories = []
                successful = []
                failed = []

                for run in range(repetitions):
                    result = await measure_async(
                        url,
                        page_count,
                        concurrency,
                    )

                    times.append(result["elapsed"])
                    speeds.append(result["speed"])
                    memories.append(result["memory_mb"])
                    successful.append(result["successful"])
                    failed.append(result["failed"])

                    print(
                        f"Async workers={concurrency}: "
                        f"{run + 1}/{repetitions}"
                    )

                median_time = statistics.median(times)

                all_results.append({
                    "pages": page_count,
                    "mode": "Async",
                    "workers": concurrency,
                    "time": median_time,
                    "speed": statistics.median(speeds),
                    "memory": statistics.median(memories),
                    "success": statistics.median(successful),
                    "failed": statistics.median(failed),
                    "speedup": (
                        sync_time / median_time
                        if median_time > 0 else 0
                    ),
                })

        finally:
            await runner.cleanup()

    print("\n\n" + "=" * 100)
    print("FINAL BENCHMARK REPORT")
    print("=" * 100)

    print(
        f"{'Pages':<10}"
        f"{'Mode':<10}"
        f"{'Workers':<10}"
        f"{'Time (s)':<12}"
        f"{'Pages/s':<12}"
        f"{'Memory MB':<12}"
        f"{'Success':<10}"
        f"{'Failed':<10}"
        f"{'Speedup':<10}"
    )

    print("-" * 100)

    for result in all_results:
        print(
            f"{result['pages']:<10}"
            f"{result['mode']:<10}"
            f"{result['workers']:<10}"
            f"{result['time']:<12.2f}"
            f"{result['speed']:<12.2f}"
            f"{result['memory']:<12.2f}"
            f"{result['success']:<10.0f}"
            f"{result['failed']:<10.0f}"
            f"{result['speedup']:<10.2f}"
        )

    print("\n" + "=" * 100)
    print("RECOMMENDATIONS")
    print("=" * 100)

    for page_count in [100, 500, 1000]:
        async_results = [
            item for item in all_results
            if item["pages"] == page_count
            and item["mode"] == "Async"
        ]

        best = max(async_results, key=lambda item: item["speed"])

        print(
            f"{page_count} pages: best concurrency = "
            f"{best['workers']}, "
            f"{best['speed']:.2f} pages/sec, "
            f"{best['speedup']:.2f}x vs sync"
        )

    overall = [
        item for item in all_results
        if item["pages"] == 1000 and item["mode"] == "Async"
    ]

    best_overall = max(overall, key=lambda item: item["speed"])

    print(
        f"\nBest configuration for 1000 pages: "
        f"{best_overall['workers']} workers"
    )
    print(
        f"Speed: {best_overall['speed']:.2f} pages/sec"
    )
    print(
        f"Memory: {best_overall['memory']:.2f} MB"
    )

if __name__ == "__main__":
    asyncio.run(main())
