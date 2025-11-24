# Performance Graphs: X-Axis Styling & Horizontal Scroll

**Date**: November 18, 2025  
**Purpose**: Final specification for X-axis visual styling and synchronized horizontal scrolling  
**Status**: Ready for Implementation

---

## 📐 X-Axis Visual Styling

### **Event Day Window Background Shading**

**Visual Design**:
- **Pre-event area** (before 0h): Slightly darker background
- **Event-day area** (after 0h): Slightly lighter background
- **Vertical line at 0h**: Thin vertical line marking event boundary
- **Small labels at the top**: Event day labels

**Layout**:
```
<----- pre-event day -----> | <--------- event day -------->

−48h   −36h  −24h  −12h   0h |  +12h   +18h   +24h
```

**Implementation**:
```typescript
// Background bands for event day window
const EventDayBackground = () => {
  const eventDayMidnight = getEventDayLocalMidnight(eventDay, stationTimezone);
  const chartStart = marketOpen; // -36h
  const chartEnd = marketClose; // +24h
  
  return (
    <>
      {/* Pre-event area (darker background) */}
      <ReferenceArea
        x1={chartStart}
        x2={eventDayMidnight}
        fill="#1a1a1a"  // Slightly darker
        fillOpacity={0.3}
      />
      
      {/* Event-day area (lighter background) */}
      <ReferenceArea
        x1={eventDayMidnight}
        x2={chartEnd}
        fill="#2a2a2a"  // Slightly lighter
        fillOpacity={0.2}
      />
      
      {/* Vertical line at 0h (event boundary) */}
      <ReferenceLine
        x={eventDayMidnight}
        stroke="#666"
        strokeWidth={1}
        strokeDasharray="2 2"
        label={{ value: "Event Day", position: "top" }}
      />
    </>
  );
};

// Apply to all three graphs
<LineChart>
  <EventDayBackground />
  {/* Graph content */}
</LineChart>
```

### **X-Axis Ticks and Labels**

**Tick Configuration**:
- **Tick every 1 hour**: Show a tick mark every hour for precision
- **Label every 3 hours**: Show label text every 3 hours to avoid clutter
- **Small labels at the top**: Position labels above the axis

**Example**:
```
Ticks (every 1h):  |  |  |  |  |  |  |  |  |  |  |  |  |
Labels (every 3h): -36h      -24h      -12h      0h      +12h      +24h
```

**Implementation**:
```typescript
// Calculate tick positions (every 1 hour)
const generateTicks = () => {
  const ticks = [];
  const eventDayMidnight = getEventDayLocalMidnight(eventDay, stationTimezone);
  const start = marketOpen; // -36h
  const end = marketClose; // +24h
  const totalHours = (end - start) / (1000 * 60 * 60); // 60 hours
  
  for (let i = 0; i <= totalHours; i++) {
    ticks.push(new Date(start.getTime() + i * 60 * 60 * 1000));
  }
  return ticks;
};

// Calculate label positions (every 3 hours)
const generateLabels = () => {
  const labels = [];
  const eventDayMidnight = getEventDayLocalMidnight(eventDay, stationTimezone);
  const start = marketOpen; // -36h
  const end = marketClose; // +24h
  const totalHours = (end - start) / (1000 * 60 * 60); // 60 hours
  
  for (let i = 0; i <= totalHours; i += 3) {
    labels.push(new Date(start.getTime() + i * 60 * 60 * 1000));
  }
  return labels;
};

// X-axis configuration
<XAxis
  domain={[marketOpen, marketClose]}
  type="number"
  scale="time"
  ticks={generateTicks()}  // Ticks every 1 hour
  tickFormatter={(value) => {
    // Only show label if it's a multiple of 3 hours
    const eventDayMidnight = getEventDayLocalMidnight(eventDay, stationTimezone);
    const hoursDiff = (value.getTime() - eventDayMidnight.getTime()) / (1000 * 60 * 60);
    
    // Show label only every 3 hours
    if (Math.abs(hoursDiff) % 3 !== 0) return '';
    
    // Format as relative hours
    if (hoursDiff === 0) return '0h';
    if (hoursDiff < 0) return `${Math.round(hoursDiff)}h`;
    return `+${Math.round(hoursDiff)}h`;
  }}
  tick={{ fontSize: 12 }}  // Small labels
  label={{ value: 'Time', position: 'insideBottom', offset: -5 }}
/>
```

### **Visual Example**

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Event Day Labels (small, at top)                                        │
│ Pre-Event Day                    | Event Day                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ──────────────────────────────────│──────────────────────────────────  │
│  -36h  -33h  -30h  -27h  -24h  -21h│-18h  -15h  -12h  -9h  -6h  -3h   │
│    │     │     │     │     │     │ │  │     │     │     │     │     │  │
│    └─────┴─────┴─────┴─────┴─────┴─┴──┴─────┴─────┴─────┴─────┴─────┘  │
│                                                                          │
│  [Darker Background]              │ [Lighter Background]                │
│  (Pre-event)                      │ (Event day)                         │
│                                   │                                     │
│                                   │ (Vertical line at 0h)               │
│                                   │                                     │
│  -36h      -24h      -12h        0h      +12h      +24h                │
│  (Labels every 3h)                │ (Labels every 3h)                   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Horizontal Scroll Synchronization

### **Critical Requirement**

**All Three Charts Must Scroll Together**

This is **KEY** for correlation in time. The entire point of these graphs is to see how Zeus forecasts, market prices, and trades correlate at the same moments in time.

**Behavior**:
- Scroll horizontally on **ANY** graph → **ALL THREE** graphs scroll together
- Maintains perfect alignment across all three graphs
- Essential for correlating data points across graphs

### **Implementation**

#### **Option 1: Individual Containers with Refs (Recommended)**

```typescript
import { useRef, useState } from 'react';

const PerformanceGraphs = () => {
  // Shared scroll state
  const [scrollLeft, setScrollLeft] = useState(0);
  const graphRefs = useRef<Array<HTMLDivElement | null>>([null, null, null]);
  const isScrolling = useRef(false); // Prevent scroll loops

  // Handle scroll on any graph
  const handleScroll = (index: number, event: React.UIEvent<HTMLDivElement>) => {
    // Prevent infinite scroll loops
    if (isScrolling.current) return;
    
    const newScrollLeft = event.currentTarget.scrollLeft;
    setScrollLeft(newScrollLeft);
    
    // Sync scroll on all other graphs
    isScrolling.current = true;
    graphRefs.current.forEach((ref, i) => {
      if (ref && i !== index) {
        ref.scrollLeft = newScrollLeft;
      }
    });
    isScrolling.current = false;
  };

  // Calculate chart width based on timeline range
  // Chart should be wider than container to enable scrolling
  // But should match exact data boundaries (no empty space)
  const timelineStart = marketOpen; // -36h
  const timelineEnd = marketClose; // +24h
  const totalHours = (timelineEnd.getTime() - timelineStart.getTime()) / (1000 * 60 * 60); // 60 hours
  
  // Pixels per hour - adjust for desired spread/zoom level
  // Higher = more spread out, easier to read
  const pixelsPerHour = 60; // Adjust based on desired zoom level (e.g., 40-80)
  const totalWidth = totalHours * pixelsPerHour;
  
  // Container width (viewport)
  const containerWidth = 1200; // Or use window.innerWidth - padding

  return (
    <div className="performance-graphs-container">
      {/* Graph 1: Zeus Snapshots */}
      <div className="graph-wrapper">
        <h3>Zeus Snapshots (Daily High Predictions)</h3>
        <div
          className="graph-container"
          ref={(el) => (graphRefs.current[0] = el)}
          onScroll={(e) => handleScroll(0, e)}
          style={{
            overflowX: 'auto',
            overflowY: 'hidden',
            width: `${containerWidth}px`, // Fixed viewport width
            height: '400px',
            position: 'relative',
          }}
        >
          <div style={{ width: `${totalWidth}px`, height: '400px' }}>
            <LineChart 
              width={totalWidth} 
              height={400}
              margin={{ left: 20, right: 20, top: 20, bottom: 40 }}
            >
              <EventDayBackground />
              {/* Graph 1 content */}
              {/* X-axis domain should match exact timeline boundaries */}
              <XAxis
                domain={[timelineStart.getTime(), timelineEnd.getTime()]}
                type="number"
                scale="time"
                // ... other X-axis config
              />
            </LineChart>
          </div>
        </div>
      </div>

      {/* Graph 2: Market Probability History */}
      <div className="graph-wrapper">
        <h3>Market Probability History</h3>
        <div
          className="graph-container"
          ref={(el) => (graphRefs.current[1] = el)}
          onScroll={(e) => handleScroll(1, e)}
          style={{
            overflowX: 'auto',
            overflowY: 'hidden',
            width: `${containerWidth}px`, // Fixed viewport width
            height: '400px',
            position: 'relative',
          }}
        >
          <div style={{ width: `${totalWidth}px`, height: '400px' }}>
            <LineChart 
              width={totalWidth} 
              height={400}
              margin={{ left: 20, right: 20, top: 20, bottom: 40 }}
            >
              <EventDayBackground />
              {/* Graph 2 content */}
              <XAxis
                domain={[timelineStart.getTime(), timelineEnd.getTime()]}
                type="number"
                scale="time"
                // ... other X-axis config
              />
            </LineChart>
          </div>
        </div>
      </div>

      {/* Graph 3: Trade Decisions */}
      <div className="graph-wrapper">
        <h3>Trading Decisions Timeline</h3>
        <div
          className="graph-container"
          ref={(el) => (graphRefs.current[2] = el)}
          onScroll={(e) => handleScroll(2, e)}
          style={{
            overflowX: 'auto',
            overflowY: 'hidden',
            width: `${containerWidth}px`, // Fixed viewport width
            height: '400px',
            position: 'relative',
          }}
        >
          <div style={{ width: `${totalWidth}px`, height: '400px' }}>
            <ScatterChart 
              width={totalWidth} 
              height={400}
              margin={{ left: 20, right: 20, top: 20, bottom: 40 }}
            >
              <EventDayBackground />
              {/* Graph 3 content */}
              <XAxis
                domain={[timelineStart.getTime(), timelineEnd.getTime()]}
                type="number"
                scale="time"
                // ... other X-axis config
              />
            </ScatterChart>
          </div>
        </div>
      </div>
    </div>
  );
};
```

#### **Option 2: Single Scroll Container (Alternative)**

```typescript
const PerformanceGraphs = () => {
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // All graphs in a single scrollable container
  return (
    <div
      ref={scrollContainerRef}
      className="graphs-scroll-container"
      style={{
        overflowX: 'auto',
        overflowY: 'hidden',
        width: '100%',
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', minWidth: totalWidth }}>
        {/* Graph 1 */}
        <div className="graph-wrapper" style={{ width: totalWidth }}>
          <h3>Zeus Snapshots (Daily High Predictions)</h3>
          <LineChart width={totalWidth} height={400}>
            <EventDayBackground />
            {/* Graph 1 content */}
          </LineChart>
        </div>

        {/* Graph 2 */}
        <div className="graph-wrapper" style={{ width: totalWidth }}>
          <h3>Market Probability History</h3>
          <LineChart width={totalWidth} height={400}>
            <EventDayBackground />
            {/* Graph 2 content */}
          </LineChart>
        </div>

        {/* Graph 3 */}
        <div className="graph-wrapper" style={{ width: totalWidth }}>
          <h3>Trading Decisions Timeline</h3>
          <ScatterChart width={totalWidth} height={400}>
            <EventDayBackground />
            {/* Graph 3 content */}
          </ScatterChart>
        </div>
      </div>
    </div>
  );
};
```

### **Chart Width Calculation**

**Critical**: Chart must be wider than container to enable scrolling, but should match exact data boundaries.

**Formula**:
```typescript
// Timeline range
const timelineStart = marketOpen; // -36h
const timelineEnd = marketClose; // +24h
const totalHours = (timelineEnd.getTime() - timelineStart.getTime()) / (1000 * 60 * 60);

// Pixels per hour - controls spread/zoom
// Higher = more spread out, easier to read
// Recommended: 50-80 pixels per hour
const pixelsPerHour = 60;

// Total chart width (must be > container width for scrolling)
const totalWidth = totalHours * pixelsPerHour;

// Container width (viewport - what user sees)
const containerWidth = 1200; // Or window.innerWidth - padding
```

**Key Points**:
- ✅ Chart width = `totalHours * pixelsPerHour` (e.g., 60 hours * 60 px = 3600px)
- ✅ Container width = viewport width (e.g., 1200px)
- ✅ Chart is wider than container → enables scrolling
- ✅ X-axis domain matches exact timeline boundaries → no empty space
- ✅ Scroll stops at boundaries → no empty space left/right

### **Preventing Empty Space**

**Issue**: Scrollable but chart hasn't changed length, creating empty space.

**Solution**:
1. **Chart width must match data range exactly**:
   - X-axis domain: `[timelineStart.getTime(), timelineEnd.getTime()]`
   - Chart width: `totalHours * pixelsPerHour`
   - No padding/margin on X-axis domain

2. **Scroll boundaries**:
   - Max scroll left = 0 (start of data)
   - Max scroll right = `totalWidth - containerWidth` (end of data)
   - Prevent scrolling beyond these boundaries

**Implementation**:
```typescript
// Constrain scroll to data boundaries
const handleScroll = (index: number, event: React.UIEvent<HTMLDivElement>) => {
  if (isScrolling.current) return;
  
  const container = event.currentTarget;
  const maxScroll = totalWidth - containerWidth;
  
  // Constrain scroll position
  let newScrollLeft = container.scrollLeft;
  newScrollLeft = Math.max(0, Math.min(newScrollLeft, maxScroll));
  
  // If constrained, update scroll position
  if (newScrollLeft !== container.scrollLeft) {
    container.scrollLeft = newScrollLeft;
  }
  
  setScrollLeft(newScrollLeft);
  
  // Sync scroll on all other graphs
  isScrolling.current = true;
  graphRefs.current.forEach((ref, i) => {
    if (ref && i !== index) {
      ref.scrollLeft = newScrollLeft;
    }
  });
  isScrolling.current = false;
};
```

### **Scroll Behavior**

**How It Works**:
1. User scrolls horizontally on Graph 1
2. `handleScroll(0, e)` is called
3. New `scrollLeft` value is captured and constrained to boundaries
4. All other graphs (Graph 2, Graph 3) are scrolled to the same position
5. All three graphs stay perfectly aligned
6. Scroll stops at data boundaries (no empty space)

**Preventing Scroll Loops**:
- Use `isScrolling` ref to prevent infinite loops
- Only sync scroll when user initiates it (not programmatic scroll)

**Scroll Indicators**:
- Show scrollbar on all three graphs
- Visual indicator that graphs are scrollable
- Scrollbar disappears when at boundaries (optional)
- Optional: Add scroll buttons for navigation

---

## 🎨 CSS Styling

### **Graph Container Styles**

```css
.performance-graphs-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 100%;
}

.graph-wrapper {
  width: 100%;
  border: 1px solid #333;
  border-radius: 4px;
  padding: 10px;
  background: #1a1a1a;
}

.graph-container {
  position: relative;
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-width: thin;
  scrollbar-color: #666 #1a1a1a;
}

.graph-container::-webkit-scrollbar {
  height: 8px;
}

.graph-container::-webkit-scrollbar-track {
  background: #1a1a1a;
}

.graph-container::-webkit-scrollbar-thumb {
  background: #666;
  border-radius: 4px;
}

.graph-container::-webkit-scrollbar-thumb:hover {
  background: #888;
}
```

### **Event Day Background Styles**

```css
/* Pre-event area (darker) */
.recharts-reference-area-pre-event {
  fill: #1a1a1a;
  fill-opacity: 0.3;
}

/* Event-day area (lighter) */
.recharts-reference-area-event-day {
  fill: #2a2a2a;
  fill-opacity: 0.2;
}

/* Event boundary line */
.recharts-reference-line-event-boundary {
  stroke: #666;
  stroke-width: 1;
  stroke-dasharray: 2 2;
}
```

---

## ✅ Implementation Checklist

### **X-Axis Styling**
- [ ] Add vertical background bands (pre-event darker, event-day lighter)
- [ ] Add thin vertical line at 0h (event boundary)
- [ ] Add small labels at the top (pre-event / event day)
- [ ] Configure ticks every 1 hour
- [ ] Configure labels every 3 hours
- [ ] Position labels at the top of the axis
- [ ] Apply to all three graphs

### **Horizontal Scroll**
- [ ] Calculate chart width based on timeline range and pixels-per-hour
- [ ] Chart width must be wider than container (to enable scrolling)
- [ ] X-axis domain matches exact timeline boundaries (no padding)
- [ ] Implement synchronized scroll handler
- [ ] Constrain scroll to data boundaries (no empty space left/right)
- [ ] Prevent scroll loops (use ref flag)
- [ ] Test scroll on all three graphs
- [ ] Verify all three graphs stay aligned during scroll
- [ ] Verify scroll stops at boundaries (no empty space)
- [ ] Verify data is spread out and easier to read
- [ ] Add scrollbar styling
- [ ] Test with mouse wheel, trackpad, and scrollbar

### **Testing**
- [ ] Test scroll synchronization (scroll Graph 1, verify Graph 2 & 3 move)
- [ ] Test scroll in both directions
- [ ] Test with different zoom levels
- [ ] Test with different screen sizes
- [ ] Verify background bands align across all three graphs
- [ ] Verify event boundary line aligns across all three graphs
- [ ] Verify labels are readable and not cluttered

---

## 🎯 Key Points

### **X-Axis Styling**
- ✅ Visual distinction between pre-event and event-day periods
- ✅ Clear event boundary marker (0h line)
- ✅ Ticks every 1 hour for precision
- ✅ Labels every 3 hours to avoid clutter
- ✅ Small, readable labels

### **Horizontal Scroll**
- ✅ **CRITICAL**: All three graphs must scroll together
- ✅ Perfect alignment maintained during scroll
- ✅ Essential for time correlation
- ✅ Works with mouse wheel, trackpad, scrollbar
- ✅ Chart width matches data range exactly (no empty space)
- ✅ Scroll stops at data boundaries (no empty space left/right)
- ✅ Data is spread out for easier reading (configurable pixels-per-hour)

---

**Last Updated**: November 18, 2025

