
from collections import Counter
from datetime import datetime, timezone
from urllib.parse import urlparse


class CrawlerStats:
    def __init__(self):
        self.started_at = datetime.now(timezone.utc)
        self.finished_at = None

        self.pages_processed = 0
        self.successful_pages = 0
        self.failed_pages = 0

        self.status_codes = Counter()
        self.domains = Counter()

    def record_page(
        self,
        url: str,
        status_code: int | None,
        success: bool,
    ) -> None:
        """Записывает результат обработки страницы."""
        self.pages_processed += 1

        if success:
            self.successful_pages += 1
        else:
            self.failed_pages += 1

        if status_code is not None:
            self.status_codes[status_code] += 1

        domain = urlparse(url).netloc

        if domain:
            self.domains[domain] += 1

    def finish(self) -> None:
        """Фиксирует время завершения обхода."""
        self.finished_at = datetime.now(timezone.utc)

    @property
    def runtime(self) -> float:
        end_time = self.finished_at or datetime.now(timezone.utc)
        return (end_time - self.started_at).total_seconds()

    @property
    def pages_per_second(self) -> float:
        if self.runtime <= 0:
            return 0.0

        return self.pages_processed / self.runtime

    @property
    def average_speed(self) -> float:
        return self.pages_per_second

    @property
    def top_domains(self) -> list[tuple[str, int]]:
        return self.domains.most_common(10)


    def to_dict(self) -> dict:
        """Возвращает статистику в формате, пригодном для JSON."""
        return {
            "pages_processed": self.pages_processed,
            "successful_pages": self.successful_pages,
            "failed_pages": self.failed_pages,

            # Совместимость с демонстрационным API.
            "total_pages": self.pages_processed,
            "successful": self.successful_pages,
            "failed": self.failed_pages,

            "runtime_seconds": round(self.runtime, 2),
            "pages_per_second": round(self.pages_per_second, 2),
            "status_distribution": dict(self.status_codes),
            "top_domains": [
                {"domain": domain, "pages": count}
                for domain, count in self.top_domains
            ],
        }