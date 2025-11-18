# Historical Graphs Time Axis - Implementation Guide

**Date**: November 17, 2025  
**Purpose**: Clarify how the time axis (X-axis) should work for the three stacked graphs on the historical data page

---

## 🎯 Key Principle

**YES - All three graphs MUST share the same X-axis (time scale) for proper alignment.**

This allows users to:
- See what happened at the same moment across all three data sources
- Hover over one graph and see a vertical line across all three
- Correlate Zeus forecasts, market prices, and trades at specific times

---

## 📊 The Three Graphs

### Graph 1: Zeus Forecast Evolution vs METAR Actual
**X-Axis**: **Snapshot fetch times** (when each Zeus forecast was fetched)

**Examples**:
- `09:00` - First Zeus snapshot of the day
- `12:15` - Zeus snapshot at 12:15
- `15:30` - Zeus snapshot at 15:30
- `18:45` - Zeus snapshot at 18:45

**Data Points**:
- Each point represents a Zeus snapshot's **predicted daily high** temperature
- Multiple lines show forecast evolution (latest, 15min ago, 30min ago, etc.)
- METAR actual temperatures are plotted at their observation times

**Time Range**: Full 24-hour day (`00:00` to `24:00`), with data points plotted at their actual snapshot times

---

### Graph 2: Polymarket Implied Probabilities
**X-Axis**: **Snapshot fetch times** (when each Polymarket snapshot was taken)

**Examples**:
- `09:00` - First Polymarket snapshot
- `12:15` - Polymarket snapshot at 12:15
- `15:30` - Polymarket snapshot at 15:30
- `18:45` - Polymarket snapshot at 18:45

**Data Points**:
- Each point represents market-implied probability for a bracket at that snapshot time
- Multiple lines (one per bracket) show how probabilities evolved

**Time Range**: Full 24-hour day (`00:00` to `24:00`), with data points plotted at their actual snapshot times

---

### Graph 3: Trading Decisions Timeline
**X-Axis**: **Decision/trade times** (when each trade was placed)

**Examples**:
- `09:15` - Trade placed at 09:15
- `12:20` - Trade placed at 12:20
- `15:35` - Trade placed at 15:35
- `18:50` - Trade placed at 18:50

**Data Points**:
- Each point represents a trade (discrete event)
- Shows trade size, bracket, and edge percentage

**Time Range**: Full 24-hour day (`00:00` to `24:00`), with trades plotted at their actual decision times

---

## ⚠️ Important: Time Alignment

### All Graphs Use the Same Time Scale

**X-Axis Format**: `HH:MM` (24-hour format)

**Time Range**: 
- **Always `00:00` to `24:00`** (full 24-hour day)
- Provides consistent context and makes it clear when events occurred
- Even if data only exists from `09:00` to `23:45`, show full day range

**Example**:
- First Zeus snapshot: `09:00`
- First Polymarket snapshot: `09:05`
- First trade: `09:15`
- Last snapshot: `23:45`

**X-Axis Range**: `00:00` to `24:00` (full day, even though data starts at 09:00)

---

## 🔄 Data Synchronization

### Snapshot Times

Zeus, Polymarket, and Decision snapshots are taken **at the same time** during each trading cycle:

```
Cycle 1: 09:00
  ├─ Zeus snapshot: 09:00:15
  ├─ Polymarket snapshot: 09:00:20
  └─ Decision snapshot: 09:00:25

Cycle 2: 12:15
  ├─ Zeus snapshot: 12:15:10
  ├─ Polymarket snapshot: 12:15:15
  └─ Decision snapshot: 12:15:20
```

**For alignment purposes**, use the **decision_time** (or cycle time) as the canonical timestamp for all three data sources in that cycle.

---

## 📐 Implementation Details

### Chart Library Configuration

**Recharts (React)**:
```typescript
// All three graphs use the same syncId for alignment
const syncId = "historicalTimeline";

// Helper function to determine which labels to show
function getXAxisTicks(times: string[], maxLabels: number = 8): string[] {
  if (times.length <= maxLabels) return times;
  
  // Show evenly spaced labels (e.g., every 2-3 hours)
  const step = Math.ceil(times.length / maxLabels);
  return times.filter((_, index) => index % step === 0 || index === times.length - 1);
}

// Graph 1: Zeus + METAR
<LineChart 
  data={zeusData} 
  syncId={syncId}
>
  <XAxis 
    dataKey="time" 
    type="category"  // or "number" if using timestamps
    domain={['00:00', '24:00']}  // Always full 24-hour day
    ticks={getXAxisTicks(['00:00', '03:00', '06:00', '09:00', '12:00', '15:00', '18:00', '21:00', '24:00'], 8)}  // Show max 8 labels
    angle={-45}  // Rotate labels for readability
    textAnchor="end"
    height={60}  // Extra height for rotated labels
  />
  <YAxis domain={[50, 60]} label="Temperature (°F)" />
  ...
</LineChart>

// Graph 2: Polymarket
<LineChart 
  data={polymarketData} 
  syncId={syncId}
>
  <XAxis 
    dataKey="time" 
    type="category"  // Same type as Graph 1
    domain={[minTime, maxTime]}  // Same domain as Graph 1
  />
  <YAxis domain={[0, 100]} label="Probability (%)" />
  ...
</LineChart>

// Graph 3: Trades
<ScatterChart 
  data={tradesData} 
  syncId={syncId}
>
  <XAxis 
    dataKey="time" 
    type="category"  // Same type as Graph 1 & 2
    domain={[minTime, maxTime]}  // Same domain as Graph 1 & 2
  />
  <YAxis domain={[0, 500]} label="Trade Size ($)" />
  ...
</ScatterChart>
```

**Plotly (Streamlit/Python)**:
```python
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# Helper function to get evenly spaced tick labels
def get_xaxis_ticks(times, max_labels=8):
    """Return evenly spaced time labels for X-axis."""
    if len(times) <= max_labels:
        return times
    # Convert times to indices, get evenly spaced indices
    indices = np.linspace(0, len(times) - 1, max_labels, dtype=int)
    return [times[i] for i in indices]

# Create subplots with shared X-axis
fig = make_subplots(
    rows=3, cols=1,
    shared_xaxes=True,  # ← KEY: Shared X-axis
    vertical_spacing=0.05,
    subplot_titles=(
        "Zeus Forecast Evolution vs METAR Actual",
        "Polymarket Implied Probabilities",
        "Trading Decisions Timeline"
    )
)

# Graph 1: Zeus + METAR
fig.add_trace(
    go.Scatter(x=zeus_times, y=zeus_temps, name="Zeus Latest"),
    row=1, col=1
)

# Graph 2: Polymarket
fig.add_trace(
    go.Scatter(x=poly_times, y=poly_probs, name="Bracket 58-59°F"),
    row=2, col=1
)

# Graph 3: Trades
fig.add_trace(
    go.Scatter(x=trade_times, y=trade_sizes, mode='markers', name="Trades"),
    row=3, col=1
)

# Update X-axis for all graphs (shared)
# Always show full 24-hour day (00:00 to 24:00)
# Show all data points, but only label every few hours
full_day_ticks = ['00:00', '03:00', '06:00', '09:00', '12:00', '15:00', '18:00', '21:00', '24:00']
xaxis_ticks = get_xaxis_ticks(full_day_ticks, max_labels=8)
fig.update_xaxes(
    title_text="Time",
    range=[0, 24],  # Full 24-hour range
    tickmode='array',
    tickvals=xaxis_ticks,  # Only show these labels
    ticktext=xaxis_ticks,  # But all data points are still plotted at their actual times
    tickangle=-45,  # Rotate labels
    row=3, col=1  # Only label bottom graph
)
```

---

## 🕐 Time Format Considerations

### Option 1: Time of Day (Recommended)
**Format**: `HH:MM` (e.g., `09:00`, `12:15`, `15:30`)

**Pros**:
- Easy to read
- Natural for users
- Works well for single-day analysis

**Cons**:
- Doesn't show date (but date is in page header)
- Can be ambiguous if spanning multiple days

**Use When**: Analyzing a single event day

---

### Option 2: Full Timestamp
**Format**: `YYYY-MM-DD HH:MM` (e.g., `2025-11-17 09:00`)

**Pros**:
- Unambiguous
- Works for multi-day analysis
- Precise

**Cons**:
- More cluttered
- Redundant if date is in page header

**Use When**: Analyzing multiple days or need precise timestamps

---

### Option 3: Relative Time
**Format**: `+HH:MM` from start (e.g., `+00:00`, `+03:15`, `+06:30`)

**Pros**:
- Clean
- Shows duration

**Cons**:
- Less intuitive
- Harder to correlate with actual times

**Use When**: Focus is on duration/sequence, not absolute time

---

## ✅ Recommended Approach

**For Historical Data Page (Single Day Analysis)**:

1. **X-Axis Format**: `HH:MM` (time of day)
2. **Time Range**: **Always `00:00` to `24:00` (full 24-hour day)**
   - Even if snapshots only exist from 09:00 to 23:00
   - Provides full day context and consistency
   - Makes it clear when in the day events occurred
3. **All Graphs**: Use same X-axis scale and domain
4. **Synchronization**: Use `syncId` (Recharts) or `shared_xaxes=True` (Plotly)

**Example X-Axis Labels**:

With snapshots every 15 minutes (96 data points), show only key labels:
```
00:00        06:00        12:00        18:00        24:00
```

Or every 2-3 hours:
```
00:00   03:00   06:00   09:00   12:00   15:00   18:00   21:00   24:00
```

**Important**: 
- **X-Axis always spans full 24 hours** (00:00 to 24:00) for consistency
- **All data points are still plotted** at their actual times (even if sparse early morning)
- **Only X-axis labels are reduced** for readability (show 6-8 labels max)
- **Empty periods** (e.g., 00:00-09:00 with no data) will show as gaps in the lines

---

## 🔍 Data Preparation

### Step 1: Prepare Full Day Time Range

```typescript
// Always use full 24-hour day for X-axis
const fullDayTimes = Array.from({ length: 97 }, (_, i) => {
  // Generate times from 00:00 to 24:00 (every 15 minutes = 97 points)
  const hours = Math.floor(i * 15 / 60);
  const minutes = (i * 15) % 60;
  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
});

// Or simpler: just define the range
const xAxisDomain = ['00:00', '24:00'];
const xAxisTicks = ['00:00', '06:00', '12:00', '18:00', '24:00'];  // Labels to show

// Get actual data timestamps (for plotting)
const zeusTimes = zeusSnapshots.map(s => s.fetch_time);
const polyTimes = polymarketSnapshots.map(s => s.fetch_time);
const tradeTimes = trades.map(t => t.timestamp);
```

### Step 2: Normalize Time Format

```typescript
// Convert all timestamps to same format (HH:MM)
function normalizeTime(timestamp: string): string {
  const date = new Date(timestamp);
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  return `${hours}:${minutes}`;
}
```

### Step 3: Create Data Points

```typescript
// For each time point, create data entry with values from all three sources
const chartData = allTimes.map(time => ({
  time: normalizeTime(time),
  zeus_temp: getZeusValueAtTime(time),
  poly_prob_58_59: getPolyValueAtTime(time, '58-59°F'),
  trade_size: getTradeSizeAtTime(time),
  // ... other values
}));
```

---

## 🎨 Visual Alignment

### Hover Interaction

When user hovers over any graph:
1. Show vertical line at that time across **all three graphs**
2. Display tooltip with values from **all three data sources** at that time
3. Highlight corresponding points on all graphs

**Example Tooltip**:
```
Time: 12:15
─────────────────
Zeus: 57.8°F
Market (58-59°F): 5.2%
Trade: $300 @ 18% edge
```

---

## ❌ Common Mistakes to Avoid

### 1. Different Time Scales
```typescript
// ❌ WRONG - Graph 1 uses 00:00-24:00, Graph 2 uses 09:00-18:00
<XAxis domain={[0, 24]} />  // Graph 1
<XAxis domain={[9, 18]} />  // Graph 2

// ✅ CORRECT - Both use same domain
const timeDomain = [minTime, maxTime];
<XAxis domain={timeDomain} />  // Graph 1
<XAxis domain={timeDomain} />  // Graph 2
```

### 2. Different Time Formats
```typescript
// ❌ WRONG - Graph 1 uses "09:00", Graph 2 uses "9:00 AM"
// ✅ CORRECT - All use same format (HH:MM)
```

### 3. Missing Synchronization
```typescript
// ❌ WRONG - No syncId, graphs don't align on hover
<LineChart data={data1} />
<LineChart data={data2} />

// ✅ CORRECT - Use syncId for alignment
<LineChart data={data1} syncId="historicalTimeline" />
<LineChart data={data2} syncId="historicalTimeline" />
```

---

## 📋 Summary

**YES - All three graphs MUST share the same X-axis (time scale).**

- **X-Axis**: Snapshot/decision times (when data was collected)
- **Format**: `HH:MM` (time of day) for single-day analysis
- **Range**: From first to last data point (or full day `00:00-24:00`)
- **Synchronization**: Use `syncId` (Recharts) or `shared_xaxes=True` (Plotly)
- **Alignment**: All graphs must use the same time domain and format

This ensures users can easily correlate what happened at the same moment across all three data sources.

---

**Last Updated**: November 17, 2025

