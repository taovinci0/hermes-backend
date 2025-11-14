"""Service for checking system status and trading engine state."""

import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from ..utils.path_utils import PROJECT_ROOT


class StatusService:
    """Service for checking system status and trading engine state."""
    
    def __init__(self):
        """Initialize status service."""
        self.logs_dir = PROJECT_ROOT / "logs"
        self.pid_file = self.logs_dir / "dynamic_paper.pid"
    
    def check_trading_engine_running(self) -> bool:
        """Check if dynamic trading engine is running.
        
        Returns:
            True if trading engine process is running, False otherwise
        """
        if not self.pid_file.exists():
            return False
        
        try:
            pid = int(self.pid_file.read_text().strip())
            # Check if process exists
            result = subprocess.run(
                ["ps", "-p", str(pid)],
                capture_output=True,
                timeout=2,
            )
            return result.returncode == 0
        except (ValueError, subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def get_trading_engine_status(self) -> Dict[str, Any]:
        """Get detailed trading engine status.
        
        Returns:
            Dictionary with status information
        """
        is_running = self.check_trading_engine_running()
        
        status = {
            "running": is_running,
            "pid_file_exists": self.pid_file.exists(),
        }
        
        if is_running and self.pid_file.exists():
            try:
                pid = int(self.pid_file.read_text().strip())
                status["pid"] = pid
                
                # Try to get process info
                try:
                    result = subprocess.run(
                        ["ps", "-p", str(pid), "-o", "etime,command"],
                        capture_output=True,
                        text=True,
                        timeout=2,
                    )
                    if result.returncode == 0:
                        lines = result.stdout.strip().split("\n")
                        if len(lines) > 1:
                            # Parse elapsed time and command
                            parts = lines[1].split(None, 1)
                            if len(parts) >= 2:
                                status["elapsed_time"] = parts[0]
                                status["command"] = parts[1][:100]  # Truncate long commands
                except (subprocess.TimeoutExpired, IndexError):
                    pass
            except ValueError:
                pass
        
        return status
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status.
        
        Returns:
            Dictionary with system status information
        """
        trading_status = self.get_trading_engine_status()
        
        # Check data directories
        data_dir = PROJECT_ROOT / "data"
        snapshots_dir = data_dir / "snapshots" / "dynamic"
        trades_dir = data_dir / "trades"
        
        # Count recent snapshots (last 24 hours)
        snapshot_count = 0
        if snapshots_dir.exists():
            for snapshot_file in snapshots_dir.rglob("*.json"):
                # Check if file was modified in last 24 hours
                try:
                    mtime = snapshot_file.stat().st_mtime
                    age_seconds = datetime.now().timestamp() - mtime
                    if age_seconds < 86400:  # 24 hours
                        snapshot_count += 1
                except (OSError, ValueError):
                    pass
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "trading_engine": trading_status,
            "data_collection": {
                "recent_snapshots_24h": snapshot_count,
                "snapshots_dir_exists": snapshots_dir.exists(),
                "trades_dir_exists": trades_dir.exists(),
            },
        }

