# Calibration Application Order - Critical Requirements

**Date**: 2025-01-XX  
**Purpose**: Document the correct order for applying calibration

---

## ✅ CRITICAL: Calibration MUST be Applied BEFORE:

1. **Daily High (μ)** - Maximum of 24 hourly temperatures
2. **Spread (σ)** - Standard deviation of hourly temperatures  
3. **Bracket Probabilities** - All probability calculations

---

## Current Implementation Flow

### ❌ WRONG Order (Current):
```
Zeus Forecast → Compute Daily High → Compute Spread → Compute Probabilities
```

### ✅ CORRECT Order (With Calibration):
```
Zeus Forecast 
  ↓
Apply Calibration to ALL hourly points (timeseries)
  ↓
Compute Daily High (from calibrated temps)
  ↓
Compute Spread (from calibrated temps)
  ↓
Compute Bracket Probabilities (using calibrated μ and σ)
```

---

## Implementation Requirements

### Step 1: Apply Calibration to Full Timeseries

**Location**: `agents/prob_mapper.py` - `_compute_daily_high_mean()`

**Before** computing daily high, apply calibration to ALL hourly points:

```python
def _compute_daily_high_mean(
    self, 
    forecast: ZeusForecast,
    station_code: str = None,
    feature_toggles: Optional[FeatureToggles] = None,
) -> float:
    # Extract temperatures and timestamps
    temps_k = [point.temp_K for point in forecast.timeseries]
    timestamps = [point.time_utc for point in forecast.timeseries]
    
    # ✅ APPLY CALIBRATION FIRST (if enabled)
    if feature_toggles and feature_toggles.station_calibration:
        if station_code:
            temps_k = self.calibration.apply_to_forecast_timeseries(
                temps_k, timestamps, station_code
            )
    
    # Convert to Fahrenheit
    temps_f = [units.kelvin_to_fahrenheit(t) for t in temps_k]
    
    # ✅ THEN compute daily high from calibrated temps
    mu = max(temps_f)
    
    return mu
```

### Step 2: Use Calibrated Temperatures for Spread (σ)

**Location**: `agents/prob_mapper.py` - `_estimate_sigma()`

**Must use the SAME calibrated temperatures** that were used for daily high:

```python
def _estimate_sigma(
    self,
    forecast: ZeusForecast,
    mu: float,  # This is already from calibrated temps
    station_code: str = None,
    feature_toggles: Optional[FeatureToggles] = None,
) -> float:
    # ✅ Use SAME calibrated temperatures as daily high
    # Extract and apply calibration (same as daily high)
    temps_k = [point.temp_K for point in forecast.timeseries]
    timestamps = [point.time_utc for point in forecast.timeseries]
    
    if feature_toggles and feature_toggles.station_calibration:
        if station_code:
            temps_k = self.calibration.apply_to_forecast_timeseries(
                temps_k, timestamps, station_code
            )
    
    temps_f = [units.kelvin_to_fahrenheit(t) for t in temps_k]
    
    # ✅ Compute spread from calibrated temps
    empirical_std = float(np.std(temps_f))
    sigma = empirical_std * np.sqrt(2.0)
    
    return sigma
```

### Step 3: Use Calibrated μ and σ for Probabilities

**Location**: `agents/prob_mapper.py` - `map_daily_high()`

Both μ and σ are already from calibrated temperatures, so probabilities are automatically correct:

```python
def map_daily_high(...):
    # μ is from calibrated temps
    mu = self._compute_daily_high_mean(...)
    
    # σ is from calibrated temps
    sigma = self._estimate_sigma(forecast, mu, ...)
    
    # ✅ Probabilities use calibrated μ and σ
    for bracket in brackets:
        prob = norm.cdf((bracket.upper_F - mu) / sigma) - ...
```

---

## Key Points

1. **Calibration is applied ONCE** to the full timeseries
2. **Both μ and σ** use the SAME calibrated temperatures
3. **All downstream calculations** (probabilities, edges, etc.) use calibrated values
4. **No recalculation needed** - calibration happens at the source

---

## Verification Checklist

- [ ] Calibration applied to timeseries BEFORE computing daily high
- [ ] Calibration applied to timeseries BEFORE computing spread
- [ ] Same calibrated temperatures used for both μ and σ
- [ ] Bracket probabilities use calibrated μ and σ
- [ ] No raw temperatures used after calibration is applied

---

**Status**: ✅ Implementation plan updated to ensure correct order


