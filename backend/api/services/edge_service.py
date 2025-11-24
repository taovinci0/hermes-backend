"""Service for retrieving current edges from decision snapshots."""

from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import date, datetime

from ..utils.path_utils import get_snapshots_dir
from ..utils.file_utils import read_json_file, list_json_files, parse_timestamp


class EdgeService:
    """Service for retrieving current edges from decision snapshots."""
    
    def __init__(self):
        """Initialize edge service."""
        self.snapshots_dir = get_snapshots_dir()
    
    def get_current_edges(
        self,
        station_code: Optional[str] = None,
        event_day: Optional[date] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get current edges from latest decision snapshots.
        
        Args:
            station_code: Optional station code filter
            event_day: Optional event day filter
            limit: Optional limit on number of edges
            
        Returns:
            List of edge dictionaries with bracket, edge, size, etc.
        """
        decision_dir = self.snapshots_dir / "decisions"
        
        if not decision_dir.exists():
            return []
        
        # Collect all decision snapshots
        all_decisions = []
        
        # If station_code specified, only check that station
        stations_to_check = [station_code] if station_code else None
        
        if stations_to_check:
            for station in stations_to_check:
                station_dir = decision_dir / station
                if not station_dir.exists():
                    continue
                
                # If event_day specified, only check that day
                if event_day:
                    day_dir = station_dir / event_day.isoformat()
                    if day_dir.exists():
                        files = list_json_files(day_dir)
                        for file_path in files:
                            data = read_json_file(file_path)
                            if data:
                                all_decisions.append((file_path, data))
                else:
                    # Check all days for this station
                    for day_dir in station_dir.iterdir():
                        if not day_dir.is_dir():
                            continue
                        files = list_json_files(day_dir)
                        for file_path in files:
                            data = read_json_file(file_path)
                            if data:
                                all_decisions.append((file_path, data))
        else:
            # Check all stations
            for station_dir in decision_dir.iterdir():
                if not station_dir.is_dir():
                    continue
                
                for day_dir in station_dir.iterdir():
                    if not day_dir.is_dir():
                        continue
                    
                    # Filter by event_day if specified
                    if event_day:
                        try:
                            day_date = date.fromisoformat(day_dir.name)
                            if day_date != event_day:
                                continue
                        except ValueError:
                            continue
                    
                    files = list_json_files(day_dir)
                    for file_path in files:
                        data = read_json_file(file_path)
                        if data:
                            all_decisions.append((file_path, data))
        
        # Sort by decision_time_utc (most recent first)
        all_decisions.sort(
            key=lambda x: parse_timestamp(x[1].get("decision_time_utc", "")) or datetime.min,
            reverse=True
        )
        
        # Extract edges from decisions
        edges = []
        seen_keys = set()  # Track (station, event_day, bracket) to avoid duplicates
        
        for file_path, snapshot_data in all_decisions:
            decisions = snapshot_data.get("decisions", [])
            station_code_snap = snapshot_data.get("station_code", "")
            event_day_snap = snapshot_data.get("event_day", "")
            
            # Apply filters
            if station_code and station_code_snap != station_code:
                continue
            
            if event_day and event_day_snap != event_day.isoformat():
                continue
            
            for decision in decisions:
                bracket = decision.get("bracket", "")
                key = (station_code_snap, event_day_snap, bracket)
                
                # Only include most recent edge for each bracket
                if key not in seen_keys:
                    seen_keys.add(key)
                    
                    edge_data = {
                        "station_code": station_code_snap,
                        "city": snapshot_data.get("city", ""),
                        "event_day": event_day_snap,
                        "decision_time_utc": snapshot_data.get("decision_time_utc", ""),
                        "bracket": bracket,
                        "lower_f": decision.get("lower_f"),
                        "upper_f": decision.get("upper_f"),
                        "market_id": decision.get("market_id", ""),
                        "edge": decision.get("edge", 0.0),
                        "edge_pct": decision.get("edge_pct", 0.0),
                        "f_kelly": decision.get("f_kelly", 0.0),
                        "size_usd": decision.get("size_usd", 0.0),
                        "reason": decision.get("reason", ""),
                        "p_zeus": decision.get("p_zeus"),
                        "p_mkt": decision.get("p_mkt"),
                    }
                    edges.append(edge_data)
        
        # Sort by edge_pct descending (best edges first)
        edges.sort(key=lambda e: e.get("edge_pct", 0.0), reverse=True)
        
        if limit:
            edges = edges[:limit]
        
        return edges
    
    def get_edges_summary(
        self,
        station_code: Optional[str] = None,
        event_day: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Get summary statistics for current edges.
        
        Args:
            station_code: Optional station code filter
            event_day: Optional event day filter
            
        Returns:
            Dictionary with summary statistics
        """
        edges = self.get_current_edges(
            station_code=station_code,
            event_day=event_day,
        )
        
        if not edges:
            return {
                "total_edges": 0,
                "avg_edge_pct": 0.0,
                "max_edge_pct": 0.0,
                "total_size_usd": 0.0,
                "brackets": [],
            }
        
        edge_pcts = [e.get("edge_pct", 0.0) for e in edges]
        sizes = [e.get("size_usd", 0.0) for e in edges]
        
        return {
            "total_edges": len(edges),
            "avg_edge_pct": round(sum(edge_pcts) / len(edge_pcts), 2) if edge_pcts else 0.0,
            "max_edge_pct": round(max(edge_pcts), 2) if edge_pcts else 0.0,
            "min_edge_pct": round(min(edge_pcts), 2) if edge_pcts else 0.0,
            "total_size_usd": round(sum(sizes), 2),
            "brackets": [e.get("bracket") for e in edges],
        }

