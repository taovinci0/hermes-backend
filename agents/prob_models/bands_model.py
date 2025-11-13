"""Bands Model - Stage 7B probability calculation using confidence intervals.

Uses Zeus's likely (≈80%) and possible (≈95%) confidence ranges to estimate
implied volatility σ_Z and compute bracket probabilities.

Method:
- μ (mean) = peak hour temperature
- σ from confidence bands:
  - σ₁ = (likely_upper - μ) / z₈₀   where z₈₀ = 0.8416
  - σ₂ = (possible_upper - μ) / z₉₅  where z₉₅ = 1.6449
  - σ_Z = mean([σ₁, σ₂])
- P(bracket) = Φ((b-μ)/σ_Z) - Φ((a-μ)/σ_Z)
"""

from typing import List, Optional
import numpy as np
from scipy.stats import norm

from core.types import ZeusForecast, MarketBracket, BracketProb
from core.logger import logger
from core import units


# Standard normal z-scores for confidence intervals
Z_80 = 0.8416  # 80% confidence → ±0.8416 std devs
Z_95 = 1.6449  # 95% confidence → ±1.6449 std devs


def _extract_confidence_bands(forecast: ZeusForecast) -> Optional[tuple[float, float, float]]:
    """Extract confidence bands from Zeus forecast if available.
    
    Args:
        forecast: Zeus forecast with potential band data
    
    Returns:
        Tuple of (mean_F, likely_upper_F, possible_upper_F) or None
    """
    # Check if forecast has band data (future Zeus API enhancement)
    if hasattr(forecast, 'likely_upper_F') and hasattr(forecast, 'possible_upper_F'):
        temps_f = [units.kelvin_to_fahrenheit(p.temp_K) for p in forecast.timeseries]
        mean_F = max(temps_f)  # Peak temperature
        
        likely_upper_F = forecast.likely_upper_F
        possible_upper_F = forecast.possible_upper_F
        
        logger.debug(
            f"Found Zeus bands: mean={mean_F:.1f}°F, "
            f"likely_upper={likely_upper_F:.1f}°F, "
            f"possible_upper={possible_upper_F:.1f}°F"
        )
        
        return (mean_F, likely_upper_F, possible_upper_F)
    
    # Bands not available in current Zeus API response
    logger.debug("Zeus confidence bands not available in forecast")
    return None


def _estimate_sigma_from_bands(
    mean_F: float,
    likely_upper_F: float,
    possible_upper_F: float,
    sigma_min: float = 0.5,
    sigma_max: float = 10.0,
) -> float:
    """Estimate σ_Z from Zeus confidence bands.
    
    Uses two z-scores:
    - 80% confidence: z₈₀ = 0.8416
    - 95% confidence: z₉₅ = 1.6449
    
    Calculates:
    - σ₁ = (likely_upper - mean) / z₈₀
    - σ₂ = (possible_upper - mean) / z₉₅
    - σ_Z = mean([σ₁, σ₂])
    
    Args:
        mean_F: Mean temperature in °F
        likely_upper_F: 80% confidence upper bound in °F
        possible_upper_F: 95% confidence upper bound in °F
        sigma_min: Minimum allowed σ
        sigma_max: Maximum allowed σ
    
    Returns:
        Estimated σ_Z in °F
    """
    # Calculate sigma from each band
    sigma_1 = abs(likely_upper_F - mean_F) / Z_80
    sigma_2 = abs(possible_upper_F - mean_F) / Z_95
    
    logger.debug(
        f"Band-derived sigmas: σ₁={sigma_1:.2f}°F (from likely), "
        f"σ₂={sigma_2:.2f}°F (from possible)"
    )
    
    # Average the two estimates
    sigma_Z = np.nanmean([sigma_1, sigma_2])
    
    # Clamp to reasonable range
    sigma_Z = float(np.clip(sigma_Z, sigma_min, sigma_max))
    
    logger.debug(f"Final σ_Z = {sigma_Z:.2f}°F (clamped to [{sigma_min}, {sigma_max}])")
    
    return sigma_Z


def compute_probabilities(
    forecast: ZeusForecast,
    brackets: List[MarketBracket],
    sigma_default: float = 2.0,
    sigma_min: float = 0.5,
    sigma_max: float = 10.0,
) -> List[BracketProb]:
    """Compute bracket probabilities using Zeus confidence bands model.
    
    Falls back to spread model if bands are not available.
    
    Args:
        forecast: Zeus hourly temperature forecast
        brackets: List of market brackets
        sigma_default: Default uncertainty if bands unavailable
        sigma_min: Minimum allowed σ
        sigma_max: Maximum allowed σ
    
    Returns:
        List of BracketProb with computed probabilities
    
    Raises:
        ValueError: If forecast or brackets are invalid
    """
    if not forecast.timeseries:
        raise ValueError("Forecast has no timeseries data")
    
    if not brackets:
        raise ValueError("No brackets provided")
    
    logger.debug(f"Using BANDS model for {forecast.station_code}")
    
    # Try to extract confidence bands from Zeus
    bands_data = _extract_confidence_bands(forecast)
    
    if bands_data:
        # Use bands model
        mean_F, likely_upper_F, possible_upper_F = bands_data
        mu = mean_F
        sigma = _estimate_sigma_from_bands(
            mean_F, likely_upper_F, possible_upper_F, sigma_min, sigma_max
        )
        logger.info(
            f"Bands model: μ = {mu:.2f}°F, σ = {sigma:.2f}°F "
            f"(from likely={likely_upper_F:.1f}°F, possible={possible_upper_F:.1f}°F)"
        )
    else:
        # Fallback to spread-like calculation
        # (Zeus API doesn't provide bands yet)
        logger.warning(
            "Zeus confidence bands not available, using fallback spread calculation"
        )
        temps_k = [point.temp_K for point in forecast.timeseries]
        temps_f = [units.kelvin_to_fahrenheit(t) for t in temps_k]
        mu = max(temps_f)
        
        if len(temps_f) > 1:
            empirical_std = float(np.std(temps_f))
            sigma = empirical_std * np.sqrt(2.0)
            sigma = max(sigma, sigma_default * 0.5)
            sigma = float(np.clip(sigma, sigma_min, sigma_max))
        else:
            sigma = sigma_default
        
        logger.info(f"Fallback: μ = {mu:.2f}°F, σ = {sigma:.2f}°F (from spread)")
    
    # Step 3: Compute bracket probabilities using Normal CDF
    bracket_probs = []
    
    for bracket in brackets:
        # Convert bounds to z-scores
        z_lower = (bracket.lower_F - mu) / sigma
        z_upper = (bracket.upper_F - mu) / sigma
        
        # Compute CDF values
        cdf_lower = norm.cdf(z_lower)
        cdf_upper = norm.cdf(z_upper)
        
        # Probability is the difference
        prob = cdf_upper - cdf_lower
        prob = max(0.0, prob)
        
        bracket_probs.append(
            BracketProb(
                bracket=bracket,
                p_zeus=prob,
                p_mkt=None,
                sigma_z=sigma,
            )
        )
        
        logger.debug(
            f"Bracket [{bracket.lower_F}, {bracket.upper_F}): "
            f"z=({z_lower:.2f}, {z_upper:.2f}), p={prob:.4f}"
        )
    
    # Step 4: Normalize probabilities to sum = 1.0
    total = sum(bp.p_zeus for bp in bracket_probs)
    
    if total == 0:
        logger.warning("All probabilities zero, distributing evenly")
        uniform_prob = 1.0 / len(bracket_probs)
        for bp in bracket_probs:
            bp.p_zeus = uniform_prob
    else:
        normalization_factor = 1.0 / total
        for bp in bracket_probs:
            bp.p_zeus = bp.p_zeus * normalization_factor
    
    # Verify sum
    final_sum = sum(bp.p_zeus for bp in bracket_probs)
    logger.debug(f"Normalized probabilities: sum = {final_sum:.6f}")
    
    return bracket_probs

