# Polymarket-Specific Rules Implementation

**Date**: 2025-11-21  
**Focus**: Polymarket-only implementation (Kalshi to be added later)  
**Priority**: High - Addresses critical microstructure issues

---

## Current State Analysis

### What We Currently Do

**Edge Calculation** (`agents/edge_and_sizing.py`):
```python
edge = (p_zeus - p_mkt) - fees - slippage
```

**Daily High Calculation** (`agents/prob_mapper.py`):
- Takes max of hourly Zeus forecast temperatures
- Maps to bracket probabilities using normal distribution
- No rounding consideration
- No METAR update timing
- No cross-day handling

**Rounding** (`core/units.py`):
- `resolve_to_whole_f()`: Simple rounding (temp + 0.5)
- Used for resolution, but not in probability calculations

**Trading Flow** (`agents/dynamic_trader/dynamic_engine.py`):
1. Fetch Zeus forecast
2. Fetch Polymarket prices
3. Fetch METAR (but don't use for adjustments)
4. Calculate probabilities
5. Calculate edges
6. Execute trades

**What We DON'T Account For**:
- ❌ Double rounding (NOAA → Polymarket)
- ❌ METAR update windows (20/50 past for London, 50 past for NYC)
- ❌ Fragile rounding boundaries (e.g., 50.95-51.05°F)
- ❌ Cross-day high bleed (overnight high affecting next day)
- ❌ Trading strategy around update windows

---

## Implementation Plan

### Phase 1: Station Rules Configuration

#### 1.1 Create Station Rules System

**New File**: `core/polymarket_station_rules.py`

```python
"""Polymarket station-specific trading rules."""

from dataclasses import dataclass
from typing import List
from zoneinfo import ZoneInfo

@dataclass
class PolymarketStationRule:
    """Station-specific rules for Polymarket trading."""
    
    station_code: str
    city: str
    timezone: str
    
    # METAR update times (minutes past hour)
    metar_update_times: List[int]  # e.g., [20, 50] for London, [50] for NYC
    
    # Rounding method
    uses_double_rounding: bool  # True for Polymarket (NOAA → Polymarket)
    
    # Cross-day bleed risk
    cross_day_bleed_risk: bool  # True if overnight high can affect next day
    
    def get_timezone(self) -> ZoneInfo:
        """Get timezone object."""
        return ZoneInfo(self.timezone)
    
    def get_next_metar_update_minutes(self, current_minute: int) -> int:
        """Get minutes until next METAR update.
        
        Args:
            current_minute: Current minute past hour (0-59)
        
        Returns:
            Minutes until next update (0-60)
        """
        for update_time in sorted(self.metar_update_times):
            if update_time > current_minute:
                return update_time - current_minute
        
        # Next update is in next hour
        return (60 - current_minute) + self.metar_update_times[0]
    
    def is_near_metar_update(self, current_minute: int, threshold_minutes: int = 5) -> bool:
        """Check if we're near a METAR update.
        
        Args:
            current_minute: Current minute past hour
            threshold_minutes: How many minutes before update to consider "near"
        
        Returns:
            True if within threshold_minutes of next update
        """
        minutes_until = self.get_next_metar_update_minutes(current_minute)
        return minutes_until <= threshold_minutes


class PolymarketStationRulesRegistry:
    """Registry of Polymarket station rules."""
    
    def __init__(self):
        self.rules: dict[str, PolymarketStationRule] = {}
        self._load_rules()
    
    def _load_rules(self):
        """Load station rules."""
        # London (EGLC)
        self.rules["EGLC"] = PolymarketStationRule(
            station_code="EGLC",
            city="London",
            timezone="Europe/London",
            metar_update_times=[20, 50],  # 20 and 50 past hour
            uses_double_rounding=True,
            cross_day_bleed_risk=True,
        )
        
        # New York (KLGA)
        self.rules["KLGA"] = PolymarketStationRule(
            station_code="KLGA",
            city="New York (Airport)",
            timezone="America/New_York",
            metar_update_times=[50],  # 50 past hour only
            uses_double_rounding=True,
            cross_day_bleed_risk=True,
        )
    
    def get_rule(self, station_code: str) -> PolymarketStationRule | None:
        """Get rules for a station."""
        return self.rules.get(station_code)


# Global registry instance
polymarket_rules = PolymarketStationRulesRegistry()
```

---

### Phase 2: Double Rounding for Polymarket

#### 2.1 Understanding Double Rounding

**Polymarket Resolution Process**:
1. NOAA reports temperature (e.g., 50.7°F)
2. NOAA rounds to whole degree (50.7°F → 51°F) - **First Rounding**
3. Polymarket uses this rounded value for bracket resolution
4. If bracket is [50-51)°F, 51°F falls into [51-52)°F - **Second Rounding Effect**

**Impact on Probability**:
- Temperature 50.7°F → rounds to 51°F → bracket [51-52)°F
- Temperature 50.3°F → rounds to 50°F → bracket [50-51)°F
- **Fragile zone**: 50.4-50.6°F could go either way depending on rounding

#### 2.2 Implement Double Rounding Adjustment

**New File**: `agents/polymarket_rounding.py`

```python
"""Polymarket double rounding adjustments."""

from typing import Tuple
from core.units import resolve_to_whole_f
from core.logger import logger

def apply_double_rounding(temp_f: float) -> int:
    """Apply Polymarket double rounding.
    
    Polymarket uses NOAA data which is already rounded.
    So we round twice to match Polymarket's resolution.
    
    Args:
        temp_f: Raw temperature in Fahrenheit
    
    Returns:
        Rounded temperature (what Polymarket would use)
    """
    # First rounding: NOAA rounds to whole degree
    first_round = resolve_to_whole_f(temp_f)
    
    # Second rounding: Polymarket uses this rounded value
    # (In practice, this is the same, but we're being explicit)
    return first_round


def is_fragile_boundary(temp_f: float, threshold: float = 0.1) -> bool:
    """Check if temperature is near a fragile rounding boundary.
    
    Fragile boundaries are temperatures where small changes can flip
    the bracket due to rounding (e.g., 50.4-50.6°F).
    
    Args:
        temp_f: Temperature in Fahrenheit
        threshold: How close to boundary to consider fragile (default 0.1°F)
    
    Returns:
        True if near fragile boundary
    """
    rounded = resolve_to_whole_f(temp_f)
    distance_to_boundary = abs(temp_f - rounded)
    
    return distance_to_boundary < threshold


def get_fragile_boundary_adjustment(
    temp_f: float,
    bracket_lower: int,
    bracket_upper: int,
) -> float:
    """Calculate probability adjustment for fragile rounding boundaries.
    
    When temperature is near a boundary (e.g., 50.95-51.05°F), there's
    uncertainty about which bracket it will fall into. This creates
    trading opportunities.
    
    Args:
        temp_f: Predicted temperature
        bracket_lower: Lower bound of bracket
        bracket_upper: Upper bound of bracket
    
    Returns:
        Adjustment factor (-0.2 to +0.2) to add to probability
    """
    rounded = resolve_to_whole_f(temp_f)
    
    # Check if we're in fragile zone
    if not is_fragile_boundary(temp_f, threshold=0.1):
        return 0.0
    
    # Calculate distance to boundary
    distance = abs(temp_f - rounded)
    
    # If very close to boundary (within 0.05°F), high uncertainty
    if distance < 0.05:
        # 50% chance it rounds up, 50% chance it rounds down
        # This creates volatility - adjust probability accordingly
        if bracket_lower == rounded:
            # We're betting on lower bracket, but might round up
            return -0.15  # Reduce probability (uncertainty)
        elif bracket_upper == rounded + 1:
            # We're betting on upper bracket, might round down
            return -0.15  # Reduce probability (uncertainty)
        else:
            # Middle bracket - less affected
            return 0.0
    
    # If near boundary but not extremely close (0.05-0.1°F)
    if bracket_lower == rounded:
        # Slight reduction due to rounding risk
        return -0.05
    elif bracket_upper == rounded + 1:
        return -0.05
    
    return 0.0


def calculate_rounding_risk_adjustment(
    zeus_temp: float,
    bracket_lower: int,
    bracket_upper: int,
) -> Tuple[float, str]:
    """Calculate adjustment for rounding risk and return reason.
    
    Args:
        zeus_temp: Zeus predicted temperature
        bracket_lower: Bracket lower bound
        bracket_upper: Bracket upper bound
    
    Returns:
        (adjustment, reason) tuple
    """
    adjustment = get_fragile_boundary_adjustment(zeus_temp, bracket_lower, bracket_upper)
    
    if abs(adjustment) > 0.1:
        reason = "high_rounding_risk"
    elif abs(adjustment) > 0.05:
        reason = "moderate_rounding_risk"
    else:
        reason = "low_rounding_risk"
    
    return adjustment, reason
```

---

### Phase 3: METAR Update Window Strategy

#### 3.1 Understanding METAR Update Windows

**London (EGLC)**:
- Updates at **:20** and **:50** past each hour
- Traders watch these updates and adjust positions
- Market moves predictably around these times

**NYC (KLGA)**:
- Updates at **:50** past each hour
- Single update window per hour
- Less frequent but still significant

**Strategy**:
- **Before Update**: Position based on METAR trend
- **After Update**: React to confirmed data
- **During Window**: High volatility, potential mispricing

#### 3.2 Implement METAR Update Strategy

**New File**: `agents/metar_update_strategy.py`

```python
"""Trading strategy around METAR update windows."""

from datetime import datetime
from typing import Optional, Dict, List
from zoneinfo import ZoneInfo

from core.polymarket_station_rules import polymarket_rules
from venues.metar.metar_service import MetarObservation
from core.logger import logger


class MetarUpdateStrategy:
    """Strategy for trading around METAR update windows."""
    
    def __init__(self):
        self.rules_registry = polymarket_rules
    
    def analyze_metar_trend(
        self,
        observations: List[MetarObservation],
        bracket_temp: float,
        lookback_minutes: int = 30,
    ) -> Dict[str, any]:
        """Analyze METAR trend toward a bracket.
        
        Args:
            observations: Recent METAR observations
            bracket_temp: Target bracket temperature
            lookback_minutes: How far back to analyze
        
        Returns:
            {
                "direction": "up" | "down" | "stable",
                "strength": 0.0-1.0,
                "trending_toward_bracket": bool,
                "current_temp": float,
                "minutes_to_bracket": Optional[float],
            }
        """
        if not observations or len(observations) < 2:
            return {
                "direction": "stable",
                "strength": 0.0,
                "trending_toward_bracket": False,
                "current_temp": None,
                "minutes_to_bracket": None,
            }
        
        # Filter to recent observations
        cutoff_time = datetime.now(ZoneInfo("UTC")) - timedelta(minutes=lookback_minutes)
        recent = [obs for obs in observations if obs.time >= cutoff_time]
        
        if len(recent) < 2:
            return {
                "direction": "stable",
                "strength": 0.0,
                "trending_toward_bracket": False,
                "current_temp": recent[0].temp_F if recent else None,
                "minutes_to_bracket": None,
            }
        
        # Calculate trend
        temps = [obs.temp_F for obs in recent]
        first_temp = temps[0]
        last_temp = temps[-1]
        temp_change = last_temp - first_temp
        
        # Determine direction
        if temp_change > 0.2:
            direction = "up"
            strength = min(1.0, abs(temp_change) / 2.0)
        elif temp_change < -0.2:
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
        
        # Estimate minutes until bracket
        minutes_to_bracket = None
        if trending_toward and direction != "stable" and len(recent) > 1:
            time_span = (recent[-1].time - recent[0].time).total_seconds() / 60.0
            if time_span > 0:
                temp_per_minute = temp_change / time_span
                if temp_per_minute != 0:
                    temp_needed = bracket_temp - last_temp
                    minutes_to_bracket = abs(temp_needed / temp_per_minute)
        
        return {
            "direction": direction,
            "strength": strength,
            "trending_toward_bracket": trending_toward,
            "current_temp": last_temp,
            "minutes_to_bracket": minutes_to_bracket,
        }
    
    def calculate_metar_update_adjustment(
        self,
        station_code: str,
        current_time: datetime,
        metar_trend: Optional[Dict] = None,
        bracket_temp: float = None,
    ) -> Tuple[float, str]:
        """Calculate probability adjustment for upcoming METAR update.
        
        Args:
            station_code: Station code (e.g., "EGLC")
            current_time: Current time (UTC)
            metar_trend: Optional METAR trend analysis
            bracket_temp: Optional bracket temperature for trend analysis
        
        Returns:
            (adjustment, reason) tuple
        """
        rule = self.rules_registry.get_rule(station_code)
        if not rule:
            return 0.0, "no_rule"
        
        # Convert to station local time
        station_tz = rule.get_timezone()
        local_time = current_time.astimezone(station_tz)
        current_minute = local_time.minute
        
        # Check if near METAR update
        minutes_until_update = rule.get_next_metar_update_minutes(current_minute)
        is_near = rule.is_near_metar_update(current_minute, threshold_minutes=5)
        
        if not is_near:
            return 0.0, "not_near_update"
        
        # If we have METAR trend, calculate expected move
        if metar_trend and bracket_temp:
            direction = metar_trend.get("direction", "stable")
            strength = metar_trend.get("strength", 0.0)
            trending_toward = metar_trend.get("trending_toward_bracket", False)
            
            if trending_toward and direction != "stable":
                # METAR is trending toward bracket
                # Market will likely move in our favor when update confirms
                
                # Expected move = trend strength × time factor × sensitivity
                time_factor = 1.0 - (minutes_until_update / 5.0)  # Closer = larger
                sensitivity = 0.8  # Polymarket is sensitive to METAR
                
                if direction == "up":
                    adjustment = strength * time_factor * sensitivity * 0.15  # Max 15%
                else:
                    adjustment = -strength * time_factor * sensitivity * 0.15
                
                reason = f"metar_trend_{direction}_update_in_{minutes_until_update}min"
                return adjustment, reason
        
        # If no trend but near update, expect volatility
        if minutes_until_update <= 2:
            # Very close to update - expect volatility
            return 0.05, "metar_update_volatility"
        
        return 0.0, "near_update_no_trend"
    
    def should_trade_before_update(
        self,
        station_code: str,
        current_time: datetime,
        metar_trend: Dict,
        zeus_prob: float,
        market_prob: float,
    ) -> Tuple[bool, str]:
        """Determine if we should trade before METAR update.
        
        Strategy:
        - If METAR trending toward bracket AND Zeus agrees → Buy before update
        - If METAR trending away AND Zeus agrees → Short before update
        - If METAR and Zeus disagree → Wait for update
        
        Args:
            station_code: Station code
            current_time: Current time
            metar_trend: METAR trend analysis
            zeus_prob: Zeus probability for bracket
            market_prob: Market probability
        
        Returns:
            (should_trade, reason) tuple
        """
        rule = self.rules_registry.get_rule(station_code)
        if not rule:
            return False, "no_rule"
        
        # Check if near update
        station_tz = rule.get_timezone()
        local_time = current_time.astimezone(station_tz)
        is_near = rule.is_near_metar_update(local_time.minute, threshold_minutes=5)
        
        if not is_near:
            return False, "not_near_update"
        
        # Analyze alignment
        trending_toward = metar_trend.get("trending_toward_bracket", False)
        direction = metar_trend.get("direction", "stable")
        zeus_edge = zeus_prob - market_prob
        
        if trending_toward and zeus_edge > 0.05:
            # METAR trending toward bracket, Zeus agrees, positive edge
            return True, "metar_zeus_aligned_buy"
        
        if direction == "down" and zeus_edge < -0.05:
            # METAR trending down, Zeus agrees, negative edge (short opportunity)
            return True, "metar_zeus_aligned_short"
        
        if not trending_toward and abs(zeus_edge) < 0.03:
            # METAR and Zeus don't align, small edge
            return False, "metar_zeus_misaligned"
        
        return False, "no_clear_signal"
```

---

### Phase 4: Cross-Day High Bleed Handling

#### 4.1 Understanding Cross-Day Bleed

**Problem**:
- Yesterday's high occurred late (e.g., 23:50)
- Overnight temperature stays warm
- Early morning (00:00-06:00) temperature might exceed yesterday's high
- Traders confuse overnight high with today's high
- Creates temporary mispricing

**Example**:
- Nov 15 high: 51.8°F at 23:50
- Nov 16 00:00-06:00: Still 50-51°F
- Traders think: "High already hit!" → Sell
- But actual Nov 16 high might be 52°F in afternoon
- **Mispricing opportunity**

#### 4.2 Implement Cross-Day Bleed Detection

**New File**: `agents/cross_day_bleed.py`

```python
"""Cross-day high bleed detection and adjustment."""

from datetime import datetime, date, timedelta
from typing import Optional, Tuple
from zoneinfo import ZoneInfo

from core.polymarket_station_rules import polymarket_rules
from venues.metar.metar_service import METARService
from core.logger import logger


class CrossDayBleedAnalyzer:
    """Analyze and adjust for cross-day high bleed."""
    
    def __init__(self):
        self.rules_registry = polymarket_rules
        self.metar_service = METARService()
    
    def detect_cross_day_bleed(
        self,
        station_code: str,
        event_day: date,
        current_time: datetime,
    ) -> Tuple[bool, Optional[Dict]]:
        """Detect if cross-day bleed is occurring.
        
        Args:
            station_code: Station code
            event_day: Event day
            current_time: Current time
        
        Returns:
            (is_bleeding, details) tuple
        """
        rule = self.rules_registry.get_rule(station_code)
        if not rule or not rule.cross_day_bleed_risk:
            return False, None
        
        # Check if early morning (00:00-06:00 local)
        station_tz = rule.get_timezone()
        local_time = current_time.astimezone(station_tz)
        
        if not (0 <= local_time.hour <= 6):
            return False, None
        
        # Get previous day's high
        previous_day = event_day - timedelta(days=1)
        prev_high = self.metar_service.get_daily_high(
            station_code=station_code,
            event_date=previous_day,
        )
        
        if not prev_high:
            return False, None
        
        # Get current temperature (from recent METAR)
        try:
            observations = self.metar_service.get_observations(
                station_code=station_code,
                event_date=event_day,
                hours=1,
            )
            
            if not observations:
                return False, None
            
            current_temp = observations[-1].temp_F
            
            # Check if current temp is close to previous day's high
            temp_diff = abs(current_temp - prev_high)
            
            if temp_diff < 1.0:  # Within 1°F of previous day's high
                return True, {
                    "previous_day_high": prev_high,
                    "current_temp": current_temp,
                    "temp_diff": temp_diff,
                    "hour": local_time.hour,
                }
        
        except Exception as e:
            logger.warning(f"Failed to get METAR for cross-day bleed: {e}")
            return False, None
        
        return False, None
    
    def calculate_bleed_adjustment(
        self,
        station_code: str,
        event_day: date,
        current_time: datetime,
        zeus_predicted_high: float,
    ) -> Tuple[float, str]:
        """Calculate adjustment for cross-day bleed.
        
        Strategy:
        - If early morning and temp near previous day's high
        - Traders might overreact and sell
        - But Zeus predicts higher afternoon high
        - This creates buying opportunity
        
        Args:
            station_code: Station code
            event_day: Event day
            current_time: Current time
            zeus_predicted_high: Zeus predicted daily high
        
        Returns:
            (adjustment, reason) tuple
        """
        is_bleeding, details = self.detect_cross_day_bleed(
            station_code, event_day, current_time
        )
        
        if not is_bleeding or not details:
            return 0.0, "no_bleed"
        
        prev_high = details["previous_day_high"]
        current_temp = details["current_temp"]
        hour = details["hour"]
        
        # If Zeus predicts higher than previous day's high
        if zeus_predicted_high > prev_high + 0.5:
            # Zeus expects higher high today
            # But traders might be confused by overnight temp
            # This is a buying opportunity
            
            # Adjustment increases with:
            # 1. How much higher Zeus predicts
            # 2. How early in the morning (earlier = more confusion)
            # 3. How close current temp is to previous high
            
            temp_premium = zeus_predicted_high - prev_high
            early_morning_factor = (6 - hour) / 6.0  # 1.0 at 00:00, 0.0 at 06:00
            confusion_factor = 1.0 - abs(current_temp - prev_high)  # Higher if temp matches
            
            adjustment = temp_premium * early_morning_factor * confusion_factor * 0.1  # Max 10%
            
            reason = f"cross_day_bleed_zeus_{zeus_predicted_high:.1f}_prev_{prev_high:.1f}"
            return adjustment, reason
        
        return 0.0, "no_bleed_opportunity"
```

---

### Phase 5: Integration with Edge Calculation

#### 5.1 Enhance Edge Calculation

**Modify**: `agents/edge_and_sizing.py`

```python
# Add imports
from agents.polymarket_rounding import calculate_rounding_risk_adjustment
from agents.metar_update_strategy import MetarUpdateStrategy
from agents.cross_day_bleed import CrossDayBleedAnalyzer

class Sizer:
    """Computes edge and sizes positions using Kelly criterion."""
    
    def __init__(self, ...):
        # ... existing init ...
        self.metar_strategy = MetarUpdateStrategy()
        self.bleed_analyzer = CrossDayBleedAnalyzer()
    
    def compute_edge(
        self,
        p_zeus: float,
        p_mkt: float,
        station_code: str = None,
        bracket: MarketBracket = None,
        current_time: datetime = None,
        metar_observations: List[MetarObservation] = None,
        zeus_predicted_high: float = None,
    ) -> Tuple[float, Dict[str, any]]:
        """Compute expected edge with microstructure adjustments.
        
        Args:
            p_zeus: Zeus-derived probability (0-1)
            p_mkt: Market-implied probability (0-1)
            station_code: Station code for rule lookup
            bracket: Market bracket for rounding analysis
            current_time: Current time for update window analysis
            metar_observations: Recent METAR observations
            zeus_predicted_high: Zeus predicted daily high
        
        Returns:
            (edge, adjustments) tuple where adjustments is dict of applied adjustments
        """
        # Base edge
        fee_decimal = self.fee_bp / 10000.0
        slip_decimal = self.slippage_bp / 10000.0
        base_edge = (p_zeus - p_mkt) - fee_decimal - slip_decimal
        
        adjustments = {
            "base_edge": base_edge,
            "rounding_adjustment": 0.0,
            "metar_adjustment": 0.0,
            "bleed_adjustment": 0.0,
            "total_adjustment": 0.0,
        }
        
        # 1. Rounding adjustment
        if bracket and station_code:
            bracket_lower = bracket.lower_F
            bracket_upper = bracket.upper_F
            bracket_mid = (bracket_lower + bracket_upper) / 2.0
            
            rounding_adj, rounding_reason = calculate_rounding_risk_adjustment(
                zeus_predicted_high or bracket_mid,
                bracket_lower,
                bracket_upper,
            )
            adjustments["rounding_adjustment"] = rounding_adj
            adjustments["rounding_reason"] = rounding_reason
        
        # 2. METAR update adjustment
        if station_code and current_time and metar_observations:
            # Analyze METAR trend
            if bracket:
                bracket_mid = (bracket.lower_F + bracket.upper_F) / 2.0
                metar_trend = self.metar_strategy.analyze_metar_trend(
                    metar_observations,
                    bracket_mid,
                )
            else:
                metar_trend = None
            
            metar_adj, metar_reason = self.metar_strategy.calculate_metar_update_adjustment(
                station_code,
                current_time,
                metar_trend,
                bracket_mid if bracket else None,
            )
            adjustments["metar_adjustment"] = metar_adj
            adjustments["metar_reason"] = metar_reason
        
        # 3. Cross-day bleed adjustment
        if station_code and current_time and zeus_predicted_high:
            from datetime import date
            event_day = current_time.date()
            
            bleed_adj, bleed_reason = self.bleed_analyzer.calculate_bleed_adjustment(
                station_code,
                event_day,
                current_time,
                zeus_predicted_high,
            )
            adjustments["bleed_adjustment"] = bleed_adj
            adjustments["bleed_reason"] = bleed_reason
        
        # Calculate total adjustment
        total_adj = (
            adjustments["rounding_adjustment"] +
            adjustments["metar_adjustment"] +
            adjustments["bleed_adjustment"]
        )
        adjustments["total_adjustment"] = total_adj
        
        # Apply adjustments to p_zeus
        p_zeus_adjusted = p_zeus + total_adj
        p_zeus_adjusted = max(0.0, min(1.0, p_zeus_adjusted))  # Clamp
        
        # Recalculate edge with adjusted probability
        adjusted_edge = (p_zeus_adjusted - p_mkt) - fee_decimal - slip_decimal
        
        logger.debug(
            f"Edge: p_zeus={p_zeus:.4f}, adj={total_adj:.4f}, "
            f"p_zeus_adj={p_zeus_adjusted:.4f}, p_mkt={p_mkt:.4f}, "
            f"edge={adjusted_edge:.4f}"
        )
        
        return adjusted_edge, adjustments
```

#### 5.2 Update Trading Engine

**Modify**: `agents/dynamic_trader/dynamic_engine.py`

```python
# In _evaluate_and_trade method, update edge calculation:

# 5. Calculate edges and sizes
logger.debug(f"     Calculating edges...")

# Get Zeus predicted high for adjustments
zeus_predicted_high = self.prob_mapper._compute_daily_high_mean(forecast)

decisions = []
for prob in probs_with_market:
    # Calculate edge with microstructure adjustments
    edge, adjustments = self.sizer.compute_edge(
        p_zeus=prob.p_zeus,
        p_mkt=prob.p_mkt,
        station_code=station.station_code,
        bracket=prob.bracket,
        current_time=cycle_time,
        metar_observations=metar_observations,
        zeus_predicted_high=zeus_predicted_high,
    )
    
    # Log adjustments if significant
    if abs(adjustments["total_adjustment"]) > 0.05:
        logger.info(
            f"     Adjustments for {prob.bracket.name}: "
            f"rounding={adjustments['rounding_adjustment']:.4f}, "
            f"metar={adjustments['metar_adjustment']:.4f}, "
            f"bleed={adjustments['bleed_adjustment']:.4f}"
        )
    
    # Continue with existing decision logic...
    if edge < self.sizer.edge_min:
        continue
    
    # ... rest of decision logic ...
```

---

## Implementation Stages

### Stage 1: Station Rules (Day 1)

**Tasks**:
1. Create `core/polymarket_station_rules.py`
2. Define `PolymarketStationRule` dataclass
3. Create registry with EGLC and KLGA rules
4. Test rule loading and timezone handling

**Time**: 2-3 hours

---

### Stage 2: Double Rounding (Day 1-2)

**Tasks**:
1. Create `agents/polymarket_rounding.py`
2. Implement `is_fragile_boundary()` function
3. Implement `get_fragile_boundary_adjustment()` function
4. Test with known fragile boundaries (50.95-51.05, etc.)

**Time**: 3-4 hours

---

### Stage 3: METAR Update Strategy (Day 2-3)

**Tasks**:
1. Create `agents/metar_update_strategy.py`
2. Implement `analyze_metar_trend()` function
3. Implement `calculate_metar_update_adjustment()` function
4. Implement `should_trade_before_update()` function
5. Test with historical METAR data

**Time**: 4-6 hours

---

### Stage 4: Cross-Day Bleed (Day 3-4)

**Tasks**:
1. Create `agents/cross_day_bleed.py`
2. Implement `detect_cross_day_bleed()` function
3. Implement `calculate_bleed_adjustment()` function
4. Test with known cross-day scenarios

**Time**: 3-4 hours

---

### Stage 5: Integration (Day 4-5)

**Tasks**:
1. Modify `agents/edge_and_sizing.py` to use adjustments
2. Update `agents/dynamic_trader/dynamic_engine.py` to pass context
3. Add logging for adjustments
4. Test full integration
5. Backtest with historical data

**Time**: 4-6 hours

---

### Stage 6: Testing & Tuning (Day 5-7)

**Tasks**:
1. Backtest with adjustments enabled
2. Compare performance: with vs without adjustments
3. Tune adjustment factors
4. Monitor live trading
5. Iterate based on results

**Time**: 6-8 hours

---

## Configuration

### Station Rules Configuration File

**File**: `data/registry/polymarket_station_rules.json`

```json
{
  "EGLC": {
    "station_code": "EGLC",
    "city": "London",
    "timezone": "Europe/London",
    "metar_update_times": [20, 50],
    "uses_double_rounding": true,
    "cross_day_bleed_risk": true
  },
  "KLGA": {
    "station_code": "KLGA",
    "city": "New York (Airport)",
    "timezone": "America/New_York",
    "metar_update_times": [50],
    "uses_double_rounding": true,
    "cross_day_bleed_risk": true
  }
}
```

---

## Testing Strategy

### Unit Tests

1. **Rounding Tests**:
   - Test fragile boundary detection
   - Test adjustment calculations
   - Test edge cases (exactly 0.5, etc.)

2. **METAR Update Tests**:
   - Test update window detection
   - Test trend analysis
   - Test adjustment calculations

3. **Cross-Day Bleed Tests**:
   - Test bleed detection
   - Test adjustment calculations
   - Test edge cases

### Integration Tests

1. **Full Trading Cycle**:
   - Test with all adjustments enabled
   - Verify edge calculations
   - Verify logging

2. **Historical Backtest**:
   - Run backtest with adjustments
   - Compare to baseline
   - Measure performance improvement

---

## Expected Outcomes

### Performance Improvements

1. **Better Edge Detection**:
   - Account for rounding uncertainty
   - Anticipate METAR updates
   - Exploit cross-day mispricing

2. **Higher Win Rate**:
   - Trade on microstructure edges
   - Avoid fragile boundaries when risky
   - Capitalize on update windows

3. **Reduced Risk**:
   - Identify fragile boundaries
   - Avoid trading during high uncertainty
   - Better position sizing

---

## Summary

**Current State**: Simple edge calculation, no microstructure awareness

**Proposed State**: 
- Station-specific rules (METAR update times)
- Double rounding adjustments
- Fragile boundary detection
- METAR update window strategy
- Cross-day bleed handling

**Implementation Time**: 5-7 days

**Priority**: High - Addresses critical Polymarket microstructure issues

---

**Status**: 📋 **Implementation Plan Created** - Ready for staged implementation

