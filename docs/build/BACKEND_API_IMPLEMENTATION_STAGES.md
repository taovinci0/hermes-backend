# Backend & API Implementation Plan - Staged Approach

**Date**: November 17, 2025  
**Purpose**: Detailed staged implementation plan for backend services and API endpoints for configuration management and engine control

---

## 🎯 Overview

This document outlines the backend and API implementation in **4 stages**, building from core functionality to advanced features.

**Stages**:
1. **Stage 1**: Engine Control Service & Endpoints
2. **Stage 2**: Configuration Service & Endpoints
3. **Stage 3**: Dynamic Engine Modifications
4. **Stage 4**: Validation, Error Handling & Testing

---

## 📋 Prerequisites

Before starting, ensure:
- ✅ FastAPI backend is running
- ✅ Existing endpoints (`/api/status`, `/api/backtest/run`) are working
- ✅ `StatusService` exists and can check engine status
- ✅ Dynamic trading engine can be started via command line

---

## 🚀 Stage 1: Engine Control Service & Endpoints

**Goal**: Enable starting, stopping, and restarting the trading engine via API

**Estimated Time**: 2-3 hours

### 1.1 Create Engine Service

**File**: `backend/api/services/engine_service.py`

**Implementation**:
```python
"""Service for controlling the trading engine process."""

import subprocess
import signal
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from ..utils.path_utils import PROJECT_ROOT


class EngineService:
    """Service for managing trading engine lifecycle."""
    
    def __init__(self):
        """Initialize engine service."""
        self.logs_dir = PROJECT_ROOT / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        self.pid_file = self.logs_dir / "dynamic_paper.pid"
        self.config_file = self.logs_dir / "engine_config.json"
    
    def start_engine(
        self,
        stations: List[str],
        interval_seconds: int,
        lookahead_days: int,
        trading_config: Dict[str, Any],
        probability_model_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Start trading engine with configuration.
        
        Args:
            stations: List of station codes
            interval_seconds: Evaluation interval
            lookahead_days: Days ahead to check
            trading_config: Trading parameters
            probability_model_config: Probability model parameters
            
        Returns:
            Dictionary with success status, PID, and message
        """
        # Check if already running
        if self.is_running():
            return {
                "success": False,
                "message": "Trading engine is already running",
                "pid": self._get_pid(),
            }
        
        # Save configuration
        engine_config = {
            "stations": stations,
            "interval_seconds": interval_seconds,
            "lookahead_days": lookahead_days,
            "trading": trading_config,
            "probability_model": probability_model_config,
            "started_at": datetime.utcnow().isoformat(),
        }
        self._save_config(engine_config)
        
        # Build command
        stations_str = ",".join(stations)
        cmd = [
            sys.executable,
            "-m",
            "core.orchestrator",
            "--mode",
            "dynamic-paper",
            "--stations",
            stations_str,
        ]
        
        # Set environment variables for config
        env = self._build_env(engine_config)
        
        # Start process
        try:
            log_file = self.logs_dir / f"dynamic_paper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            with open(log_file, "w") as f:
                process = subprocess.Popen(
                    cmd,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    env=env,
                    cwd=str(PROJECT_ROOT),
                )
            
            # Save PID
            self.pid_file.write_text(str(process.pid))
            
            return {
                "success": True,
                "message": "Trading engine started",
                "pid": process.pid,
                "status": "running",
                "config": engine_config,
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to start engine: {str(e)}",
            }
    
    def stop_engine(self) -> Dict[str, Any]:
        """Stop trading engine gracefully.
        
        Returns:
            Dictionary with success status and message
        """
        if not self.is_running():
            return {
                "success": False,
                "message": "Trading engine is not running",
            }
        
        try:
            pid = self._get_pid()
            if pid:
                # Send SIGINT for graceful shutdown
                os.kill(pid, signal.SIGINT)
                
                # Wait up to 10 seconds for graceful shutdown
                import time
                for _ in range(10):
                    if not self.is_running():
                        break
                    time.sleep(1)
                
                # Force kill if still running
                if self.is_running():
                    os.kill(pid, signal.SIGKILL)
                
                # Clean up PID file
                if self.pid_file.exists():
                    self.pid_file.unlink()
                
                return {
                    "success": True,
                    "message": "Trading engine stopped",
                    "pid": pid,
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to stop engine: {str(e)}",
            }
    
    def restart_engine(
        self,
        stations: List[str],
        interval_seconds: int,
        lookahead_days: int,
        trading_config: Dict[str, Any],
        probability_model_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Restart trading engine with new configuration.
        
        Args:
            Same as start_engine
            
        Returns:
            Dictionary with success status, PID, and message
        """
        # Stop if running
        if self.is_running():
            stop_result = self.stop_engine()
            if not stop_result["success"]:
                return {
                    "success": False,
                    "message": f"Failed to stop engine: {stop_result['message']}",
                }
        
        # Start with new config
        return self.start_engine(
            stations=stations,
            interval_seconds=interval_seconds,
            lookahead_days=lookahead_days,
            trading_config=trading_config,
            probability_model_config=probability_model_config,
        )
    
    def get_engine_config(self) -> Optional[Dict[str, Any]]:
        """Get current engine configuration.
        
        Returns:
            Engine configuration dictionary, or None if not running
        """
        if not self.config_file.exists():
            return None
        
        try:
            with open(self.config_file, "r") as f:
                return json.load(f)
        except Exception:
            return None
    
    def is_running(self) -> bool:
        """Check if engine is running.
        
        Returns:
            True if engine process is running
        """
        if not self.pid_file.exists():
            return False
        
        try:
            pid = int(self.pid_file.read_text().strip())
            result = subprocess.run(
                ["ps", "-p", str(pid)],
                capture_output=True,
                timeout=2,
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _get_pid(self) -> Optional[int]:
        """Get engine PID from file.
        
        Returns:
            PID or None
        """
        if not self.pid_file.exists():
            return None
        try:
            return int(self.pid_file.read_text().strip())
        except Exception:
            return None
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save engine configuration to file."""
        with open(self.config_file, "w") as f:
            json.dump(config, f, indent=2)
    
    def _build_env(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Build environment variables from configuration.
        
        Note: For now, we'll pass config via environment variables.
        Later stages will improve this.
        """
        import os
        env = os.environ.copy()
        
        # Set trading config
        trading = config["trading"]
        env["EDGE_MIN"] = str(trading.get("edge_min", 0.05))
        env["FEE_BP"] = str(trading.get("fee_bp", 50))
        env["SLIPPAGE_BP"] = str(trading.get("slippage_bp", 30))
        env["KELLY_CAP"] = str(trading.get("kelly_cap", 0.10))
        env["PER_MARKET_CAP"] = str(trading.get("per_market_cap", 500.0))
        env["LIQUIDITY_MIN_USD"] = str(trading.get("liquidity_min_usd", 1000.0))
        env["DAILY_BANKROLL_CAP"] = str(trading.get("daily_bankroll_cap", 3000.0))
        
        # Set probability model config
        prob = config["probability_model"]
        env["MODEL_MODE"] = prob.get("model_mode", "spread")
        env["ZEUS_LIKELY_PCT"] = str(prob.get("zeus_likely_pct", 0.80))
        env["ZEUS_POSSIBLE_PCT"] = str(prob.get("zeus_possible_pct", 0.95))
        
        # Set dynamic trading config
        env["DYNAMIC_INTERVAL_SECONDS"] = str(config["interval_seconds"])
        env["DYNAMIC_LOOKAHEAD_DAYS"] = str(config["lookahead_days"])
        
        return env
```

**Dependencies**:
- `import os` (for `os.kill`)
- `import signal` (for `signal.SIGINT`, `signal.SIGKILL`)

### 1.2 Create Engine Routes

**File**: `backend/api/routes/engine.py`

**Implementation**:
```python
"""Engine control endpoints."""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel

from ..services.engine_service import EngineService

router = APIRouter()
engine_service = EngineService()


class TradingConfig(BaseModel):
    """Trading parameters."""
    edge_min: float
    fee_bp: int
    slippage_bp: int
    kelly_cap: float
    per_market_cap: float
    liquidity_min_usd: float
    daily_bankroll_cap: float


class ProbabilityModelConfig(BaseModel):
    """Probability model parameters."""
    model_mode: str
    zeus_likely_pct: float
    zeus_possible_pct: float


class StartEngineRequest(BaseModel):
    """Request to start engine."""
    stations: List[str]
    interval_seconds: int
    lookahead_days: int
    trading: TradingConfig
    probability_model: ProbabilityModelConfig


@router.post("/start")
async def start_engine(request: StartEngineRequest):
    """Start trading engine with configuration."""
    result = engine_service.start_engine(
        stations=request.stations,
        interval_seconds=request.interval_seconds,
        lookahead_days=request.lookahead_days,
        trading_config=request.trading.dict(),
        probability_model_config=request.probability_model.dict(),
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.post("/stop")
async def stop_engine():
    """Stop trading engine."""
    result = engine_service.stop_engine()
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.post("/restart")
async def restart_engine(request: StartEngineRequest):
    """Restart trading engine with new configuration."""
    result = engine_service.restart_engine(
        stations=request.stations,
        interval_seconds=request.interval_seconds,
        lookahead_days=request.lookahead_days,
        trading_config=request.trading.dict(),
        probability_model_config=request.probability_model.dict(),
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.get("/config")
async def get_engine_config():
    """Get current engine configuration."""
    config = engine_service.get_engine_config()
    
    if config is None:
        raise HTTPException(status_code=404, detail="Engine not running or no config found")
    
    return config
```

### 1.3 Register Routes

**File**: `backend/api/main.py`

**Add**:
```python
from .routes import engine

app.include_router(engine.router, prefix="/api/engine", tags=["engine"])
```

### 1.4 Testing

**Manual Testing**:
1. Start backend API
2. Test `POST /api/engine/start` with valid config
3. Verify engine starts and PID file is created
4. Test `GET /api/engine/config` returns config
5. Test `POST /api/engine/stop` stops engine
6. Test `POST /api/engine/restart` restarts with new config

**Expected Results**:
- ✅ Engine can be started via API
- ✅ Engine can be stopped via API
- ✅ Engine can be restarted via API
- ✅ Configuration is saved and retrievable

---

## 🔧 Stage 2: Configuration Service & Endpoints

**Goal**: Enable reading, writing, and validating global configuration

**Estimated Time**: 3-4 hours

### 2.1 Create Configuration Service

**File**: `backend/api/services/config_service.py`

**Implementation**:
```python
"""Service for managing global configuration."""

import os
import yaml
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

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
                "sigma_default": 2.0,  # TODO: Add to config
                "sigma_min": 0.5,  # TODO: Add to config
                "sigma_max": 10.0,  # TODO: Add to config
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
        
        # Backup current config
        self._backup_config()
        
        # Update .env file
        self._update_env_file(updates)
        
        # Update YAML file if needed
        self._update_yaml_file(updates)
        
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
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"config_backup_{timestamp}.env"
        
        if self.config_path.exists():
            import shutil
            shutil.copy(self.config_path, backup_file)
    
    def _update_env_file(self, updates: Dict[str, Any]) -> None:
        """Update .env file with new values."""
        # Read current .env
        env_vars = {}
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key.strip()] = value.strip()
        
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
        
        # Write back to .env
        with open(self.config_path, "w") as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
    
    def _update_yaml_file(self, updates: Dict[str, Any]) -> None:
        """Update config.local.yaml if it exists."""
        # For now, we'll primarily use .env
        # YAML can be used for complex nested configs later
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
            "trading.active_stations",
            "dynamic_trading.interval_seconds",
            "dynamic_trading.lookahead_days",
            "execution_mode",
        ]
        
        for key in restart_required_keys:
            section, field = key.split(".")
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
```

### 2.2 Create Configuration Routes

**File**: `backend/api/routes/config.py`

**Implementation**:
```python
"""Configuration management endpoints."""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel

from ..services.config_service import ConfigService

router = APIRouter()
config_service = ConfigService()


@router.get("")
async def get_config():
    """Get current configuration."""
    return config_service.get_config()


@router.put("")
async def update_config(updates: Dict[str, Any]):
    """Update configuration."""
    result = config_service.update_config(updates)
    
    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail={"message": "Configuration validation failed", "errors": result["errors"]}
        )
    
    return result


@router.post("/validate")
async def validate_config(config: Dict[str, Any]):
    """Validate configuration without saving."""
    is_valid, errors = config_service.validate_config(config)
    
    return {
        "valid": is_valid,
        "errors": errors,
    }


@router.post("/reload")
async def reload_config():
    """Reload configuration from disk."""
    return config_service.reload_config()


@router.get("/defaults")
async def get_default_config():
    """Get default configuration values."""
    return config_service.get_default_config()


@router.post("/reset")
async def reset_config():
    """Reset configuration to defaults."""
    result = config_service.reset_to_defaults()
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("errors", []))
    
    return result
```

### 2.3 Register Routes

**File**: `backend/api/main.py`

**Add**:
```python
from .routes import config

app.include_router(config.router, prefix="/api/config", tags=["config"])
```

### 2.4 Testing

**Manual Testing**:
1. Test `GET /api/config` returns current config
2. Test `PUT /api/config` with valid updates
3. Test `PUT /api/config` with invalid values (should fail validation)
4. Test `POST /api/config/validate` with valid/invalid config
5. Test `POST /api/config/reload` reloads from disk
6. Test `GET /api/config/defaults` returns defaults
7. Test `POST /api/config/reset` resets to defaults

**Expected Results**:
- ✅ Can read configuration via API
- ✅ Can update configuration via API
- ✅ Validation works correctly
- ✅ Invalid values are rejected
- ✅ Configuration is saved to `.env` file

---

## ⚙️ Stage 3: Dynamic Engine Modifications

**Goal**: Modify dynamic engine to accept and use configuration parameters

**Estimated Time**: 2-3 hours

### 3.1 Modify Dynamic Engine Constructor

**File**: `agents/dynamic_trader/dynamic_engine.py`

**Changes**:
```python
def __init__(
    self,
    stations: List[str],
    interval_seconds: int = 900,
    lookahead_days: int = 2,
    trading_config: Optional[Dict[str, Any]] = None,
    probability_model_config: Optional[Dict[str, Any]] = None,
):
    """Initialize dynamic trading engine.
    
    Args:
        stations: List of station codes
        interval_seconds: Time between evaluation cycles
        lookahead_days: How many days ahead to check
        trading_config: Trading parameters (if None, uses global config)
        probability_model_config: Probability model parameters (if None, uses global config)
    """
    self.stations = stations
    self.interval_seconds = interval_seconds
    self.lookahead_days = lookahead_days
    
    # Use provided config or fall back to global config
    if trading_config is None:
        trading_config = {
            "edge_min": config.trading.edge_min,
            "fee_bp": config.trading.fee_bp,
            "slippage_bp": config.trading.slippage_bp,
            "kelly_cap": config.trading.kelly_cap,
            "per_market_cap": config.trading.per_market_cap,
            "liquidity_min_usd": config.trading.liquidity_min_usd,
            "daily_bankroll_cap": config.trading.daily_bankroll_cap,
        }
    
    if probability_model_config is None:
        probability_model_config = {
            "model_mode": config.model_mode,
            "zeus_likely_pct": config.zeus_likely_pct,
            "zeus_possible_pct": config.zeus_possible_pct,
        }
    
    # Store configs
    self.trading_config = trading_config
    self.probability_model_config = probability_model_config
    
    # Components
    self.registry = StationRegistry()
    self.fetcher = DynamicFetcher()
    self.prob_mapper = ProbabilityMapper()
    self.sizer = Sizer(
        edge_min=trading_config["edge_min"],
        fee_bp=trading_config["fee_bp"],
        slippage_bp=trading_config["slippage_bp"],
        kelly_cap=trading_config["kelly_cap"],
        per_market_cap=trading_config["per_market_cap"],
        liquidity_min_usd=trading_config["liquidity_min_usd"],
    )
    self.broker = PaperBroker(save_prices=False)
    self.snapshotter = DynamicSnapshotter()
    
    logger.info(f"🚀 Dynamic Trading Engine initialized")
    logger.info(f"   Stations: {', '.join(stations)}")
    logger.info(f"   Interval: {interval_seconds}s ({interval_seconds/60:.0f} min)")
    logger.info(f"   Lookahead: {lookahead_days} days")
    logger.info(f"   Model: {probability_model_config['model_mode']}")
    logger.info(f"   Edge Min: {trading_config['edge_min']*100:.1f}%")
```

### 3.2 Update Probability Mapper Usage

**File**: `agents/dynamic_trader/dynamic_engine.py`

**In `_evaluate_and_trade` method**, ensure probability mapper uses correct model:
```python
# Use model_mode from config
if self.probability_model_config["model_mode"] == "bands":
    # Use bands model
    probs = self.prob_mapper.map_to_brackets_bands(
        forecast,
        brackets,
        likely_pct=self.probability_model_config["zeus_likely_pct"],
        possible_pct=self.probability_model_config["zeus_possible_pct"],
    )
else:
    # Use spread model (default)
    probs = self.prob_mapper.map_to_brackets(forecast, brackets)
```

### 3.3 Update Orchestrator

**File**: `core/orchestrator.py`

**Modify `run_dynamic_paper` to accept config from environment**:
```python
def run_dynamic_paper(stations_str: str) -> None:
    """Run dynamic paper trading loop."""
    from agents.dynamic_trader.dynamic_engine import DynamicTradingEngine
    
    stations = [s.strip() for s in stations_str.split(',')]
    
    # Get config from environment (set by EngineService)
    trading_config = {
        "edge_min": float(os.getenv("EDGE_MIN", str(config.trading.edge_min))),
        "fee_bp": int(os.getenv("FEE_BP", str(config.trading.fee_bp))),
        "slippage_bp": int(os.getenv("SLIPPAGE_BP", str(config.trading.slippage_bp))),
        "kelly_cap": float(os.getenv("KELLY_CAP", str(config.trading.kelly_cap))),
        "per_market_cap": float(os.getenv("PER_MARKET_CAP", str(config.trading.per_market_cap))),
        "liquidity_min_usd": float(os.getenv("LIQUIDITY_MIN_USD", str(config.trading.liquidity_min_usd))),
        "daily_bankroll_cap": float(os.getenv("DAILY_BANKROLL_CAP", str(config.trading.daily_bankroll_cap))),
    }
    
    probability_model_config = {
        "model_mode": os.getenv("MODEL_MODE", config.model_mode),
        "zeus_likely_pct": float(os.getenv("ZEUS_LIKELY_PCT", str(config.zeus_likely_pct))),
        "zeus_possible_pct": float(os.getenv("ZEUS_POSSIBLE_PCT", str(config.zeus_possible_pct))),
    }
    
    interval_seconds = int(os.getenv("DYNAMIC_INTERVAL_SECONDS", str(config.dynamic_interval_seconds)))
    lookahead_days = int(os.getenv("DYNAMIC_LOOKAHEAD_DAYS", str(config.dynamic_lookahead_days)))
    
    logger.info(f"🚀 Launching dynamic paper trading")
    logger.info(f"Stations: {', '.join(stations)}")
    logger.info(f"Interval: {interval_seconds}s ({interval_seconds/60:.0f} minutes)")
    logger.info(f"Lookahead: {lookahead_days} days")
    
    # Create and run engine with config
    engine = DynamicTradingEngine(
        stations=stations,
        interval_seconds=interval_seconds,
        lookahead_days=lookahead_days,
        trading_config=trading_config,
        probability_model_config=probability_model_config,
    )
    
    # Run (blocks until Ctrl+C)
    engine.run()
```

### 3.4 Testing

**Manual Testing**:
1. Start engine via API with custom config
2. Verify engine uses provided config (check logs)
3. Verify probability mapper uses correct model
4. Verify sizer uses correct parameters
5. Stop and restart with different config
6. Verify new config is applied

**Expected Results**:
- ✅ Engine uses provided configuration
- ✅ Probability model mode is respected
- ✅ Trading parameters are applied correctly
- ✅ Config changes take effect on restart

---

## 🧪 Stage 4: Validation, Error Handling & Testing

**Goal**: Comprehensive validation, error handling, and unit tests

**Estimated Time**: 3-4 hours

### 4.1 Enhanced Validation

**File**: `backend/api/services/config_service.py`

**Add**:
- More comprehensive validation rules
- Cross-field validation (e.g., zeus_possible_pct > zeus_likely_pct)
- Station registry validation
- API key format validation

### 4.2 Error Handling

**Add**:
- Try-catch blocks in all service methods
- Proper error messages
- HTTP status codes
- Error logging

### 4.3 Unit Tests

**File**: `backend/tests/test_engine_service.py`

**Tests**:
- Test engine start/stop/restart
- Test config saving/loading
- Test process management
- Test error cases

**File**: `backend/tests/test_config_service.py`

**Tests**:
- Test config read/write
- Test validation rules
- Test error handling
- Test backup/restore

**File**: `backend/tests/test_engine_routes.py`

**Tests**:
- Test all endpoints
- Test request validation
- Test error responses

**File**: `backend/tests/test_config_routes.py`

**Tests**:
- Test all endpoints
- Test request validation
- Test error responses

### 4.4 Integration Tests

**Tests**:
- End-to-end engine start/stop flow
- Configuration update and engine restart flow
- Error scenarios

---

## ✅ Implementation Checklist

### Stage 1: Engine Control
- [ ] Create `EngineService` class
- [ ] Implement start/stop/restart methods
- [ ] Create engine routes
- [ ] Register routes in main.py
- [ ] Manual testing

### Stage 2: Configuration Service
- [ ] Create `ConfigService` class
- [ ] Implement read/write/validate methods
- [ ] Create config routes
- [ ] Register routes in main.py
- [ ] Manual testing

### Stage 3: Dynamic Engine Modifications
- [ ] Modify `DynamicTradingEngine.__init__`
- [ ] Update probability mapper usage
- [ ] Update orchestrator
- [ ] Manual testing

### Stage 4: Validation & Testing
- [ ] Enhanced validation
- [ ] Error handling
- [ ] Unit tests
- [ ] Integration tests

---

## 🚀 Deployment Notes

### After Implementation

1. **Update API Documentation**:
   - Add new endpoints to OpenAPI docs
   - Document request/response schemas
   - Add examples

2. **Update Frontend**:
   - Frontend can now use these endpoints
   - See `CONFIG_PAGE_IMPLEMENTATION_PLAN.md` for frontend details

3. **Monitor**:
   - Check logs for errors
   - Monitor engine process health
   - Verify configuration persistence

---

**Last Updated**: November 17, 2025

