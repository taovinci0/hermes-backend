"""Tests for API routes."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from api.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health and status endpoints."""
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data
    
    def test_health_endpoint(self):
        """Test health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data
    
    def test_status_endpoint(self):
        """Test status endpoint."""
        with patch("api.routes.status.status_service.get_system_status") as mock_status:
            mock_status.return_value = {
                "timestamp": "2025-11-14T10:00:00",
                "trading_engine": {"running": False},
                "data_collection": {"recent_snapshots_24h": 0},
            }
            
            response = client.get("/api/status")
            assert response.status_code == 200
            data = response.json()
            assert "trading_engine" in data
            assert "data_collection" in data


class TestSnapshotEndpoints:
    """Test snapshot endpoints."""
    
    def test_zeus_snapshots_endpoint(self):
        """Test Zeus snapshots endpoint."""
        with patch("api.routes.snapshots.snapshot_service.get_zeus_snapshots") as mock_get:
            mock_get.return_value = [
                {
                    "fetch_time_utc": "2025-11-13T12:00:00",
                    "station_code": "EGLC",
                    "timeseries_count": 24,
                }
            ]
            
            response = client.get("/api/snapshots/zeus?station_code=EGLC&event_day=2025-11-13")
            assert response.status_code == 200
            data = response.json()
            assert "snapshots" in data
            assert "count" in data
            assert data["count"] == 1
    
    def test_polymarket_snapshots_endpoint(self):
        """Test Polymarket snapshots endpoint."""
        with patch("api.routes.snapshots.snapshot_service.get_polymarket_snapshots") as mock_get:
            mock_get.return_value = [
                {
                    "fetch_time_utc": "2025-11-13T12:00:00",
                    "city": "London",
                    "markets": [],
                }
            ]
            
            response = client.get("/api/snapshots/polymarket?city=London&event_day=2025-11-13")
            assert response.status_code == 200
            data = response.json()
            assert "snapshots" in data
            assert data["count"] == 1
    
    def test_decision_snapshots_endpoint(self):
        """Test decision snapshots endpoint."""
        with patch("api.routes.snapshots.snapshot_service.get_decision_snapshots") as mock_get:
            mock_get.return_value = [
                {
                    "decision_time_utc": "2025-11-13T12:00:00",
                    "station_code": "EGLC",
                    "trade_count": 2,
                }
            ]
            
            response = client.get("/api/snapshots/decisions?station_code=EGLC&event_day=2025-11-13")
            assert response.status_code == 200
            data = response.json()
            assert "snapshots" in data
            assert data["count"] == 1


class TestTradeEndpoints:
    """Test trade endpoints."""
    
    def test_recent_trades_endpoint(self):
        """Test recent trades endpoint."""
        with patch("api.routes.trades.trade_service.get_trades") as mock_get:
            from api.models.schemas import Trade
            
            mock_trades = [
                Trade(
                    timestamp="2025-11-13T12:00:00",
                    station_code="EGLC",
                    bracket_name="58-59°F",
                    bracket_lower_f=58,
                    bracket_upper_f=59,
                    market_id="123",
                    edge=0.1,
                    edge_pct=10.0,
                    f_kelly=0.2,
                    size_usd=200.0,
                    reason="test",
                )
            ]
            mock_get.return_value = mock_trades
            
            response = client.get("/api/trades/recent?limit=10")
            assert response.status_code == 200
            data = response.json()
            assert "trades" in data
            assert "count" in data
            assert data["count"] == 1
    
    def test_trade_summary_endpoint(self):
        """Test trade summary endpoint."""
        with patch("api.routes.trades.trade_service.get_trade_summary") as mock_get:
            mock_get.return_value = {
                "total_trades": 10,
                "total_size_usd": 2000.0,
                "avg_edge_pct": 15.5,
            }
            
            response = client.get("/api/trades/summary?trade_date=2025-11-13")
            assert response.status_code == 200
            data = response.json()
            assert "total_trades" in data
            assert data["total_trades"] == 10


class TestEdgeEndpoints:
    """Test edge endpoints."""
    
    def test_current_edges_endpoint(self):
        """Test current edges endpoint."""
        with patch("api.routes.edges.edge_service.get_current_edges") as mock_get:
            mock_get.return_value = [
                {
                    "station_code": "EGLC",
                    "bracket": "58-59°F",
                    "edge_pct": 26.16,
                    "size_usd": 300.0,
                }
            ]
            
            response = client.get("/api/edges/current?station_code=EGLC&limit=10")
            assert response.status_code == 200
            data = response.json()
            assert "edges" in data
            assert "count" in data
            assert data["count"] == 1
    
    def test_edges_summary_endpoint(self):
        """Test edges summary endpoint."""
        with patch("api.routes.edges.edge_service.get_edges_summary") as mock_get:
            mock_get.return_value = {
                "total_edges": 5,
                "avg_edge_pct": 20.5,
                "max_edge_pct": 30.0,
                "total_size_usd": 1500.0,
            }
            
            response = client.get("/api/edges/summary?station_code=EGLC")
            assert response.status_code == 200
            data = response.json()
            assert "total_edges" in data
            assert data["total_edges"] == 5

