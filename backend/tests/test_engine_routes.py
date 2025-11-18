"""Tests for engine control API routes."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from backend.api.main import app

client = TestClient(app)


@pytest.fixture
def sample_start_request():
    """Sample engine start request."""
    return {
        "stations": ["EGLC", "KLGA"],
        "interval_seconds": 900,
        "lookahead_days": 2,
        "trading": {
            "edge_min": 0.05,
            "fee_bp": 50,
            "slippage_bp": 30,
            "kelly_cap": 0.10,
            "per_market_cap": 500.0,
            "liquidity_min_usd": 1000.0,
            "daily_bankroll_cap": 3000.0,
        },
        "probability_model": {
            "model_mode": "spread",
            "zeus_likely_pct": 0.80,
            "zeus_possible_pct": 0.95,
        },
    }


class TestEngineRoutes:
    """Test engine control API endpoints."""
    
    @patch("backend.api.routes.engine.engine_service")
    def test_start_engine_success(self, mock_service, sample_start_request):
        """Test starting engine successfully."""
        mock_service.start_engine.return_value = {
            "success": True,
            "message": "Trading engine started",
            "pid": 12345,
            "status": "running",
        }
        
        response = client.post("/api/engine/start", json=sample_start_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["pid"] == 12345
    
    @patch("backend.api.routes.engine.engine_service")
    def test_start_engine_failure(self, mock_service, sample_start_request):
        """Test starting engine with failure."""
        mock_service.start_engine.return_value = {
            "success": False,
            "message": "Engine already running",
        }
        
        response = client.post("/api/engine/start", json=sample_start_request)
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
    
    @patch("backend.api.routes.engine.engine_service")
    def test_stop_engine_success(self, mock_service):
        """Test stopping engine successfully."""
        mock_service.stop_engine.return_value = {
            "success": True,
            "message": "Trading engine stopped",
            "pid": 12345,
        }
        
        response = client.post("/api/engine/stop")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    @patch("backend.api.routes.engine.engine_service")
    def test_stop_engine_failure(self, mock_service):
        """Test stopping engine when not running."""
        mock_service.stop_engine.return_value = {
            "success": False,
            "message": "Engine not running",
        }
        
        response = client.post("/api/engine/stop")
        
        assert response.status_code == 400
    
    @patch("backend.api.routes.engine.engine_service")
    def test_restart_engine_success(self, mock_service, sample_start_request):
        """Test restarting engine successfully."""
        mock_service.restart_engine.return_value = {
            "success": True,
            "message": "Trading engine restarted",
            "pid": 12346,
            "status": "running",
        }
        
        response = client.post("/api/engine/restart", json=sample_start_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["pid"] == 12346
    
    @patch("backend.api.routes.engine.engine_service")
    def test_get_engine_config_success(self, mock_service):
        """Test getting engine configuration."""
        mock_service.get_engine_config.return_value = {
            "stations": ["EGLC", "KLGA"],
            "interval_seconds": 900,
            "trading": {"edge_min": 0.05},
        }
        
        response = client.get("/api/engine/config")
        
        assert response.status_code == 200
        data = response.json()
        assert "stations" in data
        assert "trading" in data
    
    @patch("backend.api.routes.engine.engine_service")
    def test_get_engine_config_not_found(self, mock_service):
        """Test getting engine configuration when not running."""
        mock_service.get_engine_config.return_value = None
        
        response = client.get("/api/engine/config")
        
        assert response.status_code == 404

