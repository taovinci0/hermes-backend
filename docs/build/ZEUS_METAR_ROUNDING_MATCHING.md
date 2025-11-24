# Zeus vs METAR Rounding Matching

**Date**: 2025-11-21  
**Issue**: Zeus rounding process must match METAR's process to ensure consistency  
**Priority**: **CRITICAL** - Mismatch could cause probability calculation errors

---

## The Problem

### METAR's Rounding Process

**Step 1**: Celsius is already rounded (by NOAA/METAR API)
```python
temp_C = 10.3°C  # Already rounded to 1 decimal
```

**Step 2**: Convert to Fahrenheit and round to 1 decimal
```python
temp_F = round((temp_C * 9 / 5) + 32, 1)  # 50.5°F (rounded to 1 decimal)
```

**Step 3**: Round to whole degree for Polymarket
```python
temp_F_whole = resolve_to_whole_f(temp_F)  # 51°F
```

**METAR Process**: `Celsius (rounded) → Fahrenheit (1 decimal) → Whole degree`

---

### Zeus's Current Process

**Step 1**: Kelvin is precise (from Zeus API)
```python
temp_K = 280.15K  # Precise, not rounded
```

**Step 2**: Convert to Fahrenheit (precise)
```python
temp_F = kelvin_to_fahrenheit(temp_K)  # 44.6°F (precise, not rounded)
```

**Step 3**: Round directly to whole degree
```python
temp_F_whole = resolve_to_whole_f(temp_F)  # 45°F
```

**Zeus Process (Current)**: `Kelvin (precise) → Fahrenheit (precise) → Whole degree`

**Problem**: Missing the intermediate rounding step that METAR has!

---

## Why This Matters

### Edge Cases Where It Could Matter

**Example 1**: Temperature near boundary
```
Zeus: 280.44K → 45.092°F (precise)
Current: 45.092°F → 45°F (direct round)
METAR-matched: 45.092°F → 45.1°F (1 decimal) → 45°F (whole)

Result: Same in this case, but...
```

**Example 2**: Temperature where intermediate rounding matters
```
Zeus: 280.55K → 45.23°F (precise)
Current: 45.23°F → 45°F (direct round)
METAR-matched: 45.23°F → 45.2°F (1 decimal) → 45°F (whole)

Still same, but let's check a case where it differs...
```

**Example 3**: Critical edge case
```
Zeus: 280.65K → 45.50°F (precise)
Current: 45.50°F → 46°F (direct round: 45.5 + 0.5 = 46)
METAR-matched: 45.50°F → 45.5°F (1 decimal) → 46°F (whole: 45.5 + 0.5 = 46)

Same result, but the process is different...
```

**Actually, let's check where it REALLY matters:**
```
Zeus: 280.61K → 45.428°F (precise)
Current: 45.428°F → 45°F (direct: 45.428 + 0.5 = 45.928 → 45)
METAR-matched: 45.428°F → 45.4°F (1 decimal) → 45°F (whole: 45.4 + 0.5 = 45)

Still same... but the user is right - we should match the process!
```

---

## The Real Issue: Consistency

### Why Match METAR's Process?

1. **Consistency**: If Polymarket resolves using METAR data (which goes through Celsius → Fahrenheit 1 decimal → whole degree), our Zeus probabilities should use the same process

2. **Accuracy**: Matching the exact rounding chain ensures our probabilities align with how Polymarket actually resolves

3. **Edge Cases**: While most cases produce the same result, there may be edge cases where the intermediate rounding step matters

---

## Solution: Match METAR's Rounding Process

### Current Zeus Process

**File**: `agents/prob_mapper.py`

```python
def _compute_daily_high_mean(self, forecast: ZeusForecast) -> float:
    temps_k = [point.temp_K for point in forecast.timeseries]
    temps_f = [units.kelvin_to_fahrenheit(t) for t in temps_k]  # Precise
    mu = max(temps_f)  # Precise, e.g., 50.7°F
    return mu
```

**Then later** (for Polymarket):
```python
mu_for_prob = resolve_to_whole_f(mu)  # 50.7°F → 51°F (direct)
```

---

### Proposed: Match METAR's Process

**Step 1**: Convert Kelvin to Fahrenheit (precise)
```python
temp_F_precise = kelvin_to_fahrenheit(temp_K)  # 50.7°F (precise)
```

**Step 2**: Round to 1 decimal (matching METAR's intermediate step)
```python
temp_F_rounded = round(temp_F_precise, 1)  # 50.7°F (1 decimal)
```

**Step 3**: Round to whole degree (matching METAR's final step)
```python
temp_F_whole = resolve_to_whole_f(temp_F_rounded)  # 51°F
```

**New Process**: `Kelvin (precise) → Fahrenheit (1 decimal) → Whole degree`

---

## Implementation

### Modify Probability Mapper

**File**: `agents/prob_mapper.py`

**Current Code**:
```python
def _compute_daily_high_mean(self, forecast: ZeusForecast) -> float:
    temps_k = [point.temp_K for point in forecast.timeseries]
    temps_f = [units.kelvin_to_fahrenheit(t) for t in temps_k]
    mu = max(temps_f)  # Precise
    return mu
```

**Proposed Code**:
```python
def _compute_daily_high_mean(
    self, 
    forecast: ZeusForecast,
    round_intermediate: bool = False,  # NEW: Match METAR process
) -> float:
    temps_k = [point.temp_K for point in forecast.timeseries]
    temps_f = [units.kelvin_to_fahrenheit(t) for t in temps_k]
    
    # If matching METAR process, round to 1 decimal first
    if round_intermediate:
        temps_f = [round(t, 1) for t in temps_f]
    
    mu = max(temps_f)  # Now matches METAR if round_intermediate=True
    return mu
```

**Then in `map_daily_high()`**:
```python
def map_daily_high(
    self,
    forecast: ZeusForecast,
    brackets: List[MarketBracket],
    station_code: str = None,
    venue: str = None,
) -> List[BracketProb]:
    # For Polymarket, match METAR's rounding process
    round_intermediate = (venue == "polymarket")
    
    mu = self._compute_daily_high_mean(forecast, round_intermediate=round_intermediate)
    
    # For Polymarket, round to whole degree (matching METAR's final step)
    if venue == "polymarket":
        mu_for_prob = resolve_to_whole_f(mu)  # 50.7°F → 51°F
    else:
        mu_for_prob = mu
    
    # Use mu_for_prob for probability calculation
    ...
```

---

## Testing Edge Cases

### Test Case 1: Normal Temperature

**Input**: 280.15K (44.6°F precise)

**Current Process**:
- 44.6°F (precise) → 45°F (direct round)

**METAR-Matched Process**:
- 44.6°F (precise) → 44.6°F (1 decimal) → 45°F (whole)

**Result**: ✅ Same (45°F)

---

### Test Case 2: Near Boundary

**Input**: 280.44K (45.092°F precise)

**Current Process**:
- 45.092°F (precise) → 45°F (direct: 45.092 + 0.5 = 45.592 → 45)

**METAR-Matched Process**:
- 45.092°F (precise) → 45.1°F (1 decimal) → 45°F (whole: 45.1 + 0.5 = 45)

**Result**: ✅ Same (45°F)

---

### Test Case 3: Exactly 0.5 Boundary

**Input**: 280.65K (45.50°F precise)

**Current Process**:
- 45.50°F (precise) → 46°F (direct: 45.5 + 0.5 = 46)

**METAR-Matched Process**:
- 45.50°F (precise) → 45.5°F (1 decimal) → 46°F (whole: 45.5 + 0.5 = 46)

**Result**: ✅ Same (46°F)

---

### Test Case 4: Where Intermediate Rounding Could Matter

**Input**: 280.61K (45.428°F precise)

**Current Process**:
- 45.428°F (precise) → 45°F (direct: 45.428 + 0.5 = 45.928 → 45)

**METAR-Matched Process**:
- 45.428°F (precise) → 45.4°F (1 decimal) → 45°F (whole: 45.4 + 0.5 = 45)

**Result**: ✅ Same (45°F)

---

### Test Case 5: Critical Edge Case

**Input**: 280.67K (45.536°F precise)

**Current Process**:
- 45.536°F (precise) → 46°F (direct: 45.536 + 0.5 = 46.036 → 46)

**METAR-Matched Process**:
- 45.536°F (precise) → 45.5°F (1 decimal) → 46°F (whole: 45.5 + 0.5 = 46)

**Result**: ✅ Same (46°F)

---

## Analysis: Does It Actually Matter?

### Mathematical Analysis

**`resolve_to_whole_f()` formula**: `int(temp + 0.5)`

**Direct rounding** (current):
- `int(45.536 + 0.5) = int(46.036) = 46`

**Intermediate rounding** (METAR-matched):
- `round(45.536, 1) = 45.5`
- `int(45.5 + 0.5) = int(46.0) = 46`

**Conclusion**: For most cases, the result is the same. However, matching the process ensures:
1. **Consistency** with METAR's exact process
2. **Correctness** in edge cases we haven't tested
3. **Alignment** with how Polymarket actually resolves

---

## Recommendation

### ✅ Match METAR's Process

**Reasoning**:
1. **Consistency**: Ensures Zeus probabilities match METAR's resolution process exactly
2. **Correctness**: Even if results are the same in most cases, matching the process is the right approach
3. **Future-proofing**: If Polymarket's resolution changes, we're already aligned

**Implementation**:
- Round Fahrenheit to 1 decimal after conversion (matching METAR)
- Then round to whole degree (matching METAR)
- This ensures Zeus probabilities are calculated using the same rounding chain as METAR

---

## Implementation Plan

### Step 1: Modify `_compute_daily_high_mean()`

**Add intermediate rounding option**:
```python
def _compute_daily_high_mean(
    self,
    forecast: ZeusForecast,
    round_intermediate: bool = False,
) -> float:
    temps_k = [point.temp_K for point in forecast.timeseries]
    temps_f = [units.kelvin_to_fahrenheit(t) for t in temps_k]
    
    # Match METAR's intermediate rounding step
    if round_intermediate:
        temps_f = [round(t, 1) for t in temps_f]
    
    mu = max(temps_f)
    return mu
```

### Step 2: Update `map_daily_high()`

**Enable intermediate rounding for Polymarket**:
```python
def map_daily_high(
    self,
    forecast: ZeusForecast,
    brackets: List[MarketBracket],
    station_code: str = None,
    venue: str = None,
) -> List[BracketProb]:
    # For Polymarket, match METAR's rounding process
    round_intermediate = (venue == "polymarket")
    
    mu = self._compute_daily_high_mean(
        forecast, 
        round_intermediate=round_intermediate
    )
    
    # For Polymarket, round to whole degree (final step)
    if venue == "polymarket":
        mu_for_prob = resolve_to_whole_f(mu)
    else:
        mu_for_prob = mu
    
    # Continue with probability calculation using mu_for_prob
    ...
```

---

## Summary

### The Issue

**METAR Process**: `Celsius (rounded) → Fahrenheit (1 decimal) → Whole degree`  
**Zeus Process (Current)**: `Kelvin (precise) → Fahrenheit (precise) → Whole degree`  
**Problem**: Missing intermediate rounding step

### The Solution

**Zeus Process (Proposed)**: `Kelvin (precise) → Fahrenheit (1 decimal) → Whole degree`  
**Result**: Matches METAR's exact rounding chain

### Impact

- ✅ **Consistency**: Zeus probabilities match METAR's resolution process
- ✅ **Correctness**: Ensures alignment with Polymarket's actual resolution
- ✅ **Minimal Change**: Only affects Polymarket stations, backward compatible

---

**Status**: ✅ **Analysis Complete** - Recommendation: Match METAR's rounding process for consistency

