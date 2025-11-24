# Venue & Station Rules: Structure Impact Analysis

**Date**: 2025-11-21  
**Focus**: How adding venue/station rules and double rounding affects current code structure  
**Priority**: Starting with Polymarket double rounding

---

## Current Structure

### Probability Mapping Flow

**File**: `agents/prob_mapper.py`

**Current Flow**:
```
1. Get Zeus forecast (hourly temperatures)
2. Calculate daily high mean (μ) = max of hourly temps
3. Estimate uncertainty (σ) from spread or bands
4. For each bracket [a, b):
   - Calculate probability using normal distribution
   - p = Φ((b-μ)/σ) - Φ((a-μ)/σ)
5. Return list of BracketProb objects
```

**Key Function**: `map_daily_high(forecast, brackets) -> List[BracketProb]`

**Current Code**:
```python
def map_daily_high(self, forecast: ZeusForecast, brackets: List[MarketBracket]) -> List[BracketProb]:
    # 1. Compute daily high mean
    mu = self._compute_daily_high_mean(forecast)  # Returns float (e.g., 51.5°F)
    
    # 2. Estimate uncertainty
    sigma = self._estimate_sigma(forecast, mu)
    
    # 3. For each bracket, calculate probability
    probs = []
    for bracket in brackets:
        p = self._bracket_probability(mu, sigma, bracket.lower_F, bracket.upper_F)
        probs.append(BracketProb(
            bracket=bracket,
            p_zeus=p,
            p_mkt=None,  # Added later
            sigma_z=sigma,
        ))
    
    return probs
```

**Current Rounding**: None - we use raw temperature (51.5°F) for probability calculation

---

### Edge Calculation Flow

**File**: `agents/edge_and_sizing.py`

**Current Flow**:
```
1. Get BracketProb (with p_zeus)
2. Get market price (p_mkt)
3. Calculate edge = (p_zeus - p_mkt) - fees - slippage
4. If edge > threshold, size position with Kelly
```

**Current Code**:
```python
def compute_edge(self, p_zeus: float, p_mkt: float) -> float:
    edge = (p_zeus - p_mkt) - fee_decimal - slip_decimal
    return edge
```

**No venue/station awareness**: Edge calculation is generic, no station-specific logic

---

## Proposed Changes: Double Rounding for Polymarket

### What is Double Rounding?

**Polymarket Resolution Process**:
1. NOAA reports temperature (e.g., 50.7°F)
2. NOAA rounds to whole degree: `resolve_to_whole_f(50.7) = 51°F` (First Rounding)
3. Polymarket uses this rounded value for bracket resolution
4. Bracket determined by rounded value: 51°F → [51-52)°F

**Impact on Probability**:
- Raw temperature: 50.7°F
- After rounding: 51°F
- Bracket: [51-52)°F (not [50-51)°F)

**Current Problem**: We calculate probabilities using raw temperature (50.7°F), but Polymarket resolves using rounded temperature (51°F)

---

## Structure Impact Analysis

### Impact 1: Probability Mapper Needs Venue Awareness

**Current**: `ProbabilityMapper` is venue-agnostic

**Change Needed**: 
- Add venue/station context to probability calculation
- Apply double rounding for Polymarket before calculating probabilities

**File**: `agents/prob_mapper.py`

**Current Signature**:
```python
def map_daily_high(
    self,
    forecast: ZeusForecast,
    brackets: List[MarketBracket],
) -> List[BracketProb]:
```

**Proposed Signature**:
```python
def map_daily_high(
    self,
    forecast: ZeusForecast,
    brackets: List[MarketBracket],
    station_code: str = None,  # NEW: For venue/station rules
    venue: str = None,  # NEW: "polymarket" or "kalshi"
) -> List[BracketProb]:
```

**Change in Logic**:
```python
def map_daily_high(self, forecast, brackets, station_code=None, venue=None):
    # 1. Compute daily high mean (unchanged)
    mu = self._compute_daily_high_mean(forecast)  # e.g., 50.7°F
    
    # 2. NEW: Apply venue-specific rounding
    if venue == "polymarket":
        # Polymarket uses double rounding (NOAA → Polymarket)
        mu_rounded = resolve_to_whole_f(mu)  # 50.7°F → 51°F
        # Use rounded value for probability calculation
        mu_for_prob = mu_rounded
    else:
        # Other venues use raw temperature
        mu_for_prob = mu
    
    # 3. Estimate uncertainty (unchanged)
    sigma = self._estimate_sigma(forecast, mu)
    
    # 4. Calculate probabilities using mu_for_prob (not mu)
    probs = []
    for bracket in brackets:
        p = self._bracket_probability(mu_for_prob, sigma, bracket.lower_F, bracket.upper_F)
        probs.append(BracketProb(...))
    
    return probs
```

**Impact**: 
- ✅ Minimal change to existing logic
- ✅ Backward compatible (venue parameter optional)
- ✅ Only affects Polymarket stations

---

### Impact 2: Need Station/Venue Rules Registry

**Current**: No centralized rules system

**Change Needed**: Create rules registry to look up station/venue properties

**New File**: `core/polymarket_station_rules.py`

**Structure**:
```python
@dataclass
class StationRule:
    station_code: str
    venue: str  # "polymarket" or "kalshi"
    uses_double_rounding: bool
    # Future: metar_update_times, etc.

class StationRulesRegistry:
    def get_rule(self, station_code: str) -> StationRule | None:
        ...
```

**Usage**:
```python
# In prob_mapper.py
rules = StationRulesRegistry()
rule = rules.get_rule(station_code)
if rule and rule.uses_double_rounding:
    mu_for_prob = resolve_to_whole_f(mu)
```

**Impact**:
- ✅ New file, doesn't modify existing code
- ✅ Extensible for future rules (METAR times, etc.)
- ✅ Can be loaded from config file

---

### Impact 3: Dynamic Engine Needs to Pass Context

**Current**: `DynamicEngine` doesn't pass station/venue to probability mapper

**File**: `agents/dynamic_trader/dynamic_engine.py`

**Current Code** (line ~209):
```python
probs = self.prob_mapper.map_daily_high(forecast, brackets)
```

**Proposed Change**:
```python
# Get venue from station
venue = "polymarket" if "polymarket" in station.venue_hint.lower() else "kalshi"

probs = self.prob_mapper.map_daily_high(
    forecast=forecast,
    brackets=brackets,
    station_code=station.station_code,  # NEW
    venue=venue,  # NEW
)
```

**Impact**:
- ✅ Single line change
- ✅ Uses existing `station.venue_hint` field
- ✅ Backward compatible (parameters optional)

---

### Impact 4: Backtester Needs Same Context

**Current**: `Backtester` also calls `map_daily_high` without context

**File**: `agents/backtester.py`

**Change Needed**: Same as DynamicEngine - pass station_code and venue

**Impact**:
- ✅ Same minimal change
- ✅ Ensures backtesting uses same logic as live trading

---

## Minimal Implementation Plan

### Step 1: Create Rules Registry (30 minutes)

**New File**: `core/polymarket_station_rules.py`

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class StationRule:
    station_code: str
    venue: str
    uses_double_rounding: bool

class StationRulesRegistry:
    def __init__(self):
        self.rules = {
            "EGLC": StationRule("EGLC", "polymarket", True),
            "KLGA": StationRule("KLGA", "polymarket", True),
            # Kalshi stations would have uses_double_rounding=False
        }
    
    def get_rule(self, station_code: str) -> Optional[StationRule]:
        return self.rules.get(station_code)
```

**Impact**: New file, no existing code changes

---

### Step 2: Modify Probability Mapper (1 hour)

**File**: `agents/prob_mapper.py`

**Changes**:
1. Add optional parameters to `map_daily_high()`
2. Add rounding logic for Polymarket
3. Import rules registry

```python
from core.polymarket_station_rules import StationRulesRegistry
from core.units import resolve_to_whole_f

class ProbabilityMapper:
    def __init__(self, ...):
        # ... existing init ...
        self.rules_registry = StationRulesRegistry()
    
    def map_daily_high(
        self,
        forecast: ZeusForecast,
        brackets: List[MarketBracket],
        station_code: str = None,  # NEW
        venue: str = None,  # NEW
    ) -> List[BracketProb]:
        # 1. Compute daily high mean (unchanged)
        mu = self._compute_daily_high_mean(forecast)
        
        # 2. NEW: Apply double rounding for Polymarket
        mu_for_prob = mu
        if station_code:
            rule = self.rules_registry.get_rule(station_code)
            if rule and rule.uses_double_rounding:
                mu_for_prob = resolve_to_whole_f(mu)
                logger.debug(
                    f"Applied double rounding: {mu:.2f}°F → {mu_for_prob}°F "
                    f"(station: {station_code})"
                )
        elif venue == "polymarket":
            # Fallback if no station_code but venue provided
            mu_for_prob = resolve_to_whole_f(mu)
        
        # 3. Estimate uncertainty (unchanged)
        sigma = self._estimate_sigma(forecast, mu)
        
        # 4. Calculate probabilities using mu_for_prob
        probs = []
        for bracket in brackets:
            p = self._bracket_probability(mu_for_prob, sigma, bracket.lower_F, bracket.upper_F)
            probs.append(BracketProb(...))
        
        return probs
```

**Impact**: 
- ✅ Backward compatible (parameters optional)
- ✅ Only affects Polymarket stations
- ✅ Minimal logic change

---

### Step 3: Update Dynamic Engine (15 minutes)

**File**: `agents/dynamic_trader/dynamic_engine.py`

**Change** (line ~209):
```python
# Before
probs = self.prob_mapper.map_daily_high(forecast, brackets)

# After
venue = "polymarket" if "polymarket" in station.venue_hint.lower() else "kalshi"
probs = self.prob_mapper.map_daily_high(
    forecast=forecast,
    brackets=brackets,
    station_code=station.station_code,
    venue=venue,
)
```

**Impact**: Single location change

---

### Step 4: Update Backtester (15 minutes)

**File**: `agents/backtester.py`

**Change**: Same as DynamicEngine - pass station_code and venue

**Impact**: Single location change

---

## Testing Impact

### What Needs Testing

1. **Probability Calculation**:
   - Verify Polymarket stations use rounded temperature
   - Verify Kalshi stations use raw temperature
   - Verify backward compatibility (no station_code = raw temperature)

2. **Edge Calculation**:
   - Verify edges change appropriately with rounding
   - Verify no breaking changes to existing logic

3. **Backtesting**:
   - Verify backtester uses same logic
   - Compare results before/after

---

## Backward Compatibility

### Existing Code Compatibility

**Scenario 1**: Code calls `map_daily_high()` without new parameters
```python
probs = mapper.map_daily_high(forecast, brackets)
```
**Result**: ✅ Works - uses raw temperature (backward compatible)

**Scenario 2**: Code calls with station_code
```python
probs = mapper.map_daily_high(forecast, brackets, station_code="EGLC")
```
**Result**: ✅ Uses double rounding for Polymarket stations

**Scenario 3**: Code calls with venue
```python
probs = mapper.map_daily_high(forecast, brackets, venue="polymarket")
```
**Result**: ✅ Uses double rounding

---

## Data Structure Impact

### No Changes to Existing Data Structures

**BracketProb** (unchanged):
```python
class BracketProb:
    bracket: MarketBracket
    p_zeus: float  # Still a probability, just calculated differently
    p_mkt: Optional[float]
    sigma_z: float
```

**EdgeDecision** (unchanged):
```python
class EdgeDecision:
    bracket: MarketBracket
    edge: float  # Still calculated the same way
    f_kelly: float
    size_usd: float
    reason: str
```

**Impact**: ✅ No breaking changes to data structures

---

## Configuration Impact

### Optional: Rules Configuration File

**Future Enhancement**: Load rules from config file instead of hardcoded

**File**: `data/registry/polymarket_station_rules.json`
```json
{
  "EGLC": {
    "station_code": "EGLC",
    "venue": "polymarket",
    "uses_double_rounding": true
  },
  "KLGA": {
    "station_code": "KLGA",
    "venue": "polymarket",
    "uses_double_rounding": true
  }
}
```

**Impact**: 
- ✅ Not required for initial implementation
- ✅ Can be added later without breaking changes
- ✅ Makes it easier to add new stations

---

## Summary

### Structural Impact: **Minimal**

**Files Modified**:
1. `agents/prob_mapper.py` - Add optional parameters and rounding logic
2. `agents/dynamic_trader/dynamic_engine.py` - Pass station/venue context
3. `agents/backtester.py` - Pass station/venue context

**Files Created**:
1. `core/polymarket_station_rules.py` - Rules registry

**Total Changes**: 
- ~50 lines of new code
- ~10 lines modified in existing files
- 1 new file

**Breaking Changes**: **None** - All changes backward compatible

**Testing Required**:
- Unit tests for rounding logic
- Integration tests for probability calculation
- Backward compatibility tests

**Time Estimate**: 2-3 hours for implementation + testing

---

## Next Steps

### Phase 1: Double Rounding (Current Focus)
1. ✅ Create rules registry
2. ✅ Modify probability mapper
3. ✅ Update dynamic engine
4. ✅ Update backtester
5. ✅ Test

### Phase 2: Future Rules (Not Now)
- METAR update times
- Fragile boundary detection
- Cross-day bleed handling

These can be added incrementally without affecting double rounding implementation.

---

**Status**: 📋 **Structure Impact Analysis Complete** - Ready for minimal implementation

