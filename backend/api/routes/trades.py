"""Trade endpoints."""

from fastapi import APIRouter, Query
from typing import Optional
from datetime import date

from ..services.trade_service import TradeService
from ..models.schemas import TradeListResponse

router = APIRouter()
trade_service = TradeService()


@router.get("/recent", response_model=TradeListResponse)
async def get_recent_trades(
    trade_date: Optional[str] = Query(None, description="Trade date (YYYY-MM-DD)"),
    station_code: Optional[str] = Query(None, description="Station code filter"),
    limit: Optional[int] = Query(100, description="Maximum number of trades"),
):
    """Get recent trades."""
    trade_date_obj = None
    if trade_date:
        try:
            trade_date_obj = date.fromisoformat(trade_date)
        except ValueError:
            pass
    
    trades = trade_service.get_trades(
        trade_date=trade_date_obj,
        station_code=station_code,
        limit=limit,
    )
    
    total_size = sum(t.size_usd for t in trades)
    
    return TradeListResponse(
        trades=trades,
        count=len(trades),
        total_size_usd=round(total_size, 2),
    )


@router.get("/summary")
async def get_trade_summary(
    trade_date: Optional[str] = Query(None, description="Trade date (YYYY-MM-DD)"),
    station_code: Optional[str] = Query(None, description="Station code filter"),
):
    """Get trade summary statistics."""
    trade_date_obj = None
    if trade_date:
        try:
            trade_date_obj = date.fromisoformat(trade_date)
        except ValueError:
            pass
    
    summary = trade_service.get_trade_summary(
        trade_date=trade_date_obj,
        station_code=station_code,
    )
    
    return summary

