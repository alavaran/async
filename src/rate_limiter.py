
import asyncio
import time


class RateLimiter:
    def __init__(
        self,
        requests_per_second: float = 1.0,
        per_domain: bool = True,
    ):
        if requests_per_second <= 0:
            raise ValueError("requests_per_second must be positive")

        self.interval = 1.0 / requests_per_second
        self.per_domain = per_domain

        self._locks = {}
        self._last_request = {}
        self._state_lock = asyncio.Lock()

    async def acquire(self, domain: str = None) -> None:
        key = domain if self.per_domain else "global"

        async with self._state_lock:
            if key not in self._locks:
                self._locks[key] = asyncio.Lock()

            lock = self._locks[key]

        async with lock:
            now = time.monotonic()
            last_request = self._last_request.get(key)

            if last_request is not None:
                wait_time = self.interval - (now - last_request)

                if wait_time > 0:
                    await asyncio.sleep(wait_time)

            self._last_request[key] = time.monotonic()
