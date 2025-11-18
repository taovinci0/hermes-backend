"""Service for reading trade CSV files."""

from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import date, datetime

from ..utils.path_utils import get_trades_dir
from ..utils.file_utils import read_csv_file, parse_timestamp
from ..models.schemas import Trade


class TradeService:
    """Service for reading paper trade CSV files."""
    
    def __init__(self):
        """Initialize trade service."""
        self.trades_dir = get_trades_dir()
    
    def get_trades(
        self,
        trade_date: Optional[date] = None,
        station_code: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Trade]:
        """Get trades from CSV files.
        
        Args:
            trade_date: Optional date filter (YYYY-MM-DD)
            station_code: Optional station code filter
            limit: Optional limit on number of trades
            
        Returns:
            List of Trade objects
        """
        if trade_date:
            # Read from specific date directory
            date_dir = self.trades_dir / trade_date.isoformat()
            csv_file = date_dir / "paper_trades.csv"
            
            if not csv_file.exists():
                return []
            
            rows = read_csv_file(csv_file)
        else:
            # Read from all date directories
            rows = []
            for date_dir in sorted(self.trades_dir.iterdir(), reverse=True):
                if not date_dir.is_dir():
                    continue
                
                csv_file = date_dir / "paper_trades.csv"
                if csv_file.exists():
                    rows.extend(read_csv_file(csv_file))
        
        # Convert to Trade objects
        trades = []
        for row in rows:
            # Filter by station if specified
            if station_code and row.get("station_code") != station_code:
                continue
            
            try:
                trade = Trade(
                    timestamp=row.get("timestamp", ""),
                    station_code=row.get("station_code", ""),
                    bracket_name=row.get("bracket_name", ""),
                    bracket_lower_f=int(row.get("bracket_lower_f", 0)),
                    bracket_upper_f=int(row.get("bracket_upper_f", 0)),
                    market_id=row.get("market_id", ""),
                    edge=float(row.get("edge", 0)),
                    edge_pct=float(row.get("edge_pct", 0)),
                    f_kelly=float(row.get("f_kelly", 0)),
                    size_usd=float(row.get("size_usd", 0)),
                    p_zeus=float(row["p_zeus"]) if row.get("p_zeus") else None,
                    p_mkt=float(row["p_mkt"]) if row.get("p_mkt") else None,
                    sigma_z=float(row["sigma_z"]) if row.get("sigma_z") else None,
                    reason=row.get("reason", ""),
                    # P&L tracking fields
                    outcome=row.get("outcome") or None,
                    realized_pnl=float(row["realized_pnl"]) if row.get("realized_pnl") else None,
                    venue=row.get("venue") or None,
                    resolved_at=row.get("resolved_at") or None,
                    winner_bracket=row.get("winner_bracket") or None,
                )
                trades.append(trade)
            except (ValueError, KeyError):
                # Skip invalid rows
                continue
        
        # Sort by timestamp descending (most recent first)
        trades.sort(key=lambda t: t.timestamp, reverse=True)
        
        if limit:
            trades = trades[:limit]
        
        return trades
    
    def get_trade_summary(
        self,
        trade_date: Optional[date] = None,
        station_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get summary statistics for trades.
        
        Args:
            trade_date: Optional date filter
            station_code: Optional station code filter
            
        Returns:
            Dictionary with summary statistics
        """
        trades = self.get_trades(trade_date=trade_date, station_code=station_code)
        
        if not trades:
            return {
                "total_trades": 0,
                "total_size_usd": 0.0,
                "avg_edge_pct": 0.0,
                "total_edges": [],
            }
        
        total_size = sum(t.size_usd for t in trades)
        avg_edge = sum(t.edge_pct for t in trades) / len(trades) if trades else 0.0
        
        return {
            "total_trades": len(trades),
            "total_size_usd": round(total_size, 2),
            "avg_edge_pct": round(avg_edge, 2),
            "total_edges": [t.edge_pct for t in trades],
        }

