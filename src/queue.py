
import asyncio
import heapq
from itertools import count


class CrawlerQueue:
    def __init__(self):
        self._queue = []
        self._counter = count()
        self._queued_urls = set()
        self.processed_urls = set()
        self.failed_urls = {}

    def add_url(self, url: str, priority: int = 0) -> None:
        if url in self._queued_urls:
            return

        if url in self.processed_urls or url in self.failed_urls:
            return

        heapq.heappush(
            self._queue,
            (priority, next(self._counter), url),
        )
        self._queued_urls.add(url)

    async def get_next(self) -> str | None:
        if not self._queue:
            return None

        _, _, url = heapq.heappop(self._queue)
        self._queued_urls.discard(url)
        return url

    def mark_processed(self, url: str) -> None:
        self.processed_urls.add(url)
        self.failed_urls.pop(url, None)

    def mark_failed(self, url: str, error: str) -> None:
        self.failed_urls[url] = error

    def get_stats(self) -> dict:
        return {
            "queued": len(self._queue),
            "processed": len(self.processed_urls),
            "failed": len(self.failed_urls),
        }
