# Performance Page: Three Correlated Graphs - Final Specification

**Date**: November 18, 2025  
**Purpose**: Final specification for the three correlated graphs on Performance page  
**Status**: Ready for Implementation

---

## 🎯 Overview

**Three Stacked Graphs** (all correlated via hover and click):

1. **Graph 1**: Zeus Snapshots (Daily High Predictions)
   - Clickable points showing daily high from each snapshot
   - Click opens modal with snapshot data for all three graphs

2. **Graph 2**: Market Probability History
   - Probabilities for each bracket from market open to close
   - Multiple lines (one per bracket)
   - Shows probabilities (0-100%) as primary, prices (0.0-1.0) as secondary in tooltip

3. **Graph 3**: Trade Decisions
   - Trades plotted from market open to close
   - Color-coded by outcome (win/loss/pending)

**All three share the same X-axis** (market open → close timeline) and are **correlated via hover and click**.

---

## 📊 Graph 1: Zeus Snapshots (Daily High Predictions)

### **What It Shows**

**Data Points**:
- Each point = One Zeus snapshot's predicted daily high
- X position = Snapshot fetch time (market open → close)
- Y position = Predicted daily high temperature (°F)
- **Clickable**: Click point to open modal with snapshot data

**Visual Design**:
- **Scatter plot** or **line with markers**
- Points are clickable (cursor changes on hover)
- Color: Blue
- Marker size: Medium (easy to click)

### **Y-Axis Granularity**

**Requirement**: Granular enough to show micro changes

**Implementation**:
```typescript
// Dynamic Y-axis based on data range
const minTemp = Math.min(...points.map(p => p.daily_high_F));
const maxTemp = Math.max(...points.map(p => p.daily_high_F));
const range = maxTemp - minTemp;

// Ensure granularity: at least 0.1°F visible
const yAxisDomain = [
  minTemp - Math.max(0.5, range * 0.1),  // Padding below
  maxTemp + Math.max(0.5, range * 0.1)   // Padding above
];

// Y-axis ticks: show every 0.1°F or 0.2°F depending on range
const tickInterval = range < 1 ? 0.1 : 0.2;
```

---

## 📊 Graph 2: Market Probability History

### **What It Shows**

**Data Points**:
- Each point = Market price (Yes token) for a bracket at snapshot time
- X position = Snapshot fetch time (market open → close)
- Y position = Probability (0-100%) - **Primary display**
- Multiple lines: One line per bracket (e.g., 44-45°F, 45-46°F, etc.)

**Visual Design**:
- **Line chart** with multiple series
- One line per bracket
- Color-coded by bracket
- **Y-axis: 0-100% (probability)** - Primary
- **Tooltip: Shows probability first, price second**

**Data Source**:
- Market snapshots for that day (Polymarket, Kalshi, etc.)
- Extract `mid_price` from each snapshot
- Convert to percentage: `probability = mid_price * 100`
- Plot over time (market open → close)

**Important**: 
- We snapshot `mid_price` (actual market price, 0.0-1.0)
- In prediction markets, price = probability (0.85 = 85%)
- Display: Probability (0-100%) as primary, price (0.0-1.0) as secondary in tooltip

### **Y-Axis Configuration**

```typescript
// Y-axis: Probability (0-100%) - PRIMARY
<YAxis 
  domain={[0, 100]} 
  label={{ value: 'Probability (%)', angle: -90, position: 'insideLeft' }}
  tickFormatter={(value) => `${value}%`}
/>

// Tooltip shows probability first, price second
const CustomTooltip = ({ active, payload }) => {
  if (!active) return null;
  
  return (
    <div className="tooltip">
      <p>Time: {payload[0].payload.timestamp}</p>
      {payload.map((entry, index) => {
        const probability = entry.value; // Already in percentage
        const price = probability / 100; // Convert back to price
        return (
          <p key={index}>
            {entry.dataKey}: {probability.toFixed(2)}% (Price: {price.toFixed(4)})
          </p>
        );
      })}
    </div>
  );
};
```

### **Graph Title**

**Title**: "Market Probability History"  
**Subtitle**: "Market-implied probabilities for each temperature bracket. Price = probability."

**Note**: Use "Market" not "Polymarket" since we support multiple venues (Polymarket, Kalshi, etc.)

**Where Price is Shown (Secondary)**:
- ✅ **Tooltip**: Shows probability first, price second
  - Format: `44-45°F: 13.82% (Price: 0.1382)`
- ✅ **Modal/Popup**: Shows price in market snapshot data
  - Each market entry shows both `price` and `probability` fields
  - Price displayed alongside probability for reference

---

## 📊 Graph 3: Trade Decisions

### **What It Shows**

**Data Points**:
- Each point = One trade decision
- X position = Trade timestamp (market open → close)
- Y position = Trade size (USD) or bracket (categorical)
- Marker shows: Bracket, size, outcome (if resolved)

**Visual Design**:
- **Scatter plot** or **bar chart**
- Color-coded by outcome:
  - Green: Win
  - Red: Loss
  - Gray: Pending
- Size of marker = Trade size (USD)

**Data Source**:
- Decision snapshots for that day
- Extract trades from each decision snapshot
- Plot at actual trade timestamp

---

## 🔗 Correlation via Hover & Click

### **Hover Synchronization**

**How It Works**:
- Hover on Graph 1 point at `12:15` → Shows vertical line at `12:15` on all three graphs
- Hover on Graph 2 point at `14:30` → Shows vertical line at `14:30` on all three graphs
- Hover on Graph 3 point at `16:45` → Shows vertical line at `16:45` on all three graphs

**Visual Indicator**:
- Vertical line across all three graphs
- Highlights corresponding points on other graphs
- Tooltip shows data from all three graphs at that time

### **Click Synchronization**

**How It Works**:
- Click ANY point on ANY graph → Opens modal with snapshot data for all three graphs
- Modal shows:
  - Zeus snapshot data (for that timestamp)
  - Market snapshot data (for that timestamp)
  - Decision snapshot data (for that timestamp)
- **No METAR data** in modal (METAR is for actuals, not snapshots)

**Modal Content**:
```typescript
interface SnapshotModalData {
  timestamp: string;
  zeus_snapshot: {
    daily_high_F: number;
    timeseries: Array<{ time_utc: string; temp_K: number }>;
    model_mode: string;
    // ... full Zeus snapshot
  };
  market_snapshot: {
    markets: Array<{
      bracket: string;
      price: number;        // ← Price (0.0-1.0) - shown as secondary
      probability: number;  // ← Probability (0-100%) - shown as primary
      closed: boolean;
    }>;
    // ... full market snapshot
  };
  decision_snapshot: {
    decisions: Array<{
      bracket: string;
      edge: number;
      size_usd: number;
      reason: string;
    }>;
    // ... full decision snapshot
  };
}
```

**Modal Display Format**:
- **Market Snapshot Section**:
  - Each bracket shows: `Bracket: 44-45°F | Probability: 13.82% | Price: 0.1382`
  - Or table format with columns: Bracket | Probability (%) | Price

**Implementation**:
```typescript
const [selectedSnapshot, setSelectedSnapshot] = useState<SnapshotModalData | null>(null);

// Click handler for all three graphs
const handlePointClick = (timestamp: string) => {
  // Fetch snapshot data for all three at this timestamp
  const zeusData = getZeusSnapshotAtTime(timestamp);
  const marketData = getMarketSnapshotAtTime(timestamp);
  const decisionData = getDecisionSnapshotAtTime(timestamp);
  
  setSelectedSnapshot({
    timestamp,
    zeus_snapshot: zeusData,
    market_snapshot: marketData,
    decision_snapshot: decisionData,
  });
  setShowSnapshotModal(true);
};

// Apply to all three graphs
<LineChart onPointClick={(data) => handlePointClick(data.timestamp)}>
  {/* Graph 1 */}
</LineChart>

<LineChart onPointClick={(data) => handlePointClick(data.timestamp)}>
  {/* Graph 2 */}
</LineChart>

<ScatterChart onPointClick={(data) => handlePointClick(data.timestamp)}>
  {/* Graph 3 */}
</ScatterChart>
```

---

## 📐 X-Axis: Market Timeline

### **Standard Timeline Rule**

**Standard Timeline Format**: **-36 hours to +24 hours**
- **-36 hours** = 36 hours before event day local midnight
- **+24 hours** = 24 hours after event day local midnight (end of event day)
- **0 hours** = Event day local midnight (when event resolves)

**Example**:
- Event day = Nov 20, 2025
- Event day local midnight = Nov 20 00:00 local time
- **-36 hours** = Nov 18 12:00 local time (36 hours before)
- **+24 hours** = Nov 21 00:00 local time (24 hours after)

**Market Open**:
- **-36 hours** (36 hours before event day local midnight)
- Example: Event day = Nov 20 → Market opens Nov 18 at 12:00 local time
- Consistent across all events

**Market Close**:
- **+24 hours** (24 hours after event day local midnight = end of event day)
- Example: Event day = Nov 20 → Market closes Nov 21 at 00:00 local time
- This is when event resolves (end of event day)

**X-Axis Range**:
- Start: **-36 hours** (36 hours before event day local midnight)
- End: **+24 hours** (24 hours after event day local midnight)
- Total range: **60 hours** (2.5 days)
- Standardized for all graphs (not dynamic based on snapshots)

**Why Standard Timeline**:
- ✅ Consistent X-axis across all events
- ✅ Predictable timeline range
- ✅ Matches typical market behavior (markets open ~36 hours before)
- ✅ Simple implementation
- ✅ Frontend knows exact range without API call

### **Implementation**

**Option 1: Frontend Calculates (Recommended)**

**No API call needed** - Frontend can calculate from event day:

```typescript
// Calculate timeline from event day
const eventDay = new Date(eventDayString); // e.g., "2025-11-20"
const stationTimezone = "Europe/London"; // From station data

// Get event day local midnight
const localMidnight = new Date(
  eventDay.getFullYear(),
  eventDay.getMonth(),
  eventDay.getDate(),
  0, 0, 0
);

// Convert to UTC (for display)
const localMidnightUTC = convertToUTC(localMidnight, stationTimezone);

// Calculate -36 hours and +24 hours
const marketOpen = new Date(localMidnightUTC.getTime() - 36 * 60 * 60 * 1000);
const marketClose = new Date(localMidnightUTC.getTime() + 24 * 60 * 60 * 1000);

// Use for X-axis domain on all three graphs
const xAxisDomain = [marketOpen, marketClose];

// Apply to all three graphs
<XAxis
  domain={xAxisDomain}
  type="number"
  scale="time"
  tickFormatter={(value) => {
    // Format as relative time: "-36h", "-24h", "0h", "+12h", "+24h"
    // Or absolute time: "Nov 18 12:00", "Nov 20 00:00", etc.
    return formatTime(value);
  }}
/>
```

**Option 2: Backend Endpoint (Alternative)**

**Backend Endpoint**: `GET /api/performance/market-timeline?city={CITY}&event_day={DATE}`

**Response**:
```json
{
  "city": "London",
  "event_day": "2025-11-20",
  "event_day_local_midnight_utc": "2025-11-20T00:00:00Z",
  "market_open_utc": "2025-11-18T12:00:00Z",  // -36 hours
  "market_close_utc": "2025-11-21T00:00:00Z",  // +24 hours
  "timeline_format": "standard",
  "range_hours": 60
}
```

**Frontend Usage**:
```typescript
// Fetch market timeline
const timelineResponse = await fetch(
  `/api/performance/market-timeline?city=${city}&event_day=${eventDay}`
);
const timeline = await timelineResponse.json();

// Use for X-axis domain on all three graphs
const xAxisDomain = [
  new Date(timeline.market_open_utc),
  new Date(timeline.market_close_utc),
];

// Apply to all three graphs
<XAxis
  domain={xAxisDomain}
  type="number"
  scale="time"
  tickFormatter={(value) => formatTime(value)}
/>
```

**X-Axis Label Format**: **Relative Labels (Recommended)**

Since space is limited on the X-axis, use **relative labels** only:
- `-36h`, `-24h`, `-12h`, `0h`, `+12h`, `+24h`
- `0h` = Event day local midnight (when event resolves)
- Negative values = hours before event
- Positive values = hours after event start

**Why Relative Labels**:
- ✅ Compact (takes minimal space)
- ✅ Clear reference point (0h = event resolves)
- ✅ Easy to understand (hours before/after event)
- ✅ Consistent across all events

**Implementation**:
```typescript
// X-axis tick formatter
const formatXAxisLabel = (value: Date) => {
  // Calculate hours relative to event day local midnight
  const eventDayMidnight = getEventDayLocalMidnight(eventDay, stationTimezone);
  const hoursDiff = (value.getTime() - eventDayMidnight.getTime()) / (1000 * 60 * 60);
  
  // Format as relative hours
  if (hoursDiff === 0) return '0h';
  if (hoursDiff < 0) return `${Math.round(hoursDiff)}h`;  // e.g., "-36h"
  return `+${Math.round(hoursDiff)}h`;  // e.g., "+24h"
};

<XAxis
  domain={xAxisDomain}
  type="number"
  scale="time"
  tickFormatter={formatXAxisLabel}
  // Show fewer ticks to save space (e.g., every 12 hours)
  ticks={[-36, -24, -12, 0, 12, 24]}
/>
```

**Note**: Absolute dates/times (e.g., "Nov 18 12:00") are NOT recommended due to space constraints. Use relative labels only.

**Important**: 
- ❌ **NOT** 24-hour day axis (00:00 to 24:00)
- ✅ **Standard timeline** (-36 hours to +24 hours from event day local midnight)
- ✅ **Same X-axis for all three graphs**
- ✅ **Frontend can calculate without API call** (recommended)

---

## 🔄 Horizontal Scroll Synchronization

### **How It Works**

- **Scroll horizontally on ANY graph** → **All three graphs scroll together**
- Maintains alignment across all three graphs
- Useful when timeline spans 60 hours (-36h to +24h) with many data points
- Works with mouse wheel, trackpad, or scrollbar
- **All three graphs stay synchronized** during scroll

**Key Point**: When you scroll on Graph 1, Graph 2 and Graph 3 scroll the same amount at the same time, keeping all three aligned.

### **Implementation**

```typescript
// Shared scroll state
const [scrollLeft, setScrollLeft] = useState(0);
const graphRefs = useRef<Array<HTMLDivElement | null>>([null, null, null]);

// Handle scroll on any graph
const handleScroll = (index: number, event: React.UIEvent<HTMLDivElement>) => {
  const newScrollLeft = event.currentTarget.scrollLeft;
  setScrollLeft(newScrollLeft);
  
  // Sync scroll on all other graphs
  graphRefs.current.forEach((ref, i) => {
    if (ref && i !== index) {
      ref.scrollLeft = newScrollLeft;
    }
  });
};

// Graph containers with synchronized scrolling
<div className="graph-container" 
     ref={(el) => (graphRefs.current[0] = el)}
     onScroll={(e) => handleScroll(0, e)}
     style={{ overflowX: 'auto', overflowY: 'hidden' }}>
  <LineChart width={timelineWidth} ...>
    {/* Graph 1 */}
  </LineChart>
</div>

<div className="graph-container"
     ref={(el) => (graphRefs.current[1] = el)}
     onScroll={(e) => handleScroll(1, e)}
     style={{ overflowX: 'auto', overflowY: 'hidden' }}>
  <LineChart width={timelineWidth} ...>
    {/* Graph 2 */}
  </LineChart>
</div>

<div className="graph-container"
     ref={(el) => (graphRefs.current[2] = el)}
     onScroll={(e) => handleScroll(2, e)}
     style={{ overflowX: 'auto', overflowY: 'hidden' }}>
  <ScatterChart width={timelineWidth} ...>
    {/* Graph 3 */}
  </ScatterChart>
</div>
```

---

## 📋 Data Requirements

### **Graph 1: Zeus Snapshots**

**API Endpoint**: `GET /api/snapshots/zeus?station_code={STATION}&event_day={DATE}`

**Processing**:
- Extract daily high from each snapshot
- Extract snapshot fetch time
- Sort by timestamp
- Filter to market open → close range

**Output**:
```json
[
  {
    "timestamp": "2025-11-18T16:15:00Z",
    "daily_high_F": 44.6,
    "snapshot_id": "2025-11-18_16-15-00",
    "snapshot_data": { /* full snapshot */ }
  },
  ...
]
```

---

### **Graph 2: Market Probability History**

**API Endpoint**: `GET /api/snapshots/polymarket?city={CITY}&event_day={DATE}`

**Processing**:
- Extract `mid_price` from each snapshot (this is the price, 0.0-1.0)
- Convert to probability: `probability = mid_price * 100` (0-100%)
- Extract snapshot fetch time
- Group by bracket
- Filter to market open → close range

**Output**:
```json
[
  {
    "timestamp": "2025-11-18T16:20:00Z",
    "bracket": "44-45°F",
    "price": 0.1382,  // ← mid_price from snapshot
    "probability": 13.82,  // ← price * 100 (for display)
    "snapshot_id": "2025-11-18_16-20-00"
  },
  {
    "timestamp": "2025-11-18T16:20:00Z",
    "bracket": "45-46°F",
    "price": 0.2430,  // ← mid_price from snapshot
    "probability": 24.30,  // ← price * 100 (for display)
    "snapshot_id": "2025-11-18_16-20-00"
  },
  ...
]
```

---

### **Graph 3: Trade Decisions**

**API Endpoint**: `GET /api/snapshots/decisions?station_code={STATION}&event_day={DATE}`

**Processing**:
- Extract trades from each decision snapshot
- Extract trade timestamp
- Include outcome (if resolved)
- Filter to market open → close range

**Output**:
```json
[
  {
    "timestamp": "2025-11-19T12:15:00Z",
    "bracket": "44-45°F",
    "size_usd": 300.0,
    "outcome": "win",
    "trade_id": "trade_123",
    "snapshot_id": "2025-11-19_12-15-00"
  },
  ...
]
```

---

## ✅ Summary of Changes

### **Graph 2: Market Probability History**

1. **Title**: "Market Probability History" (not "Polymarket Probabilities")
   - Reason: Support multiple venues (Polymarket, Kalshi, etc.)
   - Primary metric is probability, not price

2. **Y-Axis**: Probability (0-100%) - **Primary**
   - Display probabilities as primary metric
   - More intuitive for users

3. **Tooltip**: Probability first, price second - **Secondary Display Location #1**
   - Format: `44-45°F: 13.82% (Price: 0.1382)`
   - Shows both for completeness
   - Price shown in parentheses as secondary

4. **Modal/Popup**: Price shown in market snapshot data - **Secondary Display Location #2**
   - Each market entry displays both probability and price
   - Format: `Bracket: 44-45°F | Probability: 13.82% | Price: 0.1382`
   - Or table format with separate columns

5. **Data**: Convert `mid_price` to percentage
   - `probability = mid_price * 100`
   - Store both price and probability

### **Click Behavior**

1. **Click any point on any graph** → Opens modal
2. **Modal shows snapshot data for all three graphs**:
   - Zeus snapshot
   - Market snapshot
   - Decision snapshot
3. **No METAR data** in modal (METAR is for actuals, not snapshots)

### **X-Axis**

1. **Market timeline** (not 24-hour day)
   - Start: Market open (2 days before event at 4pm UTC)
   - End: Market close (event day local midnight)
2. **Standardized** across all events
3. **Use `/api/performance/market-timeline` endpoint**

---

## 🎯 Key Features

### **Graph 1: Zeus Snapshots**
- ✅ Clickable points (open modal with all snapshot data)
- ✅ Granular Y-axis (show micro changes)
- ✅ Daily high predictions over time

### **Graph 2: Market Probability History**
- ✅ Multiple bracket lines
- ✅ Probability (0-100%) as primary display on Y-axis
- ✅ Price (0.0-1.0) as secondary in tooltip
- ✅ Price (0.0-1.0) as secondary in modal/popup
- ✅ Market timeline (not 24-hour day)

### **Graph 3: Trade Decisions**
- ✅ Color-coded outcomes
- ✅ Trade size visualization
- ✅ Market timeline (not 24-hour day)

### **Correlation**
- ✅ Hover synchronization
- ✅ Click synchronization (modal with all three snapshots)
- ✅ Horizontal scroll synchronization
- ✅ Vertical line indicator
- ✅ Cross-graph tooltip
- ✅ Shared X-axis (market timeline)

---

## ✅ Success Criteria

**Graphs display correctly when**:
- ✅ Graph 1 shows clickable Zeus snapshot points
- ✅ Graph 1 Y-axis is granular (micro changes visible)
- ✅ Graph 2 shows multiple bracket probability lines (0-100%)
- ✅ Graph 2 tooltip shows probability first, price second (secondary)
- ✅ Graph 2 modal shows price alongside probability (secondary)
- ✅ Graph 3 shows color-coded trade decisions
- ✅ All three share same X-axis (standard timeline: -36h to +24h from event day)
- ✅ X-axis range is standardized (-36 hours to +24 hours)
- ✅ Frontend can calculate timeline without API call
- ✅ Hover on one shows corresponding points on others
- ✅ Click on any point opens modal with all three snapshot data
- ✅ Horizontal scroll on one scrolls all three together
- ✅ Vertical line appears on hover across all graphs
- ✅ Scroll maintains alignment across all graphs

---

**Last Updated**: November 18, 2025

