# New York Snapshot Time Analysis

**Date**: 2025-11-21  
**Issue**: Timezone handling for New York snapshots - start times are local, not UTC

---

## Problem Summary

When creating snapshots for New York (KLGA), we're using **local time** for the start parameter when calling Zeus API, but there's a **mismatch** in how we format and handle these times:

1. **We create local midnight correctly** in `fetchers.py`
2. **We send it to Zeus API incorrectly** - stripping timezone and adding 'Z' (UTC marker)
3. **We store start_local correctly** in snapshots
4. **But timeseries times may be mislabeled** as UTC when they're actually local

---

## Current Flow

### Step 1: Creating Local Midnight (✅ Correct)

**File**: `agents/dynamic_trader/fetchers.py` (lines 50-55)

```python
# Get local midnight for the event day (NO UTC conversion!)
local_midnight = datetime.combine(
    event_day,
    time(0, 0),
    tzinfo=ZoneInfo(station.time_zone)  # America/New_York
)
```

**For New York on 2025-11-17**:
- Creates: `2025-11-17T00:00:00-05:00` (EST, UTC-5)
- This is **correct** - local midnight in New York timezone

---

### Step 2: Sending to Zeus API (❌ PROBLEM)

**File**: `agents/zeus_forecast.py` (line 71)

```python
# Format datetime for API (ISO format)
start_time_str = start_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
```

**Problem**: 
- The parameter is named `start_utc` but we're passing **local time**
- `strftime("%Y-%m-%dT%H:%M:%SZ")` **strips the timezone** and adds 'Z' (UTC marker)
- So `2025-11-17T00:00:00-05:00` becomes `2025-11-17T00:00:00Z`
- This tells Zeus API it's UTC midnight, not EST midnight!

**What gets sent to Zeus**:
```
start_time=2025-11-17T00:00:00Z  # ⚠️ Wrong! This is UTC, not EST
```

**What Zeus probably interprets this as**:
- Zeus sees `2025-11-17T00:00:00Z` and treats it as UTC midnight
- But we wanted EST midnight (`2025-11-17T00:00:00-05:00`)
- This is a **5-hour offset error**!

---

### Step 3: Storing in Snapshot (⚠️ Partially Correct)

**File**: `agents/dynamic_trader/snapshotter.py` (lines 98-109)

```python
# Get first timestamp to determine local start time
if forecast.timeseries:
    first_point = forecast.timeseries[0]
    # Convert to station's local time
    local_start = first_point.time_utc.astimezone(ZoneInfo(station.time_zone))
else:
    local_start = None

snapshot_data = {
    "start_local": local_start.isoformat() if local_start else None,
    # ...
}
```

**What happens**:
- We take the first point's `time_utc` (which may already be in local time or UTC)
- Convert it to local time
- Store as `start_local`

**From actual snapshot**:
```json
{
  "start_local": "2025-11-17T00:00:00-05:00",
  "timeseries": [
    {
      "time_utc": "2025-11-16T19:00:00-05:00",  // ⚠️ Labeled as UTC but has -05:00!
      "temp_K": 283.10
    }
  ]
}
```

**Issue**: The `time_utc` field in timeseries has timezone offset (`-05:00`), which means it's **not actually UTC** - it's local time!

---

## Root Cause Analysis

### Issue 1: Zeus API Call Format

**Current code** (`agents/zeus_forecast.py:71`):
```python
start_time_str = start_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
```

**Problem**: 
- Strips timezone information
- Adds 'Z' suffix (UTC marker)
- Sends `2025-11-17T00:00:00Z` when we want `2025-11-17T00:00:00-05:00`

**What Zeus API expects**:
- Need to check Zeus API documentation
- Likely expects ISO format with timezone: `2025-11-17T00:00:00-05:00`
- Or expects UTC and we need to convert local → UTC before sending

---

### Issue 2: Timeseries Time Labeling

**Current code** (`agents/zeus_forecast.py:202-230`):
```python
# Parse timestamp
if isinstance(timestamp, str):
    time_utc = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
```

**Problem**:
- Field is named `time_utc` but may contain local time with timezone
- From snapshots: `"time_utc": "2025-11-16T19:00:00-05:00"` - this is EST, not UTC!

**What Zeus API returns**:
- Need to verify what format Zeus actually returns
- If Zeus returns UTC times, we should store as UTC
- If Zeus returns local times, we should store as local (and rename field)

---

## Actual Snapshot Data Analysis

### Example Snapshot: `data/snapshots/dynamic/zeus/KLGA/2025-11-17/2025-11-16_23-00-02.json`

```json
{
  "fetch_time_utc": "2025-11-16T23:00:02.209266+00:00",  // ✅ Correct UTC
  "forecast_for_local_day": "2025-11-17",
  "start_local": "2025-11-17T00:00:00-05:00",  // ✅ Correct local time
  "station_code": "KLGA",
  "city": "New York (Airport)",
  "timezone": "America/New_York",
  "timeseries": [
    {
      "time_utc": "2025-11-16T19:00:00-05:00",  // ⚠️ Labeled UTC but is EST!
      "temp_K": 283.10
    },
    {
      "time_utc": "2025-11-16T20:00:00-05:00",  // ⚠️ EST, not UTC
      "temp_K": 282.52
    }
  ]
}
```

### Observations:

1. **`start_local` is correct**: `2025-11-17T00:00:00-05:00` (EST midnight)
2. **`fetch_time_utc` is correct**: `2025-11-16T23:00:02+00:00` (UTC)
3. **`time_utc` in timeseries is WRONG**: Has `-05:00` offset, so it's EST, not UTC
4. **First timeseries point**: `2025-11-16T19:00:00-05:00` = Nov 16, 7 PM EST
5. **Expected first point**: Should be `2025-11-17T00:00:00-05:00` (Nov 17, midnight EST)

**This suggests**:
- Either Zeus API is returning times in local timezone (EST)
- Or we're parsing/formatting them incorrectly
- The timeseries starts 5 hours before local midnight, which matches UTC midnight

---

## Time Conversion Analysis

### What Should Happen:

**For New York (EST, UTC-5) on 2025-11-17**:

1. **Local midnight**: `2025-11-17T00:00:00-05:00` (EST)
2. **Convert to UTC**: `2025-11-17T05:00:00+00:00` (UTC)
3. **Send to Zeus**: Either:
   - Local: `2025-11-17T00:00:00-05:00` (if Zeus accepts local)
   - UTC: `2025-11-17T05:00:00Z` (if Zeus requires UTC)
4. **Zeus returns**: 24 hourly points starting from requested time
5. **Store in snapshot**: 
   - `start_local`: `2025-11-17T00:00:00-05:00`
   - `timeseries[0].time_utc`: Should be UTC, e.g., `2025-11-17T05:00:00+00:00`

### What's Actually Happening:

1. **Local midnight**: `2025-11-17T00:00:00-05:00` ✅
2. **Sent to Zeus**: `2025-11-17T00:00:00Z` ❌ (stripped timezone, marked as UTC)
3. **Zeus interprets**: As UTC midnight (`2025-11-17T00:00:00Z`)
4. **Zeus returns**: Times starting from UTC midnight
5. **We parse**: Times with timezone info (possibly from Zeus response format)
6. **We store**: Times with `-05:00` offset (EST) but labeled as `time_utc` ❌

---

## Recommendations

### Fix 1: Correct Zeus API Call Format

**Option A: Send Local Time with Timezone** (if Zeus accepts it)
```python
# In agents/zeus_forecast.py
start_time_str = start_utc.isoformat()  # Preserves timezone
# Result: "2025-11-17T00:00:00-05:00"
```

**Option B: Convert to UTC Before Sending** (if Zeus requires UTC)
```python
# In agents/dynamic_trader/fetchers.py
local_midnight = datetime.combine(event_day, time(0, 0), tzinfo=ZoneInfo(station.time_zone))
utc_midnight = local_midnight.astimezone(ZoneInfo("UTC"))

# Then in zeus_forecast.py
start_time_str = utc_midnight.strftime("%Y-%m-%dT%H:%M:%SZ")
# Result: "2025-11-17T05:00:00Z" for EST
```

**Need to verify**: What format does Zeus API actually expect?

---

### Fix 2: Correct Timeseries Time Storage

**Option A: Store as UTC** (if Zeus returns UTC)
```python
# In agents/zeus_forecast.py
# Parse timestamp and ensure it's UTC
time_utc = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
if time_utc.tzinfo is None:
    time_utc = time_utc.replace(tzinfo=ZoneInfo("UTC"))
elif time_utc.tzinfo != ZoneInfo("UTC"):
    # Convert to UTC if not already
    time_utc = time_utc.astimezone(ZoneInfo("UTC"))
```

**Option B: Store as Local** (if Zeus returns local)
```python
# Rename field to time_local
# Or keep time_utc but ensure it's actually UTC
```

---

### Fix 3: Verify Zeus API Behavior

**Action Items**:
1. Check Zeus API documentation for expected time format
2. Test API call with both local and UTC times
3. Verify what timezone Zeus returns times in
4. Check if Zeus API handles timezone offsets correctly

---

## Current State Summary

| Component | Status | Notes |
|-----------|--------|-------|
| Local midnight creation | ✅ Correct | Creates `2025-11-17T00:00:00-05:00` |
| Zeus API call format | ❌ Wrong | Strips timezone, sends as UTC |
| Snapshot start_local | ✅ Correct | Stores local time correctly |
| Timeseries time_utc | ⚠️ Confusing | Has timezone offset, not actually UTC |
| Timezone handling | ⚠️ Inconsistent | Mix of local and UTC without clear rules |

---

## Next Steps

1. **Verify Zeus API documentation** - What time format does it expect/return?
2. **Test API calls** - Send both local and UTC times, see what works
3. **Fix timezone conversion** - Ensure consistent UTC/local handling
4. **Update field names** - If storing local times, don't call them `time_utc`
5. **Add validation** - Verify timeseries times match expected start time

---

## Questions to Answer

1. **Does Zeus API accept local time with timezone offset?**
   - If yes: Use `local_midnight.isoformat()`
   - If no: Convert to UTC first

2. **What timezone does Zeus API return times in?**
   - UTC? Local? Same as input?
   - Check actual API responses

3. **Are we correctly interpreting Zeus responses?**
   - Are times already in UTC and we're mislabeling?
   - Or are times in local and we need to convert?

4. **What is the intended behavior?**
   - Should `time_utc` always be UTC?
   - Should we have separate `time_local` and `time_utc` fields?

---

## Code Locations

- **Creating local midnight**: `agents/dynamic_trader/fetchers.py:50-55`
- **Formatting for Zeus API**: `agents/zeus_forecast.py:71`
- **Zeus API call**: `agents/zeus_forecast.py:47-111`
- **Parsing Zeus response**: `agents/zeus_forecast.py:199-243`
- **Storing in snapshot**: `agents/dynamic_trader/snapshotter.py:98-109`

---

**Status**: ⚠️ **Needs Investigation** - Timezone handling is inconsistent and may be causing incorrect API calls or data storage.

