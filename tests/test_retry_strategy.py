import unittest
import json
import os
import tempfile

from unittest.mock import AsyncMock, patch
from src.retry_strategy import RetryStrategy
from src.exceptions import TransientError, PermanentError, NetworkError

class TestRetryStrategy(unittest.IsolatedAsyncioTestCase):
    async def test_retries_then_succeeds(self):
        strategy = RetryStrategy(max_retries=2, backoff_factor=0)
        calls = 0

        async def request():
            nonlocal calls
            calls += 1
            if calls < 3:
                raise TransientError("Temporary failure")
            return "success"

        result = await strategy.execute_with_retry(request)

        self.assertEqual(result, "success")
        self.assertEqual(calls, 3)
        self.assertEqual(strategy.successful_retries, 1)

    async def test_permanent_error_is_not_retried(self):
        strategy = RetryStrategy(max_retries=3, backoff_factor=0)
        calls = 0

        async def request():
            nonlocal calls
            calls += 1
            raise PermanentError("Not found")

        with self.assertRaises(PermanentError):
            await strategy.execute_with_retry(request)

        self.assertEqual(calls, 1)

    async def test_exponential_backoff(self):
        strategy = RetryStrategy(
            max_retries=2,
            backoff_factor=2,
        )

        request = AsyncMock(
            side_effect=[
                TransientError("Temporary error"),
                TransientError("Temporary error"),
                "success",
            ]
        )

        with patch(
            "src.retry_strategy.asyncio.sleep",
            new_callable=AsyncMock,
        ) as mock_sleep:
            result = await strategy.execute_with_retry(request)

        self.assertEqual(result, "success")
        self.assertEqual(request.await_count, 3)
        self.assertEqual(mock_sleep.await_count, 2)

        delays = [
            call.args[0]
            for call in mock_sleep.await_args_list
        ]
        self.assertEqual(delays, [2, 4])

    async def test_network_error_is_retried(self):
        strategy = RetryStrategy(
            max_retries=2,
            backoff_factor=0,
        )
        operation = AsyncMock(
            side_effect=[
                NetworkError("Connection refused"),
                "success",
            ]
        )

        result = await strategy.execute_with_retry(operation)

        self.assertEqual(result, "success")
        self.assertEqual(operation.await_count, 2)
        self.assertEqual(strategy.successful_retries, 1)


    async def test_transient_error_is_retried(self):
        strategy = RetryStrategy(
            max_retries=2,
            backoff_factor=0,
        )
        operation = AsyncMock(
            side_effect=[
                TransientError("HTTP 503"),
                "success",
            ]
        )

        result = await strategy.execute_with_retry(operation)

        self.assertEqual(result, "success")
        self.assertEqual(operation.await_count, 2)


    async def test_permanent_error_is_not_retried(self):
        strategy = RetryStrategy(
            max_retries=3,
            backoff_factor=0,
        )
        operation = AsyncMock(
            side_effect=PermanentError("HTTP 404")
        )

        with self.assertRaises(PermanentError):
            await strategy.execute_with_retry(operation)

        self.assertEqual(operation.await_count, 1)
        self.assertEqual(strategy.successful_retries, 0)


    async def test_error_statistics(self):
        strategy = RetryStrategy(
            max_retries=1,
            backoff_factor=0,
        )
        operation = AsyncMock(
            side_effect=[
                TransientError("HTTP 503"),
                "success",
            ]
        )

        await strategy.execute_with_retry(operation)
        stats = strategy.get_stats()

        self.assertEqual(stats["errors_by_type"]["TransientError"], 1)
        self.assertEqual(stats["successful_retries"], 1)

    def test_save_error_report(self):
        strategy = RetryStrategy()

        strategy.errors_by_type["TransientError"] = 2
        strategy.successful_retries = 1
        strategy.permanent_errors.append({
            "url": "https://example.com/missing",
            "error": "HTTP 404",
        })

        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = os.path.join(temp_dir, "error_report.json")

            strategy.save_error_report(filepath)

            with open(filepath, encoding="utf-8") as file:
                report = json.load(file)

        self.assertEqual(
            report["errors_by_type"]["TransientError"], 2
        )
        self.assertEqual(report["successful_retries"], 1)
        self.assertEqual(
            report["permanent_error_urls"][0]["url"],
            "https://example.com/missing",
        )

    

if __name__ == "__main__":
    unittest.main()
