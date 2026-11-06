import asyncio
import json
import logging
import csv
import io
import aiosqlite

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import aiofiles

logger = logging.getLogger(__name__)


class DataStorage(ABC):
    """Abstract interface for asynchronous data storage."""

    @abstractmethod
    async def save(self, data: dict[str, Any]) -> None:
        """Save one record."""
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        """Release storage resources."""
        raise NotImplementedError


class JSONStorage(DataStorage):
    """Append records to a JSON Lines file."""

    def __init__(
        self,
        filepath: str | Path = "results.jsonl",
        indent: int | None = None,
        max_retries: int = 3,
        retry_delay: float = 0.5,
    ) -> None:
        if max_retries < 0:
            raise ValueError("max_retries must be >= 0")
        if retry_delay < 0:
            raise ValueError("retry_delay must be >= 0")

        self.filepath = Path(filepath)
        self.indent = indent
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._lock = asyncio.Lock()
        self._closed = False

    async def save(self, data: dict[str, Any]) -> None:
        """Append one JSON record; retry transient file errors."""
        if self._closed:
            raise RuntimeError("Storage is closed")

        # Convert datetime and other unsupported values to strings.
        serialized = json.dumps(
            data,
            ensure_ascii=False,
            indent=self.indent,
            default=str,
        )

        async with self._lock:
            for attempt in range(self.max_retries + 1):
                try:
                    async with aiofiles.open(
                        self.filepath,
                        mode="a",
                        encoding="utf-8",
                    ) as file:
                        await file.write(serialized + "\n")
                    return
                except OSError:
                    logger.exception(
                        "Failed to save record to %s (attempt %s/%s)",
                        self.filepath,
                        attempt + 1,
                        self.max_retries + 1,
                    )

                    if attempt >= self.max_retries:
                        raise

                    await asyncio.sleep(
                        self.retry_delay * (2 ** attempt)
                    )

    async def close(self) -> None:
        """Mark storage as closed."""
        self._closed = True


class CSVStorage(DataStorage):
    """Append records to a CSV file asynchronously."""

    def __init__(
        self,
        filepath: str | Path = "results.csv",
        encoding: str = "utf-8-sig",
        max_retries: int = 3,
        retry_delay: float = 0.5,
    ) -> None:
        if max_retries < 0:
            raise ValueError("max_retries must be >= 0")
        if retry_delay < 0:
            raise ValueError("retry_delay must be >= 0")

        self.filepath = Path(filepath)
        self.encoding = encoding
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._lock = asyncio.Lock()
        self._closed = False
        self._headers: list[str] | None = None

    async def save(self, data: dict[str, Any]) -> None:
        """Append a record, writing the header only once."""
        if self._closed:
            raise RuntimeError("Storage is closed")

        async with self._lock:
            for attempt in range(self.max_retries + 1):
                try:
                    # Detect existing headers when the file already exists.
                    if self._headers is None and self.filepath.exists():
                        async with aiofiles.open(
                            self.filepath,
                            mode="r",
                            encoding=self.encoding,
                            newline="",
                        ) as file:
                            first_line = await file.readline()

                        if first_line:
                            self._headers = next(
                                csv.reader([first_line])
                            )

                    if self._headers is None:
                        self._headers = list(data.keys())

                    # Keep a stable schema. New fields are not silently dropped.
                    new_fields = set(data) - set(self._headers)
                    if new_fields:
                        raise ValueError(
                            "CSV schema changed; unexpected fields: "
                            f"{sorted(new_fields)}"
                        )

                    buffer = io.StringIO(newline="")
                    writer = csv.DictWriter(
                        buffer,
                        fieldnames=self._headers,
                        extrasaction="raise",
                    )

                    is_new_file = (
                        not self.filepath.exists()
                        or self.filepath.stat().st_size == 0
                    )

                    if is_new_file:
                        writer.writeheader()

                    writer.writerow(data)
                    content = buffer.getvalue()

                    async with aiofiles.open(
                        self.filepath,
                        mode="a",
                        encoding=self.encoding,
                        newline="",
                    ) as file:
                        await file.write(content)

                    return

                except OSError:
                    logger.exception(
                        "Failed to save CSV record to %s "
                        "(attempt %s/%s)",
                        self.filepath,
                        attempt + 1,
                        self.max_retries + 1,
                    )

                    if attempt >= self.max_retries:
                        raise

                    await asyncio.sleep(
                        self.retry_delay * (2 ** attempt)
                    )

    async def close(self) -> None:
        """Mark storage as closed."""
        self._closed = True


class SQLiteStorage(DataStorage):
    """Asynchronous SQLite storage for crawler results."""

    def __init__(
        self,
        filepath: str | Path = "crawler.db",
        batch_size: int = 100,
    ) -> None:
        if batch_size < 1:
            raise ValueError("batch_size must be >= 1")

        self.filepath = str(filepath)
        self.batch_size = batch_size
        self._connection: aiosqlite.Connection | None = None
        self._buffer: list[dict[str, Any]] = []
        self._lock = asyncio.Lock()
        self._closed = False

    async def init_db(self) -> None:
        """Create the database table and indexes."""
        if self._closed:
            raise RuntimeError("Storage is closed")

        if self._connection is not None:
            return

        self._connection = await aiosqlite.connect(self.filepath)
        self._connection.row_factory = aiosqlite.Row

        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS crawled_pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                title TEXT,
                text TEXT,
                links TEXT NOT NULL DEFAULT '[]',
                metadata TEXT NOT NULL DEFAULT '{}',
                crawled_at TEXT,
                status_code INTEGER,
                content_type TEXT,
                UNIQUE(url, crawled_at)
            )
        """)

        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_crawled_pages_url
            ON crawled_pages(url)
        """)

        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_crawled_pages_crawled_at
            ON crawled_pages(crawled_at)
        """)

        await self._connection.commit()

    async def save(self, data: dict[str, Any]) -> None:
        """Buffer a record and flush when batch_size is reached."""
        if self._closed:
            raise RuntimeError("Storage is closed")

        async with self._lock:
            if self._connection is None:
                await self.init_db()

            self._buffer.append(data.copy())

            if len(self._buffer) >= self.batch_size:
                await self._flush_locked()

    async def _flush_locked(self) -> None:
        """Write buffered records in one transaction. Caller holds the lock."""
        if not self._buffer:
            return

        if self._connection is None:
            await self.init_db()

        records = self._buffer.copy()

        rows = [
            (
                item["url"],
                item.get("title"),
                item.get("text"),
                json.dumps(item.get("links", []), ensure_ascii=False, default=str),
                json.dumps(item.get("metadata", {}), ensure_ascii=False, default=str),
                str(item["crawled_at"]) if item.get("crawled_at") is not None else None,
                item.get("status_code"),
                item.get("content_type"),
            )
            for item in records
        ]

        try:
            await self._connection.executemany("""
                INSERT INTO crawled_pages (
                    url, title, text, links, metadata,
                    crawled_at, status_code, content_type
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(url, crawled_at) DO UPDATE SET
                    title = excluded.title,
                    text = excluded.text,
                    links = excluded.links,
                    metadata = excluded.metadata,
                    status_code = excluded.status_code,
                    content_type = excluded.content_type
            """, rows)

            await self._connection.commit()
            del self._buffer[:len(records)]

        except Exception:
            await self._connection.rollback()
            logger.exception("Failed to flush SQLite batch")
            raise

    async def flush(self) -> None:
        """Write all buffered records."""
        async with self._lock:
            await self._flush_locked()

    async def fetch_all(self) -> list[dict[str, Any]]:
        """Read all saved records as dictionaries."""
        await self.flush()

        if self._connection is None:
            await self.init_db()

        cursor = await self._connection.execute("""
            SELECT * FROM crawled_pages ORDER BY id
        """)
        rows = await cursor.fetchall()
        await cursor.close()

        result = []
        for row in rows:
            item = dict(row)
            item["links"] = json.loads(item["links"])
            item["metadata"] = json.loads(item["metadata"])
            result.append(item)

        return result

    async def close(self) -> None:
        """Flush buffered records and close the database connection."""
        if self._closed:
            return

        async with self._lock:
            try:
                await self._flush_locked()
            finally:
                if self._connection is not None:
                    await self._connection.close()
                    self._connection = None
                self._closed = True
