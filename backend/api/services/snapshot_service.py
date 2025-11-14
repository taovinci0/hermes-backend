"""Service for reading snapshot files."""

from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import date, datetime

from ..utils.path_utils import get_snapshots_dir
from ..utils.file_utils import read_json_file, list_json_files, parse_timestamp
from ..models.schemas import ZeusSnapshot, PolymarketSnapshot, DecisionSnapshot


class SnapshotService:
    """Service for reading Zeus, Polymarket, and Decision snapshots."""
    
    def __init__(self):
        """Initialize snapshot service."""
        self.snapshots_dir = get_snapshots_dir()
    
    def get_zeus_snapshots(
        self,
        station_code: str,
        event_day: Optional[date] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get Zeus forecast snapshots for a station.
        
        Args:
            station_code: Station code (e.g., "EGLC")
            event_day: Optional date filter (YYYY-MM-DD)
            limit: Optional limit on number of snapshots
            
        Returns:
            List of snapshot dictionaries
        """
        zeus_dir = self.snapshots_dir / "zeus" / station_code
        
        if event_day:
            zeus_dir = zeus_dir / event_day.isoformat()
        
        if not zeus_dir.exists():
            return []
        
        files = list_json_files(zeus_dir)
        
        # Sort by filename (which includes timestamp) descending
        files.sort(reverse=True)
        
        if limit:
            files = files[:limit]
        
        snapshots = []
        for file_path in files:
            data = read_json_file(file_path)
            if data:
                # Add filename for reference
                data["_filename"] = file_path.name
                snapshots.append(data)
        
        return snapshots
    
    def get_polymarket_snapshots(
        self,
        city: str,
        event_day: Optional[date] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get Polymarket pricing snapshots for a city.
        
        Args:
            city: City name (e.g., "London")
            event_day: Optional date filter (YYYY-MM-DD)
            limit: Optional limit on number of snapshots
            
        Returns:
            List of snapshot dictionaries
        """
        # City name might have spaces, replace with underscore
        city_clean = city.replace(" ", "_")
        poly_dir = self.snapshots_dir / "polymarket" / city_clean
        
        if event_day:
            poly_dir = poly_dir / event_day.isoformat()
        
        if not poly_dir.exists():
            return []
        
        files = list_json_files(poly_dir)
        files.sort(reverse=True)
        
        if limit:
            files = files[:limit]
        
        snapshots = []
        for file_path in files:
            data = read_json_file(file_path)
            if data:
                data["_filename"] = file_path.name
                snapshots.append(data)
        
        return snapshots
    
    def get_decision_snapshots(
        self,
        station_code: str,
        event_day: Optional[date] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get decision snapshots for a station.
        
        Args:
            station_code: Station code (e.g., "EGLC")
            event_day: Optional date filter (YYYY-MM-DD)
            limit: Optional limit on number of snapshots
            
        Returns:
            List of snapshot dictionaries
        """
        decision_dir = self.snapshots_dir / "decisions" / station_code
        
        if event_day:
            decision_dir = decision_dir / event_day.isoformat()
        
        if not decision_dir.exists():
            return []
        
        files = list_json_files(decision_dir)
        files.sort(reverse=True)
        
        if limit:
            files = files[:limit]
        
        snapshots = []
        for file_path in files:
            data = read_json_file(file_path)
            if data:
                data["_filename"] = file_path.name
                snapshots.append(data)
        
        return snapshots
    
    def get_metar_snapshots(
        self,
        station_code: str,
        event_day: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """Get METAR observation snapshots for a station.
        
        Args:
            station_code: Station code (e.g., "EGLC")
            event_day: Optional date filter (YYYY-MM-DD)
            
        Returns:
            List of snapshot dictionaries
        """
        # METAR snapshots are stored in dynamic/metar/{station_code}/{event_day}/
        # Check both locations: dynamic/metar and metar (for backward compatibility)
        metar_dirs = [
            self.snapshots_dir / "dynamic" / "metar" / station_code,
            self.snapshots_dir / "metar" / station_code,
        ]
        
        if event_day:
            metar_dirs = [
                d / event_day.isoformat() if d.exists() else None
                for d in metar_dirs
            ]
            metar_dirs = [d for d in metar_dirs if d is not None]
        
        all_files = []
        for metar_dir in metar_dirs:
            if metar_dir.exists():
                files = list_json_files(metar_dir)
                all_files.extend(files)
        
        # Remove duplicates (by filename)
        seen = set()
        unique_files = []
        for file_path in all_files:
            if file_path.name not in seen:
                seen.add(file_path.name)
                unique_files.append(file_path)
        
        unique_files.sort()  # Sort ascending (by observation time)
        
        snapshots = []
        for file_path in unique_files:
            data = read_json_file(file_path)
            if data:
                data["_filename"] = file_path.name
                snapshots.append(data)
        
        return snapshots

