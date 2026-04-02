"""In-process queue manager with retry and dead-letter support."""
from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Callable

from .models import EventLog, Job, JobStatus, QueueName

logger = logging.getLogger(__name__)

JobHandler = Callable[[Job], dict[str, Any]]


class QueueManager:
    """Simple in-process queue with retry logic and DLQ.

    For production, swap the internal deque for Celery/Dramatiq/Arq.
    """

    def __init__(self) -> None:
        self._queues: dict[QueueName, list[Job]] = defaultdict(list)
        self._handlers: dict[str, JobHandler] = {}
        self._event_log: list[EventLog] = []

    def register_handler(self, job_type: str, handler: JobHandler) -> None:
        self._handlers[job_type] = handler

    def enqueue(self, job: Job) -> None:
        self._queues[job.queue].append(job)
        self._log(job.event_id, "unknown", job.job_id, "queued", f"queue={job.queue.value}")

    def process_next(self, queue: QueueName = QueueName.INGEST) -> Job | None:
        """Pop and process the next job from the given queue."""
        q = self._queues[queue]
        if not q:
            return None

        job = q.pop(0)
        handler = self._handlers.get(job.job_type)

        if handler is None:
            job.status = JobStatus.FAILED
            job.error = f"No handler for job_type={job.job_type}"
            self._send_to_dlq(job)
            return job

        job.status = JobStatus.PROCESSING
        try:
            handler(job)
            job.status = JobStatus.COMPLETED
            self._log(job.event_id, "unknown", job.job_id, "completed")
        except Exception as exc:
            job.retry_count += 1
            job.error = str(exc)
            if job.retry_count >= job.max_retries:
                self._send_to_dlq(job)
            else:
                job.status = JobStatus.QUEUED
                job.queue = QueueName.RETRY
                self._queues[QueueName.RETRY].append(job)
                self._log(
                    job.event_id, "unknown", job.job_id, "retry",
                    f"attempt={job.retry_count}",
                )

        return job

    def process_all(self, queue: QueueName = QueueName.INGEST) -> list[Job]:
        """Drain and process all jobs from a queue."""
        results: list[Job] = []
        while self._queues[queue]:
            job = self.process_next(queue)
            if job:
                results.append(job)
        return results

    def drain_retries(self) -> list[Job]:
        """Process everything in the retry queue."""
        return self.process_all(QueueName.RETRY)

    def get_dead_letters(self) -> list[Job]:
        return list(self._queues[QueueName.DEAD_LETTER])

    def get_event_log(self) -> list[EventLog]:
        return list(self._event_log)

    def queue_depth(self, queue: QueueName) -> int:
        return len(self._queues[queue])

    # ── Internal ───────────────────────────────────────────────────────

    def _send_to_dlq(self, job: Job) -> None:
        job.status = JobStatus.DEAD_LETTER
        job.queue = QueueName.DEAD_LETTER
        self._queues[QueueName.DEAD_LETTER].append(job)
        self._log(job.event_id, "unknown", job.job_id, "dead_letter", job.error)
        logger.warning("Job %s sent to DLQ: %s", job.job_id, job.error)

    def _log(
        self,
        event_id: str,
        event_type: str,
        job_id: str,
        status: str,
        detail: str = "",
    ) -> None:
        self._event_log.append(
            EventLog(
                event_id=event_id,
                event_type=event_type,
                job_id=job_id,
                status=status,
                detail=detail,
            )
        )
