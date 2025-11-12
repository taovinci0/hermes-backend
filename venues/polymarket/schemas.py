"""Polymarket API schemas and DTOs.

Stage 4 implementation.
"""

from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, Field


class GammaEvent(BaseModel):
    """Gamma API event response."""

    id: str
    slug: str
    title: str
    description: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    markets: Optional[List[str]] = Field(default_factory=list)
    active: Optional[bool] = True


class GammaMarket(BaseModel):
    """Gamma API market response."""

    id: str
    question: str
    slug: Optional[str] = None
    condition_id: str
    outcome: Optional[str] = None
    event_slug: Optional[str] = None
    end_date_iso: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = True
    closed: Optional[bool] = False
    archived: Optional[bool] = False
    accepting_orders: Optional[bool] = True
    tokens: Optional[List[dict]] = Field(default_factory=list)


class CLOBToken(BaseModel):
    """CLOB token information."""

    token_id: str
    outcome: str
    price: Optional[float] = None
    winner: Optional[bool] = None


class CLOBBook(BaseModel):
    """CLOB order book side (bids or asks)."""

    price: str
    size: str


class CLOBOrderBook(BaseModel):
    """CLOB order book response."""

    market: str
    asset_id: Optional[str] = None
    bids: List[CLOBBook] = Field(default_factory=list)
    asks: List[CLOBBook] = Field(default_factory=list)
    timestamp: Optional[int] = None


class CLOBMidpoint(BaseModel):
    """CLOB midpoint price."""

    mid: Optional[float] = None
    market: Optional[str] = None


class PriceHistoryPoint(BaseModel):
    """Single point in price history."""

    t: int = Field(description="Timestamp (Unix seconds)")
    p: float = Field(description="Price (0-1)")


class PriceHistory(BaseModel):
    """Price history response from CLOB."""

    history: List[PriceHistoryPoint] = Field(default_factory=list)
    market: Optional[str] = None


class MarketDepth(BaseModel):
    """Aggregated market depth/liquidity."""

    token_id: str
    bid_depth_usd: float = Field(default=0.0, description="Total USD on bid side")
    ask_depth_usd: float = Field(default=0.0, description="Total USD on ask side")
    spread_bps: Optional[float] = Field(default=None, description="Spread in basis points")
    mid_price: Optional[float] = None

