"""METAR service - fetches actual temperature observations from Aviation Weather Center.

Stage 7D-1 implementation.
"""

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config import config, PROJECT_ROOT
from core.logger import logger


class METARServiceError(Exception):
    """Exception raised for METAR API errors."""
    pass


class MetarObservation:
    """A single METAR observation."""

    def __init__(
        self,
        station_code: str,
        time: datetime,
        temp_C: float,
        temp_F: float,
        raw: Optional[str] = None,
        dewpoint_C: Optional[float] = None,
        wind_dir: Optional[int] = None,
        wind_speed: Optional[int] = None,
    ):
        self.station_code = station_code
        self.time = time
        self.temp_C = temp_C
        self.temp_F = temp_F
        self.raw = raw
        self.dewpoint_C = dewpoint_C
        self.wind_dir = wind_dir
        self.wind_speed = wind_speed

    def __repr__(self) -> str:
        return f"MetarObservation(station={self.station_code}, time={self.time}, temp_F={self.temp_F:.1f})"


class METARService:
    """Fetch METAR observations from Aviation Weather Center API."""

    def __init__(self, api_base: Optional[str] = None, user_agent: Optional[str] = None):
        """Initialize METAR service.

        Args:
            api_base: API base URL (defaults to config)
            user_agent: User-Agent header (defaults to config)
        """
        self.api_base = api_base or config.metar.api_base
        self.user_agent = user_agent or config.metar.user_agent
        self.snapshot_dir = PROJECT_ROOT / "data" / "snapshots" / "metar"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def _call_metar_api(
        self,
        params: dict,
    ) -> List[dict]:
        """Call METAR API with retry logic.

        Args:
            params: Query parameters (ids, start, end, format)

        Returns:
            List of METAR observation dictionaries

        Raises:
            METARServiceError: If API call fails
        """
        # Ensure format is JSON
        params = {**params, "format": "json"}

        logger.debug(f"Calling METAR API with params {params}")

        try:
            headers = {"User-Agent": self.user_agent}
            response = requests.get(
                self.api_base,
                params=params,
                headers=headers,
                timeout=30,
            )

            # Handle 204 (no data) as valid response
            if response.status_code == 204:
                logger.debug("METAR API returned 204 (no data available)")
                return []

            response.raise_for_status()

            data = response.json()

            # Handle both array and single object responses
            if isinstance(data, list):
                logger.debug(f"METAR API returned {len(data)} observations")
                return data
            elif isinstance(data, dict):
                # Single observation
                logger.debug("METAR API returned single observation")
                return [data]
            else:
                logger.warning(f"Unexpected METAR API response format: {type(data)}")
                return []

        except requests.exceptions.HTTPError as e:
            # Handle rate limiting (429)
            if response.status_code == 429:
                logger.warning(f"METAR API rate limit exceeded: {e}")
                raise METARServiceError(
                    f"METAR API rate limit exceeded. Please wait before retrying."
                ) from e

            logger.error(f"METAR API HTTP error: {e}")
            raise METARServiceError(f"METAR API HTTP error: {e}") from e
        except requests.exceptions.Timeout as e:
            logger.error(f"METAR API timeout: {e}")
            raise METARServiceError(f"METAR API timeout: {e}") from e
        except requests.exceptions.RequestException as e:
            logger.error(f"METAR API request error: {e}")
            raise METARServiceError(f"METAR API request error: {e}") from e
        except json.JSONDecodeError as e:
            logger.error(f"METAR API JSON decode error: {e}")
            raise METARServiceError(f"METAR API JSON decode error: {e}") from e

    def _parse_observation(self, obs_data: dict) -> Optional[MetarObservation]:
        """Parse a single METAR observation from API response.

        Args:
            obs_data: Raw observation dictionary from API

        Returns:
            MetarObservation object or None if invalid
        """
        try:
            # Handle both field name variations
            station = obs_data.get("station") or obs_data.get("icaoId", "")
            
            # Handle time in multiple formats
            time_utc = None
            time_str = obs_data.get("time") or obs_data.get("obsTime")
            
            if time_str:
                # Try ISO8601 string format first
                if isinstance(time_str, str):
                    try:
                        time_utc = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
                    except (ValueError, AttributeError):
                        pass
                # Try Unix timestamp (integer)
                elif isinstance(time_str, (int, float)):
                    try:
                        time_utc = datetime.fromtimestamp(time_str, tz=timezone.utc)
                    except (ValueError, OSError):
                        pass

            if not station or not time_utc:
                logger.debug(f"Missing station or time in observation: station={station}, time={time_str}")
                return None

            # Get temperature in Celsius
            temp_C = obs_data.get("temp")
            if temp_C is None:
                logger.debug(f"No temperature data for {station} at {time_utc}")
                return None

            # Convert to Fahrenheit
            temp_F = round((temp_C * 9 / 5) + 32, 1)

            # Optional fields (handle both naming conventions)
            dewpoint_C = obs_data.get("dewpoint") or obs_data.get("dewp")
            wind_dir = obs_data.get("windDir") or obs_data.get("wdir")
            wind_speed = obs_data.get("windSpeed") or obs_data.get("wspd")
            raw = obs_data.get("rawOb") or obs_data.get("rawOb")

            return MetarObservation(
                station_code=station,
                time=time_utc,
                temp_C=round(temp_C, 1),
                temp_F=temp_F,
                raw=raw,
                dewpoint_C=round(dewpoint_C, 1) if dewpoint_C is not None else None,
                wind_dir=wind_dir,
                wind_speed=wind_speed,
            )

        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"Failed to parse observation: {e}")
            return None

    def _save_snapshot(
        self,
        data: List[dict],
        station_code: str,
        date_str: str,
    ) -> Path:
        """Save METAR response to disk.

        Args:
            data: Raw JSON response data
            station_code: Station code
            date_str: Date string (YYYY-MM-DD)

        Returns:
            Path to saved snapshot
        """
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        snapshot_path = self.snapshot_dir / f"{station_code}_{date_str}.json"

        with open(snapshot_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

        logger.debug(f"Saved METAR snapshot to {snapshot_path}")
        return snapshot_path

    def get_observations(
        self,
        station_code: str,
        event_date: Optional[date] = None,
        hours: int = 24,
        save_snapshot: bool = False,
    ) -> List[MetarObservation]:
        """Fetch METAR observations for a station.

        Args:
            station_code: ICAO station code (e.g., "EGLC", "KLGA")
            event_date: Optional date for historical data (defaults to today)
            hours: Number of hours to fetch (default 24, max 24 for single call)
            save_snapshot: Whether to save raw response to disk

        Returns:
            List of MetarObservation objects

        Raises:
            METARServiceError: If API call fails
        """
        if event_date is None:
            event_date = date.today()

        # Calculate time range (UTC)
        start_time = datetime.combine(event_date, datetime.min.time()).replace(
            tzinfo=None
        )
        end_time = start_time + timedelta(hours=hours)

        # Format as ISO8601 UTC
        start_str = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_str = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        params = {
            "ids": station_code,
            "start": start_str,
            "end": end_str,
        }

        logger.info(
            f"Fetching METAR observations for {station_code} from {start_str} to {end_str}"
        )

        try:
            # Call API
            raw_data = self._call_metar_api(params)

            # Save snapshot if requested
            if save_snapshot and raw_data:
                self._save_snapshot(raw_data, station_code, event_date.isoformat())

            # Parse observations
            observations = []
            for obs_data in raw_data:
                obs = self._parse_observation(obs_data)
                if obs:
                    observations.append(obs)

            logger.info(
                f"Retrieved {len(observations)} valid METAR observations for {station_code}"
            )

            return observations

        except METARServiceError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching METAR data: {e}")
            raise METARServiceError(f"Unexpected error: {e}") from e

    def get_daily_high(
        self,
        station_code: str,
        event_date: Optional[date] = None,
    ) -> Optional[float]:
        """Get daily high temperature from METAR observations.

        This is the actual temperature that Polymarket will use for resolution.

        Args:
            station_code: ICAO station code
            event_date: Date (defaults to today)

        Returns:
            Daily high temperature in Fahrenheit, or None if no data available

        Raises:
            METARServiceError: If API call fails
        """
        observations = self.get_observations(station_code, event_date, hours=24)

        if not observations:
            logger.warning(
                f"No METAR observations available for {station_code} on {event_date}"
            )
            return None

        temps = [obs.temp_F for obs in observations if obs.temp_F is not None]

        if not temps:
            logger.warning(f"No temperature data in observations for {station_code}")
            return None

        daily_high = max(temps)
        logger.info(
            f"Daily high for {station_code} on {event_date}: {daily_high:.1f}°F"
        )

        return round(daily_high, 1)

    def get_daily_low(
        self,
        station_code: str,
        event_date: Optional[date] = None,
    ) -> Optional[float]:
        """Get daily low temperature from METAR observations.

        Args:
            station_code: ICAO station code
            event_date: Date (defaults to today)

        Returns:
            Daily low temperature in Fahrenheit, or None if no data available

        Raises:
            METARServiceError: If API call fails
        """
        observations = self.get_observations(station_code, event_date, hours=24)

        if not observations:
            logger.warning(
                f"No METAR observations available for {station_code} on {event_date}"
            )
            return None

        temps = [obs.temp_F for obs in observations if obs.temp_F is not None]

        if not temps:
            logger.warning(f"No temperature data in observations for {station_code}")
            return None

        daily_low = min(temps)
        logger.info(
            f"Daily low for {station_code} on {event_date}: {daily_low:.1f}°F"
        )

        return round(daily_low, 1)

