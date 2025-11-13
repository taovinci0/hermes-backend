# Hermes Frontend Architecture & Implementation Guide

**Date**: November 13, 2025  
**Purpose**: Design a web frontend for Hermes trading system  
**Current State**: Backend-only (CLI)  
**Goal**: Full-stack trading dashboard with live monitoring, backtesting, and configuration

---

## 🎯 Vision

### What You Want:

A web-based dashboard where you can:

1. **Monitor Live Trading**
   - Watch dynamic paper trading in real-time
   - See current edges, trades placed, P&L
   - View Zeus forecasts vs market prices
   - Track system health

2. **View Historical Data**
   - Browse collected snapshots
   - Visualize forecast evolution
   - Analyze past trades
   - Compare Zeus predictions vs actual outcomes

3. **Run Backtests**
   - Select date range
   - Configure trading parameters (edge_min, kelly_cap, etc.)
   - Choose probability model (spread vs bands)
   - Run backtests on collected data
   - View results with charts

4. **Compare Configurations**
   - Run multiple backtest configurations simultaneously
   - Compare: spread vs bands, different edge thresholds, Kelly caps
   - Find optimal configuration for historical period
   - Visual comparison dashboard

---

## 🏗️ Architecture Overview

### Current System (Backend Only):

```
┌─────────────────────────────────────────────────────────┐
│                    CLI (orchestrator.py)                │
│  python -m core.orchestrator --mode dynamic-paper       │
└─────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────┐
│              Hermes Backend (Python)                    │
│  • Zeus API calls                                       │
│  • Polymarket API calls                                 │
│  • Probability mapping                                  │
│  • Edge calculation                                     │
│  • Paper trading execution                              │
│  • Snapshot storage (JSON files)                        │
└─────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────┐
│              File System Storage                        │
│  • data/snapshots/dynamic/                              │
│  • data/trades/                                         │
│  • data/runs/backtests/                                 │
└─────────────────────────────────────────────────────────┘
```

### Proposed System (Full Stack):

```
┌─────────────────────────────────────────────────────────┐
│              Frontend (React/Next.js)                   │
│  • Dashboard                                            │
│  • Live trading view                                    │
│  • Historical data browser                              │
│  • Backtest configurator                                │
│  • Results visualization                                │
└─────────────────────────────────────────────────────────┘
                           │
                    HTTP/WebSocket
                           │
                           ↓
┌─────────────────────────────────────────────────────────┐
│              REST API (FastAPI/Flask)                   │
│  • GET /status - System health                          │
│  • GET /trades/live - Current trades                    │
│  • GET /snapshots - Historical data                     │
│  • POST /backtest/run - Execute backtest                │
│  • GET /backtest/results - Get results                  │
│  • WebSocket /ws - Real-time updates                    │
└─────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────┐
│           Hermes Backend (Existing Python)              │
│  • Dynamic trading engine                               │
│  • Backtester                                           │
│  • Data access layer                                    │
└─────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────┐
│        Database (Optional) + File Storage               │
│  • PostgreSQL/SQLite (structured data)                  │
│  • File system (snapshots, CSVs)                        │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 Feature Breakdown

### 1. Live Trading Dashboard (Enhanced)

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

[Example when viewing Nov 14 (Tomorrow):]

┌──────────────────────────────────────┬──────────────────────────────────────────────┐
│ 🌡️  ZEUS FORECAST EVOLUTION          │  📊 CURRENT EDGES (London, Nov 14)          │
│ London (EGLC) - Nov 14, 2025 (Tmrw) │                                              │
│ Market Status: ✅ OPEN (1d advance)  │  Bracket │Zeus│Market│ Edge │  Size │Status │
│                                      │  ────────┼────┼──────┼──────┼───────┼───────│
│ [Live Graph - Updates Every 15 min] │  59-60°F │31.2│ 8.15%│21.45%│$300.00│✅ TRADE│
│   62°F┤                              │  60-61°F │28.7│ 12.3%│15.20%│$200.00│✅ TRADE│
│       │    ━━━━━━ Zeus Latest       │  61-62°F │19.4│ 45.2%│-26.6%│   -   │❌ SKIP │
│   60°F┤  ┅┅┅┅┅┅ Zeus 15 min ago     │                                              │
│       │  ········ Zeus 30 min ago    │  💰 Trades This Cycle: 2                     │
│   58°F┤                              │  💵 Total Size: $500.00                      │
│       │  (No METAR yet - future)     │                                              │
│   56°F┤         ┅       ━            │  📈 Today's Summary (Nov 14):                │
│       │      ┅┅┅··   ━━━━            │  Cycles: 12 | Trades: 8 | Size: $2,400     │
│   54°F┤   ┅┅┅·····━━━━               │  Avg Edge: 17.8%                            │
│       └─────────────────────────────┘│                                              │
│        00  04  08  12  16  20  24    │  ℹ️  METAR data will appear when Nov 14     │
│                                      │     begins (in 9 hours)                     │
│ Legend:                              │                                              │
│ ━━━ Current Zeus (14:21)             │                                              │
│ ┅┅┅ Zeus 15min ago (14:06)          │                                              │
│ ··· Zeus 30min ago (13:51)          │                                              │
│ ⚠️  No METAR yet (event is tomorrow)│                                              │
└──────────────────────────────────────┴──────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 📜 LIVE AGENT ACTIVITY LOG                                      [Auto-scroll] [⏸️ ] │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ Filters:  Station: [EGLC (London) ▼]  Event Day: [Nov 13 (Today) ▼]  [Clear All] │
│           🔍 Showing logs for: London, Nov 13, 2025                                 │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ [14:21:10] 🔄 Starting evaluation cycle #45                                         │
│ [14:21:12] 🌡️  Fetched Zeus forecast for EGLC (Nov 13) → High: 57.8°F             │
│ [14:21:14] 💰 Fetched Polymarket prices for London Nov 13 → 12 brackets             │
│ [14:21:16] 🧮 Calculated probabilities (spread model)                               │
│            • 58-59°F: p_zeus=28.3%, p_market=0.05%, edge=26.25% ✅                  │
│            • 60-61°F: p_zeus=33.5%, p_market=6.95%, edge=25.75% ✅                  │
│            • 62-63°F: p_zeus=22.1%, p_market=85.00%, edge=-63.70% ❌               │
│ [14:21:18] 📝 Placed 2 paper trades → Total: $600.00                               │
│ [14:21:18] 💾 Saved snapshots (zeus/polymarket/decisions)                          │
│ [14:21:18] ✅ Cycle #45 complete. Next cycle in 15:00                              │
│ [14:21:18] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│ [14:06:10] 🔄 Starting evaluation cycle #44                                         │
│ [14:06:12] 🌡️  Fetched Zeus forecast for EGLC (Nov 13) → High: 58.1°F             │
│ [14:06:14] 💰 Fetched Polymarket prices for London Nov 13 → 12 brackets             │
│ [14:06:16] 🧮 Calculated probabilities (spread model)                               │
│            • 58-59°F: p_zeus=25.2%, p_market=0.04%, edge=24.36% ✅                  │
│            • 60-61°F: p_zeus=31.8%, p_market=7.12%, edge=23.88% ✅                  │
│ [14:06:18] 📝 Placed 2 paper trades → Total: $600.00                               │
│            ... 45 more log entries for Nov 13 (scroll to see all)                   │
└─────────────────────────────────────────────────────────────────────────────────────┘

[Example with different filters:]

┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 📜 LIVE AGENT ACTIVITY LOG                                      [Auto-scroll] [⏸️ ] │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ Filters:  Station: [KLGA (NYC) ▼]  Event Day: [Nov 14 (Tomorrow) ▼]  [Clear All]  │
│           🔍 Showing logs for: New York, Nov 14, 2025                               │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ [14:20:15] 🔄 Starting evaluation cycle #12                                         │
│ [14:20:17] 🌡️  Fetched Zeus forecast for KLGA (Nov 14) → High: 51.3°F             │
│ [14:20:19] 💰 Fetched Polymarket prices for NYC Nov 14 → 11 brackets                │
│ [14:20:21] 🧮 Calculated probabilities (spread model)                               │
│            • 50-51°F: p_zeus=29.1%, p_market=12.3%, edge=16.0% ✅                   │
│            • 51-52°F: p_zeus=26.4%, p_market=14.5%, edge=11.1% ✅                   │
│ [14:20:23] 📝 Placed 2 paper trades → Total: $500.00                               │
│ [14:20:23] 💾 Saved snapshots (zeus/polymarket/decisions)                          │
│ [14:20:23] ✅ Cycle #12 complete. Next cycle in 15:00                              │
│ [14:20:23] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│ [14:05:15] 🔄 Starting evaluation cycle #11                                         │
│ [14:05:17] 🌡️  Fetched Zeus forecast for KLGA (Nov 14) → High: 51.1°F             │
│            ... 12 more log entries for Nov 14 (scroll to see all)                   │
└─────────────────────────────────────────────────────────────────────────────────────┘

[Example with "All" filter:]

┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 📜 LIVE AGENT ACTIVITY LOG                                      [Auto-scroll] [⏸️ ] │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ Filters:  Station: [All Stations ▼]  Event Day: [All Days ▼]  [Clear All]         │
│           🔍 Showing logs for: All stations, All event days                         │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ [14:21:10] 🔄 [EGLC, Nov 13] Starting evaluation cycle #45                         │
│ [14:21:12] 🌡️  [EGLC, Nov 13] Fetched Zeus → High: 57.8°F                         │
│ [14:21:18] 📝 [EGLC, Nov 13] Placed 2 paper trades → $600.00                       │
│ [14:20:15] 🔄 [KLGA, Nov 14] Starting evaluation cycle #12                         │
│ [14:20:17] 🌡️  [KLGA, Nov 14] Fetched Zeus → High: 51.3°F                         │
│ [14:20:23] 📝 [KLGA, Nov 14] Placed 2 paper trades → $500.00                       │
│ [14:15:20] 🔄 [EGLC, Nov 15] Starting evaluation cycle #3                          │
│ [14:15:22] 🌡️  [EGLC, Nov 15] Fetched Zeus → High: 55.4°F                         │
│ [14:15:28] 📝 [EGLC, Nov 15] Placed 1 paper trade → $300.00                        │
│            ... logs from all stations and days (can get busy!)                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

**Filter Options:**

**Station Dropdown:**
- All Stations (shows everything)
- EGLC (London)
- KLGA (NYC)
- [Any other active stations]

**Event Day Dropdown:**
- All Days (shows everything)
- ── Recent Days ──
- Nov 10 (3 days ago)
- Nov 11 (2 days ago)
- Nov 12 (Yesterday)
- ── Active Markets ──
- Nov 13 (Today) ✅
- Nov 14 (Tomorrow) ✅
- Nov 15 (Day After) ✅

**Behavior:**
- Filters work in combination (Station AND Event Day)
- "All" options show unfiltered logs with [Station, Date] tags
- Recent days (3 days back) available for review
- Only shows days that have log data
- Real-time updates respect current filters
- "Clear All" resets to show everything

**Key Features:**

1. **Station Selector**
   - Toggle between active stations (EGLC, KLGA, etc.)
   - "View All" shows summary cards for all stations
   - Each station has its own real-time data

2. **Event Day Selector** ⭐ NEW
   - Toggle between days with **OPEN markets** (tradeable now)
   - Shows: Today, Tomorrow, Day After (if markets open)
   - Each day shows market status (Open ✅ or not yet available)
   - Example: Nov 13 (today), Nov 14 (tomorrow), Nov 15 (day after)
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

**Data Needed from API:**
- Current cycle number
- Time until next cycle
- Current edges for all stations/events
- Trades placed this cycle
- Today's cumulative stats

**API Endpoints:**
```
GET /api/status
→ {
    "running": true,
    "current_cycle": 45,
    "next_cycle_in_seconds": 154,
    "stations": ["EGLC", "KLGA"],
    "interval_seconds": 900
  }

GET /api/edges/current
→ {
    "timestamp": "2025-11-13T14:30:00Z",
    "edges": [
      {
        "station": "EGLC",
        "city": "London",
        "event_day": "2025-11-13",
        "bracket": "58-59°F",
        "p_zeus": 0.283,
        "p_market": 0.0005,
        "edge": 0.2625,
        "size_usd": 300.0,
        "decision": "trade"
      },
      ...
    ]
  }

WebSocket /ws/trades
→ Real-time updates when trades placed

GET /api/logs/activity
→ {
    "station": "EGLC",  // optional, omit for all
    "date": "2025-11-13",  // optional, omit for all
    "limit": 100  // optional, default 50
  }
→ Returns filtered activity logs
  {
    "logs": [
      {
        "timestamp": "2025-11-13T14:21:10Z",
        "station": "EGLC",
        "event_day": "2025-11-13",
        "cycle": 45,
        "action": "start_cycle",
        "message": "Starting evaluation cycle #45"
      },
      {
        "timestamp": "2025-11-13T14:21:12Z",
        "station": "EGLC",
        "event_day": "2025-11-13",
        "cycle": 45,
        "action": "fetch_zeus",
        "message": "Fetched Zeus forecast → High: 57.8°F",
        "data": {"predicted_high": 57.8}
      },
      ...
    ],
    "total": 234,
    "filtered_by": {
      "station": "EGLC",
      "date": "2025-11-13"
    }
  }

GET /api/logs/available-dates
→ Returns list of dates that have log data
  {
    "dates": [
      {"date": "2025-11-13", "label": "Today", "has_logs": true},
      {"date": "2025-11-14", "label": "Tomorrow", "has_logs": true},
      {"date": "2025-11-15", "label": "Day After", "has_logs": false},
      {"date": "2025-11-12", "label": "Yesterday", "has_logs": true},
      {"date": "2025-11-11", "label": "2 days ago", "has_logs": true}
    ]
  }
```

---

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

┌──────────────────────────────────── NOV 15 (DAY AFTER) ────────────────────────────┐
│ Markets open 2 days in advance - early positioning!                                 │
│                                                                                     │
│ ┌─────────────────────────────────┬─────────────────────────────────────────────┐ │
│ │ 🌡️  LONDON (EGLC)               │  🌡️  NEW YORK (KLGA)                       │ │
│ ├─────────────────────────────────┼─────────────────────────────────────────────┤ │
│ │ Zeus High: 55.4°F               │  Zeus High: 46.8°F                          │ │
│ │ METAR: ⏳ Not yet (future)      │  METAR: ⏳ Not yet (future)                 │ │
│ │                                 │                                             │ │
│ │ Latest Trades:                  │  Latest Trades:                             │ │
│ │ • 55-56°F @ 14:15 (+19%)       │  • No trades yet                            │ │
│ │                                 │                                             │ │
│ │ Today: 1 trade, $300            │  Today: 0 trades, $0                        │ │
│ │ Avg Edge: 19.0%                 │  Avg Edge: N/A                              │ │
│ │                                 │                                             │ │
│ │ [View Details →]                │  [View Details →]                           │ │
│ └─────────────────────────────────┴─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 📊 COMBINED SUMMARY (All Stations, All Event Days)                                  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ Total Active Markets: 6 events (3 days × 2 stations)                               │
│ Total Trades Today (all events): 16                                                 │
│ Total Size: $4,600                                                                  │
│ Average Edge: 17.9%                                                                 │
│ Active Brackets: 36 across all markets                                              │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

**Use Cases:**
- Quick overview of all active trading (today + future)
- Compare performance across stations AND event days
- See which events have better edges
- Monitor early positioning for future events
- Identify where METAR data is available vs not yet
- Monitor system health at a glance

**Key Visual Cues:**
- ✅ METAR available (current day - actual temps)
- ⏳ METAR not yet (future days - will start when day arrives)
- Event day prominently labeled (Today, Tomorrow, Day After)

Click "View Details" on any station/day → switches to single station view for that event

---

### 2. Historical Data Browser (Enhanced - Stacked Timeline View)

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
│   75%┤  ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ 60-61°F (Market favorite)                        │
│      │                                                                              │
│   50%┤  ▬▬▬▬▬▬▬▬▬▬▬▬▬▬ 58-59°F (Zeus pick)                                       │
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

┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 📊 INTERACTIVE FEATURES                                                             │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│ ⚡ Hover over any time:                                                            │
│    • Vertical line appears across all 3 graphs                                     │
│    • Tooltips show exact values at that moment                                     │
│    • See: Zeus temp, Market prices, Trades (if any)                               │
│                                                                                     │
│ 🖱️  Click any point:                                                               │
│    • Popup shows detailed snapshot from all 3 sources                              │
│    • Zeus: Full 24-hour forecast, sigma, model used                               │
│    • Polymarket: All bracket prices, liquidity, spread                             │
│    • Decisions: Edge calculation breakdown, Kelly sizing                           │
│                                                                                     │
│ 🎚️  Toggle controls:                                                               │
│    [✓] Show Zeus evolution lines  [✓] Show METAR actual  [✓] Show all brackets   │
│    [ ] Compact mode (combine graphs 1&2)                                           │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────┬──────────────────────────────────────────────┐
│ 📊 ZEUS PREDICTION ACCURACY          │  💰 TRADING DECISIONS SUMMARY                │
│                                      │                                              │
│ Zeus Predicted High: 57.8°F          │  Total Trades: 6                             │
│ Actual High (METAR): 58.2°F          │  Total Size: $1,800.00                       │
│ Error: +0.4°F (0.7%)                 │  Avg Edge: 20.8%                             │
│                                      │                                              │
│ Zeus Confidence Evolution:           │  Decision Timeline:                          │
│ • 09:00 → 56.5°F                    │  • 09:15 → Traded 58-59°F (Zeus win)        │
│ • 12:00 → 57.2°F (+0.7°F)          │  • 10:30 → Traded 58-59°F (Zeus win)        │
│ • 15:00 → 57.8°F (+0.6°F)          │  • 12:00 → Switched to 60-61°F              │
│ • 18:00 → 57.8°F (stable)          │  • 13:45 → Traded 60-61°F (Market win)      │
│                                      │  • 15:15 → Traded 60-61°F (Market win)      │
│ Peak Variance: 1.3°F                 │  • 16:30 → Traded 60-61°F (Market win)      │
│ Final Accuracy: 99.3%                │                                              │
│                                      │  Outcome:                                    │
│ ✅ Zeus correctly bracketed result  │  • Zeus brackets: 2/6 wins                   │
│ ✅ Within ±1°F threshold            │  • Market brackets: 4/6 wins                 │
│                                      │  • Overall P&L: TBD (pending resolution)     │
└──────────────────────────────────────┴──────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 🔍 SNAPSHOT DRILL-DOWN (Click any point on graph)                                  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ Time: 12:00:00 UTC                                                                  │
│                                                                                     │
│ ┌─ Zeus Snapshot ────────────────────┬─ Polymarket Snapshot ──────────────────────┐│
│ │ Predicted High: 57.2°F             │ Brackets (YES price):                       ││
│ │ Timeseries: 24 hourly points       │ • 56-57°F → $0.15 (15%)                    ││
│ │ Model: spread                      │ • 57-58°F → $0.22 (22%)                    ││
│ │ Sigma: 2.1°F                       │ • 58-59°F → $0.35 (35%) ← Our edge here    ││
│ │                                    │ • 59-60°F → $0.18 (18%)                    ││
│ │ Hourly breakdown:                  │ • 60-61°F → $0.07 (7%)                     ││
│ │ 12:00 → 56.8°F                    │                                             ││
│ │ 13:00 → 57.2°F ← Peak             │ Liquidity:                                  ││
│ │ 14:00 → 56.5°F                    │ • 58-59°F → $1,200 available               ││
│ │ ...                                │ • Spread: 1.2%                              ││
│ └────────────────────────────────────┴─────────────────────────────────────────────┘│
│                                                                                     │
│ ┌─ Decision Snapshot ────────────────────────────────────────────────────────────┐ │
│ │ Edge Calculation:                                                               │ │
│ │ • p_zeus (58-59°F) = 28.5%                                                     │ │
│ │ • p_market (58-59°F) = 35.0%                                                   │ │
│ │ • Raw edge = -6.5% (negative! market overprices)                              │ │
│ │ • Decision: NO TRADE (edge < 5% threshold)                                     │ │
│ │                                                                                 │ │
│ │ • p_zeus (60-61°F) = 33.8%                                                     │ │
│ │ • p_market (60-61°F) = 7.0%                                                    │ │
│ │ • Raw edge = 26.8% - 0.5% fee - 0.3% slippage = 26.0%                         │ │
│ │ • Kelly size = 26.0% * $3000 * 10% cap = $300                                 │ │
│ │ • Decision: ✅ TRADE $300 on 60-61°F                                           │ │
│ └─────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

**Key Features:**

1. **Three Stacked Graphs (Time-Aligned)**
   - **Graph 1 (Top)**: Zeus forecast evolution + METAR actual temperatures
     - Shows how Zeus predictions changed throughout the day (fading lines)
     - Overlays actual METAR observations (hourly dots)
     - Clear temperature scale (°F) appropriate for the data
   - **Graph 2 (Middle)**: Polymarket implied probabilities for all brackets
     - Shows market-implied probability for each temperature bracket over time
     - Multiple lines (one per bracket) showing how market pricing evolved
     - Percentage scale (0-100%) appropriate for probability data
   - **Graph 3 (Bottom)**: Trading decisions timeline
     - Shows when trades were placed, what bracket, size, and edge
     - Discrete markers with annotations for context
     - Dollar scale showing trade size

2. **Why Stacked Works Better**
   - ✅ **No scale confusion** - Each data type gets its own appropriate Y-axis
   - ✅ **Clear and readable** - No overlapping lines or cluttered dual axes
   - ✅ **Easy to correlate** - Time-aligned X-axis lets you see "what happened when"
   - ✅ **Tells the story** - Read top to bottom to understand the full picture
   - ✅ **Proven pattern** - Same layout used by TradingView, Bloomberg Terminal

3. **Interactive Features**
   - **Hover**: Vertical line appears across all 3 graphs showing values at that moment
   - **Click**: Popup with detailed snapshots from all 3 data sources (Zeus/Polymarket/Decisions)
   - **Toggles**: Show/hide specific data layers, enable compact mode
   - **Drill-down**: Click any trade marker to see full edge calculation breakdown

4. **Accuracy Analysis**
   - Compare Zeus final prediction vs METAR actual (shown in Graph 1)
   - Track how Zeus forecast evolved over time (fading lines)
   - See which trades were right/wrong (annotations on Graph 3)
   - Calculate prediction error and accuracy metrics

5. **Trading Context**
   - See WHY we made each trade (edge % shown on Graph 3)
   - See WHEN market prices changed (Graph 2 evolution)
   - See HOW Zeus forecast updated (Graph 1 evolution)
   - Understand relationship between all three data sources

**Implementation Notes:**

**Why Three Separate Graphs?**
- Different data types require different scales:
  - Temperatures: 50-60°F range (10 degree span)
  - Probabilities: 0-100% range (percentage scale)
  - Trades: Discrete events (not continuous)
- Attempting to plot on one graph with dual Y-axes creates confusion
- Stacked graphs with shared X-axis (time) makes correlations obvious
- This is the proven pattern used by professional trading platforms

**Charting Libraries:**
```typescript
// Recommended: Recharts (React)
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

// Graph 1: Zeus + METAR
<ResponsiveContainer height={300}>
  <LineChart data={zeusData} syncId="historicalTimeline">
    <XAxis dataKey="time" />
    <YAxis domain={[50, 60]} label="Temperature (°F)" />
    <Line type="monotone" dataKey="zeus_latest" stroke="#2563eb" strokeWidth={2} />
    <Line type="monotone" dataKey="zeus_15m" stroke="#2563eb" strokeWidth={1} strokeOpacity={0.5} />
    <Line type="monotone" dataKey="metar_actual" stroke="#dc2626" strokeWidth={2} />
    <Tooltip />
  </LineChart>
</ResponsiveContainer>

// Graph 2: Polymarket (sync'd by syncId)
<ResponsiveContainer height={300}>
  <LineChart data={polymarketData} syncId="historicalTimeline">
    <XAxis dataKey="time" />
    <YAxis domain={[0, 100]} label="Probability (%)" />
    {brackets.map(bracket => (
      <Line key={bracket} dataKey={bracket} stroke={colors[bracket]} />
    ))}
    <Tooltip />
  </LineChart>
</ResponsiveContainer>

// Graph 3: Trades (sync'd by syncId)
<ResponsiveContainer height={200}>
  <ScatterChart data={tradesData} syncId="historicalTimeline">
    <XAxis dataKey="time" />
    <YAxis domain={[0, 500]} label="Trade Size ($)" />
    <Scatter dataKey="size_usd" fill="#16a34a" />
    <Tooltip content={<TradeTooltip />} />
  </ScatterChart>
</ResponsiveContainer>
```

**Key Implementation Details:**
- `syncId="historicalTimeline"` syncs all 3 graphs - hover on one affects all
- Each chart maintains its own Y-axis scale
- All share the same X-axis (time) for perfect alignment
- Tooltips can be customized to show context from all 3 data sources

**Data Needed from API:**
- List of available dates with snapshots
- Zeus, Polymarket, and Decision snapshots for a given date/station
- METAR actual temperatures
- Aggregated statistics across all three data sources

**API Endpoints:**
```
GET /api/snapshots/dates
→ ["2025-11-13", "2025-11-14", ...]

GET /api/snapshots/zeus?station=EGLC&date=2025-11-13
→ [
    {
      "fetch_time": "2025-11-13T09:00:00Z",
      "predicted_high": 57.8,
      "timeseries": [...]
    },
    ...
  ]

GET /api/snapshots/decisions?station=EGLC&date=2025-11-13
→ [
    {
      "decision_time": "2025-11-13T14:30:00Z",
      "trades": [...],
      "total_edge": 0.52
    },
    ...
  ]

GET /api/metar/actual?station=EGLC&date=2025-11-13
→ {
    "station": "EGLC",
    "date": "2025-11-13",
    "observations": [
      {
        "time": "2025-11-13T00:00:00Z",
        "temp_F": 52.1,
        "raw": "EGLC 130000Z 25008KT..."
      },
      ...
    ],
    "daily_high": 58.2,
    "daily_low": 50.3
  }

GET /api/compare/zeus-vs-actual?station=EGLC&date=2025-11-13
→ {
    "zeus_predicted_high": 57.8,
    "actual_high": 58.2,
    "error": 0.4,
    "error_pct": 0.69,
    "accuracy_within_1F": true
  }
```

---

## 🌡️ METAR API Integration

### Why METAR?

**METAR (Meteorological Aerodrome Report)** is the official weather observation system used by:
- ✅ Aviation weather services worldwide
- ✅ **Polymarket for temperature market resolution**
- ✅ National Weather Service (NWS)

**Critical**: Since Polymarket uses METAR data to resolve temperature markets, integrating METAR into Hermes gives us:
1. **Real-time ground truth** - See actual temperatures as they happen
2. **Forecast accuracy tracking** - Compare Zeus predictions vs reality
3. **Resolution preview** - Know which bracket will win before Polymarket resolves
4. **System validation** - Confirm our trading logic matches Polymarket's resolution logic

### METAR Data Source

**Aviation Weather Center Data API**  
URL: https://aviationweather.gov/data/api/

**Key Details:**
- **Coverage**: Worldwide weather stations
- **Update Frequency**: Every minute (new METARs typically every hour)
- **Historical Data**: Last 15 days available
- **Formats**: JSON, XML, CSV, GeoJSON
- **Rate Limit**: 100 requests per minute
- **Cost**: Free (U.S. Government service)

### METAR API Endpoints

**Get Recent METARs:**
```
GET https://aviationweather.gov/api/data/metar?ids=EGLC&format=json&hours=24
```

**Response Example:**
```json
[
  {
    "receiptTime": "2025-11-13T14:52:00Z",
    "obsTime": "2025-11-13T14:50:00Z",
    "reportTime": "2025-11-13T14:50:00Z",
    "temp": 12.0,
    "dewp": 8.0,
    "wdir": 250,
    "wspd": 8,
    "wgst": null,
    "visib": "9999",
    "altim": 29.92,
    "rawOb": "EGLC 131450Z 25008KT 9999 FEW025 12/08 Q1013",
    "name": "LONDON CITY AIRPORT",
    "icaoId": "EGLC",
    "lat": 51.505,
    "lon": 0.05,
    "elev": 19
  }
]
```

**Key Fields:**
- `temp`: Temperature in **Celsius**
- `obsTime`: Observation timestamp (UTC)
- `rawOb`: Raw METAR string
- `name`: Station name

### Integration Architecture

```python
# backend/api/services/metar_service.py
import requests
from datetime import datetime, timedelta
from typing import List, Dict

class METARService:
    """Fetch and parse METAR observations from Aviation Weather Center."""
    
    BASE_URL = "https://aviationweather.gov/api/data/metar"
    
    def get_observations(
        self,
        station_code: str,
        hours: int = 24,
        date: str = None
    ) -> List[Dict]:
        """Fetch METAR observations for a station.
        
        Args:
            station_code: ICAO station code (e.g., "EGLC", "KLGA")
            hours: Hours of data to fetch (default 24)
            date: Optional date (YYYY-MM-DD) for historical data
        
        Returns:
            List of observations with temp in Fahrenheit
        """
        params = {
            "ids": station_code,
            "format": "json",
            "hours": hours,
        }
        
        # If date specified, calculate start time
        if date:
            dt = datetime.fromisoformat(date)
            params["date"] = dt.strftime("%Y%m%d")
        
        try:
            response = requests.get(
                self.BASE_URL,
                params=params,
                timeout=30,
                headers={"User-Agent": "HermesTradingSystem/1.0"}
            )
            response.raise_for_status()
            data = response.json()
            
            # Convert temps to Fahrenheit
            observations = []
            for obs in data:
                if obs.get("temp") is not None:
                    observations.append({
                        "time": obs["obsTime"],
                        "temp_C": obs["temp"],
                        "temp_F": round(obs["temp"] * 9/5 + 32, 1),
                        "raw": obs["rawOb"],
                    })
            
            return observations
            
        except requests.exceptions.RequestException as e:
            logger.error(f"METAR API error: {e}")
            return []
    
    def get_daily_high(
        self,
        station_code: str,
        date: str
    ) -> float:
        """Get daily high temperature from METAR observations.
        
        This is the actual temperature that Polymarket will use
        for resolution.
        
        Args:
            station_code: ICAO station code
            date: Date in YYYY-MM-DD format
        
        Returns:
            Daily high temperature in Fahrenheit
        """
        observations = self.get_observations(station_code, hours=24, date=date)
        
        if not observations:
            return None
        
        temps = [obs["temp_F"] for obs in observations]
        return max(temps)
```

### API Endpoints to Add

```python
# backend/api/routes/metar.py
from fastapi import APIRouter, HTTPException
from services.metar_service import METARService

router = APIRouter()
metar_service = METARService()

@router.get("/api/metar/observations")
def get_metar_observations(
    station: str,
    date: str = None,
    hours: int = 24
):
    """Get METAR observations for a station."""
    observations = metar_service.get_observations(station, hours, date)
    
    if not observations:
        raise HTTPException(404, "No METAR data available")
    
    return {
        "station": station,
        "observations": observations,
        "count": len(observations)
    }

@router.get("/api/metar/daily-high")
def get_daily_high(station: str, date: str):
    """Get daily high temperature (what Polymarket uses for resolution)."""
    daily_high = metar_service.get_daily_high(station, date)
    
    if daily_high is None:
        raise HTTPException(404, "No METAR data for date")
    
    return {
        "station": station,
        "date": date,
        "daily_high_F": daily_high
    }

@router.get("/api/compare/zeus-vs-metar")
def compare_zeus_vs_metar(station: str, date: str):
    """Compare Zeus predictions vs METAR actual temperatures."""
    
    # Get Zeus snapshots for the day
    from services.snapshot_service import SnapshotService
    snapshot_service = SnapshotService()
    
    zeus_snapshots = snapshot_service.get_zeus_snapshots(station, date)
    
    if not zeus_snapshots:
        raise HTTPException(404, "No Zeus data for date")
    
    # Get final Zeus prediction (last snapshot of day)
    final_zeus = zeus_snapshots[-1]
    zeus_predicted_high = max(
        (p["temp_K"] - 273.15) * 9/5 + 32 
        for p in final_zeus["timeseries"]
    )
    
    # Get METAR actual
    actual_high = metar_service.get_daily_high(station, date)
    
    if actual_high is None:
        return {
            "zeus_predicted_high": zeus_predicted_high,
            "actual_high": None,
            "error": None,
            "status": "pending"
        }
    
    error = actual_high - zeus_predicted_high
    error_pct = abs(error / actual_high * 100)
    
    return {
        "station": station,
        "date": date,
        "zeus_predicted_high": round(zeus_predicted_high, 1),
        "actual_high": round(actual_high, 1),
        "error": round(error, 1),
        "error_pct": round(error_pct, 2),
        "accuracy_within_1F": abs(error) <= 1.0,
        "accuracy_within_2F": abs(error) <= 2.0,
    }
```

### Frontend Integration

**Live Dashboard:**
```typescript
// Fetch METAR observations every minute
const { data: metar } = useQuery({
  queryKey: ['metar', station, today],
  queryFn: () => fetch(`/api/metar/observations?station=${station}&hours=24`),
  refetchInterval: 60000, // 1 minute
});

// Overlay on Zeus forecast graph
<LineChart>
  <Line data={zeusForecasts} stroke="blue" name="Zeus" />
  <Line data={metar.observations} stroke="red" name="Actual" strokeWidth={2} />
</LineChart>
```

**Historical View:**
```typescript
// Compare Zeus vs METAR for historical accuracy
const { data: comparison } = useQuery({
  queryKey: ['compare', station, date],
  queryFn: () => fetch(`/api/compare/zeus-vs-metar?station=${station}&date=${date}`),
});

// Show accuracy metrics
<AccuracyCard>
  Zeus: {comparison.zeus_predicted_high}°F
  Actual: {comparison.actual_high}°F
  Error: {comparison.error}°F ({comparison.error_pct}%)
  {comparison.accuracy_within_1F && <Badge>✅ Within 1°F</Badge>}
</AccuracyCard>
```

### Data Flow Example

**Live Trading Day:**

```
1. 09:00 → Zeus predicts 58°F high
   └─ Display on graph (blue line)

2. 10:00 → METAR reports 52°F (actual)
   └─ Display on graph (red dot)

3. 10:15 → Zeus updates to 57°F high
   └─ Update blue line (previous fades)

4. 11:00 → METAR reports 54°F (actual)
   └─ Add red dot

5. ... continues throughout day ...

6. End of day:
   - Zeus final: 57.8°F
   - METAR high: 58.2°F
   - Error: 0.4°F (accurate!)
   - Winning bracket: 58-59°F (METAR confirms)
```

### Benefits

1. **Real-Time Validation**
   - See Zeus accuracy as day progresses
   - Know if forecast is on track

2. **Resolution Preview**
   - Know winning bracket before Polymarket resolves
   - Validate trade outcomes immediately

3. **System Confidence**
   - Track Zeus accuracy over time
   - Identify patterns (time of day, weather conditions, etc.)

4. **Data Collection**
   - Build historical accuracy dataset
   - Improve future probability models

### Rate Limiting & Caching

**Strategy:**
```python
# Cache METAR data to avoid excessive API calls
from functools import lru_cache
from datetime import datetime

@lru_cache(maxsize=100)
def get_metar_cached(station: str, hour: int):
    """Cache METAR by station and hour."""
    return metar_service.get_observations(station, hours=1)

# Frontend: Only fetch when needed
// Don't poll every second - METAR updates hourly
refetchInterval: 60000  // 1 minute is sufficient
```

### Station Mapping

**Hermes Stations → METAR Stations:**
```python
# Already in data/registry/stations.csv
STATION_METAR_MAP = {
    "EGLC": "EGLC",  # London City Airport
    "KLGA": "KLGA",  # LaGuardia Airport (NYC)
    "KNYC": "KNYC",  # Central Park (NYC)
    "KLAX": "KLAX",  # LAX Airport
    "KMIA": "KMIA",  # Miami Airport
    "KPHL": "KPHL",  # Philadelphia Airport
    "KAUS": "KAUS",  # Austin Airport
    "KDEN": "KDEN",  # Denver Airport
    "KMDW": "KMDW",  # Chicago Midway
}
```

### Error Handling

```python
# Handle METAR API failures gracefully
try:
    metar_data = metar_service.get_observations(station, date)
except METARAPIError:
    # Fall back to showing only Zeus data
    logger.warning("METAR unavailable, showing Zeus only")
    metar_data = None

# Frontend shows degraded state
{metar_data ? (
  <ActualTempLine data={metar_data} />
) : (
  <InfoBanner>METAR data unavailable - showing Zeus only</InfoBanner>
)}
```

---

### 3. Backtest Configurator

**What Users See:**
```
┌─────────────────────────────────────────────────────────┐
│ 🔬 Backtest Configurator                                │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Date Range:                                             │
│   Start: [Nov 13, 2025]  End: [Nov 15, 2025]           │
│                                                          │
│ Stations: ☑ EGLC  ☑ KLGA  ☐ KAUS  ☐ KDEN              │
│                                                          │
│ Probability Model:                                      │
│   ○ Spread Model  ● Bands Model                        │
│                                                          │
│ Trading Configuration:                                  │
│   Edge Min: [5%]        Kelly Cap: [10%]               │
│   Fee BP: [50]          Slippage BP: [30]              │
│   Per Market Cap: [$500]                               │
│                                                          │
│ Data Source:                                            │
│   ● Dynamic Snapshots (recommended)                     │
│   ○ API Re-fetch (may have hindsight bias)             │
│                                                          │
│ [Run Backtest] [Save Configuration] [Load Config]      │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Data Needed from API:**
- Available date ranges with data
- Available stations
- Configuration presets

**API Endpoints:**
```
POST /api/backtest/run
Body: {
  "start_date": "2025-11-13",
  "end_date": "2025-11-15",
  "stations": ["EGLC", "KLGA"],
  "config": {
    "model_mode": "bands",
    "edge_min": 0.05,
    "kelly_cap": 0.10,
    "fee_bp": 50,
    "slippage_bp": 30,
    "per_market_cap": 500
  },
  "use_snapshots": true
}

Returns: {
  "job_id": "backtest_20251113_143022",
  "status": "running"
}

GET /api/backtest/status/{job_id}
→ {
    "status": "complete",
    "progress": 100,
    "results_url": "/api/backtest/results/backtest_20251113_143022"
  }
```

---

### 4. Configuration Comparison

**What Users See:**
```
┌─────────────────────────────────────────────────────────┐
│ 🏆 Configuration Comparison (Nov 13-15)                 │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Run multiple backtests with different configs:          │
│                                                          │
│ ┌─────┬──────────┬─────────┬──────┬─────────┬─────┐   │
│ │ #   │ Model    │ Edge Min│Kelly │ Trades  │ ROI │   │
│ ├─────┼──────────┼─────────┼──────┼─────────┼─────┤   │
│ │ 1   │ Spread   │  5%     │ 10%  │   45    │12.3%│✅ │
│ │ 2   │ Bands    │  5%     │ 10%  │   38    │15.7%│🏆 │
│ │ 3   │ Spread   │  8%     │ 10%  │   28    │ 9.2%│   │
│ │ 4   │ Spread   │  5%     │ 15%  │   45    │10.8%│   │
│ │ 5   │ Bands    │  8%     │ 15%  │   22    │14.1%│   │
│ └─────┴──────────┴─────────┴──────┴─────────┴─────┘   │
│                                                          │
│ 🏆 Best Configuration: #2 (Bands, 5% edge, 10% Kelly)  │
│    ROI: 15.7%  |  Trades: 38  |  Win Rate: 24%         │
│                                                          │
│ [View Details] [Export Results] [Apply to Live]        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Data Needed from API:**
- Batch backtest execution
- Results comparison
- Configuration management

**API Endpoints:**
```
POST /api/backtest/batch
Body: {
  "date_range": {"start": "2025-11-13", "end": "2025-11-15"},
  "stations": ["EGLC", "KLGA"],
  "configurations": [
    {"model_mode": "spread", "edge_min": 0.05, "kelly_cap": 0.10},
    {"model_mode": "bands", "edge_min": 0.05, "kelly_cap": 0.10},
    ...
  ]
}

Returns: {
  "batch_id": "batch_20251113_143022",
  "total_configs": 5,
  "status": "running"
}

GET /api/backtest/batch/{batch_id}/results
→ {
    "results": [
      {
        "config_id": 1,
        "roi": 0.123,
        "trades": 45,
        "win_rate": 0.24,
        "total_pnl": 1234.50,
        ...
      },
      ...
    ],
    "best_config_id": 2
  }
```

---

## 🔧 Technical Architecture

### Option 1: Minimal (FastAPI Backend + React Frontend)

**Pros**: Simple, fast to build, single codebase  
**Cons**: Less scalable, manual WebSocket handling

```
├── backend/
│   ├── api/
│   │   ├── main.py          # FastAPI app
│   │   ├── routes/
│   │   │   ├── status.py    # System status
│   │   │   ├── trades.py    # Trading data
│   │   │   ├── snapshots.py # Historical data
│   │   │   └── backtest.py  # Backtest execution
│   │   ├── services/
│   │   │   ├── trading_service.py
│   │   │   ├── snapshot_service.py
│   │   │   └── backtest_service.py
│   │   └── models/
│   │       └── schemas.py   # Pydantic models for API
│   └── hermes/              # Existing Hermes code
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── LiveTrading.tsx
│   │   │   ├── HistoricalView.tsx
│   │   │   ├── BacktestConfig.tsx
│   │   │   └── ComparisonView.tsx
│   │   ├── api/
│   │   │   └── client.ts    # API client
│   │   └── App.tsx
│   └── package.json
│
└── docker-compose.yml       # Optional: Containerization
```

---

### Option 2: Full Stack (Next.js + Python Backend)

**Pros**: Better SEO, server-side rendering, TypeScript full-stack  
**Cons**: More complex, two build processes

```
├── apps/
│   ├── web/                 # Next.js frontend
│   │   ├── app/
│   │   │   ├── dashboard/
│   │   │   ├── backtests/
│   │   │   └── api/         # Next.js API routes (proxy)
│   │   └── components/
│   │
│   └── api/                 # Python FastAPI
│       └── (same as Option 1)
│
└── packages/
    └── shared/              # Shared types
```

---

### Recommended: **Option 1** (FastAPI + React)

Simpler, faster to build, perfect for internal tool.

---

## 🛠️ Implementation Phases

### Phase 1: REST API Backend (Week 1)

**Goal**: Expose Hermes data via HTTP endpoints

**Tasks**:
1. Create FastAPI application
2. Implement read-only endpoints:
   - System status
   - Current trades
   - Historical snapshots
3. Add CORS for local development
4. Test with curl/Postman

**Files to Create**:
```python
# backend/api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Hermes Trading API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/status")
def get_status():
    # Check if dynamic mode running
    # Return system health
    ...

@app.get("/api/trades/recent")
def get_recent_trades(limit: int = 50):
    # Read from data/trades/
    # Return recent trades
    ...

@app.get("/api/snapshots/zeus/{station}/{date}")
def get_zeus_snapshots(station: str, date: str):
    # Read from data/snapshots/dynamic/zeus/
    # Return all snapshots for date
    ...
```

**Success Criteria**:
- ✅ API runs on http://localhost:8000
- ✅ Can fetch status via curl
- ✅ Can fetch trades via curl
- ✅ Can fetch snapshots via curl

---

### Phase 2: Basic Frontend (Week 2)

**Goal**: Simple dashboard showing live data

**Tasks**:
1. Setup React app (Vite or Create React App)
2. Create status dashboard
3. Show recent trades
4. Display current edges
5. Basic styling (Tailwind CSS)

**Components**:
```typescript
// frontend/src/components/Dashboard.tsx
export function Dashboard() {
  const { data: status } = useQuery('/api/status');
  const { data: edges } = useQuery('/api/edges/current');
  
  return (
    <div className="dashboard">
      <StatusCard status={status} />
      <EdgesTable edges={edges} />
      <RecentTradesTable />
    </div>
  );
}
```

**Success Criteria**:
- ✅ Dashboard loads and shows data
- ✅ Auto-refreshes every 30 seconds
- ✅ Shows current system status
- ✅ Shows current edges

---

### Phase 3: Historical Visualization (Week 3)

**Goal**: Visualize forecast evolution and past trades

**Tasks**:
1. Add date picker
2. Fetch historical snapshots
3. Chart Zeus forecast evolution
4. Show Polymarket price changes
5. Display trades placed

**Libraries**:
- Chart.js or Recharts for visualizations
- React Query for data fetching
- Date-fns for date handling

**Success Criteria**:
- ✅ Can select any historical date
- ✅ See Zeus forecast evolution chart
- ✅ See market price changes
- ✅ See trades placed with timestamps

---

### Phase 4: Backtest Runner (Week 4)

**Goal**: Run backtests from UI

**Tasks**:
1. Build configuration form
2. Implement backtest API endpoint
3. Show progress (if long-running)
4. Display results with charts
5. Export results to CSV

**Backend**:
```python
# backend/api/routes/backtest.py
from fastapi import BackgroundTasks

@app.post("/api/backtest/run")
def run_backtest(config: BacktestConfig, background_tasks: BackgroundTasks):
    # Validate config
    # Start backtest in background
    job_id = str(uuid.uuid4())
    background_tasks.add_task(execute_backtest, job_id, config)
    
    return {"job_id": job_id, "status": "started"}

@app.get("/api/backtest/results/{job_id}")
def get_backtest_results(job_id: str):
    # Read results from data/runs/backtests/
    # Return formatted results
    ...
```

**Frontend**:
```typescript
// frontend/src/components/BacktestConfig.tsx
export function BacktestConfig() {
  const [config, setConfig] = useState(defaultConfig);
  
  const runBacktest = async () => {
    const { job_id } = await api.post('/api/backtest/run', config);
    pollForResults(job_id);
  };
  
  return (
    <form onSubmit={runBacktest}>
      <DateRangePicker />
      <ModelSelector />
      <TradingParams />
      <button>Run Backtest</button>
    </form>
  );
}
```

**Success Criteria**:
- ✅ Can configure and run backtests from UI
- ✅ See results with charts
- ✅ Download CSV results

---

### Phase 5: Batch Comparison (Week 5)

**Goal**: Run multiple configurations, compare results

**Tasks**:
1. Multi-configuration builder
2. Parallel backtest execution
3. Results comparison table
4. Highlight best configuration
5. Export comparison report

**Backend**:
```python
@app.post("/api/backtest/batch")
def run_batch_backtest(batch: BatchBacktestRequest):
    # Run multiple configurations in parallel
    # Store results
    # Return batch_id
    ...

@app.get("/api/backtest/batch/{batch_id}/results")
def get_batch_results(batch_id: str):
    # Compare results
    # Rank by ROI or other metric
    # Return sorted comparison
    ...
```

**Success Criteria**:
- ✅ Can run 5-10 configurations at once
- ✅ See comparison table
- ✅ Identify best configuration
- ✅ Export comparison report

---

## 🗄️ Data Layer Design

### Option A: File-Based (Simpler)

**Keep current structure**, API reads from files:

```python
# backend/api/services/snapshot_service.py
class SnapshotService:
    def get_zeus_snapshots(self, station: str, date: str):
        base_path = Path(f"data/snapshots/dynamic/zeus/{station}/{date}")
        snapshots = []
        
        for file in sorted(base_path.glob("*.json")):
            with open(file) as f:
                data = json.load(f)
                snapshots.append(data)
        
        return snapshots
```

**Pros**:
- ✅ No migration needed
- ✅ Simple to implement
- ✅ Files already exist

**Cons**:
- ⚠️ Slower queries (file I/O)
- ⚠️ No indexing
- ⚠️ Limited aggregation

---

### Option B: Hybrid (File + Database)

**Keep files for raw data**, add database for queryable data:

```python
# Database schema
CREATE TABLE snapshots (
    id SERIAL PRIMARY KEY,
    fetch_time TIMESTAMP NOT NULL,
    station_code VARCHAR(10) NOT NULL,
    event_day DATE NOT NULL,
    snapshot_type VARCHAR(20) NOT NULL,  -- 'zeus', 'polymarket', 'decision'
    file_path VARCHAR(500) NOT NULL,
    metadata JSONB,  -- Summary data for fast queries
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_snapshots_station_date ON snapshots(station_code, event_day);
CREATE INDEX idx_snapshots_fetch_time ON snapshots(fetch_time);

CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    trade_time TIMESTAMP NOT NULL,
    station_code VARCHAR(10) NOT NULL,
    event_day DATE NOT NULL,
    bracket VARCHAR(20) NOT NULL,
    p_zeus DECIMAL(10, 6),
    p_market DECIMAL(10, 6),
    edge DECIMAL(10, 6),
    size_usd DECIMAL(10, 2),
    model_mode VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Import Process**:
```python
# Run after each cycle or periodically
def import_snapshots_to_db():
    for snapshot_file in new_snapshots:
        data = load_snapshot(snapshot_file)
        
        db.execute(
            "INSERT INTO snapshots (fetch_time, station_code, event_day, ...)",
            values=(data['fetch_time'], ...)
        )
```

**Pros**:
- ✅ Fast queries
- ✅ Aggregations (AVG, SUM, GROUP BY)
- ✅ Complex filters
- ✅ Still have raw files

**Cons**:
- ⚠️ More complex
- ⚠️ Import process needed
- ⚠️ Data duplication

**Recommended**: Start with **Option A** (file-based), migrate to **Option B** if needed

---

## 📡 API Specification

### Complete API Design:

```yaml
# System Status
GET /api/status
  Returns: System health, running status, current cycle

GET /api/health
  Returns: API health check

# Live Trading
GET /api/trading/status
  Returns: Dynamic mode status, next cycle time

GET /api/trading/edges/current
  Returns: Current edges for all stations/events

GET /api/trading/trades/today
  Returns: All trades placed today

WebSocket /ws/trading
  Streams: Real-time trade updates

# Historical Data
GET /api/snapshots/dates
  Returns: List of dates with data

GET /api/snapshots/zeus?station=EGLC&date=2025-11-13
  Returns: All Zeus snapshots for station/date

GET /api/snapshots/polymarket?city=London&date=2025-11-13
  Returns: All Polymarket snapshots for city/date

GET /api/snapshots/decisions?station=EGLC&date=2025-11-13
  Returns: All decision snapshots for station/date

GET /api/trades?start_date=2025-11-13&end_date=2025-11-15
  Returns: All trades in date range

# Backtesting
POST /api/backtest/run
  Body: Configuration
  Returns: Job ID

GET /api/backtest/status/{job_id}
  Returns: Progress and status

GET /api/backtest/results/{job_id}
  Returns: Complete backtest results

DELETE /api/backtest/cancel/{job_id}
  Cancels running backtest

# Batch Backtesting
POST /api/backtest/batch
  Body: Multiple configurations
  Returns: Batch ID

GET /api/backtest/batch/{batch_id}/status
  Returns: Overall progress

GET /api/backtest/batch/{batch_id}/results
  Returns: Comparison results

# Configuration
GET /api/config/presets
  Returns: Saved configuration presets

POST /api/config/presets
  Body: New preset
  Returns: Preset ID

GET /api/config/current
  Returns: Current live trading config

POST /api/config/update
  Body: New configuration
  Returns: Success (applies to next cycle)
```

---

## 🎨 Frontend Tech Stack

### Recommended Stack:

**Framework**: React (with Vite)
- Fast dev server
- Modern tooling
- Great ecosystem

**UI Library**: shadcn/ui or Chakra UI
- Pre-built components
- Good accessibility
- Easy customization

**Charts**: Recharts
- React-native
- Good for time series
- Easy to use

**State Management**: TanStack Query (React Query)
- API data caching
- Auto-refetching
- Loading/error states

**Styling**: Tailwind CSS
- Utility-first
- Fast development
- Good defaults

**Type Safety**: TypeScript
- Catch errors early
- Better DX
- API contract enforcement

### Alternative (Simpler): Streamlit

**If you want to build faster** with Python:

```python
# app.py
import streamlit as st
import pandas as pd
from hermes.api import get_status, get_trades, run_backtest

st.title("🚀 Hermes Trading Dashboard")

# Status
status = get_status()
st.metric("Status", "Running" if status['running'] else "Stopped")

# Recent trades
trades = get_trades(limit=50)
st.dataframe(trades)

# Backtest
with st.form("backtest"):
    start_date = st.date_input("Start")
    end_date = st.date_input("End")
    model = st.selectbox("Model", ["spread", "bands"])
    
    if st.form_submit_button("Run"):
        results = run_backtest(start_date, end_date, model)
        st.write(results)
```

**Pros**:
- ✅ All Python (no JavaScript)
- ✅ Very fast to build
- ✅ Good for internal tools

**Cons**:
- ⚠️ Less customizable
- ⚠️ Limited real-time updates
- ⚠️ Python-only stack

---

## 📝 Step-by-Step Implementation

### Week 1: API Foundation

**Day 1-2: Setup**
```bash
# Create API structure
mkdir -p backend/api/{routes,services,models}
cd backend

# Install dependencies
pip install fastapi uvicorn sqlalchemy psycopg2-binary

# Create main.py
```

**Day 3-4: Core Endpoints**
- Implement status endpoint
- Implement trades endpoint
- Implement snapshots endpoint
- Test with curl

**Day 5: WebSocket**
- Add WebSocket for real-time updates
- Test with WebSocket client

---

### Week 2: Frontend Foundation

**Day 1: Setup**
```bash
# Create React app
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install @tanstack/react-query recharts tailwindcss
```

**Day 2-3: Components**
- Create Dashboard layout
- Add StatusCard component
- Add EdgesTable component
- Add RecentTrades component

**Day 4-5: Integration**
- Connect to API
- Add auto-refresh
- Handle loading/error states

---

### Week 3: Historical View

**Day 1-2: Data Browser**
- Date picker
- Station selector
- Fetch historical snapshots

**Day 3-4: Visualization**
- Zeus forecast evolution chart
- Polymarket price chart
- Trade markers on timeline

**Day 5: Polish**
- Tooltips
- Export buttons
- Responsive design

---

### Week 4: Backtest Runner

**Day 1-2: Configuration Form**
- Build config form
- Validation
- Preset management

**Day 3-4: Execution & Results**
- Submit backtest
- Poll for results
- Display with charts

**Day 5: Export**
- CSV export
- PDF report
- Share results

---

### Week 5: Batch Comparison

**Day 1-2: Batch Builder**
- Multi-config builder
- Grid/matrix view
- Parameter ranges

**Day 3-4: Comparison View**
- Results table
- Sorting/filtering
- Best config highlighting

**Day 5: Analysis Tools**
- Charts comparing configs
- Statistical tests
- Recommendation engine

---

## 🔌 WebSocket Design (Real-Time Updates)

### Why WebSocket?

For live trading dashboard, you want **real-time updates** without polling.

**Without WebSocket** (Polling):
```typescript
// Poll every 5 seconds
setInterval(() => {
  fetchCurrentEdges();
}, 5000);
```
**Problem**: Delayed updates, unnecessary API calls

**With WebSocket**:
```typescript
// Subscribe once
const ws = new WebSocket('ws://localhost:8000/ws/trading');
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  updateDashboard(update);
};
```
**Benefit**: Instant updates, efficient

### Implementation:

**Backend**:
```python
# backend/api/websocket.py
from fastapi import WebSocket

active_connections = []

@app.websocket("/ws/trading")
async def trading_websocket(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Send updates when available
            await websocket.receive_text()  # Keep alive
    except:
        active_connections.remove(websocket)

# When dynamic engine places trade:
async def broadcast_trade(trade_data):
    for connection in active_connections:
        await connection.send_json({
            "type": "trade",
            "data": trade_data
        })
```

**Frontend**:
```typescript
// frontend/src/hooks/useWebSocket.ts
export function useTradingWebSocket() {
  const [data, setData] = useState(null);
  
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/trading');
    
    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);
      setData(update);
    };
    
    return () => ws.close();
  }, []);
  
  return data;
}
```

---

## 🎨 UI/UX Design Examples

### Dashboard Layout:

```
┌─────────────────────────────────────────────────────────────────┐
│ 🚀 Hermes Trading System                    [Settings] [Logout] │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐   │
│ │● RUNNING   │ │ Cycle: 45  │ │Trades: 23  │ │ ROI: 12.3% │   │
│ │Next: 2:34  │ │15min ago   │ │Today       │ │ Today      │   │
│ └────────────┘ └────────────┘ └────────────┘ └────────────┘   │
│                                                                  │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ 📊 Current Edges (London, Nov 13)           [Refresh]   │   │
│ │                                                           │   │
│ │ Bracket  │ Zeus   │ Market │ Edge    │ Size    │ Status │   │
│ │─────────┼────────┼────────┼─────────┼─────────┼────────│   │
│ │ 58-59°F │ 28.3%  │  0.05% │ +26.25% │ $300.00 │ ✅ TRADE│   │
│ │ 60-61°F │ 33.5%  │  6.95% │ +25.75% │ $300.00 │ ✅ TRADE│   │
│ │ 62-63°F │ 22.1%  │ 85.00% │ -63.70% │    -    │ ❌ SKIP │   │
│ └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ 📈 Zeus Forecast Evolution (Last 6 Hours)      [Expand] │   │
│ │                                                           │   │
│ │   58°F ●─●─●─●─●─●                                      │   │
│ │        09  11  13  15  17  19                           │   │
│ │                                                           │   │
│ └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ 💰 Recent Trades                            [View All]  │   │
│ │                                                           │   │
│ │ Time     │ Station│ Bracket │ Edge   │ Size    │ Status │   │
│ │─────────┼────────┼─────────┼────────┼─────────┼────────│   │
│ │ 14:21:10│ EGLC   │ 58-59°F │ 26.16% │ $300.00 │ 📝 Paper│   │
│ │ 14:21:10│ EGLC   │ 60-61°F │ 32.66% │ $300.00 │ 📝 Paper│   │
│ │ 14:04:22│ EGLC   │ 58-59°F │ 25.23% │ $300.00 │ 📝 Paper│   │
│ └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘

Sidebar:
[📊 Dashboard]  ← Current page
[📈 Historical]
[🔬 Backtests]
[⚙️  Settings]
```

---

## 🚀 Quick Start Path (Minimal Viable Frontend)

### If You Want Something Working FAST (1 Week):

**Use Streamlit** (Python-based UI):

```python
# frontend/dashboard.py
import streamlit as st
import pandas as pd
import json
from pathlib import Path

st.set_page_config(page_title="Hermes Trading", layout="wide")

st.title("🚀 Hermes Dynamic Trading Dashboard")

# Check if dynamic mode running
import subprocess
try:
    result = subprocess.run(
        ["pgrep", "-f", "dynamic-paper"],
        capture_output=True,
        text=True
    )
    running = bool(result.stdout.strip())
except:
    running = False

col1, col2, col3 = st.columns(3)
col1.metric("Status", "● RUNNING" if running else "○ STOPPED")

# Recent trades
trades_file = Path("data/trades/2025-11-13/paper_trades.csv")
if trades_file.exists():
    trades = pd.read_csv(trades_file)
    col2.metric("Trades Today", len(trades))
    col3.metric("Total Size", f"${trades['size_usd'].sum():,.0f}")
    
    st.subheader("Recent Trades")
    st.dataframe(trades.tail(20))

# Snapshots
st.subheader("Snapshots Collected")
zeus_snapshots = list(Path("data/snapshots/dynamic/zeus").rglob("*.json"))
st.metric("Zeus Snapshots", len(zeus_snapshots))

# Latest snapshot
if zeus_snapshots:
    latest = max(zeus_snapshots, key=lambda p: p.stat().st_mtime)
    with open(latest) as f:
        data = json.load(f)
    
    st.subheader("Latest Zeus Forecast")
    st.json(data)
```

**Run**:
```bash
pip install streamlit
streamlit run frontend/dashboard.py
```

**Opens**: http://localhost:8501 - instant dashboard!

**Effort**: 1-2 days for basic dashboard

---

## 🏆 Recommended Approach

### Phase A: Streamlit MVP (Week 1)

Build quick Streamlit dashboard:
- View system status
- See recent trades
- Browse snapshots
- Run backtests

**Effort**: 3-5 days  
**Benefit**: Something usable immediately

---

### Phase B: FastAPI (Week 2-3)

Build proper REST API:
- Expose all Hermes data
- Add WebSocket for real-time
- Proper error handling
- API documentation (OpenAPI)

**Effort**: 1-2 weeks  
**Benefit**: Solid foundation for any frontend

---

### Phase C: React Dashboard (Week 4-6)

Build professional frontend:
- Modern UI
- Real-time updates
- Advanced visualizations
- Backtest configurator

**Effort**: 3-4 weeks  
**Benefit**: Production-ready interface

---

## 📦 Technology Decisions

### Backend API:

**Option 1: FastAPI** (Recommended)
- Modern Python web framework
- Auto-generated docs (Swagger)
- Type hints with Pydantic
- WebSocket support
- Async support

**Option 2: Flask**
- Simpler, more traditional
- Good for simple APIs
- Less built-in features

**Recommendation**: **FastAPI** - Better for modern apps

---

### Frontend:

**Option 1: React + Vite** (Recommended for production)
- Modern, fast
- Great ecosystem
- Flexible

**Option 2: Streamlit** (Recommended for MVP)
- All Python
- Very fast to build
- Good enough for internal tools

**Option 3: Next.js**
- Full-stack framework
- Server-side rendering
- More complex

**Recommendation**: 
- **Streamlit** for MVP (this week)
- **React** for production (later)

---

### Database:

**Option 1: None (File-based)** - Start here
- Use existing file structure
- Simple, no migration

**Option 2: SQLite**
- Lightweight
- No server needed
- Good for small-medium data

**Option 3: PostgreSQL**
- Production-grade
- Advanced features
- Good for scaling

**Recommendation**: Start without DB, add SQLite if queries slow

---

## 🔄 Data Flow Examples

### Example 1: View Current Edges

```
User clicks "Dashboard"
  ↓
Frontend: GET /api/edges/current
  ↓
API: Read latest decision snapshots
  ↓
API: Return formatted edge data
  ↓
Frontend: Display in table
  ↓
User sees current edges with live updates
```

### Example 2: Run Backtest

```
User fills backtest form:
  - Date: Nov 13-15
  - Model: Bands
  - Edge min: 5%
  ↓
Frontend: POST /api/backtest/run {...config}
  ↓
API: Validate config
  ↓
API: Start background task
  ↓
API: Return job_id
  ↓
Frontend: Poll GET /api/backtest/status/{job_id}
  ↓
API: Run Hermes backtester with config
  ↓
API: Save results
  ↓
Frontend: Fetch GET /api/backtest/results/{job_id}
  ↓
Frontend: Display charts and tables
  ↓
User sees backtest results
```

### Example 3: Compare Configurations

```
User creates batch:
  - 5 different configurations
  - Same date range (Nov 13-15)
  ↓
Frontend: POST /api/backtest/batch {...configs}
  ↓
API: Queue 5 backtests
  ↓
API: Run in parallel
  ↓
API: Aggregate results
  ↓
API: Rank by ROI
  ↓
Frontend: Display comparison table
  ↓
User sees best configuration highlighted
```

---

## 📊 Key Features Priority

### Must Have (MVP):

1. ✅ View system status (running/stopped)
2. ✅ See recent trades
3. ✅ Basic backtest runner
4. ✅ View backtest results

### Should Have (V1):

5. ✅ Real-time trade updates (WebSocket)
6. ✅ Historical data browser
7. ✅ Zeus forecast charts
8. ✅ Configuration presets

### Nice to Have (V2):

9. ✅ Batch configuration comparison
10. ✅ Advanced charts (candlesticks, heatmaps)
11. ✅ Alert notifications
12. ✅ Export to PDF/Excel

---

## 🛠️ Minimal API Example

### Complete Working Example (FastAPI):

```python
# backend/api/main.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from datetime import date
import json
import pandas as pd
from typing import List, Optional

app = FastAPI(title="Hermes Trading API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECT_ROOT = Path(__file__).parent.parent.parent

# --- System Status ---

@app.get("/api/status")
def get_status():
    """Get system status."""
    import subprocess
    
    try:
        result = subprocess.run(
            ["pgrep", "-f", "dynamic-paper"],
            capture_output=True,
            text=True
        )
        running = bool(result.stdout.strip())
    except:
        running = False
    
    # Count snapshots
    zeus_count = len(list((PROJECT_ROOT / "data/snapshots/dynamic/zeus").rglob("*.json")))
    
    return {
        "running": running,
        "mode": "dynamic-paper" if running else "stopped",
        "snapshots_collected": zeus_count,
    }

# --- Trades ---

@app.get("/api/trades/today")
def get_todays_trades():
    """Get today's paper trades."""
    today = date.today()
    trades_file = PROJECT_ROOT / "data" / "trades" / str(today) / "paper_trades.csv"
    
    if not trades_file.exists():
        return {"trades": [], "total": 0}
    
    df = pd.read_csv(trades_file)
    trades = df.to_dict('records')
    
    return {
        "trades": trades,
        "total": len(trades),
        "total_size": df['size_usd'].sum()
    }

# --- Snapshots ---

@app.get("/api/snapshots/zeus/{station}/{event_date}")
def get_zeus_snapshots(station: str, event_date: str):
    """Get Zeus snapshots for a station/date."""
    snapshot_dir = PROJECT_ROOT / "data/snapshots/dynamic/zeus" / station / event_date
    
    if not snapshot_dir.exists():
        raise HTTPException(404, "No snapshots found")
    
    snapshots = []
    for file in sorted(snapshot_dir.glob("*.json")):
        with open(file) as f:
            data = json.load(f)
            # Extract summary
            snapshots.append({
                "fetch_time": data['fetch_time_utc'],
                "predicted_high": max(
                    (p['temp_K'] - 273.15) * 9/5 + 32 
                    for p in data['timeseries']
                ),
                "timeseries_count": data['timeseries_count'],
            })
    
    return {"snapshots": snapshots, "total": len(snapshots)}

# --- Backtesting ---

@app.post("/api/backtest/run")
def run_backtest(
    start_date: str,
    end_date: str,
    stations: List[str],
    model_mode: str = "spread",
    edge_min: float = 0.05,
):
    """Run backtest with configuration."""
    # Import Hermes backtester
    from agents.backtester import Backtester
    from datetime import date
    
    # Parse dates
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    
    # Create backtester with config
    backtester = Backtester(
        bankroll_usd=3000,
        edge_min=edge_min,
        fee_bp=50,
        slippage_bp=30,
    )
    
    # Run backtest
    output_path = backtester.run(start, end, stations)
    
    # Read results
    import pandas as pd
    df = pd.read_csv(output_path)
    
    return {
        "status": "complete",
        "results": df.to_dict('records'),
        "summary": {
            "total_trades": len(df),
            "wins": len(df[df['outcome'] == 'win']),
            "losses": len(df[df['outcome'] == 'loss']),
            "total_pnl": df['realized_pnl'].sum(),
        }
    }

# Run with: uvicorn main:app --reload
```

**Start**:
```bash
cd backend/api
uvicorn main:app --reload --port 8000
```

**Test**:
```bash
curl http://localhost:8000/api/status
curl http://localhost:8000/api/trades/today
```

---

## 🎯 Quick Win: Streamlit Dashboard (This Week!)

### Create a simple dashboard in 1 day:

```python
# frontend/dashboard.py
import streamlit as st
import pandas as pd
import json
from pathlib import Path
from datetime import date

st.set_page_config(page_title="Hermes Trading", layout="wide", page_icon="🚀")

# --- Header ---
st.title("🚀 Hermes Dynamic Trading Dashboard")

# --- Status ---
st.header("System Status")
col1, col2, col3, col4 = st.columns(4)

# Check if running
import subprocess
try:
    result = subprocess.run(["pgrep", "-f", "dynamic-paper"], capture_output=True, text=True)
    running = bool(result.stdout.strip())
except:
    running = False

col1.metric("Status", "● RUNNING" if running else "○ STOPPED")

# Count snapshots
PROJECT_ROOT = Path(".")
zeus_snapshots = list((PROJECT_ROOT / "data/snapshots/dynamic/zeus").rglob("*.json"))
col2.metric("Snapshots", len(zeus_snapshots))

# Today's trades
today_str = str(date.today())
trades_file = PROJECT_ROOT / "data/trades" / today_str / "paper_trades.csv"
if trades_file.exists():
    trades_df = pd.read_csv(trades_file)
    col3.metric("Trades Today", len(trades_df))
    col4.metric("Total Size", f"${trades_df['size_usd'].sum():,.0f}")
else:
    col3.metric("Trades Today", 0)
    col4.metric("Total Size", "$0")

# --- Recent Trades ---
st.header("📝 Recent Trades")
if trades_file.exists():
    st.dataframe(trades_df, use_container_width=True)
else:
    st.info("No trades today yet")

# --- Historical Data ---
st.header("📊 Historical Snapshots")

# Date selector
available_dates = sorted(set(
    p.parent.name 
    for p in (PROJECT_ROOT / "data/snapshots/dynamic/zeus").rglob("*.json")
))

if available_dates:
    selected_date = st.selectbox("Select Date", available_dates, index=len(available_dates)-1)
    selected_station = st.selectbox("Select Station", ["EGLC", "KLGA"])
    
    # Load snapshots
    snapshot_dir = PROJECT_ROOT / "data/snapshots/dynamic/zeus" / selected_station / selected_date
    
    if snapshot_dir.exists():
        snapshots = []
        for file in sorted(snapshot_dir.glob("*.json")):
            with open(file) as f:
                data = json.load(f)
                # Get predicted high
                temps = [(p['temp_K'] - 273.15) * 9/5 + 32 for p in data['timeseries']]
                snapshots.append({
                    "Time": data['fetch_time_utc'][:19],
                    "Predicted High": f"{max(temps):.1f}°F",
                    "Timeseries Count": len(data['timeseries'])
                })
        
        df = pd.DataFrame(snapshots)
        st.dataframe(df, use_container_width=True)
        
        # Chart
        st.line_chart(df.set_index("Time")["Predicted High"])
else:
    st.info("No historical data yet")

# --- Backtest Runner ---
st.header("🔬 Run Backtest")

with st.form("backtest_form"):
    col1, col2 = st.columns(2)
    
    start_date = col1.date_input("Start Date")
    end_date = col2.date_input("End Date")
    
    model = st.selectbox("Model", ["spread", "bands"])
    edge_min = st.slider("Minimum Edge", 0.0, 0.20, 0.05, 0.01)
    
    if st.form_submit_button("Run Backtest"):
        with st.spinner("Running backtest..."):
            # Import and run
            from agents.backtester import Backtester
            
            backtester = Backtester(
                bankroll_usd=3000,
                edge_min=edge_min,
                fee_bp=50,
                slippage_bp=30,
            )
            
            # Run
            output_path = backtester.run(start_date, end_date, [selected_station])
            
            # Show results
            results = pd.read_csv(output_path)
            st.success(f"Backtest complete! {len(results)} trades")
            st.dataframe(results)
            
            # Summary
            wins = len(results[results['outcome'] == 'win'])
            losses = len(results[results['outcome'] == 'loss'])
            st.metric("Win Rate", f"{wins/(wins+losses)*100:.1f}%")
```

**Run**:
```bash
streamlit run frontend/dashboard.py
```

**Result**: Full dashboard in browser at http://localhost:8501

**Effort**: 1 day!

---

## 🎨 Full React Example (For Later)

### When you want production-quality frontend:

```typescript
// frontend/src/App.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Dashboard } from './components/Dashboard';
import { HistoricalView } from './components/HistoricalView';
import { BacktestRunner } from './components/BacktestRunner';

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="app">
        <Sidebar />
        <Main>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/historical" element={<HistoricalView />} />
            <Route path="/backtest" element={<BacktestRunner />} />
            <Route path="/compare" element={<ConfigComparison />} />
          </Routes>
        </Main>
      </div>
    </QueryClientProvider>
  );
}

// frontend/src/components/Dashboard.tsx
export function Dashboard() {
  const { data: status } = useQuery({
    queryKey: ['status'],
    queryFn: () => fetch('/api/status').then(r => r.json()),
    refetchInterval: 5000, // Poll every 5s
  });
  
  const { data: edges } = useQuery({
    queryKey: ['edges'],
    queryFn: () => fetch('/api/edges/current').then(r => r.json()),
    refetchInterval: 10000,
  });
  
  // WebSocket for real-time trades
  const trades = useWebSocket('/ws/trading');
  
  return (
    <div className="dashboard">
      <StatusHeader status={status} />
      <EdgesTable edges={edges} />
      <TradesTable trades={trades} />
      <ForecastChart />
    </div>
  );
}
```

---

## 🔐 Security Considerations

### Authentication (For Production):

```python
# backend/api/auth.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

def verify_token(credentials = Depends(security)):
    if credentials.credentials != API_KEY:
        raise HTTPException(401, "Invalid token")
    return credentials

# Use on routes:
@app.get("/api/trades/today", dependencies=[Depends(verify_token)])
def get_todays_trades():
    ...
```

### HTTPS (For Production):

```bash
# Use Nginx reverse proxy with SSL
nginx → (HTTPS) → FastAPI (HTTP localhost:8000)
```

---

## 📈 Scaling Considerations

### If Data Grows Large:

**Problem**: 1000s of snapshots, slow file reads

**Solution 1**: Add database indexes
```sql
CREATE INDEX idx_snapshots_time ON snapshots(fetch_time);
SELECT * FROM snapshots WHERE fetch_time > '2025-11-13' ORDER BY fetch_time;
```

**Solution 2**: Add caching
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_snapshot(file_path):
    with open(file_path) as f:
        return json.load(f)
```

**Solution 3**: Lazy loading
```typescript
// Only load visible data
<VirtualizedList
  items={allSnapshots}
  renderItem={(snapshot) => <SnapshotCard />}
/>
```

---

## 🚀 Getting Started (Recommended Path)

### This Week: Streamlit MVP

**Day 1**: Setup Streamlit
```bash
pip install streamlit pandas plotly
```

**Day 2-3**: Build dashboard
- System status
- Recent trades
- Snapshot browser

**Day 4**: Add backtest runner
- Simple form
- Run backtest
- Display results

**Day 5**: Polish
- Charts
- Filters
- Export buttons

**Result**: Working dashboard in 5 days

---

### Next Month: FastAPI + React

**Week 1**: Build FastAPI
- All endpoints
- WebSocket
- Testing

**Week 2**: React setup
- Project structure
- Routing
- API client

**Week 3**: Core components
- Dashboard
- Historical view
- Backtest runner

**Week 4**: Advanced features
- Comparison tool
- Charts
- Export

**Result**: Production-ready frontend in 4 weeks

---

## 📦 Deliverables Checklist

### API Backend:

- [ ] FastAPI application setup
- [ ] Status endpoint
- [ ] Trades endpoints
- [ ] Snapshots endpoints
- [ ] Backtest execution endpoint
- [ ] Batch backtest endpoint
- [ ] WebSocket for real-time updates
- [ ] API documentation (Swagger)
- [ ] Error handling
- [ ] Tests

### Frontend:

- [ ] Dashboard view
- [ ] Live trading monitor
- [ ] Historical data browser
- [ ] Backtest configurator
- [ ] Results visualization
- [ ] Configuration comparison
- [ ] Real-time updates
- [ ] Responsive design
- [ ] Export functionality
- [ ] Tests

### Integration:

- [ ] API <> Frontend integration
- [ ] WebSocket connection
- [ ] Error handling
- [ ] Loading states
- [ ] Deployment setup

---

## 💡 Quick Decision Matrix

### Choose Your Path:

| Goal | Timeline | Recommendation | Effort |
|------|----------|---------------|--------|
| **MVP this week** | 5 days | Streamlit | Low |
| **Internal tool** | 2-3 weeks | Streamlit + FastAPI | Medium |
| **Production app** | 1-2 months | FastAPI + React | High |
| **Quick prototype** | 1 day | Streamlit basic | Very Low |

---

## 🎯 My Recommendation

### For You Right Now:

**Start with Streamlit** (this week):
1. Build basic dashboard (1-2 days)
2. Add historical viewer (1 day)
3. Add backtest runner (1 day)
4. Add comparison tool (1 day)

**Total**: 4-5 days, fully functional internal tool

**Then evaluate**:
- Is Streamlit good enough? (Yes → keep it)
- Need more polish? (Yes → build FastAPI + React)
- Need mobile? (Yes → build React Native)

---

## 🔄 Migration Path (Streamlit → React)

### If you start with Streamlit, can migrate later:

**Phase 1**: Streamlit dashboard (now)  
**Phase 2**: Extract logic to API (keep Streamlit frontend)  
**Phase 3**: Build React frontend (parallel to Streamlit)  
**Phase 4**: Deprecate Streamlit, use React

**Benefit**: Get something working NOW, improve later

---

## 📊 Expected Timeline

### Streamlit MVP:

**Week 1**: 
- Setup: 0.5 days
- Dashboard: 1.5 days
- Historical: 1 day
- Backtest: 1 day
- Polish: 1 day

**Total**: 5 days → Working dashboard

---

### FastAPI + React:

**Week 1**: FastAPI backend (5 days)  
**Week 2**: React setup + Dashboard (5 days)  
**Week 3**: Historical + Backtest (5 days)  
**Week 4**: Comparison + Polish (5 days)

**Total**: 4 weeks → Production dashboard

---

## 🎉 Summary

### To Build Frontend for Hermes:

**Path A: Quick (Streamlit)**
- 1 week
- All Python
- Good for internal use
- Start immediately

**Path B: Production (FastAPI + React)**
- 1 month
- Modern stack
- Professional UI
- Better long-term

**Path C: Hybrid**
- Week 1: Streamlit MVP
- Week 2-4: Build FastAPI
- Week 5-8: Build React
- Migrate when ready

---

### What You Need to Build:

1. **API Layer** - Expose Hermes data via HTTP
2. **Frontend** - Web interface for users
3. **Real-time** - WebSocket for live updates
4. **Database** - Optional, for faster queries

### Recommended Start:

**This week**: Build Streamlit dashboard  
**Next month**: Evaluate if you need React  
**Decision point**: Is Streamlit good enough?

---

**Ready to start when you are! I can help build either the Streamlit MVP or the FastAPI + React version.** 🚀

---

**Author**: Hermes Development Team  
**Date**: November 13, 2025  
**Status**: Design Complete, Ready to Implement

