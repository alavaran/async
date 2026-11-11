
import time


class CrawlerMonitor:
    """Собирает показатели выполнения crawler."""

    def __init__(self, total: int):
        self.total = total
        self.started_at = time.monotonic()
        self.completed = 0
        self.active_tasks = 0

    def task_started(self) -> None:
        self.active_tasks += 1

    def task_finished(self) -> None:
        self.active_tasks = max(0, self.active_tasks - 1)
        self.completed += 1

    def get_progress(self) -> dict:
        elapsed = time.monotonic() - self.started_at

        speed = (
            self.completed / elapsed
            if elapsed > 0
            else 0
        )

        remaining = max(0, self.total - self.completed)

        eta = (
            remaining / speed
            if speed > 0
            else None
        )

        progress_percent = (
            min(self.completed / self.total * 100, 100)
            if self.total > 0
            else 100
        )

        return {
            "completed": self.completed,
            "total": self.total,
            "progress_percent": round(progress_percent, 2),
            "elapsed_seconds": round(elapsed, 2),
            "pages_per_second": round(speed, 2),
            "eta_seconds": round(eta, 2) if eta is not None else None,
            "active_tasks": self.active_tasks,
        }
