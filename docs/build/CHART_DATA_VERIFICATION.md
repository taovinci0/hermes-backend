# Chart Data Verification Report

**Date**: November 17, 2025  
**Chart**: Zeus Forecast Evolution for EGLC on 2025-11-17  
**Status**: ❌ **DATA MISMATCHES FOUND**

---

## 🔍 Issues Found

### Issue 1: Daily High Values Don't Match

**Chart shows:**
- 18:09 → 47.0°F
- 18:26 → 46.0°F
- 18:29 → 47.0°F
- 18:46 → 46.0°F
- 19:02 → 47.0°F

**Actual data from snapshots:**
- 18:09 (2025-11-16) → **51.5°F** ❌ (Chart shows 47.0°F)
- 18:26 (2025-11-16) → **51.1°F** ❌ (Chart shows 46.0°F)
- 18:29 (2025-11-16) → **51.7°F** ❌ (Chart shows 47.0°F)
- 18:46 (2025-11-16) → **50.9°F** ❌ (Chart shows 46.0°F)
- 19:02 (2025-11-16) → **51.5°F** ❌ (Chart shows 47.0°F)

**For 2025-11-17 (the date shown in chart):**
- Latest snapshots are at: 14:20, 14:36, 14:53, 15:10, 15:26
- Daily highs: **46.5°F** (not 47.0°F or 46.0°F)

### Issue 2: Date/Time Mismatch

**Chart shows:**
- Date: 2025-11-17
- Times: 18:09, 18:26, 18:29, 18:46, 19:02

**Problem:**
- Those times (18:09, 18:26, etc.) are from **2025-11-16**, not 2025-11-17
- For 2025-11-17, the latest snapshots are at different times (14:20, 14:36, etc.)

### Issue 3: "Zeus Median" Calculation

**Chart shows:** "Zeus Median" as a dashed blue line

**Intent:** ✅ **This is intentional!** Zeus Median is calculated by the frontend as the median of all hourly temperatures across all snapshots for that day. This provides a more stable, consensus view than just the latest forecast.

**Calculation method:**
1. Get all Zeus snapshots for the day
2. For each hour (00:00 to 23:00), collect temperatures from all snapshots
3. Calculate the median temperature for each hour
4. Plot as a dashed line

**This is a valid and useful metric** - it shows the consensus forecast across all predictions.

---

## ✅ Correct Data for 2025-11-17

### Zeus Snapshots (Latest 5)

```
14:20 → 46.5°F
14:36 → 46.5°F
14:53 → 46.5°F
15:10 → 46.5°F
15:26 → 46.5°F
```

### METAR Observations

```
08:50 → 42.8°F
10:20 → 42.8°F
11:20 → 44.6°F
11:50 → 46.4°F
12:20 → 46.4°F
12:50 → 46.4°F
13:20 → 46.4°F
13:50 → 46.4°F
14:20 → 46.4°F
14:50 → 46.4°F
15:20 → 46.4°F
```

**Daily High (METAR):** 46.4°F

---

## 🐛 Root Causes

### 1. Wrong Date Being Used

The frontend is likely:
- Showing date as 2025-11-17
- But fetching/displaying data from 2025-11-16
- Or mixing data from multiple days

**Fix:** Verify the `event_day` parameter matches the date selector

### 2. Incorrect Daily High Calculation

The daily high values don't match. Possible issues:
- Not calculating max temperature correctly
- Using wrong temperature field
- Rounding errors
- Using a different calculation method

**Fix:** Verify daily high calculation:
```typescript
// Correct calculation
const temps_f = timeseries.map(point => {
  const temp_c = point.temp_K - 273.15;
  return (temp_c * 9/5) + 32;
});
const daily_high = Math.max(...temps_f);
```

### 3. "Zeus Median" Calculation

"Zeus Median" doesn't exist in the API. The frontend must be calculating it. Possible sources:
- Median of multiple snapshots?
- Median of timeseries temperatures?
- Some other calculation?

**Fix:** Clarify what "Zeus Median" should represent, or remove it if not needed

---

## ✅ Verification Steps

### Step 1: Verify API Call

Check what the frontend is actually calling:

```javascript
// In browser console
console.log('Fetching Zeus for:', {
  station: 'EGLC',
  event_day: '2025-11-17'  // Verify this matches chart date
});
```

### Step 2: Verify Daily High Calculation

Add logging to see calculated values:

```typescript
function calculateDailyHigh(timeseries: any[]): number {
  const temps_f = timeseries.map(point => {
    const temp_c = point.temp_K - 273.15;
    const temp_f = (temp_c * 9/5) + 32;
    return temp_f;
  });
  
  const daily_high = Math.max(...temps_f);
  
  console.log('Daily high calculation:', {
    temps_f: temps_f.slice(0, 5), // First 5 temps
    max: daily_high,
    all_temps_range: `${Math.min(...temps_f).toFixed(1)} to ${Math.max(...temps_f).toFixed(1)}`
  });
  
  return daily_high;
}
```

### Step 3: Verify Date Consistency

Ensure the date used for API calls matches the chart date:

```typescript
// Verify date format
const eventDay = selectedDate.toISOString().split('T')[0];
console.log('Using event_day:', eventDay); // Should be "2025-11-17"

// Verify API response matches
const response = await fetch(`/api/snapshots/zeus?station_code=EGLC&event_day=${eventDay}`);
const data = await response.json();

data.snapshots.forEach(snapshot => {
  console.log('Snapshot:', {
    fetch_time: snapshot.fetch_time_utc,
    forecast_day: snapshot.forecast_for_local_day, // Should match eventDay
    daily_high: calculateDailyHigh(snapshot.timeseries)
  });
});
```

---

## 📊 Expected vs Actual

### For 2025-11-17 (Current Date)

**Expected Daily High Predictions:**
```
14:20 → 46.5°F
14:36 → 46.5°F
14:53 → 46.5°F
15:10 → 46.5°F
15:26 → 46.5°F
```

**Chart Currently Shows:**
```
18:09 → 47.0°F  ❌ (Wrong time, wrong value)
18:26 → 46.0°F  ❌ (Wrong time, wrong value)
18:29 → 47.0°F  ❌ (Wrong time, wrong value)
18:46 → 46.0°F  ❌ (Wrong time, wrong value)
19:02 → 47.0°F  ❌ (Wrong time, wrong value)
```

---

## 🔧 Recommended Fixes

### Fix 1: Correct Date Handling

```typescript
// Ensure date is in YYYY-MM-DD format
const eventDay = selectedDate.toISOString().split('T')[0];

// Verify before API call
if (!/^\d{4}-\d{2}-\d{2}$/.test(eventDay)) {
  console.error('Invalid date format:', eventDay);
  return;
}
```

### Fix 2: Correct Daily High Calculation

```typescript
function calculateDailyHigh(timeseries: any[]): number {
  if (!timeseries || timeseries.length === 0) {
    return 0;
  }
  
  const temps_f = timeseries.map(point => {
    // Convert Kelvin to Fahrenheit
    const temp_c = point.temp_K - 273.15;
    const temp_f = (temp_c * 9/5) + 32;
    return temp_f;
  });
  
  const daily_high = Math.max(...temps_f);
  
  // Round to 1 decimal place
  return Math.round(daily_high * 10) / 10;
}
```

### Fix 3: Remove or Fix "Zeus Median"

**Option A: Remove it** (if not needed)
```typescript
// Don't plot "Zeus Median" line
```

**Option B: Calculate median of daily highs** (if that's the intent)
```typescript
// Calculate median of daily highs from multiple snapshots
function calculateMedianDailyHigh(snapshots: any[]): number[] {
  const daily_highs = snapshots.map(s => calculateDailyHigh(s.timeseries));
  daily_highs.sort((a, b) => a - b);
  const median = daily_highs[Math.floor(daily_highs.length / 2)];
  
  // Return array of median values for each hour (if needed)
  // Or just return the median daily high
  return median;
}
```

---

## ✅ Verification Checklist

- [ ] Date selector matches API call date
- [ ] Daily high calculation is correct (Kelvin → Fahrenheit → Max)
- [ ] Snapshot times match chart times
- [ ] Daily high values match calculated values
- [ ] "Zeus Median" is either removed or correctly calculated
- [ ] METAR observations match API response
- [ ] All temperatures are in Fahrenheit

---

## 📝 Summary

**Current Status:** ❌ **Data is incorrect**

**Main Issues:**
1. Daily high values don't match (47.0°F vs 51.5°F actual)
2. Times shown don't match snapshot times for the selected date
3. "Zeus Median" field doesn't exist in API

**Next Steps:**
1. Fix date handling to ensure correct day is used
2. Verify daily high calculation logic
3. Remove or properly implement "Zeus Median"
4. Add debug logging to verify data flow

