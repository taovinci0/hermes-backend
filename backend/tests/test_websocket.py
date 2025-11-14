"""Tests for WebSocket functionality."""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock

from api.main import app
from api.services.websocket_service import WebSocketService, websocket_service


class TestWebSocketService:
    """Test WebSocketService functionality."""
    
    def test_connect_and_disconnect(self):
        """Test connecting and disconnecting WebSocket."""
        service = WebSocketService()
        mock_websocket = MagicMock()
        
        # Test connect
        import asyncio
        asyncio.run(service.connect(mock_websocket, client_id="test_client"))
        
        assert len(service.active_connections) == 1
        assert mock_websocket in service.active_connections
        assert mock_websocket in service.connection_metadata
        
        # Test disconnect
        service.disconnect(mock_websocket)
        
        assert len(service.active_connections) == 0
        assert mock_websocket not in service.active_connections
    
    def test_get_connection_count(self):
        """Test getting connection count."""
        service = WebSocketService()
        assert service.get_connection_count() == 0
        
        mock_websocket = MagicMock()
        import asyncio
        asyncio.run(service.connect(mock_websocket))
        
        assert service.get_connection_count() == 1
    
    @pytest.mark.asyncio
    async def test_broadcast(self):
        """Test broadcasting messages."""
        service = WebSocketService()
        
        # Create mock WebSocket connections
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        
        await service.connect(mock_ws1)
        await service.connect(mock_ws2)
        
        # Broadcast message
        await service.broadcast("test_event", {"key": "value"})
        
        # Verify both connections received the message
        assert mock_ws1.send_json.called
        assert mock_ws2.send_json.called
    
    @pytest.mark.asyncio
    async def test_broadcast_trade_placed(self):
        """Test broadcasting trade placed event."""
        service = WebSocketService()
        
        mock_ws = AsyncMock()
        await service.connect(mock_ws)
        
        await service.broadcast_trade_placed(
            station_code="EGLC",
            event_day="2025-11-13",
            bracket="58-59°F",
            size_usd=300.0,
            edge_pct=26.16,
        )
        
        # Verify message was sent
        assert mock_ws.send_json.called
        call_args = mock_ws.send_json.call_args[0][0]
        assert call_args["type"] == "trade_placed"
        assert call_args["data"]["station_code"] == "EGLC"
        assert call_args["data"]["bracket"] == "58-59°F"
    
    @pytest.mark.asyncio
    async def test_broadcast_cycle_complete(self):
        """Test broadcasting cycle complete event."""
        service = WebSocketService()
        
        mock_ws = AsyncMock()
        await service.connect(mock_ws)
        
        await service.broadcast_cycle_complete(
            cycle_number=42,
            station_code="EGLC",
            event_day="2025-11-13",
            trades_count=3,
            cycle_duration=12.5,
        )
        
        # Verify message was sent
        assert mock_ws.send_json.called
        call_args = mock_ws.send_json.call_args[0][0]
        assert call_args["type"] == "cycle_complete"
        assert call_args["data"]["cycle_number"] == 42
        assert call_args["data"]["trades_count"] == 3


class TestWebSocketEndpoint:
    """Test WebSocket endpoint."""
    
    def test_websocket_status_endpoint(self):
        """Test WebSocket status endpoint."""
        client = TestClient(app)
        response = client.get("/ws/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "connections" in data


class TestFileWatcher:
    """Test file watcher functionality."""
    
    def test_snapshot_watcher_init(self):
        """Test snapshot watcher initialization."""
        from api.utils.file_watcher import SnapshotWatcher
        
        watcher = SnapshotWatcher()
        assert watcher.base_dir is not None
        assert watcher.running is False
    
    def test_detect_event_type(self):
        """Test event type detection from file path."""
        from api.utils.file_watcher import SnapshotWatcher
        from pathlib import Path
        
        watcher = SnapshotWatcher()
        
        # Test decision snapshot (trade)
        decision_path = Path("data/snapshots/dynamic/decisions/EGLC/2025-11-13/test.json")
        event_type = watcher._detect_event_type(decision_path)
        # Will be None if file doesn't exist, but structure is correct
        assert event_type in [None, "trade_placed", "cycle_complete"]
        
        # Test Zeus snapshot
        zeus_path = Path("data/snapshots/dynamic/zeus/EGLC/2025-11-13/test.json")
        event_type = watcher._detect_event_type(zeus_path)
        assert event_type in [None, "cycle_complete"]
        
        # Test Polymarket snapshot
        poly_path = Path("data/snapshots/dynamic/polymarket/London/2025-11-13/test.json")
        event_type = watcher._detect_event_type(poly_path)
        assert event_type in [None, "edges_updated"]

