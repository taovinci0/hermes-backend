"""Type definitions for Hermes.

Pydantic models for structured data throughout the pipeline.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ForecastPoint(BaseModel):
    """Single point in a temperature forecast timeseries."""

    time_utc: datetime = Field(description="Forecast timestamp in UTC")
    temp_K: float = Field(description="Temperature in Kelvin")


class ZeusForecast(BaseModel):
    """Complete Zeus weather forecast for a location."""

    timeseries: list[ForecastPoint] = Field(description="Hourly forecast points")
    station_code: str = Field(description="Weather station identifier")
    fetch_time: datetime = Field(
        default_factory=datetime.utcnow, description="When this forecast was retrieved"
    )


class MarketBracket(BaseModel):
    """Temperature bracket for a prediction market.

    Upper bound is exclusive, e.g., [59-60) means 59.0 <= temp < 60.0
    """

    name: str = Field(description="Bracket display name, e.g., '59-60°F'")
    lower_F: int = Field(description="Lower bound in °F (inclusive)")
    upper_F: int = Field(description="Upper bound in °F (exclusive)")
    market_id: Optional[str] = Field(default=None, description="Market ID for resolution (Gamma API)")
    token_id: Optional[str] = Field(default=None, description="CLOB token ID for pricing (CLOB API)")
    closed: Optional[bool] = Field(default=None, description="Whether market is closed/resolved")


class BracketProb(BaseModel):
    """Probability assessment for a market bracket."""

    bracket: MarketBracket
    p_zeus: float = Field(description="Zeus-derived probability (0-1)")
    p_mkt: Optional[float] = Field(
        default=None, description="Market-implied probability (0-1)"
    )
    sigma_z: Optional[float] = Field(
        default=None, description="Zeus forecast uncertainty (std dev in °F)"
    )


class EdgeDecision(BaseModel):
    """Trading decision with edge calculation and sizing."""

    bracket: MarketBracket
    edge: float = Field(description="Expected edge (p_zeus - p_mkt - fees)")
    f_kelly: float = Field(description="Kelly fraction (pre-caps)")
    size_usd: float = Field(description="Actual position size in USD")
    reason: str = Field(default="", description="Decision explanation")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

