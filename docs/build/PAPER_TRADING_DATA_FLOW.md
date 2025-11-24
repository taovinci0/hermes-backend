# Paper Trading Data Flow - Frontend to Backend

**Date**: November 18, 2025  
**Purpose**: Document where frontend pulls paper trade and performance data  
**Mode**: Paper Trading

---

## 📊 Data Flow Overview

```
Paper Trading Execution
    ↓
CSV Files (data/trades/{date}/paper_trades.csv)
    ↓
Backend Services (TradeService, PerformanceService, PnLService)
    ↓
API Endpoints (/api/trades/*, /api/performance/*)
    ↓
Frontend (React/TypeScript)
```

---

## 💾 Where Paper Trades Are Saved

### **File Location**

**Path**: `data/trades/{YYYY-MM-DD}/paper_trades.csv`

**Example**:
- `data/trades/2025-11-19/paper_trades.csv`
- `data/trades/2025-11-20/paper_trades.csv`

**Created By**: `PaperBroker` in `venues/polymarket/execute.py`

**When**: Every time paper trades are executed (via `orchestrator --mode paper` or dynamic trading engine)

### **CSV Format**

```csv
timestamp,station_code,bracket_name,bracket_lower_f,bracket_upper_f,market_id,edge,edge_pct,f_kelly,size_usd,p_zeus,p_mkt,sigma_z,reason,outcome,realized_pnl,venue,resolved_at,winner_bracket
2025-11-19T22:18:00Z,EGLC,51-52°F,51,52,676331,0.063700,6.37,0.228800,228.80,0.283,0.220,0.5,strong_edge,pending,,polymarket,,
2025-11-19T22:18:00Z,EGLC,45-46°F,45,46,676333,0.085600,8.56,0.300000,300.00,0.420,0.334,0.5,strong_edge,pending,,polymarket,,
```

**Fields**:
- `timestamp`: When trade was placed
- `station_code`: Weather station code (e.g., "EGLC")
- `bracket_name`: Temperature bracket (e.g., "51-52°F")
- `size_usd`: Trade size in USD
- `edge_pct`: Edge percentage
- `outcome`: "win", "loss", or "pending" (filled after resolution)
- `realized_pnl`: P&L in USD (filled after resolution)
- `venue`: "polymarket" or "kalshi" (filled after resolution)

---

## 🔌 Backend Services

### **1. TradeService** (`backend/api/services/trade_service.py`)

**Reads**: CSV files from `data/trades/{date}/paper_trades.csv`

**Methods**:
- `get_trades()`: Reads all trades from CSV files
- `get_trade_summary()`: Calculates summary statistics

**File Path Resolution**:
```python
from backend.api.utils.path_utils import get_trades_dir

trades_dir = get_trades_dir()  # Returns: PROJECT_ROOT / "data" / "trades"
date_dir = trades_dir / trade_date.isoformat()  # e.g., "2025-11-19"
csv_file = date_dir / "paper_trades.csv"
```

---

### **2. PerformanceService** (`backend/api/services/performance_service.py`)

**Reads**: Uses `TradeService` to get trades, then calculates metrics

**Methods**:
- `get_metrics()`: Calculates performance metrics (win rate, ROI, Sharpe ratio, etc.)

**Metrics Calculated**:
- Total trades, resolved trades, pending trades
- Wins, losses, win rate
- Total risk, total P&L, ROI
- Average edge
- Largest win/loss
- Sharpe ratio
- Breakdown by station

---

### **3. PnLService** (`backend/api/services/pnl_service.py`)

**Reads**: Uses `TradeService` to get trades, then aggregates P&L

**Methods**:
- `get_pnl()`: Aggregates P&L across filters

**Aggregations**:
- Total P&L, total risk, ROI
- Breakdown by station
- Breakdown by venue
- Breakdown by period (today, week, month, year, all_time)

---

## 🌐 API Endpoints

### **Trade Endpoints** (`/api/trades/*`)

**File**: `backend/api/routes/trades.py`

#### **1. Get Recent Trades**
```
GET /api/trades/recent?trade_date={DATE}&station_code={STATION}&limit={LIMIT}
```

**Returns**: List of recent trades
**Source**: `TradeService.get_trades()`
**Data**: CSV files from `data/trades/{date}/paper_trades.csv`

#### **2. Get Trade History**
```
GET /api/trades/history?start_date={DATE}&end_date={DATE}&station_code={STATION}&venue={VENUE}&outcome={OUTCOME}&mode=paper&limit={LIMIT}&offset={OFFSET}
```

**Returns**: Paginated trade history with filtering
**Source**: `TradeService.get_trades()` + filtering
**Data**: CSV files from `data/trades/{date}/paper_trades.csv`

#### **3. Get Trade Summary**
```
GET /api/trades/summary?trade_date={DATE}&station_code={STATION}
```

**Returns**: Summary statistics
**Source**: `TradeService.get_trade_summary()`
**Data**: CSV files from `data/trades/{date}/paper_trades.csv`

#### **4. Resolve Trades**
```
POST /api/trades/resolve?trade_date={DATE}&station_code={STATION}
```

**Returns**: Resolution results
**Source**: `TradeResolutionService.resolve_trades_for_date()`
**Updates**: CSV files with `outcome` and `realized_pnl` fields

---

### **Performance Endpoints** (`/api/performance/*`)

**File**: `backend/api/routes/performance.py`

#### **1. Get P&L**
```
GET /api/performance/pnl?start_date={DATE}&end_date={DATE}&station_code={STATION}&venue={VENUE}&mode=paper
```

**Returns**: Aggregated P&L data
**Source**: `PnLService.get_pnl()`
**Data**: CSV files via `TradeService.get_trades()`

#### **2. Get Performance Metrics**
```
GET /api/performance/metrics?start_date={DATE}&end_date={DATE}&station_code={STATION}&mode=paper
```

**Returns**: Performance metrics (win rate, ROI, Sharpe ratio, etc.)
**Source**: `PerformanceService.get_metrics()`
**Data**: CSV files via `TradeService.get_trades()`

---

## 📋 Frontend Data Sources

### **Trade History Page**

**API Endpoint**: `GET /api/trades/history`

**Query Parameters**:
- `start_date`: Optional start date filter
- `end_date`: Optional end date filter
- `station_code`: Optional station filter
- `venue`: Optional venue filter (polymarket, kalshi)
- `outcome`: Optional outcome filter (win, loss, pending)
- `mode`: Always `"paper"` for paper trading
- `limit`: Pagination limit (default: 100)
- `offset`: Pagination offset (default: 0)

**Example Request**:
```typescript
const response = await fetch(
  '/api/trades/history?mode=paper&limit=100&offset=0'
);
const data = await response.json();
// Returns: { trades: [...], total: 1812, limit: 100, offset: 0, has_more: true }
```

**Data Source**: `data/trades/{date}/paper_trades.csv` files

---

### **Performance Metrics Page**

**API Endpoint**: `GET /api/performance/metrics?mode=paper`

**Query Parameters**:
- `start_date`: Optional start date filter
- `end_date`: Optional end date filter
- `station_code`: Optional station filter
- `mode`: Always `"paper"` for paper trading

**Example Request**:
```typescript
const response = await fetch('/api/performance/metrics?mode=paper');
const data = await response.json();
// Returns: {
//   total_trades: 1812,
//   resolved_trades: 0,
//   pending_trades: 1812,
//   wins: 0,
//   losses: 0,
//   win_rate: 0.00,
//   total_risk: 543600.00,
//   total_pnl: 0.00,
//   roi: 0.00,
//   avg_edge_pct: 17.82,
//   largest_win: 0.00,
//   largest_loss: 0.00,
//   sharpe_ratio: 0.00,
//   by_station: { ... }
// }
```

**Data Source**: `data/trades/{date}/paper_trades.csv` files via `TradeService`

---

### **P&L Dashboard**

**API Endpoint**: `GET /api/performance/pnl?mode=paper`

**Query Parameters**:
- `start_date`: Optional start date filter
- `end_date`: Optional end date filter
- `station_code`: Optional station filter
- `venue`: Optional venue filter
- `mode`: Always `"paper"` for paper trading

**Example Request**:
```typescript
const response = await fetch('/api/performance/pnl?mode=paper');
const data = await response.json();
// Returns: {
//   total_pnl: 0.00,
//   total_risk: 543600.00,
//   roi: 0.00,
//   by_station: { ... },
//   by_venue: { ... },
//   by_period: { ... }
// }
```

**Data Source**: `data/trades/{date}/paper_trades.csv` files via `TradeService`

---

## 🔍 Data Resolution Flow

### **When Trades Are Resolved**

**Trigger**: `POST /api/trades/resolve?trade_date={DATE}`

**Process**:
1. `TradeResolutionService.resolve_trades_for_date()` reads trades from CSV
2. Fetches Polymarket events to determine winners
3. Calculates `outcome` (win/loss/pending) and `realized_pnl`
4. `TradeResolutionService.update_trade_csv()` updates CSV file
5. CSV file now contains `outcome` and `realized_pnl` fields

**Updated CSV Fields**:
- `outcome`: "win", "loss", or "pending"
- `realized_pnl`: P&L in USD (positive for wins, negative for losses)
- `venue`: "polymarket" or "kalshi"
- `resolved_at`: Timestamp when resolved
- `winner_bracket`: Winning bracket name

**After Resolution**:
- Performance metrics now show resolved trades
- Win rate, ROI, P&L all update
- Trade history shows outcomes

---

## 📁 File Structure

```
data/
└── trades/
    ├── 2025-11-19/
    │   └── paper_trades.csv  ← Paper trades for Nov 19
    ├── 2025-11-20/
    │   └── paper_trades.csv  ← Paper trades for Nov 20
    └── 2025-11-21/
        └── paper_trades.csv  ← Paper trades for Nov 21
```

**CSV File Path**: `data/trades/{YYYY-MM-DD}/paper_trades.csv`

**Backend Reads From**: `PROJECT_ROOT / "data" / "trades" / {date} / "paper_trades.csv"`

---

## 🔄 Complete Data Flow

### **1. Paper Trade Execution**

```python
# venues/polymarket/execute.py - PaperBroker.place()
broker = PaperBroker()
broker.place(decisions)

# Saves to: data/trades/2025-11-19/paper_trades.csv
```

### **2. Backend Service Reads**

```python
# backend/api/services/trade_service.py - TradeService.get_trades()
trade_service = TradeService()
trades = trade_service.get_trades(trade_date=date(2025, 11, 19))

# Reads from: data/trades/2025-11-19/paper_trades.csv
```

### **3. API Endpoint Serves**

```python
# backend/api/routes/trades.py
@router.get("/history")
async def get_trade_history(...):
    trades = trade_service.get_trades(...)
    return {"trades": trades, ...}
```

### **4. Frontend Fetches**

```typescript
// Frontend
const response = await fetch('/api/trades/history?mode=paper');
const data = await response.json();
// data.trades contains all paper trades
```

---

## ⚠️ Important Notes

### **Paper Trading Mode**

**All endpoints default to `mode=paper`**:
- `GET /api/trades/history?mode=paper` (default)
- `GET /api/performance/metrics?mode=paper` (default)
- `GET /api/performance/pnl?mode=paper` (default)

**Data Source**: Always `data/trades/{date}/paper_trades.csv` files

### **Station Code Issue**

**Current Issue**: Trades showing `station_code: "UNKNOWN"`

**Cause**: `PaperBroker` may not be correctly extracting station code from decisions

**Fix Needed**: Ensure `PaperBroker.place()` correctly sets `station_code` in CSV

**Location**: `venues/polymarket/execute.py` - `PaperBroker.place()` method

### **Trade Resolution**

**Trades start as "pending"**:
- `outcome`: Empty or "pending"
- `realized_pnl`: Empty or 0

**After resolution**:
- Call `POST /api/trades/resolve?trade_date={DATE}`
- CSV file is updated with outcomes
- Performance metrics update automatically

---

## ✅ Summary

### **Frontend Data Sources (Paper Trading Mode)**

1. **Trade History**: `GET /api/trades/history?mode=paper`
   - Source: `data/trades/{date}/paper_trades.csv`
   - Service: `TradeService.get_trades()`

2. **Performance Metrics**: `GET /api/performance/metrics?mode=paper`
   - Source: `data/trades/{date}/paper_trades.csv` (via `TradeService`)
   - Service: `PerformanceService.get_metrics()`

3. **P&L Data**: `GET /api/performance/pnl?mode=paper`
   - Source: `data/trades/{date}/paper_trades.csv` (via `TradeService`)
   - Service: `PnLService.get_pnl()`

### **Data Flow**

```
CSV Files (data/trades/{date}/paper_trades.csv)
    ↓
TradeService (reads CSV)
    ↓
PerformanceService / PnLService (calculates metrics)
    ↓
API Endpoints (/api/trades/*, /api/performance/*)
    ↓
Frontend (fetches via HTTP)
```

---

**Last Updated**: November 18, 2025

