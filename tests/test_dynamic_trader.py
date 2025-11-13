"""Tests for dynamic trading engine.

Stage 7C tests - JIT fetching, continuous loop, timestamped snapshots.
"""

import json
from datetime import datetime, date, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from unittest.mock import Mock, patch, MagicMock

import pytest

from core.registry import Station
from core.types import MarketBracket, BracketProb, EdgeDecision, ForecastPoint
from agents.zeus_forecast import ZeusForecast
from agents.dynamic_trader.fetchers import DynamicFetcher
from agents.dynamic_trader.snapshotter import DynamicSnapshotter
from agents.dynamic_trader.dynamic_engine import DynamicTradingEngine


@pytest.fixture
def mock_station():
    """Mock weather station."""
    return Station(
        city="London",
        station_name="London City Airport",
        station_code="EGLC",
        lat=51.505,
        lon=0.05,
        noaa_station="UKMO",
        venue_hint="Polymarket London",
        time_zone="Europe/London",
    )


@pytest.fixture
def mock_zeus_forecast():
    """Mock Zeus forecast."""
    base_time = datetime(2025, 11, 13, 0, 0, tzinfo=ZoneInfo("UTC"))
    
    return ZeusForecast(
        timeseries=[
            ForecastPoint(
                time_utc=base_time + timedelta(hours=i),
                temp_K=290.0 + i * 0.5,
            )
            for i in range(24)
        ],
        station_code="EGLC",
        lat=51.505,
        lon=0.05,
    )


@pytest.fixture
def mock_brackets():
    """Mock market brackets."""
    return [
        MarketBracket(
            name="58-59°F",
            lower_F=58,
            upper_F=59,
            market_id="market_58_59",
            token_id="token_58_59",
            closed=False,
        ),
        MarketBracket(
            name="60-61°F",
            lower_F=60,
            upper_F=61,
            market_id="market_60_61",
            token_id="token_60_61",
            closed=False,
        ),
    ]


# DynamicFetcher Tests

def test_fetcher_initialization():
    """Test DynamicFetcher initializes correctly."""
    fetcher = DynamicFetcher()
    
    assert fetcher.zeus is not None
    assert fetcher.discovery is not None
    assert fetcher.pricing is not None


@patch("agents.dynamic_trader.fetchers.ZeusForecastAgent")
def test_fetcher_zeus_jit_uses_local_time(mock_zeus_class, mock_station):
    """Test that Zeus is fetched with LOCAL time, not UTC."""
    mock_zeus = Mock()
    mock_zeus_class.return_value = mock_zeus
    
    fetcher = DynamicFetcher()
    fetcher.zeus = mock_zeus
    
    event_day = date(2025, 11, 13)
    
    # Mock the fetch response
    mock_zeus.fetch.return_value = ZeusForecast(
        timeseries=[],
        station_code="EGLC",
        lat=51.505,
        lon=0.05,
    )
    
    # Call fetch
    result = fetcher.fetch_zeus_jit(mock_station, event_day)
    
    # Verify fetch was called
    assert mock_zeus.fetch.called
    
    # Verify it was called with local midnight (not UTC conversion)
    call_args = mock_zeus.fetch.call_args
    start_time = call_args.kwargs['start_utc']
    
    # Should be midnight in London time
    expected = datetime.combine(event_day, time(0, 0), tzinfo=ZoneInfo("Europe/London"))
    assert start_time == expected


@patch("agents.dynamic_trader.fetchers.PolyPricing")
@patch("agents.dynamic_trader.fetchers.PolyDiscovery")
def test_fetcher_polymarket_jit(mock_discovery_class, mock_pricing_class, mock_brackets):
    """Test Polymarket JIT fetching."""
    # Setup mocks
    mock_discovery = Mock()
    mock_discovery_class.return_value = mock_discovery
    mock_discovery.list_temp_brackets.return_value = mock_brackets
    
    mock_pricing = Mock()
    mock_pricing_class.return_value = mock_pricing
    mock_pricing.midprob.side_effect = [0.35, 0.42]  # Two prices
    
    fetcher = DynamicFetcher()
    fetcher.discovery = mock_discovery
    fetcher.pricing = mock_pricing
    
    # Fetch
    brackets, prices = fetcher.fetch_polymarket_jit("London", date(2025, 11, 13))
    
    # Verify
    assert len(brackets) == 2
    assert len(prices) == 2
    assert prices[0] == 0.35
    assert prices[1] == 0.42


def test_fetcher_check_open_events():
    """Test checking if events are open."""
    fetcher = DynamicFetcher()
    
    # This will call real API, so just verify it doesn't crash
    # (Returns False if no events found)
    result = fetcher.check_open_events("London", date(2025, 11, 13))
    
    assert isinstance(result, bool)


# DynamicSnapshotter Tests

def test_snapshotter_initialization(tmp_path):
    """Test DynamicSnapshotter initializes correctly."""
    with patch("agents.dynamic_trader.snapshotter.PROJECT_ROOT", tmp_path):
        snapshotter = DynamicSnapshotter()
        
        assert snapshotter.base_dir == tmp_path / "data" / "snapshots" / "dynamic"
        assert snapshotter.base_dir.exists()


def test_snapshotter_save_zeus(tmp_path, mock_zeus_forecast, mock_station):
    """Test Zeus snapshot saving."""
    with patch("agents.dynamic_trader.snapshotter.PROJECT_ROOT", tmp_path):
        snapshotter = DynamicSnapshotter()
        
        event_day = date(2025, 11, 13)
        timestamp = "2025-11-13_14-30-00"
        cycle_time = datetime(2025, 11, 13, 14, 30, tzinfo=ZoneInfo("UTC"))
        
        snapshotter._save_zeus(mock_zeus_forecast, mock_station, event_day, timestamp, cycle_time)
        
        # Verify file created
        snapshot_path = (
            tmp_path / "data" / "snapshots" / "dynamic" / "zeus" / 
            "EGLC" / "2025-11-13" / f"{timestamp}.json"
        )
        
        assert snapshot_path.exists()
        
        # Verify content
        with open(snapshot_path) as f:
            data = json.load(f)
        
        assert data["station_code"] == "EGLC"
        assert data["forecast_for_local_day"] == "2025-11-13"
        assert data["timeseries_count"] == 24


def test_snapshotter_save_polymarket(tmp_path, mock_brackets):
    """Test Polymarket snapshot saving."""
    with patch("agents.dynamic_trader.snapshotter.PROJECT_ROOT", tmp_path):
        snapshotter = DynamicSnapshotter()
        
        event_day = date(2025, 11, 13)
        timestamp = "2025-11-13_14-30-00"
        cycle_time = datetime(2025, 11, 13, 14, 30, tzinfo=ZoneInfo("UTC"))
        prices = [0.35, 0.42]
        
        snapshotter._save_polymarket(mock_brackets, prices, "London", event_day, timestamp, cycle_time)
        
        # Verify file created
        snapshot_path = (
            tmp_path / "data" / "snapshots" / "dynamic" / "polymarket" / 
            "London" / "2025-11-13" / f"{timestamp}.json"
        )
        
        assert snapshot_path.exists()
        
        # Verify content
        with open(snapshot_path) as f:
            data = json.load(f)
        
        assert data["city"] == "London"
        assert len(data["markets"]) == 2
        assert data["markets"][0]["mid_price"] == 0.35


def test_snapshotter_save_decisions(tmp_path, mock_station, mock_brackets):
    """Test decisions snapshot saving."""
    with patch("agents.dynamic_trader.snapshotter.PROJECT_ROOT", tmp_path):
        snapshotter = DynamicSnapshotter()
        
        event_day = date(2025, 11, 13)
        timestamp = "2025-11-13_14-30-00"
        cycle_time = datetime(2025, 11, 13, 14, 30, tzinfo=ZoneInfo("UTC"))
        
        decisions = [
            EdgeDecision(
                bracket=mock_brackets[0],
                edge=0.15,
                f_kelly=0.12,
                size_usd=250.0,
                reason="edge > min",
            )
        ]
        
        snapshotter._save_decisions(decisions, mock_station, event_day, timestamp, cycle_time)
        
        # Verify file created
        snapshot_path = (
            tmp_path / "data" / "snapshots" / "dynamic" / "decisions" / 
            "EGLC" / "2025-11-13" / f"{timestamp}.json"
        )
        
        assert snapshot_path.exists()
        
        # Verify content
        with open(snapshot_path) as f:
            data = json.load(f)
        
        assert data["station_code"] == "EGLC"
        assert len(data["decisions"]) == 1
        assert data["decisions"][0]["edge"] == 0.15


# DynamicTradingEngine Tests

def test_engine_initialization():
    """Test DynamicTradingEngine initializes correctly."""
    engine = DynamicTradingEngine(
        stations=["EGLC"],
        interval_seconds=60,
        lookahead_days=2,
    )
    
    assert engine.stations == ["EGLC"]
    assert engine.interval_seconds == 60
    assert engine.lookahead_days == 2
    assert engine.fetcher is not None
    assert engine.prob_mapper is not None
    assert engine.sizer is not None


@patch("agents.dynamic_trader.dynamic_engine.DynamicFetcher")
@patch("agents.dynamic_trader.dynamic_engine.PaperBroker")
def test_engine_evaluate_and_trade_no_markets(mock_broker_class, mock_fetcher_class, mock_station):
    """Test evaluation when no open markets exist."""
    # Setup mocks
    mock_fetcher = Mock()
    mock_fetcher_class.return_value = mock_fetcher
    mock_fetcher.check_open_events.return_value = False
    
    mock_broker = Mock()
    mock_broker_class.return_value = mock_broker
    
    engine = DynamicTradingEngine(stations=["EGLC"])
    engine.fetcher = mock_fetcher
    engine.broker = mock_broker
    engine.registry.get = Mock(return_value=mock_station)
    
    # Evaluate
    event_day = date(2025, 11, 13)
    cycle_time = datetime.now(ZoneInfo("UTC"))
    
    trades = engine._evaluate_and_trade(mock_station, event_day, cycle_time)
    
    # Should return 0 (no markets open)
    assert trades == 0
    assert not mock_broker.place.called


@patch("agents.dynamic_trader.dynamic_engine.sleep")
def test_engine_run_stops_on_interrupt(mock_sleep):
    """Test engine stops gracefully on KeyboardInterrupt."""
    engine = DynamicTradingEngine(stations=["EGLC"], interval_seconds=60)
    
    # Simulate KeyboardInterrupt on first sleep
    mock_sleep.side_effect = KeyboardInterrupt()
    
    # Should not raise, should handle gracefully
    engine.run()
    
    # Should have attempted to sleep
    assert mock_sleep.called


def test_engine_lookahead_days():
    """Test engine checks multiple days based on lookahead."""
    engine = DynamicTradingEngine(stations=["EGLC"], lookahead_days=3)
    
    assert engine.lookahead_days == 3
    # Will check today, tomorrow, day after tomorrow

