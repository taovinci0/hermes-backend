"""Spread Model - Original Stage 3 probability calculation.

Uses empirical spread of Zeus hourly forecasts to estimate uncertainty.

Method:
- μ (mean) = max(hourly temps)
- σ (uncertainty) = std_dev(hourly temps) × √2
- P(bracket) = Φ((b-μ)/σ) - Φ((a-μ)/σ)
"""

from typing import List
import numpy as np
from scipy.stats import norm

from core.types import ZeusForecast, MarketBracket, BracketProb
from core.logger import logger
from core import units


def compute_probabilities(
    forecast: ZeusForecast,
    brackets: List[MarketBracket],
    sigma_default: float = 2.0,
    sigma_min: float = 0.5,
    sigma_max: float = 10.0,
) -> List[BracketProb]:
    """Compute bracket probabilities using hourly spread model.
    
    This is the original Stage 3 implementation that uses:
    - Daily high mean μ = max(hourly temps)
    - Uncertainty σ = empirical_std × √2
    
    Args:
        forecast: Zeus hourly temperature forecast
        brackets: List of market brackets
        sigma_default: Default uncertainty in °F
        sigma_min: Minimum allowed σ
        sigma_max: Maximum allowed σ
    
    Returns:
        List of BracketProb with computed probabilities
    """
    if not forecast.timeseries:
        raise ValueError("Forecast has no timeseries data")
    
    if not brackets:
        raise ValueError("No brackets provided")
    
    logger.debug(f"Using SPREAD model for {forecast.station_code}")
    
    # Step 1: Compute daily high mean μ
    temps_k = [point.temp_K for point in forecast.timeseries]
    temps_f = [units.kelvin_to_fahrenheit(t) for t in temps_k]
    mu = max(temps_f)
    
    logger.debug(f"Computed μ = {mu:.2f}°F from {len(temps_f)} hourly forecasts")
    
    # Step 2: Estimate uncertainty σ from spread
    if len(forecast.timeseries) > 1:
        # Use std dev of hourly forecasts
        empirical_std = float(np.std(temps_f))
        
        # Scale by √2 since daily high has higher variance
        sigma = empirical_std * np.sqrt(2.0)
        
        # Add minimum baseline uncertainty
        sigma = max(sigma, sigma_default * 0.5)
        
        # Clamp to reasonable range
        sigma = float(np.clip(sigma, sigma_min, sigma_max))
        
        logger.debug(
            f"Estimated σ from spread: empirical={empirical_std:.2f}°F, "
            f"scaled={sigma:.2f}°F"
        )
    else:
        # Single point - use default
        sigma = sigma_default
        logger.debug(f"Single forecast point, using default σ = {sigma:.2f}°F")
    
    logger.info(f"Daily high distribution: μ = {mu:.2f}°F, σ = {sigma:.2f}°F")
    
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
        prob = max(0.0, prob)  # Ensure non-negative
        
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
        # Distribute evenly if all zero
        logger.warning("All probabilities zero, distributing evenly")
        uniform_prob = 1.0 / len(bracket_probs)
        for bp in bracket_probs:
            bp.p_zeus = uniform_prob
    else:
        # Normalize
        normalization_factor = 1.0 / total
        for bp in bracket_probs:
            bp.p_zeus = bp.p_zeus * normalization_factor
    
    # Verify sum
    final_sum = sum(bp.p_zeus for bp in bracket_probs)
    logger.debug(f"Normalized probabilities: sum = {final_sum:.6f}")
    
    return bracket_probs

