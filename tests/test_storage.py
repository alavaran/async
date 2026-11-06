
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from src.storage import JSONStorage


class TestJSONStorage(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.filepath = Path(self.temp_dir.name) / "results.jsonl"
        self.storage = JSONStorage(self.filepath)

    async def asyncTearDown(self):
        await self.storage.close()
        self.temp_dir.cleanup()

    async def test_save_one_record(self):
        record = {
            "url": "https://example.com",
            "title": "Example",
            "text": "Test content",
        }

        await self.storage.save(record)

        with self.filepath.open(encoding="utf-8") as file:
            saved = json.loads(file.readline())

        self.assertEqual(saved, record)

    async def test_append_multiple_records(self):
        records = [
            {"url": "https://example.com", "title": "First"},
            {"url": "https://example.org", "title": "Second"},
        ]

        for record in records:
            await self.storage.save(record)

        with self.filepath.open(encoding="utf-8") as file:
            saved = [json.loads(line) for line in file if line.strip()]

        self.assertEqual(saved, records)

    async def test_save_unicode(self):
        record = {"title": "Привет, мир"}

        await self.storage.save(record)

        content = self.filepath.read_text(encoding="utf-8")
        self.assertIn("Привет, мир", content)
        self.assertEqual(json.loads(content), record)

    async def test_datetime_is_serialized(self):
        from datetime import datetime, timezone

        record = {
            "crawled_at": datetime(2026, 1, 1, tzinfo=timezone.utc)
        }

        await self.storage.save(record)

        saved = json.loads(self.filepath.read_text(encoding="utf-8"))
        self.assertEqual(saved["crawled_at"], "2026-01-01 00:00:00+00:00")

    async def test_save_after_close_fails(self):
        await self.storage.close()

        with self.assertRaises(RuntimeError):
            await self.storage.save({"url": "https://example.com"})

    async def test_retries_after_os_error(self):
        original_open = __import__("aiofiles").open
        self.storage.retry_delay = 0
        calls = 0

        def flaky_open(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise OSError("Temporary file error")
            return original_open(*args, **kwargs)

        with patch("src.storage.aiofiles.open", side_effect=flaky_open):
            await self.storage.save({"url": "https://example.com"})

        self.assertEqual(calls, 2)
        self.assertTrue(self.filepath.exists())


if __name__ == "__main__":
    unittest.main()
