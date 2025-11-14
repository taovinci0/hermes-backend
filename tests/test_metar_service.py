"""Tests for METAR service.

Stage 7D-1 implementation.
"""

import json
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests

from venues.metar import METARService, METARServiceError, MetarObservation


class TestMetarObservation:
    """Test MetarObservation class."""

    def test_observation_creation(self):
        """Test creating a MetarObservation."""
        obs = MetarObservation(
            station_code="EGLC",
            time=datetime(2025, 11, 13, 12, 0, 0, tzinfo=timezone.utc),
            temp_C=15.0,
            temp_F=59.0,
            raw="EGLC 131200Z 22010KT 9999 FEW020 15/11 Q1018",
        )

        assert obs.station_code == "EGLC"
        assert obs.temp_C == 15.0
        assert obs.temp_F == 59.0
        assert obs.raw is not None

    def test_observation_repr(self):
        """Test observation string representation."""
        obs = MetarObservation(
            station_code="EGLC",
            time=datetime(2025, 11, 13, 12, 0, 0, tzinfo=timezone.utc),
            temp_C=15.0,
            temp_F=59.0,
        )

        repr_str = repr(obs)
        assert "EGLC" in repr_str
        assert "59.0" in repr_str


class TestMETARService:
    """Test METARService class."""

    @pytest.fixture
    def service(self):
        """Create a METARService instance."""
        return METARService()

    @pytest.fixture
    def sample_metar_response(self):
        """Sample METAR API response."""
        return [
            {
                "station": "EGLC",
                "time": "2025-11-13T12:00:00Z",
                "temp": 15.0,
                "dewpoint": 11.0,
                "windDir": 220,
                "windSpeed": 10,
                "altim": 30.05,
                "fltCat": "VFR",
                "rawOb": "EGLC 131200Z 22010KT 9999 FEW020 15/11 Q1018",
            },
            {
                "station": "EGLC",
                "time": "2025-11-13T13:00:00Z",
                "temp": 16.0,
                "dewpoint": 12.0,
                "windDir": 230,
                "windSpeed": 12,
                "altim": 30.06,
                "fltCat": "VFR",
                "rawOb": "EGLC 131300Z 23012KT 9999 FEW020 16/12 Q1019",
            },
        ]

    def test_init_defaults(self, service):
        """Test service initialization with defaults."""
        assert service.api_base == "https://aviationweather.gov/api/data/metar"
        assert "Hermes" in service.user_agent

    def test_init_custom(self):
        """Test service initialization with custom values."""
        service = METARService(
            api_base="https://custom.api.com",
            user_agent="CustomAgent/1.0",
        )
        assert service.api_base == "https://custom.api.com"
        assert service.user_agent == "CustomAgent/1.0"

    @patch("venues.metar.metar_service.requests.get")
    def test_get_observations_success(self, mock_get, service, sample_metar_response):
        """Test successful observation fetch."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_metar_response
        mock_get.return_value = mock_response

        observations = service.get_observations("EGLC", date(2025, 11, 13))

        assert len(observations) == 2
        assert observations[0].station_code == "EGLC"
        assert observations[0].temp_C == 15.0
        assert observations[0].temp_F == 59.0  # 15 * 9/5 + 32
        assert observations[1].temp_F == 60.8  # 16 * 9/5 + 32

        # Verify API call
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "aviationweather.gov" in call_args[0][0]
        assert call_args[1]["params"]["ids"] == "EGLC"
        assert call_args[1]["params"]["format"] == "json"
        assert "User-Agent" in call_args[1]["headers"]

    @patch("venues.metar.metar_service.requests.get")
    def test_get_observations_no_data(self, mock_get, service):
        """Test handling of 204 (no data) response."""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_get.return_value = mock_response

        observations = service.get_observations("EGLC", date(2025, 11, 13))

        assert len(observations) == 0

    @patch("venues.metar.metar_service.requests.get")
    def test_get_observations_empty_list(self, mock_get, service):
        """Test handling of empty list response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        observations = service.get_observations("EGLC", date(2025, 11, 13))

        assert len(observations) == 0

    @patch("venues.metar.metar_service.requests.get")
    def test_get_observations_single_object(self, mock_get, service):
        """Test handling of single object response."""
        single_obs = {
            "station": "EGLC",
            "time": "2025-11-13T12:00:00Z",
            "temp": 15.0,
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = single_obs
        mock_get.return_value = mock_response

        observations = service.get_observations("EGLC", date(2025, 11, 13))

        assert len(observations) == 1
        assert observations[0].station_code == "EGLC"

    @patch("venues.metar.metar_service.requests.get")
    def test_get_observations_missing_temp(self, mock_get, service):
        """Test handling of observations without temperature."""
        response_without_temp = [
            {
                "station": "EGLC",
                "time": "2025-11-13T12:00:00Z",
                # No temp field
            }
        ]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = response_without_temp
        mock_get.return_value = mock_response

        observations = service.get_observations("EGLC", date(2025, 11, 13))

        # Should skip observations without temperature
        assert len(observations) == 0

    @patch("venues.metar.metar_service.requests.get")
    def test_get_observations_http_error(self, mock_get, service):
        """Test handling of HTTP errors."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "404 Not Found"
        )
        mock_get.return_value = mock_response

        with pytest.raises(METARServiceError, match="HTTP error"):
            service.get_observations("EGLC", date(2025, 11, 13))

    @patch("venues.metar.metar_service.requests.get")
    def test_get_observations_rate_limit(self, mock_get, service):
        """Test handling of rate limit (429) errors."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "429 Too Many Requests"
        )
        mock_get.return_value = mock_response

        with pytest.raises(METARServiceError, match="rate limit"):
            service.get_observations("EGLC", date(2025, 11, 13))

    @patch("venues.metar.metar_service.requests.get")
    def test_get_observations_timeout(self, mock_get, service):
        """Test handling of timeout errors."""
        mock_get.side_effect = requests.exceptions.Timeout("Request timeout")

        with pytest.raises(METARServiceError, match="timeout"):
            service.get_observations("EGLC", date(2025, 11, 13))

    @patch("venues.metar.metar_service.requests.get")
    def test_get_observations_json_error(self, mock_get, service):
        """Test handling of JSON decode errors."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_get.return_value = mock_response

        with pytest.raises(METARServiceError, match="JSON decode"):
            service.get_observations("EGLC", date(2025, 11, 13))

    @patch("venues.metar.metar_service.requests.get")
    def test_get_daily_high(self, mock_get, service, sample_metar_response):
        """Test getting daily high temperature."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_metar_response
        mock_get.return_value = mock_response

        daily_high = service.get_daily_high("EGLC", date(2025, 11, 13))

        # Highest temp is 16.0°C = 60.8°F
        assert daily_high == 60.8

    @patch("venues.metar.metar_service.requests.get")
    def test_get_daily_high_no_data(self, mock_get, service):
        """Test getting daily high with no data."""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_get.return_value = mock_response

        daily_high = service.get_daily_high("EGLC", date(2025, 11, 13))

        assert daily_high is None

    @patch("venues.metar.metar_service.requests.get")
    def test_get_daily_low(self, mock_get, service, sample_metar_response):
        """Test getting daily low temperature."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_metar_response
        mock_get.return_value = mock_response

        daily_low = service.get_daily_low("EGLC", date(2025, 11, 13))

        # Lowest temp is 15.0°C = 59.0°F
        assert daily_low == 59.0

    @patch("venues.metar.metar_service.requests.get")
    def test_temperature_conversion(self, mock_get, service):
        """Test Celsius to Fahrenheit conversion."""
        response = [
            {
                "station": "EGLC",
                "time": "2025-11-13T12:00:00Z",
                "temp": 0.0,  # Freezing point
            },
            {
                "station": "EGLC",
                "time": "2025-11-13T13:00:00Z",
                "temp": 100.0,  # Boiling point
            },
        ]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = response
        mock_get.return_value = mock_response

        observations = service.get_observations("EGLC", date(2025, 11, 13))

        assert observations[0].temp_F == 32.0  # 0°C = 32°F
        assert observations[1].temp_F == 212.0  # 100°C = 212°F

    @patch("venues.metar.metar_service.requests.get")
    def test_save_snapshot(self, mock_get, service, sample_metar_response, tmp_path):
        """Test saving snapshot to disk."""
        # Override snapshot directory
        service.snapshot_dir = tmp_path / "snapshots" / "metar"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_metar_response
        mock_get.return_value = mock_response

        observations = service.get_observations(
            "EGLC", date(2025, 11, 13), save_snapshot=True
        )

        # Check snapshot was saved
        snapshot_path = service.snapshot_dir / "EGLC_2025-11-13.json"
        assert snapshot_path.exists()

        # Verify snapshot content
        with open(snapshot_path) as f:
            saved_data = json.load(f)
            assert len(saved_data) == 2
            assert saved_data[0]["station"] == "EGLC"

    @patch("venues.metar.metar_service.requests.get")
    def test_parse_observation_invalid_time(self, mock_get, service):
        """Test handling of invalid time format."""
        response = [
            {
                "station": "EGLC",
                "time": "invalid-time-format",
                "temp": 15.0,
            }
        ]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = response
        mock_get.return_value = mock_response

        observations = service.get_observations("EGLC", date(2025, 11, 13))

        # Should skip invalid observations
        assert len(observations) == 0

    @patch("venues.metar.metar_service.requests.get")
    def test_parse_observation_missing_fields(self, mock_get, service):
        """Test handling of missing required fields."""
        response = [
            {
                # Missing station and time
                "temp": 15.0,
            }
        ]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = response
        mock_get.return_value = mock_response

        observations = service.get_observations("EGLC", date(2025, 11, 13))

        # Should skip invalid observations
        assert len(observations) == 0

    @patch("venues.metar.metar_service.requests.get")
    def test_default_date_today(self, mock_get, service, sample_metar_response):
        """Test that default date is today."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_metar_response
        mock_get.return_value = mock_response

        today = date.today()
        service.get_observations("EGLC")

        # Verify API was called with today's date
        call_args = mock_get.call_args
        params = call_args[1]["params"]
        assert today.isoformat() in params["start"]

    @patch("venues.metar.metar_service.requests.get")
    def test_custom_hours(self, mock_get, service, sample_metar_response):
        """Test custom hours parameter."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_metar_response
        mock_get.return_value = mock_response

        service.get_observations("EGLC", date(2025, 11, 13), hours=12)

        # Verify hours parameter affects time range
        call_args = mock_get.call_args
        params = call_args[1]["params"]
        assert "start" in params
        assert "end" in params

