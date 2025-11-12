"""Tests for Backtester (Stage 7).

Tests backtest harness functionality.
"""

import csv
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

from agents.backtester import Backtester, BacktestTrade, BacktestSummary
from core.types import MarketBracket, BracketProb, ZeusForecast, ForecastPoint


@pytest.fixture
def backtester():
    """Create a Backtester instance."""
    return Backtester(
        bankroll_usd=10000.0,
        edge_min=0.05,
        fee_bp=50,
        slippage_bp=30,
    )


@pytest.fixture
def mock_zeus_forecast():
    """Create a mock Zeus forecast."""
    now = datetime.now()
    timeseries = [
        ForecastPoint(time_utc=now + timedelta(hours=i), temp_K=290.0 + i)
        for i in range(24)
    ]
    return ZeusForecast(
        lat=51.505,
        lon=0.05,
        timeseries=timeseries,
        station_code="EGLC",
    )


@pytest.fixture
def mock_brackets():
    """Create mock market brackets."""
    return [
        MarketBracket(
            market_id="market1",
            name="55-60°F",
            lower=55,
            upper=60,
            lower_F=55,
            upper_F=60,
        ),
        MarketBracket(
            market_id="market2",
            name="60-65°F",
            lower=60,
            upper=65,
            lower_F=60,
            upper_F=65,
        ),
    ]


def test_backtester_init():
    """Test Backtester initialization."""
    backtester = Backtester(
        bankroll_usd=5000.0,
        edge_min=0.10,
        fee_bp=100,
        slippage_bp=50,
    )
    
    assert backtester.bankroll_usd == 5000.0
    assert backtester.edge_min == 0.10
    assert backtester.fee_bp == 100
    assert backtester.slippage_bp == 50
    assert backtester.registry is not None
    assert backtester.zeus is not None
    assert backtester.prob_mapper is not None
    assert backtester.sizer is not None
    assert backtester.discovery is not None
    assert backtester.pricing is not None


def test_backtester_runs_dir_created(backtester):
    """Test that backtest runs directory is created."""
    assert backtester.runs_dir.exists()
    assert backtester.runs_dir.is_dir()
    assert str(backtester.runs_dir).endswith("data/runs/backtests")


@patch("agents.backtester.PolyPricing")
@patch("agents.backtester.PolyDiscovery")
@patch("agents.backtester.ZeusForecastAgent")
def test_backtest_single_day_no_forecast(
    mock_zeus_cls,
    mock_discovery_cls,
    mock_pricing_cls,
    backtester,
):
    """Test backtest when Zeus forecast fails."""
    # Mock Zeus to raise error
    mock_zeus = MagicMock()
    mock_zeus.fetch.side_effect = Exception("API error")
    backtester.zeus = mock_zeus
    
    trades = backtester._backtest_single_day(date(2025, 11, 5), "EGLC")
    
    assert trades == []


@patch("agents.backtester.PolyPricing")
@patch("agents.backtester.PolyDiscovery")
@patch("agents.backtester.ZeusForecastAgent")
def test_backtest_single_day_no_brackets(
    mock_zeus_cls,
    mock_discovery_cls,
    mock_pricing_cls,
    backtester,
    mock_zeus_forecast,
):
    """Test backtest when no brackets are discovered."""
    # Mock Zeus to return forecast
    mock_zeus = MagicMock()
    mock_zeus.fetch.return_value = mock_zeus_forecast
    backtester.zeus = mock_zeus
    
    # Mock discovery to return no brackets
    mock_discovery = MagicMock()
    mock_discovery.list_temp_brackets.return_value = []
    backtester.discovery = mock_discovery
    
    trades = backtester._backtest_single_day(date(2025, 11, 5), "EGLC")
    
    assert trades == []


@patch("agents.backtester.PolyPricing")
@patch("agents.backtester.PolyDiscovery")
@patch("agents.backtester.ProbabilityMapper")
@patch("agents.backtester.Sizer")
@patch("agents.backtester.ZeusForecastAgent")
def test_backtest_single_day_with_trades(
    mock_zeus_cls,
    mock_sizer_cls,
    mock_mapper_cls,
    mock_discovery_cls,
    mock_pricing_cls,
    backtester,
    mock_zeus_forecast,
    mock_brackets,
):
    """Test successful backtest with trades."""
    # Mock Zeus
    mock_zeus = MagicMock()
    mock_zeus.fetch.return_value = mock_zeus_forecast
    backtester.zeus = mock_zeus
    
    # Mock discovery
    mock_discovery = MagicMock()
    mock_discovery.list_temp_brackets.return_value = mock_brackets
    backtester.discovery = mock_discovery
    
    # Mock pricing
    mock_pricing = MagicMock()
    mock_pricing.midprob.side_effect = [0.45, 0.35, 0.40, 0.38]  # open + close prices
    backtester.pricing = mock_pricing
    
    # Mock probability mapper
    mock_mapper = MagicMock()
    mock_mapper.map_daily_high.return_value = [
        BracketProb(bracket=mock_brackets[0], p_zeus=0.60),
        BracketProb(bracket=mock_brackets[1], p_zeus=0.30),
    ]
    backtester.prob_mapper = mock_mapper
    
    # Mock sizer
    from core.types import EdgeDecision
    mock_sizer = MagicMock()
    mock_sizer.decide.return_value = [
        EdgeDecision(
            bracket=mock_brackets[0],
            p_zeus=0.60,
            p_mkt=0.45,
            edge=0.15,
            f_kelly=0.10,
            size_usd=500.0,
        )
    ]
    backtester.sizer = mock_sizer
    
    trades = backtester._backtest_single_day(date(2025, 11, 5), "EGLC")
    
    assert len(trades) == 1
    assert trades[0].station_code == "EGLC"
    assert trades[0].date == date(2025, 11, 5)
    assert trades[0].edge == 0.15
    assert trades[0].size_usd == 500.0
    assert trades[0].outcome == "pending"


def test_save_results(backtester, tmp_path):
    """Test saving backtest results to CSV."""
    # Override runs_dir to use tmp_path
    backtester.runs_dir = tmp_path
    
    trades = [
        BacktestTrade(
            date=date(2025, 11, 5),
            station_code="EGLC",
            city="London",
            bracket_name="55-60°F",
            lower=55,
            upper=60,
            zeus_prob=0.60,
            market_prob_open=0.45,
            edge=0.15,
            size_usd=500.0,
            outcome="win",
            realized_pnl=75.0,
            market_prob_close=0.50,
        ),
        BacktestTrade(
            date=date(2025, 11, 6),
            station_code="KLGA",
            city="New York",
            bracket_name="40-45°F",
            lower=40,
            upper=45,
            zeus_prob=0.50,
            market_prob_open=0.40,
            edge=0.10,
            size_usd=300.0,
            outcome="loss",
            realized_pnl=-30.0,
            market_prob_close=0.38,
        ),
    ]
    
    start_date = date(2025, 11, 5)
    end_date = date(2025, 11, 6)
    
    output_path = backtester._save_results(start_date, end_date, trades)
    
    assert output_path.exists()
    assert output_path.name == "2025-11-05_to_2025-11-06.csv"
    
    # Read CSV and verify contents
    with open(output_path, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 2
    assert rows[0]["station_code"] == "EGLC"
    assert rows[0]["city"] == "London"
    assert rows[0]["outcome"] == "win"
    assert float(rows[0]["realized_pnl"]) == 75.0
    assert rows[1]["station_code"] == "KLGA"
    assert rows[1]["outcome"] == "loss"


def test_calculate_summary_no_trades(backtester):
    """Test summary calculation with no trades."""
    start_date = date(2025, 11, 5)
    end_date = date(2025, 11, 6)
    
    summary = backtester._calculate_summary(start_date, end_date, [])
    
    assert summary.total_trades == 0
    assert summary.wins == 0
    assert summary.losses == 0
    assert summary.pending == 0
    assert summary.hit_rate == 0.0
    assert summary.total_risk == 0.0
    assert summary.total_pnl == 0.0
    assert summary.roi == 0.0


def test_calculate_summary_with_trades(backtester):
    """Test summary calculation with trades."""
    trades = [
        BacktestTrade(
            date=date(2025, 11, 5),
            station_code="EGLC",
            city="London",
            bracket_name="55-60°F",
            lower=55,
            upper=60,
            zeus_prob=0.60,
            market_prob_open=0.45,
            edge=0.15,
            size_usd=500.0,
            outcome="win",
            realized_pnl=75.0,
        ),
        BacktestTrade(
            date=date(2025, 11, 6),
            station_code="EGLC",
            city="London",
            bracket_name="60-65°F",
            lower=60,
            upper=65,
            zeus_prob=0.50,
            market_prob_open=0.40,
            edge=0.10,
            size_usd=300.0,
            outcome="loss",
            realized_pnl=-30.0,
        ),
        BacktestTrade(
            date=date(2025, 11, 7),
            station_code="EGLC",
            city="London",
            bracket_name="55-60°F",
            lower=55,
            upper=60,
            zeus_prob=0.55,
            market_prob_open=0.43,
            edge=0.12,
            size_usd=400.0,
            outcome="win",
            realized_pnl=48.0,
        ),
    ]
    
    start_date = date(2025, 11, 5)
    end_date = date(2025, 11, 7)
    
    summary = backtester._calculate_summary(start_date, end_date, trades)
    
    assert summary.total_trades == 3
    assert summary.wins == 2
    assert summary.losses == 1
    assert summary.pending == 0
    assert summary.hit_rate == pytest.approx(66.67, rel=0.01)
    assert summary.total_risk == 1200.0
    assert summary.total_pnl == 93.0
    assert summary.roi == pytest.approx(7.75, rel=0.01)
    assert summary.avg_edge == pytest.approx(12.33, rel=0.01)  # (15+10+12)/3 = 12.33%
    assert summary.avg_winning_pnl == pytest.approx(61.5, rel=0.01)
    assert summary.avg_losing_pnl == -30.0
    assert summary.largest_win == 75.0
    assert summary.largest_loss == -30.0


def test_calculate_summary_pending_trades(backtester):
    """Test summary calculation with pending trades."""
    trades = [
        BacktestTrade(
            date=date(2025, 11, 5),
            station_code="EGLC",
            city="London",
            bracket_name="55-60°F",
            lower=55,
            upper=60,
            zeus_prob=0.60,
            market_prob_open=0.45,
            edge=0.15,
            size_usd=500.0,
            outcome="pending",
            realized_pnl=0.0,
        ),
    ]
    
    summary = backtester._calculate_summary(
        date(2025, 11, 5),
        date(2025, 11, 5),
        trades,
    )
    
    assert summary.total_trades == 1
    assert summary.wins == 0
    assert summary.losses == 0
    assert summary.pending == 1
    assert summary.hit_rate == 0.0  # No resolved trades


def test_print_summary(backtester, caplog):
    """Test summary printing."""
    summary = BacktestSummary(
        start_date=date(2025, 11, 5),
        end_date=date(2025, 11, 7),
        total_trades=3,
        wins=2,
        losses=1,
        pending=0,
        hit_rate=66.67,
        total_risk=1200.0,
        total_pnl=93.0,
        roi=7.75,
        avg_edge=12.33,
        avg_winning_pnl=61.5,
        avg_losing_pnl=-30.0,
        largest_win=75.0,
        largest_loss=-30.0,
    )
    
    backtester._print_summary(summary)
    
    # Just verify it doesn't crash
    # (Rich logger makes it hard to capture output in tests)


@patch("agents.backtester.Backtester._backtest_single_day")
def test_run_multiple_days(mock_backtest_day, backtester):
    """Test running backtest across multiple days."""
    # Mock _backtest_single_day to return empty lists
    mock_backtest_day.return_value = []
    
    start_date = date(2025, 11, 5)
    end_date = date(2025, 11, 7)
    stations = ["EGLC", "KLGA"]
    
    output_path = backtester.run(start_date, end_date, stations)
    
    # Should call _backtest_single_day for each date and station
    # 3 days * 2 stations = 6 calls
    assert mock_backtest_day.call_count == 6
    
    # Verify output file exists
    assert output_path.exists()
    assert "2025-11-05_to_2025-11-07" in output_path.name


def test_run_invalid_station(backtester, caplog):
    """Test running backtest with invalid station code."""
    start_date = date(2025, 11, 5)
    end_date = date(2025, 11, 5)
    
    output_path = backtester.run(start_date, end_date, ["INVALID"])
    
    # Should still create output file (empty)
    assert output_path.exists()

