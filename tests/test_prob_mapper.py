"""Tests for probability mapping.

Stage 3 implementation - probability distribution over brackets.
"""

from datetime import datetime, timezone
import pytest

from agents.prob_mapper import ProbabilityMapper
from core.types import ZeusForecast, ForecastPoint, MarketBracket


def create_test_forecast(temps_k: list[float], station_code: str = "TEST") -> ZeusForecast:
    """Helper to create a test forecast."""
    timeseries = [
        ForecastPoint(
            time_utc=datetime(2025, 11, 5, i, 0, 0, tzinfo=timezone.utc),
            temp_K=temp,
        )
        for i, temp in enumerate(temps_k)
    ]
    return ZeusForecast(timeseries=timeseries, station_code=station_code)


def create_test_brackets(start: int = 55, end: int = 70) -> list[MarketBracket]:
    """Helper to create test brackets."""
    brackets = []
    for lower in range(start, end):
        brackets.append(
            MarketBracket(
                name=f"{lower}-{lower+1}°F",
                lower_F=lower,
                upper_F=lower + 1,
            )
        )
    return brackets


def test_prob_mapper_initialization() -> None:
    """Test ProbabilityMapper initialization."""
    mapper = ProbabilityMapper(sigma_default=2.5, sigma_min=0.3, sigma_max=15.0)
    
    assert mapper.sigma_default == 2.5
    assert mapper.sigma_min == 0.3
    assert mapper.sigma_max == 15.0


def test_prob_mapper_sums_to_one() -> None:
    """Test that bracket probabilities sum to approximately 1.0."""
    # Create forecast with peak around 65°F (291.48K)
    temps_k = [
        288.15,  # 59.0°F
        289.15,  # 60.8°F
        290.15,  # 62.6°F
        291.15,  # 64.4°F
        291.48,  # 65.0°F - peak
        291.15,  # 64.4°F
        290.15,  # 62.6°F
    ]
    forecast = create_test_forecast(temps_k)
    brackets = create_test_brackets(55, 75)
    
    mapper = ProbabilityMapper()
    probs = mapper.map_daily_high(forecast, brackets)
    
    # Sum should be very close to 1.0
    total = sum(p.p_zeus for p in probs)
    assert total == pytest.approx(1.0, abs=0.0001)


def test_prob_mapper_all_positive() -> None:
    """Test that all probabilities are non-negative."""
    temps_k = [288.15 + i * 0.5 for i in range(24)]
    forecast = create_test_forecast(temps_k)
    brackets = create_test_brackets(50, 80)
    
    mapper = ProbabilityMapper()
    probs = mapper.map_daily_high(forecast, brackets)
    
    for bp in probs:
        assert bp.p_zeus >= 0.0
        assert bp.p_zeus <= 1.0


def test_prob_mapper_peak_near_mean() -> None:
    """Test that highest probability is near the forecast mean."""
    # Create forecast with clear peak at 65°F
    temps_k = [291.48] * 12  # 65°F constant
    forecast = create_test_forecast(temps_k)
    brackets = create_test_brackets(55, 75)
    
    mapper = ProbabilityMapper()
    probs = mapper.map_daily_high(forecast, brackets)
    
    # Find bracket with highest probability
    max_prob_bracket = max(probs, key=lambda bp: bp.p_zeus)
    
    # Should be around 65°F
    assert max_prob_bracket.bracket.lower_F in [64, 65, 66]


def test_prob_mapper_monotonic_shift() -> None:
    """Test that probabilities shift monotonically with mean temperature."""
    brackets = create_test_brackets(55, 75)
    mapper = ProbabilityMapper(sigma_default=2.0)
    
    # Create forecasts with increasing means
    temps_low = [288.15] * 10  # ~59°F
    temps_mid = [291.48] * 10  # ~65°F
    temps_high = [294.82] * 10  # ~71°F
    
    forecast_low = create_test_forecast(temps_low)
    forecast_mid = create_test_forecast(temps_mid)
    forecast_high = create_test_forecast(temps_high)
    
    probs_low = mapper.map_daily_high(forecast_low, brackets)
    probs_mid = mapper.map_daily_high(forecast_mid, brackets)
    probs_high = mapper.map_daily_high(forecast_high, brackets)
    
    # Find peaks
    peak_low = max(probs_low, key=lambda bp: bp.p_zeus).bracket.lower_F
    peak_mid = max(probs_mid, key=lambda bp: bp.p_zeus).bracket.lower_F
    peak_high = max(probs_high, key=lambda bp: bp.p_zeus).bracket.lower_F
    
    # Peaks should shift upward with temperature
    assert peak_low < peak_mid < peak_high


def test_prob_mapper_sigma_impact() -> None:
    """Test that higher σ spreads probability mass more evenly."""
    temps_k = [291.48] * 12  # 65°F constant
    forecast = create_test_forecast(temps_k)
    brackets = create_test_brackets(55, 75)
    
    # Narrow distribution (low sigma)
    mapper_narrow = ProbabilityMapper(sigma_default=1.0)
    probs_narrow = mapper_narrow.map_daily_high(forecast, brackets)
    
    # Wide distribution (high sigma)
    mapper_wide = ProbabilityMapper(sigma_default=5.0)
    probs_wide = mapper_wide.map_daily_high(forecast, brackets)
    
    # Narrow distribution should have higher peak
    max_prob_narrow = max(bp.p_zeus for bp in probs_narrow)
    max_prob_wide = max(bp.p_zeus for bp in probs_wide)
    
    assert max_prob_narrow > max_prob_wide
    
    # Wide distribution should have more spread
    # Count brackets with >1% probability
    significant_narrow = sum(1 for bp in probs_narrow if bp.p_zeus > 0.01)
    significant_wide = sum(1 for bp in probs_wide if bp.p_zeus > 0.01)
    
    assert significant_wide > significant_narrow


def test_prob_mapper_empty_forecast() -> None:
    """Test handling of empty forecast."""
    forecast = ZeusForecast(timeseries=[], station_code="TEST")
    brackets = create_test_brackets()
    
    mapper = ProbabilityMapper()
    
    with pytest.raises(ValueError, match="no timeseries data"):
        mapper.map_daily_high(forecast, brackets)


def test_prob_mapper_empty_brackets() -> None:
    """Test handling of empty brackets list."""
    temps_k = [288.15, 289.15, 290.15]
    forecast = create_test_forecast(temps_k)
    
    mapper = ProbabilityMapper()
    
    with pytest.raises(ValueError, match="No brackets provided"):
        mapper.map_daily_high(forecast, [])


def test_prob_mapper_sigma_clamping() -> None:
    """Test that sigma is clamped to reasonable bounds."""
    # Very uniform forecast (should produce very small sigma)
    temps_k = [288.15] * 24
    forecast = create_test_forecast(temps_k)
    brackets = create_test_brackets()
    
    mapper = ProbabilityMapper(sigma_min=0.5, sigma_max=10.0)
    probs = mapper.map_daily_high(forecast, brackets)
    
    # Sigma should be stored in BracketProb
    sigma_used = probs[0].sigma_z
    assert sigma_used >= 0.5
    assert sigma_used <= 10.0


def test_prob_mapper_empirical_sigma() -> None:
    """Test empirical sigma estimation from forecast spread."""
    # Create forecast with clear spread
    temps_k = [
        285.15,  # Low
        288.15,
        291.15,
        294.15,
        297.15,  # High
        294.15,
        291.15,
        288.15,
    ]
    forecast = create_test_forecast(temps_k)
    brackets = create_test_brackets()
    
    mapper = ProbabilityMapper(sigma_default=2.0)
    probs = mapper.map_daily_high(forecast, brackets)
    
    # Sigma should be estimated from spread (not default)
    sigma_used = probs[0].sigma_z
    # With high spread, sigma should be larger than default
    assert sigma_used > 2.0


def test_prob_mapper_single_point_forecast() -> None:
    """Test handling of single-point forecast (uses default sigma)."""
    temps_k = [291.48]  # Single point
    forecast = create_test_forecast(temps_k)
    brackets = create_test_brackets()
    
    mapper = ProbabilityMapper(sigma_default=2.5)
    probs = mapper.map_daily_high(forecast, brackets)
    
    # Should use default sigma
    sigma_used = probs[0].sigma_z
    assert sigma_used == 2.5
    
    # Should still sum to 1
    total = sum(bp.p_zeus for bp in probs)
    assert total == pytest.approx(1.0, abs=0.0001)


def test_prob_mapper_extreme_temperatures() -> None:
    """Test handling of extreme temperature forecasts."""
    # Very cold forecast
    temps_k = [250.15] * 10  # ~-9°F
    forecast_cold = create_test_forecast(temps_k)
    
    # Very hot forecast
    temps_k = [320.15] * 10  # ~116°F
    forecast_hot = create_test_forecast(temps_k)
    
    brackets = create_test_brackets(0, 120)
    mapper = ProbabilityMapper()
    
    # Should handle without errors
    probs_cold = mapper.map_daily_high(forecast_cold, brackets)
    probs_hot = mapper.map_daily_high(forecast_hot, brackets)
    
    # Probabilities should sum to 1
    assert sum(bp.p_zeus for bp in probs_cold) == pytest.approx(1.0, abs=0.01)
    assert sum(bp.p_zeus for bp in probs_hot) == pytest.approx(1.0, abs=0.01)


def test_prob_mapper_bracket_probability_details() -> None:
    """Test detailed bracket probability computation."""
    # Create very predictable forecast
    temps_k = [288.71] * 24  # Exactly 60.0°F
    forecast = create_test_forecast(temps_k)
    
    # Create specific brackets around 60°F
    brackets = [
        MarketBracket(name="58-59°F", lower_F=58, upper_F=59),
        MarketBracket(name="59-60°F", lower_F=59, upper_F=60),
        MarketBracket(name="60-61°F", lower_F=60, upper_F=61),
        MarketBracket(name="61-62°F", lower_F=61, upper_F=62),
    ]
    
    mapper = ProbabilityMapper(sigma_default=1.0)
    probs = mapper.map_daily_high(forecast, brackets)
    
    # With μ=60 and small σ, [60-61) should have highest probability
    prob_dict = {bp.bracket.name: bp.p_zeus for bp in probs}
    assert prob_dict["60-61°F"] > prob_dict["59-60°F"]
    assert prob_dict["60-61°F"] > prob_dict["61-62°F"]


def test_prob_mapper_sigma_stored_in_result() -> None:
    """Test that sigma_z is stored in BracketProb results."""
    temps_k = [288.15 + i * 0.3 for i in range(24)]
    forecast = create_test_forecast(temps_k)
    brackets = create_test_brackets()
    
    mapper = ProbabilityMapper()
    probs = mapper.map_daily_high(forecast, brackets)
    
    # All brackets should have same sigma_z
    sigmas = [bp.sigma_z for bp in probs]
    assert all(s == sigmas[0] for s in sigmas)
    assert sigmas[0] > 0

