"""Tests for station registry.

Stage 1 implementation - station metadata loading and lookup.
"""

import pytest
from pathlib import Path
from core.registry import Station, StationRegistry, get_registry


def test_station_dataclass() -> None:
    """Test Station dataclass creation."""
    station = Station(
        city="London",
        station_name="London City Airport",
        station_code="EGLC",
        lat=51.505,
        lon=0.05,
        noaa_station="UKMO",
        venue_hint="Polymarket London",
        time_zone="Europe/London",
    )
    
    assert station.city == "London"
    assert station.station_name == "London City Airport"
    assert station.station_code == "EGLC"
    assert station.lat == 51.505
    assert station.lon == 0.05
    assert station.noaa_station == "UKMO"
    assert station.venue_hint == "Polymarket London"
    assert station.time_zone == "Europe/London"
    assert "EGLC" in repr(station)


def test_station_registry_load() -> None:
    """Test loading stations from CSV."""
    registry = StationRegistry()
    
    # Should have loaded stations from data/registry/stations.csv
    assert len(registry) > 0
    assert "EGLC" in registry
    assert "KLGA" in registry


def test_station_registry_get_by_code() -> None:
    """Test getting station by code."""
    registry = StationRegistry()
    
    station = registry.get("EGLC")
    assert station is not None
    assert station.city == "London"
    assert station.station_code == "EGLC"
    assert station.time_zone == "Europe/London"
    
    # Non-existent station
    assert registry.get("NONEXISTENT") is None


def test_station_registry_get_by_city() -> None:
    """Test getting station by city name."""
    registry = StationRegistry()
    
    # Exact match
    station = registry.get_by_city("London")
    assert station is not None
    assert station.station_code == "EGLC"
    
    # Case-insensitive
    station = registry.get_by_city("london")
    assert station is not None
    assert station.station_code == "EGLC"
    
    # Partial match (will return the first match)
    station = registry.get_by_city("New York (Airport)")
    assert station is not None
    assert station.station_code == "KLGA"
    
    # Non-existent city
    assert registry.get_by_city("Atlantis") is None


def test_station_registry_list_all() -> None:
    """Test listing all stations."""
    registry = StationRegistry()
    
    all_stations = registry.list_all()
    assert isinstance(all_stations, list)
    assert len(all_stations) > 0
    assert all(isinstance(s, Station) for s in all_stations)


def test_station_registry_list_by_timezone() -> None:
    """Test filtering stations by timezone."""
    registry = StationRegistry()
    
    # Get all US Eastern stations
    eastern_stations = registry.list_by_timezone("America/New_York")
    assert len(eastern_stations) > 0
    assert all(s.time_zone == "America/New_York" for s in eastern_stations)
    
    # Should include KLGA, KNYC, KMIA, KPHL
    codes = {s.station_code for s in eastern_stations}
    assert "KLGA" in codes
    assert "KMIA" in codes


def test_station_registry_contains() -> None:
    """Test __contains__ operator."""
    registry = StationRegistry()
    
    assert "EGLC" in registry
    assert "KLGA" in registry
    assert "NONEXISTENT" not in registry


def test_station_registry_len() -> None:
    """Test __len__ operator."""
    registry = StationRegistry()
    
    count = len(registry)
    assert count > 0
    assert count == len(registry.list_all())


def test_get_registry_singleton() -> None:
    """Test global registry singleton."""
    registry1 = get_registry()
    registry2 = get_registry()
    
    # Should be same instance
    assert registry1 is registry2
    
    # Should have stations loaded
    assert len(registry1) > 0


def test_station_registry_major_cities() -> None:
    """Test that major cities are present in registry."""
    registry = StationRegistry()
    
    expected_cities = [
        ("London", "EGLC"),
        ("New York (Airport)", "KLGA"),
        ("Chicago", "KMDW"),
        ("Los Angeles", "KLAX"),
    ]
    
    for city, code in expected_cities:
        station = registry.get(code)
        assert station is not None, f"{city} ({code}) not found in registry"
        assert station.city == city


def test_station_coordinates() -> None:
    """Test that station coordinates are reasonable."""
    registry = StationRegistry()
    
    # London should be around 51°N, 0°E
    london = registry.get("EGLC")
    assert london is not None
    assert 51 < london.lat < 52
    assert -1 < london.lon < 1
    
    # New York LaGuardia should be around 40°N, 74°W
    ny = registry.get("KLGA")
    assert ny is not None
    assert 40 < ny.lat < 41
    assert -74 < ny.lon < -73
    
    # Los Angeles should be around 33°N, 118°W
    la = registry.get("KLAX")
    assert la is not None
    assert 33 < la.lat < 34
    assert -119 < la.lon < -118


def test_station_timezones_valid() -> None:
    """Test that all station timezones are valid IANA names."""
    registry = StationRegistry()
    
    import pytz
    
    for station in registry.list_all():
        # Should not raise exception
        tz = pytz.timezone(station.time_zone)
        assert tz is not None


def test_station_registry_empty_path() -> None:
    """Test registry with non-existent path (should be empty but not crash)."""
    registry = StationRegistry(registry_path=Path("/nonexistent/path.csv"))
    
    # Should create empty registry without crashing
    assert len(registry) == 0
    assert registry.get("EGLC") is None

