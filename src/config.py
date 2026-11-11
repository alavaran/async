
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CrawlerConfig:
    # Настройки crawler
    max_concurrent: int = 5
    max_per_domain: int = 3
    requests_per_second: float = 1.0

    respect_robots: bool = True
    min_delay: float = 0.5
    jitter: float = 0.0

    max_retries: int = 3
    connect_timeout: float = 10.0
    read_timeout: float = 10.0
    total_timeout: float = 20.0
    backoff_base: float = 1.0

    user_agent: str = "MyBot/1.0"

    # Настройки обхода
    start_urls: list[str] = field(default_factory=list)
    sitemap_urls: list[str] = field(default_factory=list)
    max_pages: int = 100
    max_depth: int = 2
    same_domain_only: bool = True

    include_patterns: list[str] = field(default_factory=list)
    exclude_patterns: list[str] = field(default_factory=list)

    # Настройки хранилища
    storage: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_file(cls, file_path: str | Path) -> "CrawlerConfig":
        """Загружает конфигурацию из JSON или YAML."""
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Config file not found: {path}"
            )

        suffix = path.suffix.lower()

        with path.open("r", encoding="utf-8") as file:
            if suffix == ".json":
                data = json.load(file)

            elif suffix in (".yaml", ".yml"):
                try:
                    import yaml
                except ImportError as exc:
                    raise ImportError(
                        "PyYAML is required to load YAML configs. "
                        "Install it with: pip install pyyaml"
                    ) from exc

                data = yaml.safe_load(file)

            else:
                raise ValueError(
                    f"Unsupported config format: {suffix}"
                )

        if not isinstance(data, dict):
            raise TypeError(
                "Config file must contain a dictionary/object"
            )

        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict) -> "CrawlerConfig":
        """Создаёт конфигурацию из словаря."""
        if not isinstance(data, dict):
            raise TypeError("Config data must be a dictionary")

        allowed_fields = cls.__dataclass_fields__.keys()
        unknown_fields = set(data) - set(allowed_fields)

        if unknown_fields:
            raise ValueError(
                f"Unknown config fields: {sorted(unknown_fields)}"
            )

        config = cls(**data)
        config.validate()

        return config

    def validate(self) -> None:
        """Проверяет корректность настроек."""
        if self.max_concurrent < 1:
            raise ValueError("max_concurrent must be >= 1")

        if self.max_per_domain < 1:
            raise ValueError("max_per_domain must be >= 1")

        if self.requests_per_second <= 0:
            raise ValueError("requests_per_second must be > 0")

        if self.max_retries < 0:
            raise ValueError("max_retries must be >= 0")

        if self.max_pages < 1:
            raise ValueError("max_pages must be >= 1")

        if self.max_depth < 0:
            raise ValueError("max_depth must be >= 0")

        if self.min_delay < 0 or self.jitter < 0:
            raise ValueError("min_delay and jitter must be >= 0")
        
        if not isinstance(self.start_urls, list):
            raise ValueError(  # noqa: TRY004
                "start_urls must be a list"
            )

        if not all(isinstance(url, str) for url in self.start_urls):
            raise TypeError("All start_urls must be strings")

        if not isinstance(self.sitemap_urls, list):
            raise TypeError("sitemap_urls must be a list")

        if not all(isinstance(url, str) for url in self.sitemap_urls):
            raise TypeError("All sitemap_urls must be strings")

        if not isinstance(self.storage, dict):
            raise TypeError("storage must be a dictionary")
