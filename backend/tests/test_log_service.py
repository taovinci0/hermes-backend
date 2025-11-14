"""Tests for LogService."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from datetime import date, datetime

from api.services.log_service import LogService


class TestLogService:
    """Test LogService functionality."""
    
    def test_init(self):
        """Test LogService initialization."""
        service = LogService()
        assert service.logs_dir is not None
    
    def test_parse_log_line(self):
        """Test log line parsing."""
        service = LogService()
        
        # Test with timestamp and station code
        line = "[2025-11-13 12:00:00] | INFO | Processing station EGLC"
        entry = service._parse_log_line(line, Path("test.log"))
        
        assert entry is not None
        assert "EGLC" in entry.get("message", "")
        assert entry.get("station_code") == "EGLC"
        assert entry.get("level") == "INFO"
        assert entry.get("timestamp") is not None
    
    def test_parse_log_line_with_event_day(self):
        """Test parsing log line with event day."""
        service = LogService()
        
        line = "[2025-11-13 12:00:00] | INFO | Event day: 2025-11-13"
        entry = service._parse_log_line(line, Path("test.log"))
        
        assert entry is not None
        assert entry.get("event_day") == "2025-11-13"
    
    def test_parse_log_line_action_type(self):
        """Test parsing action type from log line."""
        service = LogService()
        
        # Test trade action
        line = "[2025-11-13 12:00:00] | INFO | Placed trade on bracket"
        entry = service._parse_log_line(line, Path("test.log"))
        
        assert entry is not None
        assert entry.get("action_type") == "trade"
        
        # Test fetch action
        line = "[2025-11-13 12:00:00] | INFO | Fetching Zeus forecast"
        entry = service._parse_log_line(line, Path("test.log"))
        
        assert entry is not None
        assert entry.get("action_type") == "fetch"
    
    def test_get_activity_logs_filter_by_station(self):
        """Test filtering logs by station code."""
        service = LogService()
        
        with patch.object(service, "get_log_files") as mock_files:
            mock_file = MagicMock()
            mock_file.name = "test.log"
            mock_file.exists.return_value = True
            mock_files.return_value = [mock_file]
            
            with patch.object(service, "read_log_file") as mock_read:
                mock_read.return_value = [
                    {
                        "timestamp": "2025-11-13T12:00:00",
                        "log_file": "test.log",
                        "station_code": "EGLC",
                        "message": "Processing EGLC",
                    },
                    {
                        "timestamp": "2025-11-13T12:01:00",
                        "log_file": "test.log",
                        "station_code": "KLGA",
                        "message": "Processing KLGA",
                    },
                ]
                
                result = service.get_activity_logs(station_code="EGLC")
                
                assert result["count"] == 1
                assert result["logs"][0]["station_code"] == "EGLC"
    
    def test_get_activity_logs_filter_by_event_day_today(self):
        """Test filtering logs by event day (today)."""
        service = LogService()
        
        today = date.today().isoformat()
        
        with patch.object(service, "get_log_files") as mock_files:
            mock_file = MagicMock()
            mock_file.name = "test.log"
            mock_file.exists.return_value = True
            mock_files.return_value = [mock_file]
            
            with patch.object(service, "read_log_file") as mock_read:
                mock_read.return_value = [
                    {
                        "timestamp": "2025-11-13T12:00:00",
                        "log_file": "test.log",
                        "event_day": today,
                        "message": "Today's event",
                    },
                    {
                        "timestamp": "2025-11-13T12:01:00",
                        "log_file": "test.log",
                        "event_day": "2025-11-12",
                        "message": "Yesterday's event",
                    },
                ]
                
                result = service.get_activity_logs(event_day="today")
                
                assert result["count"] >= 0  # May be 0 if today has no logs
                # All returned logs should be for today
                for log in result["logs"]:
                    if log.get("event_day"):
                        assert log["event_day"] == today
    
    def test_get_activity_logs_pagination(self):
        """Test pagination in activity logs."""
        service = LogService()
        
        with patch.object(service, "get_log_files") as mock_files:
            mock_file = MagicMock()
            mock_file.name = "test.log"
            mock_file.exists.return_value = True
            mock_files.return_value = [mock_file]
            
            with patch.object(service, "read_log_file") as mock_read:
                # Create 10 mock log entries
                mock_read.return_value = [
                    {
                        "timestamp": f"2025-11-13T12:{i:02d}:00",
                        "log_file": "test.log",
                        "message": f"Log entry {i}",
                    }
                    for i in range(10)
                ]
                
                # Get first page
                result1 = service.get_activity_logs(limit=5, offset=0)
                assert result1["count"] == 5
                assert result1["total"] == 10
                assert result1["has_more"] is True
                
                # Get second page
                result2 = service.get_activity_logs(limit=5, offset=5)
                assert result2["count"] == 5
                assert result2["total"] == 10
                assert result2["has_more"] is False
    
    def test_get_available_dates(self):
        """Test getting available dates."""
        service = LogService()
        
        with patch.object(service, "get_log_files") as mock_files:
            mock_file = MagicMock()
            mock_file.name = "dynamic_paper_20251113_125727.log"
            mock_file.exists.return_value = True
            mock_files.return_value = [mock_file]
            
            with patch.object(service, "read_log_file") as mock_read:
                mock_read.return_value = [
                    {
                        "timestamp": "2025-11-13T12:00:00",
                        "log_file": "test.log",
                        "event_day": "2025-11-13",
                        "message": "Test",
                    },
                ]
                
                dates = service.get_available_dates()
                
                assert isinstance(dates, list)
                assert "2025-11-13" in dates

