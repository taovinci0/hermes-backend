# Winning Bracket Backend Fix

**Date**: 2025-11-21  
**Issue**: Frontend showing "Winning Bracket: Not Available"  
**Solution**: Implement 1/0 method from event snapshots to get winning bracket

---

## Current Problem

The `/api/compare/zeus-vs-metar` endpoint is not returning `winning_bracket`, causing the frontend to display "Winning Bracket: Not Available".

**Current API Response**:
```json
{
  "zeus_prediction_f": 46.3,
  "metar_actual_f": 46.4,
  "error_f": 0.1,
  "winning_bracket": null,  // ❌ Not available
  "is_correct": null,
  "correctness_status": "Unknown"
}
```

---

## Solution

**Use the 1/0 method from event snapshots** to determine the winning bracket. This is the PRIMARY method because:
- Markets don't fully resolve for days in backend
- Event snapshots are saved immediately when markets are discovered
- Event snapshots contain `outcomePrices` which show resolution (1 = won, 0 = lost)

---

## Implementation

### File to Modify

**`backend/api/services/metar_service.py`** - Method: `compare_zeus_vs_metar()`

### Changes Needed

Add code to get winning bracket from event snapshots using the 1/0 method.

### Code to Add

Add this code **after** calculating `rounded_prediction` and `rounded_actual`:

```python
# Get winning bracket (PRIMARY: 1/0 method from event API)
# This uses the EXACT same pattern as backtester.py and trade_resolution_service.py
winner_bracket = None

try:
    from core.registry import StationRegistry
    from venues.polymarket.discovery import PolyDiscovery
    from venues.polymarket.resolution import PolyResolution
    import sys
    from pathlib import Path
    
    # Add project root to path for imports
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    
    registry = StationRegistry()
    station = registry.get_station(station_code)
    
    if station:
        city = station.city
        discovery = PolyDiscovery()
        resolver = PolyResolution()
        
        # Generate event slug (same as backtester/trade_resolution)
        event_slug = discovery._generate_event_slugs(city, event_day)
        
        # Try each slug until we find an event (EXACT same pattern as working code)
        event = None
        for slug in event_slug:
            event = discovery.get_event_by_slug(slug, save_snapshot=False)
            if event:
                break
        
        if event:
            # Find winner using outcomePrices (EXACT same method as backtester/trade_resolution)
            winner_bracket = resolver.get_winner_from_event(event)
except Exception as e:
    # Log but don't fail - just won't have winning bracket
    logger.warning(f"Failed to get winning bracket: {e}")

# Method 2: From resolved trades (FALLBACK - if event API call fails)
if not winner_bracket:
    try:
        from ..services.trade_service import TradeService
        trade_service = TradeService()
        trades = trade_service.get_trades(
            trade_date=event_day,
            station_code=station_code
        )
        
        for trade in trades:
            if trade.winner_bracket:
                winner_bracket = trade.winner_bracket
                break
    except Exception as e:
        logger.debug(f"Failed to get winner from trades: {e}")
```

### Then Add Correct/Incorrect Logic

Add this code **after** getting `winner_bracket`:

```python
# Determine if correct
is_correct = False
correctness_status = "Unknown"

if winner_bracket:
    # Parse bracket bounds
    import re
    match = re.search(r'(\d+)\s*[-–—]\s*(\d+)', winner_bracket)
    if match:
        lower = int(match.group(1))
        upper = int(match.group(2))
        # Check if rounded prediction is in bracket [lower, upper)
        # Bracket is lower-inclusive, upper-exclusive
        is_correct = lower <= rounded_prediction < upper
        correctness_status = "Correct" if is_correct else "Incorrect"
```

### Update Return Dictionary

Add these fields to the return dictionary:

```python
return {
    # ... existing fields ...
    "rounded_prediction_f": rounded_prediction,
    "rounded_actual_f": rounded_actual,
    "winning_bracket": winner_bracket,  # ⭐ NEW
    "is_correct": is_correct,           # ⭐ NEW
    "correctness_status": correctness_status,  # ⭐ NEW
}
```

---

## Expected API Response

**After fix**:
```json
{
  "station_code": "EGLC",
  "event_day": "2025-11-16",
  "zeus_prediction_f": 46.3,
  "metar_actual_f": 46.4,
  "error_f": 0.1,
  "error_pct": 0.22,
  "rounded_prediction_f": 46,
  "rounded_actual_f": 46,
  "winning_bracket": "46-47°F",  // ✅ Now available
  "is_correct": true,             // ✅ Now available
  "correctness_status": "Correct", // ✅ Now available
  "zeus_forecast_time": "2025-11-16T00:15:00+00:00",
  "metar_observation_count": 48
}
```

---

## How the 1/0 Method Works

1. **Event snapshots** are saved in `data/snapshots/polymarket/events/` when markets are discovered
2. Each event contains **markets** with `outcomePrices` field
3. `outcomePrices` is an array like `["1", "0"]` or `["0", "1"]`
4. **Index 0** represents the "Yes" outcome
5. If `outcomePrices[0] == "1"`, that bracket **won**
6. If `outcomePrices[0] == "0"`, that bracket **lost**
7. We iterate through markets to find the one where `outcomePrices[0] == "1"`, then parse the bracket name from the question

**Example**:
```json
{
  "markets": [
    {
      "question": "Will the temperature be between 46-47°F?",
      "outcomePrices": ["1", "0"]  // ← "1" means Yes won
    },
    {
      "question": "Will the temperature be between 47-48°F?",
      "outcomePrices": ["0", "1"]  // ← "0" means Yes lost
    }
  ]
}
```

In this example, "46-47°F" is the winning bracket.

---

## Testing

### Test Case 1: Event Snapshot Exists

**Setup**:
- Event snapshot exists: `data/snapshots/polymarket/events/highest-temperature-in-london-on-november-16.json`
- Snapshot contains markets with `outcomePrices`

**Expected**:
- `winning_bracket` is populated (e.g., "46-47°F")
- `is_correct` is calculated
- `correctness_status` is "Correct" or "Incorrect"

### Test Case 2: Event Snapshot Missing, But Resolved Trade Exists

**Setup**:
- Event snapshot does not exist
- Resolved trade exists with `winner_bracket` field

**Expected**:
- Falls back to resolved trade
- `winning_bracket` is populated from trade
- `is_correct` is calculated

### Test Case 3: No Data Available

**Setup**:
- Event snapshot does not exist
- No resolved trades

**Expected**:
- `winning_bracket` is `null`
- `is_correct` is `false`
- `correctness_status` is "Unknown"

---

## File Locations

**Event Snapshots**: `data/snapshots/polymarket/events/{slug}.json`

**Example slug**: `highest-temperature-in-london-on-november-16`

**Filename**: `highest-temperature-in-london-on-november-16.json`

---

## Error Handling

The code includes try/except blocks to handle:
- Missing event snapshot files
- Invalid JSON in event snapshots
- API failures when fetching events
- Missing station in registry
- Invalid bracket parsing

All errors are logged as warnings and the code continues to try fallback methods.

---

## Dependencies

**Required imports** (already available):
- `core.registry.StationRegistry` - Get station/city info
- `venues.polymarket.discovery.PolyDiscovery` - Generate event slugs
- `venues.polymarket.resolution.PolyResolution` - Parse winner from event
- `core.config.PROJECT_ROOT` - Get project root path

**No new dependencies needed** - all required code already exists.

---

## Summary

**What to do**:
1. Add code to load event snapshot from disk
2. Use `PolyResolution.get_winner_from_event()` to parse winner using 1/0 method
3. Fallback to resolved trades if event snapshot not available
4. Calculate correct/incorrect based on rounded prediction vs winning bracket
5. Return new fields in API response

**Time Estimate**: 1-2 hours

**Priority**: High (frontend is waiting for this data)

---

**Status**: 📋 **Ready for Implementation** - Backend fix needed to provide winning bracket data to frontend

