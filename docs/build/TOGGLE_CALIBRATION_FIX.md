# Station Calibration Toggle Fix

**Date**: 2025-01-21  
**Issue**: Data not updating when toggling station calibration on/off  
**Status**: ✅ **FIXED**

---

## Problem Identified

The `/api/snapshots/zeus` endpoint was returning **raw snapshots** without applying calibration, even when the toggle was enabled. 

### Root Cause

`SnapshotService.get_zeus_snapshots()` was:
1. ✅ Reading snapshot files from disk
2. ❌ **NOT** checking feature toggle state
3. ❌ **NOT** applying calibration to temperatures

### What Was Working

- ✅ `/api/compare/zeus-vs-metar` - Applied calibration correctly
- ✅ Live trading (`prob_mapper.py`) - Applied calibration correctly
- ✅ Backtesting - Applied calibration correctly

### What Was Broken

- ❌ `/api/snapshots/zeus` - Returned raw snapshots without calibration

---

## Solution Implemented

### Updated `backend/api/services/snapshot_service.py`

**Changes**:

1. **Added imports**:
   - `FeatureToggles` - To check toggle state
   - `StationCalibration` - To apply calibration
   - `units` - For temperature conversions

2. **Modified `get_zeus_snapshots()`**:
   - Loads `FeatureToggles` on each request
   - Checks if `station_calibration` is enabled
   - Initializes `StationCalibration` if enabled
   - Applies calibration to each snapshot before returning

3. **Added `_apply_calibration_to_snapshot()`**:
   - Extracts temperatures and timestamps from snapshot timeseries
   - Applies calibration using `StationCalibration.apply_to_forecast_timeseries()`
   - Updates both `temp_K` and `temp_F` in timeseries points
   - Recalculates `predicted_high_F` from calibrated temperatures

---

## How It Works Now

### Data Flow

```
1. Frontend: GET /api/snapshots/zeus?station_code=EGLC&event_day=2025-11-16
   ↓
2. Backend: SnapshotService.get_zeus_snapshots()
   ↓
3. Backend: Load FeatureToggles.load()
   ↓
4. Backend: Check if station_calibration is True
   ↓
5. If True:
   - Initialize StationCalibration()
   - For each snapshot:
     - Extract temps_k and timestamps from timeseries
     - Apply calibration.apply_to_forecast_timeseries()
     - Update timeseries with calibrated temps
     - Recalculate predicted_high_F
   ↓
6. Return calibrated snapshots
```

### Key Points

- **Backend checks toggle state on EVERY request** - No caching
- **Calibration is applied server-side** - Frontend doesn't need to do anything
- **Both `temp_K` and `temp_F` are updated** - Ensures consistency
- **`predicted_high_F` is recalculated** - From calibrated timeseries max

---

## Verification Steps

### 1. Check Toggle State File

```bash
cat data/config/feature_toggles.json
```

Should show:
```json
{
  "station_calibration": false
}
```

### 2. Test API with Calibration OFF

```bash
curl "http://localhost:8000/api/snapshots/zeus?station_code=EGLC&event_day=2025-11-16" | jq '.snapshots[0].predicted_high_F'
```

**Note the value** (e.g., `46.3`)

### 3. Enable Calibration

```bash
curl -X PUT "http://localhost:8000/api/features/toggles" \
  -H "Content-Type: application/json" \
  -d '{"station_calibration": true}'
```

### 4. Verify Toggle State Updated

```bash
cat data/config/feature_toggles.json
```

Should now show:
```json
{
  "station_calibration": true
}
```

### 5. Test API with Calibration ON

```bash
curl "http://localhost:8000/api/snapshots/zeus?station_code=EGLC&event_day=2025-11-16" | jq '.snapshots[0].predicted_high_F'
```

**The value should be DIFFERENT** (e.g., `46.8` instead of `46.3`)

### 6. Check Timeseries Temperatures

```bash
# With calibration OFF
curl "http://localhost:8000/api/snapshots/zeus?station_code=EGLC&event_day=2025-11-16" | jq '.snapshots[0].timeseries[0].temp_F'

# With calibration ON (after toggling)
curl "http://localhost:8000/api/snapshots/zeus?station_code=EGLC&event_day=2025-11-16" | jq '.snapshots[0].timeseries[0].temp_F'
```

**Timeseries temperatures should also be different**

---

## Expected Behavior

### With Calibration OFF

```json
{
  "snapshots": [
    {
      "predicted_high_F": 46.3,
      "timeseries": [
        {"time_utc": "2025-11-16T00:00:00Z", "temp_F": 45.1, "temp_K": 280.43},
        {"time_utc": "2025-11-16T01:00:00Z", "temp_F": 45.3, "temp_K": 280.54},
        // ... raw Zeus predictions
      ]
    }
  ]
}
```

### With Calibration ON

```json
{
  "snapshots": [
    {
      "predicted_high_F": 46.8,  // ← Different! (calibrated)
      "timeseries": [
        {"time_utc": "2025-11-16T00:00:00Z", "temp_F": 45.6, "temp_K": 280.71},  // ← Different!
        {"time_utc": "2025-11-16T01:00:00Z", "temp_F": 45.8, "temp_K": 280.82},  // ← Different!
        // ... calibrated Zeus predictions
      ]
    }
  ]
}
```

**Key Point**: The same API endpoint returns **different data** depending on the current toggle state.

---

## Frontend Impact

### No Frontend Changes Required

The frontend doesn't need to change anything. The backend now:

1. ✅ Automatically checks toggle state on every request
2. ✅ Applies calibration if enabled
3. ✅ Returns calibrated data when toggle is ON
4. ✅ Returns raw data when toggle is OFF

### Frontend Behavior

When the frontend:
1. Toggles calibration ON/OFF
2. Dispatches `toggles-updated` event
3. Invalidates React Query cache
4. Refetches `/api/snapshots/zeus`

The backend will automatically return the correct data (calibrated or raw) based on the current toggle state.

---

## Testing Checklist

### Backend Tests

- [ ] Toggle state file updates correctly
- [ ] API returns different values when toggle is ON vs OFF
- [ ] Timeseries temperatures are calibrated
- [ ] `predicted_high_F` is recalculated from calibrated temps
- [ ] Calibration works for all stations (EGLC, KLGA)
- [ ] No errors when calibration files are missing

### Frontend Tests

- [ ] Toggle updates successfully
- [ ] Event is dispatched when toggle changes
- [ ] Queries are invalidated correctly
- [ ] Data refreshes when toggle changes
- [ ] Graphs show different values when toggle is ON vs OFF
- [ ] No console errors

---

## Debugging

### If Data Still Not Updating

1. **Check backend logs**:
   - Look for calibration application logs
   - Check for errors loading calibration files

2. **Verify calibration files exist**:
   ```bash
   ls -la data/calibration/
   ```
   Should show:
   - `station_calibration_EGLC.json`
   - `station_calibration_KLGA.json`

3. **Test calibration directly**:
   ```python
   from core.station_calibration import StationCalibration
   calibration = StationCalibration()
   print(calibration.has_calibration("EGLC"))  # Should be True
   ```

4. **Check API response**:
   - Use browser Network tab or curl
   - Compare responses before/after toggle
   - Verify `predicted_high_F` changes

5. **Check frontend cache**:
   - Clear React Query cache
   - Hard refresh browser
   - Check if queries are actually refetching

---

## Summary

✅ **Fixed**: `SnapshotService.get_zeus_snapshots()` now applies calibration based on toggle state

✅ **Automatic**: Backend checks toggle state on every request

✅ **No Frontend Changes**: Frontend just needs to refetch data when toggle changes

✅ **Consistent**: Same behavior as `/api/compare/zeus-vs-metar` endpoint

---

**Status**: Ready for testing


