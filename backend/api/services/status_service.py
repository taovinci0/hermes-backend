"""Service for checking system status and trading engine state."""

import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

# Add project root to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from core.config import config
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
    
    def _get_last_cycle_time(self) -> Optional[datetime]:
        """Get the timestamp of the last completed cycle.
        
        Looks for the most recent decision snapshot to determine last cycle time.
        
        Returns:
            Datetime of last cycle, or None if not found
        """
        decisions_dir = PROJECT_ROOT / "data" / "snapshots" / "dynamic" / "decisions"
        if not decisions_dir.exists():
            return None
        
        latest_time = None
        
        # Find the most recent decision snapshot
        for station_dir in decisions_dir.iterdir():
            if not station_dir.is_dir():
                continue
            for event_day_dir in station_dir.iterdir():
                if not event_day_dir.is_dir():
                    continue
                for snapshot_file in event_day_dir.glob("*.json"):
                    try:
                        # Extract timestamp from filename (e.g., 2025-11-17_20-15-30.json)
                        timestamp_str = snapshot_file.stem
                        # Parse: 2025-11-17_20-15-30
                        cycle_time = datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")
                        if latest_time is None or cycle_time > latest_time:
                            latest_time = cycle_time
                    except (ValueError, IndexError):
                        continue
        
        return latest_time
    
    def _calculate_next_cycle_time(self, last_cycle: Optional[datetime], interval_seconds: int) -> Optional[datetime]:
        """Calculate when the next cycle should run.
        
        Args:
            last_cycle: Timestamp of last cycle
            interval_seconds: Cycle interval in seconds
            
        Returns:
            Datetime of next cycle, or None if can't calculate
        """
        if last_cycle is None:
            return None
        
        return last_cycle + timedelta(seconds=interval_seconds)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status.
        
        Returns:
            Dictionary with system status information including:
            - Trading engine status (running, PID, etc.)
            - Execution mode (paper/live)
            - Cycle interval and next cycle time
            - Data collection status
        """
        trading_status = self.get_trading_engine_status()
        
        # Get execution mode from config
        execution_mode = config.execution_mode.upper()  # PAPER or LIVE
        
        # Get cycle interval from config
        interval_seconds = config.dynamic_interval_seconds
        interval_minutes = interval_seconds / 60
        
        # Get last cycle time and calculate next cycle
        last_cycle = self._get_last_cycle_time()
        next_cycle = self._calculate_next_cycle_time(last_cycle, interval_seconds)
        
        # Calculate seconds until next cycle
        seconds_until_next = None
        if next_cycle:
            now = datetime.now()
            delta = next_cycle - now
            seconds_until_next = max(0, int(delta.total_seconds()))
        
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
        
        status = {
            "timestamp": datetime.utcnow().isoformat(),
            "trading_engine": trading_status,
            "execution_mode": execution_mode,
            "cycle": {
                "interval_seconds": interval_seconds,
                "interval_minutes": round(interval_minutes, 1),
                "last_cycle_time": last_cycle.isoformat() if last_cycle else None,
                "next_cycle_time": next_cycle.isoformat() if next_cycle else None,
                "seconds_until_next": seconds_until_next,
            },
            "data_collection": {
                "recent_snapshots_24h": snapshot_count,
                "snapshots_dir_exists": snapshots_dir.exists(),
                "trades_dir_exists": trades_dir.exists(),
            },
        }
        
        return status

