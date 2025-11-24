# METAR Daily High Fix - Only Include Data Within Event Day

**Date**: 2025-11-21  
**Issue**: Daily high calculation includes observations from previous day (e.g., 23:50 on Nov 15 counted for Nov 16)  
**Priority**: **CRITICAL** - Must only use data from within the event day (00:00-23:59 UTC)

---

## Problem

**Current Behavior**:
- Daily high for Nov 16 includes observation at **23:50 UTC on Nov 15** (51.8°F)
- This observation is **outside** the event day (Nov 16 00:00-23:59)
- Graph shows Nov 16 00:00-23:00, but daily high shows 51.8°F which isn't on the graph

**Example**:
- Event day: 2025-11-16
- Observation: 2025-11-15T23:50:00+00:00 → 51.8°F
- **This should NOT be included** in Nov 16's daily high

---

## Root Cause

The `get_daily_high()` method in `backend/api/services/metar_service.py` gets all observations from the event day directory, but **doesn't filter by observation time**. 

Files are stored in directories by event day, but observations within those files might have timestamps from the previous day (late-night observations).

---

## Solution

**Filter observations to only include those within the event day (00:00:00 to 23:59:59 UTC)**.

### File to Modify

**`backend/api/services/metar_service.py`** - Method: `get_daily_high()`

### Code Change

**Current Code** (lines 79-98):
```python
# Get observations
observations = self.get_observations(
    station_code=station_code,
    event_day=event_day,
)

if not observations:
    return None

# Extract temperatures
temps = [
    obs.get("temp_F")
    for obs in observations
    if obs.get("temp_F") is not None
]

if not temps:
    return None

daily_high = max(temps)
```

**Fixed Code**:
```python
# Get observations
observations = self.get_observations(
    station_code=station_code,
    event_day=event_day,
)

if not observations:
    return None

# CRITICAL FIX: Filter to only include observations within event day (00:00-23:59 UTC)
from datetime import datetime, timezone

event_day_start = datetime.combine(event_day, datetime.min.time(), tzinfo=timezone.utc)
event_day_end = datetime.combine(event_day, datetime.max.time().replace(microsecond=0), tzinfo=timezone.utc)

filtered_observations = []
for obs in observations:
    obs_time_str = obs.get("observation_time_utc", "")
    if not obs_time_str:
        continue
    
    obs_time = parse_timestamp(obs_time_str)
    if obs_time is None:
        continue
    
    # Only include if observation is within event day (00:00:00 to 23:59:59 UTC)
    if event_day_start <= obs_time <= event_day_end:
        filtered_observations.append(obs)

if not filtered_observations:
    return None

# Extract temperatures from filtered observations
temps = [
    obs.get("temp_F")
    for obs in filtered_observations
    if obs.get("temp_F") is not None
]

if not temps:
    return None

daily_high = max(temps)
```

---

## Alternative: Simpler Filter

If you prefer a simpler approach using date comparison:

```python
# Get observations
observations = self.get_observations(
    station_code=station_code,
    event_day=event_day,
)

if not observations:
    return None

# CRITICAL FIX: Filter to only include observations within event day
filtered_observations = []
for obs in observations:
    obs_time_str = obs.get("observation_time_utc", "")
    if not obs_time_str:
        continue
    
    obs_time = parse_timestamp(obs_time_str)
    if obs_time is None:
        continue
    
    # Only include if observation date matches event day (UTC)
    if obs_time.date() == event_day:
        filtered_observations.append(obs)

if not filtered_observations:
    return None

# Extract temperatures from filtered observations
temps = [
    obs.get("temp_F")
    for obs in filtered_observations
    if obs.get("temp_F") is not None
]

if not temps:
    return None

daily_high = max(temps)
```

**This simpler approach** just checks if `obs_time.date() == event_day`, which ensures only observations from the exact event day are included.

---

## Testing

### Test Case 1: Nov 16, 2025 (Known Issue)

**Before Fix**:
- Daily high: 51.8°F (includes 23:50 Nov 15 observation)
- Observations included: 48 (includes Nov 15 23:50)

**After Fix**:
- Daily high: 50.0°F (max within Nov 16 00:00-23:59)
- Observations included: 47 (excludes Nov 15 23:50)

**Expected Result**:
```json
{
  "station_code": "EGLC",
  "event_day": "2025-11-16",
  "daily_high_f": 50.0,
  "available": true
}
```

### Test Case 2: Normal Day (No Late-Night Observations)

**Before Fix**: Works correctly (no late-night observations)

**After Fix**: Still works correctly (filter doesn't exclude valid data)

### Test Case 3: Edge Case - First Observation at 00:00

**Test**: Event day with first observation exactly at 00:00:00 UTC

**Expected**: Should be included (within event day)

---

## Impact

### API Endpoints Affected

1. **`GET /api/metar/daily-high`** - Will return correct daily high
2. **`GET /api/compare/zeus-vs-metar`** - Will use correct daily high for comparison

### Frontend Impact

**Before Fix**:
- Daily high: 51.8°F (not visible on graph)
- Graph shows: Max ~50.0°F
- **Mismatch**: Daily high doesn't match graph

**After Fix**:
- Daily high: 50.0°F (matches graph)
- Graph shows: Max ~50.0°F
- **Match**: Daily high matches graph ✅

---

## Cache Consideration

**Important**: The daily high is cached. After this fix:

1. **Clear cache** for affected dates (or restart backend)
2. **Or** add cache invalidation when fix is deployed

**Cache key**: `(station_code, event_day.isoformat())`

**To clear cache**:
```python
metar_service.clear_cache()
```

---

## Verification

After deploying the fix, verify:

```bash
# Test Nov 16, 2025
curl "http://localhost:8000/api/metar/daily-high?station_code=EGLC&event_day=2025-11-16"

# Should return:
# {
#   "daily_high_f": 50.0,  # NOT 51.8
#   "available": true
# }
```

---

## Summary

**Change**: Filter observations to only include those where `observation_time_utc.date() == event_day`

**Location**: `backend/api/services/metar_service.py` - `get_daily_high()` method

**Time Estimate**: 15-30 minutes

**Priority**: **CRITICAL** - This is causing data mismatch between graph and daily high display

---

**Status**: 📋 **Ready for Implementation** - Critical fix to ensure daily high only uses data from within event day

