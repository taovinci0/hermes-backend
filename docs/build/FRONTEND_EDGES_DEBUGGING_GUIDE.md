# Frontend: Current Edges Not Displaying - Debugging Guide

## Problem

The "Current Edges" panel shows "No edges available" even though:
- Trades are being placed (visible in activity logs)
- Backend API returns edges correctly
- Decision snapshots exist with edge data

## Quick Verification

### 1. Test API Endpoint Directly

```bash
# Test with specific station and event day
curl "http://localhost:8000/api/edges/current?station_code=KLGA&event_day=2025-11-19"

# Test with just station (should return all event days)
curl "http://localhost:8000/api/edges/current?station_code=KLGA"

# Test summary endpoint
curl "http://localhost:8000/api/edges/summary?station_code=KLGA&event_day=2025-11-19"
```

**Expected Response:**
```json
{
  "edges": [
    {
      "station_code": "KLGA",
      "city": "New York (Airport)",
      "event_day": "2025-11-19",
      "decision_time_utc": "2025-11-19T22:47:56.746933+00:00",
      "bracket": "45-46°F",
      "lower_f": 45,
      "upper_f": 46,
      "market_id": "687152",
      "edge": 0.125203501067666,
      "edge_pct": 12.520350106766601,
      "f_kelly": 0.13327013613573385,
      "size_usd": 300.0,
      "reason": "strong_edge, kelly_capped"
    }
  ],
  "count": 1
}
```

### 2. Check Browser Network Tab

1. Open browser DevTools (F12)
2. Go to Network tab
3. Filter by "edges"
4. Look for requests to `/api/edges/current`
5. Check:
   - **Request URL**: What parameters are being sent?
   - **Response Status**: Should be 200
   - **Response Body**: Does it contain edges?

## Common Issues to Check

### Issue 1: Date Format Mismatch

**Problem:** Frontend using `19-11-2025` but API expects `2025-11-19`

**Check:**
```javascript
// ❌ WRONG - Don't use DD-MM-YYYY
const eventDay = "19-11-2025";

// ✅ CORRECT - Use YYYY-MM-DD
const eventDay = "2025-11-19";
```

**Fix:**
```javascript
// Convert date format before API call
function formatDateForAPI(dateString) {
  // If format is DD-MM-YYYY, convert to YYYY-MM-DD
  const parts = dateString.split('-');
  if (parts[0].length === 2) {
    // DD-MM-YYYY format
    return `${parts[2]}-${parts[1]}-${parts[0]}`;
  }
  return dateString; // Already YYYY-MM-DD
}

const apiDate = formatDateForAPI(selectedEventDay);
```

### Issue 2: Event Day Mismatch

**Problem:** Frontend filtering by old event day, but most recent trades are for a different day

**Check:**
- What event day is the frontend filtering by?
- What event day do the most recent trades use?
- Are you showing edges for the correct event day?

**Fix:**
```javascript
// Option 1: Show edges for most recent event day
const response = await fetch('/api/edges/current?station_code=KLGA');
const data = await response.json();

// Group by event_day and show most recent
const edgesByDay = {};
data.edges.forEach(edge => {
  if (!edgesByDay[edge.event_day]) {
    edgesByDay[edge.event_day] = [];
  }
  edgesByDay[edge.event_day].push(edge);
});

const mostRecentDay = Object.keys(edgesByDay).sort().reverse()[0];
const currentEdges = edgesByDay[mostRecentDay] || [];

// Option 2: Show edges for all event days
// Just use data.edges directly
```

### Issue 3: API Call Not Being Made

**Check:**
- Is the API call actually being executed?
- Is it being called with the correct parameters?
- Is there an error in the console?

**Debug Code:**
```javascript
async function fetchEdges(stationCode, eventDay) {
  const params = new URLSearchParams({
    station_code: stationCode,
  });
  
  if (eventDay) {
    params.append('event_day', eventDay); // Make sure it's YYYY-MM-DD
  }
  
  console.log('Fetching edges with params:', params.toString());
  
  try {
    const response = await fetch(`/api/edges/current?${params}`);
    console.log('Response status:', response.status);
    
    const data = await response.json();
    console.log('Edges data:', data);
    console.log('Edge count:', data.count);
    console.log('Edges array:', data.edges);
    
    return data.edges || [];
  } catch (error) {
    console.error('Error fetching edges:', error);
    return [];
  }
}
```

### Issue 4: Response Not Being Parsed Correctly

**Check:**
- Is the response being parsed as JSON?
- Is the data structure what you expect?
- Are you accessing `data.edges` or just `data`?

**Debug Code:**
```javascript
const response = await fetch('/api/edges/current?station_code=KLGA');
const data = await response.json();

console.log('Full response:', data);
console.log('Edges array:', data.edges);
console.log('Count:', data.count);

// Make sure you're using data.edges, not data
const edges = data.edges || [];
```

### Issue 5: Empty Array Check

**Check:**
- Are you checking if `edges.length === 0` correctly?
- Is the "No edges" message showing even when edges exist?

**Debug Code:**
```javascript
const edges = data.edges || [];

console.log('Edges length:', edges.length);
console.log('Edges:', edges);

if (edges.length === 0) {
  console.log('No edges - showing empty state');
  // Show "No edges available" message
} else {
  console.log('Found edges - rendering table');
  // Render edges table
}
```

### Issue 6: Component Not Re-rendering

**Check:**
- Is the component state being updated?
- Is React re-rendering when edges change?
- Are you using the correct state setter?

**Debug Code (React):**
```javascript
const [edges, setEdges] = useState([]);

useEffect(() => {
  async function loadEdges() {
    const data = await fetchEdges(stationCode, eventDay);
    console.log('Setting edges:', data);
    setEdges(data);
  }
  
  loadEdges();
  
  // Poll every 15 seconds for updates
  const interval = setInterval(loadEdges, 15000);
  return () => clearInterval(interval);
}, [stationCode, eventDay]);

console.log('Current edges state:', edges);
```

## Step-by-Step Debugging Checklist

1. **Verify API is accessible:**
   ```bash
   curl "http://localhost:8000/api/edges/current?station_code=KLGA"
   ```
   - Should return JSON with edges array
   - If not, backend issue

2. **Check browser console:**
   - Open DevTools → Console
   - Look for errors or warnings
   - Check network requests

3. **Check network requests:**
   - DevTools → Network tab
   - Filter: "edges"
   - Check request URL, parameters, response

4. **Add console.log statements:**
   ```javascript
   console.log('Station:', stationCode);
   console.log('Event Day:', eventDay);
   console.log('API URL:', apiUrl);
   console.log('Response:', response);
   console.log('Edges:', edges);
   ```

5. **Check date format:**
   ```javascript
   console.log('Event day format:', eventDay);
   console.log('Is YYYY-MM-DD?', /^\d{4}-\d{2}-\d{2}$/.test(eventDay));
   ```

6. **Check response structure:**
   ```javascript
   console.log('Response keys:', Object.keys(data));
   console.log('Has edges?', 'edges' in data);
   console.log('Edges type:', typeof data.edges);
   console.log('Edges is array?', Array.isArray(data.edges));
   ```

## Expected API Behavior

### Endpoint: `GET /api/edges/current`

**Query Parameters:**
- `station_code` (optional): Filter by station (e.g., "KLGA")
- `event_day` (optional): Filter by event day in `YYYY-MM-DD` format (e.g., "2025-11-19")
- `limit` (optional): Maximum number of edges (default: 100)

**Response Format:**
```json
{
  "edges": [
    {
      "station_code": "KLGA",
      "city": "New York (Airport)",
      "event_day": "2025-11-19",
      "decision_time_utc": "2025-11-19T22:47:56.746933+00:00",
      "bracket": "45-46°F",
      "lower_f": 45,
      "upper_f": 46,
      "market_id": "687152",
      "edge": 0.125203501067666,
      "edge_pct": 12.520350106766601,
      "f_kelly": 0.13327013613573385,
      "size_usd": 300.0,
      "reason": "strong_edge, kelly_capped"
    }
  ],
  "count": 1
}
```

**Notes:**
- `edges` is always an array (may be empty)
- `count` is the length of the edges array
- Edges are sorted by `edge_pct` (descending, best first)
- Each bracket only shows the most recent edge (deduplicated)

## Recommended Frontend Implementation

### Option 1: Show Most Recent Event Day

```javascript
// Fetch edges for all event days, show most recent
const response = await fetch('/api/edges/current?station_code=KLGA');
const data = await response.json();

// Group by event_day
const edgesByDay = {};
data.edges.forEach(edge => {
  if (!edgesByDay[edge.event_day]) {
    edgesByDay[edge.event_day] = [];
  }
  edgesByDay[edge.event_day].push(edge);
});

// Get most recent day
const days = Object.keys(edgesByDay).sort().reverse();
const mostRecentDay = days[0];
const currentEdges = edgesByDay[mostRecentDay] || [];

// Update event day selector to show mostRecentDay
setSelectedEventDay(mostRecentDay);
setEdges(currentEdges);
```

### Option 2: Show All Event Days

```javascript
// Fetch edges for all event days
const response = await fetch('/api/edges/current?station_code=KLGA');
const data = await response.json();

// Show all edges, grouped by event_day
setEdges(data.edges);

// In UI, group by event_day for display
const groupedEdges = data.edges.reduce((acc, edge) => {
  if (!acc[edge.event_day]) {
    acc[edge.event_day] = [];
  }
  acc[edge.event_day].push(edge);
  return acc;
}, {});
```

### Option 3: Auto-Update Event Day

```javascript
// When new trades are detected, update event day selector
useEffect(() => {
  async function checkForNewEdges() {
    const response = await fetch('/api/edges/current?station_code=KLGA');
    const data = await response.json();
    
    if (data.edges.length > 0) {
      // Find most recent event day
      const mostRecentDay = data.edges
        .map(e => e.event_day)
        .sort()
        .reverse()[0];
      
      // Update if different from current selection
      if (mostRecentDay !== selectedEventDay) {
        setSelectedEventDay(mostRecentDay);
      }
      
      // Filter edges for selected day
      const filteredEdges = data.edges.filter(
        e => e.event_day === selectedEventDay
      );
      setEdges(filteredEdges);
    }
  }
  
  checkForNewEdges();
  const interval = setInterval(checkForNewEdges, 15000);
  return () => clearInterval(interval);
}, [selectedEventDay]);
```

## Testing Checklist

- [ ] API endpoint returns data when tested directly (curl)
- [ ] Browser network tab shows API request being made
- [ ] API request has correct parameters (station_code, event_day)
- [ ] API response status is 200 (not 404, 500, etc.)
- [ ] API response contains `edges` array
- [ ] `edges` array is not empty (check `data.count > 0`)
- [ ] Date format is `YYYY-MM-DD` (not `DD-MM-YYYY`)
- [ ] Component state is being updated with edges
- [ ] Component is re-rendering when edges change
- [ ] Empty state only shows when `edges.length === 0`
- [ ] Event day selector includes all days with open markets

## Quick Test Script

Add this to your component for debugging:

```javascript
useEffect(() => {
  async function debugEdges() {
    console.log('=== EDGES DEBUG ===');
    console.log('Station:', stationCode);
    console.log('Event Day:', eventDay);
    
    const url = `/api/edges/current?station_code=${stationCode}&event_day=${eventDay}`;
    console.log('API URL:', url);
    
    try {
      const response = await fetch(url);
      console.log('Response status:', response.status);
      
      const data = await response.json();
      console.log('Response data:', data);
      console.log('Edges count:', data.count);
      console.log('Edges array:', data.edges);
      
      if (data.edges && data.edges.length > 0) {
        console.log('✅ Edges found!');
        data.edges.forEach((edge, i) => {
          console.log(`  Edge ${i + 1}:`, edge.bracket, `edge=${edge.edge_pct}%`);
        });
      } else {
        console.log('❌ No edges in response');
      }
    } catch (error) {
      console.error('❌ Error:', error);
    }
  }
  
  debugEdges();
}, [stationCode, eventDay]);
```

## Most Likely Issues

Based on the symptoms, the most likely issues are:

1. **Date format mismatch** - Frontend using `19-11-2025` instead of `2025-11-19`
2. **Event day mismatch** - Filtering by 2025-11-19 but edges are for 2025-11-20
3. **Not calling API** - API call not being made or failing silently
4. **Response parsing** - Not accessing `data.edges` correctly

Start with checking the browser network tab and console logs!

