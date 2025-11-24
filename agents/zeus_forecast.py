"""Zeus weather forecast agent.

Fetches hourly temperature forecasts from Zeus API.
Stage 2 implementation.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from core.types import ZeusForecast, ForecastPoint
from core.config import config, PROJECT_ROOT
from core.logger import logger


class ZeusAPIError(Exception):
    """Exception raised for Zeus API errors."""
    pass


class ZeusForecastAgent:
    """Agent for fetching Zeus weather forecasts."""

    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None):
        """Initialize Zeus forecast agent.

        Args:
            api_key: Zeus API key (defaults to config)
            api_base: Zeus API base URL (defaults to config)
        """
        self.api_key = api_key or config.zeus.api_key
        self.api_base = api_base or config.zeus.api_base
        self.snapshot_dir = PROJECT_ROOT / "data" / "snapshots" / "zeus"

        if not self.api_key or self.api_key == "changeme":
            logger.warning("⚠️  Zeus API key not configured")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def _call_zeus_api(
        self,
        lat: float,
        lon: float,
        start_utc: datetime,
        predict_hours: int,
    ) -> dict:
        """Call Zeus API with retry logic.

        Args:
            lat: Latitude
            lon: Longitude
            start_utc: Forecast start time (may be local time with timezone - param name is legacy)
            predict_hours: Number of hours to forecast

        Returns:
            Raw JSON response from Zeus API

        Raises:
            ZeusAPIError: If API call fails
        """
        url = f"{self.api_base}/forecast"
        
        # Format datetime for API - preserve timezone if present
        # Zeus API expects ISO format with timezone (e.g., 2025-11-17T00:00:00-05:00)
        if start_utc.tzinfo is not None:
            # Has timezone - use ISO format to preserve it
            start_time_str = start_utc.isoformat()
        else:
            # No timezone - assume UTC and format with Z
            start_time_str = start_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        params = {
            "latitude": lat,
            "longitude": lon,
            "variable": "2m_temperature",  # Required by Zeus API
            "start_time": start_time_str,
            "predict_hours": predict_hours,
        }
        
        logger.info(
            f"Calling Zeus API: lat={lat:.4f}, lon={lon:.4f}, "
            f"start={start_time_str}, hours={predict_hours}"
        )
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Zeus API call successful, received {len(data.get('forecast', []))} data points")
            return data
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"Zeus API HTTP error: {e}")
            raise ZeusAPIError(f"Zeus API HTTP error: {e}") from e
        except requests.exceptions.Timeout as e:
            logger.error(f"Zeus API timeout: {e}")
            raise ZeusAPIError(f"Zeus API timeout: {e}") from e
        except requests.exceptions.RequestException as e:
            logger.error(f"Zeus API request error: {e}")
            raise ZeusAPIError(f"Zeus API request error: {e}") from e
        except json.JSONDecodeError as e:
            logger.error(f"Zeus API JSON decode error: {e}")
            raise ZeusAPIError(f"Zeus API JSON decode error: {e}") from e

    def _save_snapshot(
        self,
        data: dict,
        station_code: str,
        date_str: str,
    ) -> Path:
        """Save raw Zeus API response to disk.

        Args:
            data: Raw JSON response from Zeus API
            station_code: Station code (e.g., 'EGLC')
            date_str: Date string in YYYY-MM-DD format

        Returns:
            Path to saved snapshot file
        """
        # Create directory structure: data/snapshots/zeus/YYYY-MM-DD/
        date_dir = self.snapshot_dir / date_str
        date_dir.mkdir(parents=True, exist_ok=True)
        
        # Save to: data/snapshots/zeus/YYYY-MM-DD/{station}.json
        snapshot_path = date_dir / f"{station_code}.json"
        
        with open(snapshot_path, "w") as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved Zeus snapshot to {snapshot_path}")
        return snapshot_path

    def fetch(
        self,
        lat: float,
        lon: float,
        start_utc: datetime,
        hours: int = 24,
        station_code: Optional[str] = None,
    ) -> ZeusForecast:
        """Fetch hourly temperature forecast from Zeus.

        Args:
            lat: Latitude
            lon: Longitude
            start_utc: Forecast start time in UTC
            hours: Number of hours to forecast (default 24)
            station_code: Optional station code for snapshot naming

        Returns:
            ZeusForecast with hourly temperature data

        Raises:
            ZeusAPIError: If API call fails
            ValueError: If response parsing fails
        """
        # Call Zeus API
        raw_data = self._call_zeus_api(lat, lon, start_utc, hours)
        
        # Save snapshot if station_code provided
        if station_code:
            date_str = start_utc.strftime("%Y-%m-%d")
            self._save_snapshot(raw_data, station_code, date_str)
        
        # Parse response into ForecastPoint objects
        try:
            timeseries = []
            
            # Zeus API format: separate arrays for temperature and time
            if "2m_temperature" in raw_data and "time" in raw_data:
                logger.debug("Using Zeus API array format (2m_temperature + time)")
                
                temp_data = raw_data["2m_temperature"]
                time_data = raw_data["time"]
                
                if not isinstance(temp_data, dict) or "data" not in temp_data:
                    logger.error(f"Invalid 2m_temperature format")
                    raise ValueError("2m_temperature must have 'data' field")
                
                if not isinstance(time_data, dict) or "data" not in time_data:
                    logger.error(f"Invalid time format")
                    raise ValueError("time must have 'data' field")
                
                temperatures = temp_data["data"]
                timestamps = time_data["data"]
                
                if len(temperatures) != len(timestamps):
                    logger.error(f"Length mismatch: {len(temperatures)} temps vs {len(timestamps)} times")
                    raise ValueError("Temperature and time arrays must have same length")
                
                for temp_k, timestamp in zip(temperatures, timestamps):
                    # Parse timestamp
                    if isinstance(timestamp, str):
                        time_utc = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    elif isinstance(timestamp, (int, float)):
                        time_utc = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                    else:
                        time_utc = timestamp
                    
                    timeseries.append(
                        ForecastPoint(
                            time_utc=time_utc,
                            temp_K=float(temp_k),
                        )
                    )
            
            # Fallback: object-based format
            else:
                logger.debug("Using object-based forecast format")
                forecast_data = raw_data.get("forecast", [])
                
                if not forecast_data:
                    raise ValueError("No forecast data in Zeus API response")
                
                for point in forecast_data:
                    # Parse timestamp (expecting ISO format)
                    time_str = point.get("time") or point.get("timestamp")
                    if not time_str:
                        logger.warning(f"Missing time field in forecast point: {point}")
                        continue
                    
                    time_utc = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
                    
                    # Get temperature in Kelvin
                    temp_k = point.get("temperature_k") or point.get("temp_k") or point.get("temperature")
                    if temp_k is None:
                        logger.warning(f"Missing temperature in forecast point: {point}")
                        continue
                    
                    timeseries.append(
                        ForecastPoint(
                            time_utc=time_utc,
                            temp_K=float(temp_k),
                        )
                    )
            
            if not timeseries:
                raise ValueError("No valid forecast points parsed from Zeus response")
            
            forecast = ZeusForecast(
                timeseries=timeseries,
                station_code=station_code or "UNKNOWN",
                lat=lat,
                lon=lon,
            )
            
            logger.info(
                f"Parsed {len(forecast.timeseries)} forecast points "
                f"for {forecast.station_code}"
            )
            
            return forecast
            
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Failed to parse Zeus API response: {e}")
            raise ValueError(f"Failed to parse Zeus API response: {e}") from e

