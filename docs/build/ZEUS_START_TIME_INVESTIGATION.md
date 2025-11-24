# Zeus Start Time Investigation

**Date**: 2025-11-21  
**Purpose**: Investigate how we call Zeus with start times for London and NYC, and whether shifting start time would improve accuracy

---

## Current Implementation

### Code Flow

**File**: `agents/dynamic_trader/fetchers.py` - Method: `fetch_zeus_jit()`

**Step 1: Calculate Local Midnight**
```python
# Get local midnight for the event day (NO UTC conversion!)
local_midnight = datetime.combine(
    event_day,
    time(0, 0),
    tzinfo=ZoneInfo(station.time_zone)
)
```

**Step 2: Send to Zeus API**
```python
forecast = self.zeus.fetch(
    lat=station.lat,
    lon=station.lon,
    start_utc=local_midnight,  # Actually local, not UTC (param name is legacy)
    hours=24,
    station_code=station.station_code,
)
```

**Step 3: Format for API Call**
**File**: `agents/zeus_forecast.py` - Method: `_call_zeus_api()`

```python
# Format datetime for API - preserve timezone if present
if start_utc.tzinfo is not None:
    # Has timezone - use ISO format to preserve it
    start_time_str = start_utc.isoformat()
else:
    # No timezone - assume UTC and format with Z
    start_time_str = start_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
```

---

## Exact Start Times for London and NYC

### London (EGLC)

**Station Configuration**:
- **Timezone**: `Europe/London`
- **In November**: GMT (UTC+0, no DST)

**For Event Day: 2025-11-16**:
```python
event_day = date(2025, 11, 16)
local_midnight = datetime.combine(
    event_day,
    time(0, 0),
    tzinfo=ZoneInfo('Europe/London')
)
# Result: 2025-11-16T00:00:00+00:00
```

**Sent to Zeus API**:
```
start_time=2025-11-16T00:00:00+00:00
```

**UTC Equivalent**: `2025-11-16T00:00:00+00:00` (same, GMT = UTC in November)

---

### New York (KLGA)

**Station Configuration**:
- **Timezone**: `America/New_York`
- **In November**: EST (UTC-5, no DST)

**For Event Day: 2025-11-16**:
```python
event_day = date(2025, 11, 16)
local_midnight = datetime.combine(
    event_day,
    time(0, 0),
    tzinfo=ZoneInfo('America/New_York')
)
# Result: 2025-11-16T00:00:00-05:00
```

**Sent to Zeus API**:
```
start_time=2025-11-16T00:00:00-05:00
```

**UTC Equivalent**: `2025-11-16T05:00:00+00:00` (5 hours later)

---

## What Zeus API Receives

### London Example
```
GET /forecast?latitude=51.505&longitude=0.05&start_time=2025-11-16T00:00:00+00:00&predict_hours=24
```

**Zeus interprets**: Forecast starting at midnight GMT (00:00 UTC)

**Zeus returns**: 24 hourly points from 00:00 UTC to 23:00 UTC

---

### NYC Example
```
GET /forecast?latitude=40.776&longitude=-73.874&start_time=2025-11-16T00:00:00-05:00&predict_hours=24
```

**Zeus interprets**: Forecast starting at midnight EST (00:00 EST = 05:00 UTC)

**Zeus returns**: 24 hourly points from 05:00 UTC to 04:00 UTC (next day)

---

## Investigation: Would Shifting Start Time Improve Accuracy?

### Hypothesis

**Current**: We start forecast at local midnight (00:00 local time)

**Question**: Would starting earlier (e.g., 22:00 or 23:00 previous day) improve accuracy?

**Reasoning**: 
- Daily high typically occurs in afternoon (14:00-16:00)
- Starting forecast earlier might capture more of the temperature pattern
- Or starting later might be more accurate for the actual event day

---

## Analysis: London Nov 16, 2025

### Current Forecast (Starting at 00:00)

**Zeus Prediction**:
- 00:00 → 51.5°F (HIGHEST)
- 01:00 → 51.1°F
- ... (decreasing)
- 23:00 → 42.8°F (LOWEST)

**Actual METAR**:
- Daily high: 50.0°F (within Nov 16 00:00-23:59)
- Pattern: Constant 50.0°F until 15:50, then drops

**Issue**: 
- Zeus predicts high at 00:00 (51.5°F)
- Actual high was 50.0°F (constant through early afternoon)
- Zeus pattern is backwards (high at start, low at end)

### If We Started Earlier (e.g., 22:00 Previous Day)

**Hypothetical Start**: `2025-11-15T22:00:00+00:00`

**What This Would Do**:
- Forecast would start 2 hours before event day
- Would include late-night temperatures from Nov 15
- Might better capture the temperature transition

**Potential Benefit**:
- Could capture the actual pattern (warm at night, constant during day, cool in evening)
- Might align better with actual observations

**Potential Drawback**:
- Forecast would include data from previous day
- Event day resolution is based on Nov 16 only

---

## Analysis: NYC (Hypothetical)

### Current Forecast (Starting at 00:00 EST = 05:00 UTC)

**Zeus Prediction**: Starts at 05:00 UTC (midnight EST)

**If We Started Earlier**:
- Start at 22:00 EST previous day = 03:00 UTC
- Would include late-night temperatures
- Might better capture daily pattern

---

## Key Questions

### 1. What Does Zeus API Actually Do?

**Question**: When we send `start_time=2025-11-16T00:00:00-05:00`, does Zeus:
- A) Return forecast starting at that exact time (00:00 EST)?
- B) Convert to UTC and return forecast starting at 05:00 UTC?
- C) Return forecast for that timezone's day?

**Need to verify**: Check Zeus API documentation or test with different start times.

---

### 2. What Time Does Daily High Actually Occur?

**London Nov 16**:
- **Actual**: Constant 50.0°F from 00:20 to 15:50 (no clear peak)
- **Zeus predicted**: High at 00:00 (51.5°F)

**Typical Pattern** (most days):
- Low at midnight (~45°F)
- Increasing through morning
- **High in afternoon** (14:00-16:00, ~52°F)
- Decreasing in evening

**Nov 16 was unusual**: No afternoon peak, constant temperature.

---

### 3. Would Shifting Help?

**Option A: Start Earlier (22:00-23:00 Previous Day)**
- **Pros**: Might capture temperature transition better
- **Cons**: Includes previous day data, might confuse event day boundaries

**Option B: Start Later (06:00-08:00 Event Day)**
- **Pros**: Focuses on event day only, might be more accurate for daily high
- **Cons**: Misses early morning temperatures

**Option C: Keep Current (00:00 Event Day)**
- **Pros**: Clean event day boundary, standard approach
- **Cons**: Might miss temperature patterns that span midnight

---

## Recommendations for Investigation

### Test 1: Verify Zeus API Behavior

**Test different start times**:
```python
# Test 1: Current (midnight)
start1 = "2025-11-16T00:00:00+00:00"  # London
start2 = "2025-11-16T00:00:00-05:00"  # NYC

# Test 2: Earlier (22:00 previous day)
start3 = "2025-11-15T22:00:00+00:00"  # London
start4 = "2025-11-15T22:00:00-05:00"  # NYC

# Test 3: Later (06:00 event day)
start5 = "2025-11-16T06:00:00+00:00"  # London
start6 = "2025-11-16T06:00:00-05:00"  # NYC
```

**Compare**:
- What times does Zeus return?
- Do they align with start time or UTC?
- Which forecast is most accurate?

---

### Test 2: Historical Accuracy Analysis

**For multiple dates, compare**:
1. **Current method** (00:00 start) accuracy
2. **Earlier start** (22:00 previous day) accuracy
3. **Later start** (06:00 event day) accuracy

**Metrics**:
- Daily high prediction error
- Pattern match (does forecast match actual pattern?)
- Bracket accuracy (does rounded prediction match winning bracket?)

---

### Test 3: Check Actual Temperature Patterns

**Analyze historical data**:
- When does daily high typically occur? (hour of day)
- Does it vary by city/season?
- Would starting forecast at different time improve alignment?

---

## Current Code Summary

### London (EGLC)
```python
# Event day: 2025-11-16
# Local midnight: 2025-11-16T00:00:00+00:00 (GMT)
# Sent to Zeus: 2025-11-16T00:00:00+00:00
# Zeus returns: 24 hours from 00:00 UTC to 23:00 UTC
```

### NYC (KLGA)
```python
# Event day: 2025-11-16
# Local midnight: 2025-11-16T00:00:00-05:00 (EST)
# Sent to Zeus: 2025-11-16T00:00:00-05:00
# Zeus returns: 24 hours from 05:00 UTC to 04:00 UTC (next day)
```

---

## Potential Issues

### Issue 1: Timezone Interpretation

**Question**: Does Zeus API correctly interpret timezone offsets?

**Example**: When we send `2025-11-16T00:00:00-05:00`, does Zeus:
- Return forecast starting at 00:00 EST (05:00 UTC)?
- Or return forecast starting at 00:00 UTC (ignoring timezone)?

**Need to verify**: Check actual Zeus API response times.

---

### Issue 2: Forecast Alignment

**Current**: Forecast starts at local midnight

**Question**: Is this the best time to start a 24-hour forecast for daily high prediction?

**Consideration**: 
- Daily high typically occurs 14-16 hours after midnight
- Starting at midnight means forecast is 14-16 hours old when high occurs
- Would starting later (e.g., 06:00) give fresher forecast for afternoon high?

---

### Issue 3: Event Day Boundary

**Current**: Forecast starts exactly at event day midnight

**Question**: Should forecast include some data from previous day to capture temperature transitions?

**Example**: 
- Temperature at 23:00 on Nov 15 might be relevant for Nov 16's pattern
- Starting at 00:00 might miss this transition

---

## Actual Snapshot Data Analysis

### London Nov 16, 2025

**Snapshot Data**:
- **Fetch time**: 2025-11-15T05:45:02 UTC (forecast fetched on Nov 15)
- **Start local**: 2025-11-16T00:00:00+00:00 ✅
- **Timeseries**: 2025-11-16T00:00:00+00:00 to 2025-11-16T23:00:00+00:00 ✅
- **Alignment**: Perfect match between start_local and first timeseries point

**Zeus Prediction Pattern**:
- 00:00 → 51.5°F (HIGHEST - predicted high)
- Decreasing throughout day
- 23:00 → 42.8°F (LOWEST)

**Actual METAR Pattern**:
- 00:20-15:50 → 50.0°F (constant)
- 15:50+ → Decreasing (48.2°F, then 46.4°F)

**Issue**: Zeus predicts high at start, actual was constant then decreasing.

---

### NYC Nov 16, 2025

**Snapshot Data**:
- **Fetch time**: 2025-11-15T05:45:02 UTC
- **Start local**: 2025-11-16T00:00:00-05:00 ✅ (what we requested)
- **Timeseries**: 2025-11-15T19:00:00-05:00 to 2025-11-16T18:00:00-05:00 ⚠️

**⚠️ CRITICAL DISCREPANCY FOUND**:
- **We requested**: Nov 16 00:00 EST (`2025-11-16T00:00:00-05:00`)
- **Zeus returned**: Timeseries starting at Nov 15 19:00 EST (`2025-11-15T19:00:00-05:00`)
- **Offset**: 5 hours earlier than requested!

**Analysis**:
- 00:00 EST = 05:00 UTC
- 19:00 EST previous day = 00:00 UTC same day
- **Hypothesis**: Zeus might be converting our EST time to UTC, then returning data starting from UTC midnight

**Timeseries Pattern**:
- 19:00 EST (Nov 15) → 47.5°F
- 20:00 EST (Nov 15) → 47.5°F
- 21:00 EST (Nov 15) → 47.4°F
- 22:00 EST (Nov 15) → 47.4°F
- 23:00 EST (Nov 15) → 47.4°F
- 00:00 EST (Nov 16) → Present ✅
- 01:00 EST (Nov 16) → Present ✅
- ...
- 18:00 EST (Nov 16) → 45.4°F (last point)
- **Missing**: 19:00-23:00 EST on Nov 16 ❌

**Analysis**:
- **We requested**: 24 hours starting Nov 16 00:00 EST
- **Zeus returned**: 24 hours from Nov 15 19:00 EST to Nov 16 18:00 EST
- **Has**: Nov 15 19:00-23:00 (5 hours from previous day)
- **Has**: Nov 16 00:00-18:00 (19 hours from event day)
- **Missing**: Nov 16 19:00-23:00 (5 hours from event day)

**This is a MAJOR issue**: 
- We're getting 5 hours from the **previous day** (Nov 15)
- We're missing 5 hours from the **event day** (Nov 16 19:00-23:00)
- Daily high might occur during missing hours!

**Possible Causes**:
1. **Zeus API timezone bug**: Converts EST to UTC, then returns UTC-based timeseries
2. **Our timezone handling**: We send `-05:00` but Zeus might interpret it differently
3. **API response format**: Zeus might always return UTC times regardless of input

**Impact on Accuracy**:
- We're missing early morning temperatures (00:00-04:00 EST)
- Daily high might occur during these missing hours
- Forecast accuracy is compromised

---

## Hypothesis: Would Shifting Start Time Help?

### Current Issue

**London Nov 16**:
- Zeus predicts: High at 00:00 (51.5°F), decreasing
- Actual: Constant 50.0°F until 15:50, then decreasing
- **Zeus pattern is backwards** - high at start instead of constant/peak in afternoon

**If we shifted start time**:
- **Earlier (22:00 previous day)**: Might capture the transition better, but still might predict high at wrong time
- **Later (06:00 event day)**: Would miss early morning, but might better predict afternoon high

### Key Question

**Is the issue the START TIME or the FORECAST MODEL?**

**Evidence**:
- Zeus predicts decreasing pattern (high at start, low at end)
- Actual was constant then decreasing
- This suggests Zeus forecast model might be wrong, not the start time

**But**: If we started forecast later (e.g., 06:00), we'd be forecasting from a point closer to when daily high typically occurs, which might improve accuracy.

---

## Recommendations

### Immediate Investigation

1. **Verify NYC timeseries discrepancy**:
   - Why does timeseries start at 19:00 EST when we request 00:00 EST?
   - Check if this is a timezone conversion issue
   - Verify what Zeus API actually returns

2. **Test different start times**:
   - Current: 00:00 local
   - Earlier: 22:00 previous day
   - Later: 06:00 event day
   - Compare accuracy for each

3. **Analyze forecast patterns**:
   - Does Zeus always predict high at start?
   - Or does it vary based on start time?
   - Check multiple dates to see pattern

### Potential Fix

**If shifting helps**:

**Option 1: Start at 06:00 Event Day**
```python
# Instead of midnight, start at 06:00 local
local_start = datetime.combine(
    event_day,
    time(6, 0),  # 06:00 instead of 00:00
    tzinfo=ZoneInfo(station.time_zone)
)
```

**Option 2: Start at 22:00 Previous Day**
```python
# Start 2 hours before event day
previous_day = event_day - timedelta(days=1)
local_start = datetime.combine(
    previous_day,
    time(22, 0),  # 22:00 previous day
    tzinfo=ZoneInfo(station.time_zone)
)
```

**Option 3: Keep Current but Adjust**
- Keep 00:00 start
- But use forecast hours 6-30 instead of 0-24
- This would focus on event day afternoon/evening

---

## Next Steps

1. **Verify Zeus API behavior**: Test with different start times, check what times are returned
2. **Fix NYC timeseries issue**: Investigate why timeseries starts at 19:00 instead of 00:00
3. **Historical analysis**: Compare accuracy of different start times across multiple dates
4. **Pattern analysis**: Determine when daily high typically occurs, optimize start time accordingly
5. **A/B testing**: If shifting improves accuracy, implement and measure

---

## Summary

### Current Implementation

**London (EGLC)**:
- ✅ **Correct**: Starts at 00:00 GMT, timeseries matches perfectly
- ✅ **Sent to Zeus**: `2025-11-16T00:00:00+00:00`
- ✅ **Zeus returns**: 24 hours from 00:00 UTC to 23:00 UTC

**NYC (KLGA)**:
- ⚠️ **Issue**: Starts at 00:00 EST, but timeseries starts at 19:00 EST (5 hours earlier)
- ⚠️ **Sent to Zeus**: `2025-11-16T00:00:00-05:00`
- ⚠️ **Zeus returns**: 24 hours from 00:00 UTC (19:00 EST previous day) to 23:00 UTC (18:00 EST)
- ❌ **Missing**: First 5 hours of Nov 16 (00:00-04:00 EST)

### Would Shifting Start Time Help?

**For London**:
- Current pattern is backwards (high at start, low at end)
- Shifting might help, but issue might be forecast model, not start time
- **Recommendation**: Test starting at 06:00 event day (focuses on afternoon when high typically occurs)

**For NYC**:
- **CRITICAL**: First fix the timezone issue - we're missing 5 hours of data!
- Once fixed, then test if shifting helps
- **Recommendation**: Fix timezone handling first, then optimize start time

---

**Status**: 🔍 **Investigation Document Created** - Critical NYC timezone issue identified

**Priority**: 
1. **URGENT**: Fix NYC timezone handling (missing 5 hours of data)
2. **HIGH**: Test if shifting start time improves accuracy for London
3. **MEDIUM**: Optimize start time once timezone issues are resolved

