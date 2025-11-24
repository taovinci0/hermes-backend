# Performance Page: Three Correlated Graphs Plan

**Date**: November 18, 2025  
**Purpose**: Plan three correlated graphs with hover synchronization and clickable snapshots  
**Key Feature**: Hover on one graph shows corresponding data points on all three

---

## 🎯 Overview

**Three Stacked Graphs** (all correlated via hover):

1. **Graph 1**: Zeus Snapshots (Daily High Predictions)
   - Clickable points showing daily high from each snapshot
   - Click opens full snapshot details
   - Granular Y-axis to show micro changes

2. **Graph 2**: Market Prices
   - Prices for each bracket from market open to close
   - Multiple lines (one per bracket)

3. **Graph 3**: Trade Decisions
   - Trades plotted from market open to close
   - Shows when trades were placed

**All three share the same X-axis** (market open → close timeline) and are **correlated via hover**.

---

## 📊 Graph 1: Zeus Snapshots (Daily High Predictions)

### **What It Shows**

**Data Points**:
- Each point = One Zeus snapshot's predicted daily high
- X position = Snapshot fetch time (market open → close)
- Y position = Predicted daily high temperature (°F)
- **Clickable**: Click point to open full snapshot details

**Visual Design**:
- **Scatter plot** or **line with markers**
- Points are clickable (cursor changes on hover)
- Color: Blue
- Marker size: Medium (easy to click)

### **Y-Axis Granularity**

**Requirement**: Granular enough to show micro changes

**Example**:
- If predictions range from 44.5°F to 45.2°F (0.7°F range)
- Y-axis should show: `44.0°F` to `46.0°F` (2°F range)
- **Not**: `40°F` to `50°F` (too wide, micro changes invisible)

**Implementation**:
- Dynamic Y-axis: `[min - 0.5, max + 0.5]` or similar
- Ensure at least 0.1°F increments visible
- Auto-scale based on data range

### **Clickable Points**

**On Click**:
- Open modal with full snapshot details:
  - Snapshot timestamp
  - Full 24-hour forecast (timeseries)
  - Daily high prediction
  - Forecast model used
  - Sigma/uncertainty
  - Raw snapshot JSON (optional)

**Visual Feedback**:
- Hover: Point highlights, tooltip shows daily high
- Click: Point selected, snapshot details open

---

## 📊 Graph 2: Polymarket Price History

### **What It Shows**

**Data Points**:
- Each point = Market price (Yes token) for a bracket at snapshot time
- X position = Snapshot fetch time (market open → close)
- Y position = Price (0.0-1.0) - **Note: Price = implied probability**
- Multiple lines: One line per bracket (e.g., 44-45°F, 45-46°F, etc.)

**Visual Design**:
- **Line chart** with multiple series
- One line per bracket
- Color-coded by bracket
- Y-axis: 0.0-1.0 (price) - **Price IS probability in Polymarket**

**Data Source**:
- Polymarket snapshots for that day
- Extract `mid_price` from each snapshot
- Plot over time (market open → close)

**Important**: 
- We snapshot `mid_price` (actual Polymarket price)
- In Polymarket, price = probability (0.85 = 85%)
- Tooltip should show both: `Price: 0.85 (85%)`

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

## 🔗 Correlation via Hover & Scroll

### **How It Works**

**Shared X-Axis**:
- All three graphs use the same time scale (market open → close)
- X-axis values are synchronized

**Hover Synchronization**:
- Hover on Graph 1 point at `12:15` → Shows vertical line at `12:15` on all three graphs
- Hover on Graph 2 point at `14:30` → Shows vertical line at `14:30` on all three graphs
- Hover on Graph 3 point at `16:45` → Shows vertical line at `16:45` on all three graphs

**Visual Indicator**:
- Vertical line across all three graphs
- Highlights corresponding points on other graphs
- Tooltip shows data from all three graphs at that time

**Horizontal Scroll Synchronization**:
- Scroll horizontally on any graph → All three graphs scroll together
- Maintains alignment across all three graphs
- Useful when timeline spans multiple days with many data points
- Works with mouse wheel, trackpad, or scrollbar

**Implementation**:
- Use chart library's `syncId` or similar feature for hover
- Shared scroll state across all three chart containers
- Synchronized scroll event handlers
- Vertical line component that spans all graphs

---

## 📐 Visual Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Performance                                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ Station: [EGLC ▼]  Date: [2025-11-16 ▼]                                    │
│                                                                              │
│ ┌──────────────────────────────────────────────────────────────────────┐  │
│ │ Graph 1: Zeus Snapshots (Daily High Predictions)                     │  │
│ │                                                                      │  │
│ │  45.5°F ┤                                                           │  │
│ │        │      ●                                                      │  │
│ │  45.0°F ┤  ●     ●                                                   │  │
│ │        │●        ●                                                   │  │
│ │  44.5°F ┤                                                           │  │
│ │        │                                                             │  │
│ │        └────────────────────────────────────────────────────          │  │
│ │        09:00  12:00  15:00  18:00  21:00                            │  │
│ │        Market Open → Market Close                                    │  │
│ │                                                                      │  │
│ │  Click point to view full snapshot                                   │  │
│ └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│ ┌──────────────────────────────────────────────────────────────────────┐  │
│ │ Graph 2: Market Prices (Bracket Probabilities)                   │  │
│ │                                                                      │  │
│ │ 100% ┤                                                               │  │
│ │      │  ─── 44-45°F                                                  │  │
│ │  75% ┤  ─── 45-46°F                                                  │  │
│ │      │  ─── 46-47°F                                                  │  │
│ │  50% ┤                                                               │  │
│ │      │                                                               │  │
│ │  25% ┤                                                               │  │
│ │      │                                                               │  │
│ │   0% ┤                                                               │  │
│ │      └────────────────────────────────────────────────────            │  │
│ │      09:00  12:00  15:00  18:00  21:00                              │  │
│ │      Market Open → Market Close                                      │  │
│ └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│ ┌──────────────────────────────────────────────────────────────────────┐  │
│ │ Graph 3: Trade Decisions                                              │  │
│ │                                                                      │  │
│ │ $500 ┤                                                               │  │
│ │      │        ● (Win)                                                │  │
│ │ $400 ┤                                                               │  │
│ │      │  ● (Pending)                                                  │  │
│ │ $300 ┤                                                               │  │
│ │      │              ● (Loss)                                         │  │
│ │ $200 ┤                                                               │  │
│ │      │                                                               │  │
│ │ $100 ┤                                                               │  │
│ │      │                                                               │  │
│ │    $0 ┤                                                               │  │
│ │      └────────────────────────────────────────────────────            │  │
│ │      09:00  12:00  15:00  18:00  21:00                              │  │
│ │      Market Open → Market Close                                      │  │
│ │                                                                      │  │
│ │  Legend: ● Win | ● Loss | ● Pending                                 │  │
│ └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│ [Hover on any graph to see corresponding points on all three]              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Implementation Details

### **Graph 1: Zeus Snapshots**

#### **Data Structure**
```typescript
interface ZeusSnapshotPoint {
  timestamp: string;        // Snapshot fetch time
  daily_high_F: number;     // Predicted daily high
  snapshot_id: string;      // For opening full snapshot
  snapshot_data: object;     // Full snapshot data (for modal)
}
```

#### **Y-Axis Configuration**
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

#### **Click Handler**
```typescript
const handlePointClick = (point: ZeusSnapshotPoint) => {
  // Open modal/sidebar with full snapshot
  setSelectedSnapshot(point.snapshot_data);
  setShowSnapshotModal(true);
};
```

---

### **Graph 2: Polymarket Price History**

#### **Data Structure**
```typescript
interface PolymarketPricePoint {
  timestamp: string;        // Snapshot fetch time
  bracket: string;          // e.g., "44-45°F"
  price: number;           // 0.0-1.0 (mid_price from snapshot)
  probability: number;     // price * 100 (for tooltip display)
  snapshot_id: string;
}
```

#### **Multiple Lines**
```typescript
// Group by bracket
const brackets = [...new Set(points.map(p => p.bracket))];

// Create one line per bracket
brackets.map(bracket => (
  <Line
    key={bracket}
    dataKey={bracket}
    data={points.filter(p => p.bracket === bracket)}
    stroke={getBracketColor(bracket)}
  />
));
```

#### **Y-Axis Configuration**
```typescript
// Y-axis: Price (0.0 to 1.0)
<YAxis 
  domain={[0, 1]} 
  label={{ value: 'Price', angle: -90, position: 'insideLeft' }}
  tickFormatter={(value) => value.toFixed(2)}
/>

// Tooltip shows both price and percentage
const CustomTooltip = ({ active, payload }) => {
  if (!active) return null;
  
  return (
    <div className="tooltip">
      <p>Time: {payload[0].payload.timestamp}</p>
      {payload.map((entry, index) => (
        <p key={index}>
          {entry.dataKey}: {entry.value.toFixed(4)} ({(entry.value * 100).toFixed(2)}%)
        </p>
      ))}
    </div>
  );
};
```

---

### **Graph 3: Trade Decisions**

#### **Data Structure**
```typescript
interface TradeDecisionPoint {
  timestamp: string;        // Trade timestamp
  bracket: string;          // e.g., "44-45°F"
  size_usd: number;         // Trade size
  outcome: 'win' | 'loss' | 'pending';
  trade_id: string;
}
```

#### **Color Coding**
```typescript
const getPointColor = (outcome: string) => {
  switch (outcome) {
    case 'win': return '#16a34a';      // Green
    case 'loss': return '#dc2626';      // Red
    case 'pending': return '#6b7280';   // Gray
    default: return '#6b7280';
  }
};
```

---

## 🔗 Hover & Scroll Synchronization

### **Implementation**

**Using Recharts `syncId` for Hover**:
```typescript
// All three charts share the same syncId
<LineChart syncId="performanceTimeline" ...>
  {/* Graph 1 content */}
</LineChart>

<LineChart syncId="performanceTimeline" ...>
  {/* Graph 2 content */}
</LineChart>

<ScatterChart syncId="performanceTimeline" ...>
  {/* Graph 3 content */}
</ScatterChart>
```

**Synchronized Horizontal Scrolling**:
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

**Alternative: Using CSS Scroll Snap**:
```typescript
// Container with synchronized scroll
<div className="graphs-wrapper" 
     onScroll={handleScroll}
     style={{ 
       overflowX: 'auto',
       display: 'flex',
       flexDirection: 'column',
       scrollSnapType: 'x mandatory'
     }}>
  <div className="graph-container" style={{ scrollSnapAlign: 'start' }}>
    <LineChart width={timelineWidth} ...>
      {/* Graph 1 */}
    </LineChart>
  </div>
  <div className="graph-container" style={{ scrollSnapAlign: 'start' }}>
    <LineChart width={timelineWidth} ...>
      {/* Graph 2 */}
    </LineChart>
  </div>
  <div className="graph-container" style={{ scrollSnapAlign: 'start' }}>
    <ScatterChart width={timelineWidth} ...>
      {/* Graph 3 */}
    </ScatterChart>
  </div>
</div>
```

**Custom Hover Handler**:
```typescript
const [hoveredTime, setHoveredTime] = useState<string | null>(null);

const handleHover = (time: string) => {
  setHoveredTime(time);
  // Show vertical line at this time on all graphs
};

// Vertical line component
{hoveredTime && (
  <ReferenceLine
    x={hoveredTime}
    stroke="#666"
    strokeDasharray="3 3"
  />
)}
```

**Tooltip with Cross-Graph Data**:
```typescript
const CustomTooltip = ({ active, payload, label }) => {
  if (!active) return null;
  
  // Get data from all three graphs at this time
  const zeusData = getZeusDataAtTime(label);
  const polymarketData = getPolymarketDataAtTime(label);
  const tradeData = getTradeDataAtTime(label);
  
  return (
    <div className="tooltip">
      <p>Time: {label}</p>
      {zeusData && <p>Zeus: {zeusData.daily_high_F}°F</p>}
      {polymarketData && <p>Market: {polymarketData.bracket} = {polymarketData.probability}%</p>}
      {tradeData && <p>Trade: {tradeData.bracket} ${tradeData.size_usd}</p>}
    </div>
  );
};
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
    "timestamp": "2025-11-16T09:15:00Z",
    "daily_high_F": 44.6,
    "snapshot_id": "2025-11-16_09-15-00",
    "snapshot_data": { /* full snapshot */ }
  },
  ...
]
```

---

### **Graph 2: Polymarket Price History**

**API Endpoint**: `GET /api/snapshots/polymarket?city={CITY}&event_day={DATE}`

**Processing**:
- Extract `mid_price` from each snapshot (this is the price)
- Extract snapshot fetch time
- Group by bracket
- Filter to market open → close range
- **Note**: `mid_price` IS the probability (0.85 = 85%)

**Output**:
```json
[
  {
    "timestamp": "2025-11-16T09:20:00Z",
    "bracket": "44-45°F",
    "price": 0.1382,  // ← mid_price from snapshot
    "probability": 13.82,  // ← price * 100 (for tooltip)
    "snapshot_id": "2025-11-16_09-20-00"
  },
  {
    "timestamp": "2025-11-16T09:20:00Z",
    "bracket": "45-46°F",
    "price": 0.2430,  // ← mid_price from snapshot
    "probability": 24.30,  // ← price * 100 (for tooltip)
    "snapshot_id": "2025-11-16_09-20-00"
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
    "timestamp": "2025-11-16T12:15:00Z",
    "bracket": "44-45°F",
    "size_usd": 300.0,
    "outcome": "win",
    "trade_id": "trade_123"
  },
  ...
]
```

---

## 🎯 Market Open/Close Timeline

### **Standard Timeline Rule**

**Market Open**:
- **2 days before event day at 4pm UTC**
- Example: Event day = Nov 20 → Market opens Nov 18 at 4pm UTC
- Consistent across all events

**Market Close**:
- **Event day local midnight** (when event resolves)
- Example: Event day = Nov 20 → Market closes Nov 20 at 00:00 local time
- Converts to UTC for display

**X-Axis Range**:
- Start: Market open (2 days before event at 4pm UTC)
- End: Market close (event day local midnight, converted to UTC)
- Standardized for all graphs (not dynamic based on snapshots)

**Why Standard Timeline**:
- ✅ Consistent X-axis across all events
- ✅ Predictable timeline range
- ✅ Matches typical Polymarket behavior
- ✅ Simple implementation

---

## 📊 Y-Axis Granularity for Graph 1

### **Requirement**: Show micro changes

**Example Scenario**:
- Predictions range: 44.5°F to 45.2°F (0.7°F range)
- Y-axis should show: `44.0°F` to `46.0°F` (2°F range)
- **Not**: `40°F` to `50°F` (too wide)

**Implementation**:
```typescript
// Calculate dynamic Y-axis
const temps = points.map(p => p.daily_high_F);
const minTemp = Math.min(...temps);
const maxTemp = Math.max(...temps);
const range = maxTemp - minTemp;

// Padding: 10% of range, minimum 0.5°F
const padding = Math.max(range * 0.1, 0.5);

// Y-axis domain
const yAxisDomain = [
  Math.floor((minTemp - padding) * 10) / 10,  // Round down to 0.1°F
  Math.ceil((maxTemp + padding) * 10) / 10     // Round up to 0.1°F
];

// Tick interval: 0.1°F if range < 2°F, else 0.2°F
const tickInterval = range < 2 ? 0.1 : 0.2;
```

**Result**:
- Micro changes (0.1-0.2°F) are clearly visible
- Y-axis is tight around data range
- No wasted space

---

## 🔧 Implementation Stages

### **Stage 1: Graph 1 - Zeus Snapshots (Week 1)**

#### **1.1 Data Processing**
- Fetch Zeus snapshots
- Extract daily high from each
- Calculate granular Y-axis
- Prepare clickable points

**Time**: 2-3 hours

---

#### **1.2 Graph Component**
- Create scatter/line chart
- Implement clickable points
- Configure granular Y-axis
- Add hover tooltip

**Time**: 3-4 hours

---

#### **1.3 Snapshot Modal**
- Create modal/sidebar component
- Display full snapshot details
- Show 24-hour forecast
- Add close button

**Time**: 2-3 hours

---

### **Stage 2: Graph 2 - Polymarket Prices (Week 1)**

#### **2.1 Data Processing**
- Fetch Polymarket snapshots
- Extract bracket probabilities
- Group by bracket
- Prepare time series

**Time**: 2-3 hours

---

#### **2.2 Graph Component**
- Create multi-line chart
- One line per bracket
- Color-code brackets
- Add legend

**Time**: 3-4 hours

---

### **Stage 3: Graph 3 - Trade Decisions (Week 1-2)**

#### **3.1 Data Processing**
- Fetch decision snapshots
- Extract trades
- Include outcomes
- Prepare scatter data

**Time**: 2-3 hours

---

#### **3.2 Graph Component**
- Create scatter chart
- Color-code by outcome
- Size markers by trade size
- Add tooltip

**Time**: 2-3 hours

---

### **Stage 4: Hover & Scroll Synchronization (Week 2)**

#### **4.1 Shared Hover State**
- Implement shared hover state
- Create vertical line component
- Sync across all three graphs

**Time**: 2-3 hours

---

#### **4.2 Synchronized Horizontal Scrolling**
- Implement scroll synchronization
- Handle scroll events on all three graphs
- Maintain alignment during scroll
- Support mouse wheel, trackpad, scrollbar

**Time**: 3-4 hours

---

#### **4.3 Cross-Graph Tooltip**
- Create unified tooltip
- Show data from all three graphs
- Position correctly

**Time**: 2-3 hours

---

### **Stage 5: Integration & Testing (Week 2)**

#### **5.1 Integration**
- Integrate all three graphs
- Ensure proper alignment
- Test hover synchronization

**Time**: 2-3 hours

---

#### **5.2 Testing & Polish**
- Test with real data
- Verify clickable points
- Test hover correlation
- Polish styling

**Time**: 2-3 hours

---

## 📋 Implementation Checklist

### **Backend** (Minimal)
- [ ] Verify existing endpoints work for historical dates
- [ ] Test `/api/snapshots/zeus` with event_day filter
- [ ] Test `/api/snapshots/polymarket` with event_day filter
- [ ] Test `/api/snapshots/decisions` with event_day filter

### **Frontend**
- [ ] Graph 1: Zeus snapshots with clickable points
- [ ] Graph 1: Granular Y-axis (show micro changes)
- [ ] Graph 1: Snapshot modal on click
- [ ] Graph 2: Polymarket prices (multiple brackets)
- [ ] Graph 3: Trade decisions (color-coded)
- [ ] Hover synchronization across all three
- [ ] Vertical line indicator
- [ ] Cross-graph tooltip
- [ ] Market open/close timeline
- [ ] Testing with real data

---

## ⏱️ Timeline

### **Week 1**
- Day 1-2: Graph 1 (Zeus snapshots)
- Day 3-4: Graph 2 (Polymarket prices)
- Day 5: Graph 3 (Trade decisions)

### **Week 2**
- Day 1-2: Hover synchronization
- Day 3: Integration
- Day 4-5: Testing & polish

**Total**: 2 weeks

---

## 🎯 Key Features

### **Graph 1: Zeus Snapshots**
- ✅ Clickable points (open full snapshot)
- ✅ Granular Y-axis (show micro changes)
- ✅ Daily high predictions over time

### **Graph 2: Polymarket Prices**
- ✅ Multiple bracket lines
- ✅ Probability evolution
- ✅ Market open → close timeline

### **Graph 3: Trade Decisions**
- ✅ Color-coded outcomes
- ✅ Trade size visualization
- ✅ Market open → close timeline

### **Correlation**
- ✅ Hover synchronization
- ✅ Horizontal scroll synchronization
- ✅ Vertical line indicator
- ✅ Cross-graph tooltip
- ✅ Shared X-axis (market timeline)

---

## ✅ Success Criteria

**Graphs display correctly when**:
- ✅ Graph 1 shows clickable Zeus snapshot points
- ✅ Graph 1 Y-axis is granular (micro changes visible)
- ✅ Graph 2 shows multiple bracket probability lines
- ✅ Graph 3 shows color-coded trade decisions
- ✅ All three share same X-axis (market timeline)
- ✅ Hover on one shows corresponding points on others
- ✅ Horizontal scroll on one scrolls all three together
- ✅ Click on Graph 1 point opens snapshot modal
- ✅ Vertical line appears on hover across all graphs
- ✅ Scroll maintains alignment across all graphs

---

**Last Updated**: November 18, 2025

