import threading
import pytest
from counter import AsyncMetricsCounter

def test_concurrent_metric_increments():
    """
    Test Case 01: Race Condition
    Taxonomy: race_condition
    Description: 10 threads incrementing the counter 10 times concurrently.
    Without a mutex lock around dict read-modify-write, threads clobber each other's increments.
    """
    counter = AsyncMetricsCounter()
    threads = []
    num_threads = 10
    increments_per_thread = 10

    def _worker():
        for _ in range(increments_per_thread):
            counter.increment("api_requests", 1)

    for _ in range(num_threads):
        t = threading.Thread(target=_worker)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    expected = num_threads * increments_per_thread
    actual = counter.get_count("api_requests")
    assert actual == expected, f"Race condition detected! Expected {expected} increments, got {actual}"
