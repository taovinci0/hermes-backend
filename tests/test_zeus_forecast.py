"""Tests for Zeus forecast agent.

Stage 2 implementation - Zeus API client with mocking.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
import requests

from agents.zeus_forecast import ZeusForecastAgent, ZeusAPIError
from core.types import ZeusForecast


# Sample Zeus API response
SAMPLE_ZEUS_RESPONSE = {
    "forecast": [
        {"time": "2025-11-05T00:00:00Z", "temperature_k": 288.15},
        {"time": "2025-11-05T01:00:00Z", "temperature_k": 287.95},
        {"time": "2025-11-05T02:00:00Z", "temperature_k": 287.75},
        {"time": "2025-11-05T03:00:00Z", "temperature_k": 287.55},
        {"time": "2025-11-05T04:00:00Z", "temperature_k": 287.35},
        {"time": "2025-11-05T05:00:00Z", "temperature_k": 287.25},
        {"time": "2025-11-05T06:00:00Z", "temperature_k": 287.45},
        {"time": "2025-11-05T07:00:00Z", "temperature_k": 288.15},
        {"time": "2025-11-05T08:00:00Z", "temperature_k": 289.15},
        {"time": "2025-11-05T09:00:00Z", "temperature_k": 290.15},
        {"time": "2025-11-05T10:00:00Z", "temperature_k": 291.15},
        {"time": "2025-11-05T11:00:00Z", "temperature_k": 292.15},
        {"time": "2025-11-05T12:00:00Z", "temperature_k": 293.15},
        {"time": "2025-11-05T13:00:00Z", "temperature_k": 293.95},
        {"time": "2025-11-05T14:00:00Z", "temperature_k": 294.25},
        {"time": "2025-11-05T15:00:00Z", "temperature_k": 294.15},
        {"time": "2025-11-05T16:00:00Z", "temperature_k": 293.55},
        {"time": "2025-11-05T17:00:00Z", "temperature_k": 292.75},
        {"time": "2025-11-05T18:00:00Z", "temperature_k": 291.85},
        {"time": "2025-11-05T19:00:00Z", "temperature_k": 290.95},
        {"time": "2025-11-05T20:00:00Z", "temperature_k": 290.15},
        {"time": "2025-11-05T21:00:00Z", "temperature_k": 289.45},
        {"time": "2025-11-05T22:00:00Z", "temperature_k": 288.85},
        {"time": "2025-11-05T23:00:00Z", "temperature_k": 288.35},
    ]
}


def test_zeus_agent_initialization() -> None:
    """Test Zeus agent initialization."""
    agent = ZeusForecastAgent(api_key="test_key", api_base="https://test.api")
    
    assert agent.api_key == "test_key"
    assert agent.api_base == "https://test.api"
    assert agent.snapshot_dir.name == "zeus"


@patch("agents.zeus_forecast.requests.get")
def test_zeus_fetch_success(mock_get: Mock, tmp_path: Path) -> None:
    """Test successful Zeus API fetch."""
    # Mock successful API response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_ZEUS_RESPONSE
    mock_get.return_value = mock_response
    
    # Create agent with temporary snapshot directory
    agent = ZeusForecastAgent(api_key="test_key", api_base="https://test.api")
    agent.snapshot_dir = tmp_path / "snapshots" / "zeus"
    
    # Fetch forecast
    start_time = datetime(2025, 11, 5, 0, 0, 0, tzinfo=timezone.utc)
    forecast = agent.fetch(
        lat=51.505,
        lon=0.05,
        start_utc=start_time,
        hours=24,
        station_code="EGLC",
    )
    
    # Verify API was called correctly
    mock_get.assert_called_once()
    call_kwargs = mock_get.call_args[1]
    assert call_kwargs["params"]["latitude"] == 51.505
    assert call_kwargs["params"]["longitude"] == 0.05
    assert call_kwargs["params"]["predict_hours"] == 24
    assert "Authorization" in call_kwargs["headers"]
    
    # Verify forecast object
    assert isinstance(forecast, ZeusForecast)
    assert len(forecast.timeseries) == 24
    assert forecast.station_code == "EGLC"
    
    # Verify first and last points
    assert forecast.timeseries[0].temp_K == 288.15
    assert forecast.timeseries[-1].temp_K == 288.35
    
    # Verify snapshot was saved
    snapshot_path = tmp_path / "snapshots" / "zeus" / "2025-11-05" / "EGLC.json"
    assert snapshot_path.exists()
    
    with open(snapshot_path) as f:
        saved_data = json.load(f)
    assert saved_data == SAMPLE_ZEUS_RESPONSE


@patch("agents.zeus_forecast.requests.get")
def test_zeus_fetch_http_error(mock_get: Mock) -> None:
    """Test Zeus API HTTP error handling."""
    # Mock HTTP error
    mock_response = Mock()
    mock_response.status_code = 401
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("401 Unauthorized")
    mock_get.return_value = mock_response
    
    agent = ZeusForecastAgent(api_key="bad_key", api_base="https://test.api")
    
    start_time = datetime(2025, 11, 5, 0, 0, 0, tzinfo=timezone.utc)
    
    with pytest.raises(ZeusAPIError, match="HTTP error"):
        agent.fetch(lat=51.505, lon=0.05, start_utc=start_time)


@patch("agents.zeus_forecast.requests.get")
def test_zeus_fetch_timeout(mock_get: Mock) -> None:
    """Test Zeus API timeout handling."""
    # Mock timeout
    mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
    
    agent = ZeusForecastAgent(api_key="test_key", api_base="https://test.api")
    
    start_time = datetime(2025, 11, 5, 0, 0, 0, tzinfo=timezone.utc)
    
    with pytest.raises(ZeusAPIError, match="timeout"):
        agent.fetch(lat=51.505, lon=0.05, start_utc=start_time)


@patch("agents.zeus_forecast.requests.get")
def test_zeus_fetch_invalid_json(mock_get: Mock) -> None:
    """Test Zeus API invalid JSON handling."""
    # Mock invalid JSON response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
    mock_get.return_value = mock_response
    
    agent = ZeusForecastAgent(api_key="test_key", api_base="https://test.api")
    
    start_time = datetime(2025, 11, 5, 0, 0, 0, tzinfo=timezone.utc)
    
    with pytest.raises(ZeusAPIError, match="JSON decode error"):
        agent.fetch(lat=51.505, lon=0.05, start_utc=start_time)


@patch("agents.zeus_forecast.requests.get")
def test_zeus_fetch_empty_forecast(mock_get: Mock) -> None:
    """Test Zeus API with empty forecast data."""
    # Mock empty forecast response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"forecast": []}
    mock_get.return_value = mock_response
    
    agent = ZeusForecastAgent(api_key="test_key", api_base="https://test.api")
    
    start_time = datetime(2025, 11, 5, 0, 0, 0, tzinfo=timezone.utc)
    
    with pytest.raises(ValueError, match="No forecast data"):
        agent.fetch(lat=51.505, lon=0.05, start_utc=start_time)


@patch("agents.zeus_forecast.requests.get")
def test_zeus_fetch_missing_fields(mock_get: Mock) -> None:
    """Test Zeus API with missing required fields."""
    # Mock response with missing fields
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "forecast": [
            {"time": "2025-11-05T00:00:00Z"},  # Missing temperature
            {"temperature_k": 288.15},  # Missing time
        ]
    }
    mock_get.return_value = mock_response
    
    agent = ZeusForecastAgent(api_key="test_key", api_base="https://test.api")
    
    start_time = datetime(2025, 11, 5, 0, 0, 0, tzinfo=timezone.utc)
    
    with pytest.raises(ValueError, match="No valid forecast points"):
        agent.fetch(lat=51.505, lon=0.05, start_utc=start_time)


@patch("agents.zeus_forecast.requests.get")
def test_zeus_fetch_alternative_field_names(mock_get: Mock) -> None:
    """Test Zeus API with alternative field names."""
    # Mock response with alternative field names
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "forecast": [
            {"timestamp": "2025-11-05T00:00:00Z", "temp_k": 288.15},
            {"time": "2025-11-05T01:00:00Z", "temperature": 287.95},
        ]
    }
    mock_get.return_value = mock_response
    
    agent = ZeusForecastAgent(api_key="test_key", api_base="https://test.api")
    
    start_time = datetime(2025, 11, 5, 0, 0, 0, tzinfo=timezone.utc)
    forecast = agent.fetch(lat=51.505, lon=0.05, start_utc=start_time, hours=2)
    
    assert len(forecast.timeseries) == 2
    assert forecast.timeseries[0].temp_K == 288.15
    assert forecast.timeseries[1].temp_K == 287.95


@patch("agents.zeus_forecast.requests.get")
def test_zeus_fetch_without_station_code(mock_get: Mock, tmp_path: Path) -> None:
    """Test Zeus fetch without station code (no snapshot saved)."""
    # Mock successful API response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "forecast": [
            {"time": "2025-11-05T00:00:00Z", "temperature_k": 288.15},
        ]
    }
    mock_get.return_value = mock_response
    
    agent = ZeusForecastAgent(api_key="test_key", api_base="https://test.api")
    agent.snapshot_dir = tmp_path / "snapshots" / "zeus"
    
    start_time = datetime(2025, 11, 5, 0, 0, 0, tzinfo=timezone.utc)
    forecast = agent.fetch(lat=51.505, lon=0.05, start_utc=start_time, hours=1)
    
    assert len(forecast.timeseries) == 1
    assert forecast.station_code == "UNKNOWN"
    
    # Verify no snapshot was saved
    snapshot_path = tmp_path / "snapshots" / "zeus" / "2025-11-05"
    assert not snapshot_path.exists()


@patch("agents.zeus_forecast.requests.get")
def test_zeus_snapshot_directory_creation(mock_get: Mock, tmp_path: Path) -> None:
    """Test that snapshot directory is created if it doesn't exist."""
    # Mock successful API response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_ZEUS_RESPONSE
    mock_get.return_value = mock_response
    
    # Use non-existent directory
    agent = ZeusForecastAgent(api_key="test_key", api_base="https://test.api")
    agent.snapshot_dir = tmp_path / "new_dir" / "zeus"
    
    start_time = datetime(2025, 11, 5, 0, 0, 0, tzinfo=timezone.utc)
    agent.fetch(lat=51.505, lon=0.05, start_utc=start_time, station_code="TEST")
    
    # Verify directory was created
    assert agent.snapshot_dir.exists()
    assert (agent.snapshot_dir / "2025-11-05").exists()


def test_zeus_api_request_format() -> None:
    """Test that Zeus API request is formatted correctly."""
    with patch("agents.zeus_forecast.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = SAMPLE_ZEUS_RESPONSE
        mock_get.return_value = mock_response
        
        agent = ZeusForecastAgent(api_key="my_key", api_base="https://api.zeus.com")
        
        start_time = datetime(2025, 11, 5, 12, 30, 0, tzinfo=timezone.utc)
        agent.fetch(lat=40.7769, lon=-73.8740, start_utc=start_time, hours=48)
        
        # Verify call arguments
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        
        assert args[0] == "https://api.zeus.com/forecast"
        assert kwargs["headers"]["Authorization"] == "Bearer my_key"
        assert kwargs["params"]["latitude"] == 40.7769
        assert kwargs["params"]["longitude"] == -73.8740
        assert kwargs["params"]["start_time"] == "2025-11-05T12:30:00Z"
        assert kwargs["params"]["predict_hours"] == 48
        assert kwargs["timeout"] == 30

