# Performance & Portfolio Page - Implementation Plan

**Date**: November 17, 2025  
**Purpose**: Staged implementation plan for Performance & Portfolio page (backend + frontend)  
**Scope**: Paper trading (MVP), Live trading (future), Polymarket (MVP), Kalshi (future)

---

## 🎯 Overview

This document outlines a **staged implementation plan** for the Performance & Portfolio page, building from basic paper trading support to full live trading with multiple venues.

**Implementation Stages**:
- **Backend/API**: 4 stages
- **Frontend**: 5 stages

**Total Estimated Time**: 20-30 hours

---

## 📋 Prerequisites

Before starting:
- ✅ Backend API is running (`http://localhost:8000`)
- ✅ Paper trading is generating trade CSV files
- ✅ Trade resolution service exists (for backtesting)
- ✅ Frontend project is set up

---

## 🔧 Backend/API Implementation Stages

### Stage 1: Trade Resolution for Paper Trades

**Goal**: Resolve paper trade outcomes and calculate P&L

**Estimated Time**: 4-5 hours

#### 1.1 Enhance Paper Trade Schema

**File**: `backend/api/models/schemas.py`

**Add fields to Trade model**:
```python
class Trade(BaseModel):
    """Paper trade record."""
    timestamp: str
    station_code: str
    bracket_name: str
    bracket_lower_f: int
    bracket_upper_f: int
    market_id: str
    edge: float
    edge_pct: float
    f_kelly: float
    size_usd: float
    p_zeus: Optional[float] = None
    p_mkt: Optional[float] = None
    sigma_z: Optional[float] = None
    reason: str
    
    # New fields for P&L tracking
    outcome: Optional[str] = None  # 'win', 'loss', 'pending'
    realized_pnl: Optional[float] = None
    venue: Optional[str] = None  # 'polymarket', 'kalshi'
    resolved_at: Optional[str] = None
    winner_bracket: Optional[str] = None
```

#### 1.2 Create Trade Resolution Service

**File**: `backend/api/services/trade_resolution_service.py`

**Implementation**:
```python
"""Service for resolving paper trade outcomes and calculating P&L."""

from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from collections import defaultdict
import csv

from venues.polymarket.resolution import PolyResolution
from venues.polymarket.discovery import PolyDiscovery
from ..utils.path_utils import get_trades_dir
from ..models.schemas import Trade


class TradeResolutionService:
    """Service for resolving paper trade outcomes using event outcomePrices."""
    
    def __init__(self):
        self.trades_dir = get_trades_dir()
        self.resolver = PolyResolution()
        self.discovery = PolyDiscovery()
    
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
        # Map station codes to city names
        station_to_city = {
            "EGLC": "London",
            "KLGA": "New York",
            "KORD": "Chicago",
            "KLAX": "Los Angeles",
            # Add more as needed
        }
        
        trades_by_event = defaultdict(list)
        for trade in trades:
            city = station_to_city.get(trade.station_code, trade.station_code)
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
                    
                    trade.resolved_at = datetime.utcnow().isoformat()
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
                existing_trades[key]["realized_pnl"] = str(trade.realized_pnl) if trade.realized_pnl else ""
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
```

#### 1.3 Update Trade Service to Read New Fields

**File**: `backend/api/services/trade_service.py`

**Update `get_trades` method**:
```python
def get_trades(...) -> List[Trade]:
    # ... existing code ...
    
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
            # New fields
            outcome=row.get("outcome") or None,
            realized_pnl=float(row["realized_pnl"]) if row.get("realized_pnl") else None,
            venue=row.get("venue") or None,
            resolved_at=row.get("resolved_at") or None,
            winner_bracket=row.get("winner_bracket") or None,
        )
        trades.append(trade)
    except (ValueError, KeyError):
        continue
```

#### 1.4 Create Resolution Endpoint

**File**: `backend/api/routes/trades.py`

**Add endpoint**:
```python
from ..services.trade_resolution_service import TradeResolutionService

resolution_service = TradeResolutionService()

@router.post("/resolve")
async def resolve_trades(
    trade_date: Optional[str] = Query(None, description="Trade date (YYYY-MM-DD)"),
    station_code: Optional[str] = Query(None, description="Station code filter"),
):
    """Resolve paper trade outcomes and calculate P&L."""
    trade_date_obj = None
    if trade_date:
        try:
            trade_date_obj = date.fromisoformat(trade_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")
    
    resolved_trades = resolution_service.resolve_trades_for_date(
        trade_date=trade_date_obj or date.today(),
        station_code=station_code,
    )
    
    # Update CSV
    if trade_date_obj:
        resolution_service.update_trade_csv(trade_date_obj, resolved_trades)
    
    return {
        "resolved": len([t for t in resolved_trades if t.outcome]),
        "pending": len([t for t in resolved_trades if t.outcome == "pending"]),
        "wins": len([t for t in resolved_trades if t.outcome == "win"]),
        "losses": len([t for t in resolved_trades if t.outcome == "loss"]),
        "total_pnl": sum(t.realized_pnl or 0 for t in resolved_trades),
    }
```

#### 1.5 Testing

**Manual Testing**:
1. Create test paper trades
2. Resolve trades for a date
3. Verify outcomes are correct
4. Verify P&L is calculated correctly
5. Verify CSV is updated

**Expected Results**:
- ✅ Trades are resolved correctly
- ✅ P&L is calculated accurately
- ✅ CSV files are updated
- ✅ Pending trades are handled gracefully

---

### Stage 2: P&L Aggregation Service

**Goal**: Aggregate P&L across trades with various filters

**Estimated Time**: 3-4 hours

#### 2.1 Create P&L Aggregation Service

**File**: `backend/api/services/pnl_service.py`

**Implementation**:
```python
"""Service for aggregating P&L across trades."""

from typing import List, Dict, Any, Optional
from datetime import date, timedelta
from collections import defaultdict

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
                if venue and trade.venue != venue:
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
```

#### 2.2 Create P&L Endpoint

**File**: `backend/api/routes/performance.py` (new file)

**Implementation**:
```python
"""Performance and P&L endpoints."""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import date

from ..services.pnl_service import PnLService

router = APIRouter()
pnl_service = PnLService()


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
            raise HTTPException(status_code=400, detail="Invalid start_date format")
    
    if end_date:
        try:
            end_date_obj = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format")
    
    return pnl_service.get_pnl(
        start_date=start_date_obj,
        end_date=end_date_obj,
        station_code=station_code,
        venue=venue,
        mode=mode,
    )
```

#### 2.3 Register Router

**File**: `backend/api/main.py`

**Add**:
```python
from .routes import performance

app.include_router(performance.router, prefix="/api/performance", tags=["performance"])
```

#### 2.4 Testing

**Manual Testing**:
1. Test P&L aggregation with various filters
2. Test date range filtering
3. Test station filtering
4. Test venue filtering
5. Verify breakdowns are correct

**Expected Results**:
- ✅ P&L is aggregated correctly
- ✅ Filters work as expected
- ✅ Breakdowns are accurate
- ✅ ROI is calculated correctly

---

### Stage 3: Performance Metrics Service

**Goal**: Calculate performance metrics (win rate, Sharpe ratio, etc.)

**Estimated Time**: 3-4 hours

#### 3.1 Create Performance Metrics Service

**File**: `backend/api/services/performance_service.py`

**Implementation**:
```python
"""Service for calculating performance metrics."""

from typing import List, Dict, Any, Optional
from datetime import date
from collections import defaultdict
import statistics

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
        pnl_values = [t.realized_pnl for t in resolved_trades if t.realized_pnl]
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
```

#### 3.2 Create Metrics Endpoint

**File**: `backend/api/routes/performance.py`

**Add**:
```python
from ..services.performance_service import PerformanceService

performance_service = PerformanceService()

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
            raise HTTPException(status_code=400, detail="Invalid start_date format")
    
    if end_date:
        try:
            end_date_obj = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format")
    
    return performance_service.get_metrics(
        start_date=start_date_obj,
        end_date=end_date_obj,
        station_code=station_code,
        mode=mode,
    )
```

#### 3.3 Testing

**Manual Testing**:
1. Test metrics calculation
2. Test win rate calculation
3. Test Sharpe ratio calculation
4. Test station breakdowns
5. Verify all metrics are accurate

**Expected Results**:
- ✅ All metrics are calculated correctly
- ✅ Win rate is accurate
- ✅ Sharpe ratio is reasonable
- ✅ Station breakdowns are correct

---

### Stage 4: Enhanced Trade History Endpoint

**Goal**: Enhanced trade history with outcomes, P&L, and filtering

**Estimated Time**: 2-3 hours

#### 4.1 Enhance Trade History Endpoint

**File**: `backend/api/routes/trades.py`

**Update**:
```python
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
    start_date_obj = None
    end_date_obj = None
    
    if start_date:
        try:
            start_date_obj = date.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format")
    
    if end_date:
        try:
            end_date_obj = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format")
    
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
            if venue and trade.venue != venue:
                continue
            if outcome and trade.outcome != outcome:
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
```

#### 4.2 Testing

**Manual Testing**:
1. Test date range filtering
2. Test station filtering
3. Test venue filtering
4. Test outcome filtering
5. Test pagination

**Expected Results**:
- ✅ All filters work correctly
- ✅ Pagination works
- ✅ Response includes metadata

---

## 🎨 Frontend Implementation Stages

### Stage 1: Basic Page Structure & Mode Toggle

**Goal**: Create page structure with mode toggle

**Estimated Time**: 2-3 hours

#### 1.1 Create Performance Page Component

**File**: `src/pages/PerformancePage.tsx`

**Basic Structure**:
```typescript
import React, { useState, useEffect } from 'react';
import { fetchExecutionMode } from '../services/api';

export const PerformancePage: React.FC = () => {
  const [mode, setMode] = useState<'paper' | 'live'>('paper');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadExecutionMode();
  }, []);

  const loadExecutionMode = async () => {
    try {
      const status = await fetchExecutionMode();
      setMode(status.execution_mode || 'paper');
    } catch (err) {
      // Default to paper
      setMode('paper');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="performance-page">
      <h1>💰 Performance & Portfolio Overview</h1>
      
      <div className="mode-selector">
        <button
          className={mode === 'paper' ? 'active' : ''}
          onClick={() => setMode('paper')}
        >
          ⚠️ Paper Trading
        </button>
        <button
          className={mode === 'live' ? 'active' : ''}
          onClick={() => setMode('live')}
        >
          ✅ Live Trading
        </button>
      </div>

      {mode === 'paper' && (
        <div className="paper-mode-warning">
          ⚠️ Paper Trading Mode: Showing simulated trades and theoretical P&L
        </div>
      )}

      {mode === 'live' && (
        <div className="live-mode-info">
          ✅ Live Trading Mode: Showing real trades and actual account balances
        </div>
      )}

      {/* Sections will be added in later stages */}
    </div>
  );
};
```

#### 1.2 Create API Service

**File**: `src/services/performanceApi.ts`

**Implementation**:
```typescript
const API_BASE = 'http://localhost:8000';

export interface PnLData {
  total_pnl: number;
  total_risk: number;
  roi: number;
  by_station: Record<string, { pnl: number; risk: number; roi: number; trades: number }>;
  by_venue: Record<string, { pnl: number; risk: number; roi: number; trades: number }>;
  by_period: {
    today: { pnl: number; risk: number; roi: number };
    week: { pnl: number; risk: number; roi: number };
    month: { pnl: number; risk: number; roi: number };
    year: { pnl: number; risk: number; roi: number };
    all_time: { pnl: number; risk: number; roi: number };
  };
}

export interface PerformanceMetrics {
  total_trades: number;
  resolved_trades: number;
  pending_trades: number;
  wins: number;
  losses: number;
  win_rate: number;
  total_risk: number;
  total_pnl: number;
  roi: number;
  avg_edge_pct: number;
  largest_win: number;
  largest_loss: number;
  sharpe_ratio: number;
  by_station: Record<string, {
    trades: number;
    wins: number;
    losses: number;
    win_rate: number;
    pnl: number;
    roi: number;
  }>;
}

export interface TradeHistoryResponse {
  trades: Trade[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface Trade {
  timestamp: string;
  station_code: string;
  bracket_name: string;
  bracket_lower_f: number;
  bracket_upper_f: number;
  market_id: string;
  edge: number;
  edge_pct: number;
  f_kelly: number;
  size_usd: number;
  p_zeus?: number;
  p_mkt?: number;
  outcome?: string;
  realized_pnl?: number;
  venue?: string;
  resolved_at?: string;
  winner_bracket?: string;
}

// Get P&L data
export const fetchPnL = async (
  mode: 'paper' | 'live' = 'paper',
  params?: {
    start_date?: string;
    end_date?: string;
    station_code?: string;
    venue?: string;
  }
): Promise<PnLData> => {
  const queryParams = new URLSearchParams({ mode, ...params });
  const response = await fetch(`${API_BASE}/api/performance/pnl?${queryParams}`);
  if (!response.ok) throw new Error('Failed to fetch P&L');
  return response.json();
};

// Get performance metrics
export const fetchMetrics = async (
  mode: 'paper' | 'live' = 'paper',
  params?: {
    start_date?: string;
    end_date?: string;
    station_code?: string;
  }
): Promise<PerformanceMetrics> => {
  const queryParams = new URLSearchParams({ mode, ...params });
  const response = await fetch(`${API_BASE}/api/performance/metrics?${queryParams}`);
  if (!response.ok) throw new Error('Failed to fetch metrics');
  return response.json();
};

// Get trade history
export const fetchTradeHistory = async (
  mode: 'paper' | 'live' = 'paper',
  params?: {
    start_date?: string;
    end_date?: string;
    station_code?: string;
    venue?: string;
    outcome?: string;
    limit?: number;
    offset?: number;
  }
): Promise<TradeHistoryResponse> => {
  const queryParams = new URLSearchParams({ mode, ...params });
  const response = await fetch(`${API_BASE}/api/trades/history?${queryParams}`);
  if (!response.ok) throw new Error('Failed to fetch trade history');
  return response.json();
};

// Resolve trades
export const resolveTrades = async (
  trade_date?: string,
  station_code?: string
): Promise<any> => {
  const queryParams = new URLSearchParams();
  if (trade_date) queryParams.set('trade_date', trade_date);
  if (station_code) queryParams.set('station_code', station_code);
  
  const response = await fetch(`${API_BASE}/api/trades/resolve?${queryParams}`, {
    method: 'POST',
  });
  if (!response.ok) throw new Error('Failed to resolve trades');
  return response.json();
};
```

#### 1.3 Testing

**Manual Testing**:
1. Test mode toggle
2. Test page loads correctly
3. Test mode detection from API
4. Verify warnings/info messages display

**Expected Results**:
- ✅ Mode toggle works
- ✅ Page loads without errors
- ✅ Mode is detected from API
- ✅ Appropriate messages are shown

---

### Stage 2: Account Balances Section

**Goal**: Display account balances (simulated for paper, real for live)

**Estimated Time**: 2-3 hours

#### 2.1 Create Account Balances Component

**File**: `src/components/AccountBalances.tsx`

**Implementation**:
```typescript
import React, { useState, useEffect } from 'react';
import { fetchPnL } from '../services/performanceApi';
import { fetchConfig } from '../services/configApi';

interface AccountBalancesProps {
  mode: 'paper' | 'live';
}

export const AccountBalances: React.FC<AccountBalancesProps> = ({ mode }) => {
  const [pnl, setPnl] = useState<any>(null);
  const [startingBalance, setStartingBalance] = useState<number>(10000);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [mode]);

  const loadData = async () => {
    setLoading(true);
    try {
      const pnlData = await fetchPnL(mode, {});
      setPnl(pnlData);
      
      if (mode === 'paper') {
        // Get starting balance from config
        const config = await fetchConfig();
        setStartingBalance(config.trading?.daily_bankroll_cap || 10000);
      }
    } catch (err) {
      console.error('Failed to load balances:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading balances...</div>;

  if (mode === 'paper') {
    const currentBalance = startingBalance + (pnl?.total_pnl || 0);
    
    return (
      <div className="account-balances paper-mode">
        <h2>📊 Account Balances (Paper Trading)</h2>
        <div className="warning">
          ⚠️ Paper Trading Mode - No Real Account Balances
        </div>
        <div className="balance-display">
          <div className="balance-item">
            <label>Simulated Starting Balance:</label>
            <span>${startingBalance.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
          </div>
          <div className="balance-item">
            <label>Current Simulated Balance:</label>
            <span className={pnl?.total_pnl >= 0 ? 'positive' : 'negative'}>
              ${currentBalance.toLocaleString('en-US', { minimumFractionDigits: 2 })}
              {pnl?.total_pnl !== 0 && (
                <span> ({pnl?.total_pnl >= 0 ? '+' : ''}${pnl?.total_pnl.toFixed(2)})</span>
              )}
            </span>
          </div>
          <div className="balance-item">
            <label>Total P&L (Theoretical):</label>
            <span className={pnl?.total_pnl >= 0 ? 'positive' : 'negative'}>
              {pnl?.total_pnl >= 0 ? '+' : ''}${pnl?.total_pnl.toFixed(2)}
            </span>
          </div>
        </div>
        <div className="note">
          Note: These are simulated balances for testing purposes only.
        </div>
      </div>
    );
  }

  // Live mode - will be implemented when account APIs are available
  return (
    <div className="account-balances live-mode">
      <h2>📊 Account Balances (Live Trading)</h2>
      <div className="info">
        ✅ Live Trading Mode - Real Account Balances
      </div>
      <div className="coming-soon">
        Account balance integration coming soon.
        <br />
        This will show real balances from Polymarket and Kalshi APIs.
      </div>
    </div>
  );
};
```

#### 2.2 Testing

**Manual Testing**:
1. Test paper mode balances
2. Test live mode placeholder
3. Test balance calculation
4. Verify formatting

**Expected Results**:
- ✅ Paper balances display correctly
- ✅ Live mode shows placeholder
- ✅ Calculations are accurate
- ✅ Formatting is correct

---

### Stage 3: P&L Dashboard Section

**Goal**: Display P&L with period selector and breakdowns

**Estimated Time**: 3-4 hours

#### 3.1 Create P&L Dashboard Component

**File**: `src/components/PnLDashboard.tsx`

**Implementation**:
```typescript
import React, { useState, useEffect } from 'react';
import { fetchPnL, PnLData } from '../services/performanceApi';

interface PnLDashboardProps {
  mode: 'paper' | 'live';
}

type Period = 'today' | 'week' | 'month' | 'year' | 'all_time';

export const PnLDashboard: React.FC<PnLDashboardProps> = ({ mode }) => {
  const [period, setPeriod] = useState<Period>('all_time');
  const [pnl, setPnl] = useState<PnLData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPnL();
  }, [mode, period]);

  const loadPnL = async () => {
    setLoading(true);
    try {
      const data = await fetchPnL(mode);
      setPnl(data);
    } catch (err) {
      console.error('Failed to load P&L:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading P&L...</div>;
  if (!pnl) return <div>No P&L data available</div>;

  const periodData = pnl.by_period[period];

  return (
    <div className="pnl-dashboard">
      <h2>📈 Profit & Loss</h2>
      
      {mode === 'paper' && (
        <div className="warning">
          ⚠️ Theoretical P&L (Based on resolved outcomes)
        </div>
      )}

      {mode === 'live' && (
        <div className="info">
          ✅ Real P&L (From actual trade execution and settlement)
        </div>
      )}

      <div className="period-selector">
        {(['today', 'week', 'month', 'year', 'all_time'] as Period[]).map((p) => (
          <button
            key={p}
            className={period === p ? 'active' : ''}
            onClick={() => setPeriod(p)}
          >
            {p === 'all_time' ? 'All Time' : p.charAt(0).toUpperCase() + p.slice(1)}
          </button>
        ))}
      </div>

      <div className="pnl-summary">
        <div className="pnl-item">
          <label>Total P&L:</label>
          <span className={periodData.pnl >= 0 ? 'positive' : 'negative'}>
            {periodData.pnl >= 0 ? '+' : ''}${periodData.pnl.toFixed(2)}
            <span className="roi"> ({periodData.roi >= 0 ? '+' : ''}{periodData.roi.toFixed(2)}%)</span>
          </span>
        </div>
        <div className="pnl-item">
          <label>Total Risk:</label>
          <span>${periodData.risk.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
        </div>
        <div className="pnl-item">
          <label>ROI:</label>
          <span className={periodData.roi >= 0 ? 'positive' : 'negative'}>
            {periodData.roi >= 0 ? '+' : ''}{periodData.roi.toFixed(2)}%
          </span>
        </div>
      </div>

      <div className="breakdown">
        <h3>Breakdown by Venue</h3>
        <div className="venue-breakdown">
          {Object.entries(pnl.by_venue).map(([venue, data]) => (
            <div key={venue} className="venue-item">
              <span className="venue-name">{venue.charAt(0).toUpperCase() + venue.slice(1)}:</span>
              <span className={data.pnl >= 0 ? 'positive' : 'negative'}>
                {data.pnl >= 0 ? '+' : ''}${data.pnl.toFixed(2)}
              </span>
              <span className="roi">(ROI: {data.roi >= 0 ? '+' : ''}{data.roi.toFixed(2)}%)</span>
            </div>
          ))}
        </div>

        <h3>Breakdown by Station</h3>
        <div className="station-breakdown">
          {Object.entries(pnl.by_station).map(([station, data]) => (
            <div key={station} className="station-item">
              <span className="station-name">{station}:</span>
              <span className={data.pnl >= 0 ? 'positive' : 'negative'}>
                {data.pnl >= 0 ? '+' : ''}${data.pnl.toFixed(2)}
              </span>
              <span className="roi">(ROI: {data.roi >= 0 ? '+' : ''}{data.roi.toFixed(2)}%)</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
```

#### 3.2 Testing

**Manual Testing**:
1. Test period selector
2. Test P&L display
3. Test breakdowns
4. Verify calculations

**Expected Results**:
- ✅ Period selector works
- ✅ P&L displays correctly
- ✅ Breakdowns are accurate
- ✅ Formatting is correct

---

### Stage 4: Performance Metrics Section

**Goal**: Display performance metrics (win rate, ROI, etc.)

**Estimated Time**: 2-3 hours

#### 4.1 Create Performance Metrics Component

**File**: `src/components/PerformanceMetrics.tsx`

**Implementation**:
```typescript
import React, { useState, useEffect } from 'react';
import { fetchMetrics, PerformanceMetrics as Metrics } from '../services/performanceApi';

interface PerformanceMetricsProps {
  mode: 'paper' | 'live';
}

export const PerformanceMetrics: React.FC<PerformanceMetricsProps> = ({ mode }) => {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMetrics();
  }, [mode]);

  const loadMetrics = async () => {
    setLoading(true);
    try {
      const data = await fetchMetrics(mode);
      setMetrics(data);
    } catch (err) {
      console.error('Failed to load metrics:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading metrics...</div>;
  if (!metrics) return <div>No metrics available</div>;

  return (
    <div className="performance-metrics">
      <h2>📊 Performance Metrics</h2>
      
      {mode === 'paper' && (
        <div className="warning">
          ⚠️ Theoretical Performance (Based on resolved outcomes)
        </div>
      )}

      {mode === 'live' && (
        <div className="info">
          ✅ Actual Performance (From real trade execution)
        </div>
      )}

      <div className="metrics-grid">
        <div className="metric-item">
          <label>Total Trades:</label>
          <span>{metrics.total_trades}</span>
        </div>
        <div className="metric-item">
          <label>Resolved:</label>
          <span>{metrics.resolved_trades} ({((metrics.resolved_trades / metrics.total_trades) * 100).toFixed(1)}%)</span>
        </div>
        <div className="metric-item">
          <label>Pending:</label>
          <span>{metrics.pending_trades} ({((metrics.pending_trades / metrics.total_trades) * 100).toFixed(1)}%)</span>
        </div>
        <div className="metric-item">
          <label>Win Rate:</label>
          <span className="highlight">{metrics.win_rate.toFixed(2)}% ({metrics.wins} wins / {metrics.resolved_trades} resolved)</span>
        </div>
        <div className="metric-item">
          <label>Average Edge:</label>
          <span>{metrics.avg_edge_pct.toFixed(2)}%</span>
        </div>
        <div className="metric-item">
          <label>ROI:</label>
          <span className={metrics.roi >= 0 ? 'positive' : 'negative'}>
            {metrics.roi >= 0 ? '+' : ''}{metrics.roi.toFixed(2)}%
          </span>
        </div>
        <div className="metric-item">
          <label>Sharpe Ratio:</label>
          <span>{metrics.sharpe_ratio.toFixed(2)}</span>
        </div>
        <div className="metric-item">
          <label>Largest Win:</label>
          <span className="positive">+${metrics.largest_win.toFixed(2)}</span>
        </div>
        <div className="metric-item">
          <label>Largest Loss:</label>
          <span className="negative">${metrics.largest_loss.toFixed(2)}</span>
        </div>
      </div>

      <div className="station-breakdown">
        <h3>By Station</h3>
        {Object.entries(metrics.by_station).map(([station, data]) => (
          <div key={station} className="station-metrics">
            <h4>{station}</h4>
            <div className="metrics-row">
              <span>Trades: {data.trades}</span>
              <span>Wins: {data.wins}</span>
              <span>Losses: {data.losses}</span>
              <span>Win Rate: {data.win_rate.toFixed(2)}%</span>
              <span>P&L: <span className={data.pnl >= 0 ? 'positive' : 'negative'}>{data.pnl >= 0 ? '+' : ''}${data.pnl.toFixed(2)}</span></span>
              <span>ROI: <span className={data.roi >= 0 ? 'positive' : 'negative'}>{data.roi >= 0 ? '+' : ''}{data.roi.toFixed(2)}%</span></span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
```

#### 4.2 Testing

**Manual Testing**:
1. Test metrics display
2. Test win rate calculation
3. Test station breakdowns
4. Verify all metrics are shown

**Expected Results**:
- ✅ All metrics display correctly
- ✅ Win rate is accurate
- ✅ Station breakdowns work
- ✅ Formatting is correct

---

### Stage 5: Trade History Table

**Goal**: Display trade history with filtering and pagination

**Estimated Time**: 4-5 hours

#### 5.1 Create Trade History Component

**File**: `src/components/TradeHistory.tsx`

**Implementation**:
```typescript
import React, { useState, useEffect } from 'react';
import { fetchTradeHistory, Trade, TradeHistoryResponse } from '../services/performanceApi';

interface TradeHistoryProps {
  mode: 'paper' | 'live';
}

export const TradeHistory: React.FC<TradeHistoryProps> = ({ mode }) => {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    start_date: '',
    end_date: '',
    station_code: '',
    venue: '',
    outcome: '',
  });
  const [pagination, setPagination] = useState({
    limit: 50,
    offset: 0,
  });

  useEffect(() => {
    loadTrades();
  }, [mode, filters, pagination]);

  const loadTrades = async () => {
    setLoading(true);
    try {
      const response = await fetchTradeHistory(mode, {
        ...filters,
        ...pagination,
      });
      setTrades(response.trades);
      setTotal(response.total);
    } catch (err) {
      console.error('Failed to load trades:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key: string, value: string) => {
    setFilters({ ...filters, [key]: value });
    setPagination({ ...pagination, offset: 0 }); // Reset to first page
  };

  const getOutcomeIcon = (outcome?: string) => {
    if (!outcome || outcome === 'pending') return '⏳';
    if (outcome === 'win') return '✅';
    if (outcome === 'loss') return '❌';
    return '❓';
  };

  const getOutcomeLabel = (outcome?: string) => {
    if (!outcome || outcome === 'pending') return 'Pending';
    if (outcome === 'win') return 'Win';
    if (outcome === 'loss') return 'Loss';
    return 'Unknown';
  };

  return (
    <div className="trade-history">
      <h2>📝 Trade History</h2>
      
      {mode === 'paper' && (
        <div className="warning">
          ⚠️ Simulated Trades - No Real Execution
        </div>
      )}

      {mode === 'live' && (
        <div className="info">
          ✅ Real Trades - Executed on Exchange
        </div>
      )}

      <div className="filters">
        <div className="filter-group">
          <label>Start Date:</label>
          <input
            type="date"
            value={filters.start_date}
            onChange={(e) => handleFilterChange('start_date', e.target.value)}
          />
        </div>
        <div className="filter-group">
          <label>End Date:</label>
          <input
            type="date"
            value={filters.end_date}
            onChange={(e) => handleFilterChange('end_date', e.target.value)}
          />
        </div>
        <div className="filter-group">
          <label>Station:</label>
          <select
            value={filters.station_code}
            onChange={(e) => handleFilterChange('station_code', e.target.value)}
          >
            <option value="">All</option>
            <option value="EGLC">EGLC</option>
            <option value="KLGA">KLGA</option>
            {/* Add more stations */}
          </select>
        </div>
        <div className="filter-group">
          <label>Venue:</label>
          <select
            value={filters.venue}
            onChange={(e) => handleFilterChange('venue', e.target.value)}
          >
            <option value="">All</option>
            <option value="polymarket">Polymarket</option>
            <option value="kalshi">Kalshi</option>
          </select>
        </div>
        <div className="filter-group">
          <label>Outcome:</label>
          <select
            value={filters.outcome}
            onChange={(e) => handleFilterChange('outcome', e.target.value)}
          >
            <option value="">All</option>
            <option value="win">Win</option>
            <option value="loss">Loss</option>
            <option value="pending">Pending</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div>Loading trades...</div>
      ) : (
        <>
          <div className="trade-table">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Station</th>
                  <th>Bracket</th>
                  <th>Size</th>
                  <th>Edge</th>
                  <th>Outcome</th>
                  <th>P&L</th>
                  <th>Venue</th>
                </tr>
              </thead>
              <tbody>
                {trades.map((trade, idx) => (
                  <tr key={idx}>
                    <td>{new Date(trade.timestamp).toLocaleString()}</td>
                    <td>{trade.station_code}</td>
                    <td>{trade.bracket_name}</td>
                    <td>${trade.size_usd.toFixed(2)}</td>
                    <td>{trade.edge_pct.toFixed(2)}%</td>
                    <td>
                      {getOutcomeIcon(trade.outcome)} {getOutcomeLabel(trade.outcome)}
                      {mode === 'paper' && <span className="badge">Paper</span>}
                      {mode === 'live' && <span className="badge">Live</span>}
                    </td>
                    <td className={trade.realized_pnl && trade.realized_pnl >= 0 ? 'positive' : 'negative'}>
                      {trade.realized_pnl !== null && trade.realized_pnl !== undefined
                        ? `${trade.realized_pnl >= 0 ? '+' : ''}$${trade.realized_pnl.toFixed(2)}`
                        : '-'}
                    </td>
                    <td>{trade.venue || 'polymarket'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="pagination">
            <button
              disabled={pagination.offset === 0}
              onClick={() => setPagination({ ...pagination, offset: pagination.offset - pagination.limit })}
            >
              ◀ Previous
            </button>
            <span>
              Showing {pagination.offset + 1}-{Math.min(pagination.offset + pagination.limit, total)} of {total} trades
            </span>
            <button
              disabled={pagination.offset + pagination.limit >= total}
              onClick={() => setPagination({ ...pagination, offset: pagination.offset + pagination.limit })}
            >
              Next ▶
            </button>
          </div>
        </>
      )}
    </div>
  );
};
```

#### 5.2 Testing

**Manual Testing**:
1. Test table display
2. Test filtering
3. Test pagination
4. Test sorting (if implemented)
5. Test outcome indicators

**Expected Results**:
- ✅ Table displays correctly
- ✅ Filters work
- ✅ Pagination works
- ✅ Outcome indicators are clear
- ✅ Mode badges are shown

---

## ✅ Implementation Checklist

### Backend/API
- [ ] **Stage 1**: Trade Resolution for Paper Trades
  - [ ] Enhance Trade schema
  - [ ] Create TradeResolutionService
  - [ ] Update TradeService
  - [ ] Create resolution endpoint
  - [ ] Test resolution

- [ ] **Stage 2**: P&L Aggregation Service
  - [ ] Create PnLService
  - [ ] Create P&L endpoint
  - [ ] Test aggregation

- [ ] **Stage 3**: Performance Metrics Service
  - [ ] Create PerformanceService
  - [ ] Create metrics endpoint
  - [ ] Test metrics

- [ ] **Stage 4**: Enhanced Trade History
  - [ ] Enhance trade history endpoint
  - [ ] Test filtering and pagination

### Frontend
- [ ] **Stage 1**: Basic Page Structure
  - [ ] Create PerformancePage component
  - [ ] Create API service
  - [ ] Test mode toggle

- [ ] **Stage 2**: Account Balances
  - [ ] Create AccountBalances component
  - [ ] Test paper mode
  - [ ] Prepare live mode placeholder

- [ ] **Stage 3**: P&L Dashboard
  - [ ] Create PnLDashboard component
  - [ ] Test period selector
  - [ ] Test breakdowns

- [ ] **Stage 4**: Performance Metrics
  - [ ] Create PerformanceMetrics component
  - [ ] Test metrics display

- [ ] **Stage 5**: Trade History Table
  - [ ] Create TradeHistory component
  - [ ] Test filtering
  - [ ] Test pagination

---

## 🚀 Future Enhancements

### Phase 2: Live Trading Support
- [ ] Account balance API integration (Polymarket)
- [ ] Account balance API integration (Kalshi)
- [ ] Live trade execution tracking
- [ ] Exchange settlement integration

### Phase 3: Advanced Features
- [ ] P&L over time chart
- [ ] Export to CSV/PDF
- [ ] Performance comparison (this month vs last month)
- [ ] Risk metrics (VaR, max drawdown)

---

**Total Estimated Time**: 20-30 hours

**Priority**: High (MVP feature for portfolio tracking)

