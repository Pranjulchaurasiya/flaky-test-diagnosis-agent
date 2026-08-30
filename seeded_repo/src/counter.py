import time
import threading

class AsyncMetricsCounter:
    """
    In-memory counter accessed by multiple concurrent worker threads.
    Flake Cause: Unprotected dict mutation without threading.Lock causes race condition.
    """
    def __init__(self):
        self._counts = {}

    def increment(self, metric: str, amount: int = 1):
        # Intentional race condition: read-modify-write without lock
        current = self._counts.get(metric, 0)
        time.sleep(0.0001)  # Context switch window
        self._counts[metric] = current + amount

    def get_count(self, metric: str) -> int:
        return self._counts.get(metric, 0)

    def reset(self):
        self._counts.clear()
