"""Station endpoints."""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from core.registry import StationRegistry

router = APIRouter()
registry = StationRegistry()


def normalize_venue(venue_hint: str) -> str:
    """Extract venue platform from venue_hint.
    
    Args:
        venue_hint: Venue hint string (e.g., "Polymarket London", "Kalshi NYC")
        
    Returns:
        Normalized venue identifier: 'polymarket' or 'kalshi'
    """
    hint_lower = venue_hint.lower()
    if 'polymarket' in hint_lower:
        return 'polymarket'
    elif 'kalshi' in hint_lower:
        return 'kalshi'
    else:
        # Default fallback (most stations are Polymarket)
        return 'polymarket'


@router.get("/")
async def get_stations() -> Dict[str, Any]:
    """Get all stations with venue information.
    
    Returns:
        Dictionary with stations list, each containing:
        - station_code: Station code (e.g., "EGLC")
        - city: City name (e.g., "London")
        - station_name: Full station name (e.g., "London City Airport")
        - venue: Normalized venue identifier ('polymarket' or 'kalshi')
        - venue_hint: Original venue hint string
        - timezone: IANA timezone (e.g., "Europe/London")
    """
    stations = registry.list_all()
    
    station_list = []
    for station in stations:
        venue = normalize_venue(station.venue_hint)
        station_list.append({
            "station_code": station.station_code,
            "city": station.city,
            "station_name": station.station_name,
            "venue": venue,
            "venue_hint": station.venue_hint,
            "timezone": station.time_zone,
        })
    
    return {
        "stations": station_list,
        "count": len(station_list),
    }


@router.get("/{station_code}")
async def get_station(station_code: str) -> Dict[str, Any]:
    """Get single station by code.
    
    Args:
        station_code: Station code (e.g., "EGLC")
    
    Returns:
        Station information with venue:
        - station_code: Station code
        - city: City name
        - station_name: Full station name
        - venue: Normalized venue identifier ('polymarket' or 'kalshi')
        - venue_hint: Original venue hint string
        - timezone: IANA timezone
    
    Raises:
        HTTPException: 404 if station not found
    """
    station = registry.get(station_code.upper())
    
    if not station:
        raise HTTPException(
            status_code=404, 
            detail=f"Station {station_code} not found"
        )
    
    return {
        "station_code": station.station_code,
        "city": station.city,
        "station_name": station.station_name,
        "venue": normalize_venue(station.venue_hint),
        "venue_hint": station.venue_hint,
        "timezone": station.time_zone,
    }

