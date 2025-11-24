"""Service for reading and parsing activity logs with advanced filtering."""

import re
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any, Set
from datetime import datetime, date, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from core.registry import StationRegistry

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
        self.registry = StationRegistry()
    
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
        
        # Also try to extract station code from city name (e.g., "London → 2025-11-19")
        # Pattern: "City → YYYY-MM-DD" or "City → event"
        city_pattern = r'([A-Z][a-z]+(?:\s+\([^)]+\))?)\s*→'
        city_match = re.search(city_pattern, entry["message"])
        if city_match and not entry["station_code"]:
            city_name = city_match.group(1).strip()
            # Try to find station by city name
            for station in self.registry.list_all():
                if station.city == city_name or city_name in station.city:
                    entry["station_code"] = station.station_code
                    break
        
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
        
        # Also try to extract event day from timestamp if not found in message
        if not entry["event_day"] and entry["timestamp"]:
            try:
                ts = datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))
                entry["event_day"] = ts.date().isoformat()
            except (ValueError, AttributeError):
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
                            
                            # Re-parse to extract station code and event day from full message
                            updated_entry = self._parse_log_line(full_message, log_file)
                            # Preserve timestamp and level from original entry
                            if current_entry.get("timestamp"):
                                updated_entry["timestamp"] = current_entry.get("timestamp")
                            if current_entry.get("level"):
                                updated_entry["level"] = current_entry.get("level")
                            current_entry = updated_entry
                        else:
                            # No continuation lines, just use current_entry as-is
                            pass
                        
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
    
    def _format_message_for_humans(self, entry: Dict[str, Any]) -> str:
        """Format a log message for human readability.
        
        Removes technical noise, file paths, and formats key information.
        
        Args:
            entry: Log entry dictionary
            
        Returns:
            Formatted, human-readable message
        """
        message = entry.get("message", "")
        if not message:
            return ""
        
        # Remove file paths (e.g., "fetchers.py:72", "discovery.py:301")
        message = re.sub(r'\s+[a-zA-Z_]+\.py:\d+\s*', ' ', message)
        
        # Remove duplicate log level prefixes (INFO, ERROR, etc.)
        message = re.sub(r'\b(INFO|DEBUG|WARNING|ERROR|CRITICAL)\s+', '', message)
        
        # Remove long file paths
        message = re.sub(r'/Users/[^\s]+', '...', message)
        message = re.sub(r'data/[^\s]+\.csv', 'trade file', message)
        message = re.sub(r'data/[^\s]+\.json', 'snapshot', message)
        
        # Clean up common patterns
        message = re.sub(r'\s+', ' ', message)  # Multiple spaces to single
        message = message.strip()
        
        # Extract and format key information
        formatted = self._extract_key_info(message, entry)
        
        return formatted if formatted else message
    
    def _extract_key_info(self, message: str, entry: Dict[str, Any]) -> Optional[str]:
        """Extract and format key information from log message.
        
        Args:
            message: Raw log message
            entry: Log entry dictionary
            
        Returns:
            Formatted message or None if no key info found
        """
        msg_lower = message.lower()
        action_type = entry.get("action_type", "")
        
        # Build a list of key events found in this message
        events = []
        
        # Cycle start
        if "cycle" in msg_lower and ("starting" in msg_lower or "CYCLE" in message):
            cycle_match = re.search(r'CYCLE\s+(\d+)', message)
            if cycle_match:
                events.append(f"🔄 Cycle {cycle_match.group(1)} started")
            else:
                events.append("🔄 Cycle started")
        
        # Zeus forecast fetch
        if "zeus" in msg_lower and ("fetched" in msg_lower or "points" in msg_lower or "parsed" in msg_lower):
            points_match = re.search(r'(\d+)\s+points?', message)
            station = entry.get("station_code", "")
            if points_match:
                events.append(f"🌡️  Zeus forecast: {points_match.group(1)} data points for {station}")
            else:
                events.append(f"🌡️  Fetched Zeus forecast for {station}")
        
        # Polymarket fetch
        if "polymarket" in msg_lower or ("brackets" in msg_lower and "temperature" in msg_lower):
            brackets_match = re.search(r'(\d+)\s+temperature\s+brackets?', message)
            if brackets_match:
                events.append(f"💰 Found {brackets_match.group(1)} temperature brackets")
            elif "prices" in msg_lower:
                prices_match = re.search(r'(\d+)/(\d+)\s+prices?', message)
                if prices_match:
                    events.append(f"💰 Fetched {prices_match.group(1)}/{prices_match.group(2)} market prices")
            else:
                events.append("💰 Fetched Polymarket data")
        
        # METAR fetch
        if "metar" in msg_lower:
            obs_match = re.search(r'(\d+)\s+valid\s+METAR', message)
            if obs_match:
                events.append(f"🌤️  Retrieved {obs_match.group(1)} METAR observation(s)")
            else:
                events.append("🌤️  Fetched METAR data")
        
        # Probability mapping
        if "mapped probabilities" in msg_lower or "mapping forecast" in msg_lower:
            model_match = re.search(r'(spread|bands)\s+model', msg_lower)
            model = model_match.group(1).title() if model_match else "Spread"
            peak_match = re.search(r'peak\s*=\s*\[(\d+),\s*(\d+)\)', message)
            prob_match = re.search(r'p\s*=\s*([\d.]+)', message)
            if peak_match and prob_match:
                events.append(f"🧮 Probabilities ({model}): Peak {peak_match.group(1)}-{peak_match.group(2)}°F at {float(prob_match.group(1))*100:.1f}%")
            else:
                events.append(f"🧮 Calculated probabilities ({model} model)")
        
        # Edge found - extract all edges
        edge_matches = list(re.finditer(r'\[(\d+)-(\d+)°F\)[^:]*edge[=:]\s*([\d.]+)', message))
        if edge_matches:
            for match in edge_matches:
                bracket = f"{match.group(1)}-{match.group(2)}°F"
                edge_pct = float(match.group(3)) * 100
                # Try to find size for this bracket
                size_match = re.search(rf'{re.escape(bracket)}[^$]*\$?([\d.]+)', message)
                size = f" (${size_match.group(1)})" if size_match else ""
                events.append(f"✅ Edge: {bracket} → {edge_pct:.2f}%{size}")
        
        # Trade placement - extract detailed trade information (HIGH PRIORITY)
        if "placing" in msg_lower or "placed" in msg_lower or "📄" in message:
            # Extract individual trade details: [bracket]: $size @ edge=edge%
            # Pattern handles whitespace/file paths between @ and edge=
            # After cleaning, format is: [58-59°F): $300.00 @ ... edge=26.16%
            trade_details = re.findall(r'\[(\d+-\d+°F)\):\s*\$([\d.]+)\s*@[^e]*edge=([\d.]+)%', message)
            
            if trade_details:
                # Found individual trade details - format them nicely
                trade_lines = []
                
                # Check for "Placing X paper trades" message
                placing_match = re.search(r'📄\s*Placing\s+(\d+)\s+paper\s+trades?', message)
                if placing_match:
                    trade_lines.append(f"📄 Placing {placing_match.group(1)} paper trades")
                
                # Add each individual trade
                for bracket, size, edge in trade_details:
                    trade_lines.append(f"📝 [{bracket}): ${size} @ edge={edge}%")
                
                # Check for "Recorded" message
                recorded_match = re.search(r'✅\s*Recorded\s+(\d+)\s+paper\s+trades?', message)
                if recorded_match:
                    trade_lines.append(f"✅ Recorded {recorded_match.group(1)} paper trades")
                
                # Return formatted multi-line message (don't add to events list)
                if trade_lines:
                    return "\n".join(trade_lines)
            else:
                # No individual details, just show count
                trade_match = re.search(r'(\d+)\s+paper\s+trades?', message)
                if trade_match:
                    events.append(f"📝 Placed {trade_match.group(1)} paper trade(s)")
                else:
                    events.append("📝 Placed paper trade(s)")
        
        # Trade recorded (if not already captured above)
        if "recorded" in msg_lower and "trade" in msg_lower and "✅" not in message:
            trade_match = re.search(r'(\d+)\s+paper\s+trades?', message)
            if trade_match:
                events.append(f"💾 Recorded {trade_match.group(1)} trade(s)")
            else:
                events.append("💾 Trade(s) recorded")
        
        # Error
        if "error" in msg_lower or entry.get("level") == "ERROR":
            if "404" in message:
                events.append("❌ API Error: Resource not found (404)")
            elif "401" in message:
                events.append("❌ API Error: Unauthorized (401)")
            elif "timeout" in msg_lower:
                events.append("❌ API Error: Request timeout")
            else:
                events.append("❌ Error occurred")
        
        # Event found
        if "found event" in msg_lower:
            events.append("🔍 Found Polymarket event")
        
        # Snapshot saved
        if "saved" in msg_lower and ("snapshot" in msg_lower or "zeus" in msg_lower):
            events.append("💾 Snapshot saved")
        
        # Return the most important event, or combine if multiple
        if events:
            # Prioritize: trade > edge > error > other
            priority_order = ["📝", "✅", "❌", "🔄", "💰", "🧮", "🌡️", "🌤️", "💾", "🔍"]
            events_sorted = sorted(events, key=lambda e: min([priority_order.index(emoji) for emoji in priority_order if emoji in e] + [999]))
            
            # If multiple events, show the most important one
            if len(events) > 1:
                return events_sorted[0] + f" (+{len(events)-1} more)"
            return events[0]
        
        # Default: return cleaned message
        return None
    
    def get_activity_logs(
        self,
        station_code: Optional[str] = None,
        event_day: Optional[str] = None,
        action_type: Optional[str] = None,
        log_level: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
        human_readable: bool = True,
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
            human_readable: If True, format messages for human readability
            
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
        
        # Format messages for human readability if requested
        if human_readable:
            for entry in paginated_entries:
                formatted_msg = self._format_message_for_humans(entry)
                if formatted_msg:
                    entry["message"] = formatted_msg
                    entry["message_formatted"] = True
                else:
                    entry["message_formatted"] = False
        
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
