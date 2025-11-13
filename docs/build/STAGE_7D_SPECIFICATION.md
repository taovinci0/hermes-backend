# Stage 7D — Backend API for Frontend Dashboard

**Date**: November 13, 2025  
**Status**: Specification  
**Dependencies**: Stages 1-7C (Complete)

---

## 🎯 Objective

Build a **REST API + WebSocket backend** to power the Hermes frontend dashboard designed in `FRONTEND.md`. Enable real-time monitoring, historical analysis, and backtest execution via clean HTTP endpoints.

---

## 📋 Overview

### What We're Building:

A **FastAPI-based REST API** that:
- Serves real-time trading data (edges, trades, cycles)
- Provides filtered activity logs (by station/day)
- Exposes historical snapshots (Zeus/Polymarket/Decisions)
- Runs backtests on demand
- Streams real-time updates via WebSocket
- Integrates with METAR API for actual temperatures

### Why FastAPI:

✅ Modern Python web framework  
✅ Automatic OpenAPI/Swagger docs  
✅ Type safety with Pydantic  
✅ WebSocket support built-in  
✅ Async support for performance  
✅ Easy to integrate with existing Hermes code

---

## 🗄️ Database: Do We Need One?

### Short Answer: **Not Required for MVP, Helpful for Production**

### Current State (File-Based):
```
data/
├── snapshots/
│   └── dynamic/
│       ├── zeus/{station}/{date}/{timestamp}.json
│       ├── polymarket/{city}/{date}/{timestamp}.json
│       └── decisions/{station}/{date}/{timestamp}.json
├── trades/
│   └── {date}/paper_trades.csv
└── runs/
    └── backtests/{run_id}/results.csv
```

**Pros:**
- ✅ Already working
- ✅ Human-readable (can inspect files)
- ✅ Simple to implement
- ✅ No migration needed
- ✅ Good for MVP

**Cons:**
- ⚠️ Slower queries (file I/O)
- ⚠️ No indexing
- ⚠️ Complex filters require scanning all files
- ⚠️ Limited aggregations

---

### Phase 1: File-Based API (MVP) ✅ **Start Here**

**What works without database:**
- ✅ Serve current cycle status
- ✅ Read latest snapshots
- ✅ Stream recent trades (read CSV)
- ✅ Filter logs (scan files by path)
- ✅ Fetch METAR data (external API)
- ✅ Run backtests (uses existing code)

**Implementation time:** 1-2 weeks

---

### Phase 2: Database-Enhanced (Production) 🔄 **Optional Later**

**What database adds:**
- ⚡ Fast filtered queries (WHERE clauses)
- 📊 Aggregations (SUM, AVG, GROUP BY)
- 🔍 Full-text search in logs
- 📈 Better performance at scale
- 💾 Structured historical data

**When to add:**
- After MVP proves valuable
- When queries become slow (>1s)
- When you have >30 days of data
- When you want advanced analytics

**Database options:**
1. **SQLite** (simplest)
   - Single file database
   - No server needed
   - Good for <100GB data
   - Easy migration from files

2. **PostgreSQL** (production)
   - Full-featured RDBMS
   - Better for large datasets
   - Advanced indexing
   - Better for multiple clients

**Recommendation**: **Start file-based (Phase 1), add SQLite later if needed (Phase 2)**

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React/Streamlit)               │
│  • Live dashboard                                           │
│  • Historical view                                          │
│  • Backtest runner                                          │
└─────────────────────────────────────────────────────────────┘
                           │
                    HTTP + WebSocket
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (NEW)                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Routes (API Endpoints)                              │   │
│  │  • /api/status                                      │   │
│  │  • /api/edges/current                               │   │
│  │  • /api/trades/recent                               │   │
│  │  • /api/snapshots/*                                 │   │
│  │  • /api/logs/activity                               │   │
│  │  • /api/metar/*                                     │   │
│  │  • /api/backtest/run                                │   │
│  │  • /ws/trading (WebSocket)                          │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Services (Business Logic)                           │   │
│  │  • StatusService                                    │   │
│  │  • SnapshotService                                  │   │
│  │  • LogService                                       │   │
│  │  • METARService                                     │   │
│  │  • BacktestService                                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Data Access Layer                                   │   │
│  │  • File readers (JSON, CSV)                         │   │
│  │  • Path utilities                                   │   │
│  │  • Data parsers                                     │   │
│  │  • [Optional] Database queries (Phase 2)           │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              Existing Hermes Backend                        │
│  • Dynamic trading engine                                   │
│  • Backtester                                               │
│  • Zeus/Polymarket agents                                   │
│  • Probability models                                       │
└─────────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    File System                              │
│  • data/snapshots/                                          │
│  • data/trades/                                             │
│  • data/runs/                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
hermes-v1.0.0/
├── backend/                          # NEW - API backend
│   ├── api/
│   │   ├── main.py                   # FastAPI app entry point
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── status.py             # System status endpoints
│   │   │   ├── edges.py              # Current edges endpoints
│   │   │   ├── trades.py             # Trade history endpoints
│   │   │   ├── snapshots.py          # Snapshot data endpoints
│   │   │   ├── logs.py               # Activity log endpoints
│   │   │   ├── metar.py              # METAR data endpoints
│   │   │   ├── backtest.py           # Backtest execution endpoints
│   │   │   └── websocket.py          # WebSocket handlers
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── status_service.py     # System status logic
│   │   │   ├── snapshot_service.py   # Snapshot reading/parsing
│   │   │   ├── log_service.py        # Activity log filtering
│   │   │   ├── metar_service.py      # METAR API integration
│   │   │   └── backtest_service.py   # Backtest orchestration
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── schemas.py            # Pydantic models for API
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── file_utils.py         # File reading utilities
│   │       └── path_utils.py         # Path construction
│   └── requirements.txt              # FastAPI dependencies
│
├── core/                             # Existing Hermes core
├── agents/                           # Existing trading agents
├── venues/                           # Existing market integrations
└── data/                             # Existing data storage
```

---

## 🔌 API Endpoints

### 1. System Status

**Get system status**
```
GET /api/status
```

**Response:**
```json
{
  "running": true,
  "mode": "dynamic-paper",
  "current_cycle": 45,
  "next_cycle_in_seconds": 154,
  "stations": ["EGLC", "KLGA"],
  "interval_seconds": 900,
  "uptime_seconds": 32400
}
```

**Implementation:**
- Check if dynamic mode process is running (PID file)
- Read latest cycle number from logs
- Calculate time to next cycle

---

### 2. Current Edges

**Get current edges for all stations/event days**
```
GET /api/edges/current?station={station}&date={date}
```

**Query params:**
- `station` (optional): Filter by station (e.g., "EGLC")
- `date` (optional): Filter by event day (e.g., "2025-11-13")

**Response:**
```json
{
  "timestamp": "2025-11-13T14:30:00Z",
  "edges": [
    {
      "station": "EGLC",
      "city": "London",
      "event_day": "2025-11-13",
      "bracket": "58-59°F",
      "lower_F": 58,
      "upper_F": 59,
      "p_zeus": 0.283,
      "p_market": 0.0005,
      "edge": 0.2625,
      "size_usd": 300.0,
      "decision": "trade",
      "model_mode": "spread"
    }
  ]
}
```

**Implementation:**
- Read latest decision snapshots
- Parse edge calculations
- Filter by station/date if provided

---

### 3. Trades

**Get recent trades**
```
GET /api/trades/recent?limit={limit}&station={station}&date={date}
```

**Query params:**
- `limit` (optional): Number of trades (default 50)
- `station` (optional): Filter by station
- `date` (optional): Filter by date

**Response:**
```json
{
  "trades": [
    {
      "timestamp": "2025-11-13T14:21:18Z",
      "station": "EGLC",
      "event_day": "2025-11-13",
      "bracket": "58-59°F",
      "size_usd": 300.0,
      "edge": 0.2625,
      "p_zeus": 0.283,
      "p_market": 0.0005,
      "mode": "paper"
    }
  ],
  "total": 23,
  "filtered_by": {
    "station": "EGLC",
    "date": "2025-11-13"
  }
}
```

**Implementation:**
- Read paper_trades.csv files
- Parse and filter trades
- Return in reverse chronological order

---

### 4. Snapshots

**Get Zeus snapshots**
```
GET /api/snapshots/zeus?station={station}&date={date}
```

**Response:**
```json
{
  "snapshots": [
    {
      "fetch_time": "2025-11-13T14:21:10Z",
      "predicted_high": 57.8,
      "model_mode": "spread",
      "timeseries_count": 24
    }
  ]
}
```

**Get Polymarket snapshots**
```
GET /api/snapshots/polymarket?city={city}&date={date}
```

**Get Decision snapshots**
```
GET /api/snapshots/decisions?station={station}&date={date}
```

**Implementation:**
- List files in snapshot directories
- Parse JSON files
- Return sorted by timestamp

---

### 5. Activity Logs

**Get filtered activity logs**
```
GET /api/logs/activity?station={station}&date={date}&limit={limit}
```

**Response:**
```json
{
  "logs": [
    {
      "timestamp": "2025-11-13T14:21:10Z",
      "station": "EGLC",
      "event_day": "2025-11-13",
      "cycle": 45,
      "action": "start_cycle",
      "message": "Starting evaluation cycle #45",
      "level": "info"
    }
  ],
  "total": 234,
  "filtered_by": {
    "station": "EGLC",
    "date": "2025-11-13"
  }
}
```

**Get available dates with logs**
```
GET /api/logs/available-dates
```

**Response:**
```json
{
  "dates": [
    {"date": "2025-11-13", "label": "Today", "has_logs": true},
    {"date": "2025-11-14", "label": "Tomorrow", "has_logs": true},
    {"date": "2025-11-12", "label": "Yesterday", "has_logs": true}
  ]
}
```

**Implementation:**
- Parse dynamic paper trading log file
- Extract structured log entries
- Filter by station/date
- Reconstruct activity timeline from snapshots

---

### 6. METAR Data

**Get METAR observations**
```
GET /api/metar/observations?station={station}&date={date}&hours={hours}
```

**Response:**
```json
{
  "station": "EGLC",
  "date": "2025-11-13",
  "observations": [
    {
      "time": "2025-11-13T14:00:00Z",
      "temp_C": 12.0,
      "temp_F": 53.6,
      "raw": "EGLC 131400Z 25008KT..."
    }
  ],
  "daily_high": 58.2,
  "daily_low": 50.3
}
```

**Get daily high (for resolution)**
```
GET /api/metar/daily-high?station={station}&date={date}
```

**Compare Zeus vs METAR**
```
GET /api/compare/zeus-vs-metar?station={station}&date={date}
```

**Response:**
```json
{
  "station": "EGLC",
  "date": "2025-11-13",
  "zeus_predicted_high": 57.8,
  "actual_high": 58.2,
  "error": 0.4,
  "error_pct": 0.69,
  "accuracy_within_1F": true
}
```

**Implementation:**
- Call Aviation Weather Center API
- Parse METAR data
- Convert to Fahrenheit
- Compare with Zeus snapshots

---

### 7. Backtests

**Run backtest**
```
POST /api/backtest/run
```

**Request body:**
```json
{
  "start_date": "2025-11-13",
  "end_date": "2025-11-15",
  "stations": ["EGLC", "KLGA"],
  "config": {
    "model_mode": "bands",
    "edge_min": 0.05,
    "kelly_cap": 0.10,
    "fee_bp": 50,
    "slippage_bp": 30
  }
}
```

**Response:**
```json
{
  "job_id": "backtest_20251113_143022",
  "status": "running"
}
```

**Get backtest status**
```
GET /api/backtest/status/{job_id}
```

**Get backtest results**
```
GET /api/backtest/results/{job_id}
```

**Response:**
```json
{
  "job_id": "backtest_20251113_143022",
  "status": "complete",
  "config": {...},
  "summary": {
    "total_trades": 45,
    "wins": 12,
    "losses": 8,
    "pending": 25,
    "total_pnl": 1234.50,
    "roi": 0.123,
    "win_rate": 0.60
  },
  "trades": [...]
}
```

**Implementation:**
- Import Hermes Backtester
- Run in background task
- Save results to disk
- Return results when complete

---

### 8. WebSocket (Real-Time Updates)

**Connect to WebSocket**
```
WS /ws/trading
```

**Messages sent from server:**
```json
{
  "type": "cycle_complete",
  "data": {
    "cycle": 45,
    "station": "EGLC",
    "event_day": "2025-11-13",
    "trades_placed": 2,
    "total_size": 600.0
  }
}

{
  "type": "trade_placed",
  "data": {
    "station": "EGLC",
    "event_day": "2025-11-13",
    "bracket": "58-59°F",
    "size_usd": 300.0,
    "edge": 0.2625
  }
}

{
  "type": "edges_updated",
  "data": {
    "station": "EGLC",
    "event_day": "2025-11-13",
    "edges": [...]
  }
}
```

**Implementation:**
- Watch for new snapshot files (file watcher)
- Parse and broadcast to connected clients
- Support multiple concurrent connections

---

## 🛠️ Implementation Plan

### Phase 1: Core API (Week 1)

**Day 1-2: Setup**
```bash
# Create backend directory structure
mkdir -p backend/api/{routes,services,models,utils}
touch backend/api/main.py
touch backend/requirements.txt

# Install dependencies
cd backend
pip install fastapi uvicorn pydantic python-dotenv requests tenacity watchdog
```

**Day 3-4: Core Endpoints**
- Implement status endpoint
- Implement edges endpoint
- Implement trades endpoint
- Test with curl/Postman

**Day 5: Snapshot Endpoints**
- Implement Zeus snapshot endpoint
- Implement Polymarket snapshot endpoint
- Implement Decision snapshot endpoint

---

### Phase 2: Advanced Features (Week 2)

**Day 1-2: Activity Logs**
- Implement log parsing service
- Implement filtering logic
- Implement available-dates endpoint

**Day 3: METAR Integration**
- Implement METARService
- Implement comparison endpoint
- Add caching

**Day 4-5: WebSocket**
- Implement file watcher
- Implement WebSocket handler
- Test real-time updates

---

### Phase 3: Backtesting & Polish (Week 3)

**Day 1-2: Backtest API**
- Implement background task execution
- Implement status/results endpoints
- Add job queue

**Day 3-4: Testing & Documentation**
- Write unit tests
- Generate OpenAPI docs
- Test all endpoints

**Day 5: Deployment Setup**
- Add Dockerfile (optional)
- Add systemd service file
- Document deployment

---

## 📝 Service Implementation Examples

### StatusService

```python
# backend/api/services/status_service.py
from pathlib import Path
import subprocess
from typing import Optional

class StatusService:
    """Get system status information."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.pid_file = project_root / "logs" / "dynamic_paper.pid"
    
    def is_running(self) -> bool:
        """Check if dynamic paper trading is running."""
        if not self.pid_file.exists():
            return False
        
        try:
            with open(self.pid_file) as f:
                pid = int(f.read().strip())
            
            # Check if process exists
            result = subprocess.run(
                ["ps", "-p", str(pid)],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False
    
    def get_current_cycle(self) -> Optional[int]:
        """Get current cycle number from latest snapshots."""
        # Look for most recent decision snapshot
        snapshot_dir = self.project_root / "data/snapshots/dynamic/decisions"
        
        latest_file = None
        latest_time = 0
        
        for station_dir in snapshot_dir.glob("*"):
            for date_dir in station_dir.glob("*"):
                for file in date_dir.glob("*.json"):
                    mtime = file.stat().st_mtime
                    if mtime > latest_time:
                        latest_time = mtime
                        latest_file = file
        
        if latest_file:
            import json
            with open(latest_file) as f:
                data = json.load(f)
                # Extract cycle number from metadata
                return data.get("cycle")
        
        return None
    
    def get_status(self) -> dict:
        """Get complete system status."""
        return {
            "running": self.is_running(),
            "mode": "dynamic-paper" if self.is_running() else "stopped",
            "current_cycle": self.get_current_cycle(),
            "stations": ["EGLC", "KLGA"],  # Could read from config
            "interval_seconds": 900,  # Could read from config
        }
```

---

### SnapshotService

```python
# backend/api/services/snapshot_service.py
from pathlib import Path
from typing import List, Optional
import json
from datetime import date

class SnapshotService:
    """Read and parse snapshot data."""
    
    def __init__(self, project_root: Path):
        self.snapshots_dir = project_root / "data/snapshots/dynamic"
    
    def get_zeus_snapshots(
        self,
        station: str,
        event_date: date
    ) -> List[dict]:
        """Get Zeus snapshots for station/date."""
        snapshot_dir = (
            self.snapshots_dir / 
            "zeus" / 
            station / 
            event_date.isoformat()
        )
        
        if not snapshot_dir.exists():
            return []
        
        snapshots = []
        for file in sorted(snapshot_dir.glob("*.json")):
            with open(file) as f:
                data = json.load(f)
                
                # Extract summary
                temps = [
                    (p['temp_K'] - 273.15) * 9/5 + 32 
                    for p in data['timeseries']
                ]
                
                snapshots.append({
                    "fetch_time": data['fetch_time_utc'],
                    "predicted_high": round(max(temps), 1),
                    "model_mode": data.get('model_mode', 'spread'),
                    "timeseries_count": len(data['timeseries']),
                })
        
        return snapshots
    
    def get_polymarket_snapshots(
        self,
        city: str,
        event_date: date
    ) -> List[dict]:
        """Get Polymarket snapshots for city/date."""
        # Similar implementation
        pass
    
    def get_decision_snapshots(
        self,
        station: str,
        event_date: date
    ) -> List[dict]:
        """Get decision snapshots for station/date."""
        # Similar implementation
        pass
```

---

### METARService

```python
# backend/api/services/metar_service.py
import requests
from typing import List, Optional
from datetime import date, datetime

class METARService:
    """Fetch METAR data from Aviation Weather Center."""
    
    BASE_URL = "https://aviationweather.gov/api/data/metar"
    
    def get_observations(
        self,
        station: str,
        hours: int = 24,
        event_date: Optional[date] = None
    ) -> List[dict]:
        """Fetch METAR observations."""
        params = {
            "ids": station,
            "format": "json",
            "hours": hours,
        }
        
        if event_date:
            params["date"] = event_date.strftime("%Y%m%d")
        
        try:
            response = requests.get(
                self.BASE_URL,
                params=params,
                timeout=30,
                headers={"User-Agent": "HermesTradingSystem/1.0"}
            )
            response.raise_for_status()
            data = response.json()
            
            # Convert to Fahrenheit
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
            raise Exception(f"METAR API error: {e}")
    
    def get_daily_high(
        self,
        station: str,
        event_date: date
    ) -> Optional[float]:
        """Get daily high temperature."""
        observations = self.get_observations(station, hours=24, event_date=event_date)
        
        if not observations:
            return None
        
        temps = [obs["temp_F"] for obs in observations]
        return max(temps)
```

---

## 🧪 Testing

### Unit Tests

```python
# backend/tests/test_status_service.py
import pytest
from backend.api.services.status_service import StatusService

def test_status_service_running():
    service = StatusService(project_root)
    status = service.get_status()
    
    assert "running" in status
    assert "mode" in status
    assert isinstance(status["running"], bool)

# backend/tests/test_snapshot_service.py
def test_get_zeus_snapshots():
    service = SnapshotService(project_root)
    snapshots = service.get_zeus_snapshots("EGLC", date(2025, 11, 13))
    
    assert len(snapshots) > 0
    assert "fetch_time" in snapshots[0]
    assert "predicted_high" in snapshots[0]
```

---

## 🚀 Running the API

### Development

```bash
cd backend
uvicorn api.main:app --reload --port 8000
```

Access:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

### Production

```bash
# Using systemd
sudo systemctl start hermes-api

# Using Docker
docker-compose up -d

# Direct
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 🔒 Security Considerations

### CORS

```python
# backend/api/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Authentication (Future)

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

def verify_token(credentials = Depends(security)):
    if credentials.credentials != API_KEY:
        raise HTTPException(401, "Invalid token")
    return credentials

# Use on routes:
@app.get("/api/trades", dependencies=[Depends(verify_token)])
def get_trades():
    ...
```

---

## 📊 Phase 2: Database Migration (Optional)

### SQLite Schema

```sql
-- snapshots table
CREATE TABLE snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fetch_time TIMESTAMP NOT NULL,
    station_code VARCHAR(10),
    event_day DATE NOT NULL,
    snapshot_type VARCHAR(20) NOT NULL,  -- 'zeus', 'polymarket', 'decision'
    file_path VARCHAR(500) NOT NULL,
    metadata JSON,  -- Summary data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_snapshots_station_date ON snapshots(station_code, event_day);
CREATE INDEX idx_snapshots_type ON snapshots(snapshot_type);

-- trades table
CREATE TABLE trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_time TIMESTAMP NOT NULL,
    station_code VARCHAR(10) NOT NULL,
    event_day DATE NOT NULL,
    bracket VARCHAR(20) NOT NULL,
    p_zeus DECIMAL(10, 6),
    p_market DECIMAL(10, 6),
    edge DECIMAL(10, 6),
    size_usd DECIMAL(10, 2),
    model_mode VARCHAR(20),
    mode VARCHAR(10),  -- 'paper' or 'live'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trades_time ON trades(trade_time);
CREATE INDEX idx_trades_station_date ON trades(station_code, event_day);

-- activity_logs table
CREATE TABLE activity_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP NOT NULL,
    station_code VARCHAR(10),
    event_day DATE,
    cycle INTEGER,
    action VARCHAR(50) NOT NULL,
    message TEXT,
    level VARCHAR(10),
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_logs_timestamp ON activity_logs(timestamp);
CREATE INDEX idx_logs_station_date ON activity_logs(station_code, event_day);
```

### Migration Script

```python
# backend/api/migrations/migrate_to_db.py
import sqlite3
from pathlib import Path
import json
from datetime import datetime

def migrate_snapshots_to_db(project_root: Path, db_path: Path):
    """Migrate existing snapshots to database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    snapshot_dir = project_root / "data/snapshots/dynamic"
    
    for snapshot_type in ["zeus", "polymarket", "decisions"]:
        type_dir = snapshot_dir / snapshot_type
        
        for station_dir in type_dir.glob("*"):
            station = station_dir.name
            
            for date_dir in station_dir.glob("*"):
                event_day = date_dir.name
                
                for file in date_dir.glob("*.json"):
                    with open(file) as f:
                        data = json.load(f)
                    
                    fetch_time = data.get("fetch_time_utc", datetime.now().isoformat())
                    
                    # Extract summary metadata
                    metadata = {
                        # Type-specific summary
                    }
                    
                    cursor.execute("""
                        INSERT INTO snapshots 
                        (fetch_time, station_code, event_day, snapshot_type, file_path, metadata)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        fetch_time,
                        station,
                        event_day,
                        snapshot_type,
                        str(file),
                        json.dumps(metadata)
                    ))
    
    conn.commit()
    conn.close()
```

---

## ✅ Acceptance Criteria

### Phase 1 (File-Based API):

- [ ] FastAPI application runs on port 8000
- [ ] OpenAPI docs accessible at /docs
- [ ] CORS configured for frontend
- [ ] All core endpoints implemented:
  - [ ] GET /api/status
  - [ ] GET /api/edges/current
  - [ ] GET /api/trades/recent
  - [ ] GET /api/snapshots/zeus
  - [ ] GET /api/snapshots/polymarket
  - [ ] GET /api/snapshots/decisions
  - [ ] GET /api/logs/activity
  - [ ] GET /api/logs/available-dates
  - [ ] GET /api/metar/observations
  - [ ] GET /api/metar/daily-high
  - [ ] GET /api/compare/zeus-vs-metar
  - [ ] POST /api/backtest/run
  - [ ] GET /api/backtest/status/{job_id}
  - [ ] GET /api/backtest/results/{job_id}
  - [ ] WS /ws/trading
- [ ] Filtering works (by station, by date)
- [ ] WebSocket streams real-time updates
- [ ] METAR integration working
- [ ] Backtest execution functional
- [ ] Unit tests passing
- [ ] Documentation complete

### Phase 2 (Database - Optional):

- [ ] SQLite database created
- [ ] Migration script working
- [ ] Database queries optimized
- [ ] API performance improved (<100ms per request)
- [ ] Aggregations working

---

## 📚 Documentation

### API Documentation

Auto-generated by FastAPI:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

### Development Guide

Create `backend/README.md`:
- Setup instructions
- Running the API
- Testing
- Deployment
- Architecture overview

---

## 🎯 Summary

### What Stage 7D Delivers:

✅ **REST API** for Hermes frontend  
✅ **Real-time updates** via WebSocket  
✅ **METAR integration** for actual temps  
✅ **Backtest execution** on demand  
✅ **Activity log filtering** by station/day  
✅ **File-based** (no database required for MVP)  
✅ **Optional SQLite migration** for production  

### Timeline:

- **Week 1**: Core API endpoints
- **Week 2**: Advanced features (logs, METAR, WebSocket)
- **Week 3**: Backtesting, testing, polish

**Total**: 3 weeks for complete backend API

### Database Decision:

**Phase 1 (MVP)**: File-based ✅ Start here  
**Phase 2 (Production)**: SQLite 🔄 Add later if needed  

Start with files, add database only when:
- Queries become slow (>1s)
- Have >30 days of data
- Need advanced analytics

---

**Status**: Ready to implement  
**Next Step**: Create `backend/api/main.py` and begin Phase 1

**Author**: Hermes Development Team  
**Date**: November 13, 2025

