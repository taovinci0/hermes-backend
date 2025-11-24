# Market Probability History Graph - Troubleshooting Guide

**Date**: 2025-11-21  
**Issue**: Market Probability History graph on performance pages not displaying Polymarket snapshots

---

## Overview

The Market Probability History graph should display market-implied probabilities for each temperature bracket over time, showing how market prices evolved from market open to close.

**Expected Behavior**:
- Graph shows multiple lines (one per bracket)
- Each line shows probability (0-100%) over time
- Data comes from Polymarket snapshots
- X-axis: Time (market open → close)
- Y-axis: Probability (0-100%)

---

## API Endpoint

### Endpoint Details

**URL**: `GET /api/snapshots/polymarket`

**Query Parameters**:
- `city` (required): City name (e.g., "London", "New York (Airport)")
- `event_day` (optional): Event date in YYYY-MM-DD format
- `limit` (optional): Maximum number of snapshots (default: 100)

**Example Request**:
```
GET /api/snapshots/polymarket?city=London&event_day=2025-11-16
```

**Response Format**:
```json
{
  "snapshots": [
    {
      "fetch_time_utc": "2025-11-16T14:00:02.619918+00:00",
      "event_day": "2025-11-16",
      "city": "London",
      "markets": [
        {
          "market_id": "682592",
          "bracket": "42-43°F",
          "lower_f": 42,
          "upper_f": 43,
          "mid_price": 0.0115,
          "closed": false
        },
        {
          "market_id": "682594",
          "bracket": "44-45°F",
          "lower_f": 44,
          "upper_f": 45,
          "mid_price": 0.175,
          "closed": false
        }
      ],
      "_filename": "2025-11-16_14-00-02.json"
    }
  ],
  "count": 15
}
```

---

## Troubleshooting Steps

### Step 1: Verify API Endpoint is Working

**Test the API directly**:

```bash
# Test with curl
curl "http://localhost:8000/api/snapshots/polymarket?city=London&event_day=2025-11-16"

# Or in browser
http://localhost:8000/api/snapshots/polymarket?city=London&event_day=2025-11-16
```

**Expected**: Returns JSON with `snapshots` array and `count` field.

**If API returns empty**:
- Check if snapshots exist: `ls data/snapshots/dynamic/polymarket/London/2025-11-16/`
- Check city name spelling (case-sensitive, spaces matter)
- Check event_day format (must be YYYY-MM-DD)

---

### Step 2: Check City Name Matching

**Common Issue**: City name mismatch between frontend and backend.

**Backend expects**: Exact city name as stored in snapshots
- London → `London`
- New York → `New York (Airport)` (check actual city name in snapshots)

**How to find correct city name**:
```bash
# List available cities
ls data/snapshots/dynamic/polymarket/

# Check actual city name in snapshot
cat data/snapshots/dynamic/polymarket/London/2025-11-16/*.json | jq -r '.city' | head -1
```

**Fix**: Use exact city name from snapshots in API call.

---

### Step 3: Check Snapshot File Structure

**Verify snapshot files exist and are valid**:

```bash
# Check if directory exists
ls -la data/snapshots/dynamic/polymarket/London/2025-11-16/

# Check if files are valid JSON
cat data/snapshots/dynamic/polymarket/London/2025-11-16/*.json | jq . | head -20

# Count snapshots
find data/snapshots/dynamic/polymarket/London/2025-11-16 -name "*.json" | wc -l
```

**Expected**:
- Directory exists: `data/snapshots/dynamic/polymarket/{city}/{event_day}/`
- Files are valid JSON
- Files have `fetch_time_utc`, `event_day`, `city`, `markets` fields

---

### Step 4: Check Data Format

**Verify snapshot data structure**:

Each snapshot should have:
- ✅ `fetch_time_utc`: Timestamp when snapshot was taken
- ✅ `event_day`: Event date (YYYY-MM-DD)
- ✅ `city`: City name
- ✅ `markets`: Array of market objects
  - ✅ `market_id`: Market identifier
  - ✅ `bracket`: Bracket name (e.g., "44-45°F")
  - ✅ `lower_f`, `upper_f`: Bracket bounds
  - ✅ `mid_price`: Market price (0.0-1.0) - **This is what graph needs!**
  - ✅ `closed`: Whether market is closed

**Check for missing `mid_price`**:
```bash
# Check if any markets have null mid_price
cat data/snapshots/dynamic/polymarket/London/2025-11-16/*.json | \
  jq '[.markets[] | select(.mid_price == null)] | length'
```

**If many null prices**: Markets might be closed or have no liquidity.

---

### Step 5: Check Frontend API Call

**Verify frontend is calling API correctly**:

**Expected Frontend Code**:
```typescript
const response = await fetch(
  `/api/snapshots/polymarket?city=${city}&event_day=${eventDay}`
);
const data = await response.json();
```

**Common Issues**:
1. **Wrong city name**: Frontend using different name than stored
2. **Wrong date format**: Not using YYYY-MM-DD
3. **Missing error handling**: API error not caught
4. **CORS issues**: Check browser console for CORS errors

**Debug**:
```javascript
// Add logging
console.log('Fetching Polymarket snapshots:', { city, eventDay });
const response = await fetch(`/api/snapshots/polymarket?city=${city}&event_day=${eventDay}`);
console.log('Response status:', response.status);
const data = await response.json();
console.log('Snapshot data:', data);
console.log('Snapshot count:', data.count);
console.log('First snapshot:', data.snapshots[0]);
```

---

### Step 6: Check Data Processing

**Verify frontend processes data correctly**:

**Expected Processing**:
```typescript
// Process snapshots into graph data
const graphData = snapshots.map(snapshot => {
  const timestamp = new Date(snapshot.fetch_time_utc);
  
  // Extract prices for each bracket
  const bracketData = {};
  snapshot.markets.forEach(market => {
    if (market.mid_price !== null) {
      bracketData[market.bracket] = market.mid_price * 100; // Convert to percentage
    }
  });
  
  return {
    timestamp,
    time: formatTime(timestamp), // For X-axis
    ...bracketData // Spread bracket prices
  };
});
```

**Common Issues**:
1. **Not filtering null prices**: Markets with `mid_price: null` should be skipped
2. **Not converting to percentage**: `mid_price` is 0.0-1.0, need to multiply by 100
3. **Wrong timestamp parsing**: Not parsing `fetch_time_utc` correctly
4. **Not grouping by bracket**: Need to group markets by bracket name

---

### Step 7: Check Graph Configuration

**Verify graph is configured correctly**:

**Expected Graph Setup**:
```typescript
// X-axis: Time
<XAxis 
  dataKey="time"
  type="category" // or "number" with time scale
  domain={[minTime, maxTime]}
/>

// Y-axis: Probability (0-100%)
<YAxis 
  domain={[0, 100]}
  label={{ value: 'Probability (%)', angle: -90 }}
/>

// Multiple lines (one per bracket)
{Object.keys(brackets).map(bracket => (
  <Line 
    key={bracket}
    dataKey={bracket}
    name={bracket}
    stroke={getColorForBracket(bracket)}
  />
))}
```

**Common Issues**:
1. **Wrong dataKey**: Using wrong field name for Y-axis
2. **Missing lines**: Not creating Line components for each bracket
3. **Domain issues**: Y-axis domain not set correctly (should be 0-100)
4. **Data format**: Graph expects different data structure

---

### Step 8: Check Browser Console

**Look for errors in browser console**:

1. **Network errors**: Check Network tab for failed API calls
2. **JavaScript errors**: Check Console tab for errors
3. **Data validation errors**: Check if data structure matches expectations

**Common Console Errors**:
- `Cannot read property 'markets' of undefined` → Snapshot structure issue
- `mid_price is not a number` → Null price not handled
- `timestamp is invalid` → Date parsing issue

---

## Common Issues and Solutions

### Issue 1: No Data Displayed

**Symptoms**: Graph shows but no lines/data points

**Possible Causes**:
1. API returns empty array
2. All `mid_price` values are null
3. Data processing filters out all data
4. Graph not configured to show data

**Solutions**:
- Check API response: `console.log(data.snapshots)`
- Check if markets have prices: `console.log(snapshot.markets.map(m => m.mid_price))`
- Verify data processing: `console.log(graphData)`
- Check graph data binding: Verify `data` prop is passed to chart

---

### Issue 2: Wrong City Name

**Symptoms**: API returns empty array, but snapshots exist

**Solution**:
```bash
# Find correct city name
ls data/snapshots/dynamic/polymarket/

# Check city name in snapshot
cat data/snapshots/dynamic/polymarket/London/2025-11-16/*.json | jq -r '.city' | head -1
```

**Fix**: Use exact city name (case-sensitive, spaces matter)

---

### Issue 3: Null Prices

**Symptoms**: Some brackets show, others don't

**Cause**: Markets with `mid_price: null` (closed or no liquidity)

**Solution**: Filter out null prices in frontend:
```typescript
snapshot.markets
  .filter(market => market.mid_price !== null)
  .forEach(market => {
    // Process market
  });
```

---

### Issue 4: Time Format Issues

**Symptoms**: Data points at wrong X positions

**Cause**: Timestamp parsing or timezone conversion issue

**Solution**: Ensure consistent timezone handling:
```typescript
// Parse UTC timestamp
const timestamp = new Date(snapshot.fetch_time_utc);

// Convert to local time for display (if needed)
const localTime = timestamp.toLocaleTimeString('en-US', { 
  hour12: false,
  hour: '2-digit',
  minute: '2-digit'
});
```

---

### Issue 5: Bracket Name Mismatch

**Symptoms**: Lines not grouping correctly

**Cause**: Bracket names not matching between snapshots

**Solution**: Normalize bracket names:
```typescript
// Normalize bracket name
const normalizeBracket = (bracket: string) => {
  return bracket.replace(/\s+/g, '').toLowerCase();
};

// Group by normalized name
const grouped = markets.reduce((acc, market) => {
  const key = normalizeBracket(market.bracket);
  acc[key] = market.mid_price * 100;
  return acc;
}, {});
```

---

## Diagnostic Commands

### Check API Response
```bash
curl "http://localhost:8000/api/snapshots/polymarket?city=London&event_day=2025-11-16" | jq '.count'
```

### Check Snapshot Files
```bash
# Count snapshots
find data/snapshots/dynamic/polymarket/London/2025-11-16 -name "*.json" | wc -l

# Check first snapshot
cat data/snapshots/dynamic/polymarket/London/2025-11-16/*.json | jq '.[0]' | head -30

# Check for null prices
cat data/snapshots/dynamic/polymarket/London/2025-11-16/*.json | \
  jq '[.markets[] | select(.mid_price == null)] | length'
```

### Check Available Cities
```bash
ls data/snapshots/dynamic/polymarket/
```

### Check Available Dates
```bash
ls data/snapshots/dynamic/polymarket/London/
```

---

## Expected Data Flow

```
1. Frontend calls: GET /api/snapshots/polymarket?city=London&event_day=2025-11-16
   ↓
2. Backend: SnapshotService.get_polymarket_snapshots()
   - Reads from: data/snapshots/dynamic/polymarket/London/2025-11-16/
   - Returns: Array of snapshot objects
   ↓
3. Frontend receives: { snapshots: [...], count: N }
   ↓
4. Frontend processes:
   - Extract fetch_time_utc → timestamp
   - Extract markets[].mid_price → probability
   - Group by bracket
   - Convert to graph data format
   ↓
5. Graph displays:
   - X-axis: Time (from fetch_time_utc)
   - Y-axis: Probability (mid_price * 100)
   - Lines: One per bracket
```

---

## Quick Checklist

- [ ] API endpoint is accessible: `curl http://localhost:8000/api/snapshots/polymarket?city=London&event_day=2025-11-16`
- [ ] API returns data: `count > 0`
- [ ] Snapshot files exist: `ls data/snapshots/dynamic/polymarket/{city}/{date}/`
- [ ] City name matches exactly (case-sensitive, spaces matter)
- [ ] Event day format is YYYY-MM-DD
- [ ] Markets have `mid_price` values (not all null)
- [ ] Frontend calls API with correct parameters
- [ ] Frontend processes data correctly (converts to percentage)
- [ ] Frontend filters out null prices
- [ ] Graph receives data in correct format
- [ ] Graph configured with correct dataKeys
- [ ] Graph has Line components for each bracket
- [ ] Browser console shows no errors

## Important Notes

### City Name Format

**Directory names use underscores**: `New_York_(Airport)`
**API expects**: Exact city name as stored in snapshot JSON (check `.city` field)

**To find correct city name**:
```bash
# Check what city name is in snapshots
cat data/snapshots/dynamic/polymarket/London/2025-11-16/*.json | jq -r '.city' | head -1
```

### Null Prices

**Some markets may have `mid_price: null`**:
- Closed markets
- Markets with no liquidity
- Markets that haven't opened yet

**Frontend must filter these out**:
```typescript
snapshot.markets
  .filter(market => market.mid_price !== null && !market.closed)
  .forEach(market => {
    // Process market
  });
```

---

## Testing

### Test API Endpoint
```bash
# Test with different cities
curl "http://localhost:8000/api/snapshots/polymarket?city=London&event_day=2025-11-16"
curl "http://localhost:8000/api/snapshots/polymarket?city=New%20York%20(Airport)&event_day=2025-11-17"

# Test without event_day (should return all)
curl "http://localhost:8000/api/snapshots/polymarket?city=London&limit=10"
```

### Test Data Structure
```bash
# Check snapshot structure
cat data/snapshots/dynamic/polymarket/London/2025-11-16/*.json | \
  jq '{
    fetch_time_utc: .fetch_time_utc,
    event_day: .event_day,
    city: .city,
    market_count: (.markets | length),
    markets_with_price: ([.markets[] | select(.mid_price != null)] | length)
  }' | head -20
```

---

## Next Steps if Still Not Working

1. **Check backend logs**: Look for errors in snapshot service
2. **Check frontend logs**: Browser console for errors
3. **Verify data exists**: Ensure snapshots were actually created
4. **Test with known good data**: Use a date/city that definitely has snapshots
5. **Compare with working graph**: Check how Graph 1 (Zeus) works and compare

---

## Related Files

- **Backend API**: `backend/api/routes/snapshots.py` (line 40-63)
- **Backend Service**: `backend/api/services/snapshot_service.py` (line 61-100)
- **Snapshot Location**: `data/snapshots/dynamic/polymarket/{city}/{event_day}/`
- **Frontend Spec**: `docs/build/PERFORMANCE_GRAPHS_FINAL_SPEC.md` (line 523-531)

---

**Status**: ⚠️ **Troubleshooting Guide Created** - Use this to diagnose why graph isn't displaying Polymarket snapshots.

