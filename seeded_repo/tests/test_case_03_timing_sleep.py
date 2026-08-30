import time
import pytest
from job_queue import BackgroundJobRunner

def test_async_job_completion():
    """
    Test Case 03: Timing / Hardcoded Sleep Assumption
    Taxonomy: timing_sleep_assumption
    Description: Job runner worker finishes in 40-90ms. Hardcoded sleep(0.05) fails when worker takes >50ms.
    """
    runner = BackgroundJobRunner()
    job_id = "job_export_999"
    runner.submit_job(job_id)

    # Flaky timing assumption: sleep for a fixed duration hoping background job completes
    time.sleep(0.05)

    assert runner.is_finished(job_id), (
        f"Timing flake! Job {job_id} was expected to be finished within 50ms, but was still running."
    )
