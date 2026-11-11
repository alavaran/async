
import time
import unittest

from src.monitor import CrawlerMonitor


class TestCrawlerMonitor(unittest.TestCase):

    def test_initial_state(self):
        monitor = CrawlerMonitor(total=100)

        progress = monitor.get_progress()

        self.assertEqual(progress["completed"], 0)
        self.assertEqual(progress["total"], 100)
        self.assertEqual(progress["progress_percent"], 0)
        self.assertEqual(progress["active_tasks"], 0)

    def test_task_started(self):
        monitor = CrawlerMonitor(total=10)

        monitor.task_started()
        monitor.task_started()

        self.assertEqual(
            monitor.get_progress()["active_tasks"],
            2,
        )

    def test_task_finished(self):
        monitor = CrawlerMonitor(total=10)

        monitor.task_started()
        monitor.task_finished()

        progress = monitor.get_progress()

        self.assertEqual(progress["completed"], 1)
        self.assertEqual(progress["active_tasks"], 0)

    def test_progress_percentage(self):
        monitor = CrawlerMonitor(total=10)

        for _ in range(5):
            monitor.task_finished()

        self.assertEqual(
            monitor.get_progress()["progress_percent"],
            50,
        )

    def test_progress_does_not_exceed_100(self):
        monitor = CrawlerMonitor(total=2)

        for _ in range(3):
            monitor.task_finished()

        self.assertEqual(
            monitor.get_progress()["progress_percent"],
            100,
        )

    def test_zero_total(self):
        monitor = CrawlerMonitor(total=0)

        progress = monitor.get_progress()

        self.assertEqual(progress["progress_percent"], 100)
        self.assertIsNone(progress["eta_seconds"])

    def test_speed_and_eta(self):
        monitor = CrawlerMonitor(total=100)

        monitor.started_at = time.monotonic() - 10

        for _ in range(20):
            monitor.task_finished()

        progress = monitor.get_progress()

        self.assertAlmostEqual(
            progress["pages_per_second"],
            2,
            delta=0.1,
        )

        self.assertAlmostEqual(
            progress["eta_seconds"],
            40,
            delta=2,
        )


if __name__ == "__main__":
    unittest.main()
