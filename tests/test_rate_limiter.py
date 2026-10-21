
import asyncio
import time
import unittest

from src.rate_limiter import RateLimiter


class TestRateLimiter(unittest.IsolatedAsyncioTestCase):
    async def test_same_domain_is_limited(self):
        limiter = RateLimiter(requests_per_second=10)
        timestamps = []

        for _ in range(3):
            await limiter.acquire("example.com")
            timestamps.append(time.monotonic())

        intervals = [
            timestamps[i] - timestamps[i - 1]
            for i in range(1, len(timestamps))
        ]

        for interval in intervals:
            self.assertGreaterEqual(interval, 0.09)

    async def test_different_domains_have_separate_limits(self):
        limiter = RateLimiter(requests_per_second=5)

        await limiter.acquire("example.com")
        started = time.monotonic()

        await limiter.acquire("other.com")

        elapsed = time.monotonic() - started
        self.assertLess(elapsed, 0.1)

    async def test_global_limit(self):
        limiter = RateLimiter(
            requests_per_second=10,
            per_domain=False,
        )

        await limiter.acquire("example.com")
        started = time.monotonic()

        await limiter.acquire("other.com")

        elapsed = time.monotonic() - started
        self.assertGreaterEqual(elapsed, 0.09)

    async def test_invalid_rate(self):
        with self.assertRaises(ValueError):
            RateLimiter(requests_per_second=0)


if __name__ == "__main__":
    unittest.main()
