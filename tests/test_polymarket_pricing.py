"""Tests for Polymarket pricing.

Stage 4 implementation - CLOB API pricing with mocking.
"""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests

from venues.polymarket.pricing import PolyPricing, PolymarketPricingError
from venues.polymarket.schemas import MarketDepth
from core.types import MarketBracket


def test_polypricing_initialization() -> None:
    """Test PolyPricing initialization."""
    pricing = PolyPricing(clob_base="https://test.clob.api")
    
    assert pricing.clob_base == "https://test.clob.api"
    assert pricing.snapshot_dir.name == "polymarket"


@patch("venues.polymarket.pricing.requests.get")
def test_pricing_midprob_success(mock_get: Mock) -> None:
    """Test successful midprice fetch."""
    # Mock CLOB API response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"mid": 0.6234, "market": "market_59_60"}
    mock_get.return_value = mock_response
    
    pricing = PolyPricing(clob_base="https://test.clob.api")
    
    bracket = MarketBracket(
        name="59-60°F",
        lower_F=59,
        upper_F=60,
        market_id="market_59_60"
    )
    
    prob = pricing.midprob(bracket)
    
    assert prob == 0.6234
    
    # Verify API was called correctly
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert "/midpoint" in args[0]
    assert kwargs["params"]["market"] == "market_59_60"


@patch("venues.polymarket.pricing.requests.get")
def test_pricing_midprob_clamping(mock_get: Mock) -> None:
    """Test midprice clamping to [0, 1]."""
    # Mock response with out-of-range value
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"mid": 1.5}
    mock_get.return_value = mock_response
    
    pricing = PolyPricing(clob_base="https://test.clob.api")
    
    bracket = MarketBracket(
        name="59-60°F",
        lower_F=59,
        upper_F=60,
        market_id="market_59_60"
    )
    
    prob = pricing.midprob(bracket)
    
    # Should be clamped to 1.0
    assert prob == 1.0


def test_pricing_midprob_no_market_id() -> None:
    """Test midprob with missing market_id."""
    pricing = PolyPricing()
    
    bracket = MarketBracket(
        name="59-60°F",
        lower_F=59,
        upper_F=60,
        market_id=None
    )
    
    with pytest.raises(ValueError, match="no market_id"):
        pricing.midprob(bracket)


@patch("venues.polymarket.pricing.requests.get")
def test_pricing_midprob_missing_mid_field(mock_get: Mock) -> None:
    """Test midprob with missing 'mid' field in response."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"market": "market_59_60"}  # No 'mid' field
    mock_get.return_value = mock_response
    
    pricing = PolyPricing(clob_base="https://test.clob.api")
    
    bracket = MarketBracket(
        name="59-60°F",
        lower_F=59,
        upper_F=60,
        market_id="market_59_60"
    )
    
    with pytest.raises(ValueError, match="No midprice"):
        pricing.midprob(bracket)


@patch("venues.polymarket.pricing.requests.get")
def test_pricing_depth_success(mock_get: Mock) -> None:
    """Test successful depth/liquidity fetch."""
    # Mock order book response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "market": "market_59_60",
        "bids": [
            {"price": "0.60", "size": "100"},
            {"price": "0.59", "size": "200"},
        ],
        "asks": [
            {"price": "0.62", "size": "150"},
            {"price": "0.63", "size": "250"},
        ],
    }
    mock_get.return_value = mock_response
    
    pricing = PolyPricing(clob_base="https://test.clob.api")
    
    bracket = MarketBracket(
        name="59-60°F",
        lower_F=59,
        upper_F=60,
        market_id="market_59_60"
    )
    
    depth = pricing.depth(bracket)
    
    # Verify depth calculation
    assert isinstance(depth, MarketDepth)
    assert depth.token_id == "market_59_60"
    
    # Bid depth: 0.60*100 + 0.59*200 = 60 + 118 = 178
    assert depth.bid_depth_usd == pytest.approx(178.0, abs=0.01)
    
    # Ask depth: 0.62*150 + 0.63*250 = 93 + 157.5 = 250.5
    assert depth.ask_depth_usd == pytest.approx(250.5, abs=0.01)
    
    # Midprice: (0.60 + 0.62) / 2 = 0.61
    assert depth.mid_price == pytest.approx(0.61, abs=0.01)
    
    # Spread: (0.62 - 0.60) / 0.61 * 10000 ≈ 327.87 bps
    assert depth.spread_bps == pytest.approx(327.87, abs=1.0)


@patch("venues.polymarket.pricing.requests.get")
def test_pricing_depth_empty_book(mock_get: Mock) -> None:
    """Test depth with empty order book."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "market": "market_59_60",
        "bids": [],
        "asks": [],
    }
    mock_get.return_value = mock_response
    
    pricing = PolyPricing(clob_base="https://test.clob.api")
    
    bracket = MarketBracket(
        name="59-60°F",
        lower_F=59,
        upper_F=60,
        market_id="market_59_60"
    )
    
    depth = pricing.depth(bracket)
    
    assert depth.bid_depth_usd == 0.0
    assert depth.ask_depth_usd == 0.0
    assert depth.mid_price is None
    assert depth.spread_bps is None


def test_pricing_depth_no_market_id() -> None:
    """Test depth with missing market_id."""
    pricing = PolyPricing()
    
    bracket = MarketBracket(
        name="59-60°F",
        lower_F=59,
        upper_F=60,
        market_id=None
    )
    
    with pytest.raises(ValueError, match="no market_id"):
        pricing.depth(bracket)


@patch("venues.polymarket.pricing.requests.get")
def test_pricing_http_error(mock_get: Mock) -> None:
    """Test CLOB API HTTP error handling."""
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
    mock_get.return_value = mock_response
    
    pricing = PolyPricing(clob_base="https://test.clob.api")
    
    bracket = MarketBracket(
        name="59-60°F",
        lower_F=59,
        upper_F=60,
        market_id="market_59_60"
    )
    
    with pytest.raises(PolymarketPricingError, match="HTTP error"):
        pricing.midprob(bracket)


@patch("venues.polymarket.pricing.requests.get")
def test_pricing_timeout(mock_get: Mock) -> None:
    """Test CLOB API timeout handling."""
    mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
    
    pricing = PolyPricing(clob_base="https://test.clob.api")
    
    bracket = MarketBracket(
        name="59-60°F",
        lower_F=59,
        upper_F=60,
        market_id="market_59_60"
    )
    
    with pytest.raises(PolymarketPricingError, match="timeout"):
        pricing.midprob(bracket)


@patch("venues.polymarket.pricing.requests.get")
def test_pricing_snapshot_saved(mock_get: Mock, tmp_path: Path) -> None:
    """Test that pricing snapshots are saved when requested."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"mid": 0.65}
    mock_get.return_value = mock_response
    
    pricing = PolyPricing(clob_base="https://test.clob.api")
    pricing.snapshot_dir = tmp_path / "snapshots" / "polymarket"
    
    bracket = MarketBracket(
        name="59-60°F",
        lower_F=59,
        upper_F=60,
        market_id="market_test"
    )
    
    prob = pricing.midprob(bracket, save_snapshot=True)
    
    assert prob == 0.65
    
    # Verify snapshot saved
    snapshot_path = tmp_path / "snapshots" / "polymarket" / "midpoint" / "market_test.json"
    assert snapshot_path.exists()
    
    with open(snapshot_path) as f:
        saved_data = json.load(f)
    assert saved_data["mid"] == 0.65

