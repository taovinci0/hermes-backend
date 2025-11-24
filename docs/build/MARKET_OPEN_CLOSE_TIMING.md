# Market Open/Close Timing - Implementation Guide

**Date**: November 18, 2025  
**Purpose**: Determine how to get market open and close times for the three correlated graphs  
**Issue**: We need to know when markets opened and closed to set the X-axis timeline

---

## 🔍 Current Situation

### **What We Have in Snapshots**

**Polymarket Snapshots**:
```json
{
  "fetch_time_utc": "2025-11-13T12:12:35.453684+00:00",
  "event_day": "2025-11-13",
  "city": "London",
  "markets": [
    {
      "market_id": "676331",
      "bracket": "58-59°F",
      "mid_price": 0.0005,
      "closed": false  // ← Only boolean, no timestamp
    }
  ]
}
```

**What's Missing**:
- ❌ No explicit `market_open_time`
- ❌ No explicit `market_close_time`
- ✅ Only `closed: true/false` boolean
- ✅ Only `fetch_time_utc` (when snapshot was taken)

---

## 🎯 Options for Determining Market Timeline

### **Option 1: Infer from Snapshot Data (Recommended)**

**Market Open**:
- Use **first Polymarket snapshot timestamp** where `closed: false`
- This is when we first detected the market was open
- May not be exact market open time, but close enough for visualization

**Market Close**:
- Use **last Polymarket snapshot timestamp** where `closed: false`
- Or use **first snapshot** where `closed: true` (if available)
- Fallback: Event day local midnight (when event resolves)

**Pros**:
- ✅ Uses actual data we have
- ✅ No additional API calls needed
- ✅ Works for historical data

**Cons**:
- ⚠️ First snapshot might be hours/days after market actually opened
- ⚠️ Not exact, but sufficient for visualization

---

### **Option 2: Query Polymarket API for Market Metadata**

**Check if Polymarket API provides**:
- `createdAt` - When market was created
- `startDate` - When market started trading
- `endDate` - When market closes/resolves
- `resolvedAt` - When market was resolved

**Implementation**:
```python
# In discovery.py or new service
def get_market_timeline(city: str, event_day: date) -> Dict[str, datetime]:
    """Get market open and close times from Polymarket API.
    
    Returns:
        {
            "market_open": datetime,
            "market_close": datetime,
        }
    """
    # Fetch event from Polymarket
    event = discovery.get_event_by_slug(...)
    
    # Extract market metadata
    markets = event.get("markets", [])
    if not markets:
        return None
    
    # Check if API provides timing fields
    first_market = markets[0]
    
    # Possible fields (need to verify):
    market_open = first_market.get("createdAt") or first_market.get("startDate")
    market_close = first_market.get("endDate") or first_market.get("resolvedAt")
    
    return {
        "market_open": parse_datetime(market_open),
        "market_close": parse_datetime(market_close),
    }
```

**Pros**:
- ✅ Exact market open/close times
- ✅ More accurate timeline

**Cons**:
- ⚠️ Requires API call (may not be available for historical data)
- ⚠️ Need to verify what fields Polymarket API actually provides
- ⚠️ May not work for old/resolved markets

---

### **Option 3: Use Event Day Boundaries (Simplest)**

**Market Open**:
- Assume markets open **2 days before event day** at local midnight
- Or use first snapshot timestamp (whichever is earlier)

**Market Close**:
- Use **event day local midnight** (when event resolves)
- This is when temperature is measured

**Pros**:
- ✅ Simple, no data needed
- ✅ Consistent across all events

**Cons**:
- ⚠️ May not reflect actual market lifecycle
- ⚠️ Markets might open/close at different times

---

## 📋 Recommended Approach: Hybrid (Option 1 + Option 3)

### **Market Open Time**

**Priority 1**: Use first Polymarket snapshot timestamp
- If we have snapshots, use the earliest one where `closed: false`
- This is when we first detected the market was open

**Priority 2**: Fallback to estimated open time
- If no snapshots, assume market opened 2 days before event day
- Use event day - 2 days, local midnight

**Implementation**:
```python
def get_market_open_time(
    city: str,
    event_day: date,
    snapshots: List[Dict],
) -> datetime:
    """Get market open time from snapshots or estimate.
    
    Args:
        city: City name
        event_day: Event date
        snapshots: List of Polymarket snapshots
        
    Returns:
        Market open datetime (UTC)
    """
    if snapshots:
        # Use first snapshot timestamp
        first_snapshot = min(snapshots, key=lambda s: s["fetch_time_utc"])
        return parse_datetime(first_snapshot["fetch_time_utc"])
    
    # Fallback: Estimate 2 days before event
    estimated_open = event_day - timedelta(days=2)
    # Convert to UTC (assuming local midnight)
    # ... timezone conversion logic ...
    return estimated_open_midnight_utc
```

---

### **Market Close Time**

**Priority 1**: Use last snapshot before resolution
- Find last snapshot where `closed: false`
- Use that timestamp as market close

**Priority 2**: Use first snapshot where `closed: true`
- If we have a snapshot showing markets closed, use that timestamp

**Priority 3**: Fallback to event day local midnight
- Event resolves at local midnight of event day
- Convert to UTC

**Implementation**:
```python
def get_market_close_time(
    city: str,
    event_day: date,
    snapshots: List[Dict],
    station_timezone: str,
) -> datetime:
    """Get market close time from snapshots or event day.
    
    Args:
        city: City name
        event_day: Event date
        snapshots: List of Polymarket snapshots
        station_timezone: Station timezone (e.g., "Europe/London")
        
    Returns:
        Market close datetime (UTC)
    """
    # Check for closed markets in snapshots
    closed_snapshots = [s for s in snapshots if any(m.get("closed") for m in s.get("markets", []))]
    
    if closed_snapshots:
        # Use first snapshot where markets closed
        first_closed = min(closed_snapshots, key=lambda s: s["fetch_time_utc"])
        return parse_datetime(first_closed["fetch_time_utc"])
    
    # Check for last open snapshot
    open_snapshots = [
        s for s in snapshots 
        if any(not m.get("closed") for m in s.get("markets", []))
    ]
    
    if open_snapshots:
        # Use last open snapshot timestamp
        last_open = max(open_snapshots, key=lambda s: s["fetch_time_utc"])
        return parse_datetime(last_open["fetch_time_utc"])
    
    # Fallback: Event day local midnight
    local_midnight = datetime.combine(
        event_day,
        time(0, 0),
        tzinfo=ZoneInfo(station_timezone)
    )
    return local_midnight.astimezone(ZoneInfo("UTC"))
```

---

## 🔧 Backend Implementation

### **New Endpoint: Market Timeline**

**File**: `backend/api/routes/performance.py` (or new `markets.py`)

**Endpoint**: `GET /api/performance/market-timeline?city={CITY}&event_day={DATE}`

**Response**:
```json
{
  "city": "London",
  "event_day": "2025-11-13",
  "market_open_utc": "2025-11-11T00:00:00Z",
  "market_close_utc": "2025-11-13T23:59:59Z",
  "source": "snapshots",  // or "estimated" or "api"
  "snapshot_count": 45
}
```

**Implementation** (Updated for Standard Timeline):
```python
@router.get("/market-timeline")
async def get_market_timeline(
    city: str = Query(..., description="City name"),
    event_day: str = Query(..., description="Event day (YYYY-MM-DD)"),
):
    """Get market open and close times for an event.
    
    Uses standard rule:
    - Market opens: 2 days before event day at 4pm UTC
    - Market closes: Event day local midnight
    """
    from datetime import datetime, time
    from zoneinfo import ZoneInfo
    
    event_date = date.fromisoformat(event_day)
    
    # Get station for timezone
    station = registry.get_by_city(city)
    if not station:
        raise HTTPException(404, f"Station not found for city: {city}")
    
    # Market open: 2 days before event day at 4pm UTC
    market_open_date = event_date - timedelta(days=2)
    market_open = datetime.combine(
        market_open_date,
        time(16, 0),  # 4pm
        tzinfo=ZoneInfo("UTC")
    )
    
    # Market close: Event day local midnight
    local_midnight = datetime.combine(
        event_date,
        time(0, 0),
        tzinfo=ZoneInfo(station.time_zone)
    )
    market_close = local_midnight.astimezone(ZoneInfo("UTC"))
    
    return {
        "city": city,
        "event_day": event_day,
        "market_open_utc": market_open.isoformat(),
        "market_close_utc": market_close.isoformat(),
        "source": "standard",  # Always standard rule
    }
```

---

## 📊 Frontend Usage

### **Fetching Timeline**

```typescript
// Fetch market timeline
const timelineResponse = await fetch(
  `/api/performance/market-timeline?city=${city}&event_day=${eventDay}`
);
const timeline = await timelineResponse.json();

// Use for X-axis
const xAxisDomain = [
  new Date(timeline.market_open_utc),
  new Date(timeline.market_close_utc),
];
```

### **X-Axis Configuration**

```typescript
<XAxis
  domain={xAxisDomain}
  type="number"
  scale="time"
  tickFormatter={(value) => formatTime(value)}
/>
```

---

## ✅ Summary

### **Recommended Approach: Standard Timeline (Updated)**

**User Requirement**: Standard X-axis for all graphs, not dynamic based on snapshots.

**Standard Rule**:
1. **Market Open**: 2 days before event day at **4pm UTC** (or 4pm local time)
   - Example: Event day = Nov 20 → Market opens Nov 18 at 4pm UTC
2. **Market Close**: Event day local midnight (when event resolves)
   - Example: Event day = Nov 20 → Market closes Nov 20 at 00:00 local time

**Why Standard Timeline**:
- ✅ Consistent across all events
- ✅ Predictable X-axis range
- ✅ Matches typical Polymarket behavior (markets open ~2 days before)
- ✅ Simple to implement

**Backend**: New endpoint `/api/performance/market-timeline` that uses standard rule
**Frontend**: Use standard timeline for X-axis domain on all three graphs

---

## 🔍 Future Enhancement

**If Polymarket API provides market timing metadata**:
- Add `get_market_timeline_from_api()` method
- Use API data when available
- Fallback to snapshot inference when not available

**Check Polymarket API documentation for**:
- Market `createdAt` timestamp
- Market `endDate` or `resolvedAt` timestamp
- Event `startDate` and `endDate`

---

---

## 🛑 When Do Snapshots Stop?

### **Snapshotter Behavior**

**Snapshots stop when**:
- All markets for an event are closed (`closed: true`)
- The `check_open_events()` method returns `False`
- `_evaluate_and_trade()` returns early (line 182-184) without taking snapshots

**Code Flow**:
```python
# In dynamic_engine.py _evaluate_and_trade()
has_open_markets = self.fetcher.check_open_events(station.city, event_day)

if not has_open_markets:
    logger.debug(f"     No open markets")
    return 0  # ← Stops here, no snapshots taken
```

**What `check_open_events()` checks**:
```python
# In fetchers.py check_open_events()
markets = event.get('markets', [])
open_markets = [m for m in markets if not m.get('closed')]

if open_markets:
    return True  # ← Markets still open, continue
return False  # ← All markets closed, stop
```

**Result**:
- ✅ Snapshots continue as long as ANY market is open (`closed: false`)
- ❌ Snapshots stop when ALL markets are closed (`closed: true`)
- 📊 Last snapshot = Last cycle where at least one market was open

**Example Timeline**:
```
Nov 18 16:00 UTC: Market opens → Snapshots start
Nov 19 12:00 UTC: Markets still open → Snapshots continue
Nov 20 00:00 Local: Event resolves → Markets close → Snapshots stop
```

---

**Last Updated**: November 18, 2025

