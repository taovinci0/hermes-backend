"""Trade endpoints."""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import date

from ..services.trade_service import TradeService
from ..services.trade_resolution_service import TradeResolutionService
from ..models.schemas import TradeListResponse

router = APIRouter()
trade_service = TradeService()
resolution_service = TradeResolutionService()


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


@router.get("/history")
async def get_trade_history(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    station_code: Optional[str] = Query(None, description="Station code filter"),
    venue: Optional[str] = Query(None, description="Venue filter"),
    outcome: Optional[str] = Query(None, description="Outcome filter (win, loss, pending)"),
    mode: str = Query("paper", description="Trading mode (paper, live)"),
    limit: Optional[int] = Query(100, description="Maximum number of trades"),
    offset: Optional[int] = Query(0, description="Offset for pagination"),
):
    """Get trade history with filtering and pagination."""
    from datetime import datetime
    
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
    
    # Get all trades
    all_trades = trade_service.get_trades(
        trade_date=None,
        station_code=station_code,
    )
    
    # Apply filters
    filtered = []
    for trade in all_trades:
        try:
            trade_date = datetime.fromisoformat(trade.timestamp.replace("Z", "+00:00")).date()
            
            if start_date_obj and trade_date < start_date_obj:
                continue
            if end_date_obj and trade_date > end_date_obj:
                continue
            if venue and (trade.venue or "polymarket") != venue:
                continue
            if outcome and (trade.outcome or "pending") != outcome:
                continue
            
            filtered.append(trade)
        except (ValueError, AttributeError):
            continue
    
    # Pagination
    total = len(filtered)
    paginated = filtered[offset:offset + limit]
    
    return {
        "trades": paginated,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total,
    }


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


@router.post("/resolve")
async def resolve_trades(
    trade_date: Optional[str] = Query(None, description="Trade date (YYYY-MM-DD)"),
    station_code: Optional[str] = Query(None, description="Station code filter"),
):
    """Resolve paper trade outcomes and calculate P&L.
    
    Uses event outcomePrices method (same as backtester) to determine
    winners and calculate realized P&L.
    """
    trade_date_obj = None
    if trade_date:
        try:
            trade_date_obj = date.fromisoformat(trade_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        from datetime import date
        trade_date_obj = date.today()
    
    try:
        resolved_trades = resolution_service.resolve_trades_for_date(
            trade_date=trade_date_obj,
            station_code=station_code,
        )
        
        # Update CSV with resolved outcomes
        resolution_service.update_trade_csv(trade_date_obj, resolved_trades)
        
        # Calculate summary
        resolved_count = len([t for t in resolved_trades if t.outcome and t.outcome != "pending"])
        pending_count = len([t for t in resolved_trades if t.outcome == "pending" or not t.outcome])
        wins = len([t for t in resolved_trades if t.outcome == "win"])
        losses = len([t for t in resolved_trades if t.outcome == "loss"])
        total_pnl = sum(t.realized_pnl or 0 for t in resolved_trades)
        
        return {
            "success": True,
            "message": f"Resolved {len(resolved_trades)} trades",
            "resolved": resolved_count,
            "pending": pending_count,
            "wins": wins,
            "losses": losses,
            "total_pnl": round(total_pnl, 2),
            "trade_date": trade_date_obj.isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resolve trades: {str(e)}")

