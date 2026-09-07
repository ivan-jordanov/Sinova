"""
In-memory job manager for preprocessing tasks.

Tracks the state, progress, and configuration of asynchronous
preprocessing jobs. Uses simple in-memory storage.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal
from uuid import uuid4

from app.schemas.preprocessing import PreprocessingConfiguration


JobStatus = Literal["queued", "running", "completed", "failed", "cancelled"]


@dataclass
class ProcessingJob:
    """Represents a single preprocessing job."""

    id: str
    status: JobStatus
    configuration: PreprocessingConfiguration
    created_at: datetime
    progress: int = 0  # 0-100
    message: str = ""
    current_operation: str | None = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "status": self.status,
            "progress": self.progress,
            "message": self.message,
            "current_operation": self.current_operation,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
        }


class JobManager:
    """
    Manages preprocessing jobs in memory.

    Stores jobs, allows querying status, and tracks progress.
    This is suitable for a single-instance deployment.
    For distributed systems, replace with a database backend.
    """

    def __init__(self):
        """Initialize the job manager."""
        self.jobs: dict[str, ProcessingJob] = {}

    def create_job(self, configuration: PreprocessingConfiguration) -> str:
        """
        Create a new preprocessing job.

        Args:
            configuration: The preprocessing operations to apply

        Returns:
            Job ID (UUID string)
        """
        job_id = str(uuid4())
        job = ProcessingJob(
            id=job_id,
            status="queued",
            configuration=configuration,
            created_at=datetime.utcnow(),
            message="Job queued, waiting to start",
        )
        self.jobs[job_id] = job
        return job_id

    def get_job(self, job_id: str) -> ProcessingJob | None:
        """
        Retrieve a job by ID.

        Args:
            job_id: The job ID to look up

        Returns:
            ProcessingJob if found, None otherwise
        """
        return self.jobs.get(job_id)

    def start_job(self, job_id: str) -> ProcessingJob | None:
        """
        Mark a job as running.

        Args:
            job_id: The job to start

        Returns:
            Updated ProcessingJob if found, None otherwise
        """
        job = self.jobs.get(job_id)
        if job:
            job.status = "running"
            job.started_at = datetime.utcnow()
            job.message = "Processing started"
        return job

    def update_progress(
        self,
        job_id: str,
        progress: int,
        message: str = "",
        current_operation: str | None = None,
    ) -> ProcessingJob | None:
        """
        Update a job's progress.

        Args:
            job_id: The job to update
            progress: Progress percentage (0-100)
            message: Status message to display
            current_operation: Name of operation currently running

        Returns:
            Updated ProcessingJob if found, None otherwise
        """
        job = self.jobs.get(job_id)
        if job:
            job.progress = max(0, min(100, progress))  # Clamp to 0-100
            job.message = message
            if current_operation:
                job.current_operation = current_operation
        return job

    def complete_job(self, job_id: str, message: str = "Processing complete") -> ProcessingJob | None:
        """
        Mark a job as successfully completed.

        Args:
            job_id: The job to complete
            message: Final status message

        Returns:
            Updated ProcessingJob if found, None otherwise
        """
        job = self.jobs.get(job_id)
        if job:
            job.status = "completed"
            job.progress = 100
            job.message = message
            job.completed_at = datetime.utcnow()
        return job

    def fail_job(self, job_id: str, error: str) -> ProcessingJob | None:
        """
        Mark a job as failed.

        Args:
            job_id: The job that failed
            error: Error message describing what went wrong

        Returns:
            Updated ProcessingJob if found, None otherwise
        """
        job = self.jobs.get(job_id)
        if job:
            job.status = "failed"
            job.message = "Processing failed"
            job.error = error
            job.completed_at = datetime.utcnow()
        return job

    def cancel_job(self, job_id: str) -> ProcessingJob | None:
        """
        Mark a job as cancelled by user.

        Args:
            job_id: The job to cancel

        Returns:
            Updated ProcessingJob if found, None otherwise
        """
        job = self.jobs.get(job_id)
        if job and job.status in ("queued", "running"):
            job.status = "cancelled"
            job.message = "Job cancelled by user"
            job.completed_at = datetime.utcnow()
        return job


# Global job manager instance
# In production, this would be replaced with a database or distributed backend
_job_manager = JobManager()


def get_job_manager() -> JobManager:
    """Get the global job manager instance."""
    return _job_manager
