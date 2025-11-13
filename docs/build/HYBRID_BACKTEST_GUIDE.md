# Hybrid Backtesting System - Price Snapshots + Resolution-Only Mode

**Date**: 2025-11-12  
**Purpose**: Enable backtesting with or without price history

---

## Overview

Hermes now supports **two backtesting modes** that automatically adapt based on data availability:

1. **Full Backtest** (with prices) - Complete edge calculation + P&L
2. **Resolution-Only** (without prices) - Zeus accuracy validation only

---

## The Problem We Solved

### Polymarket Price History Limitations:

**Issue**: Polymarket doesn't provide price history for all markets
- `/prices-history` API returns empty data for many temperature markets
- Even CLOB-enabled markets with volume lack historical prices
- Makes backtesting historical dates impossible

**Our Solution**: **Hybrid approach**
- Save our OWN price snapshots during paper trading
- Use saved prices for future backtests (full mode)
- Fallback to resolution-only when prices unavailable
- Build complete price database over time

---

## How It Works

### Architecture:

```
Paper Trading (Daily):
  └─ Place trades
  └─ Save prices to data/price_snapshots/{date}/{station}_prices.json
  
Backtesting (Next Day):
  ├─ Check for saved prices first
  │  ├─ If found → Full backtest (edges + P&L)
  │  └─ If not found → Check Polymarket API
  │     ├─ If available → Full backtest
  │     └─ If unavailable → Resolution-only mode ✅
```

---

## Mode 1: Full Backtest (With Prices)

### When Used:
- Saved prices available from paper trading
- OR Polymarket has price history
- OR Market is still open

### What It Does:
```
1. Get market prices (saved or API)
2. Calculate edges (Zeus prob - Market prob - fees)
3. Size positions (Kelly criterion)
4. Simulate trades
5. Resolve outcomes (Polymarket)
6. Calculate P&L
```

### Output:
```csv
date,station,bracket,zeus_prob,market_prob,edge,size_usd,outcome,realized_pnl
2025-11-12,EGLC,61-62°F,0.2790,0.0005,0.2705,300.00,win,179400.00
```

### Metrics:
- ✅ Hit rate
- ✅ ROI
- ✅ Edge realization
- ✅ P&L

---

## Mode 2: Resolution-Only (Without Prices)

### When Used:
- No saved prices
- AND Polymarket price history unavailable
- AND Market is closed

### What It Does:
```
1. Get Zeus probabilities only
2. Skip edge calculation (no market prices)
3. Track ALL brackets (not just edges)
4. Resolve outcomes (Polymarket)
5. Validate Zeus accuracy
```

### Output:
```csv
date,station,bracket,zeus_prob,market_prob,edge,size_usd,outcome,realized_pnl
2025-11-11,EGLC,54-55°F,0.1520,,0.00,0.00,loss,0.00
2025-11-11,EGLC,56-57°F,0.2130,,0.00,0.00,loss,0.00
2025-11-11,EGLC,58-59°F,0.4898,,0.00,0.00,win,0.00
2025-11-11,EGLC,60-61°F,0.1225,,0.00,0.00,loss,0.00
2025-11-11,EGLC,62-63°F,0.0306,,0.00,0.00,loss,0.00
```

### Metrics:
- ✅ Zeus hit rate (did highest prob bracket win?)
- ✅ Zeus accuracy (how often was Zeus right?)
- ❌ No ROI (no prices)
- ❌ No edge realization (no market comparison)

### Value:
- Validates Zeus forecast quality
- Tests probability calibration
- Identifies which bracket ranges Zeus predicts best
- Builds confidence in forecast model

---

## Price Snapshot System

### Paper Trading Auto-Saves Prices:

When you run:
```bash
python -m core.orchestrator --mode paper --stations EGLC,KLGA
```

Automatically saves to:
```
data/price_snapshots/2025-11-12/
├── EGLC_prices.json
└── KLGA_prices.json
```

### Price Snapshot Format:

```json
[
  {
    "market_id": "88296415525125615847535417447891699972...",
    "bracket_name": "58-59°F",
    "lower_f": 58,
    "upper_f": 59,
    "p_mkt": 0.5234,
    "timestamp": "2025-11-12T09:15:23.456789"
  },
  {
    "market_id": "77721079685574295866511575253970161027...",
    "bracket_name": "59-60°F",
    "lower_f": 59,
    "upper_f": 60,
    "p_mkt": 0.4123,
    "timestamp": "2025-11-12T09:15:24.123456"
  }
]
```

### Benefits:
- ✅ Complete price history for YOUR trades
- ✅ Exact prices you would have traded at
- ✅ No dependency on Polymarket data
- ✅ Builds over time automatically

---

## Workflow Examples

### Daily Workflow (Recommended):

```bash
# Morning: Run paper trading
python -m core.orchestrator --mode paper --stations EGLC,KLGA
# → Saves prices to data/price_snapshots/2025-11-12/

# Next day: Backtest yesterday
python -m core.orchestrator --mode backtest \
  --start 2025-11-12 --end 2025-11-12 --stations EGLC
# → Uses saved prices → Full backtest ✅
# → Resolution works → Real P&L ✅
```

### Historical Backtest (Resolution-Only):

```bash
# For dates you didn't paper trade:
python -m core.orchestrator --mode backtest \
  --start 2025-11-11 --end 2025-11-11 --stations EGLC

# Output:
# ⚠️  No market prices available - using RESOLUTION-ONLY mode
# Will validate Zeus accuracy without P&L calculation
# 
# Tracks 5 brackets
# Resolves outcomes
# Shows which bracket won
# Validates Zeus probability calibration
```

---

## Console Output Examples

### Full Backtest (With Prices):

```
[INFO] Backtesting 2025-11-12...
[INFO] Prices available: 5/5 brackets
[INFO] 🧠 Using Spread model (default)
[INFO] Sizing positions: 5 brackets, bankroll=$3000.00
[INFO]   Backtest trade: 61-62°F edge=27.0% size=$300.00
[INFO] ✅ WIN: 61-62°F on 2025-11-12 (winner: 61-62) → +$179,400.00

BACKTEST SUMMARY
──────────────────────────────────────────────────────────────────
Wins: 1 | Losses: 0 | Pending: 0
Total P&L: +$179,400.00
ROI: +59,800.0%
Hit Rate: 100.0%
```

### Resolution-Only (No Prices):

```
[INFO] Backtesting 2025-11-11...
[INFO] Prices available: 0/5 brackets
[INFO] ⚠️  No market prices available - using RESOLUTION-ONLY mode
[INFO]    Will validate Zeus accuracy without P&L calculation
[INFO]    Resolution-only: Tracking all brackets for Zeus validation
[INFO] ❌ LOSS: 54-55°F on 2025-11-11 (winner: 58-59) → $0.00
[INFO] ❌ LOSS: 56-57°F on 2025-11-11 (winner: 58-59) → $0.00
[INFO] ✅ WIN: 58-59°F on 2025-11-11 (winner: 58-59) → $0.00
[INFO] ❌ LOSS: 60-61°F on 2025-11-11 (winner: 58-59) → $0.00

BACKTEST SUMMARY
──────────────────────────────────────────────────────────────────
Brackets Tracked: 5
Zeus Correct: 1 (58-59°F had highest probability)
Hit Rate: 20.0% (1 win / 5 brackets)
```

---

## Benefits of Hybrid System

### 1. **No Data Loss**
- Paper trading builds your own price database
- Never depend on Polymarket historical data
- Complete records for every trade

### 2. **Always Can Backtest**
- With prices → Full analysis
- Without prices → Still validates Zeus
- Never blocked by missing data

### 3. **Forward-Looking Performance**
- Week 1: 7 days of paper trades with prices
- Week 2: Can backtest Week 1 with full data
- Month 1: Complete performance history
- Better than historical backtests (real conditions)

### 4. **Flexible Analysis**
- Full mode: Test trading strategies
- Resolution-only: Validate forecast model
- Compare: Spread vs Bands probability models

---

## Data Flow Diagram

```
DAY 1 (Nov 12):
  Paper Trading
    ├─ Zeus forecast
    ├─ Polymarket markets (open)
    ├─ Calculate edges
    ├─ Place paper trades
    └─ 💾 Save prices → data/price_snapshots/2025-11-12/EGLC_prices.json
  
DAY 2 (Nov 13):
  Backtest Nov 12
    ├─ Zeus forecast (from snapshot)
    ├─ Load saved prices ✅ (from Day 1)
    ├─ Calculate edges (using saved prices)
    ├─ Resolution (markets closed now)
    └─ Calculate P&L → Full backtest! ✅

Historical Date (Nov 5-11):
  Backtest Nov 11
    ├─ Zeus forecast
    ├─ No saved prices (didn't paper trade)
    ├─ Polymarket price history unavailable
    ├─ Switch to resolution-only mode ⚠️
    ├─ Track all brackets
    ├─ Resolution (markets closed)
    └─ Zeus validation only (no P&L)
```

---

## Resolution-Only Validation

### What You Learn:

Even without prices, resolution-only mode tells you:

**1. Zeus Forecast Accuracy**:
```
Did Zeus predict the correct bracket?
- Highest probability bracket: 58-59°F (48.98%)
- Actual outcome: 58-59°F
- ✅ Zeus was correct!
```

**2. Probability Calibration**:
```
Over 100 backtests:
- Brackets Zeus gave 50% probability → Won 52% of time ✅
- Brackets Zeus gave 20% probability → Won 18% of time ✅
- Model is well-calibrated!
```

**3. Model Comparison**:
```
Spread Model Hit Rate: 55%
Bands Model Hit Rate: 58%
→ Bands model slightly better, switch to it!
```

**4. Bracket Performance**:
```
Zeus accuracy by temperature range:
- [54-58°F]: 62% hit rate
- [58-62°F]: 58% hit rate
- [62-66°F]: 45% hit rate
→ Zeus better at predicting lower temps
```

---

## CSV Output Comparison

### Full Backtest (With Prices):
```csv
date,station,bracket,zeus_prob,market_prob_open,edge,size_usd,outcome,realized_pnl
2025-11-12,EGLC,61-62°F,0.2790,0.0005,0.2705,300.00,win,179400.00
```

### Resolution-Only (No Prices):
```csv
date,station,bracket,zeus_prob,market_prob_open,edge,size_usd,outcome,realized_pnl
2025-11-11,EGLC,54-55°F,0.1520,,,0.00,0.00,loss,0.00
2025-11-11,EGLC,56-57°F,0.2130,,,0.00,0.00,loss,0.00
2025-11-11,EGLC,58-59°F,0.4898,,,0.00,0.00,win,0.00
2025-11-11,EGLC,60-61°F,0.1225,,,0.00,0.00,loss,0.00
2025-11-11,EGLC,62-63°F,0.0306,,,0.00,0.00,loss,0.00
```

**Note**: Empty `market_prob_open` indicates resolution-only mode

---

## Usage Guide

### Setup (One-Time):

The system is already configured! No setup needed.

### Daily Routine:

```bash
# 1. Morning: Paper trade (saves prices)
python -m core.orchestrator --mode paper --stations EGLC,KLGA

# 2. Next day: Backtest yesterday (uses saved prices)
python -m core.orchestrator --mode backtest \
  --start 2025-11-12 --end 2025-11-12 --stations EGLC,KLGA

# 3. View results
cat data/runs/backtests/2025-11-12_to_2025-11-12.csv
```

### Historical Analysis (Resolution-Only):

```bash
# Backtest dates you didn't paper trade
python -m core.orchestrator --mode backtest \
  --start 2025-11-05 --end 2025-11-11 --stations EGLC

# Will use resolution-only mode
# Validates Zeus, but no P&L
```

---

## File Structure

```
data/
├── price_snapshots/        ← NEW! Your own price history
│   ├── 2025-11-12/
│   │   ├── EGLC_prices.json
│   │   └── KLGA_prices.json
│   ├── 2025-11-13/
│   │   ├── EGLC_prices.json
│   │   └── KLGA_prices.json
│   └── ...
│
├── trades/                 ← Paper trade logs
│   └── 2025-11-12/
│       └── paper_trades.csv
│
└── runs/backtests/         ← Backtest results
    ├── 2025-11-12_to_2025-11-12.csv  (full mode)
    └── 2025-11-11_to_2025-11-11.csv  (resolution-only)
```

---

## Price Snapshot JSON Format

```json
[
  {
    "market_id": "88296415525125615847535417447891699972354430949414428269646749537178918343685",
    "bracket_name": "58-59°F",
    "lower_f": 58,
    "upper_f": 59,
    "p_mkt": 0.5234,
    "timestamp": "2025-11-12T09:15:23.456789"
  }
]
```

**Fields**:
- `market_id`: Polymarket CLOB token ID
- `bracket_name`: Human-readable bracket
- `lower_f`, `upper_f`: Temperature bounds
- `p_mkt`: Market probability at trade time
- `timestamp`: When price was captured

---

## Resolution-Only Validation Metrics

### Zeus Accuracy Analysis:

```python
# From resolution-only backtests, calculate:

# 1. Did Zeus pick the right bracket?
zeus_correct = (highest_prob_bracket == winning_bracket)

# 2. Probability calibration
# For brackets Zeus gave 50% probability:
actual_win_rate = wins / total_trades  # Should be ~50%

# 3. Forecast quality
# Average Zeus probability for winning brackets
avg_winning_prob = mean(zeus_prob for winning_brackets)
# Should be > 20% (1/num_brackets) if Zeus adds value
```

### Example Analysis:

```
Resolution-Only Backtest: Nov 5-11 (7 days × 5 brackets = 35 data points)

Zeus Predictions:
  - Highest prob bracket won: 3/7 days (43%)
  - Top 2 brackets won: 6/7 days (86%)
  - Average winning bracket Zeus prob: 38%
  - Random chance: 20% (1/5 brackets)

Conclusion:
  ✅ Zeus adds value (38% > 20% random)
  ✅ Model is somewhat calibrated
  ⚠️  Could improve (only 43% hit on top bracket)
```

---

## Advantages Over Traditional Backtesting

| Aspect | Traditional (Polymarket Data) | Hybrid (Our Approach) |
|--------|------------------------------|----------------------|
| **Price History** | Depends on Polymarket | We build our own |
| **Data Coverage** | Sparse, many gaps | Complete for our trades |
| **Accuracy** | Unknown execution prices | Exact prices we saw |
| **Historical** | Can backtest past | Only forward-looking |
| **No Price Data** | Can't backtest | Resolution-only mode |
| **Flexibility** | Limited by data | Always works |

---

## Configuration

### Enable/Disable Price Saving:

Price snapshots are **enabled by default** in paper trading.

To disable (not recommended):
```python
# In core/orchestrator.py
broker = PaperBroker(save_prices=False)
```

### Storage Location:

Default: `data/price_snapshots/`

Customize:
```python
broker = PaperBroker()
broker.prices_dir = custom_path
```

---

## Future Enhancements

### 1. **Price History API** (if Polymarket improves):
```python
# If Polymarket adds better price history:
if use_polymarket_history and polymarket_has_data:
    return polymarket_prices
else:
    return saved_prices or resolution_only_mode
```

### 2. **Resolution-Only P&L Estimation**:
```python
# Estimate P&L even without prices:
# Assume market priced at Zeus probability
estimated_market_prob = zeus_prob
edge = 0  # No edge (neutral assumption)
# Still calculate win/loss for calibration
```

### 3. **Interpolated Prices**:
```python
# If we have prices for some brackets but not all:
# Interpolate missing prices from known ones
```

---

## Success Criteria

✅ **All criteria met**:
- ✅ Paper trading saves price snapshots
- ✅ Backtester checks for saved prices first
- ✅ Falls back to Polymarket API if no saved prices
- ✅ Resolution-only mode when no prices available
- ✅ All modes tested and working
- ✅ Backward compatible (existing tests pass)
- ✅ Resolution works in both modes

---

## Quick Reference

### Commands:

```bash
# Paper trade (saves prices)
python -m core.orchestrator --mode paper --stations EGLC,KLGA

# Full backtest (next day, has prices)
python -m core.orchestrator --mode backtest \
  --start 2025-11-12 --end 2025-11-12 --stations EGLC

# Resolution-only (historical, no prices)
python -m core.orchestrator --mode backtest \
  --start 2025-11-11 --end 2025-11-11 --stations EGLC

# Check saved prices
cat data/price_snapshots/2025-11-12/EGLC_prices.json

# View backtest results
cat data/runs/backtests/2025-11-12_to_2025-11-12.csv
```

---

## Conclusion

The hybrid backtesting system solves Polymarket's price history limitations by:
1. Building our own price database through paper trading
2. Using saved prices for complete backtests when available
3. Falling back to resolution-only mode for Zeus validation

This approach provides **better data than Polymarket's history** (exact prices we traded at) while still enabling validation even for dates without price data.

**Result**: Always-working backtest system that builds comprehensive performance history over time.

---

**Documentation**: Harvey Ando  
**Implementation**: Hermes v1.0.0  
**Date**: November 12, 2025

