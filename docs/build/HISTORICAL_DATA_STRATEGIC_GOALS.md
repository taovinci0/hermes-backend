# Performance Analysis: Strategic Goals

**Purpose**: Define what performance analysis visualizations we need to improve trading performance  
**Date**: November 18, 2025  
**Focus**: Strategic "why" and "what" - what questions do we need to answer?

**Note**: This page is about **Performance Analysis** (forecast accuracy, timing, patterns).  
The **Portfolio** page is separate and focuses on account balances, P&L, and trade history.

---

## 🎯 Core Objective

**Goal**: Use historical data to identify patterns, optimize strategies, and improve future trading decisions.

**Key Question**: "What can we learn from the past to make better trades in the future?"

---

## 📊 Critical Questions We Need to Answer

### 1. **Forecast Accuracy Analysis**

**Question**: "When is Zeus most accurate, and when should we trust it?"

**What we need to visualize**:
- ✅ **Accuracy by time of day**: Is Zeus more accurate in the morning vs. afternoon?
- ✅ **Accuracy by forecast age**: How does accuracy change as the event approaches?
- ✅ **Accuracy by weather conditions**: Is Zeus better for certain temperature ranges?
- ✅ **Accuracy by station**: Which stations have the most reliable forecasts?
- ✅ **Forecast stability**: How much does Zeus change its mind? (volatility of predictions)
- ✅ **Error distribution**: Are errors systematic (always high/low) or random?

**Actionable Insights**:
- "Zeus is most accurate when forecast is made within 6 hours of event"
- "Zeus tends to overestimate temperatures in London by 1-2°F"
- "We should avoid trading on forecasts older than 12 hours"

**Visualization Needs**:
- Heatmap: Accuracy by forecast age × time of day
- Scatter plot: Predicted vs. Actual (with trend line)
- Box plot: Error distribution by station
- Time series: Forecast evolution vs. actual outcome

---

### 2. **Market Efficiency Analysis**

**Question**: "When are edges largest, and when do they disappear?"

**What we need to visualize**:
- ✅ **Edge decay over time**: How quickly do edges disappear as event approaches?
- ✅ **Edge by market age**: Are edges larger when markets first open?
- ✅ **Edge by bracket**: Which brackets consistently have the best edges?
- ✅ **Market reaction**: How do market probabilities change after we trade?
- ✅ **Edge persistence**: How long do edges last before market corrects?
- ✅ **Liquidity impact**: Do edges correlate with market liquidity?

**Actionable Insights**:
- "Edges are largest 24-48 hours before event, then decay rapidly"
- "Market corrects within 2 hours of our trades (edge disappears)"
- "58-59°F bracket consistently has 3-5% edge"

**Visualization Needs**:
- Line chart: Edge % over time (market open → close)
- Heatmap: Edge by bracket × market age
- Scatter plot: Edge vs. Liquidity
- Timeline: Edge decay after trade placement

---

### 3. **Trade Timing Analysis**

**Question**: "When should we trade for maximum profitability?"

**What we need to visualize**:
- ✅ **P&L by trade time**: Are early trades more profitable than late trades?
- ✅ **P&L by market age**: Should we trade when markets first open?
- ✅ **P&L by forecast age**: Should we wait for fresh forecasts?
- ✅ **Win rate by timing**: When are we most likely to win?
- ✅ **Optimal entry window**: What's the best time to enter trades?
- ✅ **Exit timing**: When should we close positions (if we add this feature)?

**Actionable Insights**:
- "Trades placed 24-36 hours before event have 15% higher win rate"
- "Waiting for forecast updates improves accuracy by 8%"
- "Trading in the morning (9am-12pm) yields better results"

**Visualization Needs**:
- Bar chart: Average P&L by hour of day
- Line chart: Win rate by market age
- Scatter plot: P&L vs. Forecast age
- Heatmap: Win rate by trade time × market age

---

### 4. **Risk and Loss Analysis**

**Question**: "What causes losses, and how can we avoid them?"

**What we need to visualize**:
- ✅ **Loss patterns**: What conditions lead to losses?
- ✅ **Large loss analysis**: What went wrong with our biggest losses?
- ✅ **Edge vs. Outcome**: Do larger edges lead to better outcomes?
- ✅ **Forecast error vs. Loss**: Are losses correlated with forecast errors?
- ✅ **Market mispricing**: When does the market know something we don't?
- ✅ **Black swan events**: What unexpected events caused losses?

**Actionable Insights**:
- "Losses occur when forecast error > 3°F"
- "Large edges (>10%) actually have lower win rates (market knows something)"
- "We lose when Zeus changes forecast significantly after we trade"

**Visualization Needs**:
- Scatter plot: Forecast error vs. P&L
- Box plot: Edge distribution for wins vs. losses
- Timeline: Large loss events with context
- Correlation matrix: Factors leading to losses

---

### 5. **Station and Venue Performance**

**Question**: "Which stations and venues are most profitable?"

**What we need to visualize**:
- ✅ **P&L by station**: Which stations are most profitable?
- ✅ **Win rate by station**: Which stations have highest win rates?
- ✅ **ROI by station**: Which stations give best returns?
- ✅ **Station-specific patterns**: Do certain stations have unique characteristics?
- ✅ **Venue comparison**: Polymarket vs. Kalshi performance (future)
- ✅ **Geographic patterns**: Are certain regions more profitable?

**Actionable Insights**:
- "London (EGLC) has 25% higher win rate than NYC (KLGA)"
- "Polymarket edges are larger but Kalshi has better execution"
- "Coastal stations have more volatile forecasts"

**Visualization Needs**:
- Bar chart: P&L by station
- Heatmap: Win rate × ROI by station
- Comparison chart: Station performance metrics
- Geographic map: Performance by location (future)

---

### 6. **Bracket Selection Analysis**

**Question**: "Which brackets should we focus on?"

**What we need to visualize**:
- ✅ **P&L by bracket**: Which brackets are most profitable?
- ✅ **Win rate by bracket**: Which brackets have highest win rates?
- ✅ **Edge by bracket**: Which brackets consistently have edges?
- ✅ **Bracket frequency**: How often does each bracket win?
- ✅ **Optimal bracket range**: What temperature ranges are best?
- ✅ **Bracket correlation**: Do certain brackets move together?

**Actionable Insights**:
- "58-59°F bracket has 40% win rate and 8% average edge"
- "Extreme brackets (≤50°F, ≥70°F) have high edges but low win rates"
- "Middle brackets (55-65°F) are most reliable"

**Visualization Needs**:
- Bar chart: P&L by bracket
- Scatter plot: Win rate vs. Edge by bracket
- Heatmap: Bracket performance matrix
- Distribution: Bracket win frequency

---

### 7. **Strategy Optimization**

**Question**: "How can we optimize our trading parameters?"

**What we need to visualize**:
- ✅ **Parameter sensitivity**: How do different parameters affect performance?
- ✅ **Kelly sizing impact**: Is our Kelly cap optimal?
- ✅ **Edge threshold**: Is our minimum edge threshold correct?
- ✅ **Liquidity filter**: Is our liquidity minimum too high/low?
- ✅ **Model comparison**: Spread model vs. Bands model performance
- ✅ **Backtest vs. Paper**: How does backtest performance compare to paper trading?

**Actionable Insights**:
- "Lowering edge_min from 3% to 2% increases trades by 40% but reduces win rate by 5%"
- "Kelly cap of 0.10 is optimal (higher increases risk, lower reduces returns)"
- "Bands model has 3% higher win rate than spread model"

**Visualization Needs**:
- Parameter sweep charts: Performance vs. Parameter value
- Comparison chart: Model A vs. Model B
- Sensitivity analysis: Heatmap of parameter combinations
- Backtest validation: Backtest vs. Paper performance

---

### 8. **Market Behavior Patterns**

**Question**: "How do markets behave, and can we predict movements?"

**What we need to visualize**:
- ✅ **Probability evolution**: How do market probabilities change over time?
- ✅ **Market efficiency**: Do markets correct quickly or slowly?
- ✅ **Volatility patterns**: When are markets most volatile?
- ✅ **Correlation with forecasts**: Do markets follow Zeus predictions?
- ✅ **Market sentiment shifts**: What causes large probability changes?
- ✅ **Arbitrage opportunities**: Are there price discrepancies between brackets?

**Actionable Insights**:
- "Markets move toward Zeus predictions 2-4 hours before event"
- "Market volatility spikes 6 hours before event"
- "Probability changes >5% in 1 hour indicate new information"

**Visualization Needs**:
- Line chart: Probability evolution over time
- Volatility chart: Market volatility by time
- Correlation plot: Market vs. Zeus predictions
- Event timeline: Market movements with annotations

---

### 9. **Performance Attribution**

**Question**: "What drives our performance - skill or luck?"

**What we need to visualize**:
- ✅ **Skill vs. Luck**: How much of our P&L is from skill vs. luck?
- ✅ **Edge realization**: Do we capture the edges we identify?
- ✅ **Forecast contribution**: How much does forecast accuracy contribute?
- ✅ **Market timing contribution**: How much does timing contribute?
- ✅ **Sizing contribution**: How much does position sizing contribute?
- ✅ **Consistency**: Are we consistently profitable or just lucky?

**Actionable Insights**:
- "70% of P&L comes from forecast accuracy, 20% from timing, 10% from sizing"
- "We capture 85% of identified edges (15% slippage/costs)"
- "Performance is consistent across months (not just luck)"

**Visualization Needs**:
- Attribution chart: Contribution by factor
- Rolling performance: P&L over time with confidence intervals
- Skill metric: Sharpe ratio, win rate consistency
- Decomposition: P&L breakdown by component

---

### 10. **Comparative Analysis**

**Question**: "How do we compare to benchmarks and alternatives?"

**What we need to visualize**:
- ✅ **vs. Market**: Do we outperform market probabilities?
- ✅ **vs. Baseline**: How do we compare to simple strategies?
- ✅ **vs. Zeus**: Do we add value beyond just following Zeus?
- ✅ **vs. Historical**: Are we improving over time?
- ✅ **vs. Other traders**: How do we compare (if data available)?

**Actionable Insights**:
- "We outperform market probabilities by 8% ROI"
- "Our strategy beats 'always bet on Zeus prediction' by 12%"
- "Performance improving month-over-month"

**Visualization Needs**:
- Comparison chart: Our performance vs. Benchmarks
- Improvement trend: Performance over time
- Benchmark table: Side-by-side metrics

---

## 👤 User Experience & Interface Design

### **Analysis Levels: Micro vs. Macro**

Historical data analysis should operate at **multiple levels** to provide both detailed insights and high-level overviews:

#### **Micro Level: Station-by-Station, Day-by-Day**
- **Focus**: Detailed analysis of individual events
- **Scope**: Single station, single event day
- **Use Case**: "What happened on Nov 16 for London (EGLC)?"
- **Current Implementation**: Performance page - Historical view (three stacked graphs)

#### **Macro Level: System-Wide, Aggregated**
- **Focus**: Overall performance patterns and trends
- **Scope**: All stations, all days, aggregated metrics
- **Use Case**: "Which stations are most profitable overall?"
- **Future Implementation**: Performance Dashboard, Analytics pages

#### **Mid Level: Station Aggregated, Time Series**
- **Focus**: Station performance over time
- **Scope**: Single station, multiple days
- **Use Case**: "How has London (EGLC) performed over the past month?"
- **Future Implementation**: Station performance pages

---

### **User Interface Structure**

#### **1. Performance Page - Historical View (Micro Level)**

**Current**: Station-by-station, day-by-day detailed view

**Note**: This is the **Performance** page (not "Historical Data"). The **Portfolio** page is separate and shows account balances and trade history.

**What Users See**:
```
┌─────────────────────────────────────────────────────────┐
│ Performance Analysis - Historical View                   │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Station: [EGLC ▼]  Date: [2025-11-16 ▼]  [Analyze]     │
│                                                          │
│ ┌────────────────────────────────────────────────────┐ │
│ │ Graph 1: Zeus Forecast Evolution (Hourly)          │ │
│ │ [Hourly forecast lines + METAR actual]             │ │
│ │ Daily High Panel: Predicted 44.6°F, Actual 44.8°F │ │
│ └────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌────────────────────────────────────────────────────┐ │
│ │ Graph 2: Polymarket Probabilities Over Time        │ │
│ │ [Probability lines for each bracket]               │ │
│ └────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌────────────────────────────────────────────────────┐ │
│ │ Graph 3: Trading Decisions Timeline                │ │
│ │ [Trade markers with outcomes]                      │ │
│ └────────────────────────────────────────────────────┘ │
│                                                          │
│ Summary: 3 trades, 2 wins, 1 loss, +$125.50 P&L       │
└─────────────────────────────────────────────────────────┘
```

**User Actions**:
- Select station from dropdown
- Select date from calendar (past dates only)
- View detailed graphs for that specific day
- See individual trade outcomes

**Analysis Type**: **Micro** - Single event, detailed view

---

#### **2. Performance Dashboard (Macro Level)**

**Future**: System-wide aggregated performance analysis

**Note**: This is different from the **Portfolio** page:
- **Performance Dashboard**: Analysis of forecast accuracy, timing, patterns, optimization
- **Portfolio Page**: Account balances, P&L, trade history, account status

**What Users See**:
```
┌─────────────────────────────────────────────────────────┐
│ Performance Dashboard                                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Period: [Last 30 Days ▼]  [All Time ▼]                 │
│                                                          │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │
│ │ Total P&L    │ │ Win Rate     │ │ ROI          │    │
│ │ +$8,240.00   │ │ 63.12%       │ │ 17.61%       │    │
│ │ ↗ +12.5%     │ │ ↗ +2.3%      │ │ ↗ +1.8%      │    │
│ └──────────────┘ └──────────────┘ └──────────────┘    │
│                                                          │
│ ┌────────────────────────────────────────────────────┐ │
│ │ Station Performance Comparison                      │ │
│ │                                                      │ │
│ │ EGLC (London)    ████████████ 18.75% ROI  $4,200   │ │
│ │ KLGA (NYC)       ████████     10.49% ROI  $2,340   │ │
│ │ KORD (Chicago)   ██████████   15.23% ROI  $1,700   │ │
│ │ ...                                                    │ │
│ └────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌────────────────────────────────────────────────────┐ │
│ │ P&L Over Time                                       │ │
│ │ [Line chart showing cumulative P&L]                │ │
│ └────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌────────────────────────────────────────────────────┐ │
│ │ Top Performing Brackets                            │ │
│ │ 58-59°F: 40% win rate, 8% avg edge, $2,100 P&L    │ │
│ │ 60-61°F: 35% win rate, 6% avg edge, $1,800 P&L    │ │
│ │ ...                                                    │ │
│ └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

**User Actions**:
- Select time period (today, week, month, year, all time)
- View aggregated metrics across all stations
- Compare station performance
- See overall trends

**Analysis Type**: **Macro** - System-wide, aggregated

---

#### **3. Station Performance Page (Mid Level)**

**Future**: Single station, multiple days

**What Users See**:
```
┌─────────────────────────────────────────────────────────┐
│ Station Performance: EGLC (London)                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Period: [Last 30 Days ▼]                                │
│                                                          │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │
│ │ Station P&L  │ │ Win Rate     │ │ Avg Edge     │    │
│ │ +$4,200.00   │ │ 61.64%       │ │ 18.25%       │    │
│ └──────────────┘ └──────────────┘ └──────────────┘    │
│                                                          │
│ ┌────────────────────────────────────────────────────┐ │
│ │ P&L by Day                                         │ │
│ │ [Bar chart: Each day's P&L]                       │ │
│ └────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌────────────────────────────────────────────────────┐ │
│ │ Forecast Accuracy Over Time                        │ │
│ │ [Line chart: Accuracy % by day]                    │ │
│ └────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌────────────────────────────────────────────────────┐ │
│ │ Recent Events                                      │ │
│ │ Nov 16: 3 trades, 2 wins, +$125.50  [View Details]│ │
│ │ Nov 15: 2 trades, 1 win, +$45.00   [View Details]│ │
│ │ Nov 14: 4 trades, 3 wins, +$180.00 [View Details]│ │
│ └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

**User Actions**:
- Select station
- View performance over time
- Drill down to specific days
- Compare to other stations

**Analysis Type**: **Mid** - Station aggregated, time series

---

#### **4. Analytics Pages (Macro Level)**

**Future**: Specialized analysis dashboards

**What Users See**:

**A. Forecast Accuracy Dashboard**:
```
┌─────────────────────────────────────────────────────────┐
│ Forecast Accuracy Analysis                               │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ ┌────────────────────────────────────────────────────┐ │
│ │ Accuracy by Forecast Age                           │ │
│ │ [Heatmap: Forecast age × Time of day]              │ │
│ │ Darker = More accurate                             │ │
│ └────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌────────────────────────────────────────────────────┐ │
│ │ Predicted vs. Actual                               │ │
│ │ [Scatter plot with trend line]                     │ │
│ │ R² = 0.87 (Strong correlation)                     │ │
│ └────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌────────────────────────────────────────────────────┐ │
│ │ Error Distribution by Station                      │ │
│ │ [Box plot: Error range for each station]           │ │
│ └────────────────────────────────────────────────────┘ │
│                                                          │
│ Key Insights:                                           │
│ • Zeus most accurate within 6 hours of event           │
│ • London (EGLC) has lowest error (0.8°F avg)          │
│ • Forecasts tend to overestimate by 1-2°F             │
└─────────────────────────────────────────────────────────┘
```

**B. Trade Timing Analysis**:
```
┌─────────────────────────────────────────────────────────┐
│ Trade Timing Analysis                                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ ┌────────────────────────────────────────────────────┐ │
│ │ P&L by Trade Time (Hours Before Event)             │ │
│ │ [Bar chart: Average P&L by market age]             │ │
│ │ Peak: 24-36 hours before event                     │ │
│ └────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌────────────────────────────────────────────────────┐ │
│ │ Win Rate by Market Age                             │ │
│ │ [Line chart: Win rate % vs hours before event]     │ │
│ └────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌────────────────────────────────────────────────────┐ │
│ │ Edge Decay Over Time                               │ │
│ │ [Line chart: Average edge % vs market age]         │ │
│ │ Shows how quickly edges disappear                  │ │
│ └────────────────────────────────────────────────────┘ │
│                                                          │
│ Key Insights:                                           │
│ • Optimal entry: 24-36 hours before event              │
│ • Edges decay rapidly after 12 hours                   │
│ • Win rate 15% higher for early trades                 │
└─────────────────────────────────────────────────────────┘
```

**C. Risk Analysis Dashboard**:
```
┌─────────────────────────────────────────────────────────┐
│ Risk & Loss Analysis                                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ ┌────────────────────────────────────────────────────┐ │
│ │ Loss Patterns                                      │ │
│ │ [Scatter plot: Forecast error vs. P&L]             │ │
│ │ Red dots = Losses, Green dots = Wins               │ │
│ └────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌────────────────────────────────────────────────────┐ │
│ │ Large Loss Events                                  │ │
│ │ [Timeline with annotations]                        │ │
│ │ Nov 10: -$450 (Forecast error: 4.2°F)             │ │
│ │ Nov 5:  -$320 (Market moved against us)            │ │
│ └────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌────────────────────────────────────────────────────┐ │
│ │ Edge vs. Outcome                                   │ │
│ │ [Box plot: Edge distribution for wins vs losses]   │ │
│ └────────────────────────────────────────────────────┘ │
│                                                          │
│ Key Insights:                                           │
│ • Losses occur when forecast error > 3°F               │
│ • Large edges (>10%) have lower win rates              │
│ • Market often knows something we don't                │
└─────────────────────────────────────────────────────────┘
```

**Analysis Type**: **Macro** - System-wide patterns and insights

---

### **Navigation Flow**

```
┌─────────────────────────────────────────────────────────┐
│ Main Navigation                                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ [Live Dashboard] → Real-time, active markets            │
│                                                          │
│ [Portfolio] → Account balances, P&L, trade history      │
│   └─> Account balances (Polymarket, Kalshi)            │
│   └─> Overall P&L, win rate, ROI                        │
│   └─> Trade history table                               │
│                                                          │
│ [Performance] → Performance analysis                    │
│   ├─> Historical View (Micro: Station/day)              │
│   │   └─> Select station & date                         │
│   │   └─> View three stacked graphs                     │
│   │   └─> See forecast accuracy for that day            │
│   ├─> Dashboard (Macro: System-wide)                    │
│   │   └─> Forecast accuracy analysis                    │
│   │   └─> Timing analysis                               │
│   │   └─> Station comparison                            │
│   └─> Analytics (Macro: Specialized)                    │
│       ├─> Forecast Accuracy                             │
│       ├─> Trade Timing                                  │
│       ├─> Risk Analysis                                 │
│       ├─> Bracket Performance                           │
│       └─> Strategy Optimization                         │
│                                                          │
│ [Stations] → Station performance (Mid)                  │
│   └─> Select station                                    │
│   └─> View performance over time                        │
│   └─> Drill down to specific days                       │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

### **Drill-Down Pattern**

Users should be able to **drill down** from macro to micro:

1. **Start**: Performance Dashboard (Macro)
   - See: "EGLC has best forecast accuracy"
   - Action: Click on EGLC

2. **Navigate**: Station Performance Page (Mid)
   - See: "EGLC accuracy over last 30 days"
   - See: "Nov 16: 0.8°F average error"
   - Action: Click on Nov 16

3. **Detail**: Performance Page - Historical View (Micro)
   - See: Detailed graphs for Nov 16
   - See: Forecast evolution vs. actual
   - See: Forecast accuracy for that day

**Reverse Navigation**: Users can also go back up:
- From Performance Historical View → Station Performance
- From Station Performance → Performance Dashboard

**Note**: The **Portfolio** page is separate and shows account-level data (balances, P&L, trade history), not performance analysis.

---

## 🎨 Visualization Priorities

### **Tier 1: Must Have (Core Analysis)**

1. **Forecast Accuracy Dashboard** (Macro)
   - Predicted vs. Actual scatter plot (all stations, all days)
   - Error distribution by station (comparison)
   - Accuracy by forecast age (aggregated)

2. **Trade Performance Dashboard** (Macro)
   - P&L over time (system-wide)
   - Win rate by station/bracket (comparison)
   - Edge decay analysis (aggregated)

3. **Timing Analysis** (Macro)
   - P&L by trade time (all trades)
   - Optimal entry window (aggregated)
   - Market age impact (system-wide)

4. **Performance Page - Historical View** (Micro - Current)
   - Station/day detailed view
   - Three stacked graphs
   - Forecast accuracy analysis

### **Tier 2: High Value (Optimization)**

5. **Risk Analysis** (Macro)
   - Loss patterns (all trades)
   - Large loss events (system-wide)
   - Forecast error vs. Loss (aggregated)

6. **Parameter Optimization** (Macro)
   - Parameter sensitivity (system-wide)
   - Model comparison (aggregated)
   - Strategy backtesting (all data)

7. **Bracket Analysis** (Macro)
   - Bracket performance (all stations)
   - Optimal bracket selection (comparison)
   - Bracket correlation (system-wide)

8. **Station Performance Pages** (Mid)
   - Single station over time
   - Station-specific patterns
   - Drill-down to specific days

### **Tier 3: Nice to Have (Advanced)**

9. **Market Behavior** (Macro)
   - Probability evolution (aggregated)
   - Market efficiency (system-wide)
   - Volatility patterns (all markets)

10. **Performance Attribution** (Macro)
    - Skill vs. Luck (system-wide)
    - Component contribution (aggregated)
    - Consistency metrics (all data)

11. **Comparative Analysis** (Macro)
    - vs. Benchmarks (system-wide)
    - vs. Historical (aggregated)
    - Improvement trends (over time)

---

## 📈 Key Metrics to Track

### **Forecast Metrics**
- Forecast accuracy (MAE, RMSE)
- Forecast error distribution
- Forecast stability (volatility)
- Forecast age impact

### **Trading Metrics**
- Total P&L
- Win rate
- ROI
- Sharpe ratio
- Average edge
- Edge capture rate

### **Timing Metrics**
- P&L by trade time
- P&L by market age
- Optimal entry window
- Edge decay rate

### **Risk Metrics**
- Largest loss
- Loss frequency
- Drawdown
- Risk-adjusted returns

### **Station/Venue Metrics**
- P&L by station
- Win rate by station
- ROI by station
- Venue comparison

### **Bracket Metrics**
- P&L by bracket
- Win rate by bracket
- Edge by bracket
- Bracket frequency

---

## 🔍 Analysis Workflows

### **Daily Review**
1. Check yesterday's trades
2. Review forecast accuracy
3. Identify any large losses
4. Note any patterns

### **Weekly Review**
1. Performance summary
2. Station/bracket performance
3. Parameter effectiveness
4. Strategy adjustments

### **Monthly Review**
1. Full performance analysis
2. Parameter optimization
3. Model comparison
4. Strategy refinement

### **Quarterly Review**
1. Comprehensive backtest
2. Strategy evolution
3. New feature evaluation
4. Long-term trends

---

## 🎯 Success Criteria

**We'll know historical data visualization is successful when**:

1. ✅ **We can identify patterns**: "Zeus is most accurate when X"
2. ✅ **We can optimize parameters**: "Lowering edge_min to 2% improves performance"
3. ✅ **We can avoid losses**: "We avoid trading when forecast error > 3°F"
4. ✅ **We can improve timing**: "Trading 24-36 hours before event is optimal"
5. ✅ **We can select better brackets**: "58-59°F bracket has best risk/reward"
6. ✅ **We can measure improvement**: "Performance improving month-over-month"

---

## 🚀 Implementation Roadmap

### **Phase 1: Foundation (Current)**
- ✅ Performance page - Historical View (Micro: Station/day)
- ✅ Three stacked graphs (Zeus, Market, Trades)
- ✅ Basic forecast accuracy analysis

### **Phase 2: Macro Analysis (Next)**
- Performance Dashboard (Macro: System-wide overview)
- Forecast Accuracy Dashboard (Macro: Aggregated analysis)
- Trade Performance Analysis (Macro: All trades)
- Timing Analysis (Macro: Optimal entry windows)

### **Phase 3: Mid-Level Analysis (Future)**
- Station Performance Pages (Mid: Station over time)
- Station comparison tools
- Drill-down navigation

### **Phase 4: Advanced Optimization (Future)**
- Risk Analysis Dashboard (Macro)
- Parameter Optimization Tools (Macro)
- Strategy Comparison (Macro)
- Bracket Analysis (Macro)

### **Phase 5: Intelligence (Future)**
- Pattern recognition (Macro)
- Predictive analytics (Macro)
- Automated insights (Macro)
- Comparative analysis (Macro)

---

## 📊 Analysis Level Summary

### **Micro Level (Station/Day)**
- **Current**: Performance page - Historical View
- **Scope**: Single station, single event day
- **Use Case**: Detailed analysis of specific events
- **Visualizations**: Three stacked graphs, forecast accuracy

### **Mid Level (Station/Time Series)**
- **Future**: Station Performance pages
- **Scope**: Single station, multiple days
- **Use Case**: Station performance over time
- **Visualizations**: P&L by day, accuracy trends, recent events

### **Macro Level (System-Wide)**
- **Future**: Performance Dashboard, Analytics pages
- **Scope**: All stations, all days, aggregated
- **Use Case**: Overall patterns, optimization, comparison
- **Visualizations**: Aggregated metrics, comparisons, trends

---

## 🎯 User Workflow Examples

### **Example 1: Daily Review (Micro → Macro)**
1. **Start**: Performance page - Historical View
   - Select yesterday's date
   - Review forecast accuracy and patterns
2. **Navigate**: Performance Dashboard
   - See overall forecast accuracy
   - Compare to other days
3. **Action**: Identify patterns
   - "Yesterday's forecast errors were > 3°F, leading to poor trades"

### **Example 2: Weekly Analysis (Macro → Micro)**
1. **Start**: Performance Dashboard
   - See: "EGLC has best ROI this week"
2. **Navigate**: Station Performance (EGLC)
   - See: Performance over the week
   - Identify best days
3. **Drill Down**: Performance page - Historical View
   - Review specific high-accuracy days
   - Understand what made forecasts accurate

### **Example 3: Strategy Optimization (Macro)**
1. **Start**: Analytics → Trade Timing
   - See: "Optimal entry is 24-36 hours before event"
2. **Navigate**: Analytics → Forecast Accuracy
   - See: "Zeus most accurate within 6 hours"
3. **Action**: Adjust strategy
   - "Trade earlier (24-36h) but wait for fresh forecast (<6h old)"

### **Example 4: Risk Management (Macro → Micro)**
1. **Start**: Analytics → Risk Analysis
   - See: "Losses occur when forecast error > 3°F"
2. **Navigate**: Performance page - Historical View
   - Review specific high-error days
   - Understand what caused forecast errors
3. **Action**: Implement filter
   - "Avoid trading when forecast error > 3°F"

---

## 💡 Key Insights We're Looking For

1. **When to trade**: Optimal timing for maximum profitability
2. **What to trade**: Best brackets and stations
3. **How much to trade**: Optimal position sizing
4. **When to avoid**: Conditions that lead to losses
5. **How to improve**: Parameter and strategy optimization

---

## 📋 Summary

**Historical data visualization should help us answer**:

1. ✅ **Forecast Accuracy**: When is Zeus most accurate?
2. ✅ **Market Efficiency**: When are edges largest?
3. ✅ **Trade Timing**: When should we trade?
4. ✅ **Risk Management**: What causes losses?
5. ✅ **Station Performance**: Which stations are best?
6. ✅ **Bracket Selection**: Which brackets are most profitable?
7. ✅ **Strategy Optimization**: How can we improve?
8. ✅ **Market Behavior**: How do markets move?
9. ✅ **Performance Attribution**: What drives our success?
10. ✅ **Comparative Analysis**: How do we compare?

**The goal**: Turn performance data into actionable insights that improve future trading decisions.

---

## 📤 Exportable Data for LLM Analysis

### **Purpose**

All performance analysis data should be exportable in formats suitable for LLM analysis, allowing users to:
- Share data with any LLM (ChatGPT, Claude, Gemini, etc.)
- Get AI-powered insights and recommendations
- Perform advanced analysis beyond what's built into the UI
- Generate reports and summaries

### **Export Formats**

#### **1. JSON (Structured Data)**

**Format**: Comprehensive JSON with all performance metrics

**Use Case**: Best for structured analysis, programmatic processing

**Example Structure**:
```json
{
  "export_metadata": {
    "export_date": "2025-11-18T10:00:00Z",
    "period": {
      "start_date": "2025-10-01",
      "end_date": "2025-11-18"
    },
    "stations": ["EGLC", "KLGA", "KORD"],
    "total_trades": 156,
    "version": "1.0"
  },
  "forecast_accuracy": {
    "overall": {
      "mae": 1.2,
      "rmse": 1.8,
      "mean_error": 0.3,
      "correlation": 0.87
    },
    "by_station": {
      "EGLC": {
        "mae": 0.8,
        "rmse": 1.1,
        "mean_error": 0.1
      }
    },
    "by_forecast_age": {
      "0-6_hours": {"mae": 0.9, "accuracy_pct": 92.5},
      "6-12_hours": {"mae": 1.2, "accuracy_pct": 88.3},
      "12-24_hours": {"mae": 1.6, "accuracy_pct": 82.1}
    },
    "predictions": [
      {
        "date": "2025-11-16",
        "station": "EGLC",
        "predicted_high_f": 44.6,
        "actual_high_f": 44.8,
        "error_f": 0.2,
        "forecast_age_hours": 4.5
      }
    ]
  },
  "trading_performance": {
    "overall": {
      "total_pnl": 8240.00,
      "total_risk": 46800.00,
      "roi": 17.61,
      "win_rate": 63.12,
      "sharpe_ratio": 1.23
    },
    "by_station": {
      "EGLC": {
        "pnl": 4200.00,
        "roi": 18.75,
        "win_rate": 61.64
      }
    },
    "by_timing": {
      "0-12_hours_before": {"pnl": 1200.00, "win_rate": 58.3},
      "12-24_hours_before": {"pnl": 2100.00, "win_rate": 62.1},
      "24-36_hours_before": {"pnl": 3500.00, "win_rate": 68.5}
    }
  },
  "market_analysis": {
    "edge_decay": {
      "avg_edge_by_market_age": [
        {"hours_before_event": 48, "avg_edge_pct": 8.5},
        {"hours_before_event": 24, "avg_edge_pct": 6.2},
        {"hours_before_event": 12, "avg_edge_pct": 3.8}
      ]
    },
    "bracket_performance": [
      {
        "bracket": "58-59°F",
        "win_rate": 40.0,
        "avg_edge_pct": 8.0,
        "pnl": 2100.00
      }
    ]
  },
  "risk_analysis": {
    "loss_patterns": {
      "forecast_error_threshold": 3.0,
      "loss_rate_above_threshold": 75.0,
      "loss_rate_below_threshold": 25.0
    },
    "large_losses": [
      {
        "date": "2025-11-10",
        "station": "KLGA",
        "pnl": -450.00,
        "forecast_error_f": 4.2,
        "edge_pct": 12.5
      }
    ]
  }
}
```

#### **2. CSV (Tabular Data)**

**Format**: Multiple CSV files for different analysis types

**Use Case**: Best for spreadsheet analysis, simple LLM ingestion

**Files**:
- `forecast_accuracy.csv`: All predictions vs. actuals
- `trading_performance.csv`: All trades with outcomes
- `market_analysis.csv`: Market probabilities over time
- `summary_metrics.csv`: Aggregated metrics by station/period

**Example `forecast_accuracy.csv`**:
```csv
date,station,predicted_high_f,actual_high_f,error_f,forecast_age_hours,forecast_time_utc
2025-11-16,EGLC,44.6,44.8,0.2,4.5,2025-11-16T09:18:00Z
2025-11-16,EGLC,44.8,44.8,0.0,2.1,2025-11-16T11:30:00Z
2025-11-15,KLGA,52.3,51.8,-0.5,6.2,2025-11-15T08:15:00Z
```

#### **3. Markdown Report (Human-Readable)**

**Format**: Comprehensive markdown report with insights

**Use Case**: Best for sharing with LLMs for summary/analysis, human review

**Example Structure**:
```markdown
# Performance Analysis Report
**Period**: October 1, 2025 - November 18, 2025
**Export Date**: November 18, 2025

## Executive Summary
- Total Trades: 156
- Win Rate: 63.12%
- ROI: 17.61%
- Total P&L: $8,240.00

## Forecast Accuracy
- Overall MAE: 1.2°F
- Overall RMSE: 1.8°F
- Correlation: 0.87

### By Station
- EGLC (London): MAE 0.8°F, RMSE 1.1°F
- KLGA (NYC): MAE 1.4°F, RMSE 2.0°F

### By Forecast Age
- 0-6 hours: MAE 0.9°F, Accuracy 92.5%
- 6-12 hours: MAE 1.2°F, Accuracy 88.3%
- 12-24 hours: MAE 1.6°F, Accuracy 82.1%

## Trading Performance
[Detailed sections with tables and insights]
```

#### **4. Prompt-Ready Text (LLM-Optimized)**

**Format**: Plain text optimized for LLM prompts

**Use Case**: Best for direct pasting into LLM chat interfaces

**Example**:
```
PERFORMANCE ANALYSIS DATA
Period: October 1, 2025 - November 18, 2025

FORECAST ACCURACY:
- Overall MAE: 1.2°F
- Overall RMSE: 1.8°F
- Correlation: 0.87

By Station:
- EGLC (London): MAE 0.8°F, RMSE 1.1°F, 45 trades
- KLGA (NYC): MAE 1.4°F, RMSE 2.0°F, 38 trades

By Forecast Age:
- 0-6 hours before event: MAE 0.9°F, Accuracy 92.5%
- 6-12 hours before event: MAE 1.2°F, Accuracy 88.3%
- 12-24 hours before event: MAE 1.6°F, Accuracy 82.1%

TRADING PERFORMANCE:
- Total Trades: 156
- Win Rate: 63.12%
- ROI: 17.61%
- Total P&L: $8,240.00

By Timing:
- 0-12 hours before event: Win Rate 58.3%, P&L $1,200
- 12-24 hours before event: Win Rate 62.1%, P&L $2,100
- 24-36 hours before event: Win Rate 68.5%, P&L $3,500

KEY INSIGHTS:
1. Zeus is most accurate within 6 hours of event
2. Trading 24-36 hours before event yields best results
3. Forecast errors > 3°F lead to 75% loss rate
```

### **Export Options**

**UI Controls**:
```
┌─────────────────────────────────────────────────────────┐
│ Export Performance Data                                  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Period: [Last 30 Days ▼]                                │
│ Stations: [All ▼]  [EGLC] [KLGA] [KORD]                │
│                                                          │
│ Format:                                                  │
│ ○ JSON (Structured)                                      │
│ ○ CSV (Tabular)                                          │
│ ○ Markdown Report                                        │
│ ○ Prompt-Ready Text                                      │
│                                                          │
│ Include:                                                 │
│ ☑ Forecast Accuracy Data                                │
│ ☑ Trading Performance Data                              │
│ ☑ Market Analysis Data                                  │
│ ☑ Risk Analysis Data                                    │
│ ☑ Summary Metrics                                       │
│                                                          │
│ [Export] [Cancel]                                       │
└─────────────────────────────────────────────────────────┘
```

### **LLM Prompt Templates**

**Included with exports**: Suggested prompt templates for common LLM analysis tasks

**Example Template**:
```
You are a trading performance analyst. Analyze the following performance data and provide:

1. Key insights and patterns
2. Recommendations for improvement
3. Risk factors to watch
4. Optimal trading strategies based on the data

[PASTE EXPORTED DATA HERE]

Please provide a comprehensive analysis with actionable recommendations.
```

### **API Endpoint**

**Future**: REST API endpoint for programmatic export

```
GET /api/performance/export
Query params:
  - format: json | csv | markdown | text
  - start_date: YYYY-MM-DD
  - end_date: YYYY-MM-DD
  - stations: comma-separated list
  - include: comma-separated list (forecast_accuracy, trading_performance, etc.)
```

---

## 📋 Page Naming Summary

### **Portfolio Page** (Account Status)
- **Focus**: Account balances, P&L, trade history
- **Purpose**: Track portfolio value and account status
- **Data**: Account balances, overall P&L, trade history table

### **Performance Page** (Performance Analysis)
- **Focus**: Forecast accuracy, timing, patterns, optimization
- **Purpose**: Analyze performance to improve trading
- **Data**: Forecast accuracy, timing analysis, risk patterns
- **Sub-pages**:
  - Historical View (Micro: Station/day)
  - Dashboard (Macro: System-wide)
  - Analytics (Macro: Specialized analysis)

**Key Distinction**:
- **Portfolio** = "How much money do I have?" (account status)
- **Performance** = "How well am I trading?" (analysis and optimization)

---

**Last Updated**: November 18, 2025

