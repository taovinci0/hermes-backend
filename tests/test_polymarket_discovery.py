"""Tests for Polymarket market discovery.

Stage 4 implementation - Gamma API discovery with mocking.
"""

import json
from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests

from venues.polymarket.discovery import PolyDiscovery, PolymarketAPIError
from core.types import MarketBracket


# Sample Gamma API response for temperature markets
SAMPLE_GAMMA_MARKETS = [
    {
        "id": "market_59_60",
        "question": "Will London high temperature be 59-60°F on Nov 5?",
        "slug": "london-temp-59-60-nov-5",
        "condition_id": "condition_123",
        "outcome": "59-60°F",
        "active": True,
        "closed": False,
    },
    {
        "id": "market_60_61",
        "question": "Will London high temperature be 60-61°F on Nov 5?",
        "slug": "london-temp-60-61-nov-5",
        "condition_id": "condition_123",
        "outcome": "60-61°F",
        "active": True,
        "closed": False,
    },
    {
        "id": "market_61_62",
        "question": "Will London high temperature be 61–62°F on Nov 5?",  # en dash
        "slug": "london-temp-61-62-nov-5",
        "condition_id": "condition_123",
        "outcome": "61-62°F",
        "active": True,
        "closed": False,
    },
]


def test_polydiscovery_initialization() -> None:
    """Test PolyDiscovery initialization."""
    discovery = PolyDiscovery(gamma_base="https://test.gamma.api")
    
    assert discovery.gamma_base == "https://test.gamma.api"
    assert discovery.snapshot_dir.name == "polymarket"


@patch("venues.polymarket.discovery.requests.get")
def test_discovery_list_temp_brackets_success(mock_get: Mock, tmp_path: Path) -> None:
    """Test successful market discovery via event slug."""
    # Mock Gamma event API response with nested markets
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "event123",
        "slug": "highest-temperature-in-london-on-november-5",
        "title": "Highest temperature in London on November 5",
        "markets": [
            {"id": "market_59_60", "question": "Will London temperature be 59-60°F?", "clobTokenIds": "token1"},
            {"id": "market_60_61", "question": "Will London temperature be 60-61°F?", "clobTokenIds": "token2"},
            {"id": "market_61_62", "question": "Will London temperature be 61-62°F?", "clobTokenIds": "token3"},
        ]
    }
    mock_get.return_value = mock_response
    
    discovery = PolyDiscovery(gamma_base="https://test.gamma.api")
    discovery.snapshot_dir = tmp_path / "snapshots" / "polymarket"
    
    # Discover brackets
    test_date = date(2025, 11, 5)
    brackets = discovery.list_temp_brackets("London", test_date)
    
    # Verify results
    assert len(brackets) == 3
    assert all(isinstance(b, MarketBracket) for b in brackets)
    
    # Check first bracket
    assert brackets[0].name == "59-60°F"
    assert brackets[0].lower_F == 59
    assert brackets[0].upper_F == 60
    assert brackets[0].market_id == "market_59_60"
    
    # Verify sorting by lower bound
    assert brackets[0].lower_F < brackets[1].lower_F < brackets[2].lower_F
    
    # Verify snapshot saved
    snapshot_path = tmp_path / "snapshots" / "polymarket" / "events" / "London_2025-11-05.json"
    assert snapshot_path.exists()


def test_parse_bracket_from_name() -> None:
    """Test bracket parsing from various name formats."""
    discovery = PolyDiscovery()
    
    # Standard hyphen
    assert discovery._parse_bracket_from_name("59-60°F") == (59, 60)
    assert discovery._parse_bracket_from_name("Will it be 59-60°F?") == (59, 60)
    
    # En dash
    assert discovery._parse_bracket_from_name("59–60°F") == (59, 60)
    
    # With spaces
    assert discovery._parse_bracket_from_name("59 - 60°F") == (59, 60)
    
    # "to" format
    assert discovery._parse_bracket_from_name("59 to 60°F") == (59, 60)
    
    # Degrees format
    assert discovery._parse_bracket_from_name("59 - 60 degrees") == (59, 60)
    
    # No match
    assert discovery._parse_bracket_from_name("Will it rain?") is None
    assert discovery._parse_bracket_from_name("Temperature forecast") is None


def test_parse_bracket_validation() -> None:
    """Test bracket parsing validates bounds."""
    discovery = PolyDiscovery()
    
    # Invalid: lower >= upper
    assert discovery._parse_bracket_from_name("60-59°F") is None
    assert discovery._parse_bracket_from_name("60-60°F") is None
    
    # Invalid: out of reasonable range
    assert discovery._parse_bracket_from_name("200-201°F") is None
    assert discovery._parse_bracket_from_name("-10-0°F") is None


@patch("venues.polymarket.discovery.requests.get")
def test_discovery_http_error(mock_get: Mock) -> None:
    """Test Gamma API HTTP error handling."""
    # Mock HTTP error
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
    mock_get.return_value = mock_response
    
    discovery = PolyDiscovery(gamma_base="https://test.gamma.api")
    
    test_date = date(2025, 11, 5)
    
    # Should return empty list when all searches fail
    brackets = discovery.list_temp_brackets("London", test_date)
    assert brackets == []


@patch("venues.polymarket.discovery.requests.get")
def test_discovery_no_parseable_brackets(mock_get: Mock) -> None:
    """Test when event found but brackets can't be parsed."""
    # Mock event response with non-temperature markets
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "event123",
        "markets": [
            {"id": "market1", "question": "Will it rain in London?", "clobTokenIds": "token1"},
        ]
    }
    mock_get.return_value = mock_response
    
    discovery = PolyDiscovery(gamma_base="https://test.gamma.api")
    
    test_date = date(2025, 11, 5)
    
    # Now returns empty list instead of raising (graceful handling)
    brackets = discovery.list_temp_brackets("London", test_date)
    assert brackets == []


@patch("venues.polymarket.discovery.requests.get")
def test_discovery_empty_response(mock_get: Mock) -> None:
    """Test when API returns empty response."""
    # Mock empty response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = []
    mock_get.return_value = mock_response
    
    discovery = PolyDiscovery(gamma_base="https://test.gamma.api")
    
    test_date = date(2025, 11, 5)
    brackets = discovery.list_temp_brackets("London", test_date)
    
    assert brackets == []


@patch("venues.polymarket.discovery.requests.get")
def test_discovery_multiple_search_attempts(mock_get: Mock) -> None:
    """Test that discovery tries multiple event slugs."""
    # First slug 404, second succeeds
    import requests
    fail_response = Mock(status_code=404)
    fail_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Not Found")
    
    success_response = Mock(
        status_code=200,
        json=lambda: {
            "id": "event123",
            "markets": [
                {"id": "m1", "question": "59-60°F?", "clobTokenIds": "t1"},
                {"id": "m2", "question": "60-61°F?", "clobTokenIds": "t2"},
                {"id": "m3", "question": "61-62°F?", "clobTokenIds": "t3"},
            ]
        }
    )
    
    mock_get.side_effect = [fail_response, success_response]
    
    discovery = PolyDiscovery(gamma_base="https://test.gamma.api")
    
    test_date = date(2025, 11, 5)
    brackets = discovery.list_temp_brackets("London", test_date, save_snapshot=False)
    
    assert len(brackets) == 3
    assert mock_get.call_count >= 2


@patch("venues.polymarket.discovery.requests.get")
def test_discovery_without_snapshot(mock_get: Mock, tmp_path: Path) -> None:
    """Test discovery without saving snapshot."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "event123",
        "markets": [
            {"id": "m1", "question": "59-60°F?", "clobTokenIds": "t1"},
            {"id": "m2", "question": "60-61°F?", "clobTokenIds": "t2"},
            {"id": "m3", "question": "61-62°F?", "clobTokenIds": "t3"},
        ]
    }
    mock_get.return_value = mock_response
    
    discovery = PolyDiscovery(gamma_base="https://test.gamma.api")
    discovery.snapshot_dir = tmp_path / "snapshots" / "polymarket"
    
    test_date = date(2025, 11, 5)
    brackets = discovery.list_temp_brackets("London", test_date, save_snapshot=False)
    
    assert len(brackets) == 3
    
    # Verify no snapshot saved
    snapshot_path = tmp_path / "snapshots" / "polymarket" / "events"
    assert not snapshot_path.exists()


@patch("venues.polymarket.discovery.requests.get")
def test_discovery_dict_response_format(mock_get: Mock) -> None:
    """Test discovery with event containing markets."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "event123",
        "slug": "highest-temperature-in-london-on-november-5",
        "markets": [
            {"id": "m1", "question": "Will temperature be 59-60°F?", "clobTokenIds": "t1"},
            {"id": "m2", "question": "Will temperature be 60-61°F?", "clobTokenIds": "t2"},
            {"id": "m3", "question": "Will temperature be 61-62°F?", "clobTokenIds": "t3"},
        ]
    }
    mock_get.return_value = mock_response
    
    discovery = PolyDiscovery(gamma_base="https://test.gamma.api")
    
    test_date = date(2025, 11, 5)
    brackets = discovery.list_temp_brackets("London", test_date, save_snapshot=False)
    
    assert len(brackets) == 3

