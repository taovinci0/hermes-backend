# Current Edges Display Issue

## Problem

The "Current Edges" panel shows "No edges available" even though:
1. Trades are being placed (visible in activity logs)
2. Decision snapshots exist with edges
3. API returns edges correctly

## Root Cause

**Event Day Mismatch:**

- The frontend is filtering by `event_day=2025-11-19` (19-11-2025)
- The most recent trades are for `event_day=2025-11-20` (20-11-2025)
- The API correctly returns edges for 2025-11-19, but they're from an earlier cycle (22:47:56)
- The most recent edges are for 2025-11-20 (23:04:42)

## Current Behavior

### API Response for 2025-11-19:
```json
{
  "edges": [
    {
      "station_code": "KLGA",
      "event_day": "2025-11-19",
      "decision_time_utc": "2025-11-19T22:47:56.746933+00:00",
      "bracket": "45-46°F",
      "edge_pct": 12.52,
      "size_usd": 300.0
    }
  ],
  "count": 1
}
```

### API Response for 2025-11-20:
```json
{
  "edges": [
    {
      "station_code": "KLGA",
      "event_day": "2025-11-20",
      "decision_time_utc": "2025-11-19T23:04:42.587193+00:00",
      "bracket": "43-44°F",
      "edge_pct": 25.38,
      "size_usd": 300.0
    },
    {
      "station_code": "KLGA",
      "event_day": "2025-11-20",
      "bracket": "45-46°F",
      "edge_pct": 10.35,
      "size_usd": 300.0
    }
  ],
  "count": 2
}
```

## Solution Options

### Option 1: Show Edges for Most Recent Event Day (Recommended)

The frontend should automatically show edges for the **most recent event day** with open markets, not just the selected date.

**Implementation:**
1. When filtering by station only, show edges for the most recent event day
2. Or show edges for all event days (grouped by event_day)
3. Update the event day selector to default to the most recent day with edges

### Option 2: Show Edges for All Event Days

When filtering by station, show edges for all event days (today + future days with open markets).

**API Call:**
```javascript
// Don't filter by event_day - show all
GET /api/edges/current?station_code=KLGA
```

### Option 3: Auto-Update Event Day Selector

When new trades are placed for a different event day, automatically update the event day selector to show that day's edges.

## Recommended Fix

**Frontend should:**

1. **Default to most recent event day** when showing edges
2. **Show edges for all open markets** (today + future days) when no event day is selected
3. **Update event day selector** to include all days with open markets
4. **Handle date format** correctly (use `YYYY-MM-DD` format for API calls)

**Example API Calls:**

```javascript
// Show edges for most recent event day (or all if multiple)
GET /api/edges/current?station_code=KLGA

// Or explicitly get edges for specific day
GET /api/edges/current?station_code=KLGA&event_day=2025-11-20
```

## Verification

To verify the API is working:

```bash
# Get edges for 2025-11-19 (older, but exists)
curl "http://localhost:8000/api/edges/current?station_code=KLGA&event_day=2025-11-19"

# Get edges for 2025-11-20 (most recent)
curl "http://localhost:8000/api/edges/current?station_code=KLGA&event_day=2025-11-20"

# Get all edges for KLGA (all event days)
curl "http://localhost:8000/api/edges/current?station_code=KLGA"
```

## Notes

- Decision snapshots are only saved when trades are placed (positive edges)
- Edges are extracted from decision snapshots
- Each bracket only shows the **most recent** edge (deduplicated by station/event_day/bracket)
- Edges are sorted by edge_pct (best edges first)


