"""Service for reading snapshot files."""

from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import date, datetime
import sys

from ..utils.path_utils import get_snapshots_dir
from ..utils.file_utils import read_json_file, list_json_files, parse_timestamp
from ..models.schemas import ZeusSnapshot, PolymarketSnapshot, DecisionSnapshot

# Import feature toggles and calibration
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from core.feature_toggles import FeatureToggles
from core.station_calibration import StationCalibration
from core import units


class SnapshotService:
    """Service for reading Zeus, Polymarket, and Decision snapshots."""
    
    def __init__(self):
        """Initialize snapshot service."""
        self.snapshots_dir = get_snapshots_dir()
    
    def get_zeus_snapshots(
        self,
        station_code: str,
        event_day: Optional[date] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get Zeus forecast snapshots for a station.
        
        Applies station calibration if enabled via feature toggles.
        
        Args:
            station_code: Station code (e.g., "EGLC")
            event_day: Optional date filter (YYYY-MM-DD)
            limit: Optional limit on number of snapshots
            
        Returns:
            List of snapshot dictionaries (with calibration applied if enabled)
        """
        zeus_dir = self.snapshots_dir / "zeus" / station_code
        
        if event_day:
            zeus_dir = zeus_dir / event_day.isoformat()
        
        if not zeus_dir.exists():
            return []
        
        files = list_json_files(zeus_dir)
        
        # Sort by filename (which includes timestamp) descending
        files.sort(reverse=True)
        
        if limit:
            files = files[:limit]
        
        # Load feature toggles to check if calibration is enabled
        feature_toggles = FeatureToggles.load()
        calibration_enabled = feature_toggles.station_calibration
        
        # Initialize calibration if enabled
        calibration = None
        if calibration_enabled:
            calibration = StationCalibration()
            if not calibration.has_calibration(station_code):
                # No calibration available for this station, disable
                calibration_enabled = False
        
        snapshots = []
        for file_path in files:
            data = read_json_file(file_path)
            if data:
                # Add filename for reference
                data["_filename"] = file_path.name
                
                # Apply calibration if enabled
                if calibration_enabled and calibration:
                    data = self._apply_calibration_to_snapshot(
                        data, station_code, calibration
                    )
                
                snapshots.append(data)
        
        return snapshots
    
    def _apply_calibration_to_snapshot(
        self,
        snapshot: Dict[str, Any],
        station_code: str,
        calibration: StationCalibration,
    ) -> Dict[str, Any]:
        """Apply station calibration to a Zeus snapshot.
        
        Args:
            snapshot: Raw snapshot dictionary
            station_code: Station code for calibration lookup
            calibration: StationCalibration instance
            
        Returns:
            Snapshot dictionary with calibrated temperatures
        """
        # Create a copy to avoid modifying the original
        calibrated_snapshot = snapshot.copy()
        
        # Get timeseries
        timeseries = calibrated_snapshot.get("timeseries", [])
        if not timeseries:
            return calibrated_snapshot
        
        # Extract temperatures and timestamps
        temps_k = []
        timestamps = []
        for point in timeseries:
            # Try to get temp_K first (preferred)
            temp_k = point.get("temp_K")
            if temp_k is None:
                # Fall back to temp_F and convert
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
                if isinstance(time_utc_str, str):
                    if time_utc_str.endswith("Z"):
                        timestamp = datetime.fromisoformat(time_utc_str.replace("Z", "+00:00"))
                    else:
                        timestamp = datetime.fromisoformat(time_utc_str)
                elif isinstance(time_utc_str, datetime):
                    timestamp = time_utc_str
                else:
                    continue
            except (ValueError, AttributeError, TypeError):
                continue
            
            temps_k.append(temp_k)
            timestamps.append(timestamp)
        
        # Apply calibration to timeseries
        if temps_k and len(temps_k) == len(timestamps):
            calibrated_temps_k = calibration.apply_to_forecast_timeseries(
                temps_k, timestamps, station_code
            )
            
            # Update timeseries with calibrated temperatures
            calibrated_temps_f = []
            for i, point in enumerate(timeseries):
                if i < len(calibrated_temps_k):
                    temp_k_calibrated = calibrated_temps_k[i]
                    temp_f_calibrated = units.kelvin_to_fahrenheit(temp_k_calibrated)
                    
                    # Update both temp_K and temp_F in the point
                    point["temp_K"] = temp_k_calibrated
                    point["temp_F"] = temp_f_calibrated
                    
                    calibrated_temps_f.append(temp_f_calibrated)
            
            # Recalculate predicted_high_F from calibrated temperatures
            if calibrated_temps_f:
                calibrated_snapshot["predicted_high_F"] = max(calibrated_temps_f)
        
        return calibrated_snapshot
    
    def get_polymarket_snapshots(
        self,
        city: str,
        event_day: Optional[date] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get Polymarket pricing snapshots for a city.
        
        Args:
            city: City name (e.g., "London")
            event_day: Optional date filter (YYYY-MM-DD)
            limit: Optional limit on number of snapshots
            
        Returns:
            List of snapshot dictionaries
        """
        # City name might have spaces, replace with underscore
        city_clean = city.replace(" ", "_")
        poly_dir = self.snapshots_dir / "polymarket" / city_clean
        
        if event_day:
            poly_dir = poly_dir / event_day.isoformat()
        
        if not poly_dir.exists():
            return []
        
        files = list_json_files(poly_dir)
        files.sort(reverse=True)
        
        if limit:
            files = files[:limit]
        
        snapshots = []
        for file_path in files:
            data = read_json_file(file_path)
            if data:
                data["_filename"] = file_path.name
                snapshots.append(data)
        
        return snapshots
    
    def get_decision_snapshots(
        self,
        station_code: str,
        event_day: Optional[date] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get decision snapshots for a station.
        
        Args:
            station_code: Station code (e.g., "EGLC")
            event_day: Optional date filter (YYYY-MM-DD)
            limit: Optional limit on number of snapshots
            
        Returns:
            List of snapshot dictionaries
        """
        decision_dir = self.snapshots_dir / "decisions" / station_code
        
        if event_day:
            decision_dir = decision_dir / event_day.isoformat()
        
        if not decision_dir.exists():
            return []
        
        files = list_json_files(decision_dir)
        files.sort(reverse=True)
        
        if limit:
            files = files[:limit]
        
        snapshots = []
        for file_path in files:
            data = read_json_file(file_path)
            if data:
                data["_filename"] = file_path.name
                snapshots.append(data)
        
        return snapshots
    
    def get_metar_snapshots(
        self,
        station_code: str,
        event_day: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """Get METAR observation snapshots for a station.
        
        Args:
            station_code: Station code (e.g., "EGLC")
            event_day: Optional date filter (YYYY-MM-DD)
            
        Returns:
            List of snapshot dictionaries
        """
        # METAR snapshots are stored in dynamic/metar/{station_code}/{event_day}/
        # Check both locations: dynamic/metar and metar (for backward compatibility)
        metar_dirs = [
            self.snapshots_dir / "dynamic" / "metar" / station_code,
            self.snapshots_dir / "metar" / station_code,
        ]
        
        if event_day:
            metar_dirs = [
                d / event_day.isoformat() if d.exists() else None
                for d in metar_dirs
            ]
            metar_dirs = [d for d in metar_dirs if d is not None]
        
        all_files = []
        for metar_dir in metar_dirs:
            if metar_dir.exists():
                files = list_json_files(metar_dir)
                all_files.extend(files)
        
        # Remove duplicates (by filename)
        seen = set()
        unique_files = []
        for file_path in all_files:
            if file_path.name not in seen:
                seen.add(file_path.name)
                unique_files.append(file_path)
        
        unique_files.sort()  # Sort ascending (by observation time)
        
        snapshots = []
        for file_path in unique_files:
            data = read_json_file(file_path)
            if data:
                data["_filename"] = file_path.name
                snapshots.append(data)
        
        return snapshots

