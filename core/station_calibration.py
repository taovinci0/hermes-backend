"""Station calibration system - loads and applies ERA5 bias corrections.

Loads calibration models from per-station JSON files and applies
month/hour-specific bias corrections + elevation offsets to Zeus predictions.
"""

from typing import Optional, Dict
from datetime import datetime
import json
from pathlib import Path
import logging

from .config import PROJECT_ROOT
from .logger import logger

logger = logging.getLogger(__name__)


class StationCalibration:
    """Load and apply station-specific bias corrections from ERA5 analysis."""
    
    def __init__(self, calibration_dir: Optional[Path] = None):
        """Initialize station calibration system.
        
        Args:
            calibration_dir: Optional path to calibration directory
                            (defaults to data/calibration/)
        """
        if calibration_dir is None:
            calibration_dir = PROJECT_ROOT / "data" / "calibration"
        
        self.calibration_dir = calibration_dir
        self._models: Dict[str, dict] = {}
        self._load_all()
    
    def _load_all(self) -> None:
        """Load all calibration models from directory."""
        if not self.calibration_dir.exists():
            logger.warning(
                f"Calibration directory not found: {self.calibration_dir}. "
                "No calibrations will be applied."
            )
            return
        
        # Look for station_calibration_*.json files
        pattern = "station_calibration_*.json"
        calibration_files = list(self.calibration_dir.glob(pattern))
        
        if not calibration_files:
            logger.warning(
                f"No calibration files found in {self.calibration_dir}. "
                "No calibrations will be applied."
            )
            return
        
        for calib_file in calibration_files:
            try:
                with open(calib_file) as f:
                    model = json.load(f)
                
                station_code = model.get("station", "").upper()
                if not station_code:
                    logger.warning(
                        f"Calibration file {calib_file} missing 'station' field, skipping"
                    )
                    continue
                
                # Validate required fields
                if "bias_model" not in model:
                    logger.warning(
                        f"Calibration file {calib_file} missing 'bias_model' field, skipping"
                    )
                    continue
                
                if "bias_matrix_smoothed" not in model["bias_model"]:
                    logger.warning(
                        f"Calibration file {calib_file} missing 'bias_matrix_smoothed', skipping"
                    )
                    continue
                
                if "elevation" not in model:
                    logger.warning(
                        f"Calibration file {calib_file} missing 'elevation' field, skipping"
                    )
                    continue
                
                self._models[station_code] = model
                version = model.get("version", "unknown")
                logger.info(
                    f"Loaded calibration model for {station_code} "
                    f"(version {version}) from {calib_file.name}"
                )
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in {calib_file}: {e}")
            except Exception as e:
                logger.error(f"Failed to load calibration from {calib_file}: {e}")
        
        logger.info(f"Loaded {len(self._models)} station calibration model(s)")
    
    def has_calibration(self, station_code: str) -> bool:
        """Check if calibration exists for a station.
        
        Args:
            station_code: Station code (e.g., "EGLC")
            
        Returns:
            True if calibration model exists for this station
        """
        return station_code.upper() in self._models
    
    def get_correction(
        self, 
        station_code: str, 
        month: int, 
        hour: int
    ) -> Optional[float]:
        """Get total correction (bias + elevation) for a station/month/hour.
        
        Args:
            station_code: Station code (e.g., "EGLC")
            month: Month (1-12, where 1=January)
            hour: Hour (0-23)
            
        Returns:
            Total correction in °C, or None if calibration not available
        """
        model = self._models.get(station_code.upper())
        if not model:
            return None
        
        try:
            # Get bias from smoothed matrix (recommended)
            bias_matrix = model["bias_model"]["bias_matrix_smoothed"]
            
            # Validate indices
            if not (1 <= month <= 12):
                logger.warning(f"Invalid month: {month}, must be 1-12")
                return None
            if not (0 <= hour <= 23):
                logger.warning(f"Invalid hour: {hour}, must be 0-23")
                return None
            
            # Validate matrix dimensions
            if len(bias_matrix) != 12:
                logger.error(
                    f"Bias matrix has {len(bias_matrix)} rows, expected 12 (months)"
                )
                return None
            
            if len(bias_matrix[month - 1]) != 24:
                logger.error(
                    f"Bias matrix month {month} has {len(bias_matrix[month - 1])} columns, "
                    "expected 24 (hours)"
                )
                return None
            
            # Get bias (month-1 because array is 0-indexed)
            bias = bias_matrix[month - 1][hour]
            
            # Get elevation offset
            elevation_offset = model["elevation"]["elevation_offset_c"]
            
            # Total correction
            total_correction = bias + elevation_offset
            
            return total_correction
            
        except (KeyError, IndexError, TypeError) as e:
            logger.error(
                f"Error accessing calibration model for {station_code}: {e}"
            )
            return None
    
    def apply(
        self, 
        temp_c: float, 
        station_code: str, 
        timestamp: datetime
    ) -> float:
        """Apply calibration to a temperature prediction.
        
        Args:
            temp_c: Temperature in Celsius (from Zeus/ERA5)
            station_code: Station code
            timestamp: Datetime for month/hour lookup
            
        Returns:
            Corrected temperature in Celsius
        """
        if not self.has_calibration(station_code):
            return temp_c
        
        month = timestamp.month  # 1-12
        hour = timestamp.hour    # 0-23
        
        correction = self.get_correction(station_code, month, hour)
        if correction is None:
            return temp_c
        
        corrected_temp_c = temp_c + correction
        
        logger.debug(
            f"Applied calibration to {station_code}: "
            f"{temp_c:.2f}°C + {correction:.4f}°C = {corrected_temp_c:.2f}°C "
            f"(month={month}, hour={hour})"
        )
        
        return corrected_temp_c
    
    def apply_to_forecast_timeseries(
        self,
        temps_k: list[float],
        timestamps: list[datetime],
        station_code: str,
    ) -> list[float]:
        """Apply calibration to a list of temperatures with timestamps.
        
        Args:
            temps_k: List of temperatures in Kelvin
            timestamps: List of datetime objects (same length as temps_k)
            station_code: Station code
            
        Returns:
            List of corrected temperatures in Kelvin
        """
        from . import units
        
        if not self.has_calibration(station_code):
            return temps_k
        
        if len(temps_k) != len(timestamps):
            logger.warning(
                f"Mismatch: {len(temps_k)} temperatures but {len(timestamps)} timestamps"
            )
            return temps_k
        
        corrected_temps_k = []
        for temp_k, ts in zip(temps_k, timestamps):
            # Convert to Celsius
            temp_c = units.kelvin_to_celsius(temp_k)
            
            # Apply correction
            corrected_temp_c = self.apply(temp_c, station_code, ts)
            
            # Convert back to Kelvin
            corrected_temp_k = units.celsius_to_kelvin(corrected_temp_c)
            corrected_temps_k.append(corrected_temp_k)
        
        logger.debug(
            f"Applied calibration to {len(corrected_temps_k)} forecast points "
            f"for {station_code}"
        )
        
        return corrected_temps_k
    
    def get_loaded_stations(self) -> list[str]:
        """Get list of station codes with loaded calibrations.
        
        Returns:
            List of station codes (e.g., ["EGLC", "KLGA"])
        """
        return list(self._models.keys())
    
    def get_model_info(self, station_code: str) -> Optional[dict]:
        """Get calibration model metadata for a station.
        
        Args:
            station_code: Station code
            
        Returns:
            Dictionary with model info (version, elevation, etc.) or None
        """
        model = self._models.get(station_code.upper())
        if not model:
            return None
        
        return {
            "station": model.get("station"),
            "version": model.get("version"),
            "elevation": model.get("elevation", {}),
        }


