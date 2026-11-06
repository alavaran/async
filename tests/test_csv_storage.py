
import csv
import tempfile
import unittest
from pathlib import Path

from src.storage import CSVStorage


class TestCSVStorage(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.filepath = Path(self.temp_dir.name) / "results.csv"
        self.storage = CSVStorage(self.filepath)

    async def asyncTearDown(self):
        await self.storage.close()
        self.temp_dir.cleanup()

    async def test_save_record_and_header(self):
        await self.storage.save({
            "url": "https://example.com",
            "title": "Example",
        })

        with self.filepath.open(
            encoding="utf-8-sig",
            newline="",
        ) as file:
            rows = list(csv.DictReader(file))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["title"], "Example")

    async def test_append_multiple_records(self):
        await self.storage.save({"url": "https://a.com", "title": "A"})
        await self.storage.save({"url": "https://b.com", "title": "B"})

        with self.filepath.open(
            encoding="utf-8-sig",
            newline="",
        ) as file:
            rows = list(csv.DictReader(file))

        self.assertEqual(len(rows), 2)
        self.assertEqual([row["title"] for row in rows], ["A", "B"])

    async def test_special_characters_and_unicode(self):
        record = {
            "url": "https://example.com",
            "title": 'Тест, "кавычки"',
        }
        await self.storage.save(record)

        with self.filepath.open(
            encoding="utf-8-sig",
            newline="",
        ) as file:
            rows = list(csv.DictReader(file))

        self.assertEqual(rows[0]["title"], record["title"])

    async def test_reject_new_fields(self):
        await self.storage.save({"url": "https://a.com"})

        with self.assertRaises(ValueError):
            await self.storage.save({
                "url": "https://b.com",
                "title": "Unexpected field",
            })

    async def test_save_after_close_fails(self):
        await self.storage.close()

        with self.assertRaises(RuntimeError):
            await self.storage.save({"url": "https://example.com"})


if __name__ == "__main__":
    unittest.main()
