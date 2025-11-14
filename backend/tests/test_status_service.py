"""Tests for StatusService."""

import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, mock_open, MagicMock

from api.services.status_service import StatusService
from api.utils.path_utils import PROJECT_ROOT


class TestStatusService:
    """Test StatusService functionality."""
    
    def test_init(self):
        """Test StatusService initialization."""
        service = StatusService()
        assert service.logs_dir == PROJECT_ROOT / "logs"
        assert service.pid_file == service.logs_dir / "dynamic_paper.pid"
    
    def test_check_trading_engine_running_no_pid_file(self):
        """Test check when PID file doesn't exist."""
        service = StatusService()
        
        with patch.object(Path, "exists", return_value=False):
            assert service.check_trading_engine_running() is False
    
    def test_check_trading_engine_running_pid_file_exists(self):
        """Test check when PID file exists."""
        service = StatusService()
        
        with patch.object(Path, "exists", return_value=True):
            with patch.object(Path, "read_text", return_value="12345"):
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value.returncode = 0
                    assert service.check_trading_engine_running() is True
                    
                    mock_run.return_value.returncode = 1
                    assert service.check_trading_engine_running() is False
    
    def test_get_trading_engine_status_not_running(self):
        """Test status when engine is not running."""
        service = StatusService()
        
        with patch.object(service, "check_trading_engine_running", return_value=False):
            with patch.object(Path, "exists", return_value=False):
                status = service.get_trading_engine_status()
                
                assert status["running"] is False
                assert status["pid_file_exists"] is False
    
    def test_get_trading_engine_status_running(self):
        """Test status when engine is running."""
        service = StatusService()
        
        with patch.object(service, "check_trading_engine_running", return_value=True):
            with patch.object(Path, "exists", return_value=True):
                with patch.object(Path, "read_text", return_value="12345"):
                    with patch("subprocess.run") as mock_run:
                        mock_run.return_value.returncode = 0
                        mock_run.return_value.stdout = "ELAPSED COMMAND\n01:23:45 python -m core.orchestrator"
                        
                        status = service.get_trading_engine_status()
                        
                        assert status["running"] is True
                        assert status["pid_file_exists"] is True
                        assert status["pid"] == 12345
    
    def test_get_system_status(self):
        """Test overall system status."""
        service = StatusService()
        
        with patch.object(service, "get_trading_engine_status") as mock_trading:
            mock_trading.return_value = {
                "running": True,
                "pid_file_exists": True,
                "pid": 12345,
            }
            
            with patch.object(Path, "exists", return_value=True):
                with patch.object(Path, "rglob") as mock_rglob:
                    # Mock snapshot files
                    mock_file1 = MagicMock()
                    mock_file1.stat.return_value.st_mtime = 1000000000  # Old file
                    mock_file2 = MagicMock()
                    mock_file2.stat.return_value.st_mtime = datetime.now().timestamp() - 3600  # Recent file
                    mock_rglob.return_value = [mock_file1, mock_file2]
                    
                    status = service.get_system_status()
                    
                    assert "timestamp" in status
                    assert "trading_engine" in status
                    assert "data_collection" in status
                    assert status["trading_engine"]["running"] is True

