"""Service for controlling the trading engine process."""

import os
import signal
import subprocess
import sys
import json
import time
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
            "started_at": datetime.now().isoformat(),
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
        except ProcessLookupError:
            # Process already gone
            if self.pid_file.exists():
                self.pid_file.unlink()
            return {
                "success": True,
                "message": "Trading engine was not running",
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
            stations: List of station codes
            interval_seconds: Evaluation interval
            lookahead_days: Days ahead to check
            trading_config: Trading parameters
            probability_model_config: Probability model parameters
            
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
            # Give it a moment to fully stop
            time.sleep(2)
        
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
        
        Args:
            config: Engine configuration dictionary
            
        Returns:
            Environment variables dictionary
        """
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

