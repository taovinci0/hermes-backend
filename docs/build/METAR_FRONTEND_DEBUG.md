# METAR Data Display - Frontend Debug Guide

**Date**: November 16, 2025  
**Issue**: METAR data not displaying on frontend despite API returning data

---

## ✅ Confirmed: API Has Data

**METAR observations available for today (2025-11-16):**
- **EGLC (London)**: 3 observations
  - 18:20 UTC → 48.2°F
  - 18:50 UTC → 48.2°F
  - 19:20 UTC → 48.2°F
- **Daily high**: 48.2°F

**API endpoints working:**
- ✅ `GET /api/metar/observations?station_code=EGLC&event_day=2025-11-16`
- ✅ `GET /api/metar/daily-high?station_code=EGLC&event_day=2025-11-16`

---

## 🔍 Debugging Steps

### Step 1: Verify API Call in Browser

Open browser DevTools (F12) → Network tab → Filter by "metar"

**Check:**
1. Is the API call being made?
2. What URL is being called?
3. What's the response status code?
4. What's the response body?

**Expected request:**
```
GET http://localhost:8000/api/metar/observations?station_code=EGLC&event_day=2025-11-16
```

**Expected response:**
```json
{
  "observations": [
    {
      "observation_time_utc": "2025-11-16T18:20:00+00:00",
      "fetch_time_utc": "2025-11-16T18:29:31.496834+00:00",
      "station_code": "EGLC",
      "event_day": "2025-11-16",
      "temp_C": 9,
      "temp_F": 48.2,
      "dewpoint_C": 2,
      "wind_dir": 40,
      "wind_speed": 5,
      "raw": "METAR EGLC 161820Z AUTO 04005KT 340V080 9999 OVC040 09/02 Q1014",
      "_filename": "2025-11-16_18-20-00.json"
    },
    // ... more observations
  ],
  "count": 3
}
```

### Step 2: Check Console for Errors

Open browser DevTools → Console tab

**Look for:**
- JavaScript errors
- API fetch errors
- Data processing errors
- Time matching errors

**Common errors:**
- `Failed to fetch` → CORS or network issue
- `Cannot read property 'observations' of undefined` → Response structure mismatch
- `observations is not iterable` → Response is not an array

### Step 3: Verify Data Processing

Add console logging to see what data is being processed:

```typescript
// After fetching METAR data
const response = await fetch(
  `/api/metar/observations?station_code=${stationCode}&event_day=${eventDay}`
);
const data = await response.json();

console.log('METAR API Response:', data);
console.log('Observations count:', data.count);
console.log('Observations array:', data.observations);

// Check if observations exist
if (!data.observations || data.observations.length === 0) {
  console.warn('⚠️ No METAR observations in response');
  return;
}

// Process each observation
data.observations.forEach((obs, idx) => {
  console.log(`Observation ${idx + 1}:`, {
    time: obs.observation_time_utc,
    tempF: obs.temp_F,
    station: obs.station_code
  });
});
```

### Step 4: Check Time Matching Logic

The frontend matches METAR observations to Zeus hourly times within 30 minutes. Verify this logic:

```typescript
// Example time matching function
function findClosestMETAR(zeusHour: Date, metarObservations: any[]): any | null {
  const zeusTime = zeusHour.getTime();
  const thirtyMinutes = 30 * 60 * 1000; // 30 minutes in milliseconds
  
  let closest: any | null = null;
  let minDiff = Infinity;
  
  for (const obs of metarObservations) {
    const obsTime = new Date(obs.observation_time_utc).getTime();
    const diff = Math.abs(zeusTime - obsTime);
    
    if (diff <= thirtyMinutes && diff < minDiff) {
      minDiff = diff;
      closest = obs;
    }
  }
  
  console.log(`Zeus hour: ${zeusHour.toISOString()}, Closest METAR:`, closest);
  return closest;
}
```

**Debug output:**
```typescript
// Log time matching results
zeusTimeseries.forEach((zeusPoint, idx) => {
  const zeusTime = new Date(zeusPoint.time_utc);
  const matchedMETAR = findClosestMETAR(zeusTime, metarObservations);
  
  console.log(`Hour ${idx} (${zeusTime.toISOString()}):`, {
    zeusTemp: zeusPoint.temp_F,
    metarTemp: matchedMETAR?.temp_F || 'NO MATCH',
    metarTime: matchedMETAR?.observation_time_utc || 'N/A'
  });
});
```

### Step 5: Verify Date Format

**Check if date format matches:**
- Frontend might be using: `2025-11-16` ✅
- Frontend might be using: `11/16/2025` ❌
- Frontend might be using: `Nov 16, 2025` ❌

**Ensure consistent format:**
```typescript
// Convert date to YYYY-MM-DD format
const eventDay = selectedDate.toISOString().split('T')[0];
// Result: "2025-11-16"
```

---

## 🐛 Common Issues & Fixes

### Issue 1: Empty Observations Array

**Symptom:** API returns `{"observations": [], "count": 0}`

**Possible causes:**
- Wrong date format
- Wrong station code
- No data collected yet

**Fix:**
```typescript
// Verify parameters before API call
console.log('API call params:', {
  station_code: stationCode,
  event_day: eventDay,
  url: `/api/metar/observations?station_code=${stationCode}&event_day=${eventDay}`
});
```

### Issue 2: Time Matching Too Strict

**Symptom:** METAR observations exist but don't match Zeus hours

**Possible causes:**
- 30-minute window too narrow
- Timezone mismatch
- Observation times don't align with hourly times

**Fix:**
```typescript
// Increase window or use different matching strategy
const windowMinutes = 60; // Increase to 60 minutes
const windowMs = windowMinutes * 60 * 1000;

// Or match to nearest hour regardless of window
function findNearestMETAR(zeusHour: Date, metarObservations: any[]): any | null {
  const zeusTime = zeusHour.getTime();
  let closest: any | null = null;
  let minDiff = Infinity;
  
  for (const obs of metarObservations) {
    const obsTime = new Date(obs.observation_time_utc).getTime();
    const diff = Math.abs(zeusTime - obsTime);
    
    if (diff < minDiff) {
      minDiff = diff;
      closest = obs;
    }
  }
  
  // Accept if within 2 hours (METAR updates hourly)
  if (minDiff <= 2 * 60 * 60 * 1000) {
    return closest;
  }
  
  return null;
}
```

### Issue 3: Response Structure Mismatch

**Symptom:** `Cannot read property 'observations' of undefined`

**Possible causes:**
- API returns different structure
- Error response not handled
- Response not parsed as JSON

**Fix:**
```typescript
try {
  const response = await fetch(url);
  
  if (!response.ok) {
    console.error('API error:', response.status, response.statusText);
    return;
  }
  
  const data = await response.json();
  
  // Verify structure
  if (!data || typeof data !== 'object') {
    console.error('Invalid response structure:', data);
    return;
  }
  
  if (!Array.isArray(data.observations)) {
    console.error('Observations is not an array:', data);
    return;
  }
  
  // Process data
  const observations = data.observations;
  console.log(`Found ${observations.length} METAR observations`);
  
} catch (error) {
  console.error('Fetch error:', error);
}
```

### Issue 4: Date/Time Parsing Issues

**Symptom:** Times don't match or are incorrect

**Possible causes:**
- Timezone conversion issues
- Date parsing errors
- UTC vs local time confusion

**Fix:**
```typescript
// Ensure consistent timezone handling
function parseMETARTime(timeStr: string): Date {
  // API returns UTC time, parse as UTC
  return new Date(timeStr); // JavaScript Date handles UTC automatically
}

// For display, convert to local time if needed
function formatTimeForDisplay(date: Date): string {
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  });
}
```

---

## 📊 Expected Data Structure

### METAR Observation Object

```typescript
interface METARObservation {
  observation_time_utc: string;  // "2025-11-16T18:20:00+00:00"
  fetch_time_utc: string;        // "2025-11-16T18:29:31.496834+00:00"
  station_code: string;          // "EGLC"
  event_day: string;             // "2025-11-16"
  temp_C: number;                // 9
  temp_F: number;                // 48.2
  dewpoint_C: number;            // 2
  wind_dir: number;              // 40
  wind_speed: number;            // 5
  raw: string;                   // "METAR EGLC 161820Z..."
  _filename: string;             // "2025-11-16_18-20-00.json"
}
```

### API Response Structure

```typescript
interface METARResponse {
  observations: METARObservation[];
  count: number;
}
```

---

## 🧪 Test API Directly

**Test in browser console:**
```javascript
// Test METAR API
fetch('http://localhost:8000/api/metar/observations?station_code=EGLC&event_day=2025-11-16')
  .then(r => r.json())
  .then(data => {
    console.log('METAR Response:', data);
    console.log('Count:', data.count);
    console.log('Observations:', data.observations);
    
    if (data.observations && data.observations.length > 0) {
      console.log('First observation:', data.observations[0]);
      console.log('Temperature:', data.observations[0].temp_F, '°F');
    } else {
      console.warn('⚠️ No observations in response');
    }
  })
  .catch(error => console.error('Error:', error));
```

**Expected output:**
```
METAR Response: {observations: Array(3), count: 3}
Count: 3
Observations: (3) [{...}, {...}, {...}]
First observation: {observation_time_utc: "2025-11-16T18:20:00+00:00", temp_F: 48.2, ...}
Temperature: 48.2 °F
```

---

## ✅ Quick Debug Checklist

- [ ] API call is being made (check Network tab)
- [ ] API returns 200 status code
- [ ] Response contains `observations` array
- [ ] `observations.length > 0`
- [ ] Each observation has `observation_time_utc` and `temp_F`
- [ ] Date format matches (`YYYY-MM-DD`)
- [ ] Station code matches (`EGLC`, `KLGA`, etc.)
- [ ] Time matching logic finds matches
- [ ] Chart receives data to plot
- [ ] No console errors

---

## 🔧 Recommended Debug Code

Add this to your METAR fetching function:

```typescript
async function fetchMETARData(stationCode: string, eventDay: string) {
  const url = `/api/metar/observations?station_code=${stationCode}&event_day=${eventDay}`;
  
  console.log('🔍 Fetching METAR data:', { stationCode, eventDay, url });
  
  try {
    const response = await fetch(url);
    console.log('📡 Response status:', response.status, response.statusText);
    
    if (!response.ok) {
      console.error('❌ API error:', response.status);
      return null;
    }
    
    const data = await response.json();
    console.log('📦 Response data:', data);
    console.log('📊 Observations count:', data.count);
    
    if (!data.observations || data.observations.length === 0) {
      console.warn('⚠️ No METAR observations found');
      return null;
    }
    
    console.log('✅ METAR data loaded:', data.observations.length, 'observations');
    data.observations.forEach((obs, idx) => {
      console.log(`  ${idx + 1}. ${obs.observation_time_utc} → ${obs.temp_F}°F`);
    });
    
    return data.observations;
    
  } catch (error) {
    console.error('❌ Fetch error:', error);
    return null;
  }
}
```

---

## 📝 Summary

**Current Status:**
- ✅ API has data (3 observations for EGLC today)
- ✅ API endpoints working correctly
- ❓ Frontend may not be calling API correctly
- ❓ Frontend may not be processing response correctly
- ❓ Time matching may be filtering out data

**Next Steps:**
1. Add console logging to see what API returns
2. Verify date format matches exactly
3. Check time matching logic
4. Verify chart receives data to plot

**The data is there - we just need to debug why the frontend isn't displaying it!**

