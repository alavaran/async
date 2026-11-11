
import logging
import tempfile
import unittest
from pathlib import Path

from src.logging_config import setup_logging

logger = logging.getLogger(__name__)


class TestLoggingConfig(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_path = Path(self.temp_dir.name) / "crawler.log"

        self.root_logger = logging.getLogger()
        self.old_level = self.root_logger.level
        self.old_handlers = self.root_logger.handlers[:]

        for handler in self.root_logger.handlers[:]:
            self.root_logger.removeHandler(handler)
            handler.close()

    def tearDown(self):
        for handler in self.root_logger.handlers[:]:
            self.root_logger.removeHandler(handler)
            handler.close()

        for handler in self.old_handlers:
            self.root_logger.addHandler(handler)

        self.root_logger.setLevel(self.old_level)
        self.temp_dir.cleanup()

    def test_log_file_creation(self):
        """Создаётся файл логов."""
        setup_logging(log_file=str(self.log_path))

        logger.info("Test message")

        self.assertTrue(self.log_path.exists())

    def test_log_message_written_to_file(self):
        """Сообщение записывается в файл."""
        setup_logging(log_file=str(self.log_path))

        logger.info("Hello crawler")

        for handler in logging.getLogger().handlers:
            handler.flush()

        content = self.log_path.read_text(encoding="utf-8")

        self.assertIn("Hello crawler", content)

    def test_console_logging(self):
        """Проверяем наличие консольного обработчика."""
        setup_logging(log_file=str(self.log_path))

        handlers = logging.getLogger().handlers

        self.assertTrue(
            any(
                type(handler) is logging.StreamHandler
                for handler in handlers
            )
        )

    def test_log_level(self):
        """Настраивается уровень логирования."""
        setup_logging(
            log_file=str(self.log_path),
            level=logging.WARNING,
        )

        logger.info("Should not appear")
        logger.warning("Warning message")

        for handler in logging.getLogger().handlers:
            handler.flush()

        content = self.log_path.read_text(encoding="utf-8")

        self.assertNotIn("Should not appear", content)
        self.assertIn("Warning message", content)

    def test_log_rotation(self):
        """Проверяем ротацию при превышении размера файла."""
        setup_logging(
            log_file=str(self.log_path),
            max_bytes=100,
            backup_count=2,
        )

        for i in range(20):
            logger.warning("Log message number %s: %s", i, "x" * 50)

        for handler in logging.getLogger().handlers:
            handler.flush()

        rotated_file = Path(str(self.log_path) + ".1")

        self.assertTrue(rotated_file.exists())

    def test_log_directory_creation(self):
        """Автоматически создаётся директория для логов."""
        nested_path = (
            Path(self.temp_dir.name) / "nested" / "logs" / "crawler.log"
        )

        setup_logging(log_file=str(nested_path))

        logger.info("Directory test")

        self.assertTrue(nested_path.exists())


if __name__ == "__main__":
    unittest.main()
