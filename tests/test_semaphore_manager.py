
import asyncio
import unittest

from src.semaphore_manager import SemaphoreManager


class TestSemaphoreManager(unittest.IsolatedAsyncioTestCase):
    async def test_active_tasks_count(self):
        manager = SemaphoreManager(max_concurrent=2, max_per_domain=1)

        await manager.acquire("example.com")
        self.assertEqual(manager.active_tasks, 1)

        manager.release("example.com")
        self.assertEqual(manager.active_tasks, 0)

    async def test_global_limit(self):
        manager = SemaphoreManager(max_concurrent=1, max_per_domain=2)

        await manager.acquire("example.com")

        acquired = False

        async def second_task():
            nonlocal acquired
            await manager.acquire("other.com")
            acquired = True
            manager.release("other.com")

        task = asyncio.create_task(second_task())
        await asyncio.sleep(0.05)

        self.assertFalse(acquired)

        manager.release("example.com")
        await task

        self.assertTrue(acquired)


if __name__ == "__main__":
    unittest.main()
