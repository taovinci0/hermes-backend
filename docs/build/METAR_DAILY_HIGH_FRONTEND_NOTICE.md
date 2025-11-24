# METAR Daily High Fix - Frontend Notice

**Date**: 2025-11-21  
**Change**: Backend now only includes observations from within event day (00:00-23:59 UTC)  
**Impact**: Daily high values may change for dates with late-night observations

---

## What Changed

**Backend Fix**: The `get_daily_high()` API endpoint now filters observations to **only include data from within the event day** (00:00:00 to 23:59:59 UTC).

**Before**:
- Daily high included observations from previous day (e.g., 23:50 on Nov 15 counted for Nov 16)
- Example: Nov 16 showed 51.8°F (from Nov 15 23:50) even though graph only showed up to 50.0°F

**After**:
- Daily high only includes observations from the exact event day
- Example: Nov 16 now shows 50.0°F (max within Nov 16 00:00-23:59) ✅

---

## API Response Change

**Endpoint**: `GET /api/metar/daily-high?station_code={STATION}&event_day={DATE}`

**Example - Nov 16, 2025**:

**Before Fix**:
```json
{
  "station_code": "EGLC",
  "event_day": "2025-11-16",
  "daily_high_f": 51.8,  // ❌ Included Nov 15 23:50 observation
  "available": true
}
```

**After Fix**:
```json
{
  "station_code": "EGLC",
  "event_day": "2025-11-16",
  "daily_high_f": 50.0,  // ✅ Only Nov 16 00:00-23:59 observations
  "available": true
}
```

---

## Impact on Frontend

### What You Need to Know

1. **Daily high values may change** for historical dates
   - Dates with late-night observations from previous day will show different values
   - Example: Nov 16 changed from 51.8°F to 50.0°F

2. **Daily high now matches graph data**
   - Daily high will always be within the graph's displayed range (00:00-23:00)
   - No more "daily high not visible on graph" issues

3. **No frontend code changes needed**
   - API contract unchanged (still returns `daily_high_f`)
   - Just the values will be more accurate

### Cache Note

**If you're caching daily high values**:
- Clear your cache for affected dates
- Or let cache expire naturally

---

## Verification

**Test the fix**:
```bash
curl "http://localhost:8000/api/metar/daily-high?station_code=EGLC&event_day=2025-11-16"
```

**Expected**: `"daily_high_f": 50.0` (not 51.8)

---

## Why This Matters

**User Experience**:
- Daily high displayed in UI should match what's visible on the graph
- Users won't see confusing "51.8°F" when graph only shows up to 50.0°F

**Data Accuracy**:
- Daily high now accurately represents the event day only
- No contamination from previous day's late-night observations

---

**Status**: ✅ **Backend Fix Deployed** - Frontend should see corrected daily high values

