# Performance & Portfolio Page - Paper vs Live Trading

**Date**: November 17, 2025  
**Purpose**: Explain how the Performance & Portfolio page works with both paper trading and live trading modes

---

## 🎯 Overview

The Performance & Portfolio page must handle **two distinct trading modes**:

1. **Paper Trading** - Simulated trades, no real money at risk
2. **Live Trading** - Real trades, real money, real account balances

The page should clearly distinguish between these modes and provide appropriate metrics for each.

---

## 📊 Mode-Specific Behavior

### Paper Trading Mode

**Characteristics**:
- ✅ Simulated trades (no real execution)
- ✅ No real account balances
- ✅ Outcomes resolved from Polymarket after event
- ✅ P&L is theoretical (what would have happened)
- ✅ Safe for testing and strategy validation

**Data Sources**:
- Paper trade CSV files (`data/trades/{date}/paper_trades.csv`)
- Polymarket resolution API (to determine win/loss)
- No account balance API needed

**P&L Calculation**:
- Based on resolved outcomes from Polymarket
- Theoretical profit/loss (not real money)
- Can be calculated retroactively for any past trade

---

### Live Trading Mode

**Characteristics**:
- ✅ Real trades executed on Polymarket/Kalshi
- ✅ Real account balances (from exchange APIs)
- ✅ Real P&L (affects actual account)
- ✅ Outcomes determined by exchange settlement
- ✅ Real money at risk

**Data Sources**:
- Live trade execution records (from exchange APIs)
- Account balance APIs (Polymarket, Kalshi)
- Exchange settlement data (for outcomes)
- Real-time balance updates

**P&L Calculation**:
- Based on actual trade execution and settlement
- Real profit/loss (affects account balance)
- Can only be calculated after trade settlement

---

## 🎨 UI Design: Mode Toggle

### Page Header with Mode Selector

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 💰 Performance & Portfolio Overview                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Mode: [● Paper Trading] [○ Live Trading]                                   │
│                                                                             │
│ ⚠️  Paper Trading Mode: Showing simulated trades and theoretical P&L       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Or**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 💰 Performance & Portfolio Overview                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Mode: [● Live Trading] [○ Paper Trading]                                   │
│                                                                             │
│ ✅ Live Trading Mode: Showing real trades and actual account balances      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📋 Section-by-Section Behavior

### 1. Account Balances Section

#### Paper Trading Mode

**Display**:
```
┌─────────────────────────────────────────────────────────────────────────┐
│ 📊 ACCOUNT BALANCES (Paper Trading)                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ⚠️  Paper Trading Mode - No Real Account Balances                     │
│                                                                         │
│  Simulated Starting Balance:  $10,000.00                               │
│  Current Simulated Balance:   $11,234.56  (+$1,234.56)                │
│  Total P&L (Theoretical):     +$1,234.56                               │
│                                                                         │
│  Note: These are simulated balances for testing purposes only.         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Data Source**:
- Starting balance from config (`daily_bankroll_cap` or separate paper balance)
- Current balance = Starting balance + Total P&L
- No API calls to exchanges

**Implementation**:
```typescript
// Paper trading mode
const startingBalance = config.paper_starting_balance || 10000;
const currentBalance = startingBalance + totalPnl;
```

---

#### Live Trading Mode

**Display**:
```
┌─────────────────────────────────────────────────────────────────────────┐
│ 📊 ACCOUNT BALANCES (Live Trading)                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Polymarket:  $5,000.00  (Available: $3,500.00 | Allocated: $1,500.00) │
│  Kalshi:      $3,000.00  (Available: $3,000.00 | Allocated: $0.00)     │
│  ─────────────────────────────────────────────────────────────────────  │
│  Total:       $8,000.00  (Available: $6,500.00 | Allocated: $1,500.00) │
│                                                                         │
│  Last Updated: Nov 17, 2025 14:30 UTC                                  │
│  [Refresh Balances]                                                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Data Source**:
- Real-time API calls to Polymarket account API
- Real-time API calls to Kalshi account API
- Actual account balances from exchanges

**Implementation**:
```typescript
// Live trading mode
const balances = await fetch('/api/accounts/balances');
// Returns real balances from exchange APIs
```

---

### 2. Profit & Loss Section

#### Paper Trading Mode

**Display**:
```
┌─────────────────────────────────────────────────────────────────────────┐
│ 📈 PROFIT & LOSS (Paper Trading - Theoretical)                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Period: [Today ▼] [This Week] [This Month] [This Year] [All Time]    │
│                                                                         │
│  ⚠️  Theoretical P&L (Based on resolved outcomes)                      │
│                                                                         │
│  Total P&L:     +$1,234.56  ▲ 12.35%                                   │
│  Total Risk:    $10,000.00                                             │
│  ROI:           +12.35%                                                │
│                                                                         │
│  Note: This is what would have happened if trades were executed.       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Data Source**:
- Paper trades from CSV
- Outcomes resolved from Polymarket (after event)
- P&L calculated based on resolved outcomes

**Calculation**:
```python
# For each paper trade:
if outcome == "win":
    pnl = (1 / market_prob_open - 1) * size_usd
elif outcome == "loss":
    pnl = -size_usd
else:  # pending
    pnl = 0
```

---

#### Live Trading Mode

**Display**:
```
┌─────────────────────────────────────────────────────────────────────────┐
│ 📈 PROFIT & LOSS (Live Trading - Actual)                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Period: [Today ▼] [This Week] [This Month] [This Year] [All Time]    │
│                                                                         │
│  ✅ Real P&L (From actual trade execution and settlement)              │
│                                                                         │
│  Total P&L:     +$856.23  ▲ 8.56%                                      │
│  Total Risk:    $10,000.00                                             │
│  ROI:           +8.56%                                                 │
│                                                                         │
│  Breakdown:                                                             │
│  • Polymarket:  +$600.00  (ROI: +12.00%)                              │
│  • Kalshi:      +$256.23  (ROI: +5.12%)                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Data Source**:
- Live trades from exchange APIs
- Settlement data from exchanges
- Actual P&L from exchange records

**Calculation**:
```python
# For each live trade:
# P&L comes directly from exchange settlement
pnl = exchange_settlement_pnl  # Real money
```

---

### 3. Performance Metrics Section

#### Paper Trading Mode

**Display**:
```
┌─────────────────────────────────────────────────────────────────────────┐
│ 📊 PERFORMANCE METRICS (Paper Trading)                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ⚠️  Theoretical Performance (Based on resolved outcomes)              │
│                                                                         │
│  Total Trades:        156                                               │
│  Resolved:            141  (90.4%)                                      │
│  Pending:             15   (9.6%)                                       │
│                                                                         │
│  Win Rate:            63.12%  (89 wins / 141 resolved)                 │
│  Average Edge:        18.25%                                            │
│  ROI:                 12.35%                                            │
│                                                                         │
│  Note: These metrics show how the strategy would have performed.       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Data Source**:
- Paper trades with resolved outcomes
- Theoretical P&L calculations

---

#### Live Trading Mode

**Display**:
```
┌─────────────────────────────────────────────────────────────────────────┐
│ 📊 PERFORMANCE METRICS (Live Trading)                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ✅ Actual Performance (From real trade execution)                     │
│                                                                         │
│  Total Trades:        89                                                │
│  Resolved:            75   (84.3%)                                      │
│  Pending:             14   (15.7%)                                      │
│                                                                         │
│  Win Rate:            58.67%  (44 wins / 75 resolved)                  │
│  Average Edge:        16.50%                                            │
│  ROI:                 8.56%                                             │
│                                                                         │
│  Largest Win:         +$450.00                                          │
│  Largest Loss:        -$300.00                                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Data Source**:
- Live trades from exchange APIs
- Actual settlement data
- Real P&L from exchanges

---

### 4. Trade History Table

#### Paper Trading Mode

**Display**:
```
┌─────────────────────────────────────────────────────────────────────────┐
│ 📝 TRADE HISTORY (Paper Trading)                                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ⚠️  Simulated Trades - No Real Execution                              │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ Date       │ Station │ Bracket │ Size    │ Edge  │ Outcome │ P&L  │ │
│  ├───────────────────────────────────────────────────────────────────┤ │
│  │ Nov 17     │ EGLC    │ 58-59°F │ $300.00 │ 26.25%│ ✅ Win  │+$112 │ │
│  │ 14:21      │         │         │         │       │ (Paper) │      │ │
│  │ Nov 17     │ EGLC    │ 60-61°F │ $300.00 │ 25.75%│ ✅ Win  │+$115 │ │
│  │ 14:21      │         │         │         │       │ (Paper) │      │ │
│  │ Nov 17     │ KLGA    │ 48-49°F │ $250.00 │ 18.00%│ ⏳ Pend │  -   │ │
│  │ 14:20      │         │         │         │       │ (Paper) │      │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  Note: "Paper" indicator shows these are simulated trades.            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Data Source**:
- Paper trade CSV files
- Resolved outcomes from Polymarket

**Columns**:
- Date, Station, Bracket, Size, Edge, Outcome, P&L
- **Mode Indicator**: "Paper" badge or icon

---

#### Live Trading Mode

**Display**:
```
┌─────────────────────────────────────────────────────────────────────────┐
│ 📝 TRADE HISTORY (Live Trading)                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ✅ Real Trades - Executed on Exchange                                 │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ Date       │ Station │ Bracket │ Size    │ Edge  │ Outcome │ P&L  │ │
│  ├───────────────────────────────────────────────────────────────────┤ │
│  │ Nov 17     │ EGLC    │ 58-59°F │ $300.00 │ 26.25%│ ✅ Win  │+$112 │ │
│  │ 14:21      │         │         │         │       │ (Live)  │      │ │
│  │ Nov 17     │ EGLC    │ 60-61°F │ $300.00 │ 25.75%│ ✅ Win  │+$115 │ │
│  │ 14:21      │         │         │         │       │ (Live)  │      │ │
│  │ Nov 17     │ KLGA    │ 48-49°F │ $250.00 │ 18.00%│ ⏳ Pend │  -   │ │
│  │ 14:20      │         │         │         │       │ (Live)  │      │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  Note: "Live" indicator shows these are real executed trades.         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Data Source**:
- Live trades from exchange APIs
- Settlement data from exchanges

**Columns**:
- Date, Station, Bracket, Size, Edge, Outcome, P&L
- **Mode Indicator**: "Live" badge or icon
- **Exchange ID**: Link to trade on exchange

---

## 🔄 Combined View (Optional)

### Option: Show Both Modes Side-by-Side

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 💰 Performance & Portfolio Overview                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│ View: [● Combined] [○ Paper Only] [○ Live Only]                       │
│                                                                         │
│ ┌─────────────────────────────┬───────────────────────────────────────┐ │
│ │ 📊 PAPER TRADING            │  📊 LIVE TRADING                      │ │
│ ├─────────────────────────────┼───────────────────────────────────────┤ │
│ │                             │                                       │ │
│ │ Simulated Balance:          │  Real Balance:                        │
│ │ $11,234.56                  │  $8,856.23                            │
│ │                             │                                       │ │
│ │ Theoretical P&L:            │  Actual P&L:                          │
│ │ +$1,234.56 (12.35%)        │  +$856.23 (8.56%)                    │ │
│ │                             │                                       │ │
│ │ Win Rate: 63.12%            │  Win Rate: 58.67%                    │ │
│ │ Trades: 156                 │  Trades: 89                          │ │
│ │                             │                                       │ │
│ └─────────────────────────────┴───────────────────────────────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Use Case**: Compare paper trading performance vs live trading performance

---

## 🔧 Backend Implementation

### Mode Detection

**From Configuration**:
```python
# core/config.py
execution_mode: "paper" | "live"
```

**API Endpoint**:
```python
GET /api/status

Response:
{
  "execution_mode": "paper",  # or "live"
  "trading_engine": {...}
}
```

### Data Separation

#### Paper Trading Data
- **Storage**: `data/trades/{date}/paper_trades.csv`
- **Resolution**: Polymarket resolution API (after event)
- **P&L**: Calculated from resolved outcomes

#### Live Trading Data
- **Storage**: `data/trades/{date}/live_trades.csv` (or exchange APIs)
- **Resolution**: Exchange settlement data
- **P&L**: From exchange records

### API Endpoints

#### Paper Trading Endpoints
```
GET /api/performance/pnl?mode=paper
GET /api/performance/metrics?mode=paper
GET /api/trades/history?mode=paper
```

#### Live Trading Endpoints
```
GET /api/performance/pnl?mode=live
GET /api/performance/metrics?mode=live
GET /api/trades/history?mode=live
GET /api/accounts/balances  # Only for live mode
```

#### Combined Endpoints
```
GET /api/performance/pnl?mode=combined
GET /api/performance/metrics?mode=combined
```

---

## 📊 Data Flow

### Paper Trading Flow

```
1. Paper Trade Executed
   ↓
2. Saved to: data/trades/{date}/paper_trades.csv
   ↓
3. Event Day Arrives
   ↓
4. Polymarket Resolves Market
   ↓
5. Resolution Service Updates Trade with Outcome
   ↓
6. P&L Calculated (Theoretical)
   ↓
7. Performance Page Shows Paper Trading Data
```

### Live Trading Flow

```
1. Live Trade Executed on Exchange
   ↓
2. Exchange API Returns Trade Confirmation
   ↓
3. Saved to: data/trades/{date}/live_trades.csv
   ↓
4. Account Balance Updated (Real Money)
   ↓
5. Event Day Arrives
   ↓
6. Exchange Settles Trade
   ↓
7. Settlement Data Retrieved from Exchange
   ↓
8. P&L Recorded (Real Money)
   ↓
9. Performance Page Shows Live Trading Data
```

---

## 🎨 UI Indicators

### Visual Distinctions

**Paper Trading**:
- ⚠️ Warning icon/badge
- Yellow/amber color scheme
- "Paper" or "Simulated" labels
- Tooltip: "Theoretical P&L based on resolved outcomes"

**Live Trading**:
- ✅ Checkmark icon/badge
- Green color scheme
- "Live" or "Real" labels
- Tooltip: "Actual P&L from real trade execution"

### Color Coding

```
Paper Trading:
- Background: Light yellow/amber
- Border: Yellow
- Text: Dark amber
- Icons: ⚠️ Warning

Live Trading:
- Background: Light green
- Border: Green
- Text: Dark green
- Icons: ✅ Checkmark
```

---

## 🔐 Security Considerations

### Paper Trading Mode
- ✅ Safe to show all data
- ✅ No sensitive account information
- ✅ Can be shared/demoed

### Live Trading Mode
- ⚠️ Real account balances (sensitive)
- ⚠️ Real P&L (sensitive)
- ⚠️ Requires authentication
- ⚠️ Should not be shared publicly

**Implementation**:
- Add authentication check for live mode
- Mask sensitive data if needed
- Log access to live trading data

---

## 📝 Summary

### Key Differences

| Feature | Paper Trading | Live Trading |
|---------|--------------|--------------|
| **Account Balances** | Simulated | Real (from exchange APIs) |
| **P&L** | Theoretical | Actual |
| **Trade Execution** | Simulated | Real (on exchange) |
| **Outcome Resolution** | Polymarket API | Exchange settlement |
| **Data Source** | CSV files | Exchange APIs + CSV |
| **Risk** | None | Real money |
| **Use Case** | Testing/validation | Production trading |

### Implementation Strategy

1. **Mode Toggle**: Allow user to switch between paper/live views
2. **Data Separation**: Store paper and live trades separately
3. **API Endpoints**: Support `mode` parameter for filtering
4. **UI Indicators**: Clear visual distinction between modes
5. **Security**: Protect live trading data with authentication

---

**Next Steps**: Implement mode-aware Performance & Portfolio page with proper data separation and UI indicators.

