"""Tests for METAR routes."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from api.main import app

client = TestClient(app)


class TestMetarEndpoints:
    """Test METAR endpoints."""
    
    def test_metar_observations_endpoint(self):
        """Test METAR observations endpoint."""
        with patch("api.routes.metar.metar_service.get_observations") as mock_get:
            mock_get.return_value = [
                {
                    "observation_time_utc": "2025-11-13T12:00:00+00:00",
                    "station_code": "EGLC",
                    "temp_F": 58.2,
                    "temp_C": 14.6,
                },
                {
                    "observation_time_utc": "2025-11-13T13:00:00+00:00",
                    "station_code": "EGLC",
                    "temp_F": 59.1,
                    "temp_C": 15.1,
                },
            ]
            
            response = client.get("/api/metar/observations?station_code=EGLC&event_day=2025-11-13")
            assert response.status_code == 200
            data = response.json()
            assert "observations" in data
            assert "count" in data
            assert data["count"] == 2
            assert data["observations"][0]["temp_F"] == 58.2
    
    def test_metar_daily_high_endpoint(self):
        """Test METAR daily high endpoint."""
        with patch("api.routes.metar.metar_service.get_daily_high") as mock_get:
            mock_get.return_value = 59.1
            
            response = client.get("/api/metar/daily-high?station_code=EGLC&event_day=2025-11-13")
            assert response.status_code == 200
            data = response.json()
            assert data["station_code"] == "EGLC"
            assert data["event_day"] == "2025-11-13"
            assert data["daily_high_f"] == 59.1
            assert data["available"] is True
    
    def test_metar_daily_high_no_data(self):
        """Test METAR daily high endpoint when no data available."""
        with patch("api.routes.metar.metar_service.get_daily_high") as mock_get:
            mock_get.return_value = None
            
            response = client.get("/api/metar/daily-high?station_code=EGLC&event_day=2025-11-13")
            assert response.status_code == 200
            data = response.json()
            assert data["station_code"] == "EGLC"
            assert data["daily_high_f"] is None
            assert data["available"] is False


class TestCompareEndpoints:
    """Test comparison endpoints."""
    
    def test_zeus_vs_metar_endpoint(self):
        """Test Zeus vs METAR comparison endpoint."""
        with patch("api.routes.compare.metar_service.compare_zeus_vs_metar") as mock_compare:
            mock_compare.return_value = {
                "station_code": "EGLC",
                "event_day": "2025-11-13",
                "zeus_prediction_f": 58.8,
                "metar_actual_f": 59.1,
                "error_f": -0.3,
                "error_pct": -0.51,
                "zeus_bracket": "58-59°F",
                "metar_bracket": "59-60°F",
                "brackets_match": False,
            }
            
            response = client.get("/api/compare/zeus-vs-metar?station_code=EGLC&event_day=2025-11-13")
            assert response.status_code == 200
            data = response.json()
            assert data["available"] is True
            assert data["zeus_prediction_f"] == 58.8
            assert data["metar_actual_f"] == 59.1
            assert data["error_f"] == -0.3
            assert data["brackets_match"] is False
    
    def test_zeus_vs_metar_no_data(self):
        """Test comparison endpoint when data is missing."""
        with patch("api.routes.compare.metar_service.compare_zeus_vs_metar") as mock_compare:
            mock_compare.return_value = None
            
            response = client.get("/api/compare/zeus-vs-metar?station_code=EGLC&event_day=2025-11-13")
            assert response.status_code == 200
            data = response.json()
            assert data["available"] is False
            assert "error" in data

