"""Service for reading and parsing activity logs with advanced filtering."""

import re
from pathlib import Path
from typing import List, Optional, Dict, Any, Set
from datetime import datetime, date, timedelta

from ..utils.path_utils import get_logs_dir
from ..utils.file_utils import parse_timestamp


class LogService:
    """Service for reading and parsing activity logs with advanced filtering."""
    
    # Log level patterns
    LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    
    # Action type patterns (keywords that indicate action types)
    ACTION_PATTERNS = {
        "fetch": ["fetch", "fetched", "fetching"],
        "trade": ["trade", "trading", "placed", "executed"],
        "decision": ["decision", "edge", "kelly", "sizing"],
        "snapshot": ["snapshot", "saved", "saving"],
        "cycle": ["cycle", "CYCLE"],
        "error": ["error", "failed", "exception"],
    }
    
    def __init__(self):
        """Initialize log service."""
        self.logs_dir = get_logs_dir()
    
    def get_log_files(self) -> List[Path]:
        """Get all log files in the logs directory.
        
        Returns:
            List of log file paths, sorted by modification time (newest first)
        """
        if not self.logs_dir.exists():
            return []
        
        log_files = list(self.logs_dir.glob("*.log"))
        # Sort by modification time, newest first
        log_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return log_files
    
    def _parse_log_line(self, line: str, log_file: Path) -> Optional[Dict[str, Any]]:
        """Parse a single log line into structured data.
        
        Handles Rich console output format:
        - [YYYY-MM-DD HH:MM:SS] LEVEL     message     file.py:line
        - Continuation lines (no timestamp) are handled separately
        
        Args:
            line: Raw log line
            log_file: Path to log file
            
        Returns:
            Parsed log entry dictionary or None if parsing fails
        """
        if not line.strip():
            return None
        
        entry = {
            "timestamp": None,
            "log_file": log_file.name,
            "level": None,
            "message": line.strip(),
            "station_code": None,
            "event_day": None,
            "action_type": None,
        }
        
        # Try to extract timestamp
        # Format: [YYYY-MM-DD HH:MM:SS] INFO     message
        timestamp_match = re.search(r'\[(\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2})\]', line)
        if timestamp_match:
            ts_str = timestamp_match.group(1).replace(" ", "T")
            timestamp = parse_timestamp(ts_str)
            if timestamp:
                entry["timestamp"] = timestamp.isoformat()
            
            # Extract log level (comes right after timestamp bracket)
            # Format: ] INFO     message
            level_match = re.search(r'\]\s+([A-Z]+)\s+', line)
            if level_match:
                level = level_match.group(1).upper()
                if level in self.LOG_LEVELS:
                    entry["level"] = level
            
            # Extract message (everything after level, before file:line)
            # Remove file:line suffix if present
            message_match = re.search(r'\]\s+[A-Z]+\s+(.+?)(?:\s+[a-zA-Z_]+\.py:\d+)?$', line)
            if message_match:
                entry["message"] = message_match.group(1).strip()
        else:
            # No timestamp - this is a continuation line
            # Just use the stripped line as message
            entry["message"] = line.strip()
        
        # Try to extract station code (common patterns: EGLC, KLGA, etc.)
        station_match = re.search(r'\b([A-Z]{4})\b', entry["message"])
        if station_match:
            code = station_match.group(1)
            # Common station codes are 4 letters
            if len(code) == 4 and code.isalpha():
                entry["station_code"] = code
        
        # Try to extract event day (YYYY-MM-DD format)
        date_match = re.search(r'\b(\d{4}-\d{2}-\d{2})\b', entry["message"])
        if date_match:
            date_str = date_match.group(1)
            try:
                # Validate it's a real date
                date.fromisoformat(date_str)
                entry["event_day"] = date_str
            except ValueError:
                pass
        
        # Try to determine action type
        line_lower = entry["message"].lower()
        for action_type, patterns in self.ACTION_PATTERNS.items():
            if any(pattern in line_lower for pattern in patterns):
                entry["action_type"] = action_type
                break
        
        return entry
    
    def read_log_file(
        self,
        log_file: Path,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Read and parse log entries from a file.
        
        Handles multi-line log entries by grouping continuation lines
        with their timestamped parent line.
        
        Args:
            log_file: Path to log file
            limit: Optional limit on number of entries
            
        Returns:
            List of parsed log entry dictionaries
        """
        if not log_file.exists():
            return []
        
        try:
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            
            entries = []
            current_entry = None
            continuation_lines = []
            
            for line in lines:
                # Check if this line has a timestamp (new log entry)
                has_timestamp = bool(re.search(r'\[(\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2})\]', line))
                
                if has_timestamp:
                    # Save previous entry if it exists
                    if current_entry:
                        # Append continuation lines to message
                        if continuation_lines:
                            full_message = current_entry["message"]
                            for cont_line in continuation_lines:
                                cont_msg = cont_line.strip()
                                if cont_msg:
                                    full_message += " " + cont_msg
                            current_entry["message"] = full_message
                        entries.append(current_entry)
                    
                    # Start new entry
                    current_entry = self._parse_log_line(line, log_file)
                    continuation_lines = []
                else:
                    # Continuation line - add to current entry's message
                    if current_entry:
                        continuation_lines.append(line)
                    else:
                        # Orphaned continuation line - create minimal entry
                        entry = self._parse_log_line(line, log_file)
                        if entry:
                            entries.append(entry)
            
            # Don't forget the last entry
            if current_entry:
                if continuation_lines:
                    full_message = current_entry["message"]
                    for cont_line in continuation_lines:
                        cont_msg = cont_line.strip()
                        if cont_msg:
                            full_message += " " + cont_msg
                    current_entry["message"] = full_message
                entries.append(current_entry)
            
            # Filter out entries with no meaningful content
            entries = [
                e for e in entries
                if e.get("message") and len(e["message"].strip()) > 0
            ]
            
            # Sort by timestamp descending (newest first)
            entries.sort(
                key=lambda e: e["timestamp"] or "",
                reverse=True
            )
            
            if limit:
                entries = entries[:limit]
            
            return entries
        except IOError:
            return []
    
    def get_activity_logs(
        self,
        station_code: Optional[str] = None,
        event_day: Optional[str] = None,
        action_type: Optional[str] = None,
        log_level: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Get filtered activity logs with pagination.
        
        Args:
            station_code: Filter by station code
            event_day: Filter by event day (YYYY-MM-DD) or special values:
                      "today", "tomorrow", "past_3_days", "future"
            action_type: Filter by action type (fetch, trade, decision, etc.)
            log_level: Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            limit: Maximum number of entries to return
            offset: Number of entries to skip (for pagination)
            
        Returns:
            Dictionary with logs, count, total, and pagination info
        """
        log_files = self.get_log_files()
        
        all_entries = []
        
        # Read all log files
        for log_file in log_files:
            entries = self.read_log_file(log_file, limit=None)
            all_entries.extend(entries)
        
        # Apply filters
        filtered_entries = all_entries
        
        # Filter by station code
        if station_code:
            filtered_entries = [
                e for e in filtered_entries
                if e.get("station_code") == station_code.upper()
            ]
        
        # Filter by event day
        if event_day:
            today = date.today()
            
            if event_day == "today":
                target_date = today.isoformat()
                filtered_entries = [
                    e for e in filtered_entries
                    if e.get("event_day") == target_date
                ]
            elif event_day == "tomorrow":
                target_date = (today + timedelta(days=1)).isoformat()
                filtered_entries = [
                    e for e in filtered_entries
                    if e.get("event_day") == target_date
                ]
            elif event_day == "past_3_days":
                cutoff_date = (today - timedelta(days=3))
                filtered_entries = [
                    e for e in filtered_entries
                    if e.get("event_day") and date.fromisoformat(e["event_day"]) >= cutoff_date
                ]
            elif event_day == "future":
                filtered_entries = [
                    e for e in filtered_entries
                    if e.get("event_day") and date.fromisoformat(e["event_day"]) > today
                ]
            else:
                # Specific date (YYYY-MM-DD)
                try:
                    date.fromisoformat(event_day)  # Validate
                    filtered_entries = [
                        e for e in filtered_entries
                        if e.get("event_day") == event_day
                    ]
                except ValueError:
                    pass  # Invalid date format, ignore filter
        
        # Filter by action type
        if action_type:
            filtered_entries = [
                e for e in filtered_entries
                if e.get("action_type") == action_type.lower()
            ]
        
        # Filter by log level
        if log_level:
            filtered_entries = [
                e for e in filtered_entries
                if e.get("level") == log_level.upper()
            ]
        
        # Sort by timestamp descending (newest first)
        filtered_entries.sort(
            key=lambda e: e["timestamp"] or "",
            reverse=True
        )
        
        total = len(filtered_entries)
        
        # Apply pagination
        paginated_entries = filtered_entries[offset:]
        if limit:
            paginated_entries = paginated_entries[:limit]
        
        return {
            "logs": paginated_entries,
            "count": len(paginated_entries),
            "total": total,
            "offset": offset,
            "limit": limit,
            "has_more": (offset + len(paginated_entries)) < total,
        }
    
    def get_available_dates(self) -> List[str]:
        """Get list of dates that have log entries.
        
        Returns:
            List of date strings (YYYY-MM-DD), sorted descending (newest first)
        """
        log_files = self.get_log_files()
        
        dates: Set[str] = set()
        
        for log_file in log_files:
            entries = self.read_log_file(log_file, limit=None)
            for entry in entries:
                event_day = entry.get("event_day")
                if event_day:
                    dates.add(event_day)
        
        # Also extract dates from log file names (e.g., dynamic_paper_20251113_125727.log)
        for log_file in log_files:
            # Try to extract date from filename
            date_match = re.search(r'(\d{8})', log_file.name)
            if date_match:
                date_str = date_match.group(1)
                try:
                    # Convert YYYYMMDD to YYYY-MM-DD
                    formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                    date.fromisoformat(formatted_date)  # Validate
                    dates.add(formatted_date)
                except (ValueError, IndexError):
                    pass
        
        # Sort descending (newest first)
        sorted_dates = sorted(dates, reverse=True)
        return sorted_dates
    
    # Legacy methods for backward compatibility
    def get_recent_logs(
        self,
        limit: int = 100,
        filter_text: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get recent log entries from all log files (legacy method).
        
        Args:
            limit: Maximum number of log entries to return
            filter_text: Optional text to filter by
            
        Returns:
            List of log entry dictionaries
        """
        result = self.get_activity_logs(limit=limit)
        logs = result["logs"]
        
        # Apply text filter if specified
        if filter_text:
            filter_lower = filter_text.lower()
            logs = [
                log for log in logs
                if filter_lower in log.get("message", "").lower()
            ]
        
        return logs
    
    def get_log_entries_by_station(
        self,
        station_code: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get log entries filtered by station code (legacy method).
        
        Args:
            station_code: Station code to filter by
            limit: Maximum number of entries
            
        Returns:
            List of log entry dictionaries
        """
        result = self.get_activity_logs(
            station_code=station_code,
            limit=limit,
        )
        return result["logs"]
    
    def get_log_entries_by_date(
        self,
        event_day: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get log entries filtered by event day (legacy method).
        
        Args:
            event_day: Event day string (YYYY-MM-DD)
            limit: Maximum number of entries
            
        Returns:
            List of log entry dictionaries
        """
        result = self.get_activity_logs(
            event_day=event_day,
            limit=limit,
        )
        return result["logs"]
