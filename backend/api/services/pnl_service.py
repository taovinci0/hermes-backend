"""Service for aggregating P&L across trades."""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import date, timedelta, datetime
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from ..services.trade_service import TradeService
from ..models.schemas import Trade


class PnLService:
    """Service for calculating aggregated P&L."""
    
    def __init__(self):
        self.trade_service = TradeService()
    
    def get_pnl(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        station_code: Optional[str] = None,
        venue: Optional[str] = None,
        mode: str = "paper",
    ) -> Dict[str, Any]:
        """Get aggregated P&L.
        
        Args:
            start_date: Start date filter
            end_date: End date filter
            station_code: Station filter
            venue: Venue filter ('polymarket', 'kalshi')
            mode: Trading mode ('paper', 'live')
            
        Returns:
            Dictionary with aggregated P&L data
        """
        # Get all trades in date range
        trades = self._get_trades_in_range(
            start_date=start_date,
            end_date=end_date,
            station_code=station_code,
            venue=venue,
            mode=mode,
        )
        
        # Calculate totals
        total_pnl = sum(t.realized_pnl or 0 for t in trades)
        total_risk = sum(t.size_usd for t in trades)
        roi = (total_pnl / total_risk * 100) if total_risk > 0 else 0.0
        
        # Breakdown by station
        by_station = defaultdict(lambda: {"pnl": 0.0, "risk": 0.0, "trades": 0})
        for trade in trades:
            by_station[trade.station_code]["pnl"] += trade.realized_pnl or 0
            by_station[trade.station_code]["risk"] += trade.size_usd
            by_station[trade.station_code]["trades"] += 1
        
        for station in by_station:
            station_roi = (by_station[station]["pnl"] / by_station[station]["risk"] * 100) if by_station[station]["risk"] > 0 else 0.0
            by_station[station]["roi"] = round(station_roi, 2)
            by_station[station]["pnl"] = round(by_station[station]["pnl"], 2)
            by_station[station]["risk"] = round(by_station[station]["risk"], 2)
        
        # Breakdown by venue
        by_venue = defaultdict(lambda: {"pnl": 0.0, "risk": 0.0, "trades": 0})
        for trade in trades:
            venue_name = trade.venue or "polymarket"
            by_venue[venue_name]["pnl"] += trade.realized_pnl or 0
            by_venue[venue_name]["risk"] += trade.size_usd
            by_venue[venue_name]["trades"] += 1
        
        for venue_name in by_venue:
            venue_roi = (by_venue[venue_name]["pnl"] / by_venue[venue_name]["risk"] * 100) if by_venue[venue_name]["risk"] > 0 else 0.0
            by_venue[venue_name]["roi"] = round(venue_roi, 2)
            by_venue[venue_name]["pnl"] = round(by_venue[venue_name]["pnl"], 2)
            by_venue[venue_name]["risk"] = round(by_venue[venue_name]["risk"], 2)
        
        # Breakdown by period
        today = date.today()
        by_period = {
            "today": self._get_pnl_for_period(trades, today, today),
            "week": self._get_pnl_for_period(trades, today - timedelta(days=7), today),
            "month": self._get_pnl_for_period(trades, today - timedelta(days=30), today),
            "year": self._get_pnl_for_period(trades, today - timedelta(days=365), today),
            "all_time": self._get_pnl_for_period(trades, None, None),
        }
        
        return {
            "total_pnl": round(total_pnl, 2),
            "total_risk": round(total_risk, 2),
            "roi": round(roi, 2),
            "by_station": dict(by_station),
            "by_venue": dict(by_venue),
            "by_period": by_period,
        }
    
    def _get_trades_in_range(
        self,
        start_date: Optional[date],
        end_date: Optional[date],
        station_code: Optional[str],
        venue: Optional[str],
        mode: str,
    ) -> List[Trade]:
        """Get trades in date range with filters."""
        # Get all trades (no date filter from service)
        all_trades = self.trade_service.get_trades(
            trade_date=None,
            station_code=station_code,
        )
        
        # Filter by date range
        filtered = []
        for trade in all_trades:
            try:
                trade_date = datetime.fromisoformat(trade.timestamp.replace("Z", "+00:00")).date()
                
                if start_date and trade_date < start_date:
                    continue
                if end_date and trade_date > end_date:
                    continue
                if venue and (trade.venue or "polymarket") != venue:
                    continue
                
                filtered.append(trade)
            except (ValueError, AttributeError):
                continue
        
        return filtered
    
    def _get_pnl_for_period(
        self,
        trades: List[Trade],
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> Dict[str, float]:
        """Get P&L for a specific period."""
        period_trades = []
        for trade in trades:
            try:
                trade_date = datetime.fromisoformat(trade.timestamp.replace("Z", "+00:00")).date()
                
                if start_date and trade_date < start_date:
                    continue
                if end_date and trade_date > end_date:
                    continue
                
                period_trades.append(trade)
            except (ValueError, AttributeError):
                continue
        
        pnl = sum(t.realized_pnl or 0 for t in period_trades)
        risk = sum(t.size_usd for t in period_trades)
        roi = (pnl / risk * 100) if risk > 0 else 0.0
        
        return {
            "pnl": round(pnl, 2),
            "risk": round(risk, 2),
            "roi": round(roi, 2),
        }

