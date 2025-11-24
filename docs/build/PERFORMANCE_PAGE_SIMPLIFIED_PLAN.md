# Performance Page: Simplified Implementation Plan

**Purpose**: Streamlined plan focused on answering 4 essential questions  
**Date**: November 18, 2025  
**Approach**: Two-level structure (Macro + Micro), no complex tabs

---

## 🎯 The 4 Essential Questions

1. **Was Zeus accurate?**
2. **Did we trade at the right time?**
3. **Which stations/brackets work best?**
4. **Why did we lose when we lost?**

**That's it. Everything else is noise.**

---

## 📊 Two-Level Structure

### **Level 1: Macro View** (System-Wide)
One page showing overall performance and patterns.

### **Level 2: Micro View** (Day-by-Day)
Drill-down for specific days and stations (already mostly implemented).

---

## 🎯 LEVEL 1: Macro View

**Purpose**: System-wide, high-level insight

**One page. No tabs. Keep it simple.**

---

### **A. Forecast Accuracy (Zeus Performance)**

**Why**: Zeus is dynamic and changes all day. We need to understand its accuracy.

**3 Essential Metrics**:

1. **MAE (Mean Absolute Error)**
   - "How many °F off is Zeus on average?"
   - Simple number: `1.2°F`

2. **Accuracy by Forecast Age**
   - Because a forecast 2 hours before event ≠ 22 hours before
   - **Buckets**: 0-6h, 6-12h, 12-24h, 24h+
   - **Chart**: Bar chart showing MAE by bucket

3. **Forecast Stability**
   - "How much does Zeus change its mind throughout the day?"
   - **Metric**: Hourly forecast volatility (std dev of daily high predictions)
   - **Simple number**: `±0.8°F` (average volatility)

**Visualization**:
- **Card**: MAE, RMSE, Stability
- **Chart**: Accuracy by Forecast Age (bar chart)

---

### **B. Trading Performance** (REMOVED - Portfolio shows this)

**Note**: Basic P&L, Win Rate, and ROI are shown on the Portfolio page.  
Performance page focuses on **analysis**, not basic metrics.

**Removed from Performance**:
- ❌ Total P&L card (Portfolio shows this)
- ❌ Win Rate card (Portfolio shows this)
- ❌ ROI card (Portfolio shows this)
- ❌ Total Trades card (Portfolio shows this)

**Performance shows analysis instead**:
- ✅ P&L by Station (which stations work best)
- ✅ P&L by Timing (when to trade)
- ✅ P&L Over Time (trends, not balance)

---

### **C. Timing Analysis**

**Why**: Zeus and Polymarket evolve dynamically. When should we trade?

**Essential Metric**:
- **P&L by Trade Timing** (hours before event)
- **Buckets**: 0-12h, 12-24h, 24-36h, 36h+

**Visualization**:
- **Chart**: Bar chart showing average P&L by timing bucket
- **Insight**: Immediately shows optimal window

---

### **D. Station/Bracket Performance**

**Why**: Different stations behave differently.

**Essential Metrics**:
- P&L by station
- Win rate by station
- P&L by bracket (top 5-10 brackets)

**Visualization**:
- **Chart**: Bar chart showing P&L by station
- **Chart**: Bar chart showing P&L by bracket (top performers)

---

### **Macro View Layout**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Performance > Overview                                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ Period: [Last 30 Days ▼]  Stations: [All ▼]  [Apply]                       │
│                                                                              │
│ ┌──────────────────────────────────────────────────────────────────────┐  │
│ │ Forecast Accuracy                                                    │  │
│ │                                                                      │  │
│ │ MAE: 1.2°F  |  RMSE: 1.8°F  |  Stability: ±0.8°F                   │  │
│ │                                                                      │  │
│ │ Answers: "Was Zeus accurate?"                                       │  │
│ └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│ ┌──────────────────────────────────────────────────────────────────────┐  │
│ │ Chart 1: Forecast Accuracy by Age                                   │  │
│ │ [Bar chart: MAE by forecast age bucket]                             │  │
│ │ 0-6h: 0.9°F | 6-12h: 1.2°F | 12-24h: 1.6°F | 24h+: 2.1°F          │  │
│ └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│ ┌──────────────────────────────────────────────────────────────────────┐  │
│ │ Chart 2: P&L by Trade Timing                                        │  │
│ │ [Bar chart: Average P&L by timing bucket]                           │  │
│ │ 0-12h: $200 | 12-24h: $350 | 24-36h: $500 | 36h+: $300            │  │
│ │                                                                      │  │
│ │ Answers: "Did we trade at the right time?"                          │  │
│ └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│ ┌──────────────────────────────────────────────────────────────────────┐  │
│ │ Chart 3: P&L by Station                                             │  │
│ │ [Bar chart: P&L by station]                                         │  │
│ │ EGLC: $4,200 | KLGA: $2,340 | KORD: $1,700                         │  │
│ │                                                                      │  │
│ │ Answers: "Which stations work best?"                                │  │
│ └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│ ┌──────────────────────────────────────────────────────────────────────┐  │
│ │ Chart 4: P&L Over Time (Trend Analysis)                             │  │
│ │ [Line chart: Cumulative P&L trend]                                  │  │
│ │ Shows: Performance trends, not account balance                      │  │
│ └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│ ┌──────────────────────────────────────────────────────────────────────┐  │
│ │ Loss Analysis                                                        │  │
│ │                                                                      │  │
│ │ • Top 5 Loss Events                                                 │  │
│ │ • Forecast Error vs. P&L Correlation                                │  │
│ │ • Common Loss Patterns                                               │  │
│ │                                                                      │  │
│ │ Answers: "Why did we lose when we lost?"                            │  │
│ └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│ [Export Data]                                                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Note**: No basic P&L/Win Rate/ROI cards - Portfolio page shows these.  
Performance focuses on **analysis**, not account status.

**That's it. 1 card. 4 charts. 1 analysis section. One page.**

---

## 🎯 LEVEL 2: Micro View

**Purpose**: Drill-down for each Day + Station

**Already mostly implemented. Just refine it.**

---

### **Micro View Must Answer**:

1. **What did Zeus predict throughout the day?**
   - Zeus is dynamic - visualize evolution clearly

2. **How did Polymarket probabilities move?**
   - Polymarket is dynamic too

3. **When did Hermes trade, and were trades good?**
   - Show timing and post-trade evolution

4. **Zeus Daily High Panel**
   - Latest predicted high
   - Actual METAR high
   - Forecast error
   - Recent prediction drift

---

### **Micro View Layout**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Performance > Historical                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ Station: [EGLC ▼]  Date: [2025-11-16 ▼]                                    │
│                                                                              │
│ ┌──────────────────────────────────────────────────────────────────────┐  │
│ │ Graph 1: Zeus Forecast Evolution vs METAR Actual                    │  │
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
│ │  │ Daily High Prediction                                      │    │  │
│ │  │ Latest: 44.6°F                                             │    │  │
│ │  │ Actual: 44.8°F ✅                                          │    │  │
│ │  │ Error: +0.2°F (0.4%)                                       │    │  │
│ │  │ Stability: ±0.8°F                                          │    │  │
│ │  │                                                             │    │  │
│ │  │ Recent Updates:                                            │    │  │
│ │  │ 09:18 → 44.6°F                                             │    │  │
│ │  │ 10:51 → 44.8°F (+0.2°F)                                    │    │  │
│ │  └────────────────────────────────────────────────────────────┘    │  │
│ └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│ ┌──────────────────────────────────────────────────────────────────────┐  │
│ │ Graph 2: Polymarket Probabilities Over Time                         │  │
│ │ [Probability lines for each bracket]                                │  │
│ │ Timeline: Market open → close (actual timeline)                     │  │
│ └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│ ┌──────────────────────────────────────────────────────────────────────┐  │
│ │ Graph 3: Trading Decisions Timeline                                 │  │
│ │ [Trade markers with outcomes]                                       │  │
│ │ Timeline: Market open → close (actual timeline)                     │  │
│ │                                                                      │  │
│ │ Post-Trade Analysis:                                                │  │
│ │ • Trade 1 (12:15): Market moved +2% in our favor                    │  │
│ │ • Trade 2 (14:30): Zeus changed -1°F against us                     │  │
│ └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│ Summary: 3 trades | 2 wins, 1 loss | +$125.50 P&L                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Graphs 2 & 3 are linked (hover on one affects the other).**

---

## 🚀 Why This Matters

**Your trading decisions depend on just three dynamic forces**:

1. **Zeus forecast trajectory**
2. **Market price trajectory**
3. **Your execution timing**

**The Performance page only needs to show how these interacted in reality.**

**Backtesting** = Hypothetical parameter tuning  
**Performance** = Reality analysis

**Mixing them is a mistake.**

---

## 🎯 Key Distinction from Portfolio

**Portfolio Page** shows:
- Account balances
- Total P&L, Win Rate, ROI (basic metrics)
- Trade history table

**Performance Page** shows:
- Forecast accuracy analysis
- Timing analysis
- Station/bracket performance analysis
- Loss analysis
- Day-by-day detailed analysis

**No overlap**: Portfolio = "What happened?" | Performance = "Why did it happen? How to improve?"

See `PERFORMANCE_VS_PORTFOLIO_CLARIFICATION.md` for full details.

---

## 📋 Implementation Plan

### **Backend: Essential Services**

#### **1. Forecast Accuracy Service**
**Metrics**:
- Overall MAE, RMSE
- MAE by forecast age (4 buckets)
- Forecast stability (volatility)

**Endpoint**: `GET /api/forecast-accuracy/metrics`

**Time**: 3-4 hours

---

#### **2. Loss Analysis Service**
**Metrics**:
- Top 5-10 loss events (with context)
- Forecast error vs. P&L correlation
- Common loss patterns

**Endpoint**: `GET /api/analytics/loss-analysis`

**Time**: 3-4 hours

---

#### **3. Timing Analysis Service**
**Metrics**:
- P&L by trade timing (4 buckets)
- Win rate by trade timing

**Endpoint**: `GET /api/analytics/timing`

**Time**: 3-4 hours

---

#### **4. Station Performance Service** (Analysis-focused)
**Metrics**:
- P&L by station (for analysis, not account status)
- P&L by bracket (top performers)
- Win rate by station/bracket

**Endpoint**: `GET /api/analytics/station-performance`

**Time**: 2-3 hours

---

#### **5. Historical Summary Endpoint**
**Metrics**:
- Summary for specific day/station
- Forecast accuracy for that day
- Trade outcomes
- Post-trade analysis

**Endpoint**: `GET /api/performance/historical/{station_code}/{date}`

**Time**: 2-3 hours

---

#### **6. Export Service**
**Formats**: JSON, Prompt-Ready Text

**Endpoint**: `GET /api/performance/export`

**Time**: 2 hours

---

### **Frontend: Two Pages**

#### **1. Macro View (Overview)**
**Components**:
- 1 Summary Card (Forecast Accuracy only)
- 4 Charts (Forecast Accuracy by Age, P&L by Timing, P&L by Station, P&L Over Time)
- 1 Analysis Section (Loss Analysis)
- Period/Station selectors
- Export button

**Note**: No P&L/Win Rate/ROI cards - Portfolio shows these.

**Time**: 8-10 hours

---

#### **2. Micro View (Historical)**
**Enhancements**:
- Add actual daily high to Daily High Panel
- Add forecast stability indicator
- Add post-trade analysis to Graph 3
- Ensure Graphs 2 & 3 are linked

**Time**: 4-5 hours

---

## ✅ Success Criteria

**We'll know it's complete when we can answer**:

1. ✅ **"Was Zeus accurate?"** → Macro shows MAE, accuracy by age, stability
2. ✅ **"Did we trade at the right time?"** → Macro shows P&L by timing, Micro shows post-trade analysis
3. ✅ **"Which stations/brackets work best?"** → Macro shows P&L by station/bracket
4. ✅ **"Why did we lose when we lost?"** → Micro shows forecast/market evolution and trade timing

---

## 🎯 Key Principles

1. **Answer 4 questions. Nothing more.**
2. **Two levels: Macro (overview) + Micro (drill-down)**
3. **No complex tabs. Keep it simple.**
4. **Focus on dynamic evolution (Zeus + Polymarket)**
5. **Show reality, not hypotheticals**

---

## 📅 Timeline

### **Week 1: Backend**
- Forecast Accuracy Service
- Enhanced Performance Service
- Timing Analysis Service
- Historical Summary Endpoint
- Export Service

### **Week 2: Frontend**
- Macro View (Overview page)
- Micro View enhancements

### **Week 3: Polish & Test**
- Testing
- Bug fixes
- UI polish

**Total**: 3 weeks

---

## 🧠 In One Sentence

**Macro Performance Page** = "Are we trading well?"  
**Micro Performance Page** = "Why did this specific day behave the way it did?"

---

**Last Updated**: November 18, 2025

