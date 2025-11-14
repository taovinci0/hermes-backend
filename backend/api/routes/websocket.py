"""WebSocket endpoints for real-time updates."""

import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional

from ..services.websocket_service import websocket_service

router = APIRouter()


@router.websocket("/trading")
async def websocket_trading(websocket: WebSocket, client_id: Optional[str] = None):
    """WebSocket endpoint for real-time trading updates.
    
    Broadcasts events:
    - cycle_complete: New cycle finished
    - trade_placed: New trade executed
    - edges_updated: Edges recalculated
    
    Args:
        websocket: WebSocket connection
        client_id: Optional client identifier
    """
    await websocket_service.connect(websocket, client_id)
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "timestamp": websocket_service.connection_metadata[websocket]["connected_at"],
            "message": "Connected to Hermes trading updates",
            "connection_count": websocket_service.get_connection_count(),
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages (client can send ping/pong or other commands)
                data = await websocket.receive_text()
                
                # Try to parse as JSON
                try:
                    message = json.loads(data)
                    message_type = message.get("type")
                    
                    if message_type == "ping":
                        # Respond to ping
                        await websocket.send_json({
                            "type": "pong",
                            "timestamp": websocket_service.connection_metadata[websocket]["connected_at"],
                        })
                    elif message_type == "subscribe":
                        # Handle subscription requests (future enhancement)
                        await websocket.send_json({
                            "type": "subscribed",
                            "channels": message.get("channels", []),
                        })
                except json.JSONDecodeError:
                    # Not JSON, ignore
                    pass
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                # Log error but keep connection alive
                print(f"WebSocket error: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        websocket_service.disconnect(websocket)


@router.get("/ws/status")
async def get_websocket_status():
    """Get WebSocket service status.
    
    Returns information about active connections.
    """
    return websocket_service.get_connections_info()

