# Rounding Chain: Backend & Frontend Implementation Plan

**Date**: 2025-11-21  
**Purpose**: Plan backend and frontend changes to match Polymarket's exact rounding chain  
**Priority**: **CRITICAL** - Affects probability accuracy and graph display

---

## Current Situation

### Data Sources

**METAR**:
- **Format**: Celsius (already rounded to 1 decimal by API)
- **Example**: `10.3°C` (from API)

**Zeus**:
- **Format**: Kelvin (precise, not rounded)
- **Example**: `280.15K` (precise)

### Polymarket's Resolution Process

**Polymarket Chain** (CORRECTED):
1. Celsius (from METAR/NOAA, may be decimal like `17.8°C`)
2. **Round Celsius to whole number** → `18°C`
3. Convert to Fahrenheit → `64.4°F` (precise calculation)
4. **Round Fahrenheit to whole number** → `64°F` (for bracket)

**Example**:
- `17.8°C` → round to `18°C` → convert to `64.4°F` → round to `64°F`

**Key Insight**: Polymarket goes through **Celsius → Round to whole → Fahrenheit → Round to whole**

---

## Current Implementation Issues

### Issue 1: Zeus Rounding Chain Doesn't Match

**Current Zeus Process**:
```
Kelvin (precise) → Fahrenheit (precise) → Round to whole
```

**Polymarket Process** (CORRECTED):
```
Celsius (decimal) → Round to whole → Fahrenheit → Round to whole
```

**Problem**: We skip the Celsius intermediate step and round, which could cause misalignment.

**Example**:
```
Zeus: 280.44K
Current: 280.44K → 45.122°F → 45°F
Polymarket-matched: 280.44K → 7.29°C → 7°C (round) → 44.6°F → 45°F (round)
```

**Impact**: The intermediate Celsius rounding step can affect the final result in edge cases.

---

### Issue 2: Graph Display

**Current Graph Display**:
- **METAR**: Shows `temp_F` (rounded to 1 decimal, e.g., `50.5°F`)
- **Zeus**: Shows precise Fahrenheit (e.g., `50.7°F`)

**Question**: Should graphs show:
- Raw values (current)?
- Rounded values (matching Polymarket)?
- Both?

---

## Backend Changes Required

### Change 1: Zeus Probability Calculation

**File**: `agents/prob_mapper.py`

**Current Code**:
```python
def _compute_daily_high_mean(self, forecast: ZeusForecast) -> float:
    temps_k = [point.temp_K for point in forecast.timeseries]
    temps_f = [units.kelvin_to_fahrenheit(t) for t in temps_k]  # Direct conversion
    mu = max(temps_f)  # Precise, e.g., 50.7°F
    return mu
```

**Proposed Code** (Match Polymarket's chain - CORRECTED):
```python
def _compute_daily_high_mean(
    self, 
    forecast: ZeusForecast,
    match_polymarket_chain: bool = False,  # NEW: Match Polymarket's rounding chain
) -> float:
    temps_k = [point.temp_K for point in forecast.timeseries]
    
    if match_polymarket_chain:
        # Match Polymarket: Kelvin → Celsius → Round to whole → Fahrenheit → Round to whole
        temps_f = []
        for temp_k in temps_k:
            # Step 1: Convert to Celsius
            temp_c = units.kelvin_to_celsius(temp_k)  # e.g., 7.29°C (precise)
            
            # Step 2: Round Celsius to whole number (matching Polymarket)
            temp_c_whole = round(temp_c)  # e.g., 7°C
            
            # Step 3: Convert to Fahrenheit
            temp_f_precise = units.celsius_to_fahrenheit(temp_c_whole)  # e.g., 44.6°F
            
            # Step 4: Round Fahrenheit to whole number (matching Polymarket)
            temp_f_whole = round(temp_f_precise)  # e.g., 45°F
            
            temps_f.append(temp_f_whole)
    else:
        # Current: Direct conversion
        temps_f = [units.kelvin_to_fahrenheit(t) for t in temps_k]
    
    mu = max(temps_f)  # e.g., 45°F (if matching) or 45.7°F (if not)
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
    # For Polymarket, match the exact rounding chain
    match_polymarket = (venue == "polymarket")
    
    mu = self._compute_daily_high_mean(
        forecast, 
        match_polymarket_chain=match_polymarket
    )
    
    # For Polymarket, mu is already rounded to whole degree (from matching chain)
    if venue == "polymarket":
        mu_for_prob = mu  # Already whole number (e.g., 45°F)
    else:
        mu_for_prob = mu
    
    # Continue with probability calculation...
```

---

### Change 2: METAR Daily High for Polymarket

**File**: `backend/api/services/metar_service.py`

**Current Code**:
```python
def get_daily_high(
    self,
    station_code: str,
    event_day: Optional[date] = None,
    use_cache: bool = True,
) -> Optional[float]:
    ...
    daily_high = max(temps)  # e.g., 50.5°F (1 decimal)
    return round(daily_high, 1)  # Returns 50.5°F
```

**Proposed Code** (Add venue parameter - CORRECTED):
```python
def get_daily_high(
    self,
    station_code: str,
    event_day: Optional[date] = None,
    use_cache: bool = True,
    venue: str = None,  # NEW: "polymarket" or None
) -> Optional[float]:
    ...
    # Get max temperature (currently in Fahrenheit, 1 decimal)
    daily_high_f = max(temps)  # e.g., 50.5°F (1 decimal)
    
    # For Polymarket, match the exact chain: Celsius → Round whole → Fahrenheit → Round whole
    if venue == "polymarket":
        # Convert back to Celsius (from stored Fahrenheit)
        # Note: This is approximate - ideally we'd store original Celsius
        # But for now, we'll round the Fahrenheit directly
        return round(daily_high_f)  # 50.5°F → 51°F (round to whole)
    else:
        return round(daily_high_f, 1)  # Keep 1 decimal for other uses
```

**Note**: Ideally, we should store original Celsius from METAR API and apply the full chain:
```python
# Better approach (if we store temp_C):
temp_C_whole = round(obs.temp_C)  # Round Celsius to whole
temp_F = (temp_C_whole * 9 / 5) + 32  # Convert
temp_F_whole = round(temp_F)  # Round Fahrenheit to whole
```

But since we already convert to Fahrenheit, we can round the Fahrenheit directly for Polymarket.

---

### Change 3: Graph Data - Should We Round for Display?

**Question**: Do graphs need rounded values, or can they show precise values?

**Current Behavior**:
- **METAR**: Shows `temp_F` (1 decimal, e.g., `50.5°F`)
- **Zeus**: Shows precise Fahrenheit (e.g., `50.7°F`)

**Options**:

**Option A: Show Raw Values (Current)**
- **Pros**: More precise, shows actual data
- **Cons**: Doesn't match Polymarket's resolution

**Option B: Show Rounded Values (Matching Polymarket)**
- **Pros**: Matches how Polymarket resolves
- **Cons**: Less precise, might hide forecast details

**Option C: Show Both**
- **Pros**: Best of both worlds
- **Cons**: More complex UI

**Recommendation**: **Option A** (show raw values) for graphs, but ensure backend calculations use rounded values for probability/edge calculations.

---

## Frontend Impact Analysis

### Current Graph Data

**API Endpoints Used**:
- `GET /api/snapshots/zeus` - Zeus forecast data
- `GET /api/metar/observations` - METAR observations
- `GET /api/compare/zeus-vs-metar` - Comparison data

**Current Data Structure**:

**Zeus Snapshot**:
```json
{
  "timeseries": [
    {
      "time_utc": "2025-11-24T00:00:00+00:00",
      "temp_K": 280.15
    }
  ]
}
```

**METAR Observation**:
```json
{
  "observation_time_utc": "2025-11-24T15:50:00+00:00",
  "temp_C": 10.3,
  "temp_F": 50.5
}
```

---

### Frontend Changes Needed

#### Change 1: Graph Display (Optional)

**Current**: Frontend converts Kelvin → Fahrenheit for display
```typescript
// Current: Direct conversion
const tempF = (tempK - 273.15) * 9/5 + 32;  // Precise
```

**Option**: Match Polymarket's chain (if desired)
```typescript
// Match Polymarket: Kelvin → Celsius → Round → Fahrenheit → Round
const tempC = tempK - 273.15;
const tempCRounded = Math.round(tempC * 10) / 10;  // Round to 1 decimal
const tempF = (tempCRounded * 9/5) + 32;
const tempFRounded = Math.round(tempF * 10) / 10;  // Round to 1 decimal
```

**Recommendation**: **Keep current** (show precise values on graph), but ensure backend uses rounded values for calculations.

---

#### Change 2: Daily High Display

**Current**: Shows precise or 1-decimal values

**For Polymarket**: Should show rounded whole degree

**API Response Enhancement**:
```json
{
  "zeus_prediction_f": 50.7,
  "zeus_prediction_rounded_f": 51,  // NEW: Rounded for Polymarket
  "metar_actual_f": 50.5,
  "metar_actual_rounded_f": 51,  // NEW: Rounded for Polymarket
  "winning_bracket": "51-52°F"
}
```

**Frontend Display**:
- Show rounded values when venue is Polymarket
- Show precise values for other venues or analysis

---

## Implementation Plan

### Phase 1: Backend - Zeus Rounding Chain (Priority: HIGH)

**File**: `agents/prob_mapper.py`

**Changes**:
1. Add `match_polymarket_chain` parameter to `_compute_daily_high_mean()`
2. Implement Celsius intermediate step when matching Polymarket
3. Round Celsius to 1 decimal, then Fahrenheit to 1 decimal
4. Update `map_daily_high()` to enable for Polymarket

**Time**: 2-3 hours

**Testing**:
- Compare results with/without matching
- Test edge cases where intermediate rounding matters
- Verify probabilities align with Polymarket resolution

---

### Phase 2: Backend - METAR Rounding (Priority: MEDIUM)

**File**: `backend/api/services/metar_service.py`

**Changes**:
1. Add `venue` parameter to `get_daily_high()`
2. Round to whole degree for Polymarket
3. Keep 1 decimal for other uses

**Time**: 1 hour

**Testing**:
- Verify daily high matches Polymarket resolution
- Ensure backward compatibility

---

### Phase 3: Backend - API Response Enhancement (Priority: MEDIUM)

**Files**: 
- `backend/api/services/metar_service.py` - `compare_zeus_vs_metar()`
- `backend/api/routes/compare.py`

**Changes**:
1. Add rounded values to comparison response
2. Include rounding chain information

**New Response Fields**:
```json
{
  "zeus_prediction_f": 50.7,
  "zeus_prediction_rounded_f": 51,  // NEW
  "metar_actual_f": 50.5,
  "metar_actual_rounded_f": 51,  // NEW
  "rounding_chain": {
    "zeus": "Kelvin → Celsius → Round → Fahrenheit → Round → Whole",
    "metar": "Celsius (rounded) → Fahrenheit → Round → Whole"
  }
}
```

**Time**: 1-2 hours

---

### Phase 4: Frontend - Graph Display (Priority: LOW)

**Decision Needed**: Show raw or rounded values?

**Option A: Keep Current (Recommended)**
- Show precise values on graphs
- More informative for analysis
- **No frontend changes needed**

**Option B: Show Rounded**
- Match Polymarket's resolution visually
- Less precise but more aligned
- **Requires frontend changes**

**Recommendation**: **Option A** - Keep graphs showing precise values, but ensure backend calculations use rounded values.

---

### Phase 5: Frontend - Daily High Display (Priority: MEDIUM)

**Changes**:
1. Display rounded values when venue is Polymarket
2. Show both rounded and precise (tooltip or secondary display)
3. Update accuracy card to use rounded values

**Time**: 2-3 hours

---

## Detailed Implementation

### Backend: Zeus Rounding Chain Matching

**File**: `agents/prob_mapper.py`

**Complete Implementation** (CORRECTED):
```python
def _compute_daily_high_mean(
    self, 
    forecast: ZeusForecast,
    match_polymarket_chain: bool = False,
) -> float:
    """Compute daily high mean, optionally matching Polymarket's rounding chain.
    
    Args:
        forecast: Zeus forecast
        match_polymarket_chain: If True, match Polymarket's exact process:
            Kelvin → Celsius → Round to whole → Fahrenheit → Round to whole
    
    Returns:
        Daily high in Fahrenheit (whole number if matching, precise if not)
    """
    if not forecast.timeseries:
        raise ValueError("Forecast has no timeseries data")
    
    temps_k = [point.temp_K for point in forecast.timeseries]
    
    if match_polymarket_chain:
        # Match Polymarket: Kelvin → Celsius → Round whole → Fahrenheit → Round whole
        temps_f = []
        for temp_k in temps_k:
            # Step 1: Convert to Celsius
            temp_c = units.kelvin_to_celsius(temp_k)  # e.g., 7.29°C
            
            # Step 2: Round Celsius to whole number (matching Polymarket)
            temp_c_whole = round(temp_c)  # e.g., 7°C
            
            # Step 3: Convert to Fahrenheit
            temp_f_precise = units.celsius_to_fahrenheit(temp_c_whole)  # e.g., 44.6°F
            
            # Step 4: Round Fahrenheit to whole number (matching Polymarket)
            temp_f_whole = round(temp_f_precise)  # e.g., 45°F
            
            temps_f.append(temp_f_whole)
            
        logger.debug(
            f"Applied Polymarket rounding chain: "
            f"Kelvin → Celsius (round whole) → Fahrenheit (round whole)"
        )
    else:
        # Current: Direct conversion
        temps_f = [units.kelvin_to_fahrenheit(t) for t in temps_k]
    
    mu = max(temps_f)
    
    logger.debug(
        f"Computed daily high μ = {mu:.1f}°F from {len(temps_f)} hourly forecasts "
        f"(match_polymarket={match_polymarket_chain})"
    )
    
    return mu
```

---

### Backend: Update map_daily_high()

```python
def map_daily_high(
    self,
    forecast: ZeusForecast,
    brackets: List[MarketBracket],
    station_code: str = None,
    venue: str = None,
) -> List[BracketProb]:
    ...
    
    # For Polymarket, match the exact rounding chain
    match_polymarket = (venue == "polymarket")
    
    mu = self._compute_daily_high_mean(
        forecast, 
        match_polymarket_chain=match_polymarket
    )
    
    # For Polymarket, mu is already rounded to whole degree (from matching chain)
    if venue == "polymarket":
        mu_for_prob = mu  # Already whole number (e.g., 45°F)
        logger.debug(
            f"Using Polymarket-rounded daily high: {mu_for_prob}°F "
            f"(for probability calculation)"
        )
    else:
        mu_for_prob = mu
    
    # Continue with probability calculation using mu_for_prob
    ...
```

---

### Backend: METAR Daily High Enhancement

**File**: `backend/api/services/metar_service.py`

```python
def get_daily_high(
    self,
    station_code: str,
    event_day: Optional[date] = None,
    use_cache: bool = True,
    venue: str = None,  # NEW
) -> Optional[float]:
    ...
    daily_high = max(temps)  # e.g., 50.5°F (1 decimal)
    
    # For Polymarket, round to whole degree (matching resolution)
    if venue == "polymarket":
        # Round Fahrenheit to whole number (matching Polymarket's process)
        rounded_high = round(daily_high)  # 50.5°F → 51°F
        logger.debug(
            f"Applied Polymarket rounding: {daily_high:.1f}°F → {rounded_high}°F"
        )
        return rounded_high
    else:
        return round(daily_high, 1)  # Keep 1 decimal
```

---

### Backend: Enhanced Comparison Response

**File**: `backend/api/services/metar_service.py` - `compare_zeus_vs_metar()`

```python
def compare_zeus_vs_metar(
    self,
    station_code: str,
    event_day: Optional[date] = None,
    venue: str = None,  # NEW
) -> Optional[Dict[str, Any]]:
    ...
    
    # Get rounded values for Polymarket
    if venue == "polymarket":
        # Round to whole numbers (matching Polymarket's process)
        zeus_rounded = round(zeus_high)  # e.g., 50.7°F → 51°F
        metar_rounded = round(metar_high)  # e.g., 50.5°F → 51°F
    else:
        zeus_rounded = None
        metar_rounded = None
    
    return {
        # Existing fields
        "zeus_prediction_f": round(zeus_high, 1),
        "metar_actual_f": round(metar_high, 1),
        "error_f": round(error_f, 1),
        
        # NEW: Rounded values for Polymarket
        "zeus_prediction_rounded_f": zeus_rounded,
        "metar_actual_rounded_f": metar_rounded,
        
        # NEW: Rounding chain info
        "rounding_chain": {
            "zeus": "Kelvin → Celsius → Round whole → Fahrenheit → Round whole" if venue == "polymarket" else "Kelvin → Fahrenheit",
            "metar": "Celsius → Round whole → Fahrenheit → Round whole" if venue == "polymarket" else "Celsius → Fahrenheit → Round(1 decimal)",
        } if venue == "polymarket" else None,
        
        # Existing fields...
    }
```

---

## Frontend Changes

### Change 1: Graph Display (Optional)

**Decision**: Keep showing precise values on graphs

**Rationale**:
- Graphs are for analysis/visualization
- Precise values show forecast details
- Backend calculations use rounded values (correct for trading)

**Action**: **No changes needed** (keep current behavior)

---

### Change 2: Daily High Accuracy Card

**Current Display**:
- Predicted High: `49.7°F`
- Actual High: `51.8°F`
- Rounded Prediction: `50°F`
- Winning Bracket: `51-52°F`

**Enhanced Display** (for Polymarket):
- Predicted High: `49.7°F` (raw) / `50°F` (rounded) ← Show both
- Actual High: `51.8°F` (raw) / `52°F` (rounded) ← Show both
- Rounded Prediction: `50°F` ✅
- Winning Bracket: `51-52°F` ✅
- Status: Correct/Incorrect (based on rounded values)

**API Changes Needed**:
- Add `zeus_prediction_rounded_f` and `metar_actual_rounded_f` to response
- Frontend can display both raw and rounded

**Frontend Code**:
```typescript
// Display both raw and rounded
<div>
  <span>Predicted: {zeus_prediction_f}°F</span>
  {zeus_prediction_rounded_f && (
    <span className="text-muted"> ({zeus_prediction_rounded_f}°F rounded)</span>
  )}
</div>
```

---

## Testing Strategy

### Test Case 1: Edge Case Where Intermediate Rounding Matters

**Input**: `280.44K`

**Current Process**:
- `280.44K → 45.122°F → 45°F` (direct round)

**Polymarket-Matched Process**:
- `280.44K → 7.29°C → 7°C (round) → 44.6°F → 45°F (round)`

**Result**: Same (45°F), but process matches Polymarket exactly

---

### Test Case 2: Temperature Near Boundary

**Input**: `280.65K`

**Current Process**:
- `280.65K → 45.50°F → 46°F` (direct round)

**Polymarket-Matched Process**:
- `280.65K → 7.50°C → 8°C (round) → 46.4°F → 46°F (round)`

**Result**: Same (46°F), process matches

---

### Test Case 3: Verify Probability Alignment

**Test**: Compare probabilities calculated with/without matching

**Expected**: Probabilities should align better with Polymarket resolution when matching is enabled

---

## Summary

### Polymarket's Actual Process (CORRECTED)

**Example**: `17.8°C → 18°C (round) → 64.4°F → 64°F (round)`

**Chain**: `Celsius → Round to whole → Fahrenheit → Round to whole`

### Backend Changes

1. **Zeus Probability Calculation**:
   - Convert Kelvin → Celsius
   - **Round Celsius to whole number** (e.g., `7.29°C → 7°C`)
   - Convert to Fahrenheit
   - **Round Fahrenheit to whole number** (e.g., `44.6°F → 45°F`)
   - Use whole number for probability calculation

2. **METAR Daily High**:
   - Add venue parameter
   - Round to whole number for Polymarket (e.g., `50.5°F → 51°F`)

3. **API Responses**:
   - Add rounded values to comparison endpoint
   - Include rounding chain information

### Frontend Changes

1. **Graphs**: **No changes** (keep showing precise values for analysis)
2. **Daily High Card**: Display both raw and rounded values (optional enhancement)

### Implementation Priority

1. **HIGH**: Backend Zeus rounding chain matching (Celsius → Round whole → Fahrenheit → Round whole)
2. **MEDIUM**: METAR rounding for Polymarket
3. **MEDIUM**: API response enhancements
4. **LOW**: Frontend display enhancements (optional)

---

**Status**: 📋 **Implementation Plan Complete** - Ready for staged implementation

