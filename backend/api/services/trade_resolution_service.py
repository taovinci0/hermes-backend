"""Service for resolving paper trade outcomes and calculating P&L."""

import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from venues.polymarket.resolution import PolyResolution
from venues.polymarket.discovery import PolyDiscovery
from core.registry import StationRegistry
from ..utils.path_utils import get_trades_dir
from ..models.schemas import Trade


class TradeResolutionService:
    """Service for resolving paper trade outcomes using event outcomePrices."""
    
    def __init__(self):
        self.trades_dir = get_trades_dir()
        self.resolver = PolyResolution()
        self.discovery = PolyDiscovery()
        self.registry = StationRegistry()
    
    def resolve_trades_for_date(
        self,
        trade_date: date,
        station_code: Optional[str] = None,
    ) -> List[Trade]:
        """Resolve all trades for a specific date using event outcomePrices.
        
        Uses the same method as backtester: fetch event, check outcomePrices
        for markets where outcomePrices[0] == "1" (Yes won).
        
        Args:
            trade_date: Date to resolve trades for
            station_code: Optional station filter
            
        Returns:
            List of resolved Trade objects
        """
        from ..services.trade_service import TradeService
        
        trade_service = TradeService()
        trades = trade_service.get_trades(
            trade_date=trade_date,
            station_code=station_code,
        )
        
        # Group trades by date and city (need city name, not station code)
        trades_by_event = defaultdict(list)
        for trade in trades:
            # Get city from station registry
            station = self.registry.get(trade.station_code)
            if not station:
                # Fallback to station code if not found
                city = trade.station_code
            else:
                city = station.city
            
            key = (trade_date, city)
            trades_by_event[key].append(trade)
        
        resolved_trades = []
        
        # Resolve each event
        for (event_date, city), event_trades in trades_by_event.items():
            try:
                # Fetch event using discovery (same as backtester)
                event_slug = self.discovery._generate_event_slugs(city, event_date)
                
                event = None
                for slug in event_slug:
                    event = self.discovery.get_event_by_slug(slug, save_snapshot=False)
                    if event:
                        break
                
                if not event:
                    # Event not found - mark all trades as pending
                    for trade in event_trades:
                        if not trade.outcome:  # Only update if not already resolved
                            trade.outcome = "pending"
                            trade.realized_pnl = 0.0
                        resolved_trades.append(trade)
                    continue
                
                # Find winner using outcomePrices (same method as backtester)
                winner_bracket = self.resolver.get_winner_from_event(event)
                
                if not winner_bracket:
                    # Event not resolved yet - mark all trades as pending
                    for trade in event_trades:
                        if not trade.outcome:
                            trade.outcome = "pending"
                            trade.realized_pnl = 0.0
                        resolved_trades.append(trade)
                    continue
                
                # Apply winner to all trades from this event
                for trade in event_trades:
                    if trade.outcome:  # Skip if already resolved
                        resolved_trades.append(trade)
                        continue
                    
                    # Store actual winner
                    trade.winner_bracket = winner_bracket
                    
                    # Normalize bracket names for comparison (exact match)
                    winner_normalized = winner_bracket.replace("°F", "").replace("≤", "").replace("≥", "").strip()
                    trade_normalized = trade.bracket_name.replace("°F", "").strip()
                    
                    # Check if this trade's bracket matches the winner
                    if winner_normalized == trade_normalized:
                        # WIN!
                        trade.outcome = "win"
                        # Calculate P&L: (1 / market_prob - 1) * size
                        if trade.p_mkt and trade.p_mkt > 0:
                            trade.realized_pnl = round((1 / trade.p_mkt - 1) * trade.size_usd, 2)
                        else:
                            # Fallback: assume 50% market prob if not available
                            trade.realized_pnl = round(trade.size_usd, 2)
                    else:
                        # LOSS
                        trade.outcome = "loss"
                        trade.realized_pnl = round(-trade.size_usd, 2)
                    
                    trade.resolved_at = datetime.now().isoformat()
                    trade.venue = "polymarket"
                    resolved_trades.append(trade)
            
            except Exception as e:
                # If resolution fails, mark all trades as pending
                for trade in event_trades:
                    if not trade.outcome:
                        trade.outcome = "pending"
                        trade.realized_pnl = 0.0
                    resolved_trades.append(trade)
        
        return resolved_trades
    
    def update_trade_csv(
        self,
        trade_date: date,
        resolved_trades: List[Trade],
    ) -> Path:
        """Update trade CSV with resolved outcomes.
        
        Args:
            trade_date: Date of trades
            resolved_trades: List of resolved trades
            
        Returns:
            Path to updated CSV file
        """
        import csv
        
        date_dir = self.trades_dir / trade_date.isoformat()
        date_dir.mkdir(parents=True, exist_ok=True)
        csv_file = date_dir / "paper_trades.csv"
        
        # Read existing trades to preserve order
        existing_trades = {}
        if csv_file.exists():
            with open(csv_file, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    key = f"{row['timestamp']}_{row['market_id']}"
                    existing_trades[key] = row
        
        # Update with resolved outcomes
        for trade in resolved_trades:
            key = f"{trade.timestamp}_{trade.market_id}"
            if key in existing_trades:
                existing_trades[key]["outcome"] = trade.outcome or ""
                existing_trades[key]["realized_pnl"] = str(trade.realized_pnl) if trade.realized_pnl is not None else ""
                existing_trades[key]["venue"] = trade.venue or "polymarket"
                existing_trades[key]["resolved_at"] = trade.resolved_at or ""
                existing_trades[key]["winner_bracket"] = trade.winner_bracket or ""
        
        # Write updated CSV
        fieldnames = [
            "timestamp", "station_code", "bracket_name", "bracket_lower_f",
            "bracket_upper_f", "market_id", "edge", "edge_pct", "f_kelly",
            "size_usd", "p_zeus", "p_mkt", "sigma_z", "reason",
            "outcome", "realized_pnl", "venue", "resolved_at", "winner_bracket"
        ]
        
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(existing_trades.values())
        
        return csv_file

