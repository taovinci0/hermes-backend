"""Tests for Polymarket Resolution (Stage 7A).

Tests resolution fetching and outcome determination.
"""

from unittest.mock import MagicMock, patch
import pytest

from venues.polymarket.resolution import PolyResolution, PolymarketResolutionError


@pytest.fixture
def resolution():
    """Create a PolyResolution instance."""
    return PolyResolution()


def test_resolution_init():
    """Test PolyResolution initialization."""
    res = PolyResolution()
    
    assert res.gamma_base is not None
    assert res.snapshot_dir.exists()
    assert str(res.snapshot_dir).endswith("polymarket/resolution")


@patch("venues.polymarket.resolution.requests.get")
def test_get_winner_resolved_market(mock_get, resolution):
    """Test getting winner for a resolved market."""
    # Mock successful resolved market response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{
        "id": "market123",
        "resolved": True,
        "winning_outcome": "55-60",
        "status": "resolved"
    }]
    mock_get.return_value = mock_response
    
    result = resolution.get_winner("market123", save_snapshot=False)
    
    assert result["resolved"] is True
    assert result["winner"] == "55-60"
    assert "raw" in result


@patch("venues.polymarket.resolution.requests.get")
def test_get_winner_unresolved_market(mock_get, resolution):
    """Test getting winner for an unresolved market."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{
        "id": "market123",
        "resolved": False,
        "status": "active"
    }]
    mock_get.return_value = mock_response
    
    result = resolution.get_winner("market123", save_snapshot=False)
    
    assert result["resolved"] is False
    assert result["winner"] is None


@patch("venues.polymarket.resolution.requests.get")
def test_get_winner_with_outcomes_array(mock_get, resolution):
    """Test parsing winner from outcomes array."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{
        "id": "market123",
        "resolved": True,
        "status": "resolved",
        "outcomes": [
            {"name": "50-55°F", "winner": False, "payout": "0"},
            {"name": "55-60°F", "winner": True, "payout": "1"},
            {"name": "60-65°F", "winner": False, "payout": "0"},
        ]
    }]
    mock_get.return_value = mock_response
    
    result = resolution.get_winner("market123", save_snapshot=False)
    
    assert result["resolved"] is True
    assert result["winner"] == "55-60"  # °F removed


@patch("venues.polymarket.resolution.requests.get")
def test_get_winner_cleans_temperature_format(mock_get, resolution):
    """Test that winner string is cleaned (°F removed)."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{
        "id": "market123",
        "resolved": True,
        "winning_outcome": "55-60°F"
    }]
    mock_get.return_value = mock_response
    
    result = resolution.get_winner("market123", save_snapshot=False)
    
    assert result["winner"] == "55-60"  # No °F
    assert "°" not in result["winner"]


@patch("venues.polymarket.resolution.requests.get")
def test_get_winner_http_error(mock_get, resolution):
    """Test handling of HTTP errors."""
    import requests
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Not found")
    mock_get.return_value = mock_response
    
    with pytest.raises(PolymarketResolutionError):
        resolution.get_winner("market123", save_snapshot=False)


@patch("venues.polymarket.resolution.requests.get")
def test_get_winner_timeout(mock_get, resolution):
    """Test handling of timeouts."""
    import requests
    mock_get.side_effect = requests.exceptions.Timeout("Timeout")
    
    with pytest.raises(PolymarketResolutionError):
        resolution.get_winner("market123", save_snapshot=False)


@patch("venues.polymarket.resolution.requests.get")
def test_get_winner_empty_response(mock_get, resolution):
    """Test handling of empty response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = []
    mock_get.return_value = mock_response
    
    result = resolution.get_winner("market123", save_snapshot=False)
    
    assert result["resolved"] is False
    assert result["winner"] is None


def test_get_winner_no_market_id(resolution):
    """Test handling of missing market_id."""
    result = resolution.get_winner("", save_snapshot=False)
    
    assert result["resolved"] is False
    assert result["winner"] is None


def test_get_winner_none_market_id(resolution):
    """Test handling of None market_id."""
    result = resolution.get_winner(None, save_snapshot=False)
    
    assert result["resolved"] is False
    assert result["winner"] is None


@patch("venues.polymarket.resolution.requests.get")
def test_get_winner_saves_snapshot(mock_get, resolution, tmp_path):
    """Test that snapshot is saved when requested."""
    # Override snapshot dir to use tmp_path
    resolution.snapshot_dir = tmp_path
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{
        "id": "market123",
        "resolved": True,
        "winning_outcome": "55-60"
    }]
    mock_get.return_value = mock_response
    
    resolution.get_winner("market123", save_snapshot=True)
    
    # Check snapshot was saved
    snapshot_file = tmp_path / "market123.json"
    assert snapshot_file.exists()


@patch("venues.polymarket.resolution.requests.get")
def test_get_winner_retry_on_failure(mock_get, resolution):
    """Test that retries work on transient failures."""
    # First two calls fail, third succeeds
    mock_get.side_effect = [
        Exception("Temporary failure"),
        Exception("Temporary failure"),
        MagicMock(
            status_code=200,
            json=lambda: [{
                "id": "market123",
                "resolved": True,
                "winning_outcome": "55-60"
            }]
        )
    ]
    
    result = resolution.get_winner("market123", save_snapshot=False)
    
    assert result["resolved"] is True
    assert result["winner"] == "55-60"
    assert mock_get.call_count == 3


@patch("venues.polymarket.resolution.requests.get")
def test_get_winner_alternative_status_field(mock_get, resolution):
    """Test resolution detection with different status fields."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{
        "id": "market123",
        "resolved": False,  # This is False
        "status": "closed",  # But status is closed
        "winning_outcome": "55-60"
    }]
    mock_get.return_value = mock_response
    
    result = resolution.get_winner("market123", save_snapshot=False)
    
    # Should be resolved because status is "closed"
    assert result["resolved"] is True
    assert result["winner"] == "55-60"


@patch("venues.polymarket.resolution.requests.get")
def test_get_winner_payout_detection(mock_get, resolution):
    """Test winner detection via payout field."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{
        "id": "market123",
        "resolved": True,
        "outcomes": [
            {"name": "50-55", "payout": "0"},
            {"name": "55-60", "payout": "1.0"},  # Winner via payout
        ]
    }]
    mock_get.return_value = mock_response
    
    result = resolution.get_winner("market123", save_snapshot=False)
    
    assert result["resolved"] is True
    assert result["winner"] == "55-60"


@patch("venues.polymarket.resolution.requests.get")
def test_get_winner_dict_response_format(mock_get, resolution):
    """Test handling dict response with 'markets' key."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "markets": [{
            "id": "market123",
            "resolved": True,
            "winning_outcome": "55-60"
        }]
    }
    mock_get.return_value = mock_response
    
    result = resolution.get_winner("market123", save_snapshot=False)
    
    assert result["resolved"] is True
    assert result["winner"] == "55-60"

