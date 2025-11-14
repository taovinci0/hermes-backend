"""Snapshot endpoints."""

from fastapi import APIRouter, Query
from typing import Optional
from datetime import date

from ..services.snapshot_service import SnapshotService
from ..models.schemas import SnapshotListResponse

router = APIRouter()
snapshot_service = SnapshotService()


@router.get("/zeus", response_model=SnapshotListResponse)
async def get_zeus_snapshots(
    station_code: str = Query(..., description="Station code (e.g., EGLC)"),
    event_day: Optional[str] = Query(None, description="Event day (YYYY-MM-DD)"),
    limit: Optional[int] = Query(100, description="Maximum number of snapshots"),
):
    """Get Zeus forecast snapshots."""
    event_date = None
    if event_day:
        try:
            event_date = date.fromisoformat(event_day)
        except ValueError:
            pass
    
    snapshots = snapshot_service.get_zeus_snapshots(
        station_code=station_code,
        event_day=event_date,
        limit=limit,
    )
    
    return SnapshotListResponse(
        snapshots=snapshots,
        count=len(snapshots),
    )


@router.get("/polymarket", response_model=SnapshotListResponse)
async def get_polymarket_snapshots(
    city: str = Query(..., description="City name (e.g., London)"),
    event_day: Optional[str] = Query(None, description="Event day (YYYY-MM-DD)"),
    limit: Optional[int] = Query(100, description="Maximum number of snapshots"),
):
    """Get Polymarket pricing snapshots."""
    event_date = None
    if event_day:
        try:
            event_date = date.fromisoformat(event_day)
        except ValueError:
            pass
    
    snapshots = snapshot_service.get_polymarket_snapshots(
        city=city,
        event_day=event_date,
        limit=limit,
    )
    
    return SnapshotListResponse(
        snapshots=snapshots,
        count=len(snapshots),
    )


@router.get("/decisions", response_model=SnapshotListResponse)
async def get_decision_snapshots(
    station_code: str = Query(..., description="Station code (e.g., EGLC)"),
    event_day: Optional[str] = Query(None, description="Event day (YYYY-MM-DD)"),
    limit: Optional[int] = Query(100, description="Maximum number of snapshots"),
):
    """Get decision snapshots."""
    event_date = None
    if event_day:
        try:
            event_date = date.fromisoformat(event_day)
        except ValueError:
            pass
    
    snapshots = snapshot_service.get_decision_snapshots(
        station_code=station_code,
        event_day=event_date,
        limit=limit,
    )
    
    return SnapshotListResponse(
        snapshots=snapshots,
        count=len(snapshots),
    )


@router.get("/metar", response_model=SnapshotListResponse)
async def get_metar_snapshots(
    station_code: str = Query(..., description="Station code (e.g., EGLC)"),
    event_day: Optional[str] = Query(None, description="Event day (YYYY-MM-DD)"),
):
    """Get METAR observation snapshots."""
    event_date = None
    if event_day:
        try:
            event_date = date.fromisoformat(event_day)
        except ValueError:
            pass
    
    snapshots = snapshot_service.get_metar_snapshots(
        station_code=station_code,
        event_day=event_date,
    )
    
    return SnapshotListResponse(
        snapshots=snapshots,
        count=len(snapshots),
    )

