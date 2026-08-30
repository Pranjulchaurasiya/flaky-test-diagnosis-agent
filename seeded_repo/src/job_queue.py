import time
import threading
import random

class BackgroundJobRunner:
    """
    Asynchronous job worker.
    Flake Cause: Job takes variable execution duration (30ms - 90ms); hardcoded test sleep (50ms) flakes.
    """
    def __init__(self):
        self.completed_jobs = set()

    def submit_job(self, job_id: str):
        def _worker():
            # Variable execution latency
            duration = 0.04 + (0.05 * random.random())
            time.sleep(duration)
            self.completed_jobs.add(job_id)

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    def is_finished(self, job_id: str) -> bool:
        return job_id in self.completed_jobs
