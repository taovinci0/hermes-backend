# Graph Display Issue - Both Zeus and METAR Show High at Midnight

**Date**: 2025-11-21  
**Issue**: Graph displays both Zeus forecast and METAR actual temperatures with high at midnight (00:00)

---

## Problem

User reports that the graph shows:
- **Zeus forecast**: Highest temperature at 00:00 (midnight)
- **METAR actual**: Also shows highest temperature at 00:00 (midnight)

**This is suspicious** because:
1. If both show the same pattern, it's likely a **display issue**, not a data issue
2. Actual weather (METAR) should show high in afternoon, not midnight
3. If METAR is correct but displayed wrong, the graph is misinterpreting times

---

## Investigation

### METAR Actual Data

From `data/snapshots/dynamic/metar/EGLC/2025-11-16/`:

```
2025-11-16_13-20-00.json → Time: 2025-11-16T13:20:00+00:00, Temp: 50.0°F
2025-11-16_05-50-00.json → Time: 2025-11-16T05:50:00+00:00, Temp: 50.0°F
2025-11-16_19-50-00.json → Time: 2025-11-16T19:50:00+00:00, Temp: 48.2°F
2025-11-16_08-50-00.json → Time: 2025-11-16T08:50:00+00:00, Temp: 50.0°F
2025-11-16_14-50-00.json → Time: 2025-11-16T14:50:00+00:00, Temp: 50.0°F
```

**Observation**: METAR observations are at various times (05:50, 08:50, 13:20, 14:50, 19:50), not hourly.

### Zeus Forecast Data

From `data/snapshots/dynamic/zeus/EGLC/2025-11-16/`:

```
Timeseries (hourly, 00:00 to 23:00):
  00:00 → 51.5°F (HIGHEST)
  01:00 → 51.1°F
  02:00 → 50.7°F
  ...
  14:00 → 49.8°F
  ...
  23:00 → 42.8°F (LOWEST)
```

**Observation**: Zeus forecast shows decreasing pattern (high at start, low at end).

---

## Possible Causes

### 1. Graph X-Axis Reversed

**Hypothesis**: Graph might be displaying X-axis in reverse order (23:00 to 00:00 instead of 00:00 to 23:00).

**Check**: Does the graph show times increasing left-to-right (00:00 → 23:00) or decreasing (23:00 → 00:00)?

### 2. Time Extraction Issue

**Hypothesis**: Graph might be extracting time incorrectly from `time_utc` strings.

**Example**:
- `time_utc: "2025-11-16T14:00:00+00:00"` should extract hour `14` → display as `14:00`
- But if extracting wrong part, might get `00` → display as `00:00`

### 3. Timezone Conversion Issue

**Hypothesis**: Graph might be converting UTC to wrong timezone, causing time shift.

**For London in November**:
- UTC = GMT (no DST)
- `2025-11-16T14:00:00+00:00` UTC = `14:00` GMT = `14:00` London time ✅

**But if graph converts to wrong timezone**:
- Converting to EST (UTC-5): `14:00 UTC` → `09:00 EST` ❌
- Converting to PST (UTC-8): `14:00 UTC` → `06:00 PST` ❌

### 4. Data Ordering Issue

**Hypothesis**: Timeseries data might be stored/parsed in reverse order.

**Check**: Is timeseries array `[00:00, 01:00, ..., 23:00]` or `[23:00, 22:00, ..., 00:00]`?

### 5. Graph Plotting Issue

**Hypothesis**: Graph might be plotting data points in wrong order or at wrong X positions.

**Check**: 
- Are data points plotted at correct X positions?
- Is the X-axis scale correct?
- Are timeseries points being sorted/ordered incorrectly before plotting?

---

## Diagnostic Steps

### Step 1: Verify Data Order

```bash
# Check if timeseries is in correct order
cat snapshot.json | jq '.timeseries[] | .time_utc' | head -5
# Should show: 00:00, 01:00, 02:00, 03:00, 04:00
```

### Step 2: Check Graph Code

Check frontend code that:
1. Extracts time from `time_utc` strings
2. Converts to display format
3. Maps to X-axis positions
4. Orders/sorts data points

### Step 3: Test with Known Data

Create test data with:
- Known temperature pattern (low at 00:00, high at 14:00)
- Verify graph displays correctly

### Step 4: Check METAR Display

Check how METAR observations are:
- Extracted from `observation_time_utc`
- Converted to display time
- Plotted on graph

---

## Expected vs Actual

### Expected (Correct)

```
X-Axis: 00:00 → 23:00 (left to right)
Temperature: Low at 00:00, High at 14:00-16:00, Low at 23:00
```

### Actual (Wrong)

```
X-Axis: 00:00 → 23:00 (appears correct)
Temperature: High at 00:00, Decreasing, Low at 23:00 (WRONG!)
```

---

## Most Likely Cause

Given that **both Zeus and METAR show the same pattern**, the issue is most likely:

1. **Graph X-axis is reversed** - showing 23:00 on left, 00:00 on right
2. **Time extraction is wrong** - extracting wrong part of timestamp
3. **Data is being sorted incorrectly** - reversing order before display

**Recommendation**: Check frontend graph code for:
- X-axis domain/scale configuration
- Time extraction/parsing logic
- Data sorting/ordering before plotting

---

## Next Steps

1. ⏳ **Check frontend code** - How does it extract/display times?
2. ⏳ **Verify X-axis** - Is it reversed or correct?
3. ⏳ **Test with known data** - Create test case with correct pattern
4. ⏳ **Fix display logic** - Correct time extraction/display
5. ⏳ **Verify** - Confirm graph shows correct pattern

---

**Status**: ⚠️ **Display Issue Suspected** - Both data sources show same wrong pattern, suggesting graph display problem rather than data problem.

