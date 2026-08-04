from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .models import Job, JobStatus


class JobEngine:
    def run(self, job: Job, handler: Callable[[dict[str, Any]], dict[str, Any]]) -> Job:
        job.status = JobStatus.RUNNING
        try:
            job.result = handler(job.payload)
            job.status = JobStatus.SUCCEEDED
        except Exception as exc:  # noqa: BLE001 - boundary converts failures to state
            job.error = str(exc)
            job.status = JobStatus.FAILED
        return job
