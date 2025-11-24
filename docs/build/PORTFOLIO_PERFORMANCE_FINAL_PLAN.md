# Portfolio & Performance: Final Implementation Plan

**Date**: November 18, 2025  
**Purpose**: Complete implementation plan for Portfolio (Macro) and Performance (Micro) pages  
**Structure**: Portfolio = System-wide | Performance = Day-by-day drill-down

---

## 🎯 Final Structure

### **Portfolio Page (Macro)**
**Purpose**: "How are we doing overall?"

**Shows**:
- Account balances
- Total P&L, Win Rate, ROI
- System-wide forecast accuracy
- System-wide timing analysis
- System-wide station performance
- System-wide loss analysis
- Trade history table

### **Performance Page (Micro)**
**Purpose**: "What happened on this specific day?"

**Shows**:
- Day-by-day detailed graphs
- Forecast evolution for specific day
- Market dynamics for specific day
- Trading decisions for specific day
- Post-trade analysis for specific day

---

## 📊 Portfolio Page (Macro) - Implementation

### **Page Structure**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Portfolio (Macro)                                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ Mode: [Paper ▼] [Live ▼]                                                    │
│                                                                              │
│ ┌──────────────────────────────────────────────────────────────────────┐  │
│ │ Section 1: Account Status                                            │  │
│ │                                                                      │  │
│ │ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐              │  │
│ │ │ Account  │ │ Total    │ │ Win Rate │ │ ROI      │              │  │
│ │ │ Balance  │ │ P&L      │ │          │ │          │              │  │
│ │ │          │ │          │ │          │ │          │              │  │
│ │ │ $10,240  │ │ +$8,240  │ │ 63.12%   │ │ 17.61%   │              │  │
│ │ └──────────┘ └──────────┘ └──────────┘ └──────────┘              │  │
│ │                                                                      │  │
│ │ Period: [All Time ▼] [Last 30 Days ▼] [Last 7 Days ▼]            │  │
│ └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│ ┌──────────────────────────────────────────────────────────────────────┐  │
│ │ Section 2: System-Wide Forecast Accuracy                            │  │
│ │                                                                      │  │
│ │ MAE: 1.2°F  |  RMSE: 1.8°F  |  Stability: ±0.8°F                   │  │
│ │                                                                      │  │
│ │ [Chart: Forecast Accuracy by Age]                                   │  │
│ │ 0-6h: 0.9°F | 6-12h: 1.2°F | 12-24h: 1.6°F | 24h+: 2.1°F          │  │
│ │                                                                      │  │
│ │ Answers: "Was Zeus accurate overall?"                               │  │
│ └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│ ┌──────────────────────────────────────────────────────────────────────┐  │
│ │ Section 3: System-Wide Timing Analysis                              │  │
│ │                                                                      │  │
│ │ [Chart: P&L by Trade Timing]                                        │  │
│ │ 0-12h: $200 | 12-24h: $350 | 24-36h: $500 | 36h+: $300            │  │
│ │                                                                      │  │
│ │ Answers: "When should we trade (overall)?"                          │  │
│ └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│ ┌──────────────────────────────────────────────────────────────────────┐  │
│ │ Section 4: System-Wide Station Performance                          │  │
│ │                                                                      │  │
│ │ [Chart: P&L by Station]                                             │  │
│ │ EGLC: $4,200 | KLGA: $2,340 | KORD: $1,700                         │  │
│ │                                                                      │  │
│ │ [Chart: P&L by Bracket (Top 10)]                                    │  │
│ │                                                                      │  │
│ │ Answers: "Which stations/brackets work best (overall)?"            │  │
│ └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│ ┌──────────────────────────────────────────────────────────────────────┐  │
│ │ Section 5: System-Wide Loss Analysis                                │  │
│ │                                                                      │  │
│ │ • Top 5 Loss Events                                                 │  │
│ │ • Forecast Error vs. P&L Correlation                                │  │
│ │ • Common Loss Patterns                                               │  │
│ │                                                                      │  │
│ │ Answers: "Why did we lose when we lost (overall)?"                 │  │
│ └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│ ┌──────────────────────────────────────────────────────────────────────┐  │
│ │ Section 6: Trade History                                            │  │
│ │                                                                      │  │
│ │ [Filterable, searchable trade history table]                        │  │
│ │ [Click row → Navigate to Performance page for that day]            │  │
│ └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│ [Export Data]                                                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Performance Page (Micro) - Implementation

### **Page Structure**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Performance (Micro)                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ Station: [EGLC ▼]  Date: [2025-11-16 ▼]  [← Back to Portfolio]            │
│                                                                              │
│ ┌──────────────────────────────────────────────────────────────────────┐  │
│ │ Quick Summary for This Day                                           │  │
│ │                                                                      │  │
│ │ Forecast Accuracy: 0.2°F error ✅                                   │  │
│ │ Trades: 3 | Wins: 2 | Losses: 1 | P&L: +$125.50                    │  │
│ └──────────────────────────────────────────────────────────────────────┘  │
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

---

## 🔧 Backend Implementation Stages

### **Stage 1: Portfolio Page Backend (Week 1)**

#### **1.1 Forecast Accuracy Service (System-Wide)**
**File**: `backend/api/services/forecast_accuracy_service.py`

**Metrics**:
- Overall MAE, RMSE, Correlation
- MAE by forecast age (0-6h, 6-12h, 12-24h, 24h+)
- Forecast stability (volatility)

**Endpoint**: `GET /api/portfolio/forecast-accuracy`

**Time**: 4-5 hours

---

#### **1.2 Timing Analysis Service (System-Wide)**
**File**: `backend/api/services/timing_analysis_service.py`

**Metrics**:
- P&L by trade timing (0-12h, 12-24h, 24-36h, 36h+)
- Win rate by trade timing
- Average edge by trade timing

**Endpoint**: `GET /api/portfolio/timing-analysis`

**Time**: 3-4 hours

---

#### **1.3 Station Performance Service (System-Wide)**
**File**: `backend/api/services/station_performance_service.py`

**Metrics**:
- P&L by station (all stations)
- P&L by bracket (top 10-20 brackets)
- Win rate by station/bracket

**Endpoint**: `GET /api/portfolio/station-performance`

**Time**: 3-4 hours

---

#### **1.4 Loss Analysis Service (System-Wide)**
**File**: `backend/api/services/loss_analysis_service.py`

**Metrics**:
- Top 5-10 loss events (with context)
- Forecast error vs. P&L correlation
- Common loss patterns

**Endpoint**: `GET /api/portfolio/loss-analysis`

**Time**: 4-5 hours

---

### **Stage 2: Performance Page Backend (Week 1-2)**

#### **2.1 Historical Summary Endpoint (Day-by-Day)**
**File**: `backend/api/routes/performance.py`

**Endpoint**: `GET /api/performance/historical/{station_code}/{date}`

**Returns**:
- Summary metrics for that day
- Forecast accuracy for that day
- Trade outcomes for that day
- Post-trade analysis

**Time**: 3-4 hours

---

#### **2.2 Post-Trade Analysis Service**
**File**: `backend/api/services/post_trade_analysis_service.py`

**Metrics**:
- Market movement after trade
- Zeus forecast changes after trade
- Edge evolution after trade

**Endpoint**: `GET /api/performance/post-trade-analysis/{station_code}/{date}`

**Time**: 3-4 hours

---

### **Stage 3: Shared Services (Week 2)**

#### **3.1 Export Service**
**File**: `backend/api/services/export_service.py`

**Formats**: JSON, Prompt-Ready Text

**Endpoints**:
- `GET /api/portfolio/export`
- `GET /api/performance/export`

**Time**: 2-3 hours

---

## 🎨 Frontend Implementation Stages

### **Stage 1: Portfolio Page Frontend (Week 2-3)**

#### **1.1 Page Structure & Navigation**
**File**: `frontend/src/pages/Portfolio/PortfolioPage.tsx`

**Components**:
- Mode toggle (Paper/Live)
- Period selector
- Section layout

**Time**: 2-3 hours

---

#### **1.2 Account Status Section**
**File**: `frontend/src/pages/Portfolio/AccountStatus.tsx`

**Components**:
- Account balance card
- Total P&L card
- Win Rate card
- ROI card
- Period selector

**Time**: 3-4 hours

---

#### **1.3 Forecast Accuracy Section**
**File**: `frontend/src/pages/Portfolio/ForecastAccuracy.tsx`

**Components**:
- MAE, RMSE, Stability metrics
- Forecast Accuracy by Age chart

**Time**: 3-4 hours

---

#### **1.4 Timing Analysis Section**
**File**: `frontend/src/pages/Portfolio/TimingAnalysis.tsx`

**Components**:
- P&L by Trade Timing chart

**Time**: 2-3 hours

---

#### **1.5 Station Performance Section**
**File**: `frontend/src/pages/Portfolio/StationPerformance.tsx`

**Components**:
- P&L by Station chart
- P&L by Bracket chart

**Time**: 3-4 hours

---

#### **1.6 Loss Analysis Section**
**File**: `frontend/src/pages/Portfolio/LossAnalysis.tsx`

**Components**:
- Top Loss Events list
- Forecast Error vs. P&L correlation chart
- Common Loss Patterns

**Time**: 4-5 hours

---

#### **1.7 Trade History Table**
**File**: `frontend/src/pages/Portfolio/TradeHistory.tsx`

**Components**:
- Filterable trade history table
- Click row → Navigate to Performance page

**Time**: 4-5 hours

---

### **Stage 2: Performance Page Frontend (Week 3-4)**

#### **2.1 Page Structure & Navigation**
**File**: `frontend/src/pages/Performance/PerformancePage.tsx`

**Components**:
- Station/Date selector
- Back to Portfolio button
- Quick summary panel

**Time**: 2-3 hours

---

#### **2.2 Enhance Existing Graphs**
**File**: `frontend/src/pages/Performance/HistoricalGraphs.tsx`

**Enhancements**:
- Add actual daily high to Daily High Panel
- Add forecast stability indicator
- Ensure Graphs 2 & 3 are linked (hover correlation)

**Time**: 3-4 hours

---

#### **2.3 Post-Trade Analysis Component**
**File**: `frontend/src/pages/Performance/PostTradeAnalysis.tsx`

**Components**:
- Post-trade market movement
- Post-trade Zeus changes
- Trade outcome analysis

**Time**: 3-4 hours

---

#### **2.4 Day Summary Component**
**File**: `frontend/src/pages/Performance/DaySummary.tsx`

**Components**:
- Forecast accuracy for that day
- Trade outcomes summary
- Key insights

**Time**: 2-3 hours

---

### **Stage 3: Integration & Polish (Week 4)**

#### **3.1 Navigation Integration**
- Add Portfolio to main navigation
- Add Performance to main navigation
- Implement drill-down from Portfolio → Performance

**Time**: 2-3 hours

---

#### **3.2 Export Functionality**
- Add export buttons to both pages
- Implement JSON and Text export

**Time**: 2-3 hours

---

#### **3.3 Testing & Bug Fixes**
- Test all components
- Fix bugs
- UI polish

**Time**: 4-5 hours

---

## 📋 Implementation Checklist

### **Backend**

#### **Portfolio Page Backend**
- [ ] Forecast Accuracy Service (system-wide)
- [ ] Timing Analysis Service (system-wide)
- [ ] Station Performance Service (system-wide)
- [ ] Loss Analysis Service (system-wide)
- [ ] Export Service

#### **Performance Page Backend**
- [ ] Historical Summary Endpoint (day-by-day)
- [ ] Post-Trade Analysis Service
- [ ] Export Service

---

### **Frontend**

#### **Portfolio Page Frontend**
- [ ] Page structure & navigation
- [ ] Account Status section
- [ ] Forecast Accuracy section
- [ ] Timing Analysis section
- [ ] Station Performance section
- [ ] Loss Analysis section
- [ ] Trade History table

#### **Performance Page Frontend**
- [ ] Page structure & navigation
- [ ] Enhance existing graphs
- [ ] Post-Trade Analysis component
- [ ] Day Summary component

#### **Integration**
- [ ] Navigation integration
- [ ] Export functionality
- [ ] Testing & bug fixes

---

## 📅 Timeline

### **Week 1: Backend - Portfolio**
- Day 1-2: Forecast Accuracy Service
- Day 3: Timing Analysis Service
- Day 4: Station Performance Service
- Day 5: Loss Analysis Service

### **Week 2: Backend - Performance + Shared**
- Day 1-2: Historical Summary Endpoint
- Day 3: Post-Trade Analysis Service
- Day 4-5: Export Service

### **Week 3: Frontend - Portfolio**
- Day 1: Page structure & Account Status
- Day 2: Forecast Accuracy & Timing Analysis
- Day 3: Station Performance & Loss Analysis
- Day 4-5: Trade History table

### **Week 4: Frontend - Performance + Integration**
- Day 1: Performance page structure
- Day 2: Enhance existing graphs
- Day 3: Post-Trade Analysis
- Day 4: Navigation integration & Export
- Day 5: Testing & bug fixes

**Total**: 4 weeks

---

## 🎯 Success Criteria

### **Portfolio Page**
- ✅ Shows account balances and basic metrics
- ✅ Shows system-wide forecast accuracy
- ✅ Shows system-wide timing analysis
- ✅ Shows system-wide station performance
- ✅ Shows system-wide loss analysis
- ✅ Trade history table with drill-down to Performance

### **Performance Page**
- ✅ Shows day-by-day detailed graphs
- ✅ Shows forecast evolution for specific day
- ✅ Shows market dynamics for specific day
- ✅ Shows trading decisions for specific day
- ✅ Shows post-trade analysis
- ✅ Can navigate back to Portfolio

---

## 🔗 API Endpoints Summary

### **Portfolio Endpoints**
- `GET /api/portfolio/forecast-accuracy` - System-wide forecast accuracy
- `GET /api/portfolio/timing-analysis` - System-wide timing analysis
- `GET /api/portfolio/station-performance` - System-wide station performance
- `GET /api/portfolio/loss-analysis` - System-wide loss analysis
- `GET /api/portfolio/export` - Export portfolio data

### **Performance Endpoints**
- `GET /api/performance/historical/{station_code}/{date}` - Day-by-day summary
- `GET /api/performance/post-trade-analysis/{station_code}/{date}` - Post-trade analysis
- `GET /api/performance/export` - Export performance data

### **Shared Endpoints** (Already Exist)
- `GET /api/performance/pnl` - P&L data (used by Portfolio)
- `GET /api/performance/metrics` - Performance metrics (used by Portfolio)
- `GET /api/trades/history` - Trade history (used by Portfolio)
- `GET /api/snapshots/*` - Snapshot data (used by Performance)

---

## 🚀 Key Principles

1. **Portfolio = Macro**: System-wide account status and analysis
2. **Performance = Micro**: Day-by-day detailed drill-down
3. **Clear Navigation**: Portfolio → Performance (drill-down)
4. **No Overlap**: Each page has distinct purpose
5. **User-Centric**: Matches user mental model

---

**Last Updated**: November 18, 2025

