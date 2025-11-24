# Historical Data Visualization Strategy

**Purpose**: Define the best approach for displaying historical data on the Historical Data page  
**Date**: November 18, 2025  
**Key Insight**: Historical page should show **hourly forecast evolution** (like live dashboard), not just daily high predictions

---

## 🎯 Core Distinction

### Live Trading Dashboard
- **Shows**: Zeus hourly temperature forecasts throughout the day
- **Purpose**: See what Zeus predicts for each hour (00:00, 01:00, 02:00, etc.)
- **Updates**: Every 15 minutes with new forecast
- **Time Range**: Today + future days (active markets)

### Historical Data Page
- **Should Show**: How Zeus's hourly forecasts evolved over time (same as live dashboard)
- **Purpose**: Analyze past performance, see forecast accuracy hour-by-hour
- **Time Range**: **Only past dates** (not today or tomorrow)
- **Additional**: Show if predictions were correct (outcome known)

---

## 📊 Recommended Approach: Three Linked Graphs

### Graph 1: Zeus Forecast Evolution vs METAR Actual (Hourly)

**What it shows**: Same as live dashboard - Zeus hourly temperature forecasts at different snapshot times

**X-Axis**: Time of day (00:00 to 24:00) - full 24-hour day

**Y-Axis**: Temperature (°F)

**Data Lines**:
- **Zeus Latest** (solid blue) - Most recent snapshot's hourly forecast
- **Zeus Median** (dashed blue) - Median of all snapshots' hourly forecasts
- **METAR Actual** (orange dots/line) - Actual observed temperatures

**Daily High Prediction Panel** (right side, like live dashboard):
- Latest predicted daily high
- Update time
- Recent updates with changes
- **Actual daily high** (from METAR) - **NEW for historical**
- **Accuracy indicator** - ✅ Correct / ❌ Incorrect (if resolved)
- **Error** - Difference between predicted and actual

**Key Difference from Live Dashboard**:
- ✅ Shows **actual daily high** (known for past dates)
- ✅ Shows **accuracy** (was Zeus correct?)
- ✅ Shows **error** (how far off was Zeus?)

**Example**:
```
Daily High Prediction
─────────────────────
Latest: 44.6°F
Updated: 09:18

Actual: 44.8°F ✅
Error: +0.2°F (0.4%)

Recent Updates:
09:18 → 44.6°F
10:51 → 44.8°F (+0.2°F)
11:50 → 44.2°F (-0.6°F)

Drift (last 2h): ±0.8°F
```

---

### Graph 2: Polymarket Implied Probabilities Over Time

**What it shows**: How market probabilities changed over time (markets open days in advance)

**X-Axis**: **Time** (not just 00:00-24:00, but actual timeline - could span multiple days)

**Y-Axis**: Probability (0-100%)

**Data Lines**: One line per bracket showing probability evolution

**Key Points**:
- Markets open **1-2 days before** the event
- X-axis should show **actual timeline** (e.g., Nov 16 00:00 → Nov 18 00:00)
- Shows how market sentiment changed as event approached
- Can see if market moved toward or away from Zeus prediction

**Example Timeline**:
```
Nov 16 00:00  →  Market opens, 58-59°F at 5%
Nov 16 12:00  →  Market moves, 58-59°F at 8%
Nov 17 00:00  →  Market stabilizes, 58-59°F at 6%
Nov 17 12:00  →  Event day, 58-59°F at 5%
Nov 18 00:00  →  Market closes, resolves
```

**Why Different X-Axis?**
- Markets are open longer than 24 hours
- Need to see full market lifecycle
- Shows how probabilities evolved leading up to event

---

### Graph 3: Trading Decisions Timeline

**What it shows**: When trades were placed (markets open days before event)

**X-Axis**: **Actual timeline** (market open → close, spans multiple days) - **same as Graph 2**

**Y-Axis**: Trade size ($) or edge (%)

**Data Points**: 
- Each trade as a marker
- Shows bracket, size, edge, outcome (if resolved)
- Plotted at actual trade timestamp (could be days before event)

**Key Points**:
- Uses same X-axis as Graph 2 (actual timeline)
- Shows trades placed throughout market lifecycle (not just event day)
- Can see if trades were placed early/late in market lifecycle
- Shows outcome (win/loss) if resolved
- **Linked with Graph 2** (hover on one affects the other)

---

## 🔗 Graph Linking Strategy

### Recommended: Two Time Scales with Linked Pairs

**Graph 1**: Independent X-axis (time of day: 00:00-24:00)
- Shows hourly forecast evolution for event day
- Not linked to other graphs (different time scale)
- Focus: Forecast accuracy during the event day

**Graph 2 & 3**: Share same X-axis (actual timeline: market open → close)
- **Linked hover/tooltip** - hover on one affects the other
- Correlate: "At Nov 16 12:00, market probability was X%, and we placed a trade"
- Shows full market lifecycle (markets open days before event)

**Visual Layout**:
```
┌─────────────────────────────────────────────────────────┐
│ Graph 1: Zeus Forecast Evolution (Hourly)               │
│ X-Axis: 00:00 ──────────────────────────────── 24:00    │
│ [Independent - shows event day forecast]                │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Graph 2: Polymarket Probabilities Over Time             │
│ X-Axis: Nov 16 00:00 ──────────────────── Nov 18 00:00  │
│ [Linked hover with Graph 3]                             │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Graph 3: Trading Decisions Timeline                     │
│ X-Axis: Nov 16 00:00 ──────────────────── Nov 18 00:00  │
│ [Linked hover with Graph 2]                             │
└─────────────────────────────────────────────────────────┘
```

---

## ✅ Recommended: Two Time Scales with Linked Pairs

### Why This Works Best

1. **Graph 1**: Event day focus
   - Shows hourly forecast evolution during the event day
   - Independent (different time scale)
   - Focus: Forecast accuracy hour-by-hour

2. **Graph 2 & 3**: Market lifecycle correlation
   - Both use actual timeline (markets open days before event)
   - **Linked hover** - hover on one affects the other
   - Can see: "At Nov 16 12:00, market probability was X%, we traded bracket Y"
   - Shows full market lifecycle (when markets opened, when we traded, when they closed)

3. **User Understanding**:
   - Clear separation: "Event day forecast" vs "Market lifecycle"
   - Graphs 2 & 3 linked for easy correlation
   - Can see: "Did we trade early or late in market lifecycle?"
   - Can see: "How did market probabilities change after we traded?"

---

## 📋 Implementation Details

### Graph 1: Zeus Forecast Evolution (Hourly)

**Data Structure**:
```typescript
interface ZeusSnapshot {
  fetch_time_utc: string;
  forecast_for_local_day: string;
  timeseries: Array<{
    time_utc: string;
    temp_F: number;  // Hourly temperature
  }>;
  predicted_high_F: number;  // Daily high from this snapshot
}

// For each snapshot, extract hourly temps
const zeusLatest = latestSnapshot.timeseries.map(hour => ({
  hour: extractHour(hour.time_utc),  // 00, 01, 02, ..., 23
  temp_F: hour.temp_F
}));

// For median, calculate median temp for each hour across all snapshots
const zeusMedian = calculateMedianByHour(allSnapshots);
```

**Display**:
- Multiple Zeus lines (latest, 15min ago, 30min ago, median)
- METAR actual temperatures
- Daily High Prediction panel with actual outcome

### Graph 2: Polymarket Probabilities Over Time

**Data Structure**:
```typescript
interface PolymarketSnapshot {
  fetch_time_utc: string;  // Could be days before event
  event_day: string;
  markets: Array<{
    bracket: string;
    mid_price: number;  // Probability
  }>;
}

// Group by bracket, show probability evolution
const bracketProbs = groupByBracket(polymarketSnapshots);
// X-axis: actual timestamp (could span multiple days)
// Y-axis: probability (0-100%)
```

**Display**:
- One line per bracket
- X-axis shows actual timeline (market open → close)
- Can span 2-3 days before event

### Graph 3: Trading Decisions Timeline

**Data Structure**:
```typescript
interface Trade {
  timestamp: string;  // Trade time (actual timestamp, could be days before event)
  bracket_name: string;
  size_usd: number;
  edge_pct: number;
  outcome?: 'win' | 'loss' | 'pending';
}

// Use actual timestamp for X-axis (same as Graph 2)
const tradeTime = new Date(trade.timestamp);  // Actual date/time
```

**Display**:
- Markers at actual trade timestamps
- Show bracket, size, edge
- Color-code by outcome (green=win, red=loss, gray=pending)
- X-axis matches Graph 2 (actual timeline)

---

## 🎨 Visual Design

### Graph 1: Independent Hover

**When hovering over Graph 1**:
- Show vertical line at that time of day
- Show tooltip with:
  - Zeus temp at that hour
  - METAR actual at that hour
  - Time of day (e.g., "12:15")
- No cross-graph linking (different time scale)

### Graph 2 & 3: Linked Hover

**When hovering over Graph 2**:
- Show vertical line at that timestamp
- Show tooltip with:
  - Market probabilities for all brackets at that time
  - Timestamp (actual date/time, e.g., "Nov 16 12:00")
  - Any trades placed at that time (from Graph 3)
- Highlight corresponding point on Graph 3

**When hovering over Graph 3**:
- Show vertical line at that timestamp
- Show tooltip with:
  - Trade details (bracket, size, edge, outcome)
  - Market probability at that time (from Graph 2)
  - Timestamp (actual date/time, e.g., "Nov 16 12:00")
- Highlight corresponding point on Graph 2

**Key Benefit**: Can see exactly when trades were placed relative to market probability changes

---

## 📅 Date Selection

### Historical Page Scope

**Should Show**:
- ✅ **Only past dates** (dates before today)
- ✅ Dates where event has occurred
- ✅ Dates where we have complete data (Zeus, Polymarket, METAR)

**Should NOT Show**:
- ❌ Today (use Live Dashboard for that)
- ❌ Tomorrow (use Live Dashboard for that)
- ❌ Future dates (no data yet)

**Date Picker**:
- Default to most recent past date with data
- Allow selection of any past date
- Show warning if data is incomplete
- Disable future dates

---

## 🔍 What Users Can Analyze

### 1. Forecast Accuracy (Graph 1)
- **Hour-by-hour accuracy**: How close was Zeus to actual temps?
- **Daily high accuracy**: Was Zeus's predicted high correct?
- **Forecast stability**: Did Zeus change its mind?
- **Timing**: When did Zeus get most accurate?

### 2. Market Evolution (Graph 2)
- **Market sentiment**: What did the market think?
- **Probability shifts**: Did market move toward/away from Zeus?
- **Market efficiency**: Did market price correctly?
- **Timing**: When did market probabilities stabilize?

### 3. Trading Performance (Graph 3)
- **Trade timing**: When did we trade?
- **Trade selection**: Which brackets did we pick?
- **Outcomes**: Which trades won/lost?
- **Correlation**: Did we trade when Zeus was accurate?

### 4. Cross-Correlation
- **Zeus vs Market**: Did we trade when Zeus disagreed with market?
- **Timing**: Did we trade at optimal times?
- **Accuracy**: Were our trades based on accurate forecasts?

---

## ✅ Summary: Recommended Approach

### Graph 1: Zeus Forecast Evolution (Hourly)
- **X-Axis**: Time of day (00:00-24:00)
- **Shows**: Zeus hourly forecasts (like live dashboard)
- **Plus**: Actual daily high, accuracy indicator, error
- **Independent**: Different time scale (focuses on event day)

### Graph 2: Polymarket Probabilities Over Time
- **X-Axis**: Actual timeline (market open → close, could span days)
- **Shows**: How market probabilities evolved
- **Linked with**: Graph 3 (same X-axis, hover correlation)

### Graph 3: Trading Decisions Timeline
- **X-Axis**: Actual timeline (market open → close, could span days) - **same as Graph 2**
- **Shows**: When trades were placed (actual timestamps)
- **Linked with**: Graph 2 (same X-axis, hover correlation)

### Key Features
- ✅ Historical page shows **only past dates**
- ✅ Graph 1 shows **hourly forecast evolution** (like live dashboard)
- ✅ Daily High Prediction panel shows **actual outcome** and **accuracy**
- ✅ Graphs 2 & 3 are **linked** (same X-axis, hover on one affects the other)
- ✅ Graphs 2 & 3 show **full market lifecycle** (markets open days before event)
- ✅ Can correlate: "When we traded, what was the market probability?"

---

## 🎯 Benefits of This Approach

1. **Consistency**: Graph 1 matches live dashboard format (familiar to users)
2. **Completeness**: Shows hourly accuracy, not just daily high
3. **Context**: Graphs 2 & 3 show full market lifecycle (markets open days in advance)
4. **Correlation**: Graphs 2 & 3 linked for easy analysis - see exactly when trades were placed relative to market changes
5. **Clarity**: Clear separation between "event day forecast" and "market lifecycle"
6. **Trading Analysis**: Can see if trades were placed early/late in market lifecycle, and how market reacted

---

**Last Updated**: November 18, 2025

