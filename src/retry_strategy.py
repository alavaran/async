import asyncio
import logging
import time
import json
import inspect

from collections import defaultdict
from typing import Callable, Coroutine, Any
from src.exceptions import (
    CrawlerError,
    TransientError,
    PermanentError,
    NetworkError,
)

logger = logging.getLogger(__name__)


class RetryStrategy:
    def __init__(
        self,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        retry_on: list[type[Exception]] | None = None,
    ):
        if max_retries < 0:
            raise ValueError("max_retries must be >= 0")

        if backoff_factor < 0:
            raise ValueError("backoff_factor must be >= 0")

        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.retry_on = tuple(
            retry_on if retry_on is not None
            else [TransientError, NetworkError]
        )

        self.errors_by_type: dict[str, int] = defaultdict(int)
        self.successful_retries = 0
        self.retry_times: list[float] = []
        self.permanent_errors: list[dict[str, str]] = []

    async def execute_with_retry(
        self,
        coro: Callable[..., Coroutine[Any, Any, Any]],
        *args,
        **kwargs,
    ) -> Any:
        """Execute an async function with exponential backoff."""
        signature = inspect.signature(coro)
        accepts_retry_attempt = (
            "_retry_attempt" in signature.parameters
            or any(
                parameter.kind == inspect.Parameter.VAR_KEYWORD
                for parameter in signature.parameters.values()
            )
        )

        for attempt in range(self.max_retries + 1):
            try:
                call_kwargs = kwargs.copy()

                if accepts_retry_attempt:
                    call_kwargs["_retry_attempt"] = attempt

                result = await coro(*args, **call_kwargs)

                if attempt > 0:
                    self.successful_retries += 1
                    logger.info(
                        "Retry succeeded on attempt %s",
                        attempt + 1,
                    )

                return result

            except PermanentError as exc:
                self.errors_by_type[type(exc).__name__] += 1

                url = str(
                    kwargs.get("url", args[0] if args else "unknown")
                )
                self.permanent_errors.append({
                    "url": url,
                    "error": str(exc),
                })

                logger.warning(
                    "Permanent error for %s: %s",
                    url,
                    exc,
                )
                raise

            except Exception as exc:
                error_type = type(exc).__name__
                self.errors_by_type[error_type] += 1

                should_retry = isinstance(exc, self.retry_on)
                is_last_attempt = attempt >= self.max_retries

                if not should_retry or is_last_attempt:
                    logger.error(
                        "Giving up after attempt %s: %s",
                        attempt + 1,
                        exc,
                    )
                    raise

                delay = self.backoff_factor * (2 ** attempt)

                logger.warning(
                    "Attempt %s failed (%s). Retrying in %.2f seconds",
                    attempt + 1,
                    error_type,
                    delay,
                )

                retry_start = time.monotonic()
                await asyncio.sleep(delay)
                actual_delay = time.monotonic() - retry_start
                self.retry_times.append(actual_delay)

        raise RuntimeError("Retry loop ended unexpectedly")


    def get_stats(self) -> dict:
        """Return retry and error statistics."""
        return {
            "errors_by_type": dict(self.errors_by_type),
            "successful_retries": self.successful_retries,
            "average_retry_delay_seconds": (
                sum(self.retry_times) / len(self.retry_times)
                if self.retry_times else 0.0
            ),
            "permanent_error_urls": list(self.permanent_errors),
        }

    def save_error_report(self, filepath: str = "error_report.json") -> None:
        """Save retry and error statistics to a JSON file."""
        report = self.get_stats()

        with open(filepath, "w", encoding="utf-8") as file:
            json.dump(
                report,
                file,
                ensure_ascii=False,
                indent=4,
            )

        logger.info("Error report saved to %s", filepath)