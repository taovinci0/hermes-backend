"""Feature toggle management endpoints.

Allows frontend to get and update feature toggle states.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from core.feature_toggles import FeatureToggles
from core.station_calibration import StationCalibration

router = APIRouter()


class ToggleUpdate(BaseModel):
    """Request model for updating feature toggles."""
    station_calibration: Optional[bool] = None


@router.get("/api/features/toggles")
async def get_toggles():
    """Get current feature toggle states.
    
    Returns:
        Dictionary with current toggle states:
        {
            "station_calibration": bool
        }
    """
    try:
        toggles = FeatureToggles.load()
        return toggles.to_dict()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load feature toggles: {str(e)}"
        )


@router.put("/api/features/toggles")
async def update_toggles(update: ToggleUpdate):
    """Update feature toggle states.
    
    Args:
        update: ToggleUpdate with optional fields to update
        
    Returns:
        Dictionary with status and updated toggle states:
        {
            "status": "updated",
            "toggles": {
                "station_calibration": bool
            }
        }
    """
    try:
        toggles = FeatureToggles.load()
        
        if update.station_calibration is not None:
            toggles.station_calibration = update.station_calibration
        
        toggles.save()
        
        return {
            "status": "updated",
            "toggles": toggles.to_dict()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update feature toggles: {str(e)}"
        )


@router.get("/api/features/calibrations")
async def get_calibrations():
    """Get station calibration status.
    
    Returns information about which stations have calibration models loaded
    and whether calibration is currently enabled.
    
    Returns:
        Dictionary with calibration status:
        {
            "enabled": bool,
            "stations_with_calibration": [str],
            "total_calibrations": int
        }
    """
    try:
        calibration = StationCalibration()
        toggles = FeatureToggles.load()
        
        # Get list of stations with calibrations
        stations_with_cal = []
        # Check common stations (can be expanded)
        for station_code in ["EGLC", "KLGA"]:
            if calibration.has_calibration(station_code):
                stations_with_cal.append(station_code)
        
        # Also check all loaded stations
        loaded_stations = calibration.get_loaded_stations()
        for station_code in loaded_stations:
            if station_code not in stations_with_cal:
                stations_with_cal.append(station_code)
        
        return {
            "enabled": toggles.station_calibration,
            "stations_with_calibration": sorted(stations_with_cal),
            "total_calibrations": len(stations_with_cal),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get calibration status: {str(e)}"
        )


