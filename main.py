import asyncio
import time

from src.crawler import AsyncCrawler
from src.parser import HTMLParser


async def main():
    crawler = AsyncCrawler(max_concurrent=5)
    parser = HTMLParser()

    catalog_url = "http://books.toscrape.com/"

    catalog_html = await crawler.fetch_url(catalog_url)

    if not catalog_html:
        print("Не удалось загрузить каталог")
        await crawler.close()
        return

    book_urls = parser.get_book_urls(catalog_html)

    print(f"Найдено книг: {len(book_urls)}")

    book_urls = book_urls[:10]

    # Последовательная загрузка
    start = time.perf_counter()

    sequential_results = {}

    for url in book_urls:
        sequential_results[url] = await crawler.fetch_url(url)

    sequential_time = time.perf_counter() - start

    # Берём только успешно загруженные URL
    successful_urls = [
        url
        for url, html in sequential_results.items()
        if html
    ]

    # Параллельная загрузка
    start = time.perf_counter()

    parallel_results = await crawler.fetch_urls(successful_urls)

    parallel_time = time.perf_counter() - start

    # Результаты
    print("\nРезультаты сравнения:")
    print(f"Последовательно: {sequential_time:.2f} сек.")
    print(f"Параллельно:     {parallel_time:.2f} сек.")

    if parallel_time > 0:
        speedup = sequential_time / parallel_time
        print(f"Ускорение:       {speedup:.2f}x")

    # Ошибки параллельной загрузки
    print("\nОшибки параллельной загрузки:")

    for url, html in parallel_results.items():
        if not html:
            print(f"❌ {url}")

    # Парсим результаты
    books = []

    for url, html in parallel_results.items():
        if not html:
            continue

        book = parser.parse(html)
        book["url"] = url
        books.append(book)

    print(f"\nУспешно распарсено: {len(books)} книг")

    await crawler.close()


if __name__ == "__main__":
    asyncio.run(main())