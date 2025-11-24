# Venue & Station Microstructure Implementation Plan

**Date**: 2025-11-21  
**Purpose**: Implement venue and station-specific trading rules to account for microstructure (METAR updates, rounding, forecast updates, etc.) and enable intraday trading

---

## Executive Summary

**Current State**: We trade on simple edge: `Edge = (p_zeus - p_mkt) - fees - slippage`

**Proposed State**: We trade on adjusted edge that accounts for microstructure:
```
Edge = (p_zeus + microstructure_adjustment - p_mkt) - fees - slippage
```

**Key Innovation**: Anticipate predictable market moves from METAR updates, forecast updates, rounding boundaries, and venue-specific quirks.

---

## Current Implementation Analysis

### Current Edge Calculation

**File**: `agents/edge_and_sizing.py`

**Current Formula**:
```python
def compute_edge(self, p_zeus: float, p_mkt: float) -> float:
    fee_decimal = self.fee_bp / 10000.0
    slip_decimal = self.slippage_bp / 10000.0
    edge = (p_zeus - p_mkt) - fee_decimal - slip_decimal
    return edge
```

**What We Do**:
1. ✅ Fetch Zeus forecast (once per cycle)
2. ✅ Map to bracket probabilities
3. ✅ Get market prices
4. ✅ Calculate edge: `(p_zeus - p_mkt) - fees - slippage`
5. ✅ Size positions with Kelly criterion
6. ✅ Execute trades

**What We DON'T Account For**:
- ❌ METAR update timing (20/50 past hour for London, 50 past for NYC)
- ❌ Forecast update cycles (HRRR, NBM)
- ❌ Rounding boundaries and fragile brackets
- ❌ Cross-day temperature bleed
- ❌ Venue-specific resolution methods
- ❌ Intraday trading opportunities

---

## Proposed Architecture: Venue & Station Rules System

### Core Concept

**Venue Rules**: Polymarket vs Kalshi - different resolution methods, update cycles, trader behavior

**Station Rules**: London vs NYC - different METAR update times, timezone handling, rounding quirks

**Microstructure Adjustments**: Expected market moves from known upcoming events

---

## Implementation Plan

### Phase 1: Venue & Station Rules Framework

#### 1.1 Create Rules Configuration System

**New File**: `core/venue_station_rules.py`

```python
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import time
from enum import Enum

class Venue(str, Enum):
    POLYMARKET = "polymarket"
    KALSHI = "kalshi"

@dataclass
class StationRule:
    """Station-specific trading rules."""
    station_code: str
    city: str
    venue: Venue
    
    # METAR update times (minutes past hour)
    metar_update_times: List[int]  # e.g., [20, 50] for London, [50] for NYC
    
    # Rounding method
    rounding_method: str  # "standard", "double_rounding", "nws_cli"
    
    # Resolution source
    resolution_source: str  # "wunderground", "nws_cli", "noaa"
    
    # Timezone
    timezone: str
    
    # Special considerations
    fragile_boundaries: List[float]  # Temperatures where rounding is fragile
    cross_day_bleed_risk: bool  # Does overnight high affect next day?

@dataclass
class VenueRule:
    """Venue-specific trading rules."""
    venue: Venue
    
    # Forecast update cycles
    hrrr_update_interval_minutes: int  # Polymarket: 60
    nbm_update_interval_minutes: Optional[int]  # Polymarket: varies
    
    # Resolution method
    resolution_method: str  # "rounding", "hourly_obs", "cli_report"
    
    # Trader behavior
    trader_discipline: str  # "low" (Polymarket), "high" (Kalshi)
    overreaction_factor: float  # How much traders overreact (1.0-2.0)
    
    # Update sensitivity
    metar_sensitivity: float  # How much METAR updates move markets (0.0-1.0)
    forecast_sensitivity: float  # How much forecast updates move markets (0.0-1.0)
    
    # Minimum edge thresholds
    edge_min: float  # Polymarket: 0.05, Kalshi: 0.08

class VenueStationRulesRegistry:
    """Registry of venue and station-specific rules."""
    
    def __init__(self):
        self.station_rules: Dict[str, StationRule] = {}
        self.venue_rules: Dict[Venue, VenueRule] = {}
        self._load_rules()
    
    def _load_rules(self):
        """Load rules from configuration."""
        # Station rules
        self.station_rules["EGLC"] = StationRule(
            station_code="EGLC",
            city="London",
            venue=Venue.POLYMARKET,
            metar_update_times=[20, 50],  # 20 and 50 past hour
            rounding_method="standard",
            resolution_source="wunderground",
            timezone="Europe/London",
            fragile_boundaries=[],  # To be determined
            cross_day_bleed_risk=True,
        )
        
        self.station_rules["KLGA"] = StationRule(
            station_code="KLGA",
            city="New York (Airport)",
            venue=Venue.POLYMARKET,
            metar_update_times=[50],  # 50 past hour only
            rounding_method="double_rounding",  # NOAA → Polymarket
            resolution_source="wunderground",
            timezone="America/New_York",
            fragile_boundaries=[],
            cross_day_bleed_risk=True,
        )
        
        self.station_rules["KNYC"] = StationRule(
            station_code="KNYC",
            city="New York (City)",
            venue=Venue.KALSHI,
            metar_update_times=[50],  # 50 past hour
            rounding_method="nws_cli",
            resolution_source="nws_cli",
            timezone="America/New_York",
            fragile_boundaries=[],
            cross_day_bleed_risk=True,
        )
        
        # Venue rules
        self.venue_rules[Venue.POLYMARKET] = VenueRule(
            venue=Venue.POLYMARKET,
            hrrr_update_interval_minutes=60,
            nbm_update_interval_minutes=None,  # Varies
            resolution_method="rounding",
            trader_discipline="low",
            overreaction_factor=1.5,  # Traders overreact 50% more
            metar_sensitivity=0.8,  # High sensitivity to METAR
            forecast_sensitivity=0.9,  # Very high sensitivity to forecasts
            edge_min=0.05,  # 5% minimum
        )
        
        self.venue_rules[Venue.KALSHI] = VenueRule(
            venue=Venue.KALSHI,
            hrrr_update_interval_minutes=60,  # Not as relevant
            nbm_update_interval_minutes=None,
            resolution_method="hourly_obs",
            trader_discipline="high",
            overreaction_factor=1.2,  # Less overreaction
            metar_sensitivity=0.6,  # Lower sensitivity (METAR doesn't settle)
            forecast_sensitivity=0.4,  # Lower sensitivity
            edge_min=0.08,  # 8% minimum (more stable markets)
        )
    
    def get_station_rule(self, station_code: str) -> Optional[StationRule]:
        """Get rules for a station."""
        return self.station_rules.get(station_code)
    
    def get_venue_rule(self, venue: Venue) -> Optional[VenueRule]:
        """Get rules for a venue."""
        return self.venue_rules.get(venue)
```

---

### Phase 2: Microstructure Adjustment Calculator

#### 2.1 Create Microstructure Service

**New File**: `agents/microstructure_adjustment.py`

```python
"""Microstructure adjustments for venue/station-specific market moves."""

from datetime import datetime, timedelta
from typing import Optional, Dict
from zoneinfo import ZoneInfo

from core.venue_station_rules import VenueStationRulesRegistry, StationRule, VenueRule
from core.logger import logger

class MicrostructureAdjustment:
    """Calculate expected market moves from microstructure events."""
    
    def __init__(self):
        self.rules_registry = VenueStationRulesRegistry()
    
    def compute_adjustment(
        self,
        station_code: str,
        venue: str,
        current_time: datetime,
        bracket_temp: float,
        metar_trend: Optional[Dict] = None,
    ) -> float:
        """Compute microstructure adjustment to Zeus probability.
        
        Args:
            station_code: Station code (e.g., "EGLC")
            venue: Venue name ("polymarket", "kalshi")
            current_time: Current time (for update timing)
            bracket_temp: Bracket temperature (for rounding analysis)
            metar_trend: Optional METAR trend data
        
        Returns:
            Adjustment factor (0.0-1.0) to add to p_zeus
        """
        station_rule = self.rules_registry.get_station_rule(station_code)
        venue_rule = self.rules_registry.get_venue_rule(Venue(venue))
        
        if not station_rule or not venue_rule:
            return 0.0
        
        adjustment = 0.0
        
        # 1. METAR update adjustment
        metar_adjustment = self._compute_metar_adjustment(
            station_rule, venue_rule, current_time, metar_trend
        )
        adjustment += metar_adjustment
        
        # 2. Forecast update adjustment (HRRR, NBM)
        forecast_adjustment = self._compute_forecast_adjustment(
            venue_rule, current_time
        )
        adjustment += forecast_adjustment
        
        # 3. Rounding boundary adjustment
        rounding_adjustment = self._compute_rounding_adjustment(
            station_rule, venue_rule, bracket_temp
        )
        adjustment += rounding_adjustment
        
        # 4. Cross-day bleed adjustment
        cross_day_adjustment = self._compute_cross_day_adjustment(
            station_rule, venue_rule, current_time
        )
        adjustment += cross_day_adjustment
        
        return adjustment
    
    def _compute_metar_adjustment(
        self,
        station_rule: StationRule,
        venue_rule: VenueRule,
        current_time: datetime,
        metar_trend: Optional[Dict],
    ) -> float:
        """Compute expected move from upcoming METAR update."""
        # Get station timezone
        station_tz = ZoneInfo(station_rule.timezone)
        local_time = current_time.astimezone(station_tz)
        minutes_past_hour = local_time.minute
        
        # Find next METAR update
        next_update_minutes = None
        for update_time in sorted(station_rule.metar_update_times):
            if update_time > minutes_past_hour:
                next_update_minutes = update_time
                break
        
        if next_update_minutes is None:
            # Next update is in next hour
            next_update_minutes = station_rule.metar_update_times[0]
        
        minutes_until_update = next_update_minutes - minutes_past_hour
        if minutes_until_update < 0:
            minutes_until_update += 60
        
        # If update is soon (within 10 minutes), calculate expected move
        if minutes_until_update <= 10 and metar_trend:
            # Analyze METAR trend
            trend_direction = metar_trend.get("direction", "stable")  # "up", "down", "stable"
            trend_strength = metar_trend.get("strength", 0.0)  # 0.0-1.0
            
            # Expected move = trend direction × strength × venue sensitivity
            if trend_direction == "up":
                expected_move = trend_strength * venue_rule.metar_sensitivity * 0.1  # 10% max
            elif trend_direction == "down":
                expected_move = -trend_strength * venue_rule.metar_sensitivity * 0.1
            else:
                expected_move = 0.0
            
            # Scale by time until update (closer = larger expected move)
            time_factor = 1.0 - (minutes_until_update / 10.0)
            return expected_move * time_factor
        
        return 0.0
    
    def _compute_forecast_adjustment(
        self,
        venue_rule: VenueRule,
        current_time: datetime,
    ) -> float:
        """Compute expected move from upcoming forecast update (HRRR, NBM)."""
        # For Polymarket: HRRR updates every hour
        if venue_rule.venue == Venue.POLYMARKET:
            minutes_past_hour = current_time.minute
            minutes_until_hrrr = 60 - minutes_past_hour
            
            # If HRRR update is soon (within 15 minutes)
            if minutes_until_hrrr <= 15:
                # Expected move depends on Zeus vs HRRR alignment
                # If Zeus is ahead of HRRR, market will catch up
                # This is venue-specific logic
                return venue_rule.forecast_sensitivity * 0.05  # 5% max adjustment
        
        return 0.0
    
    def _compute_rounding_adjustment(
        self,
        station_rule: StationRule,
        venue_rule: VenueRule,
        bracket_temp: float,
    ) -> float:
        """Compute adjustment for fragile rounding boundaries."""
        # Check if bracket_temp is near a fragile boundary
        # Fragile boundaries: 50.95-51.05, 51.95-52.05, etc.
        
        # Extract integer part
        temp_int = int(bracket_temp)
        temp_decimal = bracket_temp - temp_int
        
        # Check if near boundary (0.95-1.05 range)
        if 0.95 <= temp_decimal <= 1.05 or 0.95 <= (1.0 - temp_decimal) <= 1.05:
            # This is a fragile boundary
            # Market might overreact to small METAR changes
            # Adjust probability to account for rounding uncertainty
            
            fragility_factor = abs(temp_decimal - 1.0) if temp_decimal > 0.5 else abs(temp_decimal)
            adjustment = fragility_factor * venue_rule.overreaction_factor * 0.15  # 15% max
            
            return adjustment
        
        return 0.0
    
    def _compute_cross_day_adjustment(
        self,
        station_rule: StationRule,
        venue_rule: VenueRule,
        current_time: datetime,
    ) -> float:
        """Compute adjustment for cross-day temperature bleed."""
        if not station_rule.cross_day_bleed_risk:
            return 0.0
        
        # If it's early morning (00:00-06:00 local), overnight high might affect today
        station_tz = ZoneInfo(station_rule.timezone)
        local_time = current_time.astimezone(station_tz)
        
        if 0 <= local_time.hour <= 6:
            # Early morning: overnight high might be confused with today's high
            # This creates temporary mispricing
            # Adjust for this confusion
            return venue_rule.overreaction_factor * 0.05  # 5% max
        
        return 0.0
```

---

### Phase 3: Enhanced Edge Calculation

#### 3.1 Modify Edge Calculation

**File**: `agents/edge_and_sizing.py` - Modify `compute_edge()` method

**Current**:
```python
def compute_edge(self, p_zeus: float, p_mkt: float) -> float:
    edge = (p_zeus - p_mkt) - fee_decimal - slip_decimal
    return edge
```

**Enhanced**:
```python
def compute_edge(
    self,
    p_zeus: float,
    p_mkt: float,
    microstructure_adjustment: float = 0.0,
) -> float:
    """Compute expected edge after costs and microstructure adjustments.
    
    Args:
        p_zeus: Zeus-derived probability (0-1)
        p_mkt: Market-implied probability (0-1)
        microstructure_adjustment: Expected market move from microstructure (0-1)
    
    Returns:
        Edge as a decimal (0.05 = 5% edge)
    """
    # Adjusted Zeus probability = base + expected microstructure move
    p_zeus_adjusted = p_zeus + microstructure_adjustment
    
    # Clamp to valid range
    p_zeus_adjusted = max(0.0, min(1.0, p_zeus_adjusted))
    
    # Calculate edge with adjusted probability
    edge = (p_zeus_adjusted - p_mkt) - fee_decimal - slip_decimal
    
    logger.debug(
        f"Edge: p_zeus={p_zeus:.4f}, adjustment={microstructure_adjustment:.4f}, "
        f"p_zeus_adj={p_zeus_adjusted:.4f}, p_mkt={p_mkt:.4f}, "
        f"fees={fee_decimal:.4f}, slip={slip_decimal:.4f}, edge={edge:.4f}"
    )
    
    return edge
```

---

### Phase 4: METAR Trend Analysis

#### 4.1 Create METAR Trend Service

**New File**: `agents/metar_trend_analyzer.py`

```python
"""Analyze METAR trends to predict market moves."""

from typing import List, Optional, Dict
from datetime import datetime
from core.types import MetarObservation

class MetarTrendAnalyzer:
    """Analyze METAR observations to predict market direction."""
    
    def analyze_trend(
        self,
        observations: List[MetarObservation],
        bracket_temp: float,
        lookback_minutes: int = 30,
    ) -> Dict[str, float]:
        """Analyze METAR trend for a bracket.
        
        Args:
            observations: Recent METAR observations
            bracket_temp: Target bracket temperature
            lookback_minutes: How far back to look
        
        Returns:
            {
                "direction": "up" | "down" | "stable",
                "strength": 0.0-1.0,
                "trending_toward_bracket": bool,
                "minutes_to_bracket": Optional[float],
            }
        """
        if not observations or len(observations) < 2:
            return {
                "direction": "stable",
                "strength": 0.0,
                "trending_toward_bracket": False,
                "minutes_to_bracket": None,
            }
        
        # Filter to recent observations
        cutoff_time = datetime.now() - timedelta(minutes=lookback_minutes)
        recent = [obs for obs in observations if obs.time >= cutoff_time]
        
        if len(recent) < 2:
            return {"direction": "stable", "strength": 0.0, ...}
        
        # Calculate trend
        temps = [obs.temp_F for obs in recent]
        first_temp = temps[0]
        last_temp = temps[-1]
        temp_change = last_temp - first_temp
        
        # Determine direction
        if temp_change > 0.2:  # Warming
            direction = "up"
            strength = min(1.0, abs(temp_change) / 2.0)  # Normalize
        elif temp_change < -0.2:  # Cooling
            direction = "down"
            strength = min(1.0, abs(temp_change) / 2.0)
        else:
            direction = "stable"
            strength = 0.0
        
        # Check if trending toward bracket
        bracket_lower = int(bracket_temp)
        bracket_upper = bracket_lower + 1
        
        trending_toward = False
        if direction == "up" and last_temp < bracket_upper:
            trending_toward = True
        elif direction == "down" and last_temp > bracket_lower:
            trending_toward = True
        
        # Estimate minutes until bracket (if trending)
        minutes_to_bracket = None
        if trending_toward and direction != "stable":
            temp_per_minute = temp_change / len(recent)  # Rough estimate
            if temp_per_minute != 0:
                temp_needed = bracket_temp - last_temp
                minutes_to_bracket = abs(temp_needed / temp_per_minute)
        
        return {
            "direction": direction,
            "strength": strength,
            "trending_toward_bracket": trending_toward,
            "minutes_to_bracket": minutes_to_bracket,
        }
```

---

### Phase 5: Intraday Trading System

#### 5.1 Enhanced Trading Engine

**File**: `agents/dynamic_trader/dynamic_engine.py` - Enhance `_evaluate_and_trade()`

**Current Flow**:
1. Fetch Zeus
2. Fetch Polymarket
3. Map probabilities
4. Calculate edges
5. Execute trades

**Enhanced Flow**:
1. Fetch Zeus
2. Fetch Polymarket
3. **Fetch METAR (with trend analysis)**
4. Map probabilities
5. **Calculate microstructure adjustments**
6. **Calculate adjusted edges**
7. **Check for intraday opportunities** (METAR updates, forecast updates)
8. Execute trades (both position entry and intraday adjustments)

**New Method**:
```python
def _check_intraday_opportunities(
    self,
    station: Station,
    current_time: datetime,
    probs: List[BracketProb],
    metar_observations: List[MetarObservation],
) -> List[EdgeDecision]:
    """Check for intraday trading opportunities around updates.
    
    Returns:
        List of intraday trade decisions (scaling, hedging, exiting)
    """
    station_rule = self.rules_registry.get_station_rule(station.station_code)
    venue_rule = self.rules_registry.get_venue_rule(Venue(station.venue_hint))
    
    if not station_rule or not venue_rule:
        return []
    
    opportunities = []
    
    # Check if METAR update is imminent
    station_tz = ZoneInfo(station_rule.timezone)
    local_time = current_time.astimezone(station_tz)
    minutes_past_hour = local_time.minute
    
    # Find next METAR update
    next_update = None
    for update_time in sorted(station_rule.metar_update_times):
        if update_time > minutes_past_hour:
            next_update = update_time
            break
    
    if next_update and (next_update - minutes_past_hour) <= 5:
        # METAR update within 5 minutes - analyze trend
        trend_analyzer = MetarTrendAnalyzer()
        
        for prob in probs:
            bracket_temp = (prob.bracket.lower_F + prob.bracket.upper_F) / 2.0
            trend = trend_analyzer.analyze_trend(metar_observations, bracket_temp)
            
            if trend["trending_toward_bracket"]:
                # METAR is trending toward this bracket
                # Market will likely move in our favor
                # Consider scaling up position or entering if not already in
                
                # Calculate expected move
                microstructure = self.microstructure_adjustment.compute_adjustment(
                    station.station_code,
                    station.venue_hint,
                    current_time,
                    bracket_temp,
                    metar_trend=trend,
                )
                
                # Recalculate edge with adjustment
                adjusted_edge = self.sizer.compute_edge(
                    prob.p_zeus,
                    prob.p_mkt,
                    microstructure_adjustment=microstructure,
                )
                
                if adjusted_edge > self.sizer.edge_min:
                    # Create intraday opportunity
                    opportunity = EdgeDecision(
                        bracket=prob.bracket,
                        edge=adjusted_edge,
                        f_kelly=self.sizer.compute_kelly_fraction(
                            prob.p_zeus + microstructure, prob.p_mkt
                        ),
                        size_usd=0,  # Calculate based on existing position
                        reason=f"intraday_metar_update_{next_update}",
                    )
                    opportunities.append(opportunity)
    
    return opportunities
```

---

## Implementation Stages

### Stage 1: Rules Framework (Week 1)

**Tasks**:
1. ✅ Create `core/venue_station_rules.py`
2. ✅ Define `StationRule` and `VenueRule` dataclasses
3. ✅ Create `VenueStationRulesRegistry`
4. ✅ Load rules for existing stations (EGLC, KLGA, KNYC, etc.)
5. ✅ Add rules to station registry CSV or separate config file

**Time**: 4-6 hours

---

### Stage 2: Microstructure Calculator (Week 1-2)

**Tasks**:
1. ✅ Create `agents/microstructure_adjustment.py`
2. ✅ Implement METAR update adjustment
3. ✅ Implement forecast update adjustment (HRRR, NBM)
4. ✅ Implement rounding boundary adjustment
5. ✅ Implement cross-day bleed adjustment
6. ✅ Test with known scenarios

**Time**: 8-12 hours

---

### Stage 3: METAR Trend Analysis (Week 2)

**Tasks**:
1. ✅ Create `agents/metar_trend_analyzer.py`
2. ✅ Implement trend detection (up/down/stable)
3. ✅ Implement bracket convergence analysis
4. ✅ Integrate with microstructure calculator
5. ✅ Test with historical data

**Time**: 6-8 hours

---

### Stage 4: Enhanced Edge Calculation (Week 2)

**Tasks**:
1. ✅ Modify `agents/edge_and_sizing.py`
2. ✅ Add `microstructure_adjustment` parameter to `compute_edge()`
3. ✅ Update `decide()` method to calculate adjustments
4. ✅ Integrate with rules registry
5. ✅ Test edge calculations with adjustments

**Time**: 4-6 hours

---

### Stage 5: Intraday Trading (Week 3)

**Tasks**:
1. ✅ Enhance `dynamic_engine.py`
2. ✅ Add `_check_intraday_opportunities()` method
3. ✅ Implement position scaling logic
4. ✅ Implement hedging around boundaries
5. ✅ Add exit logic for intraday trades
6. ✅ Test intraday trading flow

**Time**: 12-16 hours

---

### Stage 6: Configuration & Testing (Week 3-4)

**Tasks**:
1. ✅ Create rules configuration file
2. ✅ Add rules for all stations
3. ✅ Backtest with microstructure adjustments
4. ✅ Compare performance: with vs without adjustments
5. ✅ Tune adjustment factors based on results

**Time**: 8-12 hours

---

## Configuration File Structure

### Station Rules Configuration

**File**: `data/registry/station_rules.json`

```json
{
  "EGLC": {
    "station_code": "EGLC",
    "city": "London",
    "venue": "polymarket",
    "metar_update_times": [20, 50],
    "rounding_method": "standard",
    "resolution_source": "wunderground",
    "timezone": "Europe/London",
    "fragile_boundaries": [],
    "cross_day_bleed_risk": true
  },
  "KLGA": {
    "station_code": "KLGA",
    "city": "New York (Airport)",
    "venue": "polymarket",
    "metar_update_times": [50],
    "rounding_method": "double_rounding",
    "resolution_source": "wunderground",
    "timezone": "America/New_York",
    "fragile_boundaries": [],
    "cross_day_bleed_risk": true
  },
  "KNYC": {
    "station_code": "KNYC",
    "city": "New York (City)",
    "venue": "kalshi",
    "metar_update_times": [50],
    "rounding_method": "nws_cli",
    "resolution_source": "nws_cli",
    "timezone": "America/New_York",
    "fragile_boundaries": [],
    "cross_day_bleed_risk": true,
    "cli_release_time": "16:30",  # 4:30 PM local
    "hourly_obs_release_minute": 51
  }
}
```

### Venue Rules Configuration

**File**: `data/registry/venue_rules.json`

```json
{
  "polymarket": {
    "venue": "polymarket",
    "hrrr_update_interval_minutes": 60,
    "nbm_update_interval_minutes": null,
    "resolution_method": "rounding",
    "trader_discipline": "low",
    "overreaction_factor": 1.5,
    "metar_sensitivity": 0.8,
    "forecast_sensitivity": 0.9,
    "edge_min": 0.05
  },
  "kalshi": {
    "venue": "kalshi",
    "hrrr_update_interval_minutes": 60,
    "nbm_update_interval_minutes": null,
    "resolution_method": "hourly_obs",
    "trader_discipline": "high",
    "overreaction_factor": 1.2,
    "metar_sensitivity": 0.6,
    "forecast_sensitivity": 0.4,
    "edge_min": 0.08,
    "cli_release_time_local": "16:30",
    "hourly_obs_release_minute": 51
  }
}
```

---

## Enhanced Trading Flow

### Current Flow

```
1. Fetch Zeus → p_zeus
2. Fetch Market → p_mkt
3. Calculate: edge = (p_zeus - p_mkt) - fees
4. If edge > threshold → Trade
```

### Enhanced Flow

```
1. Fetch Zeus → p_zeus
2. Fetch Market → p_mkt
3. Fetch METAR → Analyze trend
4. Get Station Rules → METAR update times, rounding method, etc.
5. Get Venue Rules → Trader behavior, sensitivity factors
6. Calculate Microstructure Adjustment:
   - METAR update expected move
   - Forecast update expected move
   - Rounding boundary adjustment
   - Cross-day bleed adjustment
7. Calculate: edge = (p_zeus + adjustment - p_mkt) - fees
8. Check Intraday Opportunities:
   - METAR update within 5 minutes?
   - Forecast update soon?
   - Fragile boundary?
9. If edge > threshold OR intraday opportunity → Trade
10. Monitor for exit/scaling opportunities
```

---

## Special Trading Plays

### Play 1: Rounding Boundary Trade

**When**: Bracket temperature is near fragile boundary (e.g., 50.95-51.05°F)

**Strategy**:
```python
def is_fragile_boundary(bracket_temp: float) -> bool:
    temp_int = int(bracket_temp)
    temp_decimal = bracket_temp - temp_int
    return 0.95 <= temp_decimal <= 1.05 or 0.95 <= (1.0 - temp_decimal) <= 1.05

if is_fragile_boundary(bracket_temp):
    # Increase position size (higher EV)
    kelly_multiplier = 1.5  # 50% larger position
    # Adjust edge threshold down (more opportunities)
    edge_min = 0.03  # 3% instead of 5%
```

---

### Play 2: METAR Update Front-Run

**When**: METAR update within 5 minutes, trend is clear

**Strategy**:
```python
# Before update (5 minutes before)
if minutes_until_metar <= 5 and trend["trending_toward_bracket"]:
    # Enter position
    # Market will move when METAR confirms trend
    
# After update (immediately after)
if just_after_metar_update and trend_confirmed:
    # Scale up if trend continues
    # Exit if trend reverses
```

---

### Play 3: Hourly Obs Fade (Kalshi)

**When**: METAR spikes but not close to hourly obs release

**Strategy**:
```python
# If METAR shows spike but:
# - Not at :51-:56 (hourly obs window)
# - Not sustained
# - Not consistent with forecast
# → Fade the spike (bet against it)

if venue == "kalshi":
    if metar_spike and not near_hourly_obs_release:
        # Market overreacted
        # Bet against the spike
        fade_edge = calculate_fade_edge(...)
        if fade_edge > threshold:
            trade_against_spike()
```

---

### Play 4: HRRR Drift Play (Polymarket)

**When**: Zeus and HRRR align, or Zeus ahead of HRRR

**Strategy**:
```python
# If Zeus predicts higher than HRRR:
# → Market will catch up when HRRR updates
# → Enter position before HRRR update

if zeus_prob > hrrr_prob and minutes_until_hrrr <= 15:
    # Anticipatory trade
    expected_move = (zeus_prob - hrrr_prob) * forecast_sensitivity
    adjusted_edge = base_edge + expected_move
    if adjusted_edge > threshold:
        trade()
```

---

## Data Requirements

### New Data to Track

1. **METAR Update Times**: When each station gets METAR updates
2. **Forecast Update Cycles**: HRRR, NBM update schedules
3. **Historical Market Moves**: How much markets move after updates
4. **Rounding Boundary Data**: Which temperatures are fragile
5. **Cross-Day Patterns**: Overnight high patterns

### New Snapshots to Save

1. **METAR Trend Snapshots**: Before/after update trends
2. **Forecast Update Snapshots**: HRRR/NBM update impacts
3. **Intraday Trade Snapshots**: Entry/exit times and reasons

---

## Testing Strategy

### Unit Tests

1. **Rules Loading**: Verify rules load correctly for all stations
2. **Microstructure Calculation**: Test each adjustment type
3. **Trend Analysis**: Test METAR trend detection
4. **Edge Calculation**: Test enhanced edge with adjustments

### Integration Tests

1. **Full Trading Cycle**: Test with microstructure adjustments
2. **Intraday Opportunities**: Test detection and execution
3. **Multiple Stations**: Test London vs NYC differences

### Backtesting

1. **Historical Performance**: Compare with vs without adjustments
2. **Update Windows**: Test if timing adjustments correctly
3. **Special Plays**: Test rounding, fade, drift plays

---

## Performance Metrics

### New Metrics to Track

1. **Microstructure Capture**: How often we correctly predict moves
2. **Intraday P&L**: Profit from intraday trades vs hold-to-resolution
3. **Update Timing Accuracy**: How well we time METAR/forecast updates
4. **Rounding Play Success**: Win rate on fragile boundary trades

---

## Migration Path

### Phase 1: Add Without Breaking (Week 1-2)

- Add rules framework
- Add microstructure calculator
- **Don't change existing edge calculation yet**
- Log adjustments for analysis

### Phase 2: Enable Gradually (Week 2-3)

- Add feature flag: `use_microstructure_adjustments`
- Enable for one station first (e.g., EGLC)
- Compare performance
- Tune factors

### Phase 3: Full Rollout (Week 3-4)

- Enable for all stations
- Add intraday trading
- Monitor and optimize

---

## Summary

**Current State**: Simple edge calculation, no microstructure awareness

**Proposed State**: 
- Venue/station rules system
- Microstructure adjustments
- Intraday trading capabilities
- Special plays for high-EV situations

**Key Benefits**:
- Trade before market moves (anticipate updates)
- Capture intraday volatility
- Exploit rounding boundaries
- Front-run other traders

**Implementation Time**: 3-4 weeks

**Priority**: High - This could significantly improve trading performance

---

**Status**: 📋 **Implementation Plan Created** - Ready for staged implementation

