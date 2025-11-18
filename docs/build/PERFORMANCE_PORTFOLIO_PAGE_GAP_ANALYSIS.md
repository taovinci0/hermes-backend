# Performance & Portfolio Page - Gap Analysis

**Date**: November 17, 2025  
**Purpose**: Identify gaps between current frontend implementation and desired Performance/Portfolio overview page

---

## 🎯 User Requirement

A dedicated **Performance & Portfolio** page that provides:
- **Overall Profit & Loss** (P&L) tracking
- **Collated Trade History** (across all stations, not per-station)
- **Account Balances** (Polymarket, Kalshi)
- **Performance Metrics** (win rate, ROI, etc.)
- **High-level overview** without needing to dig into Live Dashboard or Historical pages

**Key Distinction**:
- **Live Dashboard**: Real-time, ongoing trades, current edges, forecasts
- **Historical Page**: Per-station detailed analysis with graphs
- **Performance Page**: **Aggregated overview** of system performance and account status

---

## 📊 Current Frontend Implementation

### 1. Live Trading Dashboard ✅

**What it shows**:
- Real-time trading status
- Current edges for active markets
- Zeus forecast evolution (live)
- Recent trades (per station/event day)
- Activity logs (filtered by station/day)

**What it doesn't show**:
- ❌ Overall P&L across all trades
- ❌ Account balances
- ❌ Win/loss statistics
- ❌ Performance metrics (ROI, win rate)
- ❌ Collated trade history (all stations together)

**Data Source**: 
- `/api/edges/current` - Current edges
- `/api/trades/recent` - Recent trades (filtered)
- `/api/status` - System status
- WebSocket - Real-time updates

---

### 2. Historical Data Page ✅

**What it shows**:
- Per-station historical analysis
- Three stacked graphs (Zeus/METAR, Polymarket, Trades)
- Detailed snapshot data
- Station-specific trade history

**What it doesn't show**:
- ❌ Aggregated P&L across all stations
- ❌ Overall performance metrics
- ❌ Account-level balances
- ❌ Cross-station trade history
- ❌ Portfolio-level statistics

**Data Source**:
- `/api/snapshots/zeus` - Zeus snapshots
- `/api/snapshots/polymarket` - Polymarket snapshots
- `/api/snapshots/decisions` - Decision snapshots
- `/api/trades/recent` - Trades (per station)

---

### 3. Backtest Results ✅

**What it shows**:
- Backtest P&L and ROI
- Win/loss statistics
- Trade history for backtest period
- Performance metrics

**What it doesn't show**:
- ❌ Real paper trading P&L
- ❌ Account balances
- ❌ Ongoing performance tracking
- ❌ Live account status

**Data Source**:
- `/api/backtest/results/{job_id}` - Backtest results

---

## 🔍 Gap Analysis

### Missing: Performance & Portfolio Page

**What's Needed**:

#### 1. Overall P&L Dashboard

**Required Data**:
- Total P&L (all time)
- P&L by time period (Today, Week, Month, Year, All Time)
- P&L breakdown by:
  - Station
  - Event day
  - Venue (Polymarket, Kalshi)
  - Date range

**Current Status**: ❌ **NOT AVAILABLE**

**Why**: 
- Paper trades CSV doesn't track P&L (only trade size)
- No resolution tracking for paper trades
- No aggregation service for P&L calculation

**Data Needed**:
- Resolved trade outcomes (win/loss)
- Realized P&L per trade
- Aggregated P&L by various dimensions

---

#### 2. Collated Trade History

**Required Data**:
- All trades across all stations in one view
- Sortable/filterable table
- Columns: Date, Station, Bracket, Size, Edge, Outcome, P&L
- Pagination for large datasets

**Current Status**: ⚠️ **PARTIALLY AVAILABLE**

**Why**:
- `/api/trades/recent` exists but:
  - No P&L/outcome data
  - Designed for recent trades, not full history
  - No aggregation across stations

**Data Needed**:
- Trade history with outcomes
- P&L per trade
- Better aggregation endpoint

---

#### 3. Account Balances

**Required Data**:
- Polymarket account balance (USD)
- Kalshi account balance (USD)
- Total portfolio value
- Available balance vs. allocated
- Balance history over time

**Current Status**: ❌ **NOT AVAILABLE**

**Why**:
- No account integration yet
- No balance tracking
- No API endpoints for account data

**Data Needed**:
- Account balance API endpoints
- Balance history tracking
- Integration with Polymarket/Kalshi APIs

---

#### 4. Performance Metrics

**Required Data**:
- **Win Rate**: Wins / Total Resolved Trades
- **ROI**: (Total P&L / Total Risk) * 100
- **Average Edge**: Mean edge across all trades
- **Sharpe Ratio**: Risk-adjusted returns
- **Largest Win/Loss**: Best and worst trades
- **Trade Count**: Total trades, by status (win/loss/pending)
- **Total Risk**: Sum of all trade sizes
- **Total P&L**: Sum of all realized P&L

**Current Status**: ⚠️ **PARTIALLY AVAILABLE**

**Why**:
- Backtest service has some metrics
- Paper trades don't have outcomes/P&L
- No aggregation service for live trading

**Data Needed**:
- Trade outcomes (win/loss)
- Realized P&L
- Aggregation service

---

#### 5. Trade History Table

**Required Features**:
- Sortable columns
- Filterable by:
  - Date range
  - Station
  - Outcome (win/loss/pending)
  - Venue (Polymarket/Kalshi)
- Export to CSV
- Pagination

**Current Status**: ⚠️ **PARTIALLY AVAILABLE**

**Why**:
- `/api/trades/recent` exists but limited
- No outcome/P&L data
- No advanced filtering

---

## 📋 Backend API Gaps

### Missing Endpoints

#### 1. P&L Aggregation Endpoint

**Needed**:
```
GET /api/performance/pnl
Query params:
  - start_date (optional)
  - end_date (optional)
  - station_code (optional)
  - venue (optional: 'polymarket' | 'kalshi' | 'all')

Response:
{
  "total_pnl": 1234.56,
  "total_risk": 10000.00,
  "roi": 12.35,
  "by_station": {
    "EGLC": {"pnl": 500.00, "risk": 3000.00, "roi": 16.67},
    "KLGA": {"pnl": 734.56, "risk": 7000.00, "roi": 10.49}
  },
  "by_venue": {
    "polymarket": {"pnl": 1000.00, "risk": 8000.00},
    "kalshi": {"pnl": 234.56, "risk": 2000.00}
  },
  "by_period": {
    "today": {"pnl": 50.00, "risk": 500.00},
    "week": {"pnl": 200.00, "risk": 2000.00},
    "month": {"pnl": 800.00, "risk": 8000.00},
    "all_time": {"pnl": 1234.56, "risk": 10000.00}
  }
}
```

**Status**: ❌ **NOT IMPLEMENTED**

---

#### 2. Trade History with Outcomes

**Needed**:
```
GET /api/trades/history
Query params:
  - start_date (optional)
  - end_date (optional)
  - station_code (optional)
  - venue (optional)
  - outcome (optional: 'win' | 'loss' | 'pending')
  - limit (optional, default: 100)
  - offset (optional, default: 0)

Response:
{
  "trades": [
    {
      "timestamp": "2025-11-13T14:21:10Z",
      "station_code": "EGLC",
      "bracket_name": "58-59°F",
      "size_usd": 300.00,
      "edge_pct": 26.25,
      "outcome": "win",
      "realized_pnl": 112.50,
      "venue": "polymarket",
      "market_id": "market_58_59"
    },
    ...
  ],
  "total": 156,
  "has_more": true
}
```

**Status**: ⚠️ **PARTIALLY IMPLEMENTED**
- `/api/trades/recent` exists but:
  - No `outcome` field
  - No `realized_pnl` field
  - No `venue` field

---

#### 3. Performance Metrics Endpoint

**Needed**:
```
GET /api/performance/metrics
Query params:
  - start_date (optional)
  - end_date (optional)
  - station_code (optional)

Response:
{
  "total_trades": 156,
  "resolved_trades": 141,
  "pending_trades": 15,
  "wins": 89,
  "losses": 52,
  "win_rate": 63.12,
  "total_risk": 46800.00,
  "total_pnl": 8240.00,
  "roi": 17.61,
  "avg_edge_pct": 18.25,
  "largest_win": 450.00,
  "largest_loss": -300.00,
  "sharpe_ratio": 1.23,
  "by_station": {
    "EGLC": {
      "trades": 78,
      "wins": 45,
      "losses": 28,
      "win_rate": 61.64,
      "pnl": 4200.00,
      "roi": 18.75
    },
    ...
  }
}
```

**Status**: ❌ **NOT IMPLEMENTED**

---

#### 4. Account Balances Endpoint

**Needed**:
```
GET /api/accounts/balances

Response:
{
  "polymarket": {
    "balance_usd": 5000.00,
    "available_usd": 3500.00,
    "allocated_usd": 1500.00,
    "last_updated": "2025-11-17T14:30:00Z"
  },
  "kalshi": {
    "balance_usd": 3000.00,
    "available_usd": 3000.00,
    "allocated_usd": 0.00,
    "last_updated": "2025-11-17T14:30:00Z"
  },
  "total": {
    "balance_usd": 8000.00,
    "available_usd": 6500.00,
    "allocated_usd": 1500.00
  }
}
```

**Status**: ❌ **NOT IMPLEMENTED**

**Note**: This requires:
- Polymarket API integration for account balance
- Kalshi API integration for account balance
- Balance tracking/history

---

#### 5. Trade Outcomes Resolution

**Current Issue**: Paper trades don't have outcomes/P&L

**What's Needed**:
- Resolution service to determine win/loss for paper trades
- P&L calculation based on outcomes
- Integration with Polymarket resolution API (already exists for backtesting)

**Status**: ⚠️ **PARTIALLY AVAILABLE**
- `PolyResolution` exists for backtesting
- Not integrated with paper trade tracking
- No automatic resolution for paper trades

---

## 📊 Data Model Gaps

### Paper Trade CSV Schema

**Current Schema** (`data/trades/{date}/paper_trades.csv`):
```csv
timestamp,station_code,bracket_name,bracket_lower_f,bracket_upper_f,market_id,edge,edge_pct,f_kelly,size_usd,p_zeus,p_mkt,sigma_z,reason
```

**Missing Fields**:
- ❌ `outcome` (win/loss/pending)
- ❌ `realized_pnl`
- ❌ `venue` (polymarket/kalshi)
- ❌ `resolved_at` (timestamp when outcome determined)
- ❌ `winner_bracket` (actual winning bracket)

**Impact**: Cannot calculate P&L or performance metrics from paper trades

---

### Backtest Trade Schema

**Current Schema** (`data/backtests/runs/{date_range}.csv`):
```csv
date,station_code,city,bracket_name,lower,upper,zeus_prob,market_prob_open,market_prob_close,edge,size_usd,outcome,realized_pnl
```

**Status**: ✅ **HAS OUTCOMES AND P&L**

**Note**: Backtest trades have outcomes, but paper trades don't

---

## 🎨 Frontend Page Requirements

### Performance & Portfolio Page Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 💰 Performance & Portfolio Overview                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 📊 ACCOUNT BALANCES                                                     │ │
│ ├─────────────────────────────────────────────────────────────────────────┤ │
│ │                                                                         │ │
│ │  Polymarket:  $5,000.00  (Available: $3,500.00 | Allocated: $1,500.00) │ │
│ │  Kalshi:      $3,000.00  (Available: $3,000.00 | Allocated: $0.00)     │ │
│ │  ─────────────────────────────────────────────────────────────────────  │ │
│ │  Total:       $8,000.00  (Available: $6,500.00 | Allocated: $1,500.00) │ │
│ │                                                                         │ │
│ │  Last Updated: Nov 17, 2025 14:30 UTC                                  │ │
│ │  [Refresh Balances]                                                     │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 📈 PROFIT & LOSS                                                        │ │
│ ├─────────────────────────────────────────────────────────────────────────┤ │
│ │                                                                         │ │
│ │  Period: [Today ▼] [This Week] [This Month] [This Year] [All Time]    │ │
│ │                                                                         │ │
│ │  Total P&L:     +$1,234.56  ▲ 12.35%                                   │ │
│ │  Total Risk:    $10,000.00                                             │ │
│ │  ROI:           +12.35%                                                │ │
│ │                                                                         │ │
│ │  Breakdown:                                                             │ │
│ │  • Polymarket:  +$1,000.00  (ROI: +12.50%)                            │ │
│ │  • Kalshi:      +$234.56    (ROI: +11.73%)                            │ │
│ │                                                                         │ │
│ │  By Station:                                                            │ │
│ │  • EGLC (London):    +$500.00  (ROI: +16.67%)                         │ │
│ │  • KLGA (NYC):       +$734.56  (ROI: +10.49%)                         │ │
│ │                                                                         │ │
│ │  [View P&L Chart →]                                                    │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 📊 PERFORMANCE METRICS                                                  │ │
│ ├─────────────────────────────────────────────────────────────────────────┤ │
│ │                                                                         │ │
│ │  Total Trades:        156                                               │ │
│ │  Resolved:            141  (90.4%)                                      │ │
│ │  Pending:             15   (9.6%)                                       │ │
│ │                                                                         │ │
│ │  Win Rate:            63.12%  (89 wins / 141 resolved)                 │ │
│ │  Average Edge:        18.25%                                            │ │
│ │  Sharpe Ratio:        1.23                                              │ │
│ │                                                                         │ │
│ │  Largest Win:         +$450.00                                          │ │
│ │  Largest Loss:        -$300.00                                          │ │
│ │                                                                         │ │
│ │  [View Detailed Metrics →]                                             │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 📝 TRADE HISTORY                                                        │ │
│ ├─────────────────────────────────────────────────────────────────────────┤ │
│ │                                                                         │ │
│ │  Filters:                                                               │ │
│ │  Date Range: [Nov 1, 2025] to [Nov 17, 2025]                          │ │
│ │  Station: [All ▼]  Venue: [All ▼]  Outcome: [All ▼]                   │ │
│ │                                                                         │ │
│ │  [Export CSV]  [Refresh]                                               │ │
│ │                                                                         │ │
│ │  ┌───────────────────────────────────────────────────────────────────┐ │ │
│ │  │ Date       │ Station │ Bracket │ Size    │ Edge  │ Outcome │ P&L  │ │ │
│ │  ├───────────────────────────────────────────────────────────────────┤ │ │
│ │  │ Nov 17     │ EGLC    │ 58-59°F │ $300.00 │ 26.25%│ ✅ Win  │+$112 │ │ │
│ │  │ 14:21      │         │         │         │       │         │      │ │ │
│ │  │ Nov 17     │ EGLC    │ 60-61°F │ $300.00 │ 25.75%│ ✅ Win  │+$115 │ │ │
│ │  │ 14:21      │         │         │         │       │         │      │ │ │
│ │  │ Nov 17     │ KLGA    │ 48-49°F │ $250.00 │ 18.00%│ ⏳ Pend │  -   │ │ │
│ │  │ 14:20      │         │         │         │       │         │      │ │ │
│ │  │ Nov 17     │ KLGA    │ 49-50°F │ $200.00 │ 15.00%│ ❌ Loss │ -$200│ │ │
│ │  │ 14:20      │         │         │         │       │         │      │ │ │
│ │  │ ...        │ ...     │ ...     │ ...     │ ...   │ ...     │ ...  │ │ │
│ │  └───────────────────────────────────────────────────────────────────┘ │ │
│ │                                                                         │ │
│ │  Showing 1-50 of 156 trades  [◀ Previous] [Next ▶]                    │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 📈 P&L OVER TIME CHART                                                  │ │
│ ├─────────────────────────────────────────────────────────────────────────┤ │
│ │                                                                         │ │
│ │  [Line chart showing cumulative P&L over time]                         │ │
│ │  [Toggle: By Station | By Venue | Overall]                             │ │
│ │                                                                         │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ✅ Implementation Checklist

### Backend Requirements

#### Phase 1: Trade Resolution & P&L
- [ ] **Enhance Paper Trade Schema**
  - Add `outcome` field (win/loss/pending)
  - Add `realized_pnl` field
  - Add `venue` field (polymarket/kalshi)
  - Add `resolved_at` timestamp
  - Add `winner_bracket` field

- [ ] **Create Trade Resolution Service**
  - Integrate `PolyResolution` for paper trades
  - Calculate P&L based on outcomes
  - Update paper trade CSV with outcomes
  - Handle pending trades (not yet resolved)

- [ ] **Create P&L Aggregation Service**
  - Aggregate P&L by date range
  - Aggregate by station
  - Aggregate by venue
  - Calculate ROI

#### Phase 2: API Endpoints
- [ ] **`GET /api/performance/pnl`**
  - Return aggregated P&L data
  - Support filtering by date, station, venue
  - Return breakdowns (by station, by venue, by period)

- [ ] **`GET /api/performance/metrics`**
  - Return performance metrics (win rate, ROI, etc.)
  - Support filtering
  - Return station-level breakdowns

- [ ] **`GET /api/trades/history`**
  - Enhanced version of `/api/trades/recent`
  - Include outcomes and P&L
  - Support advanced filtering
  - Support pagination

- [ ] **`GET /api/accounts/balances`** (Future)
  - Return Polymarket balance
  - Return Kalshi balance
  - Return total portfolio value
  - Note: Requires API integration

#### Phase 3: Account Integration (Future)
- [ ] **Polymarket Account API Integration**
  - Fetch account balance
  - Track balance history
  - Handle authentication

- [ ] **Kalshi Account API Integration**
  - Fetch account balance
  - Track balance history
  - Handle authentication

---

### Frontend Requirements

#### Phase 1: Basic Page Structure
- [ ] **Create PerformancePage Component**
  - Page layout
  - Section components
  - Data fetching hooks

- [ ] **Account Balances Section**
  - Display balances
  - Refresh button
  - Last updated timestamp
  - Note: Will show "Not Available" until API integration

#### Phase 2: P&L Dashboard
- [ ] **P&L Summary Section**
  - Period selector (Today/Week/Month/Year/All Time)
  - Total P&L display
  - ROI display
  - Breakdown by venue
  - Breakdown by station

- [ ] **P&L Chart**
  - Line chart showing cumulative P&L over time
  - Toggle between views (by station, by venue, overall)
  - Date range selector

#### Phase 3: Performance Metrics
- [ ] **Metrics Section**
  - Win rate
  - Total trades
  - Resolved vs pending
  - Average edge
  - Sharpe ratio
  - Largest win/loss

#### Phase 4: Trade History Table
- [ ] **Trade History Table**
  - Sortable columns
  - Filterable (date range, station, venue, outcome)
  - Pagination
  - Export to CSV
  - Outcome indicators (✅ win, ❌ loss, ⏳ pending)

---

## 🚀 Implementation Priority

### High Priority (MVP)
1. ✅ Trade resolution for paper trades
2. ✅ P&L calculation and aggregation
3. ✅ `/api/performance/pnl` endpoint
4. ✅ `/api/performance/metrics` endpoint
5. ✅ Enhanced `/api/trades/history` endpoint
6. ✅ Frontend Performance page (without account balances)

### Medium Priority
7. ⚠️ Account balance API integration (Polymarket)
8. ⚠️ Account balance API integration (Kalshi)
9. ⚠️ Balance history tracking
10. ⚠️ Frontend account balances section

### Low Priority (Nice to Have)
11. 📊 Advanced charts (P&L over time, win rate trends)
12. 📊 Performance comparison (this month vs last month)
13. 📊 Risk metrics (VaR, max drawdown)
14. 📊 Export functionality (PDF reports)

---

## 📝 Summary

### What Exists ✅
- Live Trading Dashboard (real-time edges, trades, forecasts)
- Historical Data Page (per-station detailed analysis)
- Backtest results (with P&L and metrics)
- Basic trade endpoints (`/api/trades/recent`)

### What's Missing ❌
- **Overall P&L tracking** (aggregated across all trades)
- **Trade outcomes** for paper trades (win/loss)
- **Performance metrics** aggregation service
- **Account balances** API integration
- **Collated trade history** with outcomes and P&L
- **Performance & Portfolio page** in frontend

### Key Gaps
1. **Data Model**: Paper trades don't have outcomes/P&L
2. **Backend Services**: No P&L aggregation service
3. **API Endpoints**: Missing performance/portfolio endpoints
4. **Frontend Page**: No Performance & Portfolio page
5. **Account Integration**: No balance tracking (future)

---

**Next Steps**: Create implementation plan for Performance & Portfolio page (backend + frontend)

