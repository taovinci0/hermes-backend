"""File utilities for reading snapshots and data files."""

import json
import csv
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime, date


def read_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Read a JSON file and return its contents.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Dictionary with file contents, or None if file doesn't exist or is invalid
    """
    if not file_path.exists():
        return None
    
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        return None


def read_csv_file(file_path: Path) -> List[Dict[str, Any]]:
    """Read a CSV file and return list of dictionaries.
    
    Args:
        file_path: Path to CSV file
        
    Returns:
        List of dictionaries, one per row
    """
    if not file_path.exists():
        return []
    
    try:
        with open(file_path, "r") as f:
            reader = csv.DictReader(f)
            return list(reader)
    except (csv.Error, IOError):
        return []


def list_json_files(directory: Path, pattern: str = "*.json") -> List[Path]:
    """List all JSON files in a directory.
    
    Args:
        directory: Directory to search
        pattern: File pattern (default: "*.json")
        
    Returns:
        List of Path objects, sorted by filename
    """
    if not directory.exists():
        return []
    
    files = list(directory.glob(pattern))
    return sorted(files)


def parse_timestamp(timestamp_str: str) -> Optional[datetime]:
    """Parse ISO format timestamp string.
    
    Args:
        timestamp_str: ISO format timestamp string
        
    Returns:
        datetime object or None if parsing fails
    """
    try:
        # Try ISO format with timezone
        if "T" in timestamp_str:
            return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        # Try date only
        return datetime.fromisoformat(timestamp_str)
    except (ValueError, AttributeError):
        return None

