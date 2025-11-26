"""Backend service for METAR data access and comparison.

Reads METAR observations from snapshots (saved by dynamic trading engine).
Does NOT call the METAR API directly, as the API only returns recent data.
Historical METAR data is preserved via snapshots taken during trading cycles.

Snapshots are stored in: data/snapshots/dynamic/metar/{station}/{event_day}/
Each observation is saved with its observation_time_utc for historical accuracy.
"""

from datetime import date, datetime
from typing import List, Optional, Dict, Any
from functools import lru_cache

from ..services.snapshot_service import SnapshotService
from ..utils.file_utils import parse_timestamp


class MetarService:
    """Backend service for METAR data access."""
    
    def __init__(self):
        """Initialize METAR service."""
        self.snapshot_service = SnapshotService()
        # Cache for daily highs (key: (station_code, event_day), value: temp_F)
        self._daily_high_cache: Dict[tuple[str, str], float] = {}
    
    def get_observations(
        self,
        station_code: str,
        event_day: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """Get METAR observations from snapshots.
        
        Args:
            station_code: Station code (e.g., "EGLC")
            event_day: Optional date filter (YYYY-MM-DD)
            
        Returns:
            List of observation dictionaries sorted by observation time
        """
        snapshots = self.snapshot_service.get_metar_snapshots(
            station_code=station_code,
            event_day=event_day,
        )
        
        # Sort by observation time
        snapshots.sort(
            key=lambda s: parse_timestamp(s.get("observation_time_utc", "")) or datetime.min
        )
        
        return snapshots
    
    def get_daily_high(
        self,
        station_code: str,
        event_day: Optional[date] = None,
        use_cache: bool = True,
    ) -> Optional[float]:
        """Get daily high temperature from METAR observations.
        
        Args:
            station_code: Station code (e.g., "EGLC")
            event_day: Date (defaults to today)
            use_cache: Whether to use cache (default True)
            
        Returns:
            Daily high temperature in Fahrenheit, or None if no data
        """
        if event_day is None:
            event_day = date.today()
        
        cache_key = (station_code, event_day.isoformat())
        
        # Check cache
        if use_cache and cache_key in self._daily_high_cache:
            return self._daily_high_cache[cache_key]
        
        # Get observations
        observations = self.get_observations(
            station_code=station_code,
            event_day=event_day,
        )
        
        if not observations:
            return None
        
        # CRITICAL: Filter to only include observations within event day (00:00-23:59 UTC)
        # This ensures we don't include late-night observations from previous day
        filtered_observations = []
        for obs in observations:
            obs_time_str = obs.get("observation_time_utc", "")
            if not obs_time_str:
                continue
            
            obs_time = parse_timestamp(obs_time_str)
            if obs_time is None:
                continue
            
            # Only include if observation date matches event day (UTC)
            if obs_time.date() == event_day:
                filtered_observations.append(obs)
        
        if not filtered_observations:
            return None
        
        # Extract temperatures from filtered observations
        temps = [
            obs.get("temp_F")
            for obs in filtered_observations
            if obs.get("temp_F") is not None
        ]
        
        if not temps:
            return None
        
        daily_high = max(temps)
        
        # Cache result
        if use_cache:
            self._daily_high_cache[cache_key] = daily_high
        
        return round(daily_high, 1)
    
    def compare_zeus_vs_metar(
        self,
        station_code: str,
        event_day: Optional[date] = None,
        feature_toggles: Optional[Any] = None,  # NEW: FeatureToggles (using Any to avoid import issues)
    ) -> Optional[Dict[str, Any]]:
        """Compare Zeus forecast vs METAR actual temperature.
        
        Args:
            station_code: Station code (e.g., "EGLC")
            event_day: Date (defaults to today)
            
        Returns:
            Comparison dictionary with predictions, actual, error, etc.
            Returns None if data is not available
        """
        if event_day is None:
            event_day = date.today()
        
        # Get METAR daily high
        metar_high = self.get_daily_high(station_code, event_day)
        if metar_high is None:
            return None
        
        # Get latest Zeus forecast for this event day
        zeus_snapshots = self.snapshot_service.get_zeus_snapshots(
            station_code=station_code,
            event_day=event_day,
            limit=1,  # Get most recent
        )
        
        if not zeus_snapshots:
            return None
        
        zeus_snapshot = zeus_snapshots[0]
        
        # Extract Zeus daily high (max of hourly temps)
        timeseries = zeus_snapshot.get("timeseries", [])
        if not timeseries:
            return None
        
        # Apply calibration if enabled
        if feature_toggles and feature_toggles.station_calibration:
            from core.station_calibration import StationCalibration
            from core import units
            from datetime import datetime
            
            calibration = StationCalibration()
            
            # Extract temps and timestamps, apply calibration
            calibrated_temps_f = []
            for point in timeseries:
                # Try to get temp_K first (preferred), fall back to temp_F
                temp_k = point.get("temp_K")
                if temp_k is None:
                    # Convert from temp_F if temp_K not available
                    temp_f = point.get("temp_F")
                    if temp_f is None:
                        continue
                    temp_k = units.fahrenheit_to_kelvin(temp_f)
                
                # Get timestamp
                time_utc_str = point.get("time_utc")
                if not time_utc_str:
                    continue
                
                try:
                    # Parse timestamp (handle both with and without timezone)
                    if time_utc_str.endswith("Z"):
                        timestamp = datetime.fromisoformat(time_utc_str.replace("Z", "+00:00"))
                    else:
                        timestamp = datetime.fromisoformat(time_utc_str)
                except (ValueError, AttributeError):
                    continue
                
                # Apply calibration
                temp_c = units.kelvin_to_celsius(temp_k)
                temp_c_corrected = calibration.apply(temp_c, station_code, timestamp)
                temp_k_corrected = units.celsius_to_kelvin(temp_c_corrected)
                temp_f_corrected = units.kelvin_to_fahrenheit(temp_k_corrected)
                
                calibrated_temps_f.append(temp_f_corrected)
            
            if calibrated_temps_f:
                zeus_high = max(calibrated_temps_f)
            else:
                # Fallback to original method if calibration failed
                zeus_temps = [
                    point.get("temp_F")
                    for point in timeseries
                    if point.get("temp_F") is not None
                ]
                if not zeus_temps:
                    return None
                zeus_high = max(zeus_temps)
        else:
            # No calibration - use original method
            zeus_temps = [
                point.get("temp_F")
                for point in timeseries
                if point.get("temp_F") is not None
            ]
            
            if not zeus_temps:
                return None
            
            zeus_high = max(zeus_temps)
        
        # Calculate error
        error_f = zeus_high - metar_high
        error_pct = (error_f / metar_high * 100) if metar_high != 0 else 0.0
        
        # Determine which bracket each falls into (if brackets available)
        zeus_bracket = None
        metar_bracket = None
        
        # Try to get brackets from decision snapshots
        decision_snapshots = self.snapshot_service.get_decision_snapshots(
            station_code=station_code,
            event_day=event_day,
            limit=1,
        )
        
        if decision_snapshots:
            decisions = decision_snapshots[0].get("decisions", [])
            if decisions:
                # Find bracket for Zeus prediction
                for decision in decisions:
                    lower = decision.get("lower_f")
                    upper = decision.get("upper_f")
                    if lower is not None and upper is not None:
                        if lower <= zeus_high < upper:
                            zeus_bracket = decision.get("bracket")
                            break
                
                # Find bracket for METAR actual
                for decision in decisions:
                    lower = decision.get("lower_f")
                    upper = decision.get("upper_f")
                    if lower is not None and upper is not None:
                        if lower <= metar_high < upper:
                            metar_bracket = decision.get("bracket")
                            break
        
        return {
            "station_code": station_code,
            "event_day": event_day.isoformat(),
            "zeus_prediction_f": round(zeus_high, 1),
            "metar_actual_f": round(metar_high, 1),
            "error_f": round(error_f, 1),
            "error_pct": round(error_pct, 2),
            "zeus_bracket": zeus_bracket,
            "metar_bracket": metar_bracket,
            "brackets_match": zeus_bracket == metar_bracket if zeus_bracket and metar_bracket else None,
            "zeus_forecast_time": zeus_snapshot.get("fetch_time_utc"),
            "metar_observation_count": len(self.get_observations(station_code, event_day)),
        }
    
    def clear_cache(self):
        """Clear the daily high cache."""
        self._daily_high_cache.clear()

