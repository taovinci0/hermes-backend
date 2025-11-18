"""Tests for configuration API routes."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from backend.api.main import app

client = TestClient(app)


class TestConfigRoutes:
    """Test configuration API endpoints."""
    
    @patch("backend.api.routes.config.config_service")
    def test_get_config(self, mock_service):
        """Test getting configuration."""
        mock_service.get_config.return_value = {
            "trading": {"edge_min": 0.05},
            "execution_mode": "paper",
        }
        
        response = client.get("/api/config")
        
        assert response.status_code == 200
        data = response.json()
        assert "trading" in data
        assert "execution_mode" in data
    
    @patch("backend.api.routes.config.config_service")
    def test_update_config_success(self, mock_service):
        """Test updating configuration successfully."""
        mock_service.update_config.return_value = {
            "success": True,
            "message": "Configuration updated",
            "requires_restart": False,
            "updated_fields": ["trading.edge_min"],
        }
        
        updates = {
            "trading": {
                "edge_min": 0.06,
            },
        }
        
        response = client.put("/api/config", json=updates)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    @patch("backend.api.routes.config.config_service")
    def test_update_config_validation_failure(self, mock_service):
        """Test updating configuration with validation failure."""
        mock_service.update_config.return_value = {
            "success": False,
            "errors": ["edge_min must be between 0.01 and 0.50"],
        }
        
        updates = {
            "trading": {
                "edge_min": 0.60,  # Invalid
            },
        }
        
        response = client.put("/api/config", json=updates)
        
        assert response.status_code == 400
        data = response.json()
        assert "errors" in data["detail"]
    
    @patch("backend.api.routes.config.config_service")
    def test_validate_config_valid(self, mock_service):
        """Test validating valid configuration."""
        mock_service.validate_config.return_value = (True, [])
        
        config = {
            "trading": {
                "edge_min": 0.05,
            },
        }
        
        response = client.post("/api/config/validate", json=config)
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert len(data["errors"]) == 0
    
    @patch("backend.api.routes.config.config_service")
    def test_validate_config_invalid(self, mock_service):
        """Test validating invalid configuration."""
        mock_service.validate_config.return_value = (
            False,
            ["edge_min must be between 0.01 and 0.50"],
        )
        
        config = {
            "trading": {
                "edge_min": 0.60,
            },
        }
        
        response = client.post("/api/config/validate", json=config)
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert len(data["errors"]) > 0
    
    @patch("backend.api.routes.config.config_service")
    def test_reload_config(self, mock_service):
        """Test reloading configuration."""
        mock_service.reload_config.return_value = {
            "trading": {"edge_min": 0.05},
        }
        
        response = client.post("/api/config/reload")
        
        assert response.status_code == 200
        data = response.json()
        assert "trading" in data
    
    @patch("backend.api.routes.config.config_service")
    def test_get_default_config(self, mock_service):
        """Test getting default configuration."""
        mock_service.get_default_config.return_value = {
            "trading": {"edge_min": 0.05},
            "execution_mode": "paper",
        }
        
        response = client.get("/api/config/defaults")
        
        assert response.status_code == 200
        data = response.json()
        assert "trading" in data
    
    @patch("backend.api.routes.config.config_service")
    def test_reset_config_success(self, mock_service):
        """Test resetting configuration to defaults."""
        mock_service.reset_to_defaults.return_value = {
            "success": True,
            "message": "Configuration reset",
        }
        
        response = client.post("/api/config/reset")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    @patch("backend.api.routes.config.config_service")
    def test_reset_config_failure(self, mock_service):
        """Test resetting configuration with failure."""
        mock_service.reset_to_defaults.return_value = {
            "success": False,
            "errors": ["Failed to reset"],
        }
        
        response = client.post("/api/config/reset")
        
        assert response.status_code == 400

