# Daily High Prediction Accuracy Enhancement Plan

**Date**: 2025-11-21  
**Purpose**: Enhance the "Daily High Prediction Accuracy" card to show rounded degree, winning bracket, and correct/incorrect status

---

## Current State

**Current Display**:
- Predicted High: 46.3°F
- Actual High: 46.4°F
- Error: +0.1°F (Accurate) ✅
- Final Forecast Age: 23.8 hours before event ❌ (REMOVE)
- Forecast Stability: ±0.0°F ❌ (REMOVE)

---

## Desired State

**New Display**:
- Predicted High: 46.3°F
- Actual High: 46.4°F
- **Rounded Prediction: 46°F** ⭐ (NEW)
- **Winning Bracket: 46-47°F** ⭐ (NEW)
- **Correct/Incorrect: ✅ Correct** ⭐ (NEW - MAIN INDICATOR)
- Error: +0.1°F (secondary, smaller)

**Priority**:
- **Primary**: Correct/Incorrect status (was rounded prediction in winning bracket?)
- **Secondary**: Error difference (raw temperature error)

---

## Data Requirements

### 1. Rounded Prediction

**Calculation**:
```python
from core.units import resolve_to_whole_f

predicted_high_f = 46.3  # From Zeus forecast
rounded_prediction = resolve_to_whole_f(predicted_high_f)  # 46
```

**Logic**: Round predicted high to nearest whole degree using `resolve_to_whole_f()` (same as Polymarket/Wunderground rounding)

---

### 2. Winning Bracket

**Source**: Historical data - we know which bracket won because it's resolved

**How to Get** (in priority order):

1. **From Event Snapshots using 1/0 Method** (PRIMARY - Most Reliable):
   ```python
   # Get event snapshot (saved when we discovered markets)
   # Event snapshots are in: data/snapshots/polymarket/events/
   # They contain markets with outcomePrices field
   
   from venues.polymarket.resolution import PolyResolution
   from venues.polymarket.discovery import PolyDiscovery
   from pathlib import Path
   import json
   
   resolver = PolyResolution()
   discovery = PolyDiscovery()
   
   # Get city from station
   from core.registry import StationRegistry
   registry = StationRegistry()
   station = registry.get_station(station_code)
   city = station.city if station else None
   
   if city:
       # Generate event slug (e.g., "highest-temperature-in-london-on-november-16")
       slugs = discovery._generate_event_slugs(city, event_day)
       if slugs:
           slug = slugs[0]
           
           # Try to load event snapshot from disk first
           event_snapshot_path = Path("data/snapshots/polymarket/events") / f"{slug.replace('/', '_')}.json"
           
           if event_snapshot_path.exists():
               with open(event_snapshot_path, 'r') as f:
                   event = json.load(f)
               # Use 1/0 method: outcomePrices[0] == "1" means Yes won
               winner_bracket = resolver.get_winner_from_event(event)
           else:
               # Fallback: fetch from API (if still available)
               event = discovery.get_event_by_slug(slug, save_snapshot=False)
               if event:
                   winner_bracket = resolver.get_winner_from_event(event)
   ```

2. **From Resolved Trades** (Fallback - if event snapshot not available):
   ```python
   # Get trades for event day/station
   trades = trade_service.get_trades(
       trade_date=event_day,
       station_code=station_code
   )
   
   # Find resolved trade with winner_bracket
   winner_bracket = None
   for trade in trades:
       if trade.winner_bracket:
           winner_bracket = trade.winner_bracket  # e.g., "46-47°F"
           break
   ```

**The 1/0 Method** (PRIMARY):
- Polymarket stores `outcomePrices` as `["1", "0"]` or `["0", "1"]`
- `outcomePrices[0] == "1"` means the "Yes" outcome won (that bracket is the winner)
- `outcomePrices[0] == "0"` means the "Yes" outcome lost
- We iterate through markets and find the one where `outcomePrices[0] == "1"`, then parse the bracket from the question
- **Why Primary**: Markets don't fully resolve for days in backend, so resolved trades may not have `winner_bracket` populated yet. Event snapshots are saved immediately when markets are discovered and contain the resolution data.

**Note**: Event snapshots are saved when we discover markets, so they should be available for historical dates. This is the most reliable source for winning brackets.

---

### 3. Correct/Incorrect Determination

**Logic**:
```python
# Check if rounded prediction falls within winning bracket
def is_correct(rounded_prediction: int, winner_bracket: str) -> bool:
    """
    Args:
        rounded_prediction: Rounded temperature (e.g., 46)
        winner_bracket: Winning bracket string (e.g., "46-47°F")
    
    Returns:
        True if rounded prediction is in winning bracket
    """
    # Parse bracket bounds
    # Format: "46-47°F" or "46–47°F" (en dash) or "46 to 47°F"
    import re
    match = re.search(r'(\d+)\s*[-–—]\s*(\d+)', winner_bracket)
    if match:
        lower = int(match.group(1))
        upper = int(match.group(2))
        
        # Check if rounded prediction is in bracket [lower, upper)
        # Bracket is lower-inclusive, upper-exclusive
        return lower <= rounded_prediction < upper
    
    return False
```

**Example**:
- Rounded Prediction: 46°F
- Winning Bracket: "46-47°F" (lower=46, upper=47)
- Check: `46 <= 46 < 47` → ✅ **Correct**

**Another Example**:
- Rounded Prediction: 45°F
- Winning Bracket: "46-47°F" (lower=46, upper=47)
- Check: `46 <= 45 < 47` → ❌ **Incorrect**

---

## Backend Changes

### 1. Enhance `compare_zeus_vs_metar` Endpoint

**File**: `backend/api/services/metar_service.py`

**Current Method**: `compare_zeus_vs_metar()`

**Enhancement**: Add rounded prediction, winning bracket, and correct/incorrect status

**New Return Fields**:
```python
{
    # Existing fields
    "zeus_prediction_f": 46.3,
    "metar_actual_f": 46.4,
    "error_f": 0.1,
    "error_pct": 0.22,
    
    # New fields
    "rounded_prediction_f": 46,  # ⭐ NEW
    "rounded_actual_f": 46,      # ⭐ NEW (for consistency)
    "winning_bracket": "46-47°F", # ⭐ NEW
    "is_correct": True,          # ⭐ NEW (main indicator)
    "correctness_status": "Correct",  # ⭐ NEW ("Correct" or "Incorrect")
}
```

**Implementation**:
```python
def compare_zeus_vs_metar(
    self,
    station_code: str,
    event_day: Optional[date] = None,
) -> Optional[Dict[str, Any]]:
    # ... existing code ...
    
    # Get rounded predictions
    from core.units import resolve_to_whole_f
    rounded_prediction = resolve_to_whole_f(zeus_high)
    rounded_actual = resolve_to_whole_f(metar_high)
    
    # Get winning bracket (PRIMARY: 1/0 method from event snapshots)
    winner_bracket = None
    
    # Method 1: From event snapshots using 1/0 method (PRIMARY)
    # This is primary because markets don't fully resolve for days in backend
    from core.registry import StationRegistry
    from venues.polymarket.discovery import PolyDiscovery
    from venues.polymarket.resolution import PolyResolution
    from pathlib import Path
    import json
    
    registry = StationRegistry()
    station = registry.get_station(station_code)
    
    if station:
        city = station.city
        discovery = PolyDiscovery()
        resolver = PolyResolution()
        
        # Generate event slug (e.g., "highest-temperature-in-london-on-november-16")
        slugs = discovery._generate_event_slugs(city, event_day)
        if slugs:
            slug = slugs[0]
            
            # Try to load event snapshot from disk first
            event_snapshot_path = PROJECT_ROOT / "data" / "snapshots" / "polymarket" / "events" / f"{slug.replace('/', '_')}.json"
            
            if event_snapshot_path.exists():
                with open(event_snapshot_path, 'r') as f:
                    event = json.load(f)
                # Use 1/0 method: outcomePrices[0] == "1" means Yes won
                winner_bracket = resolver.get_winner_from_event(event)
            else:
                # Fallback: fetch from API (if still available)
                event = discovery.get_event_by_slug(slug, save_snapshot=False)
                if event:
                    winner_bracket = resolver.get_winner_from_event(event)
    
    # Method 2: From resolved trades (FALLBACK - if event snapshot not available)
    if not winner_bracket:
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
            is_correct = lower <= rounded_prediction < upper
            correctness_status = "Correct" if is_correct else "Incorrect"
    
    return {
        # ... existing fields ...
        "rounded_prediction_f": rounded_prediction,
        "rounded_actual_f": rounded_actual,
        "winning_bracket": winner_bracket,
        "is_correct": is_correct,
        "correctness_status": correctness_status,
    }
```

---

### 2. Alternative: New Endpoint

**If we want to keep `compare_zeus_vs_metar` unchanged**, create new endpoint:

**File**: `backend/api/routes/compare.py` or `backend/api/routes/performance.py`

**Endpoint**: `GET /api/performance/prediction-accuracy?station_code={STATION}&event_day={DATE}`

**Returns**: Enhanced accuracy data with rounded prediction, winning bracket, correct/incorrect

---

## Frontend Changes

### 1. Update Display Layout

**New Layout** (priority order):

```
┌─────────────────────────────────────────┐
│ Daily High Prediction Accuracy          │
├─────────────────────────────────────────┤
│                                         │
│ Predicted High: 46.3°F                  │
│ Actual High: 46.4°F                     │
│                                         │
│ Rounded Prediction: 46°F               │
│ Winning Bracket: 46-47°F                 │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ ✅ Correct                          │ │ ← MAIN INDICATOR (large, prominent)
│ └─────────────────────────────────────┘ │
│                                         │
│ Error: +0.1°F                           │ ← Secondary (smaller)
│                                         │
└─────────────────────────────────────────┘
```

### 2. Visual Design

**Correct/Incorrect Indicator**:
- **Large, prominent** (main focus)
- **Green checkmark** (✅) for Correct
- **Red X** (❌) for Incorrect
- **Bold text**: "Correct" or "Incorrect"
- **Background color**: Light green for correct, light red for incorrect

**Error Display**:
- **Smaller font** (secondary)
- **Same color coding** as before (green/yellow/red based on error magnitude)
- **Position**: Below main indicator

**Rounded Prediction & Winning Bracket**:
- **Medium prominence** (between main and secondary)
- **Clear labels**: "Rounded Prediction:" and "Winning Bracket:"
- **Format**: "46°F" and "46-47°F"

---

## Implementation Steps

### Step 1: Backend Enhancement

1. **Modify `MetarService.compare_zeus_vs_metar()`**:
   - Add `resolve_to_whole_f()` import
   - Calculate rounded prediction and rounded actual
   - **Get winning bracket from event snapshots using 1/0 method (PRIMARY)**
   - Fallback to resolved trades if event snapshot not available
   - Determine correct/incorrect status
   - Add new fields to return dict

2. **Test Backend**:
   - Test with known data (event day with event snapshots)
   - Verify rounded prediction calculation
   - Verify winning bracket extraction from event snapshots (1/0 method)
   - Verify fallback to resolved trades
   - Verify correct/incorrect logic

**Time**: 2-3 hours

---

### Step 2: Frontend Update

1. **Update API Call**:
   - Call `/api/compare/zeus-vs-metar` (or new endpoint)
   - Extract new fields: `rounded_prediction_f`, `winning_bracket`, `is_correct`, `correctness_status`

2. **Update Display**:
   - Remove "Final Forecast Age" and "Forecast Stability"
   - Add "Rounded Prediction" and "Winning Bracket"
   - Add prominent "Correct/Incorrect" indicator
   - Make error display smaller/secondary

3. **Styling**:
   - Style correct/incorrect indicator (large, prominent, color-coded)
   - Adjust error display (smaller, secondary)
   - Ensure good visual hierarchy

**Time**: 3-4 hours

---

## Edge Cases

### 1. No Winning Bracket Available

**Scenario**: Event not yet resolved, or no trades for that event

**Handling**:
- Show "Winning Bracket: Not Available"
- Show "Correct/Incorrect: Unknown"
- Still show rounded prediction and error

---

### 2. Bracket Format Variations

**Scenario**: Bracket names might vary (e.g., "46-47°F", "46–47°F", "46 to 47°F")

**Handling**:
- Use regex to parse bracket bounds (already in code)
- Normalize bracket names for comparison
- Handle edge cases (≤, ≥, etc.)

---

### 3. Rounded Prediction at Bracket Boundary

**Scenario**: Rounded prediction exactly equals bracket upper bound

**Example**: Rounded = 47°F, Bracket = "46-47°F" (lower=46, upper=47)

**Handling**:
- Bracket is `[lower, upper)` (lower-inclusive, upper-exclusive)
- `46 <= 47 < 47` → False (not in bracket)
- This is correct behavior (47°F is in next bracket: "47-48°F")

---

## Testing

### Test Cases

1. **Correct Prediction**:
   - Predicted: 46.3°F → Rounded: 46°F
   - Winning Bracket: "46-47°F"
   - Expected: ✅ Correct

2. **Incorrect Prediction**:
   - Predicted: 45.8°F → Rounded: 46°F
   - Winning Bracket: "45-46°F"
   - Expected: ❌ Incorrect (46°F is not in [45, 46))

3. **Boundary Case**:
   - Predicted: 46.9°F → Rounded: 47°F
   - Winning Bracket: "46-47°F"
   - Expected: ❌ Incorrect (47°F is not in [46, 47))

4. **No Winner Available**:
   - Predicted: 46.3°F → Rounded: 46°F
   - Winning Bracket: None
   - Expected: "Unknown" status

---

## API Response Example

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
  "winning_bracket": "46-47°F",
  "is_correct": true,
  "correctness_status": "Correct",
  "zeus_forecast_time": "2025-11-16T00:15:00+00:00",
  "metar_observation_count": 48
}
```

---

## Summary

**Changes**:
1. ✅ Add rounded prediction calculation
2. ✅ Get winning bracket from resolved trades
3. ✅ Determine correct/incorrect status
4. ✅ Update backend API response
5. ✅ Update frontend display (remove old fields, add new fields)
6. ✅ Make correct/incorrect the main indicator
7. ✅ Make error secondary

**Priority**:
- **Primary**: Correct/Incorrect status (main focus)
- **Secondary**: Error difference (smaller, less prominent)

**Time Estimate**:
- Backend: 2-3 hours
- Frontend: 3-4 hours
- **Total**: 5-7 hours

---

**Status**: 📋 **Plan Created** - Ready for implementation

