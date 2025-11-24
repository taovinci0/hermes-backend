# Timezone Fix Implementation

**Date**: 2025-11-21  
**Status**: ✅ Code Fixed, Migration Script Ready

---

## Problem Summary

When fetching Zeus forecasts for New York (KLGA), we were:
1. ✅ Creating local midnight correctly: `2025-11-17T00:00:00-05:00`
2. ❌ Sending to Zeus API incorrectly: Stripping timezone and adding 'Z' → `2025-11-17T00:00:00Z`
3. ⚠️ Storing timeseries with timezone offsets but labeled as `time_utc`

This caused a **5-hour offset error** - Zeus thought we wanted UTC midnight instead of EST midnight.

---

## Fix 1: Code Fix (✅ Complete)

### File: `agents/zeus_forecast.py`

**Changed**: Line 71 - Format datetime to preserve timezone

**Before**:
```python
start_time_str = start_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
# Strips timezone, always adds 'Z' (UTC marker)
```

**After**:
```python
# Format datetime for API - preserve timezone if present
# Zeus API expects ISO format with timezone (e.g., 2025-11-17T00:00:00-05:00)
if start_utc.tzinfo is not None:
    # Has timezone - use ISO format to preserve it
    start_time_str = start_utc.isoformat()
else:
    # No timezone - assume UTC and format with Z
    start_time_str = start_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
```

**Result**:
- Local time with timezone: `2025-11-17T00:00:00-05:00` → Sent as-is ✅
- UTC time: `2025-11-17T05:00:00+00:00` → Sent as `2025-11-17T05:00:00Z` ✅

---

## Fix 2: Migration Script (✅ Ready)

### File: `scripts/fix_nyc_snapshot_times.py`

**Purpose**: Fix existing NYC snapshot data that was collected with incorrect timezone handling.

**What it does**:
1. Finds all KLGA snapshot files in `data/snapshots/dynamic/zeus/KLGA/`
2. Checks `start_local` field - ensures it's in correct timezone
3. Checks `timeseries[].time_utc` fields - fixes if they have wrong timezone
4. Creates backups (optional)
5. Reports all changes

**Usage**:

```bash
# Dry run (see what would be fixed, no changes)
python scripts/fix_nyc_snapshot_times.py --dry-run

# Actually fix the files
python scripts/fix_nyc_snapshot_times.py

# With backup
python scripts/fix_nyc_snapshot_times.py --backup

# Fix different station
python scripts/fix_nyc_snapshot_times.py --station EGLC
```

**What gets fixed**:

1. **start_local**: If it's in wrong timezone or missing timezone, converts to station's local timezone
2. **timeseries times**: 
   - If time has timezone offset (like `-05:00`) but is labeled as UTC, ensures it's in correct timezone
   - If time is UTC but should be local, converts to local
   - If time has no timezone, assumes UTC and converts to local

**Example Output**:
```
🔧 Fixing snapshots for New York (Airport) (KLGA)
   Timezone: America/New_York
   
📁 Found 15 snapshot file(s)

✅ 2025-11-16_14-00-02.json
   - Fixed start_local: 2025-11-17T00:00:00Z → 2025-11-17T00:00:00-05:00
   - Fixed 24 timeseries times

✅ 2025-11-16_18-30-02.json
   - Fixed 24 timeseries times

Summary:
  Total files: 15
  Fixed: 12
  Errors: 0
  Total changes: 36
```

---

## Testing the Fix

### Test 1: Verify Code Fix

```python
from datetime import datetime, time, date
from zoneinfo import ZoneInfo
from agents.zeus_forecast import ZeusForecastAgent

# Create local midnight for NYC
event_day = date(2025, 11, 17)
local_midnight = datetime.combine(
    event_day,
    time(0, 0),
    tzinfo=ZoneInfo("America/New_York")
)

# Check what gets sent to API
agent = ZeusForecastAgent()
# The _call_zeus_api method will now use .isoformat() which preserves timezone
# Should send: "2025-11-17T00:00:00-05:00"
```

### Test 2: Run Migration Script

```bash
# First, see what would be fixed
python scripts/fix_nyc_snapshot_times.py --dry-run

# If looks good, run for real
python scripts/fix_nyc_snapshot_times.py --backup
```

---

## Impact

### Before Fix:
- Zeus API received: `2025-11-17T00:00:00Z` (UTC midnight)
- Zeus interpreted as: UTC midnight
- Actual intent: EST midnight (`2025-11-17T00:00:00-05:00`)
- **Error**: 5-hour offset

### After Fix:
- Zeus API receives: `2025-11-17T00:00:00-05:00` (EST midnight)
- Zeus interprets as: EST midnight (or converts internally)
- **Correct**: Matches intent

---

## Verification

After running the migration script, verify:

1. **Check a fixed snapshot**:
   ```bash
   cat data/snapshots/dynamic/zeus/KLGA/2025-11-17/2025-11-16_14-00-02.json | jq '.start_local'
   # Should show: "2025-11-17T00:00:00-05:00"
   ```

2. **Check timeseries times**:
   ```bash
   cat data/snapshots/dynamic/zeus/KLGA/2025-11-17/2025-11-16_14-00-02.json | jq '.timeseries[0].time_utc'
   # Should show time in correct timezone or UTC
   ```

3. **Test new fetches**:
   - Run dynamic trading for NYC
   - Check new snapshots have correct `start_local` format
   - Verify timeseries times are correct

---

## Notes

1. **Zeus API Behavior**: We assume Zeus API accepts ISO format with timezone. If Zeus actually requires UTC, we may need to convert local → UTC before sending, but keep `start_local` in local time.

2. **Timeseries Storage**: The field is named `time_utc` but may contain local times with timezone. Consider:
   - Option A: Keep as-is (times have timezone info)
   - Option B: Always store as UTC, convert when needed
   - Option C: Rename field to `time` and store with timezone

3. **Backward Compatibility**: The migration script fixes existing data. New data will be correct going forward.

---

## Next Steps

1. ✅ **Code fix applied** - New fetches will use correct timezone
2. ⏳ **Run migration script** - Fix existing NYC snapshots
3. ⏳ **Verify** - Check a few fixed snapshots manually
4. ⏳ **Monitor** - Watch new snapshots to ensure they're correct
5. ⏳ **Consider** - Whether to fix other stations (if they have same issue)

---

## Files Changed

- ✅ `agents/zeus_forecast.py` - Fixed timezone formatting
- ✅ `scripts/fix_nyc_snapshot_times.py` - Migration script (new)

---

**Status**: Ready to run migration script on existing data.

