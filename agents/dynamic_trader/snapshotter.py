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
from core.types import EdgeDecision, MarketBracket, BracketProb
from agents.zeus_forecast import ZeusForecast
from venues.metar import MetarObservation


class DynamicSnapshotter:
    """Save timestamped snapshots of Zeus, Polymarket, decisions, and METAR."""
    
    def __init__(self):
        """Initialize snapshotter with directory structure."""
        self.base_dir = PROJECT_ROOT / "data" / "snapshots" / "dynamic"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Track which METAR observations we've already saved (by observation time)
        # Key: (station_code, obs_time_iso), Value: True
        self._saved_metar_obs: dict[tuple[str, str], bool] = {}
    
    def save_all(
        self,
        forecast: ZeusForecast,
        brackets: List[MarketBracket],
        prices: List[Optional[float]],
        decisions: List[EdgeDecision],
        cycle_time: datetime,
        event_day: date,
        station: Station,
        metar_observations: Optional[List[MetarObservation]] = None,
        probs: Optional[List[BracketProb]] = None,
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
            metar_observations: Optional METAR observations (only for today's events)
        """
        # Create timestamp string for filenames (UTC)
        timestamp = cycle_time.strftime("%Y-%m-%d_%H-%M-%S")
        
        # Save Zeus snapshot
        self._save_zeus(forecast, station, event_day, timestamp, cycle_time)
        
        # Save Polymarket snapshot
        self._save_polymarket(brackets, prices, station.city, event_day, timestamp, cycle_time)
        
        # Save decision snapshot (if any decisions made)
        if decisions:
            self._save_decisions(decisions, station, event_day, timestamp, cycle_time, probs)
        
        # Save METAR observations (only NEW ones, using observation time)
        if metar_observations:
            self._save_metar(metar_observations, station, event_day)
        
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
        probs: Optional[List[BracketProb]] = None,
    ):
        """Save trading decisions snapshot.
        
        Args:
            decisions: Trading decisions (positive edges only)
            station: Weather station
            event_day: Event date
            timestamp: Filename timestamp
            cycle_time: When cycle ran
            probs: Optional BracketProb list to look up p_zeus and p_mkt
        """
        decisions_dir = self.base_dir / "decisions" / station.station_code / event_day.isoformat()
        decisions_dir.mkdir(parents=True, exist_ok=True)
        
        snapshot_path = decisions_dir / f"{timestamp}.json"
        
        # Create mapping from market_id to BracketProb for lookup
        prob_map = {}
        if probs:
            for prob in probs:
                if prob.bracket.market_id:
                    prob_map[prob.bracket.market_id] = prob
        
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
                    "p_zeus": prob_map.get(decision.bracket.market_id).p_zeus if decision.bracket.market_id and prob_map.get(decision.bracket.market_id) else None,
                    "p_mkt": prob_map.get(decision.bracket.market_id).p_mkt if decision.bracket.market_id and prob_map.get(decision.bracket.market_id) else None,
                }
                for decision in decisions
            ],
        }
        
        with open(snapshot_path, "w") as f:
            json.dump(snapshot_data, f, indent=2)
        
        logger.debug(f"  💾 Decisions → {snapshot_path.name} ({len(decisions)} trades)")
    
    def _save_metar(
        self,
        observations: List[MetarObservation],
        station: Station,
        event_day: date,
    ):
        """Save METAR observations, only NEW ones (deduplicated by observation time).
        
        Uses observation time (not fetch time) for timestamping.
        Only saves observations we haven't seen before.
        
        Args:
            observations: List of METAR observations
            station: Weather station
            event_day: Event date
        """
        if not observations:
            return
        
        metar_dir = self.base_dir / "metar" / station.station_code / event_day.isoformat()
        metar_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing observation times from disk (for persistence across restarts)
        existing_obs_times = self._load_existing_metar_times(metar_dir)
        
        new_count = 0
        
        for obs in observations:
            # Use observation time (not fetch time) for filename
            obs_time_str = obs.time.strftime("%Y-%m-%d_%H-%M-%S")
            
            # Create unique key for deduplication
            obs_key = (station.station_code, obs.time.isoformat())
            
            # Skip if we've already saved this observation (in-memory)
            if obs_key in self._saved_metar_obs:
                logger.debug(f"  ⏭️  METAR: Skipping duplicate (in-memory) @ {obs_time_str}")
                continue
            
            # Skip if file already exists on disk
            snapshot_path = metar_dir / f"{obs_time_str}.json"
            if snapshot_path.exists() or obs.time.isoformat() in existing_obs_times:
                logger.debug(f"  ⏭️  METAR: Skipping duplicate (on disk) @ {obs_time_str}")
                self._saved_metar_obs[obs_key] = True
                continue
            
            # Save observation
            snapshot_data = {
                "observation_time_utc": obs.time.isoformat(),
                "fetch_time_utc": datetime.now(ZoneInfo("UTC")).isoformat(),
                "station_code": obs.station_code,
                "event_day": event_day.isoformat(),
                "temp_C": obs.temp_C,
                "temp_F": obs.temp_F,
                "dewpoint_C": obs.dewpoint_C,
                "wind_dir": obs.wind_dir,
                "wind_speed": obs.wind_speed,
                "raw": obs.raw,
            }
            
            with open(snapshot_path, "w") as f:
                json.dump(snapshot_data, f, indent=2)
            
            # Mark as saved
            self._saved_metar_obs[obs_key] = True
            existing_obs_times.add(obs.time.isoformat())
            new_count += 1
            
            logger.debug(f"  💾 METAR → {snapshot_path.name} ({obs.temp_F:.1f}°F)")
        
        if new_count > 0:
            logger.info(f"  ✅ METAR: Saved {new_count} new observation(s) for {station.city}")
    
    def _load_existing_metar_times(self, metar_dir: Path) -> set[str]:
        """Load existing METAR observation times from disk.
        
        Args:
            metar_dir: Directory containing METAR snapshots
        
        Returns:
            Set of observation time ISO strings
        """
        existing_times = set()
        
        if not metar_dir.exists():
            return existing_times
        
        for snapshot_file in metar_dir.glob("*.json"):
            try:
                with open(snapshot_file) as f:
                    data = json.load(f)
                    obs_time = data.get("observation_time_utc")
                    if obs_time:
                        existing_times.add(obs_time)
            except (json.JSONDecodeError, KeyError, IOError):
                # Skip invalid files
                continue
        
        return existing_times

