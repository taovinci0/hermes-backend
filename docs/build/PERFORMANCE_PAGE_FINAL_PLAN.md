# Performance Page: Final Implementation Plan

**Purpose**: Streamlined, prioritized implementation plan focusing on what's most valuable  
**Date**: November 18, 2025  
**Approach**: Build MVP first, add advanced features later

---

## 🎯 Core Principle

**Focus on actionable insights that directly improve trading decisions.**

Build the essentials first, add advanced analysis later.

---

## 📊 What We Actually Need

### **Essential Questions** (Must Answer)
1. "Was Zeus accurate?" → Forecast accuracy
2. "When should we trade?" → Optimal timing
3. "What went wrong?" → Loss analysis
4. "Which stations/brackets work best?" → Performance by station/bracket

### **Nice-to-Have Questions** (Can Add Later)
- Forecast evolution details
- Market dynamics deep dive
- Advanced correlation analysis
- Strategy optimization tools

---

## 🏗️ MVP Structure

### **Three Views** (Simplified)

1. **Overview** - Quick summary of key metrics
2. **Historical** - Day-by-day detailed view (already exists, needs enhancements)
3. **Analytics** - Focused analysis (3 essential tabs, not 5)

---

## 🔧 Backend/API: Essential Services Only

### **Stage 1: Core Metrics** (Week 1)

**Goal**: Get basic performance metrics working

#### 1.1 Forecast Accuracy Service
**File**: `backend/api/services/forecast_accuracy_service.py`

**Essential Metrics Only**:
- Overall MAE, RMSE, Correlation
- Accuracy by station
- Accuracy by forecast age (0-6h, 6-12h, 12-24h, 24h+)

**Skip for MVP**:
- Detailed forecast evolution analysis
- Forecast volatility calculations
- Convergence analysis

**Endpoint**: `GET /api/forecast-accuracy/metrics`

**Time**: 3-4 hours

---

#### 1.2 Enhanced Performance Service
**File**: `backend/api/services/performance_service.py` (enhance existing)

**Add**:
- P&L by station
- P&L by bracket
- Win rate by station/bracket

**Endpoint**: `GET /api/performance/metrics` (already exists, enhance)

**Time**: 2 hours

---

#### 1.3 Timing Analysis Service
**File**: `backend/api/services/timing_analysis_service.py`

**Essential Metrics Only**:
- P&L by trade time (hours before event: 0-12h, 12-24h, 24-36h, 36h+)
- Win rate by trade time
- Average edge by trade time

**Skip for MVP**:
- Detailed edge decay analysis
- Market efficiency calculations
- Opportunity cost analysis

**Endpoint**: `GET /api/analytics/timing`

**Time**: 3-4 hours

---

### **Stage 2: Risk Analysis** (Week 1-2)

**Goal**: Understand what causes losses

#### 2.1 Risk Analysis Service
**File**: `backend/api/services/risk_analysis_service.py`

**Essential Metrics Only**:
- Loss patterns (forecast error vs. P&L)
- Large loss events (top 10 losses with context)
- Edge vs. Outcome (do larger edges = better outcomes?)

**Skip for MVP**:
- Detailed volatility analysis
- Dynamic risk factors
- Advanced correlation matrices

**Endpoint**: `GET /api/analytics/risk`

**Time**: 3-4 hours

---

### **Stage 3: Historical Enhancement** (Week 2)

**Goal**: Enhance existing Historical view with actual outcomes

#### 3.1 Historical Summary Endpoint
**File**: `backend/api/routes/performance.py`

**Endpoint**: `GET /api/performance/historical/{station_code}/{date}`

**Returns**:
- Summary metrics for that day
- Forecast accuracy (predicted vs. actual)
- Trade outcomes
- Key insights (3-5 bullet points)

**Time**: 2-3 hours

---

### **Stage 4: Export** (Week 2)

**Goal**: Export data for LLM analysis

#### 4.1 Export Service
**File**: `backend/api/services/export_service.py`

**Formats**:
- JSON (structured)
- Prompt-Ready Text (for LLM)

**Skip for MVP**:
- CSV export
- Markdown reports

**Endpoint**: `GET /api/performance/export`

**Time**: 2-3 hours

---

## 🎨 Frontend: Essential Components Only

### **Stage 1: Navigation & Overview** (Week 2-3)

#### 1.1 Navigation Setup
- Add "Performance" dropdown to main nav
- Create Performance page layout
- Set up routing

**Time**: 2 hours

---

#### 1.2 Overview Page
**File**: `frontend/src/pages/Performance/Overview/OverviewPage.tsx`

**Essential Components**:
- **Summary Cards** (4 cards):
  - Forecast Accuracy (MAE, RMSE)
  - Trading Performance (P&L, ROI)
  - Win Rate
  - Total Trades

- **Station Comparison** (simple bar chart):
  - ROI by station
  - Clickable to drill down

- **P&L Over Time** (line chart):
  - Cumulative P&L
  - Simple, clear

**Skip for MVP**:
- Forecast accuracy over time chart
- Top performing brackets list
- Multiple time series charts

**Time**: 6-8 hours

---

### **Stage 2: Historical Enhancements** (Week 3)

**Goal**: Enhance existing Historical view

#### 2.1 Enhance Daily High Panel
- Add actual daily high
- Add accuracy indicator (✅/❌)
- Add error calculation

**Time**: 2 hours

#### 2.2 Ensure Graph Linking
- Verify Graphs 2 & 3 are linked (hover)
- Ensure both use actual timeline

**Time**: 1-2 hours

---

### **Stage 3: Analytics - Essential Tabs Only** (Week 3-4)

**Goal**: Build 3 essential analytics tabs, not 5

#### 3.1 Forecast Accuracy Tab
**File**: `frontend/src/pages/Performance/Analytics/ForecastAccuracy.tsx`

**Essential Charts**:
- Predicted vs. Actual scatter plot
- Accuracy by Forecast Age (bar chart)
- Error Distribution by Station (box plot)

**Skip for MVP**:
- Heatmaps
- Detailed convergence analysis
- Forecast volatility charts

**Time**: 4-5 hours

---

#### 3.2 Timing Analysis Tab
**File**: `frontend/src/pages/Performance/Analytics/TimingAnalysis.tsx`

**Essential Charts**:
- P&L by Trade Time (bar chart)
- Win Rate by Trade Time (line chart)

**Skip for MVP**:
- Edge decay charts
- Market efficiency analysis
- Detailed correlation charts

**Time**: 3-4 hours

---

#### 3.3 Risk Analysis Tab
**File**: `frontend/src/pages/Performance/Analytics/RiskAnalysis.tsx`

**Essential Charts**:
- Loss Patterns (scatter: Forecast Error vs. P&L)
- Large Loss Events (simple list with details)
- Edge vs. Outcome (box plot)

**Skip for MVP**:
- Detailed volatility analysis
- Market dynamics
- Advanced risk factors

**Time**: 4-5 hours

---

### **Stage 4: Export UI** (Week 4)

#### 4.1 Export Modal
**File**: `frontend/src/pages/Performance/ExportModal.tsx`

**Features**:
- Format selection (JSON, Text)
- Period selection
- Station selection
- Export button

**Time**: 2-3 hours

---

## 📋 MVP Feature List

### ✅ **Must Have** (Build First)

**Overview Page**:
- [x] Summary cards (4 key metrics)
- [x] Station comparison chart
- [x] P&L over time chart
- [x] Period selection

**Historical Page**:
- [x] Three stacked graphs (already exists)
- [x] Daily High panel with actual outcome
- [x] Accuracy indicator
- [x] Graph linking (Graphs 2 & 3)

**Analytics Page**:
- [x] Forecast Accuracy tab (3 charts)
- [x] Timing Analysis tab (2 charts)
- [x] Risk Analysis tab (3 charts)

**Export**:
- [x] JSON export
- [x] Prompt-ready text export

---

### ⏭️ **Can Add Later** (Not MVP)

**Advanced Analytics**:
- Forecast Evolution tab (detailed volatility, convergence)
- Market Dynamics tab (market efficiency, opportunity cost)
- Dynamic Timing tab (optimal entry windows, correlation)
- Bracket Analysis tab (detailed bracket performance)
- Strategy Optimization tab (parameter sensitivity)

**Advanced Features**:
- CSV export
- Markdown reports
- Multiple time series on Overview
- Top performers lists
- Detailed forecast evolution analysis

---

## 🎯 Key Metrics (MVP Only)

### **Forecast Accuracy**
- MAE, RMSE, Correlation
- By station
- By forecast age (4 buckets)

### **Trading Performance**
- Total P&L, ROI, Win Rate
- By station
- By bracket
- Over time

### **Timing**
- P&L by trade time (4 buckets)
- Win rate by trade time

### **Risk**
- Forecast error vs. P&L
- Large loss events
- Edge vs. Outcome

---

## 📅 Streamlined Timeline

### **Week 1: Backend Core**
- Day 1-2: Forecast Accuracy Service
- Day 3: Enhanced Performance Service
- Day 4-5: Timing Analysis Service

### **Week 2: Backend Complete**
- Day 1-2: Risk Analysis Service
- Day 3: Historical Summary Endpoint
- Day 4-5: Export Service

### **Week 3: Frontend Core**
- Day 1: Navigation & Structure
- Day 2-4: Overview Page
- Day 5: Historical Enhancements

### **Week 4: Frontend Complete**
- Day 1-2: Forecast Accuracy Tab
- Day 3: Timing Analysis Tab
- Day 4: Risk Analysis Tab
- Day 5: Export UI & Testing

**Total**: 4 weeks (was 5 weeks)

---

## 🎨 Simplified Page Structure

### **Overview Page** (Macro)
```
┌─────────────────────────────────────────────────────────┐
│ Performance > Overview                                   │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Period: [Last 30 Days ▼]  Stations: [All ▼]            │
│                                                          │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│ │ Forecast │ │ Trading  │ │ Win Rate │ │ ROI      │  │
│ │ Accuracy │ │ P&L      │ │          │ │          │  │
│ │ MAE: 1.2 │ │ $8,240   │ │ 63.12%   │ │ 17.61%   │  │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
│                                                          │
│ ┌────────────────────────────────────────────────────┐ │
│ │ Station Performance                                │ │
│ │ EGLC: ████████████ 18.75% ROI  [View]            │ │
│ │ KLGA: ████████      10.49% ROI  [View]            │ │
│ └────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌────────────────────────────────────────────────────┐ │
│ │ P&L Over Time                                      │ │
│ │ [Simple line chart: Cumulative P&L]               │ │
│ └────────────────────────────────────────────────────┘ │
│                                                          │
│ [Export Data]                                            │
└─────────────────────────────────────────────────────────┘
```

### **Historical Page** (Micro)
```
┌─────────────────────────────────────────────────────────┐
│ Performance > Historical                                 │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Station: [EGLC ▼]  Date: [2025-11-16 ▼]                │
│                                                          │
│ ┌────────────────────────────────────────────────────┐ │
│ │ Graph 1: Zeus Forecast Evolution                  │ │
│ │ [Hourly forecast + METAR actual]                  │ │
│ │ Daily High: Predicted 44.6°F, Actual 44.8°F ✅   │ │
│ └────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌────────────────────────────────────────────────────┐ │
│ │ Graph 2: Market Probabilities                     │ │
│ │ [Probability lines over time]                     │ │
│ └────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌────────────────────────────────────────────────────┐ │
│ │ Graph 3: Trading Decisions                        │ │
│ │ [Trade markers over time]                         │ │
│ └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### **Analytics Page** (Macro)
```
┌─────────────────────────────────────────────────────────┐
│ Performance > Analytics                                  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ [Forecast Accuracy] [Timing] [Risk]                     │
│  └─ Current ─┘                                          │
│                                                          │
│ ┌────────────────────────────────────────────────────┐ │
│ │ [Content changes based on active tab]             │ │
│ │                                                    │ │
│ │ Forecast Accuracy Tab:                            │ │
│ │ - Predicted vs. Actual scatter                    │ │
│ │ - Accuracy by Forecast Age                        │ │
│ │ - Error Distribution by Station                   │ │
│ │                                                    │ │
│ │ Timing Tab:                                        │ │
│ │ - P&L by Trade Time                               │ │
│ │ - Win Rate by Trade Time                          │ │
│ │                                                    │ │
│ │ Risk Tab:                                          │ │
│ │ - Loss Patterns                                   │ │
│ │ - Large Loss Events                               │ │
│ │ - Edge vs. Outcome                                │ │
│ └────────────────────────────────────────────────────┘ │
│                                                          │
│ [Export Data]                                            │
└─────────────────────────────────────────────────────────┘
```

---

## ✅ Success Criteria (MVP)

**We'll know MVP is complete when we can answer**:

1. ✅ "Was Zeus accurate?" → Forecast Accuracy tab shows MAE, RMSE, by station/age
2. ✅ "When should we trade?" → Timing tab shows P&L by trade time
3. ✅ "What went wrong?" → Risk tab shows loss patterns and large losses
4. ✅ "Which stations work best?" → Overview shows station comparison
5. ✅ "Can I export for LLM analysis?" → Export works for JSON and Text

---

## 🚀 Implementation Order

### **Phase 1: Backend Essentials** (Week 1-2)
1. Forecast Accuracy Service
2. Enhanced Performance Service
3. Timing Analysis Service
4. Risk Analysis Service
5. Historical Summary Endpoint
6. Export Service

### **Phase 2: Frontend Essentials** (Week 3-4)
1. Navigation & Structure
2. Overview Page
3. Historical Enhancements
4. Analytics Tabs (3 tabs)
5. Export UI

### **Phase 3: Polish & Test** (Week 4)
- Testing
- Bug fixes
- UI polish

---

## 📊 Data Requirements (MVP)

### **Existing Data** (Already Available)
- ✅ Zeus snapshots (with timestamps)
- ✅ Polymarket snapshots (with timestamps)
- ✅ METAR snapshots (with actual daily highs)
- ✅ Trade records (with outcomes)
- ✅ Decision snapshots

### **New Calculations Needed**
- Forecast accuracy (predicted vs. actual)
- Trade timing (hours before event)
- P&L by station/bracket
- Loss patterns

---

## 🔗 API Endpoints (MVP)

### **Essential Endpoints**

**Forecast Accuracy**:
- `GET /api/forecast-accuracy/metrics`

**Performance**:
- `GET /api/performance/metrics` (enhance existing)
- `GET /api/performance/historical/{station_code}/{date}` (new)

**Analytics**:
- `GET /api/analytics/timing`
- `GET /api/analytics/risk`

**Export**:
- `GET /api/performance/export`

**Existing** (Use As-Is):
- `GET /api/snapshots/*` (for Historical view)
- `GET /api/performance/pnl` (for Overview)

---

## 🎯 What We're NOT Building (Yet)

### **Deferred to Future**
- Forecast Evolution tab (detailed volatility analysis)
- Market Dynamics tab (market efficiency, opportunity cost)
- Dynamic Timing tab (optimal entry windows, correlation)
- Bracket Analysis tab (detailed bracket performance)
- Strategy Optimization tab (parameter sensitivity)

**Why**: These are valuable but not essential for MVP. Build core first, add advanced features based on actual usage.

---

## 💡 Key Principles

1. **Start Simple**: Build MVP with essential metrics only
2. **Add Value First**: Focus on actionable insights
3. **Iterate Based on Usage**: Add advanced features after MVP is proven useful
4. **Avoid Over-Engineering**: Don't build features "just in case"
5. **Keep It Fast**: MVP should load quickly and be easy to use

---

## 📋 MVP Checklist

### Backend
- [ ] Forecast Accuracy Service
- [ ] Enhanced Performance Service
- [ ] Timing Analysis Service
- [ ] Risk Analysis Service
- [ ] Historical Summary Endpoint
- [ ] Export Service
- [ ] All endpoints tested

### Frontend
- [ ] Navigation & Routing
- [ ] Overview Page (summary cards, station comparison, P&L chart)
- [ ] Historical Page (enhanced with actual outcomes)
- [ ] Analytics Page (3 tabs: Forecast Accuracy, Timing, Risk)
- [ ] Export Modal
- [ ] All pages tested

---

## 🎯 Summary

**MVP Focus**: Answer the 4 essential questions with clear, actionable insights.

**Build**:
- Overview: Key metrics at a glance
- Historical: Day-by-day analysis (enhance existing)
- Analytics: 3 essential tabs (Forecast Accuracy, Timing, Risk)
- Export: JSON and Text formats

**Defer**:
- Advanced analytics tabs
- Detailed dynamic analysis
- Complex visualizations
- Strategy optimization tools

**Timeline**: 4 weeks (streamlined from 5 weeks)

**Approach**: Build MVP, validate with usage, add advanced features based on actual needs.

---

**Last Updated**: November 18, 2025

