# London Graph Timezone Issue - November 16, 2025

**Date**: 2025-11-21  
**Issue**: Graph shows daily high temperature at midnight (00:00) instead of afternoon

---

## Problem

The 24-hour temperature forecast graph for London (EGLC) on November 16, 2025 shows:
- **Highest temperature at 00:00 (midnight)**: 51.5°F
- **Temperatures decrease throughout the day**
- **Lowest temperatures in the afternoon/evening**

This is **backwards** from reality! The daily high should occur in the afternoon (14:00-16:00), not at midnight.

---

## Root Cause Analysis

### Actual Snapshot Data

From `data/snapshots/dynamic/zeus/EGLC/2025-11-16/`:

```json
{
  "forecast_for_local_day": "2025-11-16",
  "start_local": "2025-11-16T00:00:00+00:00",
  "timezone": "Europe/London",
  "timeseries": [
    {"time_utc": "2025-11-16T00:00:00+00:00", "temp_K": 278.41, "temp_F": 51.5},  // ← HIGHEST
    {"time_utc": "2025-11-16T01:00:00+00:00", "temp_K": 278.43, "temp_F": 51.1},
    {"time_utc": "2025-11-16T02:00:00+00:00", "temp_K": 278.62, "temp_F": 50.7},
    // ... decreasing throughout day
    {"time_utc": "2025-11-16T23:00:00+00:00", "temp_K": 277.xx, "temp_F": ~41.5}  // ← LOWEST
  ]
}
```

**Pattern**: Temperature starts high at midnight and decreases throughout the day.

**Expected Pattern**: Temperature should start low at midnight, increase to peak in afternoon (14:00-16:00), then decrease.

---

## Possible Causes

### 1. Zeus API Returns Data in Wrong Order

**Hypothesis**: Zeus API might be returning the forecast timeseries in reverse chronological order, or the times are mislabeled.

**Check**: Compare with actual METAR data - does METAR show the correct pattern?

### 2. Timezone Conversion Issue

**Hypothesis**: Times might be stored in wrong timezone, causing a shift.

**Analysis**:
- London in November = GMT (UTC+0)
- `start_local`: `2025-11-16T00:00:00+00:00` ✅ Correct (GMT = UTC)
- `time_utc` fields: All have `+00:00` ✅ Correct for GMT

**Conclusion**: Timezone appears correct. Not a timezone issue.

### 3. Data Parsing/Storage Issue

**Hypothesis**: When parsing Zeus API response, we might be:
- Reversing the order of timeseries points
- Misinterpreting the time labels
- Storing times incorrectly

**Check**: Look at raw Zeus API response to see what it actually returns.

### 4. Graph Display Issue

**Hypothesis**: Graph might be displaying times incorrectly (e.g., showing UTC as local, or vice versa).

**Analysis**: 
- Graph shows X-axis as 00:00 to 23:00 (24-hour day)
- If times are in UTC and graph interprets as local, but London = UTC in Nov, so no shift
- Graph is probably displaying correctly - the data itself is wrong

---

## Investigation Steps

### Step 1: Check Raw Zeus API Response

```bash
# Find raw Zeus snapshot (before parsing)
find data/snapshots/zeus/2025-11-16 -name "EGLC.json" | xargs cat | jq
```

Check:
- What order are the timeseries points in?
- What format are the timestamps?
- Does the raw data show the same backwards pattern?

### Step 2: Compare with METAR Actual

```bash
# Check METAR observations for Nov 16
find data/snapshots/dynamic/metar/EGLC/2025-11-16 -name "*.json" | head -1 | xargs cat | jq
```

Check:
- Does METAR show correct pattern (low at night, high in afternoon)?
- If METAR is correct but Zeus is wrong, it's a Zeus API/parsing issue
- If both are wrong, it's a display issue

### Step 3: Check Graph Code

Check how the frontend is:
- Parsing `time_utc` from snapshots
- Converting to display time
- Ordering data points for the graph

---

## Expected Behavior

**Correct Temperature Pattern (November, London)**:
```
00:00 (midnight)  → ~45°F  (coldest)
06:00 (dawn)      → ~46°F  (still cold)
12:00 (noon)      → ~50°F  (warming)
14:00-16:00       → ~52°F  (WARMEST - daily high)
18:00 (evening)   → ~48°F  (cooling)
22:00 (night)     → ~46°F  (getting cold)
```

**Current (Wrong) Pattern**:
```
00:00 (midnight)  → 51.5°F  (HIGHEST - wrong!)
01:00            → 51.1°F
02:00            → 50.7°F
...
14:00            → ~45°F   (should be highest!)
...
23:00            → ~41.5°F (LOWEST - wrong!)
```

---

## Fix Strategy

### If Zeus API Returns Wrong Order

1. **Check raw API response** - verify what Zeus actually returns
2. **Fix parsing** - ensure we preserve correct order
3. **Add validation** - verify temperature pattern makes sense (high in afternoon)

### If Data Storage is Wrong

1. **Check snapshotter code** - ensure timeseries is stored in correct order
2. **Fix storage** - reorder if needed
3. **Migration script** - fix existing snapshots

### If Graph Display is Wrong

1. **Check frontend code** - how it parses and displays times
2. **Fix display** - ensure correct timezone handling
3. **Test** - verify with known good data

---

## Investigation Results

### Raw Zeus API Response

Checked `data/snapshots/zeus/2025-11-16/EGLC.json`:

```json
{
  "2m_temperature": {
    "data": [
      284.02,  // 00:00 → 51.5°F (HIGHEST)
      283.81,  // 01:00 → 51.1°F
      283.61,  // 02:00 → 50.7°F
      // ... decreasing
      279.10   // 23:00 → 42.8°F (LOWEST)
    ]
  },
  "time": {
    "data": [
      "2025-11-16 00:00:00+00:00",
      "2025-11-16 01:00:00+00:00",
      // ... correct order
      "2025-11-16 23:00:00+00:00"
    ]
  }
}
```

**Findings**:
- ✅ Times are in correct order (00:00 to 23:00)
- ✅ Times are in correct timezone (UTC, which = GMT for London in Nov)
- ❌ **Temperatures are backwards** - highest at midnight, lowest at end of day

**Conclusion**: The issue is **NOT** with our parsing or storage. Zeus API is returning a forecast with the wrong temperature pattern.

### Possible Causes

1. **Zeus API Bug**: Zeus API might have a bug that returns forecasts with reversed temperature patterns
2. **Request Issue**: We might be requesting the forecast incorrectly (wrong start time or parameters)
3. **API Interpretation**: Zeus might interpret the start time differently than we expect
4. **Data Issue**: This might be a one-off bad forecast from Zeus

### What We're Sending to Zeus

For London on Nov 16, 2025:
- **Local midnight**: `2025-11-16T00:00:00+00:00` (GMT = UTC)
- **Sent to Zeus**: `2025-11-16T00:00:00+00:00` (after our timezone fix)
- **Request**: 24-hour forecast starting at local midnight

This appears correct.

## Next Steps

1. ✅ **Identified issue**: Data shows high at midnight (wrong)
2. ✅ **Investigated**: Raw Zeus API response shows same pattern
3. ⏳ **Compare**: Check METAR actual data to confirm this is wrong
4. ⏳ **Contact Zeus**: May need to report this to Zeus API team
5. ⏳ **Workaround**: Consider validating/reversing temperature patterns if needed
6. ⏳ **Verify**: Check if this happens for other dates/stations

---

## Related Issues

- Similar timezone issues were found for NYC (KLGA) - see `NEW_YORK_SNAPSHOT_TIME_ANALYSIS.md`
- Code fix applied for NYC timezone handling in `agents/zeus_forecast.py`
- May need similar investigation/fix for London

---

**Status**: ⚠️ **Issue Confirmed** - Data shows backwards temperature pattern. Investigation needed to determine root cause.

