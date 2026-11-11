
import json
import tempfile
import unittest
from pathlib import Path

from src.config import CrawlerConfig


class TestCrawlerConfig(unittest.TestCase):

    def test_default_config(self):
        """Проверяет значения по умолчанию."""
        config = CrawlerConfig()

        self.assertEqual(config.max_concurrent, 5)
        self.assertEqual(config.max_per_domain, 3)
        self.assertEqual(config.requests_per_second, 1.0)
        self.assertEqual(config.max_pages, 100)
        self.assertEqual(config.max_depth, 2)
        self.assertEqual(config.start_urls, [])

    def test_from_dict(self):
        """Создаёт конфигурацию из словаря."""
        config = CrawlerConfig.from_dict({
            "max_concurrent": 10,
            "max_pages": 200,
            "start_urls": ["https://example.com"],
        })

        self.assertEqual(config.max_concurrent, 10)
        self.assertEqual(config.max_pages, 200)
        self.assertEqual(config.start_urls, ["https://example.com"])

    def test_load_json(self):
        """Загружает конфигурацию из JSON."""
        data = {
            "max_concurrent": 8,
            "max_pages": 150,
            "start_urls": ["https://example.com"],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.json"
            path.write_text(json.dumps(data), encoding="utf-8")

            config = CrawlerConfig.from_file(path)

        self.assertEqual(config.max_concurrent, 8)
        self.assertEqual(config.max_pages, 150)

    def test_load_yaml(self):
        """Загружает конфигурацию из YAML."""
        import yaml

        data = {
            "max_concurrent": 6,
            "max_pages": 80,
            "start_urls": ["https://example.com"],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.yaml"
            path.write_text(
                yaml.safe_dump(data),
                encoding="utf-8",
            )

            config = CrawlerConfig.from_file(path)

        self.assertEqual(config.max_concurrent, 6)
        self.assertEqual(config.max_pages, 80)

    def test_missing_file(self):
        """Отсутствующий файл вызывает FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            CrawlerConfig.from_file("missing_config.yaml")

    def test_unsupported_format(self):
        """Неподдерживаемый формат вызывает ValueError."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.txt"
            path.write_text("test", encoding="utf-8")

            with self.assertRaises(ValueError):
                CrawlerConfig.from_file(path)

    def test_unknown_field(self):
        """Неизвестные параметры вызывают ValueError."""
        with self.assertRaises(ValueError):
            CrawlerConfig.from_dict({
                "unknown_parameter": 123,
            })

    def test_invalid_max_concurrent(self):
        """Количество конкурентных задач должно быть положительным."""
        with self.assertRaises(ValueError):
            CrawlerConfig.from_dict({
                "max_concurrent": 0,
            })

    def test_invalid_requests_per_second(self):
        """Скорость запросов должна быть положительной."""
        with self.assertRaises(ValueError):
            CrawlerConfig.from_dict({
                "requests_per_second": 0,
            })

    def test_invalid_start_urls(self):
        """Стартовые URL должны быть списком строк."""
        with self.assertRaises(ValueError):
            CrawlerConfig.from_dict({
                "start_urls": "https://example.com",
            })


if __name__ == "__main__":
    unittest.main()
