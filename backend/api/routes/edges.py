"""Edge endpoints."""

from fastapi import APIRouter, Query
from typing import Optional
from datetime import date

from ..services.edge_service import EdgeService

router = APIRouter()
edge_service = EdgeService()


@router.get("/current")
async def get_current_edges(
    station_code: Optional[str] = Query(None, description="Station code filter (e.g., EGLC)"),
    event_day: Optional[str] = Query(None, description="Event day filter (YYYY-MM-DD)"),
    limit: Optional[int] = Query(100, description="Maximum number of edges"),
):
    """Get current edges from latest decision snapshots.
    
    Returns the most recent edges for each bracket, sorted by edge percentage.
    """
    event_date = None
    if event_day:
        try:
            event_date = date.fromisoformat(event_day)
        except ValueError:
            pass
    
    edges = edge_service.get_current_edges(
        station_code=station_code,
        event_day=event_date,
        limit=limit,
    )
    
    return {
        "edges": edges,
        "count": len(edges),
    }


@router.get("/summary")
async def get_edges_summary(
    station_code: Optional[str] = Query(None, description="Station code filter"),
    event_day: Optional[str] = Query(None, description="Event day filter (YYYY-MM-DD)"),
):
    """Get summary statistics for current edges."""
    event_date = None
    if event_day:
        try:
            event_date = date.fromisoformat(event_day)
        except ValueError:
            pass
    
    summary = edge_service.get_edges_summary(
        station_code=station_code,
        event_day=event_date,
    )
    
    return summary

