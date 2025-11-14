"""METAR endpoints."""

from fastapi import APIRouter, Query
from typing import Optional
from datetime import date

from ..services.metar_service import MetarService
from ..services.snapshot_service import SnapshotService

router = APIRouter()
metar_service = MetarService()
snapshot_service = SnapshotService()


@router.get("/observations")
async def get_metar_observations(
    station_code: str = Query(..., description="Station code (e.g., EGLC)"),
    event_day: Optional[str] = Query(None, description="Event day (YYYY-MM-DD)"),
):
    """Get METAR observations for a station.
    
    Returns all METAR observations from snapshots, sorted by observation time.
    """
    event_date = None
    if event_day:
        try:
            event_date = date.fromisoformat(event_day)
        except ValueError:
            pass
    
    observations = metar_service.get_observations(
        station_code=station_code,
        event_day=event_date,
    )
    
    return {
        "observations": observations,
        "count": len(observations),
    }


@router.get("/daily-high")
async def get_daily_high(
    station_code: str = Query(..., description="Station code (e.g., EGLC)"),
    event_day: Optional[str] = Query(None, description="Event day (YYYY-MM-DD)"),
):
    """Get daily high temperature from METAR observations.
    
    Returns the maximum temperature observed during the event day.
    """
    event_date = None
    if event_day:
        try:
            event_date = date.fromisoformat(event_day)
        except ValueError:
            pass
    
    daily_high = metar_service.get_daily_high(
        station_code=station_code,
        event_day=event_date,
    )
    
    if daily_high is None:
        return {
            "station_code": station_code,
            "event_day": event_date.isoformat() if event_date else date.today().isoformat(),
            "daily_high_f": None,
            "available": False,
        }
    
    return {
        "station_code": station_code,
        "event_day": event_date.isoformat() if event_date else date.today().isoformat(),
        "daily_high_f": daily_high,
        "available": True,
    }

