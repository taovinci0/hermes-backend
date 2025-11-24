"""Service for managing global configuration."""

import os
import yaml
import shutil
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from core.config import Config, PROJECT_ROOT
from ..utils.path_utils import PROJECT_ROOT as API_PROJECT_ROOT


class ConfigService:
    """Service for reading and writing configuration."""
    
    def __init__(self):
        """Initialize config service."""
        self.config_path = PROJECT_ROOT / ".env"
        self.yaml_config_path = PROJECT_ROOT / "config.local.yaml"
        self.backup_dir = PROJECT_ROOT / "data" / "config_backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration.
        
        Returns:
            Dictionary with all configuration values
        """
        config = Config.load()
        
        return {
            "trading": {
                "active_stations": config.trading.active_stations,
                "edge_min": config.trading.edge_min,
                "fee_bp": config.trading.fee_bp,
                "slippage_bp": config.trading.slippage_bp,
                "kelly_cap": config.trading.kelly_cap,
                "daily_bankroll_cap": config.trading.daily_bankroll_cap,
                "per_market_cap": config.trading.per_market_cap,
                "liquidity_min_usd": config.trading.liquidity_min_usd,
            },
            "probability_model": {
                "model_mode": config.model_mode,
                "zeus_likely_pct": config.zeus_likely_pct,
                "zeus_possible_pct": config.zeus_possible_pct,
                "sigma_default": 2.0,  # TODO: Add to config if needed
                "sigma_min": 0.5,  # TODO: Add to config if needed
                "sigma_max": 10.0,  # TODO: Add to config if needed
            },
            "dynamic_trading": {
                "interval_seconds": config.dynamic_interval_seconds,
                "lookahead_days": config.dynamic_lookahead_days,
            },
            "execution_mode": config.execution_mode,
            "api_keys": self._get_masked_api_keys(),
        }
    
    def update_config(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update configuration values.
        
        Args:
            updates: Dictionary with configuration updates
            
        Returns:
            Dictionary with success status and updated fields
        """
        # Validate before updating
        is_valid, errors = self.validate_config(updates)
        if not is_valid:
            return {
                "success": False,
                "errors": errors,
            }
        
        # Get old config for changelog
        old_config = self.get_config()
        
        # Backup current config
        self._backup_config()
        
        # Update .env file
        self._update_env_file(updates)
        
        # Update YAML file if needed
        self._update_yaml_file(updates)
        
        # Get new config for changelog
        new_config = self.get_config()
        
        # Log configuration change to strategy changelog
        try:
            from .strategy_service import StrategyService
            strategy_service = StrategyService()
            strategy_service.log_configuration_change(
                old_config=old_config,
                new_config=new_config,
            )
        except Exception as e:
            # Don't fail the update if changelog logging fails
            import logging
            logging.warning(f"Failed to log configuration change to changelog: {e}")
        
        # Determine if restart is required
        requires_restart = self._requires_restart(updates)
        
        return {
            "success": True,
            "message": "Configuration updated",
            "requires_restart": requires_restart,
            "updated_fields": self._get_updated_fields(updates),
        }
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate configuration values.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate trading config
        if "trading" in config:
            trading = config["trading"]
            if "edge_min" in trading:
                if not 0.01 <= trading["edge_min"] <= 0.50:
                    errors.append("edge_min must be between 0.01 and 0.50")
            if "fee_bp" in trading:
                if not 0 <= trading["fee_bp"] <= 1000:
                    errors.append("fee_bp must be between 0 and 1000")
            if "slippage_bp" in trading:
                if not 0 <= trading["slippage_bp"] <= 1000:
                    errors.append("slippage_bp must be between 0 and 1000")
            if "kelly_cap" in trading:
                if not 0.01 <= trading["kelly_cap"] <= 0.50:
                    errors.append("kelly_cap must be between 0.01 and 0.50")
            if "daily_bankroll_cap" in trading:
                if trading["daily_bankroll_cap"] < 0:
                    errors.append("daily_bankroll_cap must be >= 0")
            if "per_market_cap" in trading:
                if trading["per_market_cap"] < 0:
                    errors.append("per_market_cap must be >= 0")
            if "liquidity_min_usd" in trading:
                if trading["liquidity_min_usd"] < 0:
                    errors.append("liquidity_min_usd must be >= 0")
            if "active_stations" in trading:
                # Validate stations exist in registry
                from core.registry import get_registry
                registry = get_registry()
                for station in trading["active_stations"]:
                    if not registry.get(station):
                        errors.append(f"Station {station} not found in registry")
        
        # Validate probability model config
        if "probability_model" in config:
            prob = config["probability_model"]
            if "model_mode" in prob:
                if prob["model_mode"] not in ["spread", "bands"]:
                    errors.append("model_mode must be 'spread' or 'bands'")
            if "zeus_likely_pct" in prob:
                if not 0.50 <= prob["zeus_likely_pct"] <= 0.99:
                    errors.append("zeus_likely_pct must be between 0.50 and 0.99")
            if "zeus_possible_pct" in prob:
                if not 0.80 <= prob["zeus_possible_pct"] <= 0.99:
                    errors.append("zeus_possible_pct must be between 0.80 and 0.99")
            # Cross-field validation
            if "zeus_likely_pct" in prob and "zeus_possible_pct" in prob:
                if prob["zeus_possible_pct"] <= prob["zeus_likely_pct"]:
                    errors.append("zeus_possible_pct must be greater than zeus_likely_pct")
        
        # Validate dynamic trading config
        if "dynamic_trading" in config:
            dyn = config["dynamic_trading"]
            if "interval_seconds" in dyn:
                if not 60 <= dyn["interval_seconds"] <= 3600:
                    errors.append("interval_seconds must be between 60 and 3600")
            if "lookahead_days" in dyn:
                if not 1 <= dyn["lookahead_days"] <= 7:
                    errors.append("lookahead_days must be between 1 and 7")
        
        # Validate execution mode
        if "execution_mode" in config:
            if config["execution_mode"] not in ["paper", "live"]:
                errors.append("execution_mode must be 'paper' or 'live'")
        
        return len(errors) == 0, errors
    
    def reload_config(self) -> Dict[str, Any]:
        """Reload configuration from disk.
        
        Returns:
            Current configuration
        """
        # Force reload by clearing any caches
        # (Config.load() already reads from disk each time)
        return self.get_config()
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values.
        
        Returns:
            Dictionary with default values
        """
        return {
            "trading": {
                "active_stations": ["EGLC", "KLGA"],
                "edge_min": 0.05,
                "fee_bp": 50,
                "slippage_bp": 30,
                "kelly_cap": 0.10,
                "daily_bankroll_cap": 3000.0,
                "per_market_cap": 500.0,
                "liquidity_min_usd": 1000.0,
            },
            "probability_model": {
                "model_mode": "spread",
                "zeus_likely_pct": 0.80,
                "zeus_possible_pct": 0.95,
                "sigma_default": 2.0,
                "sigma_min": 0.5,
                "sigma_max": 10.0,
            },
            "dynamic_trading": {
                "interval_seconds": 900,
                "lookahead_days": 2,
            },
            "execution_mode": "paper",
        }
    
    def reset_to_defaults(self) -> Dict[str, Any]:
        """Reset configuration to defaults.
        
        Returns:
            Dictionary with success status
        """
        defaults = self.get_default_config()
        result = self.update_config(defaults)
        return result
    
    def _get_masked_api_keys(self) -> Dict[str, str]:
        """Get masked API keys for display.
        
        Returns:
            Dictionary with masked API keys
        """
        config = Config.load()
        
        def mask_key(key: str) -> str:
            if not key or len(key) < 4:
                return "****"
            return f"****{key[-4:]}"
        
        return {
            "zeus_api_key": mask_key(config.zeus.api_key),
            "polymarket_api_key": "****",  # Not in config yet
            "polymarket_private_key": "****",  # Not in config yet
            "polymarket_wallet_address": "",  # Not in config yet
        }
    
    def _backup_config(self) -> None:
        """Backup current configuration."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"config_backup_{timestamp}.env"
        
        if self.config_path.exists():
            shutil.copy(self.config_path, backup_file)
    
    def _update_env_file(self, updates: Dict[str, Any]) -> None:
        """Update .env file with new values."""
        # Read current .env
        env_vars = {}
        comments = []
        
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                for line in f:
                    line_stripped = line.strip()
                    if line_stripped and not line_stripped.startswith("#"):
                        if "=" in line_stripped:
                            key, value = line_stripped.split("=", 1)
                            env_vars[key.strip()] = value.strip()
                    elif line_stripped.startswith("#"):
                        # Preserve comments
                        comments.append(line.rstrip())
        
        # Update with new values
        if "trading" in updates:
            trading = updates["trading"]
            if "active_stations" in trading:
                env_vars["ACTIVE_STATIONS"] = ",".join(trading["active_stations"])
            if "edge_min" in trading:
                env_vars["EDGE_MIN"] = str(trading["edge_min"])
            if "fee_bp" in trading:
                env_vars["FEE_BP"] = str(trading["fee_bp"])
            if "slippage_bp" in trading:
                env_vars["SLIPPAGE_BP"] = str(trading["slippage_bp"])
            if "kelly_cap" in trading:
                env_vars["KELLY_CAP"] = str(trading["kelly_cap"])
            if "daily_bankroll_cap" in trading:
                env_vars["DAILY_BANKROLL_CAP"] = str(trading["daily_bankroll_cap"])
            if "per_market_cap" in trading:
                env_vars["PER_MARKET_CAP"] = str(trading["per_market_cap"])
            if "liquidity_min_usd" in trading:
                env_vars["LIQUIDITY_MIN_USD"] = str(trading["liquidity_min_usd"])
        
        if "probability_model" in updates:
            prob = updates["probability_model"]
            if "model_mode" in prob:
                env_vars["MODEL_MODE"] = prob["model_mode"]
            if "zeus_likely_pct" in prob:
                env_vars["ZEUS_LIKELY_PCT"] = str(prob["zeus_likely_pct"])
            if "zeus_possible_pct" in prob:
                env_vars["ZEUS_POSSIBLE_PCT"] = str(prob["zeus_possible_pct"])
        
        if "dynamic_trading" in updates:
            dyn = updates["dynamic_trading"]
            if "interval_seconds" in dyn:
                env_vars["DYNAMIC_INTERVAL_SECONDS"] = str(dyn["interval_seconds"])
            if "lookahead_days" in dyn:
                env_vars["DYNAMIC_LOOKAHEAD_DAYS"] = str(dyn["lookahead_days"])
        
        if "execution_mode" in updates:
            env_vars["EXECUTION_MODE"] = updates["execution_mode"]
        
        # Write back to .env (preserve existing keys not being updated)
        with open(self.config_path, "w") as f:
            # Write comments first
            for comment in comments:
                f.write(comment + "\n")
            # Write all env vars
            for key, value in sorted(env_vars.items()):
                f.write(f"{key}={value}\n")
    
    def _update_yaml_file(self, updates: Dict[str, Any]) -> None:
        """Update config.local.yaml if it exists.
        
        For now, we'll primarily use .env
        YAML can be used for complex nested configs later
        """
        # TODO: Implement YAML updates if needed
        pass
    
    def _requires_restart(self, updates: Dict[str, Any]) -> bool:
        """Check if updates require engine restart.
        
        Args:
            updates: Configuration updates
            
        Returns:
            True if restart is required
        """
        # These changes require restart
        restart_required_keys = [
            ("trading", "active_stations"),
            ("dynamic_trading", "interval_seconds"),
            ("dynamic_trading", "lookahead_days"),
            ("execution_mode", None),
        ]
        
        for section, field in restart_required_keys:
            if field is None:
                # Top-level key
                if section in updates:
                    return True
            else:
                if section in updates and field in updates[section]:
                    return True
        
        return False
    
    def _get_updated_fields(self, updates: Dict[str, Any]) -> List[str]:
        """Get list of updated field paths.
        
        Args:
            updates: Configuration updates
            
        Returns:
            List of field paths (e.g., ["trading.edge_min"])
        """
        fields = []
        for section, values in updates.items():
            if isinstance(values, dict):
                for field in values.keys():
                    fields.append(f"{section}.{field}")
            else:
                fields.append(section)
        return fields

