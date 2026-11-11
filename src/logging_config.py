
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(
    log_file: str = "logs/crawler.log",
    level: int = logging.INFO,
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 3,
) -> None:
    """Настраивает логирование в консоль и файл с ротацией."""

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        filename=log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Удаляем предыдущие обработчики, чтобы не дублировать сообщения.
    for handler in root_logger.handlers[:]:
        handler.close()
        root_logger.removeHandler(handler)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
