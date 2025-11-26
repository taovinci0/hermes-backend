"""File watcher for detecting new snapshots and triggering WebSocket events."""

import json
import asyncio
from pathlib import Path
from typing import Optional, Callable, Dict
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent

from ..utils.path_utils import PROJECT_ROOT
from ..services.websocket_service import websocket_service


class SnapshotFileHandler(FileSystemEventHandler):
    """Handler for snapshot file events."""
    
    def __init__(self, on_new_file: Optional[Callable] = None):
        """Initialize file handler.
        
        Args:
            on_new_file: Callback function when new file is detected
        """
        self.on_new_file = on_new_file
        self.last_processed: Dict[str, float] = {}  # Track processed files by path
    
    def on_created(self, event):
        """Handle file creation event."""
        if not event.is_directory and event.src_path.endswith('.json'):
            self._process_file(event.src_path)
    
    def on_modified(self, event):
        """Handle file modification event."""
        if not event.is_directory and event.src_path.endswith('.json'):
            self._process_file(event.src_path)
    
    def _process_file(self, file_path: str):
        """Process a new or modified file.
        
        Args:
            file_path: Path to the file
        """
        # Avoid processing the same file multiple times
        import time
        current_time = time.time()
        if file_path in self.last_processed:
            # Only process if file was modified more than 1 second ago
            if current_time - self.last_processed[file_path] < 1.0:
                return
        
        self.last_processed[file_path] = current_time
        
        if self.on_new_file:
            try:
                self.on_new_file(file_path)
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")


class SnapshotWatcher:
    """Watcher for snapshot directories."""
    
    def __init__(self):
        """Initialize snapshot watcher."""
        self.observer = Observer()
        self.base_dir = PROJECT_ROOT / "data" / "snapshots" / "dynamic"
        self.running = False
    
    def _detect_event_type(self, file_path: Path) -> Optional[str]:
        """Detect event type from file path.
        
        Args:
            file_path: Path to the snapshot file
            
        Returns:
            Event type string or None
        """
        path_str = str(file_path)
        
        # Check if it's a decision snapshot (indicates cycle complete or trade)
        if "/decisions/" in path_str:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    decisions = data.get("decisions", [])
                    trade_count = data.get("trade_count", 0)
                    
                    if trade_count > 0:
                        # Trade placed event
                        return "trade_placed"
                    else:
                        # Cycle complete but no trades
                        return "cycle_complete"
            except Exception:
                pass
        
        # Check if it's a Zeus snapshot (indicates cycle complete)
        elif "/zeus/" in path_str:
            return "cycle_complete"
        
        # Check if it's a Polymarket snapshot (indicates edges updated)
        elif "/polymarket/" in path_str:
            return "edges_updated"
        
        return None
    
    def _extract_metadata(self, file_path: Path, event_type: str) -> Optional[Dict]:
        """Extract metadata from snapshot file.
        
        Args:
            file_path: Path to the snapshot file
            event_type: Type of event
            
        Returns:
            Metadata dictionary or None
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            metadata = {
                "file_path": str(file_path.relative_to(self.base_dir)),
            }
            
            if event_type == "trade_placed":
                # Extract trade information
                decisions = data.get("decisions", [])
                if decisions:
                    trade = decisions[0]  # First trade
                    metadata.update({
                        "station_code": data.get("station_code"),
                        "event_day": data.get("event_day"),
                        "bracket": trade.get("bracket"),
                        "size_usd": trade.get("size_usd"),
                        "edge_pct": trade.get("edge_pct"),
                    })
            
            elif event_type == "cycle_complete":
                metadata.update({
                    "station_code": data.get("station_code"),
                    "event_day": data.get("event_day"),
                    "trade_count": data.get("trade_count", 0),
                })
            
            elif event_type == "edges_updated":
                metadata.update({
                    "city": data.get("city"),
                    "event_day": data.get("event_day"),
                })
            
            return metadata
        except Exception:
            return None
    
    def _on_new_file(self, file_path: str):
        """Handle new file detection.
        
        Args:
            file_path: Path to the new file
        """
        path = Path(file_path)
        if not path.exists():
            return
        
        event_type = self._detect_event_type(path)
        if not event_type:
            return
        
        metadata = self._extract_metadata(path, event_type)
        if not metadata:
            return
        
        # Broadcast event via WebSocket
        asyncio.create_task(self._broadcast_event(event_type, metadata))
    
    async def _broadcast_event(self, event_type: str, metadata: Dict):
        """Broadcast event to WebSocket clients.
        
        Args:
            event_type: Type of event
            metadata: Event metadata
        """
        if event_type == "trade_placed":
            await websocket_service.broadcast_trade_placed(
                station_code=metadata.get("station_code", ""),
                event_day=metadata.get("event_day", ""),
                bracket=metadata.get("bracket", ""),
                size_usd=metadata.get("size_usd", 0.0),
                edge_pct=metadata.get("edge_pct", 0.0),
            )
        elif event_type == "cycle_complete":
            await websocket_service.broadcast_cycle_complete(
                cycle_number=0,  # Would need to track this
                station_code=metadata.get("station_code", ""),
                event_day=metadata.get("event_day", ""),
                trades_count=metadata.get("trade_count", 0),
                cycle_duration=0.0,  # Would need to track this
            )
        elif event_type == "edges_updated":
            await websocket_service.broadcast_edges_updated(
                station_code="",  # Not available in Polymarket snapshots
                event_day=metadata.get("event_day", ""),
                edges_count=0,  # Would need to calculate
                max_edge_pct=0.0,  # Would need to calculate
            )
    
    def start(self):
        """Start watching snapshot directories."""
        if self.running:
            return
        
        if not self.base_dir.exists():
            self.base_dir.mkdir(parents=True, exist_ok=True)
        
        handler = SnapshotFileHandler(on_new_file=self._on_new_file)
        
        # Watch the dynamic snapshots directory recursively
        self.observer.schedule(handler, str(self.base_dir), recursive=True)
        self.observer.start()
        self.running = True
    
    def stop(self):
        """Stop watching snapshot directories."""
        if self.running:
            self.observer.stop()
            self.observer.join()
            self.running = False


# Global watcher instance
snapshot_watcher = SnapshotWatcher()

