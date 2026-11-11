
import unittest
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from src.stats import CrawlerStats


class TestCrawlerStats(unittest.TestCase):

    def setUp(self):
        self.stats = CrawlerStats()

    def test_initial_state(self):
        """Статистика создаётся с нулевыми счётчиками."""
        self.assertEqual(self.stats.pages_processed, 0)
        self.assertEqual(self.stats.successful_pages, 0)
        self.assertEqual(self.stats.failed_pages, 0)
        self.assertEqual(self.stats.status_codes, {})
        self.assertEqual(self.stats.domains, {})

    def test_record_successful_page(self):
        """Успешная страница учитывается корректно."""
        self.stats.record_page(
            "https://example.com/page",
            200,
            True,
        )

        self.assertEqual(self.stats.pages_processed, 1)
        self.assertEqual(self.stats.successful_pages, 1)
        self.assertEqual(self.stats.failed_pages, 0)

    def test_record_failed_page(self):
        """Неуспешная страница учитывается корректно."""
        self.stats.record_page(
            "https://example.com/page",
            500,
            False,
        )

        self.assertEqual(self.stats.pages_processed, 1)
        self.assertEqual(self.stats.successful_pages, 0)
        self.assertEqual(self.stats.failed_pages, 1)

    def test_status_distribution(self):
        """Подсчитывается распределение HTTP-статусов."""
        self.stats.record_page("https://example.com/1", 200, True)
        self.stats.record_page("https://example.com/2", 200, True)
        self.stats.record_page("https://example.com/3", 404, False)

        self.assertEqual(self.stats.status_codes[200], 2)
        self.assertEqual(self.stats.status_codes[404], 1)

    def test_domain_distribution(self):
        """Подсчитывается количество страниц по доменам."""
        self.stats.record_page("https://example.com/1", 200, True)
        self.stats.record_page("https://example.com/2", 200, True)
        self.stats.record_page("https://google.com/", 200, True)

        self.assertEqual(self.stats.domains["example.com"], 2)
        self.assertEqual(self.stats.domains["google.com"], 1)

    def test_top_domains_limit(self):
        """В топ доменов попадают максимум 10 записей."""
        for i in range(12):
            self.stats.record_page(
                f"https://domain{i}.com/",
                200,
                True,
            )

        self.assertEqual(len(self.stats.top_domains), 10)

    def test_runtime_and_speed(self):
        """Проверяется расчёт времени работы и скорости."""
        start = datetime(2026, 1, 1, tzinfo=UTC)

        with patch("src.stats.datetime") as mock_datetime:
            mock_datetime.now.side_effect = [
                start,
                start + timedelta(seconds=10),
            ]

            stats = CrawlerStats()

            for i in range(20):
                stats.record_page(
                    f"https://example.com/{i}",
                    200,
                    True,
                )

            stats.finish()

            self.assertEqual(stats.runtime, 10)
            self.assertEqual(stats.pages_per_second, 2)

    def test_to_dict(self):
        """Экспорт статистики возвращает словарь."""
        self.stats.record_page(
            "https://example.com/",
            200,
            True,
        )

        result = self.stats.to_dict()

        self.assertEqual(result["pages_processed"], 1)
        self.assertEqual(result["successful_pages"], 1)
        self.assertEqual(result["failed_pages"], 0)
        self.assertIn("status_distribution", result)
        self.assertIn("top_domains", result)
        self.assertIn("pages_per_second", result)


if __name__ == "__main__":
    unittest.main()
