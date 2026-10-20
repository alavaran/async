
import asyncio
from collections import defaultdict


class SemaphoreManager:
    def __init__(
        self,
        max_concurrent: int = 10,
        max_per_domain: int = 3,
    ):
        self.global_semaphore = asyncio.Semaphore(max_concurrent)
        self.max_per_domain = max_per_domain
        self.domain_semaphores = defaultdict(
            lambda: asyncio.Semaphore(max_per_domain)
        )
        self.active_tasks = 0

    async def acquire(self, domain: str) -> None:
        await self.global_semaphore.acquire()
        try:
            await self.domain_semaphores[domain].acquire()
        except BaseException:
            self.global_semaphore.release()
            raise

        self.active_tasks += 1

    def release(self, domain: str) -> None:
        self.domain_semaphores[domain].release()
        self.global_semaphore.release()
        self.active_tasks -= 1
