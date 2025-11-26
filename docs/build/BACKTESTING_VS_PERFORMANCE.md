# Backtesting vs. Performance: Key Differences

**Purpose**: Clarify the distinction between Backtesting and Performance analysis  
**Date**: November 18, 2025

---

## 🎯 Core Distinction

### **Backtesting** = "What IF?"
- **Simulated/hypothetical** performance
- Tests different parameters/models on historical data
- Shows what **would have happened** if you used different settings
- Used **BEFORE** making changes to optimize parameters
- **Focus**: Parameter optimization and strategy testing

### **Performance** = "What ACTUALLY Happened?"
- **Real/actual** performance from executed trades
- Analyzes what **actually happened** with your current settings
- Shows results from **real trades** (paper or live)
- Used **AFTER** trades to understand what worked/didn't work
- **Focus**: Understanding actual results and identifying patterns

---

## 📊 Detailed Comparison

### Backtesting

**What it does**:
- Runs simulations on historical data
- Tests different parameter combinations
- Compares different models (spread vs. bands)
- Shows hypothetical P&L, win rate, ROI
- Helps you **choose** optimal parameters

**When you use it**:
- Before changing trading parameters
- When testing new strategies
- When comparing models
- When optimizing edge_min, kelly_cap, etc.

**Example Questions**:
- "What if I used edge_min=2% instead of 3%?"
- "Which model is better: spread or bands?"
- "What's the optimal kelly_cap for maximum returns?"

**Output**:
- Simulated trades (not real)
- Hypothetical P&L
- Parameter comparison
- "Best" parameter recommendations

---

### Performance Page

**What it does**:
- Analyzes **actual executed trades**
- Shows real forecast accuracy
- Identifies patterns in real performance
- Analyzes timing of real trades
- Helps you **understand** what happened

**When you use it**:
- After trades have been executed
- To review daily/weekly performance
- To understand why trades won/lost
- To identify patterns and trends
- To improve future decisions

**Example Questions**:
- "Was Zeus accurate for yesterday's trades?"
- "When did we actually trade, and was that optimal?"
- "Which stations performed best in reality?"
- "What caused our losses?"

**Output**:
- Real trade outcomes
- Actual forecast accuracy
- Real timing analysis
- Actual performance patterns

---

## 🔄 Workflow: How They Work Together

### Step 1: Backtesting (Before Trading)
```
1. Run backtest with different parameters
2. Compare results
3. Choose optimal parameters
4. Update config with best parameters
```

### Step 2: Trading (Execute)
```
1. System trades with chosen parameters
2. Trades are executed (paper or live)
3. Results are recorded
```

### Step 3: Performance Analysis (After Trading)
```
1. Review actual performance
2. Analyze what worked/didn't work
3. Identify patterns
4. Use insights to inform next backtest
```

### Step 4: Iterate
```
1. Use Performance insights to refine backtest
2. Test new parameters based on real results
3. Update config
4. Trade again
5. Analyze performance again
```

---

## 📋 Specific Feature Comparison

### Backtesting Features

**What it shows**:
- ✅ Simulated trades with different parameters
- ✅ Hypothetical P&L for each parameter set
- ✅ Win rate comparison
- ✅ ROI comparison
- ✅ Parameter sensitivity analysis
- ✅ Model comparison (spread vs. bands)

**What it doesn't show**:
- ❌ Actual forecast accuracy (uses historical forecasts)
- ❌ Real trade timing
- ❌ Actual market behavior
- ❌ Real slippage/costs
- ❌ Actual execution issues

---

### Performance Page Features

**What it shows**:
- ✅ **Actual forecast accuracy** (Zeus predictions vs. METAR actuals)
- ✅ **Real trade timing** (when trades were actually placed)
- ✅ **Actual market behavior** (how markets actually moved)
- ✅ **Real outcomes** (what actually happened)
- ✅ **Pattern identification** (what conditions lead to wins/losses)
- ✅ **Timing analysis** (optimal entry windows based on real data)

**What it doesn't show**:
- ❌ Hypothetical "what if" scenarios
- ❌ Parameter optimization
- ❌ Model comparison
- ❌ Simulated trades

---

## 🎯 Key Use Cases

### Use Backtesting When:

1. **Optimizing Parameters**
   - "What's the best edge_min value?"
   - "Should I use kelly_cap=0.10 or 0.15?"
   - "What's the optimal liquidity_min_usd?"

2. **Comparing Models**
   - "Is spread model or bands model better?"
   - "Which zeus_likely_pct gives best results?"

3. **Testing Strategies**
   - "What if I only trade 24-36 hours before event?"
   - "What if I increase per_market_cap?"

4. **Before Making Changes**
   - Test changes before applying them
   - Validate improvements

---

### Use Performance Page When:

1. **Understanding Results**
   - "Why did we lose money yesterday?"
   - "Was Zeus accurate for that trade?"
   - "What went wrong?"

2. **Identifying Patterns**
   - "When are we most profitable?"
   - "Which stations perform best?"
   - "What conditions lead to losses?"

3. **Reviewing Performance**
   - Daily/weekly/monthly reviews
   - Understanding actual results
   - Learning from real trades

4. **Informing Future Backtests**
   - Use real insights to improve backtest scenarios
   - Identify parameters to test
   - Understand what actually matters

---

## 💡 Example Scenario

### Scenario: Optimizing Trading Strategy

**Step 1: Backtesting**
```
Question: "What's the best edge_min value?"

Run backtests:
- edge_min=2%: Simulated ROI = 15.2%
- edge_min=3%: Simulated ROI = 17.8%
- edge_min=4%: Simulated ROI = 16.1%

Decision: Use edge_min=3% (best simulated ROI)
```

**Step 2: Trading**
```
System trades with edge_min=3%
Executes real trades (paper or live)
Records actual results
```

**Step 3: Performance Analysis**
```
Review actual performance:
- Actual ROI = 14.5% (lower than backtest!)
- Forecast accuracy was poor on some days
- Trades placed at suboptimal times

Insights:
- Backtest assumed perfect forecast accuracy
- Real trades had timing issues
- Some stations underperformed
```

**Step 4: Iterate**
```
Use Performance insights:
- Backtest with forecast accuracy filters
- Test timing-based strategies
- Exclude underperforming stations

Run new backtest with insights
Update parameters
Trade again
Analyze performance again
```

---

## 🔍 Overlap & Synergy

### Where They Overlap

Both analyze **historical data**, but:
- **Backtesting**: Uses historical data to simulate trades
- **Performance**: Uses historical data to analyze actual trades

### How They Work Together

1. **Backtesting informs Performance**
   - Backtest results help set expectations
   - "Backtest said 17.8% ROI, Performance shows 14.5% - why the gap?"

2. **Performance informs Backtesting**
   - Real insights improve backtest scenarios
   - "Performance shows timing matters - test timing filters in backtest"

3. **Continuous Improvement Loop**
   ```
   Backtest → Choose Parameters → Trade → Analyze Performance
                                                      ↓
   Refine Backtest ← Use Insights ← Identify Patterns
   ```

---

## 📊 Visual Comparison

### Backtesting Dashboard
```
┌─────────────────────────────────────────────────────────┐
│ Backtest Results                                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Parameter Set 1: edge_min=2%                            │
│   Simulated ROI: 15.2%                                  │
│   Simulated P&L: $7,600                                 │
│                                                          │
│ Parameter Set 2: edge_min=3%  ← BEST                    │
│   Simulated ROI: 17.8%                                  │
│   Simulated P&L: $8,900                                 │
│                                                          │
│ Parameter Set 3: edge_min=4%                            │
│   Simulated ROI: 16.1%                                  │
│   Simulated P&L: $8,050                                 │
│                                                          │
│ [Use edge_min=3%]                                       │
└─────────────────────────────────────────────────────────┘
```

### Performance Dashboard
```
┌─────────────────────────────────────────────────────────┐
│ Performance Overview                                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Actual ROI: 14.5%                                       │
│ Actual P&L: $7,250                                      │
│                                                          │
│ Forecast Accuracy:                                      │
│   MAE: 1.2°F                                            │
│   RMSE: 1.8°F                                           │
│                                                          │
│ Timing Analysis:                                        │
│   Optimal: 24-36 hours before event                     │
│   Actual: Mixed timing                                  │
│                                                          │
│ Key Insights:                                           │
│   • Forecast errors caused some losses                  │
│   • Timing could be improved                            │
│                                                          │
│ [Export Data] [View Analytics]                          │
└─────────────────────────────────────────────────────────┘
```

---

## ✅ Summary

### Backtesting
- **Purpose**: Optimize parameters before trading
- **Data**: Historical data (simulated trades)
- **Output**: "What would happen if..."
- **Use**: Before making changes
- **Focus**: Parameter optimization

### Performance
- **Purpose**: Understand actual results after trading
- **Data**: Real executed trades
- **Output**: "What actually happened and why..."
- **Use**: After trades execute
- **Focus**: Pattern identification and learning

### Key Insight

**Backtesting** helps you **choose** the best parameters.  
**Performance** helps you **understand** what actually happened and **learn** from it.

They work together in a continuous improvement loop:
1. Backtest to find optimal parameters
2. Trade with those parameters
3. Analyze performance to understand results
4. Use insights to improve next backtest
5. Repeat

---

**Last Updated**: November 18, 2025


