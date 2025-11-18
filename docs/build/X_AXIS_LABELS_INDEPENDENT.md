# X-Axis Labels Independent of Data - Implementation Guide

**Date**: November 17, 2025  
**Purpose**: How to show full 24-hour X-axis labels (00:00 to 24:00) regardless of when data exists

---

## 🎯 Goal

**X-axis should always show full 24-hour range (00:00 to 24:00) with hourly labels, regardless of when snapshots/trades actually occurred.**

**Problem**: Category axes in many charting libraries only show labels for categories that exist in the data. If you only have snapshots from 09:00 to 23:45, the X-axis might only show those times.

**Solution**: Use a **continuous/numeric axis** or properly configure the axis to show all labels independently of data.

---

## ✅ Solution 1: Use Numeric/Continuous Axis (Recommended)

Instead of using a category axis (which requires data for each label), use a numeric axis that represents time as hours (0-24).

### Recharts (React)

```typescript
// Convert time strings to numeric hours for X-axis
function timeToHours(timeStr: string): number {
  const [hours, minutes] = timeStr.split(':').map(Number);
  return hours + minutes / 60;  // e.g., "09:15" → 9.25
}

// Prepare data with numeric time values
const chartData = actualData.map(point => ({
  time: timeToHours(point.time),  // Numeric: 9.25, 12.5, etc.
  timeLabel: point.time,  // Keep original for tooltip
  value: point.value,
}));

// X-Axis configuration
<XAxis 
  type="number"  // ← KEY: Use numeric, not category
  domain={[0, 24]}  // Full 24-hour range
  ticks={[0, 3, 6, 9, 12, 15, 18, 21, 24]}  // Hourly labels
  tickFormatter={(value) => {
    // Format numeric hours back to HH:MM
    const hours = Math.floor(value);
    const minutes = Math.round((value - hours) * 60);
    return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
  }}
  angle={-45}
  height={60}
/>
```

**Benefits**:
- ✅ No dummy data needed
- ✅ Labels always show (00:00 to 24:00)
- ✅ Data points plotted at exact times
- ✅ Works regardless of data density

---

### Plotly (Python/Streamlit)

```python
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# Convert time strings to numeric hours
def time_to_hours(time_str):
    """Convert 'HH:MM' to numeric hours."""
    hours, minutes = map(int, time_str.split(':'))
    return hours + minutes / 60

# Prepare data
zeus_times_numeric = [time_to_hours(t) for t in zeus_times]
poly_times_numeric = [time_to_hours(t) for t in poly_times]
trade_times_numeric = [time_to_hours(t) for t in trade_times]

# Create figure
fig = make_subplots(
    rows=3, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.05,
)

# Add traces with numeric X values
fig.add_trace(
    go.Scatter(x=zeus_times_numeric, y=zeus_temps, name="Zeus Latest"),
    row=1, col=1
)

# Configure X-axis
fig.update_xaxes(
    title_text="Time",
    range=[0, 24],  # Full 24-hour range
    tickmode='linear',  # or 'array'
    tick0=0,
    dtick=3,  # Show label every 3 hours (0, 3, 6, 9, 12, 15, 18, 21, 24)
    tickformat='%H:%M',  # Format as HH:MM
    tickangle=-45,
    row=3, col=1
)
```

**Benefits**:
- ✅ No dummy data needed
- ✅ Labels always show
- ✅ Clean and simple

---

## ✅ Solution 2: Configure Category Axis Properly

If you must use a category axis, configure it to show all labels.

### Recharts with Category Axis

```typescript
// Define all hourly labels upfront
const allHourlyLabels = Array.from({ length: 25 }, (_, i) => {
  const hours = i;
  return `${String(hours).padStart(2, '0')}:00`;
});  // ['00:00', '01:00', ..., '24:00']

// Prepare data - include all hours, but only actual data has values
const chartData = allHourlyLabels.map(hour => {
  // Find actual data point for this hour (if exists)
  const actualPoint = actualData.find(d => d.time.startsWith(hour.substring(0, 2)));
  
  return {
    time: hour,  // Always include the hour label
    value: actualPoint ? actualPoint.value : null,  // null if no data
  };
});

// X-Axis configuration
<XAxis 
  type="category"  // Category axis
  dataKey="time"
  domain={allHourlyLabels}  // Explicitly set all categories
  ticks={allHourlyLabels.filter((_, i) => i % 3 === 0)}  // Show every 3rd hour
  angle={-45}
  height={60}
/>
```

**Note**: This approach still requires creating data entries for all hours (with null values), but it's more explicit and controlled.

---

## ✅ Solution 3: Use Time Scale (Best for Time Series)

Some libraries support proper time scales that handle this automatically.

### Chart.js with Time Scale

```typescript
import { Chart, registerables } from 'chart.js';
import 'chartjs-adapter-date-fns';

Chart.register(...registerables);

const chartData = {
  labels: actualData.map(d => d.timestamp),  // ISO timestamps
  datasets: [{
    data: actualData.map(d => d.value),
  }]
};

const options = {
  scales: {
    x: {
      type: 'time',  // ← Time scale
      time: {
        unit: 'hour',
        displayFormats: {
          hour: 'HH:mm'
        }
      },
      min: '2025-11-17T00:00:00',  // Start of day
      max: '2025-11-17T24:00:00',  // End of day
      ticks: {
        stepSize: 3,  // Show label every 3 hours
        maxRotation: 45,
        minRotation: 45,
      }
    }
  }
};
```

**Benefits**:
- ✅ Proper time handling
- ✅ Automatic label generation
- ✅ No dummy data needed
- ✅ Handles time zones correctly

---

## 📊 Comparison of Approaches

| Approach | Dummy Data Needed? | Labels Always Show? | Complexity | Best For |
|----------|-------------------|---------------------|------------|----------|
| **Numeric Axis** | ❌ No | ✅ Yes | Low | Recharts, Plotly |
| **Category Axis (Configured)** | ⚠️ Yes (null values) | ✅ Yes | Medium | Recharts |
| **Time Scale** | ❌ No | ✅ Yes | Low | Chart.js, D3 |

---

## 🎯 Recommended Implementation

### For Recharts (React)

**Use Numeric Axis** - It's the cleanest solution:

```typescript
// Helper functions
function timeToHours(timeStr: string): number {
  const [hours, minutes] = timeStr.split(':').map(Number);
  return hours + minutes / 60;
}

function hoursToTime(hours: number): string {
  const h = Math.floor(hours);
  const m = Math.round((hours - h) * 60);
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

// Prepare data
const zeusData = zeusSnapshots.map(snapshot => ({
  time: timeToHours(snapshot.fetch_time),  // Numeric: 9.25, 12.5, etc.
  timeLabel: snapshot.fetch_time,  // Keep for tooltip
  temp: snapshot.predicted_high,
}));

// X-Axis configuration
<XAxis 
  type="number"  // ← Numeric axis
  domain={[0, 24]}  // Full 24-hour range
  ticks={[0, 3, 6, 9, 12, 15, 18, 21, 24]}  // Hourly labels (every 3 hours)
  tickFormatter={(value) => hoursToTime(value)}  // Format back to HH:MM
  angle={-45}
  height={60}
  label={{ value: 'Time', position: 'insideBottom', offset: -5 }}
/>
```

### For Plotly (Python/Streamlit)

**Use Numeric Axis** - Same approach:

```python
def time_to_hours(time_str):
    """Convert 'HH:MM' to numeric hours."""
    hours, minutes = map(int, time_str.split(':'))
    return hours + minutes / 60

# Convert all times to numeric
zeus_times_numeric = [time_to_hours(t) for t in zeus_times]

# Configure X-axis
fig.update_xaxes(
    title_text="Time",
    range=[0, 24],  # Full 24-hour range
    tickmode='linear',
    tick0=0,
    dtick=3,  # Every 3 hours
    tickformat='%H:%M',  # Format as HH:MM
    tickangle=-45,
    row=3, col=1
)
```

---

## ❌ What NOT to Do

### Don't Add Dummy Data Points

```typescript
// ❌ BAD: Adding dummy data just for labels
const dummyData = Array.from({ length: 25 }, (_, i) => ({
  time: `${String(i).padStart(2, '0')}:00`,
  value: null,  // Dummy point
}));
const chartData = [...dummyData, ...actualData];
```

**Why it's bad**:
- Clutters data structure
- Can cause rendering issues
- Makes data processing more complex
- Not necessary with proper axis configuration

---

## ✅ Summary

**Best Practice**: Use a **numeric/continuous axis** that represents time as hours (0-24).

1. **Convert time strings to numeric hours** (e.g., "09:15" → 9.25)
2. **Set X-axis domain to [0, 24]** (full day)
3. **Configure ticks** to show hourly labels (e.g., every 3 hours: 0, 3, 6, 9, 12, 15, 18, 21, 24)
4. **Format ticks** back to HH:MM for display
5. **Plot actual data** at their numeric time values

**Result**: 
- ✅ X-axis always shows full 24-hour range
- ✅ Labels appear regardless of data
- ✅ No dummy data needed
- ✅ Clean and maintainable code

---

## 🔧 Quick Reference

### Recharts (Numeric Axis)
```typescript
<XAxis 
  type="number"
  domain={[0, 24]}
  ticks={[0, 3, 6, 9, 12, 15, 18, 21, 24]}
  tickFormatter={(h) => `${String(Math.floor(h)).padStart(2, '0')}:00`}
/>
```

### Plotly (Numeric Axis)
```python
fig.update_xaxes(
    range=[0, 24],
    tickmode='linear',
    tick0=0,
    dtick=3,
    tickformat='%H:%M',
)
```

### Chart.js (Time Scale)
```typescript
scales: {
  x: {
    type: 'time',
    min: '2025-11-17T00:00:00',
    max: '2025-11-17T24:00:00',
  }
}
```

---

**Last Updated**: November 17, 2025

