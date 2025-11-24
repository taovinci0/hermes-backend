# Performance Page: Historical 24-Hour Temperature Forecast Graph

**Date**: November 18, 2025  
**Purpose**: Plan the historical version of Live Dashboard's intraday forecast graph for Performance page  
**Graph Name**: "24-Hour Temperature Forecast (Historical)"

---

## 🎯 Overview

**Goal**: Use the SAME graph component from Live Dashboard, just showing:
- **Final/historical data** (not updating)
- **Zeus Latest** (final intraday forecast) - same as Live Dashboard
- **Zeus Median** - same as Live Dashboard
- **METAR Actual** (NEW - only for historical)
- **Accuracy panel** on right side (NEW - shows if prediction was correct)

**Key Point**: This is essentially the SAME graph as Live Dashboard, just the final/historical version with METAR and accuracy metrics added.

---

## 📊 Graph Specification

### **Graph Name**
**"24-Hour Temperature Forecast (Historical)"**

### **Purpose**
Show the archived intraday forecast for the selected station/day, compared directly to METAR actual temperatures, along with an accuracy panel for the daily high prediction.

**This is the historical version of the live dashboard's intraday forecast chart** — not to be confused with forecast evolution over multiple days.

---

## 📈 What the Graph Shows (Left Side)

### **Data Series**

**This is the SAME graph as Live Dashboard, just with historical data:**

1. **Zeus Latest Curve**
   - Final intraday temperature forecast for that day
   - **Same as Live Dashboard's "Zeus Latest"**
   - Source: Latest Zeus snapshot for that day (before event started)
   - Shows: Full 24-hour hourly temperature forecast curve

2. **Zeus Median Curve**
   - Median of all intraday temperature forecasts for that day
   - **Same as Live Dashboard's "Zeus Median"**
   - Source: All Zeus snapshots for that day
   - Shows: Median hourly temperature across all snapshots

3. **METAR Actual Temperatures** (NEW for historical)
   - Observed temperatures from METAR
   - Plotted at their actual observation times
   - Source: METAR snapshots for that day
   - Shows: Actual temperature observations throughout the day

### **Axes**

- **X-Axis**: Local time (00:00 → 23:00)
  - Full 24-hour day
  - Labels: Hourly or every few hours for readability
  - Independent of data point density

- **Y-Axis**: Temperature (°F)
  - **Dynamically scaled** to min/max of actual and forecasted data
  - Ensures lines are easy to read
  - Not fixed range (unlike Live Dashboard which might use fixed range)

### **Visual Design**

- **Same look/feel as Live Dashboard**:
  - Same line styles
  - Same colors
  - Same legend
  - Same overall layout

- **Historical adaptations**:
  - METAR actual line added (different color/style)
  - All data is complete (no "updating" indicators)
  - Can show final outcome (correct/incorrect)

---

## 📋 Right-Side Panel: Daily High Prediction Accuracy

**Panel Title**: "Daily High Prediction Accuracy"

This panel evaluates Zeus's final predicted high vs. the actual observed high.

### **Metrics to Display**

#### **1. Predicted High**
- The final forecasted high before the event began
- Source: Latest Zeus snapshot's `daily_high` prediction
- Format: `44.6°F`

#### **2. Actual High**
- Observed maximum temperature from METAR
- Source: Maximum temperature from all METAR observations for that day
- Format: `44.8°F`

#### **3. Error**
- Actual minus predicted (METAR actual high - Zeus predicted high)
- Format: `+0.2°F` or `-0.5°F`
- **Color-coded accuracy** (based on raw temperature error):
  - ✅ Green: Error ≤ 0.5°F (accurate)
  - ⚠️ Yellow: Error 0.5-1.0°F (acceptable)
  - ❌ Red: Error > 1.0°F (inaccurate)
- **Note**: This shows forecast accuracy (Zeus vs METAR), not trading bracket accuracy. For bracket accuracy, see the trading decisions graph.

#### **4. Final Forecast Age**
- How many hours before the event Zeus issued its final prediction
- Format: `2.5 hours before event`
- Source: Time difference between last Zeus snapshot and event start time

#### **5. Forecast Stability**
- How much the predicted high fluctuated in the final few hours
- Format: `±0.4°F`
- Calculation: Standard deviation of predicted highs from last 3-4 snapshots
- Source: Last few Zeus snapshots before event

#### **6. Final Updates**
- A short list of the last forecasted highs leading up to the event
- Shows drift and direction
- Format:
  ```
  Final Updates:
  09:18 → 44.6°F
  10:51 → 44.8°F (+0.2°F)
  12:15 → 44.6°F (-0.2°F)
  ```
- Source: Last 3-4 Zeus snapshots before event

---

## 🔄 Differences from Live Dashboard

### **Live Dashboard Graph**
- **Real-time**: Updates as new data arrives
- **No METAR**: Only shows forecasts (actual not yet available)
- **No accuracy panel**: Can't evaluate accuracy yet
- **Dynamic updates**: Shows "updating" indicators
- **Same data series**: Zeus Latest + Zeus Median

### **Historical Graph (Performance Page)**
- **Static**: All data is complete (final version)
- **Includes METAR**: Shows actual temperatures (NEW)
- **Accuracy panel**: Shows if prediction was correct (NEW)
- **Same graph component**: Reuse Live Dashboard graph, just add METAR line
- **Dynamic Y-axis**: Scaled to data for readability (same as Live Dashboard)

**Key Point**: This is essentially the SAME graph as Live Dashboard, just:
1. Showing final/historical data (not updating)
2. Adding METAR actual line
3. Adding accuracy panel on right side

---

## 🎨 Visual Mockup

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Performance                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ Station: [EGLC ▼]  Date: [2025-11-16 ▼]                                    │
│                                                                              │
│ ┌──────────────────────────────────────────────────────────────────────┐  │
│ │ 24-Hour Temperature Forecast (Historical)                            │  │
│ │                                                                      │  │
│ │  50°F ┤                                                              │  │
│ │       │         ╱─── Zeus Latest                                    │  │
│ │  45°F ┤    ╱───╱     ┅┅┅ Zeus Median                                │  │
│ │       │   ╱           ••• METAR Actual                              │  │
│ │  40°F ┤──╱                                                           │  │
│ │       │                                                              │  │
│ │       └────────────────────────────────────────────────────          │  │
│ │       00:00  06:00  12:00  18:00  24:00                             │  │
│ │                                                                      │  │
│ │  ┌────────────────────────────────────────────────────────────┐    │  │
│ │  │ Daily High Prediction Accuracy                             │    │  │
│ │  │                                                             │    │  │
│ │  │ Predicted High: 44.6°F                                     │    │  │
│ │  │ Actual High: 44.8°F                                        │    │  │
│ │  │ Error: +0.2°F ✅ (Accurate)                                │    │  │
│ │  │                                                             │    │  │
│ │  │ Final Forecast Age: 2.5 hours before event                 │    │  │
│ │  │ Forecast Stability: ±0.4°F                                 │    │  │
│ │  │                                                             │    │  │
│ │  │ Final Updates:                                             │    │  │
│ │  │ 09:18 → 44.6°F                                             │    │  │
│ │  │ 10:51 → 44.8°F (+0.2°F)                                    │    │  │
│ │  │ 12:15 → 44.6°F (-0.2°F)                                    │    │  │
│ │  └────────────────────────────────────────────────────────────┘    │  │
│ └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│ [Graph 2: Polymarket Probabilities]                                         │
│ [Graph 3: Trading Decisions]                                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Implementation Plan

### **Stage 1: Data Collection & Processing**

#### **1.1 Zeus Forecast Data**
**Source**: Zeus snapshots for selected day/station

**Required Data**:
- All Zeus snapshots for that day
- Extract `daily_high` from each snapshot
- Extract intraday temperature curve from latest snapshot
- Calculate median intraday curve from all snapshots

**Processing**:
- Filter snapshots by date and station
- Sort by timestamp
- Identify "final" snapshot (last one before event start)
- Extract temperature data points

**Time**: 2-3 hours

---

#### **1.2 METAR Actual Data**
**Source**: METAR snapshots for selected day/station

**Required Data**:
- All METAR observations for that day
- Extract temperature and observation time
- Calculate daily high (maximum temperature)

**Processing**:
- Filter METAR snapshots by date and station
- Extract temperature and timestamp
- Find maximum temperature (daily high)
- Prepare time series for plotting

**Time**: 2-3 hours

---

#### **1.3 Accuracy Metrics Calculation**
**Source**: Zeus and METAR data

**Calculations**:
- Predicted High: Latest Zeus snapshot's `daily_high`
- Actual High: Maximum METAR temperature
- Error: Actual - Predicted
- Final Forecast Age: Time between last Zeus snapshot and event start
- Forecast Stability: Std dev of last 3-4 predicted highs
- Final Updates: Last 3-4 predicted highs with timestamps

**Time**: 2-3 hours

---

### **Stage 2: Backend API Endpoint**

#### **2.1 Create Historical Forecast Endpoint**
**File**: `backend/api/routes/performance.py`

**Endpoint**: `GET /api/performance/historical-forecast/{station_code}/{date}`

**Response**:
```json
{
  "station_code": "EGLC",
  "date": "2025-11-16",
  "zeus_latest": {
    "times": ["00:00", "01:00", ...],
    "temperatures": [40.2, 40.5, ...]
  },
  "zeus_median": {
    "times": ["00:00", "01:00", ...],
    "temperatures": [40.1, 40.4, ...]
  },
  "metar_actual": {
    "times": ["00:15", "01:30", ...],
    "temperatures": [40.3, 40.6, ...]
  },
  "daily_high_accuracy": {
    "predicted_high": 44.6,
    "actual_high": 44.8,
    "error": 0.2,
    "error_category": "accurate",
    "final_forecast_age_hours": 2.5,
    "forecast_stability": 0.4,
    "final_updates": [
      {"time": "09:18", "predicted_high": 44.6, "change": null},
      {"time": "10:51", "predicted_high": 44.8, "change": 0.2},
      {"time": "12:15", "predicted_high": 44.6, "change": -0.2}
    ]
  }
}
```

**Time**: 4-5 hours

---

### **Stage 3: Frontend Graph Component**

#### **3.1 Create Historical Forecast Graph Component**
**File**: `frontend/src/pages/Performance/HistoricalForecastGraph.tsx`

**Features**:
- Reuse Live Dashboard graph component (if possible)
- Add METAR actual line
- Dynamic Y-axis scaling
- Accuracy panel on right side
- Same styling as Live Dashboard

**Time**: 6-8 hours

---

#### **3.2 Accuracy Panel Component**
**File**: `frontend/src/pages/Performance/DailyHighAccuracyPanel.tsx`

**Features**:
- Display all 6 metrics
- Color-coded error indicator
- Final updates list
- Responsive layout

**Time**: 3-4 hours

---

#### **3.3 Integration**
**File**: `frontend/src/pages/Performance/PerformancePage.tsx`

**Changes**:
- Replace existing Graph 1 with new Historical Forecast Graph
- Integrate accuracy panel
- Ensure proper data flow

**Time**: 2-3 hours

---

## 📋 Implementation Checklist

### **Backend**
- [ ] Create historical forecast data processing service
- [ ] Create METAR data processing for historical dates
- [ ] Calculate accuracy metrics
- [ ] Create `/api/performance/historical-forecast` endpoint
- [ ] Test endpoint with real data

### **Frontend**
- [ ] Create Historical Forecast Graph component
- [ ] Reuse/adapt Live Dashboard graph styling
- [ ] Add METAR actual line
- [ ] Implement dynamic Y-axis scaling
- [ ] Create Daily High Accuracy Panel component
- [ ] Integrate into Performance page
- [ ] Test with real data

---

## 🎯 Key Requirements

### **Must Match Live Dashboard**
- ✅ Same line styles
- ✅ Same colors
- ✅ Same legend
- ✅ Same overall layout
- ✅ Same look/feel

### **Historical Adaptations**
- ✅ Add METAR actual line
- ✅ Add accuracy panel
- ✅ Dynamic Y-axis (not fixed)
- ✅ Show final outcome
- ✅ All data complete (no "updating")

### **Data Requirements**
- ✅ Zeus Latest curve (final intraday forecast)
- ✅ Zeus Median curve
- ✅ METAR actual temperatures
- ✅ Daily high accuracy metrics
- ✅ Forecast stability
- ✅ Final updates list

---

## 🔍 Data Sources

### **Zeus Data**
- **Source**: `data/snapshots/zeus/{date}/{station_code}/*.json`
- **Fields**: `daily_high`, intraday temperature curve
- **Processing**: Extract latest snapshot, calculate median

### **METAR Data**
- **Source**: `data/snapshots/metar/{date}/{station_code}/*.json`
- **Fields**: `temperature`, `observation_time`
- **Processing**: Extract all observations, find daily high

### **Event Start Time**
- **Source**: Station timezone + event date
- **Calculation**: Local midnight of event date

---

## ✅ Success Criteria

**Graph displays correctly when**:
- ✅ Shows Zeus Latest curve (final intraday forecast)
- ✅ Shows Zeus Median curve
- ✅ Shows METAR actual temperatures
- ✅ X-axis spans 00:00 → 23:00 (local time)
- ✅ Y-axis dynamically scaled to data
- ✅ Accuracy panel shows all 6 metrics
- ✅ Error is color-coded correctly
- ✅ Final updates list shows last 3-4 predictions
- ✅ Matches Live Dashboard look/feel

---

## 🚀 Timeline

### **Week 1: Backend**
- Day 1-2: Data processing services
- Day 3-4: API endpoint
- Day 5: Testing

### **Week 2: Frontend**
- Day 1-2: Graph component
- Day 3: Accuracy panel
- Day 4: Integration
- Day 5: Testing & polish

**Total**: 2 weeks

---

**Last Updated**: November 18, 2025

