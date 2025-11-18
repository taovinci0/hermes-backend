"""Service for calculating performance metrics."""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import date, datetime
from collections import defaultdict
import statistics

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from ..services.trade_service import TradeService
from ..models.schemas import Trade


class PerformanceService:
    """Service for calculating performance metrics."""
    
    def __init__(self):
        self.trade_service = TradeService()
    
    def get_metrics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        station_code: Optional[str] = None,
        mode: str = "paper",
    ) -> Dict[str, Any]:
        """Get performance metrics.
        
        Args:
            start_date: Start date filter
            end_date: End date filter
            station_code: Station filter
            mode: Trading mode ('paper', 'live')
            
        Returns:
            Dictionary with performance metrics
        """
        # Get trades
        trades = self._get_trades_in_range(
            start_date=start_date,
            end_date=end_date,
            station_code=station_code,
            mode=mode,
        )
        
        # Basic counts
        total_trades = len(trades)
        resolved_trades = [t for t in trades if t.outcome and t.outcome != "pending"]
        pending_trades = [t for t in trades if t.outcome == "pending" or not t.outcome]
        
        wins = [t for t in resolved_trades if t.outcome == "win"]
        losses = [t for t in resolved_trades if t.outcome == "loss"]
        
        win_rate = (len(wins) / len(resolved_trades) * 100) if resolved_trades else 0.0
        
        # P&L metrics
        total_risk = sum(t.size_usd for t in trades)
        total_pnl = sum(t.realized_pnl or 0 for t in resolved_trades)
        roi = (total_pnl / total_risk * 100) if total_risk > 0 else 0.0
        
        # Average edge
        avg_edge = statistics.mean([t.edge_pct for t in trades]) if trades else 0.0
        
        # Largest win/loss
        pnl_values = [t.realized_pnl for t in resolved_trades if t.realized_pnl is not None]
        largest_win = max(pnl_values) if pnl_values else 0.0
        largest_loss = min(pnl_values) if pnl_values else 0.0
        
        # Sharpe ratio (simplified: mean return / std dev)
        if len(pnl_values) > 1:
            mean_return = statistics.mean(pnl_values)
            std_dev = statistics.stdev(pnl_values)
            sharpe_ratio = (mean_return / std_dev) if std_dev > 0 else 0.0
        else:
            sharpe_ratio = 0.0
        
        # Breakdown by station
        by_station = {}
        stations = set(t.station_code for t in trades)
        for station in stations:
            station_trades = [t for t in trades if t.station_code == station]
            station_metrics = self._calculate_metrics_for_trades(station_trades)
            by_station[station] = station_metrics
        
        return {
            "total_trades": total_trades,
            "resolved_trades": len(resolved_trades),
            "pending_trades": len(pending_trades),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": round(win_rate, 2),
            "total_risk": round(total_risk, 2),
            "total_pnl": round(total_pnl, 2),
            "roi": round(roi, 2),
            "avg_edge_pct": round(avg_edge, 2),
            "largest_win": round(largest_win, 2),
            "largest_loss": round(largest_loss, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "by_station": by_station,
        }
    
    def _get_trades_in_range(
        self,
        start_date: Optional[date],
        end_date: Optional[date],
        station_code: Optional[str],
        mode: str,
    ) -> List[Trade]:
        """Get trades in date range."""
        all_trades = self.trade_service.get_trades(
            trade_date=None,
            station_code=station_code,
        )
        
        filtered = []
        for trade in all_trades:
            try:
                trade_date = datetime.fromisoformat(trade.timestamp.replace("Z", "+00:00")).date()
                
                if start_date and trade_date < start_date:
                    continue
                if end_date and trade_date > end_date:
                    continue
                
                filtered.append(trade)
            except (ValueError, AttributeError):
                continue
        
        return filtered
    
    def _calculate_metrics_for_trades(self, trades: List[Trade]) -> Dict[str, Any]:
        """Calculate metrics for a list of trades."""
        resolved = [t for t in trades if t.outcome and t.outcome != "pending"]
        wins = [t for t in resolved if t.outcome == "win"]
        losses = [t for t in resolved if t.outcome == "loss"]
        
        win_rate = (len(wins) / len(resolved) * 100) if resolved else 0.0
        total_risk = sum(t.size_usd for t in trades)
        total_pnl = sum(t.realized_pnl or 0 for t in resolved)
        roi = (total_pnl / total_risk * 100) if total_risk > 0 else 0.0
        
        return {
            "trades": len(trades),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": round(win_rate, 2),
            "pnl": round(total_pnl, 2),
            "roi": round(roi, 2),
        }

