"""Log endpoints."""

from fastapi import APIRouter, Query
from typing import Optional

from ..services.log_service import LogService

router = APIRouter()
log_service = LogService()


@router.get("/activity")
async def get_activity_logs(
    station_code: Optional[str] = Query(None, description="Filter by station code (e.g., EGLC)"),
    event_day: Optional[str] = Query(
        None,
        description="Filter by event day. Can be: YYYY-MM-DD, 'today', 'tomorrow', 'past_3_days', 'future'"
    ),
    action_type: Optional[str] = Query(
        None,
        description="Filter by action type: fetch, trade, decision, snapshot, cycle, error"
    ),
    log_level: Optional[str] = Query(
        None,
        description="Filter by log level: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    ),
    limit: Optional[int] = Query(100, description="Maximum number of log entries"),
    offset: int = Query(0, description="Number of entries to skip (for pagination)"),
):
    """Get filtered activity logs with pagination.
    
    Supports filtering by:
    - Station code (e.g., EGLC, KLGA)
    - Event day (specific date or special values: today, tomorrow, past_3_days, future)
    - Action type (fetch, trade, decision, snapshot, cycle, error)
    - Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns paginated results with total count and has_more flag.
    """
    result = log_service.get_activity_logs(
        station_code=station_code,
        event_day=event_day,
        action_type=action_type,
        log_level=log_level,
        limit=limit,
        offset=offset,
    )
    
    return result


@router.get("/available-dates")
async def get_available_dates():
    """Get list of dates that have log entries.
    
    Returns dates sorted descending (newest first).
    """
    dates = log_service.get_available_dates()
    
    return {
        "dates": dates,
        "count": len(dates),
    }

