"""Simple job queue for background task execution."""

import uuid
import asyncio
from enum import Enum
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field


class JobStatus(str, Enum):
    """Job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Job:
    """A background job."""
    
    job_id: str
    job_type: str
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    progress: float = 0.0  # 0.0 to 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class JobQueue:
    """Simple in-memory job queue for background tasks."""
    
    def __init__(self):
        """Initialize job queue."""
        self.jobs: Dict[str, Job] = {}
        self._lock = asyncio.Lock()
    
    async def create_job(
        self,
        job_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a new job.
        
        Args:
            job_type: Type of job (e.g., "backtest")
            metadata: Optional job metadata
            
        Returns:
            Job ID
        """
        job_id = str(uuid.uuid4())
        job = Job(
            job_id=job_id,
            job_type=job_type,
            metadata=metadata or {},
        )
        
        async with self._lock:
            self.jobs[job_id] = job
        
        return job_id
    
    async def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job object or None if not found
        """
        async with self._lock:
            return self.jobs.get(job_id)
    
    async def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        error: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None,
        progress: Optional[float] = None,
    ):
        """Update job status.
        
        Args:
            job_id: Job ID
            status: New status
            error: Error message if failed
            result: Result data if completed
            progress: Progress (0.0 to 1.0)
        """
        async with self._lock:
            if job_id not in self.jobs:
                return
            
            job = self.jobs[job_id]
            job.status = status
            
            if status == JobStatus.RUNNING and not job.started_at:
                job.started_at = datetime.utcnow()
            elif status in (JobStatus.COMPLETED, JobStatus.FAILED):
                job.completed_at = datetime.utcnow()
            
            if error:
                job.error = error
            if result:
                job.result = result
            if progress is not None:
                job.progress = max(0.0, min(1.0, progress))
    
    async def run_job(
        self,
        job_id: str,
        task: Callable,
        *args,
        **kwargs,
    ):
        """Run a job in the background.
        
        Args:
            job_id: Job ID
            task: Task function to execute
            *args: Positional arguments for task
            **kwargs: Keyword arguments for task
        """
        await self.update_job_status(job_id, JobStatus.RUNNING)
        
        try:
            # Run task (can be sync or async)
            if asyncio.iscoroutinefunction(task):
                result = await task(*args, **kwargs)
            else:
                # Run sync function in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, lambda: task(*args, **kwargs))
            
            await self.update_job_status(
                job_id,
                JobStatus.COMPLETED,
                result=result if isinstance(result, dict) else {"output": result},
            )
        except Exception as e:
            await self.update_job_status(
                job_id,
                JobStatus.FAILED,
                error=str(e),
            )
            raise
    
    async def list_jobs(
        self,
        job_type: Optional[str] = None,
        status: Optional[JobStatus] = None,
        limit: int = 100,
    ) -> list[Job]:
        """List jobs with optional filtering.
        
        Args:
            job_type: Filter by job type
            status: Filter by status
            limit: Maximum number of jobs to return
            
        Returns:
            List of jobs
        """
        async with self._lock:
            jobs = list(self.jobs.values())
        
        # Apply filters
        if job_type:
            jobs = [j for j in jobs if j.job_type == job_type]
        if status:
            jobs = [j for j in jobs if j.status == status]
        
        # Sort by created_at descending (newest first)
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        
        return jobs[:limit]
    
    async def cleanup_old_jobs(self, days: int = 7):
        """Remove old completed/failed jobs.
        
        Args:
            days: Remove jobs older than this many days
        """
        cutoff = datetime.utcnow().timestamp() - (days * 24 * 60 * 60)
        
        async with self._lock:
            to_remove = [
                job_id
                for job_id, job in self.jobs.items()
                if job.status in (JobStatus.COMPLETED, JobStatus.FAILED)
                and job.completed_at
                and job.completed_at.timestamp() < cutoff
            ]
            
            for job_id in to_remove:
                del self.jobs[job_id]


# Global job queue instance
job_queue = JobQueue()

