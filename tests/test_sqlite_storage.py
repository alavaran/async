
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from src.storage import SQLiteStorage


class TestSQLiteStorage(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.filepath = Path(self.temp_dir.name) / "crawler.db"
        self.storage = SQLiteStorage(self.filepath, batch_size=2)
        await self.storage.init_db()

    async def asyncTearDown(self):
        await self.storage.close()
        self.temp_dir.cleanup()

    def make_record(self, url):
        return {
            "url": url,
            "title": "Заголовок",
            "text": "Текст страницы",
            "links": ["https://example.org"],
            "metadata": {"language": "ru"},
            "crawled_at": datetime.now(UTC).isoformat(),
            "status_code": 200,
            "content_type": "text/html",
        }

    async def test_batch_insert(self):
        await self.storage.save(self.make_record("https://a.example"))
        await self.storage.save(self.make_record("https://b.example"))

        rows = await self.storage.fetch_all()

        self.assertEqual(len(rows), 2)

    async def test_flush_remaining_records(self):
        await self.storage.save(self.make_record("https://a.example"))

        await self.storage.flush()
        rows = await self.storage.fetch_all()

        self.assertEqual(len(rows), 1)

    async def test_json_fields_round_trip(self):
        record = self.make_record("https://a.example")
        await self.storage.save(record)

        rows = await self.storage.fetch_all()

        self.assertEqual(rows[0]["links"], record["links"])
        self.assertEqual(rows[0]["metadata"], record["metadata"])

    async def test_close_flushes_buffer(self):
        await self.storage.save(self.make_record("https://a.example"))
        await self.storage.close()

        self.assertTrue(self.storage._closed)

        # Verify persistence through a separate connection.
        import aiosqlite

        async with aiosqlite.connect(self.filepath) as db:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM crawled_pages"
            )
            count = (await cursor.fetchone())[0]

        self.assertEqual(count, 1)

    async def test_save_after_close_fails(self):
        await self.storage.close()

        with self.assertRaises(RuntimeError):
            await self.storage.save(self.make_record("https://a.example"))


if __name__ == "__main__":
    unittest.main()
