"""WebSocket service for managing connections and broadcasting events."""

import json
import asyncio
from typing import Set, Dict, Any, Optional
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect


class WebSocketService:
    """Service for managing WebSocket connections and broadcasting events."""
    
    def __init__(self):
        """Initialize WebSocket service."""
        # Active connections: Set of WebSocket instances
        self.active_connections: Set[WebSocket] = set()
        # Connection metadata: WebSocket -> metadata dict
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: Optional[str] = None):
        """Accept a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            client_id: Optional client identifier
        """
        await websocket.accept()
        self.active_connections.add(websocket)
        self.connection_metadata[websocket] = {
            "client_id": client_id,
            "connected_at": datetime.utcnow().isoformat(),
        }
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection.
        
        Args:
            websocket: WebSocket connection to remove
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send a message to a specific WebSocket connection.
        
        Args:
            message: Message dictionary to send
            websocket: Target WebSocket connection
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            # Connection may be closed, remove it
            self.disconnect(websocket)
    
    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        """Broadcast an event to all connected clients.
        
        Args:
            event_type: Type of event (cycle_complete, trade_placed, edges_updated)
            data: Event data dictionary
        """
        if not self.active_connections:
            return
        
        message = {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
        }
        
        # Send to all connections, removing dead ones
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_cycle_complete(
        self,
        cycle_number: int,
        station_code: str,
        event_day: str,
        trades_count: int,
        cycle_duration: float,
    ):
        """Broadcast a cycle completion event.
        
        Args:
            cycle_number: Cycle number
            station_code: Station code
            event_day: Event day (YYYY-MM-DD)
            trades_count: Number of trades placed
            cycle_duration: Cycle duration in seconds
        """
        await self.broadcast(
            "cycle_complete",
            {
                "cycle_number": cycle_number,
                "station_code": station_code,
                "event_day": event_day,
                "trades_count": trades_count,
                "cycle_duration": cycle_duration,
            }
        )
    
    async def broadcast_trade_placed(
        self,
        station_code: str,
        event_day: str,
        bracket: str,
        size_usd: float,
        edge_pct: float,
    ):
        """Broadcast a trade placement event.
        
        Args:
            station_code: Station code
            event_day: Event day (YYYY-MM-DD)
            bracket: Temperature bracket
            size_usd: Trade size in USD
            edge_pct: Edge percentage
        """
        await self.broadcast(
            "trade_placed",
            {
                "station_code": station_code,
                "event_day": event_day,
                "bracket": bracket,
                "size_usd": size_usd,
                "edge_pct": edge_pct,
            }
        )
    
    async def broadcast_edges_updated(
        self,
        station_code: str,
        event_day: str,
        edges_count: int,
        max_edge_pct: float,
    ):
        """Broadcast an edges update event.
        
        Args:
            station_code: Station code
            event_day: Event day (YYYY-MM-DD)
            edges_count: Number of edges calculated
            max_edge_pct: Maximum edge percentage
        """
        await self.broadcast(
            "edges_updated",
            {
                "station_code": station_code,
                "event_day": event_day,
                "edges_count": edges_count,
                "max_edge_pct": max_edge_pct,
            }
        )
    
    def get_connection_count(self) -> int:
        """Get the number of active connections.
        
        Returns:
            Number of active WebSocket connections
        """
        return len(self.active_connections)
    
    def get_connections_info(self) -> Dict[str, Any]:
        """Get information about active connections.
        
        Returns:
            Dictionary with connection count and metadata
        """
        return {
            "count": len(self.active_connections),
            "connections": [
                {
                    "client_id": meta.get("client_id"),
                    "connected_at": meta.get("connected_at"),
                }
                for meta in self.connection_metadata.values()
            ],
        }


# Global WebSocket service instance
websocket_service = WebSocketService()

