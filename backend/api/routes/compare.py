"""Comparison endpoints."""

from fastapi import APIRouter, Query
from typing import Optional
from datetime import date
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from core.feature_toggles import FeatureToggles

from ..services.metar_service import MetarService

router = APIRouter()
metar_service = MetarService()


@router.get("/zeus-vs-metar")
async def compare_zeus_vs_metar(
    station_code: str = Query(..., description="Station code (e.g., EGLC)"),
    event_day: Optional[str] = Query(None, description="Event day (YYYY-MM-DD)"),
):
    """Compare Zeus forecast vs METAR actual temperature.
    
    Compares the Zeus daily high prediction with the actual METAR daily high,
    calculating error and determining if they fall in the same bracket.
    """
    event_date = None
    if event_day:
        try:
            event_date = date.fromisoformat(event_day)
        except ValueError:
            pass
    
    # Load feature toggles and pass to service
    feature_toggles = FeatureToggles.load()
    
    comparison = metar_service.compare_zeus_vs_metar(
        station_code=station_code,
        event_day=event_date,
        feature_toggles=feature_toggles,  # NEW: Pass toggles
    )
    
    if comparison is None:
        return {
            "station_code": station_code,
            "event_day": event_date.isoformat() if event_date else date.today().isoformat(),
            "available": False,
            "error": "Missing Zeus forecast or METAR data",
        }
    
    comparison["available"] = True
    return comparison

