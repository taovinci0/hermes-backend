"""Pydantic models for API responses."""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ============================================================================
# Snapshot Models
# ============================================================================

class ForecastPoint(BaseModel):
    """Single forecast point."""
    time_utc: str
    temp_K: float


class ZeusSnapshot(BaseModel):
    """Zeus forecast snapshot."""
    fetch_time_utc: str
    forecast_for_local_day: str
    start_local: str
    station_code: str
    city: str
    timezone: str
    model_mode: Optional[str] = None
    timeseries_count: int
    timeseries: List[ForecastPoint]


class MarketPrice(BaseModel):
    """Market price data."""
    market_id: str
    bracket: str
    lower_f: int
    upper_f: int
    mid_price: Optional[float] = None
    closed: bool


class PolymarketSnapshot(BaseModel):
    """Polymarket pricing snapshot."""
    fetch_time_utc: str
    event_day: str
    city: str
    markets: List[MarketPrice]


class Decision(BaseModel):
    """Trading decision."""
    bracket: str
    lower_f: int
    upper_f: int
    market_id: str
    edge: float
    edge_pct: float
    f_kelly: float
    size_usd: float
    reason: str


class DecisionSnapshot(BaseModel):
    """Decision snapshot."""
    decision_time_utc: str
    event_day: str
    station_code: str
    city: str
    model_mode: Optional[str] = None
    trade_count: int
    decisions: List[Decision]


# ============================================================================
# Trade Models
# ============================================================================

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
    # P&L tracking fields
    outcome: Optional[str] = None  # 'win', 'loss', 'pending'
    realized_pnl: Optional[float] = None
    venue: Optional[str] = None  # 'polymarket', 'kalshi'
    resolved_at: Optional[str] = None
    winner_bracket: Optional[str] = None


# ============================================================================
# API Response Models
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    version: str = "1.0.0"


class SnapshotListResponse(BaseModel):
    """Response for listing snapshots."""
    snapshots: List[Dict[str, Any]]
    count: int


class TradeListResponse(BaseModel):
    """Response for listing trades."""
    trades: List[Trade]
    count: int
    total_size_usd: float

