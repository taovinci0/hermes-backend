"""Tests for config service."""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from backend.api.services.config_service import ConfigService


@pytest.fixture
def config_service(tmp_path):
    """Create config service with temporary directories."""
    service = ConfigService()
    # Override paths to use temp directory
    service.config_path = tmp_path / ".env"
    service.yaml_config_path = tmp_path / "config.local.yaml"
    service.backup_dir = tmp_path / "backups"
    service.backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Create initial .env file
    with open(service.config_path, "w") as f:
        f.write("EDGE_MIN=0.05\n")
        f.write("FEE_BP=50\n")
        f.write("MODEL_MODE=spread\n")
    
    return service


class TestConfigService:
    """Test config service functionality."""
    
    @patch("backend.api.services.config_service.Config")
    def test_get_config(self, mock_config_class, config_service):
        """Test getting configuration."""
        # Mock config object
        mock_config = MagicMock()
        mock_config.trading.active_stations = ["EGLC", "KLGA"]
        mock_config.trading.edge_min = 0.05
        mock_config.trading.fee_bp = 50
        mock_config.trading.slippage_bp = 30
        mock_config.trading.kelly_cap = 0.10
        mock_config.trading.daily_bankroll_cap = 3000.0
        mock_config.trading.per_market_cap = 500.0
        mock_config.trading.liquidity_min_usd = 1000.0
        mock_config.model_mode = "spread"
        mock_config.zeus_likely_pct = 0.80
        mock_config.zeus_possible_pct = 0.95
        mock_config.dynamic_interval_seconds = 900
        mock_config.dynamic_lookahead_days = 2
        mock_config.execution_mode = "paper"
        mock_config.zeus.api_key = "test_key_1234"
        
        mock_config_class.load.return_value = mock_config
        
        config = config_service.get_config()
        
        assert "trading" in config
        assert "probability_model" in config
        assert "dynamic_trading" in config
        assert config["execution_mode"] == "paper"
        assert "api_keys" in config
    
    def test_validate_config_valid(self, config_service):
        """Test validation with valid configuration."""
        valid_config = {
            "trading": {
                "edge_min": 0.05,
                "fee_bp": 50,
                "slippage_bp": 30,
                "kelly_cap": 0.10,
            },
            "probability_model": {
                "model_mode": "spread",
                "zeus_likely_pct": 0.80,
                "zeus_possible_pct": 0.95,
            },
        }
        
        is_valid, errors = config_service.validate_config(valid_config)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_config_invalid_edge_min(self, config_service):
        """Test validation with invalid edge_min."""
        invalid_config = {
            "trading": {
                "edge_min": 0.60,  # Too high
            },
        }
        
        is_valid, errors = config_service.validate_config(invalid_config)
        assert is_valid is False
        assert any("edge_min" in error for error in errors)
    
    def test_validate_config_invalid_model_mode(self, config_service):
        """Test validation with invalid model_mode."""
        invalid_config = {
            "probability_model": {
                "model_mode": "invalid",
            },
        }
        
        is_valid, errors = config_service.validate_config(invalid_config)
        assert is_valid is False
        assert any("model_mode" in error for error in errors)
    
    def test_validate_config_cross_field_validation(self, config_service):
        """Test cross-field validation (zeus_possible_pct > zeus_likely_pct)."""
        invalid_config = {
            "probability_model": {
                "zeus_likely_pct": 0.90,
                "zeus_possible_pct": 0.80,  # Less than likely_pct
            },
        }
        
        is_valid, errors = config_service.validate_config(invalid_config)
        assert is_valid is False
        assert any("zeus_possible_pct must be greater" in error for error in errors)
    
    def test_validate_config_invalid_station(self, config_service):
        """Test validation with invalid station code."""
        invalid_config = {
            "trading": {
                "active_stations": ["INVALID"],
            },
        }
        
        is_valid, errors = config_service.validate_config(invalid_config)
        assert is_valid is False
        assert any("Station INVALID not found" in error for error in errors)
    
    def test_update_env_file(self, config_service):
        """Test updating .env file."""
        updates = {
            "trading": {
                "edge_min": 0.06,
                "fee_bp": 60,
            },
            "dynamic_trading": {
                "interval_seconds": 1800,
            },
        }
        
        config_service._update_env_file(updates)
        
        # Read back
        with open(config_service.config_path, "r") as f:
            content = f.read()
        
        assert "EDGE_MIN=0.06" in content
        assert "FEE_BP=60" in content
        assert "DYNAMIC_INTERVAL_SECONDS=1800" in content
    
    def test_update_config_success(self, config_service):
        """Test updating configuration successfully."""
        updates = {
            "trading": {
                "edge_min": 0.06,
            },
        }
        
        result = config_service.update_config(updates)
        
        assert result["success"] is True
        assert "trading.edge_min" in result["updated_fields"]
        assert config_service.backup_dir.exists()
    
    def test_update_config_validation_failure(self, config_service):
        """Test updating configuration with validation failure."""
        updates = {
            "trading": {
                "edge_min": 0.60,  # Invalid
            },
        }
        
        result = config_service.update_config(updates)
        
        assert result["success"] is False
        assert "errors" in result
    
    def test_requires_restart(self, config_service):
        """Test _requires_restart detection."""
        # Should require restart
        updates1 = {
            "trading": {
                "active_stations": ["EGLC"],
            },
        }
        assert config_service._requires_restart(updates1) is True
        
        # Should not require restart
        updates2 = {
            "trading": {
                "edge_min": 0.06,
            },
        }
        assert config_service._requires_restart(updates2) is False
    
    def test_get_updated_fields(self, config_service):
        """Test getting list of updated fields."""
        updates = {
            "trading": {
                "edge_min": 0.06,
                "fee_bp": 60,
            },
            "execution_mode": "live",
        }
        
        fields = config_service._get_updated_fields(updates)
        
        assert "trading.edge_min" in fields
        assert "trading.fee_bp" in fields
        assert "execution_mode" in fields
    
    def test_get_default_config(self, config_service):
        """Test getting default configuration."""
        defaults = config_service.get_default_config()
        
        assert "trading" in defaults
        assert "probability_model" in defaults
        assert "dynamic_trading" in defaults
        assert defaults["execution_mode"] == "paper"
    
    @patch.object(ConfigService, "update_config")
    def test_reset_to_defaults(self, mock_update, config_service):
        """Test resetting to defaults."""
        mock_update.return_value = {"success": True, "message": "Reset"}
        
        result = config_service.reset_to_defaults()
        
        assert result["success"] is True
        mock_update.assert_called_once()

