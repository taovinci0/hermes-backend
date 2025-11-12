"""Tests for paper execution.

Stage 6 implementation - Paper broker with CSV logging.
"""

import csv
from datetime import datetime, timezone
from pathlib import Path

import pytest

from venues.polymarket.execute import PaperBroker, Broker
from core.types import EdgeDecision, MarketBracket


def test_paper_broker_initialization(tmp_path: Path) -> None:
    """Test PaperBroker initialization."""
    broker = PaperBroker(trades_dir=tmp_path / "trades")
    
    assert broker.trades_dir == tmp_path / "trades"
    assert broker.trades_placed == []


def test_paper_broker_is_broker() -> None:
    """Test that PaperBroker is a Broker subclass."""
    broker = PaperBroker()
    
    assert isinstance(broker, Broker)


def test_paper_broker_place_single_trade(tmp_path: Path) -> None:
    """Test placing a single paper trade."""
    broker = PaperBroker(trades_dir=tmp_path / "trades")
    
    # Create a decision
    bracket = MarketBracket(name="59-60°F", lower_F=59, upper_F=60, market_id="m1")
    decision = EdgeDecision(
        bracket=bracket,
        edge=0.0920,
        f_kelly=0.20,
        size_usd=250.0,
        reason="standard",
    )
    
    csv_path = broker.place([decision])
    
    # Verify CSV was created
    assert csv_path.exists()
    assert csv_path.name == "paper_trades.csv"
    
    # Verify content
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 1
    row = rows[0]
    
    assert row["bracket_name"] == "59-60°F"
    assert row["bracket_lower_f"] == "59"
    assert row["bracket_upper_f"] == "60"
    assert row["market_id"] == "m1"
    assert float(row["edge"]) == pytest.approx(0.0920, abs=1e-4)
    assert float(row["edge_pct"]) == pytest.approx(9.20, abs=0.01)
    assert float(row["f_kelly"]) == pytest.approx(0.20, abs=1e-4)
    assert float(row["size_usd"]) == pytest.approx(250.0, abs=0.01)
    assert row["reason"] == "standard"


def test_paper_broker_place_multiple_trades(tmp_path: Path) -> None:
    """Test placing multiple paper trades."""
    broker = PaperBroker(trades_dir=tmp_path / "trades")
    
    # Create multiple decisions
    decisions = [
        EdgeDecision(
            bracket=MarketBracket(name="59-60°F", lower_F=59, upper_F=60, market_id="m1"),
            edge=0.10,
            f_kelly=0.20,
            size_usd=200.0,
            reason="strong_edge",
        ),
        EdgeDecision(
            bracket=MarketBracket(name="60-61°F", lower_F=60, upper_F=61, market_id="m2"),
            edge=0.08,
            f_kelly=0.15,
            size_usd=150.0,
            reason="kelly_capped",
        ),
        EdgeDecision(
            bracket=MarketBracket(name="61-62°F", lower_F=61, upper_F=62, market_id="m3"),
            edge=0.06,
            f_kelly=0.12,
            size_usd=120.0,
            reason="standard",
        ),
    ]
    
    csv_path = broker.place(decisions)
    
    # Verify all trades recorded
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 3
    assert rows[0]["bracket_name"] == "59-60°F"
    assert rows[1]["bracket_name"] == "60-61°F"
    assert rows[2]["bracket_name"] == "61-62°F"


def test_paper_broker_append_mode(tmp_path: Path) -> None:
    """Test that broker appends to existing CSV."""
    broker = PaperBroker(trades_dir=tmp_path / "trades")
    
    # Place first trade
    decision1 = EdgeDecision(
        bracket=MarketBracket(name="59-60°F", lower_F=59, upper_F=60, market_id="m1"),
        edge=0.10,
        f_kelly=0.20,
        size_usd=200.0,
        reason="first",
    )
    csv_path = broker.place([decision1])
    
    # Place second trade
    decision2 = EdgeDecision(
        bracket=MarketBracket(name="60-61°F", lower_F=60, upper_F=61, market_id="m2"),
        edge=0.08,
        f_kelly=0.15,
        size_usd=150.0,
        reason="second",
    )
    csv_path = broker.place([decision2])
    
    # Verify both trades in file
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 2
    assert rows[0]["reason"] == "first"
    assert rows[1]["reason"] == "second"


def test_paper_broker_empty_decisions(tmp_path: Path) -> None:
    """Test broker with empty decisions list."""
    broker = PaperBroker(trades_dir=tmp_path / "trades")
    
    result = broker.place([])
    
    # Should return None and not create file
    assert result is None


def test_paper_broker_get_trades() -> None:
    """Test getting trades placed in session."""
    broker = PaperBroker()
    
    decision = EdgeDecision(
        bracket=MarketBracket(name="59-60°F", lower_F=59, upper_F=60, market_id="m1"),
        edge=0.10,
        f_kelly=0.20,
        size_usd=200.0,
        reason="test",
    )
    
    # Initially empty
    assert broker.get_trades() == []
    
    # Place trade (will fail without proper path, but that's ok for this test)
    try:
        broker.place([decision])
    except:
        pass
    
    # Should have tracked the trade
    trades = broker.get_trades()
    assert len(trades) == 1
    assert trades[0].bracket.name == "59-60°F"


def test_paper_broker_csv_header() -> None:
    """Test that CSV header contains all required fields."""
    broker = PaperBroker(trades_dir=Path("/tmp/hermes_test_trades"))
    
    decision = EdgeDecision(
        bracket=MarketBracket(name="59-60°F", lower_F=59, upper_F=60, market_id="m1"),
        edge=0.10,
        f_kelly=0.20,
        size_usd=200.0,
        reason="test",
    )
    
    csv_path = broker.place([decision])
    
    # Read header
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
    
    # Verify required fields
    required_fields = [
        "timestamp",
        "bracket_name",
        "bracket_lower_f",
        "bracket_upper_f",
        "market_id",
        "edge",
        "edge_pct",
        "f_kelly",
        "size_usd",
        "reason",
    ]
    
    for field in required_fields:
        assert field in fieldnames, f"Missing field: {field}"


def test_paper_broker_timestamp_format(tmp_path: Path) -> None:
    """Test that timestamps are in ISO format."""
    broker = PaperBroker(trades_dir=tmp_path / "trades")
    
    decision = EdgeDecision(
        bracket=MarketBracket(name="59-60°F", lower_F=59, upper_F=60, market_id="m1"),
        edge=0.10,
        f_kelly=0.20,
        size_usd=200.0,
        reason="test",
        timestamp=datetime(2025, 11, 5, 12, 30, 45, tzinfo=timezone.utc),
    )
    
    csv_path = broker.place([decision])
    
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        row = next(reader)
    
    # Verify ISO format
    timestamp = datetime.fromisoformat(row["timestamp"])
    assert timestamp.year == 2025
    assert timestamp.month == 11
    assert timestamp.day == 5


def test_paper_broker_directory_creation(tmp_path: Path) -> None:
    """Test that broker creates trade directory if it doesn't exist."""
    trades_dir = tmp_path / "new_trades_dir"
    
    # Directory doesn't exist yet
    assert not trades_dir.exists()
    
    broker = PaperBroker(trades_dir=trades_dir)
    
    decision = EdgeDecision(
        bracket=MarketBracket(name="59-60°F", lower_F=59, upper_F=60, market_id="m1"),
        edge=0.10,
        f_kelly=0.20,
        size_usd=200.0,
        reason="test",
    )
    
    csv_path = broker.place([decision])
    
    # Directory should be created
    assert trades_dir.exists()
    assert csv_path.exists()

