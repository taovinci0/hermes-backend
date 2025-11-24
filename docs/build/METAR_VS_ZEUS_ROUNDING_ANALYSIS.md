# METAR vs Zeus Rounding Analysis

**Date**: 2025-11-21  
**Purpose**: Clarify rounding requirements for METAR vs Zeus data for Polymarket

---

## Key Insight

**METAR**: Celsius is already rounded in the data → Only need to round Fahrenheit **once**  
**Zeus**: Raw temperature data → Need to round Fahrenheit **once** for Polymarket (this is the "double rounding" adjustment)

---

## METAR Data Flow

### Current METAR Processing

**File**: `venues/metar/metar_service.py` (lines 174-198)

**Step 1: Get Temperature from API**
```python
# Get temperature in Celsius
temp_C = obs_data.get("temp")  # e.g., 10.3°C (already rounded to 1 decimal by NOAA)
```

**Step 2: Convert to Fahrenheit**
```python
# Convert to Fahrenheit
temp_F = round((temp_C * 9 / 5) + 32, 1)  # e.g., 50.5°F (rounded to 1 decimal)
```

**Step 3: Store Observation**
```python
return MetarObservation(
    station_code=station,
    time=time_utc,
    temp_C=round(temp_C, 1),  # Already rounded: 10.3°C
    temp_F=temp_F,  # 50.5°F (1 decimal)
    ...
)
```

**Key Point**: 
- ✅ Celsius is **already rounded** to 1 decimal by NOAA/METAR API
- ✅ Fahrenheit is rounded to 1 decimal during conversion
- ✅ **No additional rounding needed** in our code

---

### METAR Daily High for Polymarket

**File**: `backend/api/services/metar_service.py` (line 117)

**Current Code**:
```python
daily_high = max(temps)  # e.g., 50.7°F (from METAR observations)
return round(daily_high, 1)  # Returns 50.7°F (1 decimal)
```

**For Polymarket Resolution**:
- METAR reports: 50.7°F (1 decimal)
- Polymarket needs: Whole degree (51°F)
- **Action**: Round **once** using `resolve_to_whole_f(50.7) = 51°F`

**Conclusion**: ✅ METAR only needs **single rounding** (Fahrenheit to whole degree)

---

## Zeus Data Flow

### Current Zeus Processing

**File**: `agents/zeus_forecast.py` (lines 205-219)

**Step 1: Get Temperature from API**
```python
temperatures = temp_data["data"]  # Raw Kelvin values from Zeus API
# e.g., [280.15, 280.45, 280.75, ...] (precise, not rounded)
```

**Step 2: Convert to Fahrenheit**
```python
# In prob_mapper.py, line 56:
temps_f = [units.kelvin_to_fahrenheit(t) for t in temps_k]
# e.g., [44.6, 45.1, 45.6, ...] (precise, not rounded)
```

**Step 3: Calculate Daily High**
```python
# In prob_mapper.py, line 59:
mu = max(temps_f)  # e.g., 50.7°F (raw, precise value)
```

**Key Point**:
- ✅ Zeus provides **raw, precise** temperatures (not rounded)
- ✅ We convert Kelvin → Fahrenheit (precise conversion)
- ✅ Daily high is **raw temperature** (e.g., 50.7°F)

---

### Zeus Daily High for Polymarket Probability Calculation

**Current Problem**:
- Zeus predicts: 50.7°F (raw)
- We calculate probabilities using: 50.7°F
- Polymarket resolves using: 51°F (rounded)

**Impact**:
- Probability calculated for bracket [50-51)°F based on 50.7°F
- But Polymarket will resolve to [51-52)°F (because 50.7°F rounds to 51°F)
- **Mismatch**: We're calculating probabilities for the wrong bracket!

**Solution**: Round Zeus daily high **once** before probability calculation

**For Polymarket**:
- Zeus raw: 50.7°F
- Round to whole: `resolve_to_whole_f(50.7) = 51°F`
- Use 51°F for probability calculation
- Probabilities now align with how Polymarket will resolve

**Conclusion**: ✅ Zeus needs **single rounding** (Fahrenheit to whole degree) for Polymarket

---

## Why It's Called "Double Rounding"

### The Confusion

**Terminology**: "Double rounding" refers to the **Polymarket resolution process**, not our code:

1. **NOAA/METAR**: Reports temperature (e.g., 50.7°F)
2. **NOAA rounds**: 50.7°F → 51°F (first rounding)
3. **Polymarket uses**: 51°F for bracket resolution (second "rounding" effect)

**But in our code**:
- We receive METAR data where Celsius is **already rounded**
- We receive Zeus data that is **raw**
- We need to round **once** in both cases to match Polymarket's resolution

---

## Implementation Requirements

### METAR: Single Rounding

**Where**: When getting daily high for Polymarket resolution

**Current**: 
```python
daily_high = max(temps)  # 50.7°F
return round(daily_high, 1)  # 50.7°F (1 decimal)
```

**For Polymarket**:
```python
daily_high = max(temps)  # 50.7°F
rounded_high = resolve_to_whole_f(daily_high)  # 51°F
return rounded_high
```

**File**: `backend/api/services/metar_service.py` - `get_daily_high()`

**Change**: Add optional parameter for venue
```python
def get_daily_high(
    self,
    station_code: str,
    event_day: Optional[date] = None,
    venue: str = None,  # NEW: "polymarket" or None
) -> Optional[float]:
    ...
    daily_high = max(temps)
    
    # For Polymarket, round to whole degree
    if venue == "polymarket":
        return resolve_to_whole_f(daily_high)
    else:
        return round(daily_high, 1)  # Keep 1 decimal for other uses
```

**Impact**: ✅ Minimal - only affects Polymarket resolution

---

### Zeus: Single Rounding for Probability Calculation

**Where**: In probability mapper, before calculating bracket probabilities

**Current**:
```python
def map_daily_high(self, forecast, brackets):
    mu = self._compute_daily_high_mean(forecast)  # 50.7°F (raw)
    # Calculate probabilities using mu = 50.7°F
    ...
```

**For Polymarket**:
```python
def map_daily_high(self, forecast, brackets, station_code=None, venue=None):
    mu = self._compute_daily_high_mean(forecast)  # 50.7°F (raw)
    
    # For Polymarket, round to whole degree before probability calculation
    if venue == "polymarket":
        mu_for_prob = resolve_to_whole_f(mu)  # 51°F
    else:
        mu_for_prob = mu  # Use raw for other venues
    
    # Calculate probabilities using mu_for_prob
    ...
```

**File**: `agents/prob_mapper.py` - `map_daily_high()`

**Impact**: ✅ Critical - ensures probabilities match Polymarket resolution

---

## Summary

### Rounding Requirements

| Data Source | Current State | Polymarket Requirement | Action Needed |
|-------------|---------------|------------------------|---------------|
| **METAR** | Celsius already rounded (1 decimal) → Fahrenheit (1 decimal) | Whole degree | Round Fahrenheit **once** to whole degree |
| **Zeus** | Raw temperature (precise) | Whole degree | Round Fahrenheit **once** to whole degree |

### Key Points

1. **METAR**: Celsius is already rounded → Only round Fahrenheit once
2. **Zeus**: Raw temperature → Round Fahrenheit once for Polymarket
3. **"Double Rounding"**: Refers to Polymarket's process (NOAA → Polymarket), not our code
4. **Our Code**: Both need **single rounding** to whole degree for Polymarket

### Implementation

**METAR**:
- Add venue parameter to `get_daily_high()`
- Round to whole degree if `venue == "polymarket"`

**Zeus**:
- Add venue parameter to `map_daily_high()`
- Round daily high to whole degree before probability calculation if `venue == "polymarket"`

---

## Code Changes Summary

### 1. METAR Service

**File**: `backend/api/services/metar_service.py`

**Change**: Add venue parameter, round for Polymarket
```python
def get_daily_high(
    self,
    station_code: str,
    event_day: Optional[date] = None,
    venue: str = None,  # NEW
) -> Optional[float]:
    ...
    daily_high = max(temps)
    
    if venue == "polymarket":
        from core.units import resolve_to_whole_f
        return resolve_to_whole_f(daily_high)  # Round to whole degree
    else:
        return round(daily_high, 1)  # Keep 1 decimal
```

### 2. Probability Mapper

**File**: `agents/prob_mapper.py`

**Change**: Round daily high for Polymarket before probability calculation
```python
def map_daily_high(
    self,
    forecast: ZeusForecast,
    brackets: List[MarketBracket],
    station_code: str = None,  # NEW
    venue: str = None,  # NEW
) -> List[BracketProb]:
    mu = self._compute_daily_high_mean(forecast)  # Raw: 50.7°F
    
    # For Polymarket, round to whole degree
    if venue == "polymarket":
        mu_for_prob = resolve_to_whole_f(mu)  # 51°F
    else:
        mu_for_prob = mu  # Use raw
    
    # Use mu_for_prob for probability calculation
    ...
```

---

**Status**: ✅ **Rounding Requirements Clarified** - Both need single rounding to whole degree for Polymarket

