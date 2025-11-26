# Portfolio vs Performance: Structure Analysis

**Date**: November 18, 2025  
**Purpose**: Analyze the best UX structure for Portfolio and Performance pages

---

## 🤔 The Question

**Current Plan**:
- Portfolio = Account status (balances, P&L, trade history)
- Performance = Analysis (macro overview + micro drill-down)

**User's Suggestion**:
- Portfolio = Macro (system-wide account status)
- Performance = Micro (detailed day-by-day analysis)

**Which makes more sense for UX?**

---

## 🎯 User Journey Analysis

### **What Users Actually Need**

1. **Quick Status Check** (Most Common)
   - "How much money do I have?"
   - "Am I profitable overall?"
   - "What's my win rate?"
   - **Answer**: Portfolio page

2. **Understanding Performance** (Less Frequent, But Critical)
   - "Why did I win/lose?"
   - "Was Zeus accurate?"
   - "When should I trade?"
   - "Which stations work best?"
   - **Answer**: Performance page

3. **Deep Dive** (When Something Goes Wrong)
   - "What happened on Nov 16?"
   - "Why did this trade lose?"
   - "How did the forecast evolve?"
   - **Answer**: Performance page (micro view)

---

## 📊 Two Possible Structures

### **Option A: Current Plan (Portfolio = Status, Performance = Analysis)**

**Portfolio Page**:
- Account balances
- Total P&L, Win Rate, ROI
- Trade history table
- **Purpose**: "What happened?" (account status)

**Performance Page**:
- **Macro View**: System-wide analysis
  - Forecast accuracy (system-wide)
  - Timing analysis (system-wide)
  - Station performance (system-wide)
  - Loss analysis (system-wide)
- **Micro View**: Day-by-day drill-down
  - Three stacked graphs
  - Forecast evolution
  - Market dynamics
- **Purpose**: "Why did it happen? How to improve?"

**Pros**:
- ✅ Clear separation: Status vs Analysis
- ✅ Performance page answers all 4 questions
- ✅ Can do both macro and micro analysis

**Cons**:
- ❌ Performance page is complex (macro + micro)
- ❌ Might be confusing to have "macro" analysis on "Performance"

---

### **Option B: User's Suggestion (Portfolio = Macro, Performance = Micro)**

**Portfolio Page (Macro)**:
- Account balances
- Total P&L, Win Rate, ROI
- **System-wide analysis**:
  - Forecast accuracy (overall)
  - Timing analysis (overall)
  - Station performance (overall)
  - Loss patterns (overall)
- Trade history table
- **Purpose**: "What happened overall? How are we doing?"

**Performance Page (Micro)**:
- Day-by-day detailed analysis
- Three stacked graphs (already implemented)
- Forecast evolution for specific days
- Market dynamics for specific days
- Post-trade analysis
- **Purpose**: "Why did this specific day behave the way it did?"

**Pros**:
- ✅ Clearer structure: Macro vs Micro
- ✅ Portfolio = "How are we doing overall?"
- ✅ Performance = "What happened on this day?"
- ✅ Simpler Performance page (just micro)
- ✅ Better matches user mental model

**Cons**:
- ❌ Portfolio page becomes more complex
- ❌ Need to decide: where do the 4 essential questions live?

---

## 💡 My Recommendation: **Option B (User's Suggestion)**

**Why Option B is Better**:

1. **Matches User Mental Model**
   - Portfolio = "My account" (macro view)
   - Performance = "This specific day" (micro view)
   - More intuitive

2. **Clearer Navigation**
   - Portfolio: System-wide status and analysis
   - Performance: Drill-down to specific days
   - Natural flow: Portfolio → Performance (drill-down)

3. **Simpler Performance Page**
   - Just micro view (day-by-day)
   - Already mostly implemented
   - Less cognitive load

4. **Better Information Architecture**
   - Macro analysis belongs with account status
   - Micro analysis is separate drill-down
   - Clear hierarchy

---

## 🎯 Revised Structure: Option B

### **Portfolio Page (Macro)**

**Purpose**: "How are we doing overall?"

**Sections**:

1. **Account Status** (Top)
   - Account balances
   - Total P&L, Win Rate, ROI
   - Quick health check

2. **System-Wide Analysis** (Middle)
   - **Forecast Accuracy** (overall)
     - MAE, RMSE, Stability
     - Accuracy by forecast age
   - **Timing Analysis** (overall)
     - P&L by trade timing
     - Optimal window
   - **Station Performance** (overall)
     - P&L by station
     - Win rate by station
   - **Loss Analysis** (overall)
     - Top loss events
     - Common patterns

3. **Trade History** (Bottom)
   - All trades table
   - Filterable, searchable

**User Flow**: "I want to see how I'm doing overall" → Portfolio

---

### **Performance Page (Micro)**

**Purpose**: "What happened on this specific day?"

**Sections**:

1. **Day/Station Selector** (Top)
   - Select date
   - Select station
   - Quick summary for that day

2. **Detailed Analysis** (Main)
   - **Graph 1**: Zeus Forecast Evolution vs METAR Actual
   - **Graph 2**: Polymarket Probabilities Over Time
   - **Graph 3**: Trading Decisions Timeline
   - **Daily High Panel**: Forecast accuracy for that day
   - **Post-Trade Analysis**: What happened after trades

3. **Insights** (Bottom)
   - Why did we win/lose this day?
   - Forecast accuracy for this day
   - Market dynamics for this day

**User Flow**: "I want to understand what happened on Nov 16" → Performance

---

## 🔄 Navigation Flow

```
┌─────────────────────────────────────────────────────────┐
│ Main Navigation                                         │
│                                                         │
│ [Live Dashboard] [Portfolio] [Performance] [Config]    │
│              └───┐         └───┐                       │
│                  │             │                       │
│         "How are we doing?"    │                       │
│         (System-wide)          │                       │
│                                │                       │
│                                │                       │
│                        "What happened on this day?"    │
│                        (Day-by-day drill-down)         │
└─────────────────────────────────────────────────────────┘
```

**Natural Flow**:
1. User checks Portfolio → "Overall, we're doing well"
2. User sees a bad day → Clicks to Performance → "Let me see what happened on Nov 16"
3. User drills down → Sees detailed graphs and analysis

---

## 📋 Updated Page Responsibilities

### **Portfolio Page (Macro)**
**Shows**:
- ✅ Account balances
- ✅ Total P&L, Win Rate, ROI
- ✅ System-wide forecast accuracy
- ✅ System-wide timing analysis
- ✅ System-wide station performance
- ✅ System-wide loss analysis
- ✅ Trade history table

**Answers**:
- "How much money do I have?"
- "Am I profitable overall?"
- "Was Zeus accurate overall?"
- "When should we trade (overall)?"
- "Which stations work best (overall)?"

---

### **Performance Page (Micro)**
**Shows**:
- ✅ Day-by-day detailed graphs
- ✅ Forecast evolution for specific day
- ✅ Market dynamics for specific day
- ✅ Trading decisions for specific day
- ✅ Post-trade analysis for specific day
- ✅ Forecast accuracy for specific day

**Answers**:
- "What happened on Nov 16?"
- "Why did we win/lose this day?"
- "How did the forecast evolve on this day?"
- "How did the market move on this day?"

---

## ✅ Final Recommendation

**Go with Option B (User's Suggestion)**:

1. **Portfolio = Macro**
   - System-wide account status
   - System-wide analysis
   - Answers: "How are we doing overall?"

2. **Performance = Micro**
   - Day-by-day detailed analysis
   - Drill-down from Portfolio
   - Answers: "What happened on this day?"

**Why This Works**:
- ✅ More intuitive
- ✅ Clearer structure
- ✅ Better UX flow
- ✅ Simpler Performance page
- ✅ Natural drill-down pattern

---

## 🚀 Implementation Impact

### **Portfolio Page Changes**:
- ✅ Add system-wide analysis sections
- ✅ Keep account status at top
- ✅ Add forecast accuracy, timing, station performance, loss analysis
- ✅ Keep trade history table

### **Performance Page Changes**:
- ✅ Remove macro analysis (move to Portfolio)
- ✅ Keep only micro view (day-by-day)
- ✅ Enhance with post-trade analysis
- ✅ Simplify structure

---

## 🎯 Key Insight

**The user is right!**

Portfolio should be the **macro view** (system-wide status and analysis), and Performance should be the **micro view** (day-by-day drill-down).

This matches the natural user mental model:
- "How am I doing?" → Portfolio (macro)
- "What happened on this day?" → Performance (micro)

---

**Last Updated**: November 18, 2025


