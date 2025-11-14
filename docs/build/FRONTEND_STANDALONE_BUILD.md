# Hermes Frontend - Standalone Build Guide

**Date**: November 13, 2025  
**Purpose**: Complete guide for building the Hermes frontend dashboard as a separate project  
**Status**: Standalone - Can be built independently from the main Hermes trading engine  
**Backend API**: Must connect to running Hermes FastAPI backend at `http://localhost:8000`

---

## 🎯 Overview

This document provides everything needed to build the Hermes frontend dashboard **as a separate project**. The frontend connects to the existing Hermes FastAPI backend API (which must be running separately).

**Key Principle**: Frontend is built separately, communicates with backend via REST API and WebSocket.

---

## 📋 Prerequisites

### Backend API Must Be Running

Before building the frontend, ensure the Hermes backend API is running:

```bash
# In the main Hermes project directory
cd backend
python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

**Verify API is running:**
- Open http://localhost:8000/docs in your browser
- You should see FastAPI interactive documentation
- Test endpoint: http://localhost:8000/api/status

### Backend API Endpoints

The frontend will connect to these endpoints:

**Base URL**: `http://localhost:8000`

**Available Endpoints:**
- `GET /api/status` - System status
- `GET /api/edges/current` - Current trading edges
- `GET /api/trades/recent` - Recent trades
- `GET /api/snapshots/*` - Historical snapshots
- `GET /api/logs/activity` - Activity logs
- `GET /api/metar/*` - METAR observations
- `GET /api/compare/zeus-vs-metar` - Zeus vs METAR comparison
- `GET /api/backtest/*` - Backtest execution
- `WebSocket /ws/trading` - Real-time updates

**Full API Documentation**: http://localhost:8000/docs

---

## 🎨 What Users Will See

### 1. Live Trading Dashboard

**What Users See:**

Live dashboard shows **ACTIVE/OPEN MARKETS** (tradeable now) with station and event day selection. Markets open 1-2 days in advance, so you'll see today + future days.

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 🚀 Hermes Dynamic Paper Trading - ACTIVE MARKETS                                    │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ Status: ● RUNNING    Cycle: 45    Next: 2:34    Current Time: Nov 13, 14:30 UTC   │
│                                                                                     │
│ Station: [● EGLC (London)] [○ KLGA (NYC)]    [View All] [View Historical →]       │
│                                                                                     │
│ Event Day: [● Nov 13 (Today)] [○ Nov 14 (Tomorrow)] [○ Nov 15]                    │
│            Markets Open: Yes ✅    Markets Open: Yes ✅    Markets Open: Yes ✅     │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────┬──────────────────────────────────────────────┐
│ 🌡️  ZEUS FORECAST EVOLUTION          │  📊 CURRENT EDGES (London, Nov 13)          │
│ London (EGLC) - Nov 13, 2025 (Today) │                                              │
│ Market Status: ✅ OPEN               │  Bracket │Zeus│Market│ Edge │  Size │Status │
│                                      │  ────────┼────┼──────┼──────┼───────┼───────│
│ [Live Graph - Updates Every 15 min] │  58-59°F │28.3│ 0.05%│26.25%│$300.00│✅ TRADE│
│   60°F┤                              │  60-61°F │33.5│ 6.95%│25.75%│$300.00│✅ TRADE│
│       │    ━━━━━━ Zeus Latest       │  62-63°F │22.1│85.00%│-63.7%│   -   │❌ SKIP │
│   58°F┤  ┅┅┅┅┅┅ Zeus 15 min ago     │                                              │
│       │  ········ Zeus 30 min ago    │  💰 Trades This Cycle: 2                     │
│   56°F┤  ▪▪▪▪▪▪ METAR (actual)       │  💵 Total Size: $600.00                      │
│       │                              │                                              │
│   54°F┤ ▪         ┅       ━          │  📈 Today's Summary (Nov 13):                │
│       │ ▪      ┅┅┅··   ━━━━          │  Cycles: 45 | Trades: 23 | Size: $6,900    │
│   52°F┤ ▪   ┅┅┅·····━━━━             │  Avg Edge: 18.5% | Win Rate: 24%           │
│       └─────────────────────────────┘│                                              │
│        00  04  08  12  16  20  24    │                                              │
│                                      │                                              │
│ Legend:                              │  [Click "Nov 14" tab to see tomorrow's      │
│ ━━━ Current Zeus (14:21)             │   markets and edges →]                      │
│ ┅┅┅ Zeus 15min ago (14:06)          │                                              │
│ ··· Zeus 30min ago (13:51)          │                                              │
│ ▪▪▪ METAR Actual (Updates hourly)   │                                              │
│                                      │                                              │
│ Daily High Predictions:              │                                              │
│ • 14:21 → 57.8°F                    │                                              │
│ • 14:06 → 58.1°F (+0.3°F)          │                                              │
│ • 13:51 → 58.5°F (+0.7°F)          │                                              │
│                                      │                                              │
└──────────────────────────────────────┴──────────────────────────────────────────────┘
```

**Key Features:**

1. **Station Selector**
   - Toggle between active stations (EGLC, KLGA, etc.)
   - "View All" shows summary cards for all stations
   - Each station has its own real-time data

2. **Event Day Selector**
   - Toggle between days with **OPEN markets** (tradeable now)
   - Shows: Today, Tomorrow, Day After (if markets open)
   - Each day shows market status (Open ✅ or not yet available)
   - Only shows days where Polymarket markets exist

3. **Zeus Forecast Evolution Graph**
   - Shows current Zeus prediction (solid line)
   - Overlays previous predictions (faded lines)
   - Visualizes how forecast changes **for selected event day**
   - Updates every 15 minutes automatically
   - Works for future days too (Zeus predicts ahead!)

4. **METAR Integration (Actual Temperature)**
   - Plots real observed temperatures from METAR
   - **For today**: Shows actual temps as they happen (updates hourly)
   - **For future days**: No data yet (day hasn't happened)
   - Graph shows "No METAR data yet (future event)" for future days
   - Once day arrives, METAR starts plotting automatically

5. **Live Activity Log** (with Filtering)
   - Streams agent decisions in real-time
   - **Filter by Station**: Dropdown to select specific station or "All"
   - **Filter by Event Day**: Dropdown to select specific day or "All"
     - Shows last 3 days + today + future open markets
     - Only includes days with actual log data
   - Filters work in combination (Station AND Day)
   - Shows each step: fetch → calculate → trade
   - Color-coded actions (🔄 fetch, 🧮 calculate, 📝 trade)
   - Auto-scrolls with new events
   - When "All" selected: Adds [Station, Date] prefix to each log entry
   - Clear indicator showing current filter selection

6. **Edge Summary**
   - Shows current edges **for selected station + event day**
   - Updates every 15 minutes
   - Works for all open markets (today and future)
   - Shows: "Market opens in X hours" if not yet open

### 1a. Live Dashboard - "View All Stations" Mode

**Alternative view showing all active stations at once, including future event days:**

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 🚀 Hermes Dynamic Paper Trading - ALL STATIONS & EVENT DAYS                         │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ Status: ● RUNNING    Cycle: 45    Next: 2:34    Current Time: Nov 13, 14:30 UTC   │
│                                                                                     │
│ Showing: [View All] [Single Station →]                                             │
│ Event Days with Open Markets: Nov 13 (Today) | Nov 14 (Tomorrow) | Nov 15         │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────── NOV 13 (TODAY) ────────────────────────────────┐
│                                                                                     │
│ ┌─────────────────────────────────┬─────────────────────────────────────────────┐ │
│ │ 🌡️  LONDON (EGLC)               │  🌡️  NEW YORK (KLGA)                       │ │
│ ├─────────────────────────────────┼─────────────────────────────────────────────┤ │
│ │ Zeus High: 57.8°F               │  Zeus High: 48.2°F                          │ │
│ │ METAR Now: 53.1°F ✅            │  METAR Now: 44.6°F ✅                       │ │
│ │                                 │                                             │ │
│ │ Latest Trades:                  │  Latest Trades:                             │ │
│ │ • 58-59°F @ 14:21 (+26%)       │  • 48-49°F @ 14:20 (+18%)                  │ │
│ │ • 60-61°F @ 14:21 (+26%)       │  • 49-50°F @ 14:20 (+15%)                  │ │
│ │                                 │                                             │ │
│ │ Today: 6 trades, $1,800         │  Today: 4 trades, $1,200                    │ │
│ │ Avg Edge: 20.8%                 │  Avg Edge: 16.5%                            │ │
│ │                                 │                                             │ │
│ │ [View Details →]                │  [View Details →]                           │ │
│ └─────────────────────────────────┴─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────── NOV 14 (TOMORROW) ─────────────────────────────┐
│ Markets open 1 day in advance - actively trading!                                   │
│                                                                                     │
│ ┌─────────────────────────────────┬─────────────────────────────────────────────┐ │
│ │ 🌡️  LONDON (EGLC)               │  🌡️  NEW YORK (KLGA)                       │ │
│ ├─────────────────────────────────┼─────────────────────────────────────────────┤ │
│ │ Zeus High: 60.1°F               │  Zeus High: 51.3°F                          │ │
│ │ METAR: ⏳ Not yet (future)      │  METAR: ⏳ Not yet (future)                 │ │
│ │                                 │                                             │ │
│ │ Latest Trades:                  │  Latest Trades:                             │ │
│ │ • 59-60°F @ 14:20 (+21%)       │  • 50-51°F @ 14:19 (+16%)                  │ │
│ │ • 60-61°F @ 14:20 (+15%)       │  • 51-52°F @ 14:19 (+12%)                  │ │
│ │                                 │                                             │ │
│ │ Today: 3 trades, $800           │  Today: 2 trades, $500                      │ │
│ │ Avg Edge: 17.5%                 │  Avg Edge: 14.0%                            │ │
│ │                                 │                                             │ │
│ │ [View Details →]                │  [View Details →]                           │ │
│ └─────────────────────────────────┴─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 2. Historical Data Browser (Stacked Timeline View)

**What Users See:**

Three **time-aligned stacked graphs** showing Zeus forecasts, Polymarket prices, and trading decisions all on the same timeline. Each layer has its own appropriate scale for maximum clarity.

**Controls:** Select ANY past date and ANY station to review complete historical data.

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 📂 Historical Analysis - Stacked Timeline View                                      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ Date: [◀ Nov 12] [Nov 13, 2025 ▼] [Nov 14 ▶]                                      │
│ Station: [London (EGLC) ▼] [New York (KLGA)] [All Available ▼]                    │
│                                                                                     │
│ Data Points: 24 Zeus snapshots | 24 Polymarket snapshots | 24 Decision snapshots    │
│                                                                                     │
│ [Hover over any time to see vertical line across all graphs]                       │
│ [Click any point to see detailed snapshot popup]                                   │
│ [← Back to Live Dashboard]                                                         │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 🌡️  GRAPH 1: ZEUS FORECAST EVOLUTION vs METAR ACTUAL                               │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│   Temperature (°F)                                                                  │
│   60°F┤                                                ★ METAR actual high (58.2°F)│
│       │                                           ★  ★                              │
│   58°F┤                                     ★  ★                                    │
│       │                                ★                                            │
│   56°F┤                           ★  ━━━━━━━━━━━━━━━━ Zeus latest (57.8°F)        │
│       │                        ★  ━━━━━━━━━                                        │
│   54°F┤                     ★  ━━━ ┅┅┅┅┅┅┅┅┅┅┅┅┅ Zeus 15min ago (58.1°F)          │
│       │                   ━━━ ┅┅┅┅┅ ·········· Zeus 30min ago (58.5°F)            │
│   52°F┤              ★  ━━━ ┅┅┅ ·····                                              │
│       │         ★  ━━━ ┅┅┅ ····                                                    │
│   50°F┤    ★  ━━━ ┅┅┅ ···                                                          │
│       │  ★  ━━━ ┅┅┅ ··                                                             │
│       └─────────────────────────────────────────────────────────────────────────────│
│        00:00   04:00   08:00   12:00   16:00   20:00   24:00                      │
│                                                                                     │
│ Legend: ━━━ Current Zeus  ┅┅┅ Zeus 15m ago  ··· Zeus 30m ago  ★ METAR actual    │
│                                                                                     │
│ Final Prediction: 57.8°F  |  Actual: 58.2°F  |  Error: +0.4°F (0.7%)  ✅ Accurate│
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 💰 GRAPH 2: POLYMARKET IMPLIED PROBABILITIES (All Brackets)                        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│   Probability (%)                                                                   │
│  100%┤                                                                              │
│      │                                                                              │
│   75%┤  ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ 60-61°F (Market favorite)                        │
│      │                                                                              │
│   50%┤  ▬▬▬▬▬▬▬▬▬▬▬▬ 58-59°F (Zeus pick)                                       │
│      │                                                                              │
│   25%┤  ▬▬▬▬▬▬ 56-57°F                                                            │
│      │  ▬▬▬▬▬▬ 57-58°F                                                            │
│      │  ▬▬▬▬▬▬ 59-60°F                                                            │
│    0%┤  ▬▬▬ 61-62°F                                                                │
│      └─────────────────────────────────────────────────────────────────────────────│
│        09:00      12:00      15:00      18:00      21:00                           │
│                                                                                     │
│ Shows: How market-implied probabilities evolved for each temperature bracket       │
│ Note: Market heavily favored 60-61°F (75%), while Zeus favored 58-59°F (50%)     │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 📝 GRAPH 3: TRADING DECISIONS TIMELINE (What/When/Why)                             │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│   Trade Size ($)                                                                    │
│  $400┤                                                                              │
│      │                                                                              │
│  $300┤    💰           💰           💰           💰           💰           💰       │
│      │  58-59°F     58-59°F     60-61°F     60-61°F     60-61°F     60-61°F       │
│      │  Edge:18%    Edge:22%    Edge:26%    Edge:25%    Edge:19%    Edge:15%      │
│  $200┤                                                                              │
│      │                                                                              │
│  $100┤                                                                              │
│      │                                                                              │
│    $0└─────────────────────────────────────────────────────────────────────────────│
│        09:15      10:30      12:00      13:45      15:15      16:30               │
│                                                                                     │
│ Summary: 6 trades | $1,800 total | Avg edge: 20.8%                                │
│ Strategy: Started with Zeus pick (58-59°F), switched to Market pick (60-61°F)     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

**Key Features:**

1. **Three Stacked Graphs (Time-Aligned)**
   - **Graph 1 (Top)**: Zeus forecast evolution + METAR actual temperatures
   - **Graph 2 (Middle)**: Polymarket implied probabilities for all brackets
   - **Graph 3 (Bottom)**: Trading decisions timeline

2. **Interactive Features**
   - **Hover**: Vertical line appears across all 3 graphs showing values at that moment
   - **Click**: Popup with detailed snapshots from all 3 data sources
   - **Toggles**: Show/hide specific data layers, enable compact mode
   - **Drill-down**: Click any trade marker to see full edge calculation breakdown

3. **Accuracy Analysis**
   - Compare Zeus final prediction vs METAR actual
   - Track how Zeus forecast evolved over time
   - See which trades were right/wrong
   - Calculate prediction error and accuracy metrics

### 3. Backtest Runner

**What Users See:**

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 🧪 Backtest Configuration                                                           │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ Date Range: [Nov 1, 2025] to [Nov 13, 2025]                                        │
│ Stations: [✓ EGLC] [✓ KLGA] [ ] KORD [ ] KLAX                                     │
│                                                                                     │
│ Trading Parameters:                                                                 │
│ • Edge Minimum: [5.0] %                                                            │
│ • Kelly Cap: [10.0] %                                                              │
│ • Fee: [0.5] % (50 bps)                                                            │
│ • Slippage: [0.3] % (30 bps)                                                       │
│                                                                                     │
│ Probability Model: [● Spread Model] [○ Bands Model]                                │
│                                                                                     │
│ [Run Backtest] [Save Preset] [Load Preset ▼]                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 📊 Backtest Results                                                                 │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ Status: ✅ COMPLETED    Duration: 2m 34s                                           │
│                                                                                     │
│ Summary:                                                                            │
│ • Total Trades: 156                                                                │
│ • Wins: 89 (57.1%)                                                                 │
│ • Losses: 52 (33.3%)                                                               │
│ • Pending: 15 (9.6%)                                                               │
│                                                                                     │
│ P&L:                                                                                │
│ • Total Risk: $46,800                                                              │
│ • Total P&L: +$8,240                                                               │
│ • ROI: +17.6%                                                                      │
│                                                                                     │
│ Performance:                                                                        │
│ • Avg Edge: 18.2%                                                                  │
│ • Largest Win: $450                                                                │
│ • Largest Loss: -$300                                                              │
│                                                                                     │
│ [View Detailed Results] [Export CSV] [Compare with Other Configs]                  │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 Backend API Integration

### API Base Configuration

```typescript
// src/config/api.ts
export const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:8000';
export const WS_URL = process.env.VITE_WS_URL || 'ws://localhost:8000/ws/trading';
```

### Required API Endpoints

#### 1. System Status

```typescript
GET /api/status

Response:
{
  "timestamp": "2025-11-13T14:30:00Z",
  "trading_engine": {
    "running": true,
    "pid": 12345
  },
  "data_collection": {
    "snapshots_dir_exists": true,
    "recent_snapshots_24h": 156
  },
  "version": "1.0.0"
}
```

#### 2. Current Edges

```typescript
GET /api/edges/current?station=EGLC&event_day=2025-11-13&limit=10

Response:
[
  {
    "station_code": "EGLC",
    "city": "London",
    "event_day": "2025-11-13",
    "bracket": "58-59°F",
    "p_zeus": 0.283,
    "p_market": 0.0005,
    "edge": 0.2625,
    "edge_pct": 26.25,
    "size_usd": 300.0,
    "decision_time_utc": "2025-11-13T14:21:10Z"
  },
  ...
]
```

#### 3. Activity Logs

```typescript
GET /api/logs/activity?station=EGLC&event_day=2025-11-13&limit=100&offset=0

Response:
{
  "logs": [
    {
      "timestamp": "2025-11-13T14:21:10Z",
      "station_code": "EGLC",
      "event_day": "2025-11-13",
      "action": "start_cycle",
      "message": "Starting evaluation cycle #45",
      "log_level": "INFO"
    },
    ...
  ],
  "total": 234,
  "has_more": true
}
```

#### 4. Zeus Snapshots

```typescript
GET /api/snapshots/zeus?station_code=EGLC&event_day=2025-11-13&limit=10

Response:
[
  {
    "fetch_time_utc": "2025-11-13T14:21:10Z",
    "station_code": "EGLC",
    "event_day": "2025-11-13",
    "timeseries": [
      {
        "time_utc": "2025-11-13T00:00:00Z",
        "temp_K": 285.15,
        "temp_F": 53.6
      },
      ...
    ],
    "predicted_high_F": 57.8
  },
  ...
]
```

#### 5. METAR Observations

```typescript
GET /api/metar/observations?station_code=EGLC&event_day=2025-11-13

Response:
[
  {
    "observation_time_utc": "2025-11-13T00:00:00Z",
    "temp_F": 52.1,
    "temp_C": 11.2,
    "raw": "EGLC 130000Z 25008KT..."
  },
  ...
]
```

#### 6. Zeus vs METAR Comparison

```typescript
GET /api/compare/zeus-vs-metar?station_code=EGLC&event_day=2025-11-13

Response:
{
  "station_code": "EGLC",
  "event_day": "2025-11-13",
  "zeus_prediction_f": 57.8,
  "metar_actual_f": 58.2,
  "error_f": 0.4,
  "error_pct": 0.69,
  "zeus_bracket": "58-59°F",
  "metar_bracket": "58-59°F",
  "brackets_match": true
}
```

#### 7. Backtest Execution

```typescript
POST /api/backtest/run

Request:
{
  "start_date": "2025-11-01",
  "end_date": "2025-11-13",
  "stations": ["EGLC", "KLGA"],
  "bankroll_usd": 3000.0,
  "edge_min": 0.05,
  "fee_bp": 50,
  "slippage_bp": 30
}

Response:
{
  "job_id": "abc123",
  "status": "pending"
}

GET /api/backtest/status/{job_id}

Response:
{
  "job_id": "abc123",
  "status": "running",
  "progress": 0.65
}

GET /api/backtest/results/{job_id}

Response:
{
  "job_id": "abc123",
  "status": "completed",
  "result": {
    "total_trades": 156,
    "wins": 89,
    "losses": 52,
    "total_pnl_usd": 8240.0,
    "roi_pct": 17.6,
    ...
  }
}
```

### WebSocket Real-Time Updates

```typescript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/trading');

// Message types:
{
  "type": "cycle_complete",
  "data": {
    "station_code": "EGLC",
    "event_day": "2025-11-13",
    "timestamp": "2025-11-13T14:21:18Z"
  }
}

{
  "type": "trade_placed",
  "data": {
    "station_code": "EGLC",
    "event_day": "2025-11-13",
    "bracket": "58-59°F",
    "edge_pct": 26.25,
    "size_usd": 300.0
  }
}

{
  "type": "edges_updated",
  "data": {
    "summary": {
      "station_code": "EGLC",
      "event_day": "2025-11-13",
      "trade_count": 2,
      "total_size_usd": 600.0
    }
  }
}
```

---

## 🛠️ Technology Stack

### Recommended: React + TypeScript

**Why React:**
- Professional UI/UX
- Real-time WebSocket support
- Rich charting libraries
- Modern development experience

**Tech Stack:**
- **Framework**: React 18+ with TypeScript
- **Build Tool**: Vite
- **State Management**: React Query (TanStack Query) for server state
- **Charts**: Recharts or Chart.js
- **Styling**: Tailwind CSS or Material-UI
- **HTTP Client**: Axios or Fetch API
- **WebSocket**: Native WebSocket API or Socket.io-client

### Alternative: Streamlit (Python)

**Why Streamlit:**
- Faster to build (all Python)
- No API needed (reads files directly)
- Good for internal tools

**Tech Stack:**
- **Framework**: Streamlit
- **Charts**: Plotly or Altair
- **Data**: Pandas

---

## 📦 Project Setup

### Option 1: React + TypeScript (Recommended)

```bash
# Create new project
npm create vite@latest hermes-frontend -- --template react-ts
cd hermes-frontend

# Install dependencies
npm install
npm install @tanstack/react-query axios recharts tailwindcss
npm install -D @types/node

# Initialize Tailwind CSS
npx tailwindcss init -p

# Start development server
npm run dev
```

**Project Structure:**
```
hermes-frontend/
├── src/
│   ├── components/
│   │   ├── Dashboard/
│   │   │   ├── LiveDashboard.tsx
│   │   │   ├── StationSelector.tsx
│   │   │   ├── EventDaySelector.tsx
│   │   │   ├── ZeusForecastGraph.tsx
│   │   │   ├── EdgesTable.tsx
│   │   │   └── ActivityLog.tsx
│   │   ├── Historical/
│   │   │   ├── HistoricalBrowser.tsx
│   │   │   ├── StackedGraphs.tsx
│   │   │   └── SnapshotDrillDown.tsx
│   │   ├── Backtest/
│   │   │   ├── BacktestConfig.tsx
│   │   │   └── BacktestResults.tsx
│   │   └── common/
│   │       ├── StatusCard.tsx
│   │       └── LoadingSpinner.tsx
│   ├── api/
│   │   ├── client.ts
│   │   ├── endpoints.ts
│   │   └── websocket.ts
│   ├── hooks/
│   │   ├── useSystemStatus.ts
│   │   ├── useEdges.ts
│   │   ├── useActivityLogs.ts
│   │   └── useWebSocket.ts
│   ├── types/
│   │   └── api.ts
│   ├── config/
│   │   └── api.ts
│   ├── App.tsx
│   └── main.tsx
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

### Option 2: Streamlit (Python)

```bash
# Create new project
mkdir hermes-frontend
cd hermes-frontend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install streamlit pandas plotly requests

# Create main file
touch dashboard.py
```

**Project Structure:**
```
hermes-frontend/
├── dashboard.py
├── components/
│   ├── live_dashboard.py
│   ├── historical_browser.py
│   └── backtest_runner.py
├── api/
│   └── client.py
├── requirements.txt
└── README.md
```

---

## 🚀 Implementation Steps

### Step 1: API Client Setup

**React:**
```typescript
// src/api/client.ts
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// src/api/endpoints.ts
import { apiClient } from './client';

export const statusApi = {
  getStatus: () => apiClient.get('/api/status'),
};

export const edgesApi = {
  getCurrent: (params?: { station?: string; event_day?: string; limit?: number }) =>
    apiClient.get('/api/edges/current', { params }),
};

export const logsApi = {
  getActivity: (params?: { station?: string; event_day?: string; limit?: number; offset?: number }) =>
    apiClient.get('/api/logs/activity', { params }),
};
```

**Streamlit:**
```python
# api/client.py
import requests

API_BASE_URL = "http://localhost:8000"

def get_status():
    response = requests.get(f"{API_BASE_URL}/api/status")
    return response.json()

def get_current_edges(station=None, event_day=None, limit=None):
    params = {}
    if station:
        params["station_code"] = station
    if event_day:
        params["event_day"] = event_day
    if limit:
        params["limit"] = limit
    response = requests.get(f"{API_BASE_URL}/api/edges/current", params=params)
    return response.json()
```

### Step 2: Live Dashboard Component

**React:**
```typescript
// src/components/Dashboard/LiveDashboard.tsx
import { useQuery } from '@tanstack/react-query';
import { statusApi, edgesApi } from '../../api/endpoints';
import ZeusForecastGraph from './ZeusForecastGraph';
import EdgesTable from './EdgesTable';
import ActivityLog from './ActivityLog';

export default function LiveDashboard() {
  const { data: status } = useQuery({
    queryKey: ['status'],
    queryFn: () => statusApi.getStatus().then(res => res.data),
    refetchInterval: 5000, // Poll every 5 seconds
  });

  const { data: edges } = useQuery({
    queryKey: ['edges', 'current'],
    queryFn: () => edgesApi.getCurrent().then(res => res.data),
    refetchInterval: 15000, // Poll every 15 seconds
  });

  return (
    <div className="dashboard">
      <div className="status-bar">
        Status: {status?.trading_engine?.running ? '● RUNNING' : '○ STOPPED'}
        Cycle: {status?.current_cycle || 'N/A'}
      </div>
      
      <div className="main-content">
        <div className="left-panel">
          <ZeusForecastGraph station="EGLC" eventDay="2025-11-13" />
        </div>
        <div className="right-panel">
          <EdgesTable edges={edges || []} />
        </div>
      </div>
      
      <ActivityLog />
    </div>
  );
}
```

**Streamlit:**
```python
# components/live_dashboard.py
import streamlit as st
import plotly.graph_objects as go
from api.client import get_status, get_current_edges

def render_live_dashboard():
    st.title("🚀 Hermes Dynamic Paper Trading")
    
    # Status
    status = get_status()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Status", "RUNNING" if status["trading_engine"]["running"] else "STOPPED")
    with col2:
        st.metric("Cycle", status.get("current_cycle", "N/A"))
    
    # Edges table
    edges = get_current_edges()
    st.dataframe(edges)
    
    # Charts
    # ... (implement with Plotly)
```

### Step 3: Historical Browser with Stacked Graphs

**React:**
```typescript
// src/components/Historical/StackedGraphs.tsx
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ScatterChart, Scatter } from 'recharts';

export default function StackedGraphs({ zeusData, polymarketData, tradesData }) {
  return (
    <div className="stacked-graphs">
      {/* Graph 1: Zeus + METAR */}
      <ResponsiveContainer height={300}>
        <LineChart data={zeusData} syncId="historicalTimeline">
          <XAxis dataKey="time" />
          <YAxis domain={[50, 60]} label={{ value: 'Temperature (°F)', angle: -90 }} />
          <Tooltip />
          <Line type="monotone" dataKey="zeus_latest" stroke="#2563eb" strokeWidth={2} name="Zeus Latest" />
          <Line type="monotone" dataKey="metar_actual" stroke="#dc2626" strokeWidth={2} name="METAR Actual" />
        </LineChart>
      </ResponsiveContainer>
      
      {/* Graph 2: Polymarket */}
      <ResponsiveContainer height={300}>
        <LineChart data={polymarketData} syncId="historicalTimeline">
          <XAxis dataKey="time" />
          <YAxis domain={[0, 100]} label={{ value: 'Probability (%)', angle: -90 }} />
          <Tooltip />
          {brackets.map(bracket => (
            <Line key={bracket} dataKey={bracket} stroke={colors[bracket]} />
          ))}
        </LineChart>
      </ResponsiveContainer>
      
      {/* Graph 3: Trades */}
      <ResponsiveContainer height={200}>
        <ScatterChart data={tradesData} syncId="historicalTimeline">
          <XAxis dataKey="time" />
          <YAxis domain={[0, 500]} label={{ value: 'Trade Size ($)', angle: -90 }} />
          <Tooltip />
          <Scatter dataKey="size_usd" fill="#16a34a" />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
```

### Step 4: WebSocket Integration

**React:**
```typescript
// src/hooks/useWebSocket.ts
import { useEffect, useState } from 'react';

const WS_URL = 'ws://localhost:8000/ws/trading';

export function useWebSocket() {
  const [messages, setMessages] = useState([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      setConnected(true);
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setMessages(prev => [...prev, message]);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      setConnected(false);
    };

    return () => {
      ws.close();
    };
  }, []);

  return { messages, connected };
}
```

---

## 📝 Complete API Reference

See the running backend API documentation at:
**http://localhost:8000/docs**

All endpoints are documented with:
- Request parameters
- Response schemas
- Example requests/responses
- Try-it-out functionality

---

## ✅ Testing Checklist

### Functionality Tests

- [ ] System status displays correctly
- [ ] Current edges table shows data
- [ ] Station selector works
- [ ] Event day selector works
- [ ] Zeus forecast graph displays
- [ ] METAR data overlays correctly
- [ ] Activity log filters work
- [ ] Historical browser loads data
- [ ] Stacked graphs display correctly
- [ ] Backtest runner submits jobs
- [ ] Backtest results display
- [ ] WebSocket connects and receives messages
- [ ] Real-time updates work

### Integration Tests

- [ ] All API endpoints connect successfully
- [ ] Error handling works (API down, network errors)
- [ ] Loading states display correctly
- [ ] Empty states display correctly
- [ ] Data refresh works
- [ ] Filters persist across page navigation

---

## 🚀 Deployment

### Development

```bash
# React
npm run dev
# Access at http://localhost:5173

# Streamlit
streamlit run dashboard.py
# Access at http://localhost:8501
```

### Production

**React:**
```bash
npm run build
# Deploy dist/ folder to Vercel, Netlify, or any static host
```

**Streamlit:**
```bash
# Deploy to Streamlit Cloud or run on server
streamlit run dashboard.py --server.port 8501
```

---

## 📚 Additional Resources

- **Backend API Docs**: http://localhost:8000/docs
- **React Query Docs**: https://tanstack.com/query/latest
- **Recharts Docs**: https://recharts.org/
- **Streamlit Docs**: https://docs.streamlit.io/

---

## 🆘 Troubleshooting

### API Connection Issues

**Problem**: Frontend can't connect to backend API

**Solution**:
1. Verify backend is running: `curl http://localhost:8000/api/status`
2. Check CORS settings in backend (should allow all origins for dev)
3. Verify API_BASE_URL in frontend config

### WebSocket Connection Issues

**Problem**: WebSocket fails to connect

**Solution**:
1. Verify WebSocket endpoint: `ws://localhost:8000/ws/trading`
2. Check backend WebSocket route is registered
3. Check browser console for connection errors

### Data Not Displaying

**Problem**: API returns data but frontend doesn't show it

**Solution**:
1. Check browser console for errors
2. Verify data structure matches expected format
3. Check React Query cache/refetch settings
4. Verify date/time formatting

---

**Ready to build!** 🚀

This document contains everything needed to build the Hermes frontend dashboard as a separate project. The backend API must be running separately, and the frontend connects to it via REST API and WebSocket.

