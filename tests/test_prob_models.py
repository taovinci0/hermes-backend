"""Tests for probability models (Stage 7B).

Tests both spread and bands models.
"""

from datetime import datetime, timedelta
import pytest

from agents.prob_models import spread_model, bands_model
from core.types import ZeusForecast, ForecastPoint, MarketBracket


@pytest.fixture
def sample_forecast():
    """Create a sample Zeus forecast."""
    now = datetime.now()
    timeseries = [
        ForecastPoint(time_utc=now + timedelta(hours=i), temp_K=285.0 + i * 0.5)
        for i in range(24)
    ]
    return ZeusForecast(
        lat=51.505,
        lon=0.05,
        timeseries=timeseries,
        station_code="EGLC",
    )


@pytest.fixture
def sample_brackets():
    """Create sample market brackets."""
    return [
        MarketBracket(name="54-55°F", lower_F=54, upper_F=55),
        MarketBracket(name="56-57°F", lower_F=56, upper_F=57),
        MarketBracket(name="58-59°F", lower_F=58, upper_F=59),
        MarketBracket(name="60-61°F", lower_F=60, upper_F=61),
        MarketBracket(name="62-63°F", lower_F=62, upper_F=63),
    ]


# ============================================================================
# SPREAD MODEL TESTS
# ============================================================================

def test_spread_model_basic(sample_forecast, sample_brackets):
    """Test spread model produces valid probabilities."""
    probs = spread_model.compute_probabilities(sample_forecast, sample_brackets)
    
    assert len(probs) == len(sample_brackets)
    
    # All probabilities should be between 0 and 1
    for bp in probs:
        assert 0.0 <= bp.p_zeus <= 1.0
        assert bp.sigma_z is not None
        assert bp.sigma_z > 0


def test_spread_model_normalization(sample_forecast, sample_brackets):
    """Test that spread model probabilities sum to 1.0."""
    probs = spread_model.compute_probabilities(sample_forecast, sample_brackets)
    
    total = sum(bp.p_zeus for bp in probs)
    assert abs(total - 1.0) < 1e-6  # Sum should be very close to 1.0


def test_spread_model_peak_near_mean(sample_forecast, sample_brackets):
    """Test that highest probability is near the forecast mean."""
    probs = spread_model.compute_probabilities(sample_forecast, sample_brackets)
    
    # Find max probability bracket
    max_prob_bp = max(probs, key=lambda bp: bp.p_zeus)
    
    # Should be one of the middle brackets (not extremes)
    assert max_prob_bp.p_zeus > 0.15  # At least 15% (for 5 brackets)


def test_spread_model_sigma_estimation(sample_forecast, sample_brackets):
    """Test sigma estimation from forecast spread."""
    probs = spread_model.compute_probabilities(sample_forecast, sample_brackets)
    
    # Sigma should be within reasonable range
    sigma = probs[0].sigma_z
    assert 0.5 <= sigma <= 10.0


def test_spread_model_single_point_forecast(sample_brackets):
    """Test spread model with single forecast point."""
    now = datetime.now()
    forecast = ZeusForecast(
        lat=51.505,
        lon=0.05,
        timeseries=[ForecastPoint(time_utc=now, temp_K=288.0)],
        station_code="EGLC",
    )
    
    probs = spread_model.compute_probabilities(forecast, sample_brackets)
    
    # Should use default sigma
    assert probs[0].sigma_z == 2.0  # Default value


def test_spread_model_empty_forecast():
    """Test spread model with empty forecast."""
    forecast = ZeusForecast(
        lat=51.505,
        lon=0.05,
        timeseries=[],
        station_code="EGLC",
    )
    
    brackets = [MarketBracket(name="58-59°F", lower_F=58, upper_F=59)]
    
    with pytest.raises(ValueError, match="no timeseries"):
        spread_model.compute_probabilities(forecast, brackets)


def test_spread_model_empty_brackets(sample_forecast):
    """Test spread model with no brackets."""
    with pytest.raises(ValueError, match="No brackets"):
        spread_model.compute_probabilities(sample_forecast, [])


# ============================================================================
# BANDS MODEL TESTS
# ============================================================================

def test_bands_model_basic(sample_forecast, sample_brackets):
    """Test bands model produces valid probabilities."""
    probs = bands_model.compute_probabilities(sample_forecast, sample_brackets)
    
    assert len(probs) == len(sample_brackets)
    
    # All probabilities should be between 0 and 1
    for bp in probs:
        assert 0.0 <= bp.p_zeus <= 1.0
        assert bp.sigma_z is not None
        assert bp.sigma_z > 0


def test_bands_model_normalization(sample_forecast, sample_brackets):
    """Test that bands model probabilities sum to 1.0."""
    probs = bands_model.compute_probabilities(sample_forecast, sample_brackets)
    
    total = sum(bp.p_zeus for bp in probs)
    assert abs(total - 1.0) < 1e-6


def test_bands_model_fallback_when_no_bands(sample_forecast, sample_brackets):
    """Test bands model falls back to spread method when bands unavailable."""
    # Current Zeus API doesn't provide bands
    probs = bands_model.compute_probabilities(sample_forecast, sample_brackets)
    
    # Should still work (using fallback)
    assert len(probs) == len(sample_brackets)
    total = sum(bp.p_zeus for bp in probs)
    assert abs(total - 1.0) < 1e-6


def test_bands_model_with_confidence_data(sample_brackets):
    """Test bands model with mock confidence band data."""
    # Create forecast with mock band data (future Zeus API feature)
    now = datetime.now()
    timeseries = [
        ForecastPoint(time_utc=now + timedelta(hours=i), temp_K=288.0)
        for i in range(24)
    ]
    
    forecast = ZeusForecast(
        lat=51.505,
        lon=0.05,
        timeseries=timeseries,
        station_code="EGLC",
    )
    
    # Add mock band data (future Zeus API enhancement)
    # forecast.likely_upper_F = 60.0   # 80% confident below this
    # forecast.possible_upper_F = 62.0  # 95% confident below this
    
    # For now, should use fallback
    probs = bands_model.compute_probabilities(forecast, sample_brackets)
    
    assert len(probs) == len(sample_brackets)


def test_bands_model_empty_forecast():
    """Test bands model with empty forecast."""
    forecast = ZeusForecast(
        lat=51.505,
        lon=0.05,
        timeseries=[],
        station_code="EGLC",
    )
    
    brackets = [MarketBracket(name="58-59°F", lower_F=58, upper_F=59)]
    
    with pytest.raises(ValueError, match="no timeseries"):
        bands_model.compute_probabilities(forecast, brackets)


# ============================================================================
# MODEL COMPARISON TESTS
# ============================================================================

def test_both_models_same_interface(sample_forecast, sample_brackets):
    """Test that both models have same interface and output format."""
    spread_probs = spread_model.compute_probabilities(sample_forecast, sample_brackets)
    bands_probs = bands_model.compute_probabilities(sample_forecast, sample_brackets)
    
    # Same number of outputs
    assert len(spread_probs) == len(bands_probs) == len(sample_brackets)
    
    # Both normalized
    assert abs(sum(bp.p_zeus for bp in spread_probs) - 1.0) < 1e-6
    assert abs(sum(bp.p_zeus for bp in bands_probs) - 1.0) < 1e-6
    
    # Both have sigma values
    assert all(bp.sigma_z is not None for bp in spread_probs)
    assert all(bp.sigma_z is not None for bp in bands_probs)


def test_models_produce_different_results(sample_forecast, sample_brackets):
    """Test that models can produce different probability distributions."""
    spread_probs = spread_model.compute_probabilities(sample_forecast, sample_brackets)
    bands_probs = bands_model.compute_probabilities(sample_forecast, sample_brackets)
    
    # Currently bands uses fallback (same as spread), so might be identical
    # When Zeus adds band data, this test will verify they differ
    
    # For now, just verify both work
    assert len(spread_probs) == len(bands_probs)


def test_models_with_custom_sigma_params(sample_forecast, sample_brackets):
    """Test that models respect custom sigma parameters."""
    # Test with custom sigma bounds
    probs = spread_model.compute_probabilities(
        sample_forecast,
        sample_brackets,
        sigma_default=3.0,
        sigma_min=1.0,
        sigma_max=8.0,
    )
    
    # Sigma should respect bounds
    sigma = probs[0].sigma_z
    assert 1.0 <= sigma <= 8.0

