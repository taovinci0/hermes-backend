"""Station registry management.

Loads and manages weather station metadata from CSV.
Stage 1 implementation.
"""

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .config import PROJECT_ROOT
from .logger import logger


@dataclass
class Station:
    """Weather station metadata."""

    city: str
    station_name: str
    station_code: str
    lat: float
    lon: float
    noaa_station: str
    venue_hint: str
    time_zone: str

    def __repr__(self) -> str:
        return f"Station({self.city}, {self.station_code}, tz={self.time_zone})"


class StationRegistry:
    """Registry of weather stations for trading.

    Loads station metadata from CSV and provides lookup methods.
    """

    def __init__(self, registry_path: Optional[Path] = None):
        """Initialize station registry.

        Args:
            registry_path: Path to stations.csv (defaults to data/registry/stations.csv)
        """
        if registry_path is None:
            registry_path = PROJECT_ROOT / "data" / "registry" / "stations.csv"

        self.registry_path = registry_path
        self.stations: dict[str, Station] = {}
        self._load()

    def _load(self) -> None:
        """Load stations from CSV file."""
        if not self.registry_path.exists():
            logger.warning(
                f"Station registry not found at {self.registry_path}. "
                "Registry will be empty."
            )
            return

        try:
            with open(self.registry_path, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    station = Station(
                        city=row["city"],
                        station_name=row["station_name"],
                        station_code=row["station_code"],
                        lat=float(row["lat"]),
                        lon=float(row["lon"]),
                        noaa_station=row["noaa_station"],
                        venue_hint=row["venue_hint"],
                        time_zone=row["time_zone"],
                    )
                    self.stations[station.station_code] = station

            logger.info(f"Loaded {len(self.stations)} stations from registry")

        except Exception as e:
            logger.error(f"Failed to load station registry: {e}")
            raise

    def get(self, station_code: str) -> Optional[Station]:
        """Get station by code.

        Args:
            station_code: Station code (e.g., 'EGLC', 'KLGA')

        Returns:
            Station object or None if not found
        """
        return self.stations.get(station_code)

    def get_by_city(self, city: str) -> Optional[Station]:
        """Get station by city name.

        Args:
            city: City name (case-insensitive)

        Returns:
            Station object or None if not found
        """
        city_lower = city.lower()
        for station in self.stations.values():
            if station.city.lower() == city_lower:
                return station
        return None

    def list_all(self) -> list[Station]:
        """Get all stations.

        Returns:
            List of all Station objects
        """
        return list(self.stations.values())

    def list_by_timezone(self, timezone: str) -> list[Station]:
        """Get all stations in a timezone.

        Args:
            timezone: IANA timezone name (e.g., 'America/New_York')

        Returns:
            List of Station objects in that timezone
        """
        return [s for s in self.stations.values() if s.time_zone == timezone]

    def __contains__(self, station_code: str) -> bool:
        """Check if station code exists in registry.

        Args:
            station_code: Station code to check

        Returns:
            True if station exists
        """
        return station_code in self.stations

    def __len__(self) -> int:
        """Get number of stations in registry.

        Returns:
            Count of stations
        """
        return len(self.stations)


# Global registry instance
_registry: Optional[StationRegistry] = None


def get_registry() -> StationRegistry:
    """Get global station registry instance.

    Returns:
        StationRegistry singleton
    """
    global _registry
    if _registry is None:
        _registry = StationRegistry()
    return _registry

