"""Probability mapper - converts Zeus forecasts to bracket probabilities.

Stage 3 implementation (original spread model).
Stage 7B enhancement (dual model system with configurable switching).
"""

from typing import List, Optional
import numpy as np
from scipy.stats import norm

from core.types import ZeusForecast, MarketBracket, BracketProb
from core.logger import logger
from core.config import config
from core import units
from core.feature_toggles import FeatureToggles
from core.station_calibration import StationCalibration

# Import probability models (Stage 7B)
from agents.prob_models import spread_model, bands_model


class ProbabilityMapper:
    """Maps Zeus temperature forecasts to market bracket probabilities."""

    def __init__(
        self,
        sigma_default: float = 2.0,
        sigma_min: float = 0.5,
        sigma_max: float = 10.0,
    ):
        """Initialize probability mapper.

        Args:
            sigma_default: Default uncertainty (std dev in °F) when Zeus bands unavailable
            sigma_min: Minimum allowed sigma (prevents division by zero)
            sigma_max: Maximum allowed sigma (prevents extreme distributions)
        """
        self.sigma_default = sigma_default
        self.sigma_min = sigma_min
        self.sigma_max = sigma_max
        self.calibration = StationCalibration()  # NEW: Station calibration system

    def _compute_daily_high_mean(self, forecast: ZeusForecast) -> float:
        """Compute daily high mean μ as max of hourly temps.

        Args:
            forecast: Zeus hourly temperature forecast

        Returns:
            Daily high temperature in °F
        """
        if not forecast.timeseries:
            raise ValueError("Forecast has no timeseries data")

        # Get all hourly temps in Kelvin
        temps_k = [point.temp_K for point in forecast.timeseries]

        # Convert to Fahrenheit
        temps_f = [units.kelvin_to_fahrenheit(t) for t in temps_k]

        # Daily high is the maximum
        mu = max(temps_f)

        logger.debug(
            f"Computed daily high μ = {mu:.2f}°F from {len(temps_f)} hourly forecasts"
        )

        return mu

    def _estimate_sigma(
        self,
        forecast: ZeusForecast,
        mu: float,
    ) -> float:
        """Estimate forecast uncertainty σ_Z.

        Uses multiple methods in order of preference:
        1. Zeus uncertainty bands if present (future enhancement)
        2. Empirical std dev from hourly forecast spread
        3. Default sigma

        Args:
            forecast: Zeus hourly temperature forecast
            mu: Daily high mean in °F

        Returns:
            Uncertainty (standard deviation) in °F
        """
        # Method 1: Zeus uncertainty bands (future enhancement)
        # TODO: Extract from Zeus API response when available
        # if hasattr(forecast, 'uncertainty_bands'):
        #     sigma = self._derive_sigma_from_bands(forecast.uncertainty_bands)
        #     return self._clamp_sigma(sigma)

        # Method 2: Empirical std dev from forecast spread
        if len(forecast.timeseries) > 1:
            temps_f = [
                units.kelvin_to_fahrenheit(p.temp_K) for p in forecast.timeseries
            ]
            
            # Use std dev of hourly forecasts as uncertainty proxy
            # Scale by sqrt(2) since daily high has higher variance
            empirical_std = float(np.std(temps_f))
            sigma = empirical_std * np.sqrt(2.0)
            
            # Add minimum baseline uncertainty
            sigma = max(sigma, self.sigma_default * 0.5)
            
            logger.debug(
                f"Estimated σ = {sigma:.2f}°F from empirical spread "
                f"(hourly std: {empirical_std:.2f}°F)"
            )
            
            return self._clamp_sigma(sigma)

        # Method 3: Default sigma
        logger.debug(f"Using default σ = {self.sigma_default}°F")
        return self.sigma_default

    def _clamp_sigma(self, sigma: float) -> float:
        """Clamp sigma to reasonable bounds.

        Args:
            sigma: Unclamped sigma value

        Returns:
            Sigma clamped to [sigma_min, sigma_max]
        """
        clamped = max(self.sigma_min, min(sigma, self.sigma_max))
        if clamped != sigma:
            logger.debug(f"Clamped σ from {sigma:.2f}°F to {clamped:.2f}°F")
        return clamped

    def _compute_bracket_probability(
        self,
        bracket: MarketBracket,
        mu: float,
        sigma: float,
    ) -> float:
        """Compute probability for a single bracket using normal CDF.

        For bracket [a, b), probability is:
        P(a ≤ T < b) = Φ((b-μ)/σ) - Φ((a-μ)/σ)

        Args:
            bracket: Market bracket with lower and upper bounds
            mu: Daily high mean in °F
            sigma: Forecast uncertainty in °F

        Returns:
            Probability (0-1) for this bracket
        """
        # Standardize bounds
        z_lower = (bracket.lower_F - mu) / sigma
        z_upper = (bracket.upper_F - mu) / sigma

        # Compute CDF values
        cdf_lower = norm.cdf(z_lower)
        cdf_upper = norm.cdf(z_upper)

        # Probability is the difference
        prob = cdf_upper - cdf_lower

        # Ensure non-negative (can be slightly negative due to floating point)
        prob = max(0.0, prob)

        logger.debug(
            f"Bracket [{bracket.lower_F}, {bracket.upper_F}): "
            f"z=({z_lower:.2f}, {z_upper:.2f}), "
            f"CDF=({cdf_lower:.4f}, {cdf_upper:.4f}), "
            f"p={prob:.4f}"
        )

        return prob

    def _normalize_probabilities(
        self,
        bracket_probs: List[BracketProb],
    ) -> List[BracketProb]:
        """Normalize probabilities to sum to 1.0.

        Args:
            bracket_probs: List of BracketProb with raw probabilities

        Returns:
            List of BracketProb with normalized probabilities
        """
        total = sum(bp.p_zeus for bp in bracket_probs)

        if total == 0:
            # Edge case: all probabilities are zero
            # Distribute evenly
            logger.warning("All probabilities zero, distributing evenly")
            uniform_prob = 1.0 / len(bracket_probs)
            for bp in bracket_probs:
                bp.p_zeus = uniform_prob
            return bracket_probs

        # Normalize
        normalization_factor = 1.0 / total
        for bp in bracket_probs:
            bp.p_zeus = bp.p_zeus * normalization_factor

        # Verify sum (for logging)
        final_sum = sum(bp.p_zeus for bp in bracket_probs)
        logger.debug(f"Normalized probabilities: sum = {final_sum:.6f}")

        return bracket_probs

    def _apply_calibration_to_forecast(
        self,
        forecast: ZeusForecast,
        station_code: str,
        feature_toggles: Optional[FeatureToggles] = None,
    ) -> ZeusForecast:
        """Apply calibration to forecast timeseries if enabled.
        
        Args:
            forecast: Original Zeus forecast
            station_code: Station code for calibration lookup
            feature_toggles: Feature toggle configuration
            
        Returns:
            Forecast with calibrated temperatures (or original if calibration disabled)
        """
        if not feature_toggles or not feature_toggles.station_calibration:
            return forecast
        
        if not station_code:
            return forecast
        
        if not self.calibration.has_calibration(station_code):
            logger.debug(f"No calibration available for {station_code}")
            return forecast
        
        # Apply calibration to timeseries
        temps_k = [point.temp_K for point in forecast.timeseries]
        timestamps = [point.time_utc for point in forecast.timeseries]
        
        calibrated_temps_k = self.calibration.apply_to_forecast_timeseries(
            temps_k, timestamps, station_code
        )
        
        # Create new forecast with calibrated temperatures
        from copy import deepcopy
        calibrated_forecast = deepcopy(forecast)
        
        # Update temperatures in timeseries
        for i, point in enumerate(calibrated_forecast.timeseries):
            point.temp_K = calibrated_temps_k[i]
        
        logger.debug(
            f"Applied station calibration to {station_code} forecast "
            f"({len(calibrated_temps_k)} points)"
        )
        
        return calibrated_forecast
    
    def map_daily_high(
        self,
        forecast: ZeusForecast,
        brackets: List[MarketBracket],
        station_code: Optional[str] = None,
        feature_toggles: Optional[FeatureToggles] = None,
    ) -> List[BracketProb]:
        """Convert Zeus forecast into daily-high distribution over brackets.

        Stage 7B: Routes to appropriate model based on config.model_mode:
        - "spread" (default): Uses hourly spread × √2 (Stage 3 original)
        - "bands": Uses Zeus likely/possible confidence intervals (Stage 7B)

        **CRITICAL**: Applies station calibration BEFORE computing probabilities
        if feature toggle is enabled.

        Computes:
        1. Apply calibration to timeseries (if enabled)
        2. Daily high mean μ as max of hourly temps (K→°F)
        3. Uncertainty σ_Z from Zeus bands or empirical spread
        4. For each bracket [a,b), p_zeus = Φ((b-μ)/σ) - Φ((a-μ)/σ)
        5. Normalize probabilities to sum ≈ 1.0

        Args:
            forecast: Zeus hourly temperature forecast
            brackets: List of market brackets to compute probabilities for
            station_code: Station code for calibration lookup
            feature_toggles: Feature toggle configuration (if None, uses defaults)

        Returns:
            List of BracketProb with Zeus-derived probabilities

        Raises:
            ValueError: If forecast or brackets are invalid
        """
        if not forecast.timeseries:
            raise ValueError("Forecast has no timeseries data")

        if not brackets:
            raise ValueError("No brackets provided")
        
        if feature_toggles is None:
            feature_toggles = FeatureToggles()  # Default: all off

        logger.info(
            f"Mapping forecast for {forecast.station_code} "
            f"({len(forecast.timeseries)} points) "
            f"to {len(brackets)} brackets"
        )

        # ✅ STEP 1: Apply calibration to forecast if enabled
        calibrated_forecast = self._apply_calibration_to_forecast(
            forecast,
            station_code or forecast.station_code,
            feature_toggles,
        )
        
        if calibrated_forecast is not forecast:
            logger.info(
                f"📊 Station calibration applied to {station_code or forecast.station_code}"
            )

        # Stage 7B: Route to appropriate model
        model_mode = config.model_mode
        
        if model_mode == "bands":
            logger.info("🧠 Using Zeus-Bands model (Stage 7B)")
            bracket_probs = bands_model.compute_probabilities(
                calibrated_forecast,  # Use calibrated forecast
                brackets,
                sigma_default=self.sigma_default,
                sigma_min=self.sigma_min,
                sigma_max=self.sigma_max,
            )
        else:
            # Default: spread model (Stage 3 original)
            logger.info("🧠 Using Spread model (default)")
            bracket_probs = spread_model.compute_probabilities(
                calibrated_forecast,  # Use calibrated forecast
                brackets,
                sigma_default=self.sigma_default,
                sigma_min=self.sigma_min,
                sigma_max=self.sigma_max,
            )
        
        # Log summary
        total_prob = sum(bp.p_zeus for bp in bracket_probs)
        max_prob_bracket = max(bracket_probs, key=lambda bp: bp.p_zeus)

        logger.info(
            f"Mapped probabilities: sum = {total_prob:.6f}, "
            f"peak = [{max_prob_bracket.bracket.lower_F}, "
            f"{max_prob_bracket.bracket.upper_F}) "
            f"with p = {max_prob_bracket.p_zeus:.4f}"
        )

        return bracket_probs

