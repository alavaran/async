
import json
import tempfile
import unittest
from pathlib import Path

from src.exporter import ReportExporter


class TestReportExporter(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)

        self.stats = {
            "pages_processed": 50,
            "successful_pages": 45,
            "failed_pages": 5,
            "runtime_seconds": 25.5,
            "pages_per_second": 1.96,
            "status_distribution": {
                "200": 45,
                "404": 3,
                "500": 2,
            },
            "top_domains": [
                {"domain": "example.com", "pages": 40},
                {"domain": "google.com", "pages": 10},
            ],
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_export_json(self):
        """JSON-файл создаётся."""
        path = self.base_path / "stats.json"

        ReportExporter.export_json(self.stats, path)

        self.assertTrue(path.exists())

    def test_json_content(self):
        """JSON содержит корректные данные."""
        path = self.base_path / "stats.json"

        ReportExporter.export_json(self.stats, path)

        with path.open(encoding="utf-8") as file:
            result = json.load(file)

        self.assertEqual(
            result["pages_processed"],
            50,
        )
        self.assertEqual(
            result["successful_pages"],
            45,
        )

    def test_export_html(self):
        """HTML-отчёт создаётся."""
        path = self.base_path / "report.html"

        ReportExporter.export_html(self.stats, path)

        self.assertTrue(path.exists())

    def test_html_contains_metrics(self):
        """HTML содержит основные метрики."""
        path = self.base_path / "report.html"

        ReportExporter.export_html(self.stats, path)

        content = path.read_text(encoding="utf-8")

        self.assertIn("Pages processed", content)
        self.assertIn("Successful pages", content)
        self.assertIn("Failed pages", content)
        self.assertIn("25.5 sec", content)

    def test_html_contains_status_codes(self):
        """HTML содержит HTTP-статусы."""
        path = self.base_path / "report.html"

        ReportExporter.export_html(self.stats, path)

        content = path.read_text(encoding="utf-8")

        self.assertIn("200", content)
        self.assertIn("404", content)
        self.assertIn("500", content)

    def test_html_contains_domains(self):
        """HTML содержит топ доменов."""
        path = self.base_path / "report.html"

        ReportExporter.export_html(self.stats, path)

        content = path.read_text(encoding="utf-8")

        self.assertIn("example.com", content)
        self.assertIn("google.com", content)

    def test_nested_directory_creation(self):
        """Экспортёр создаёт вложенные директории."""
        path = self.base_path / "reports" / "2026" / "stats.json"

        ReportExporter.export_json(self.stats, path)

        self.assertTrue(path.exists())


if __name__ == "__main__":
    unittest.main()
