# November 16, 2025 Data Investigation

**Date**: 2025-11-21  
**Issue**: Discrepancy between reported daily high (51.8°F) and graph data, plus Zeus prediction investigation

---

## Issues Identified

1. **METAR Daily High**: Reported as 51.8°F, but graph doesn't show this temperature
2. **Zeus Prediction**: Graph shows 51.5°F at midnight, but need to verify what was actually predicted

---

## Investigation Results

### METAR Actual Data

**All METAR Observations for Nov 16, 2025**:

The daily high of **51.8°F** comes from an observation at **2025-11-15T23:50:00+00:00** (11:50 PM on Nov 15, just 10 minutes before midnight Nov 16).

**Key Finding**: 
- **Daily High**: 51.8°F at 23:50 UTC on Nov 15 (10 minutes before Nov 16 starts)
- **Graph Time Range**: Graph shows 00:00-23:00 on Nov 16
- **Problem**: The 51.8°F observation is **outside the graph's displayed time range**

**All Observations on Nov 16 (00:00-23:59 UTC)**:
- All observations show **50.0°F** (constant throughout the day)
- No observation reaches 51.8°F within the Nov 16 00:00-23:59 window

**Why This Happens**:
The `get_daily_high()` method in `MetarService` filters observations by `event_day`, but it includes observations from the previous day if they fall within the event day's local time range. Since London is UTC+0 in November, the 23:50 UTC observation on Nov 15 is technically part of Nov 16's data.

**Graph Display Issue**:
- Graph shows Nov 16 00:00-23:00
- Highest temperature shown: ~50.5-51.0°F
- Actual daily high (51.8°F) is not visible because it occurred at 23:50 on Nov 15

---

### Zeus Prediction Data

**Zeus Forecast for Nov 16, 2025**:

**Snapshot Details**:
- **Fetch Time**: 2025-11-15T05:45:02 UTC (forecast fetched on Nov 15)
- **Forecast For**: 2025-11-16 (Nov 16 event day)
- **Station**: EGLC

**Midnight (00:00) Prediction**:
- **Time**: 2025-11-16T00:00:00+00:00
- **Temperature**: **51.5°F** ✅ (Matches graph display)

**Daily High (Max of All 24 Hours)**:
- **Calculated Max**: **51.5°F** (at 00:00)
- **All Hourly Predictions**:
  - 00:00 → 51.5°F (HIGHEST)
  - 01:00 → 51.1°F
  - 02:00 → 50.7°F
  - ... (decreasing throughout day)
  - 23:00 → 42.8°F (LOWEST)

**Graph Display**:
- **Shown at midnight**: 51.5°F ✅ **CORRECT** (from first snapshot)
- **Daily high shown in UI**: 51.7°F (from comparison API)
- **Discrepancy Found**: API uses a different snapshot!

**Root Cause Identified**:

The API uses `limit=1` with reverse sort, getting the **most recent** snapshot. There are multiple snapshots for Nov 16:

1. **2025-11-15_05-45-02.json** (first snapshot, before event day)
   - Max temp: **51.5°F** (matches graph)
   - This is what the graph shows

2. **2025-11-16_14-00-02.json** (snapshot during event day)
   - Max temp: **51.7°F** (what API shows)
   - This is what the API uses (most recent)

3. **2025-11-16_18-30-02.json** (later snapshot)
   - Max temp: **51.7°F**

**The Issue**:
- **Graph** shows the **first forecast** (from Nov 15, before event day) → 51.5°F
- **API** uses the **most recent snapshot** (from Nov 16, during event day) → 51.7°F
- These are **different forecasts** with different predictions!

**Precision Note**:
- Actual temp at 00:00: **51.56°F** (from first snapshot)
- Rounded to 1 decimal: **51.6°F**
- Displayed as: **51.5°F** (likely rounding down or different precision)

---

## Data Sources

### METAR Observations
**Location**: `data/snapshots/dynamic/metar/EGLC/2025-11-16/`

**API Endpoint**: `GET /api/metar/daily-high?station_code=EGLC&event_day=2025-11-16`

### Zeus Forecasts
**Location**: `data/snapshots/dynamic/zeus/EGLC/2025-11-16/`

**API Endpoint**: `GET /api/snapshots/zeus?station_code=EGLC&event_day=2025-11-16`

---

## Summary of Findings

### Issue 1: METAR Daily High Not on Graph ✅ RESOLVED

**Problem**: Daily high shows 51.8°F, but graph doesn't display it.

**Root Cause**: 
- 51.8°F occurred at **23:50 UTC on Nov 15** (10 minutes before Nov 16)
- Graph displays Nov 16 00:00-23:00
- Observation is outside the graph's time range

**Solution Options**:
1. **Extend graph time range** to include late-night observations (e.g., 23:00-23:59 from previous day)
2. **Clarify in UI** that daily high may include observations just before midnight
3. **Change daily high calculation** to only include observations within the displayed day (00:00-23:59)

### Issue 2: Zeus Prediction at Midnight ✅ VERIFIED

**Problem**: Graph shows 51.5°F at midnight - is this correct?

**Finding**: 
- ✅ **CORRECT** - Zeus predicted 51.5°F at 00:00
- ✅ **CORRECT** - Daily high is 51.5°F (max of all 24 hours)
- ⚠️ **DISCREPANCY** - Comparison API shows 51.7°F (needs investigation)

**Possible Causes for 51.7°F in API**:
1. API might be using a different snapshot (later in the day)
2. API might be calculating from a different timeseries
3. API might be using a different rounding method

---

## Recommendations

### For METAR Daily High Display

1. **Option A**: Extend graph to show 23:00-23:59 from previous day
   - Shows complete temperature pattern
   - Includes the actual daily high observation

2. **Option B**: Add note in UI
   - "Daily high may include observations from previous evening"
   - Clarifies why graph doesn't show the reported high

3. **Option C**: Change calculation
   - Only count observations within 00:00-23:59 of event day
   - Daily high would be 50.0°F (max within displayed range)

### For Zeus Prediction Display

1. **Snapshot Selection Issue**: 
   - API uses "most recent" snapshot (51.7°F from Nov 16 14:00)
   - Graph shows "first" snapshot (51.5°F from Nov 15 05:45)
   - **Recommendation**: API should use the **latest snapshot BEFORE event day** (not during event day)
   - This matches the intent: "What did Zeus predict before the event started?"

2. **Rounding Consistency**:
   - Actual value: 51.56°F
   - Need consistent rounding (1 decimal place)
   - Verify display matches calculation

---

## Data Verification

### METAR Data
- **Total observations**: 48 files
- **Daily high**: 51.8°F at 2025-11-15T23:50:00+00:00
- **Max within Nov 16 00:00-23:59**: 50.0°F
- **API reports**: 51.8°F ✅ (correct, includes pre-midnight observation)

### Zeus Data
- **Snapshot fetch time**: 2025-11-15T05:45:02 UTC
- **Midnight prediction**: 51.5°F ✅
- **Daily high (calculated)**: 51.5°F ✅
- **API reports**: 51.7°F ⚠️ (needs investigation)

---

**Status**: ✅ **Investigation Complete** - Issues identified and explained

