"""Performance and P&L endpoints."""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import date

from ..services.pnl_service import PnLService
from ..services.performance_service import PerformanceService

router = APIRouter()
pnl_service = PnLService()
performance_service = PerformanceService()


@router.get("/pnl")
async def get_pnl(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    station_code: Optional[str] = Query(None, description="Station code filter"),
    venue: Optional[str] = Query(None, description="Venue filter (polymarket, kalshi)"),
    mode: str = Query("paper", description="Trading mode (paper, live)"),
):
    """Get aggregated P&L."""
    start_date_obj = None
    end_date_obj = None
    
    if start_date:
        try:
            start_date_obj = date.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")
    
    if end_date:
        try:
            end_date_obj = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")
    
    try:
        return pnl_service.get_pnl(
            start_date=start_date_obj,
            end_date=end_date_obj,
            station_code=station_code,
            venue=venue,
            mode=mode,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate P&L: {str(e)}")


@router.get("/metrics")
async def get_metrics(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    station_code: Optional[str] = Query(None, description="Station code filter"),
    mode: str = Query("paper", description="Trading mode (paper, live)"),
):
    """Get performance metrics."""
    start_date_obj = None
    end_date_obj = None
    
    if start_date:
        try:
            start_date_obj = date.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")
    
    if end_date:
        try:
            end_date_obj = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")
    
    try:
        return performance_service.get_metrics(
            start_date=start_date_obj,
            end_date=end_date_obj,
            station_code=station_code,
            mode=mode,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate metrics: {str(e)}")

