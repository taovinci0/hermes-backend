"""Save timestamped snapshots for replay backtesting.

Stores Zeus forecasts, Polymarket pricing, and trading decisions
with precise timestamps to enable accurate historical replay.
"""

import json
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional
from zoneinfo import ZoneInfo

from core.config import config, PROJECT_ROOT
from core.logger import logger
from core.registry import Station
from core.types import EdgeDecision, MarketBracket
from agents.zeus_forecast import ZeusForecast


class DynamicSnapshotter:
    """Save timestamped snapshots of Zeus, Polymarket, and decisions."""
    
    def __init__(self):
        """Initialize snapshotter with directory structure."""
        self.base_dir = PROJECT_ROOT / "data" / "snapshots" / "dynamic"
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def save_all(
        self,
        forecast: ZeusForecast,
        brackets: List[MarketBracket],
        prices: List[Optional[float]],
        decisions: List[EdgeDecision],
        cycle_time: datetime,
        event_day: date,
        station: Station,
    ):
        """Save complete snapshot for this evaluation cycle.
        
        Args:
            forecast: Zeus forecast
            brackets: Market brackets
            prices: Market prices (aligned with brackets)
            decisions: Trading decisions (only positive edges)
            cycle_time: When this cycle ran (UTC)
            event_day: Event date
            station: Weather station
        """
        # Create timestamp string for filenames (UTC)
        timestamp = cycle_time.strftime("%Y-%m-%d_%H-%M-%S")
        
        # Save Zeus snapshot
        self._save_zeus(forecast, station, event_day, timestamp, cycle_time)
        
        # Save Polymarket snapshot
        self._save_polymarket(brackets, prices, station.city, event_day, timestamp, cycle_time)
        
        # Save decision snapshot (if any decisions made)
        if decisions:
            self._save_decisions(decisions, station, event_day, timestamp, cycle_time)
        
        logger.debug(f"💾 Saved snapshots for {station.city} {event_day} @ {timestamp}")
    
    def _save_zeus(
        self,
        forecast: ZeusForecast,
        station: Station,
        event_day: date,
        timestamp: str,
        cycle_time: datetime,
    ):
        """Save Zeus forecast snapshot with metadata.
        
        Args:
            forecast: Zeus forecast object
            station: Weather station
            event_day: Event date
            timestamp: Filename timestamp
            cycle_time: When cycle ran
        """
        zeus_dir = self.base_dir / "zeus" / station.station_code / event_day.isoformat()
        zeus_dir.mkdir(parents=True, exist_ok=True)
        
        snapshot_path = zeus_dir / f"{timestamp}.json"
        
        # Get first timestamp to determine local start time
        if forecast.timeseries:
            first_point = forecast.timeseries[0]
            # Convert to station's local time
            local_start = first_point.time_utc.astimezone(ZoneInfo(station.time_zone))
        else:
            local_start = None
        
        snapshot_data = {
            "fetch_time_utc": cycle_time.isoformat(),
            "forecast_for_local_day": event_day.isoformat(),
            "start_local": local_start.isoformat() if local_start else None,
            "station_code": station.station_code,
            "city": station.city,
            "timezone": station.time_zone,
            "model_mode": config.model_mode,
            "timeseries_count": len(forecast.timeseries),
            "timeseries": [
                {
                    "time_utc": point.time_utc.isoformat(),
                    "temp_K": point.temp_K,
                }
                for point in forecast.timeseries
            ],
        }
        
        with open(snapshot_path, "w") as f:
            json.dump(snapshot_data, f, indent=2)
        
        logger.debug(f"  💾 Zeus → {snapshot_path.name}")
    
    def _save_polymarket(
        self,
        brackets: List[MarketBracket],
        prices: List[Optional[float]],
        city: str,
        event_day: date,
        timestamp: str,
        cycle_time: datetime,
    ):
        """Save Polymarket pricing snapshot.
        
        Args:
            brackets: Market brackets
            prices: Current prices (aligned with brackets)
            city: City name
            event_day: Event date
            timestamp: Filename timestamp
            cycle_time: When cycle ran
        """
        poly_dir = self.base_dir / "polymarket" / city.replace(" ", "_") / event_day.isoformat()
        poly_dir.mkdir(parents=True, exist_ok=True)
        
        snapshot_path = poly_dir / f"{timestamp}.json"
        
        snapshot_data = {
            "fetch_time_utc": cycle_time.isoformat(),
            "event_day": event_day.isoformat(),
            "city": city,
            "markets": [
                {
                    "market_id": bracket.market_id,
                    "bracket": bracket.name,
                    "lower_f": bracket.lower_F,
                    "upper_f": bracket.upper_F,
                    "mid_price": price,
                    "closed": bracket.closed,
                }
                for bracket, price in zip(brackets, prices)
            ],
        }
        
        with open(snapshot_path, "w") as f:
            json.dump(snapshot_data, f, indent=2)
        
        logger.debug(f"  💾 Polymarket → {snapshot_path.name}")
    
    def _save_decisions(
        self,
        decisions: List[EdgeDecision],
        station: Station,
        event_day: date,
        timestamp: str,
        cycle_time: datetime,
    ):
        """Save trading decisions snapshot.
        
        Args:
            decisions: Trading decisions (positive edges only)
            station: Weather station
            event_day: Event date
            timestamp: Filename timestamp
            cycle_time: When cycle ran
        """
        decisions_dir = self.base_dir / "decisions" / station.station_code / event_day.isoformat()
        decisions_dir.mkdir(parents=True, exist_ok=True)
        
        snapshot_path = decisions_dir / f"{timestamp}.json"
        
        snapshot_data = {
            "decision_time_utc": cycle_time.isoformat(),
            "event_day": event_day.isoformat(),
            "station_code": station.station_code,
            "city": station.city,
            "model_mode": config.model_mode,
            "trade_count": len(decisions),
            "decisions": [
                {
                    "bracket": decision.bracket.name,
                    "lower_f": decision.bracket.lower_F,
                    "upper_f": decision.bracket.upper_F,
                    "market_id": decision.bracket.market_id,
                    "edge": decision.edge,
                    "edge_pct": decision.edge * 100,
                    "f_kelly": decision.f_kelly,
                    "size_usd": decision.size_usd,
                    "reason": decision.reason,
                }
                for decision in decisions
            ],
        }
        
        with open(snapshot_path, "w") as f:
            json.dump(snapshot_data, f, indent=2)
        
        logger.debug(f"  💾 Decisions → {snapshot_path.name} ({len(decisions)} trades)")

