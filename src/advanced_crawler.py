
from pathlib import Path

from src.config import CrawlerConfig
from src.crawler import AsyncCrawler
from src.exporter import ReportExporter
from src.retry_strategy import RetryStrategy
from src.storage import CSVStorage, JSONStorage, SQLiteStorage


class AdvancedCrawler:
    """Facade для управления crawler и его компонентами."""

    def __init__(self, config: CrawlerConfig):
        self.config = config

        retry_strategy = RetryStrategy(
            max_retries=config.max_retries,
            backoff_factor=config.backoff_base,
        )

        storage = self._create_storage(config.storage)
        self.crawler = AsyncCrawler(
            max_concurrent=config.max_concurrent,
            max_per_domain=config.max_per_domain,
            requests_per_second=config.requests_per_second,
            respect_robots=config.respect_robots,
            min_delay=config.min_delay,
            jitter=config.jitter,
            max_retries=config.max_retries,
            connect_timeout=config.connect_timeout,
            read_timeout=config.read_timeout,
            total_timeout=config.total_timeout,
            backoff_base=config.backoff_base,
            user_agent=config.user_agent,
            retry_strategy=retry_strategy,
            storage=storage,
        )

        self.results = {}

    @classmethod
    def from_config(cls, config_path: str = "config.yaml"):
        """Создаёт crawler из конфигурационного файла."""
        config = CrawlerConfig.from_file(config_path)
        return cls(config)

    async def crawl(self) -> dict:
        """Запускает обход с параметрами из конфигурации."""

        self.results = await self.crawler.crawl(
            start_urls=self.config.start_urls,
            max_pages=self.config.max_pages,
            max_depth=self.config.max_depth,
            same_domain_only=self.config.same_domain_only,
            include_patterns=self.config.include_patterns,
            exclude_patterns=self.config.exclude_patterns,
            sitemap_urls=self.config.sitemap_urls,
        )

        return self.results

    def get_stats(self) -> dict:
        return self.crawler.get_stats()

    def get_monitoring(self) -> dict:
        return self.crawler.get_monitoring()

    def get_rate_stats(self) -> dict:
        return self.crawler.get_rate_stats()

    def get_error_stats(self) -> dict:
        return self.crawler.get_error_stats()

    def export_reports(
        self,
        output_dir: str = "reports",
    ) -> None:
        """Экспортирует результаты обхода и отчёты."""

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        stats = self.get_stats()

        ReportExporter.export_json(
            self.results,
            output_path / "crawl_results.json",
        )

        ReportExporter.export_json(
            stats,
            output_path / "crawler_stats.json",
        )

        ReportExporter.export_json(
            self.get_error_stats(),
            output_path / "error_report.json",
        )

        ReportExporter.export_html(
            stats,
            output_path / "crawler_report.html",
        )

    def export_to_json(self, filename: str) -> None:
        """Экспортирует статистику crawler в JSON."""
        ReportExporter.export_json(
            self.get_stats(),
            filename,
        )

    def export_to_html_report(self, filename: str) -> None:
        """Создаёт HTML-отчёт со статистикой crawler."""
        ReportExporter.export_html(
            self.get_stats(),
            filename,
        )

    async def close(self) -> None:
        await self.crawler.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()

    @staticmethod
    def _create_storage(storage_config: dict):
        """Создаёт хранилище на основе конфигурации."""

        if not storage_config:
            return None

        config = storage_config.copy()
        storage_type = config.pop("type", "").lower()

        storage_classes = {
            "json": JSONStorage,
            "csv": CSVStorage,
            "sqlite": SQLiteStorage,
        }

        storage_class = storage_classes.get(storage_type)

        if storage_class is None:
            raise ValueError(
                f"Unsupported storage type: {storage_type}"
            )

        return storage_class(**config)
