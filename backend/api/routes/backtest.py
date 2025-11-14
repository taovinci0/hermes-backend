"""Backtest API endpoints."""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional, List
from datetime import date
from pydantic import BaseModel

from ..services.backtest_service import BacktestService

router = APIRouter()
backtest_service = BacktestService()


class BacktestRequest(BaseModel):
    """Request model for starting a backtest."""
    start_date: str  # YYYY-MM-DD
    end_date: str  # YYYY-MM-DD
    stations: List[str]
    bankroll_usd: Optional[float] = None
    edge_min: Optional[float] = None
    fee_bp: Optional[int] = None
    slippage_bp: Optional[int] = None


@router.post("/run")
async def run_backtest(request: BacktestRequest):
    """Start a backtest job.
    
    Returns immediately with a job ID. Use the status endpoint
    to check progress and results endpoint to get results.
    """
    try:
        start_date = date.fromisoformat(request.start_date)
        end_date = date.fromisoformat(request.end_date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="Start date must be before end date")
    
    if not request.stations:
        raise HTTPException(status_code=400, detail="At least one station is required")
    
    job_id = await backtest_service.start_backtest(
        start_date=start_date,
        end_date=end_date,
        stations=request.stations,
        bankroll_usd=request.bankroll_usd,
        edge_min=request.edge_min,
        fee_bp=request.fee_bp,
        slippage_bp=request.slippage_bp,
    )
    
    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Backtest job started",
    }


@router.get("/status/{job_id}")
async def get_backtest_status(job_id: str):
    """Get backtest job status.
    
    Returns current status, progress, and metadata.
    """
    status = await backtest_service.get_job_status(job_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return status


@router.get("/results/{job_id}")
async def get_backtest_results(job_id: str):
    """Get backtest results.
    
    Returns results if job is completed, otherwise returns status.
    """
    results = await backtest_service.get_job_results(job_id)
    
    if not results:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return results


@router.get("/jobs")
async def list_backtest_jobs(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, description="Maximum number of jobs"),
):
    """List backtest jobs.
    
    Returns list of jobs with optional status filtering.
    """
    from ..utils.job_queue import JobStatus, job_queue
    
    status_filter = None
    if status:
        try:
            status_filter = JobStatus(status.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    jobs = await job_queue.list_jobs(
        job_type="backtest",
        status=status_filter,
        limit=limit,
    )
    
    return {
        "jobs": [
            {
                "job_id": job.job_id,
                "status": job.status.value,
                "created_at": job.created_at.isoformat(),
                "metadata": job.metadata,
            }
            for job in jobs
        ],
        "count": len(jobs),
    }

