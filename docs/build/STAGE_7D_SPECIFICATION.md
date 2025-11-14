# Stage 7D — Backend API & Frontend Dashboard

**Date**: November 13, 2025  
**Status**: Specification  
**Dependencies**: Stages 1-7C (Complete)  
**Structure**: Backend API in main repo, Frontend built separately

---

## 🎯 Objective

Build a **REST API backend** to power real-time monitoring, historical analysis, and backtest execution for the Hermes trading system.

**End Goal**: Complete FastAPI backend with all endpoints needed for a frontend dashboard. The frontend will be built separately as a standalone project.

**Note**: Frontend dashboard is built separately. See `docs/build/FRONTEND_STANDALONE_BUILD.md` for complete frontend build guide.

---

## 📋 Overview

### What We're Building:

1. **METAR API Integration** - Fetch actual temperatures for comparison
2. **FastAPI Backend** - REST API + WebSocket for frontend
3. **API Documentation** - Complete endpoint specifications for frontend developers

### Project Structure:

```
hermes-v1.0.0/                          # Main Hermes repository
├── core/                               # Existing - Trading engine
├── agents/                             # Existing - Trading logic
├── venues/                             # Existing - Market APIs
│   └── metar/                          # NEW - Stage 7D-1
├── data/                               # Existing - Data storage
│
└── backend/                            # NEW - FastAPI backend
    ├── api/
    │   ├── main.py
    │   ├── routes/
    │   ├── services/
    │   └── models/
    └── requirements.txt

hermes-frontend/                        # SEPARATE PROJECT (built separately)
├── src/                                # React or Streamlit
└── package.json                        # or requirements.txt
```

**Key Principle**: Backend API is built in the main Hermes repo. Frontend is built as a separate project that connects to the backend API.

---

## 🗺️ Stage Breakdown

### Stage 7D-1: METAR API Integration ⚠️ **START HERE**

**Why First**: METAR service is needed by backend API endpoints. Must be integrated before building API.

**Goal**: Integrate Aviation Weather Center METAR API to fetch actual temperature observations.

**📋 Reference**: See `docs/build/metar_integration.md` for complete API documentation, endpoint specifications, rate limits, error handling, and best practices.

**Deliverables**:
1. Create `venues/metar/` module
2. Implement `METARService` class
3. Fetch observations for station/date
4. Calculate daily high/low
5. Convert Celsius to Fahrenheit
6. Add retry logic and error handling
7. Unit tests

**Files to Create**:
- `venues/metar/__init__.py`
- `venues/metar/metar_service.py`
- `tests/test_metar_service.py`

**Acceptance Criteria**:
- [ ] Can fetch METAR observations for any station
- [ ] Returns temperatures in Fahrenheit
- [ ] Calculates daily high correctly
- [ ] Handles API errors gracefully
- [ ] Tests passing

**Estimated Time**: 1 day

---

### Stage 7D-2: Backend Structure & Core Services

**Dependencies**: Stage 7D-1 (METAR integration)

**Goal**: Set up FastAPI backend structure and core file-reading services.

**Deliverables**:
1. Create `backend/` directory structure
2. Initialize FastAPI app with CORS
3. Create `SnapshotService` (read Zeus/Polymarket/Decision snapshots)
4. Create `LogService` (read and parse activity logs)
5. Create `TradeService` (read paper trades CSV)
6. Create Pydantic models/schemas
7. Basic health check endpoint

**Files to Create**:
- `backend/api/main.py`
- `backend/api/services/__init__.py`
- `backend/api/services/snapshot_service.py`
- `backend/api/services/log_service.py`
- `backend/api/services/trade_service.py`
- `backend/api/models/schemas.py`
- `backend/api/utils/file_utils.py`
- `backend/api/utils/path_utils.py`
- `backend/requirements.txt`
- `backend/README.md`

**Acceptance Criteria**:
- [ ] FastAPI app runs on port 8000
- [ ] OpenAPI docs accessible at /docs
- [ ] CORS configured
- [ ] Can read snapshots from file system
- [ ] Can read trades from CSV
- [ ] Can parse activity logs
- [ ] Health check endpoint works

**Estimated Time**: 1-2 days

---

### Stage 7D-3: Basic API Endpoints (Status, Edges, Trades, Snapshots)

**Dependencies**: Stage 7D-2 (Backend structure)

**Goal**: Implement core REST endpoints for system status, edges, trades, and snapshots.

**Deliverables**:
1. `StatusService` - Check if trading engine is running
2. `GET /api/status` - System status endpoint
3. `GET /api/edges/current` - Current edges with filtering
4. `GET /api/trades/recent` - Recent trades with filtering
5. `GET /api/snapshots/zeus` - Zeus snapshots
6. `GET /api/snapshots/polymarket` - Polymarket snapshots
7. `GET /api/snapshots/decisions` - Decision snapshots

**Files to Create/Modify**:
- `backend/api/services/status_service.py`
- `backend/api/routes/status.py`
- `backend/api/routes/edges.py`
- `backend/api/routes/trades.py`
- `backend/api/routes/snapshots.py`
- `backend/tests/test_status_service.py`
- `backend/tests/test_routes.py`

**Acceptance Criteria**:
- [ ] All endpoints return correct data
- [ ] Filtering works (by station, by date)
- [ ] Error handling for missing data
- [ ] Response formats match spec
- [ ] Tests passing

**Estimated Time**: 2-3 days

---

### Stage 7D-4: METAR Endpoints & Comparison

**Dependencies**: Stage 7D-1 (METAR integration), Stage 7D-3 (Basic endpoints)

**Goal**: Expose METAR data via API and add Zeus vs METAR comparison.

**Deliverables**:
1. `GET /api/metar/observations` - METAR observations endpoint
2. `GET /api/metar/daily-high` - Daily high temperature
3. `GET /api/compare/zeus-vs-metar` - Compare predictions vs actual
4. Integrate METAR service from Stage 7D-1
5. Add caching for METAR responses

**Files to Create/Modify**:
- `backend/api/routes/metar.py`
- `backend/api/services/metar_service.py` (wrapper around venues/metar)
- `backend/tests/test_metar_routes.py`

**Acceptance Criteria**:
- [ ] METAR endpoints return correct data
- [ ] Comparison endpoint calculates error correctly
- [ ] Caching reduces API calls
- [ ] Handles missing METAR data gracefully
- [ ] Tests passing

**Estimated Time**: 1 day

---

### Stage 7D-5: Activity Logs & Filtering

**Dependencies**: Stage 7D-3 (Basic endpoints)

**Goal**: Implement activity log endpoints with advanced filtering.

**Deliverables**:
1. `GET /api/logs/activity` - Filtered activity logs
2. `GET /api/logs/available-dates` - List dates with logs
3. Enhanced `LogService` with filtering logic
4. Support filtering by:
   - Station
   - Event day (today, tomorrow, past 3 days, future)
   - Action type
   - Log level
5. Pagination support

**Files to Create/Modify**:
- `backend/api/routes/logs.py`
- `backend/api/services/log_service.py` (enhance)
- `backend/tests/test_log_service.py`

**Acceptance Criteria**:
- [ ] Can filter logs by station
- [ ] Can filter logs by event day
- [ ] Available dates endpoint works
- [ ] Pagination works
- [ ] Performance acceptable (<500ms)
- [ ] Tests passing

**Estimated Time**: 1-2 days

---

### Stage 7D-6: WebSocket Real-Time Updates

**Dependencies**: Stage 7D-3 (Basic endpoints)

**Goal**: Add WebSocket support for real-time dashboard updates.

**Deliverables**:
1. `WS /ws/trading` - WebSocket endpoint
2. File watcher for new snapshots
3. Broadcast events:
   - `cycle_complete` - New cycle finished
   - `trade_placed` - New trade executed
   - `edges_updated` - Edges recalculated
4. Support multiple concurrent connections
5. Connection management

**Files to Create/Modify**:
- `backend/api/routes/websocket.py`
- `backend/api/services/websocket_service.py`
- `backend/api/utils/file_watcher.py`
- `backend/tests/test_websocket.py`

**Acceptance Criteria**:
- [ ] WebSocket connects successfully
- [ ] Receives real-time updates
- [ ] Multiple clients supported
- [ ] Handles disconnections gracefully
- [ ] File watcher detects new snapshots
- [ ] Tests passing

**Estimated Time**: 2 days

---

### Stage 7D-7: Backtest API

**Dependencies**: Stage 7D-3 (Basic endpoints)

**Goal**: Expose backtest execution via API with background job support.

**Deliverables**:
1. `POST /api/backtest/run` - Start backtest job
2. `GET /api/backtest/status/{job_id}` - Check job status
3. `GET /api/backtest/results/{job_id}` - Get results
4. Background job execution (async)
5. Job queue management
6. Integrate existing `Backtester` from `agents/backtester.py`

**Files to Create/Modify**:
- `backend/api/routes/backtest.py`
- `backend/api/services/backtest_service.py`
- `backend/api/utils/job_queue.py`
- `backend/tests/test_backtest_service.py`

**Acceptance Criteria**:
- [ ] Can start backtest via API
- [ ] Job status endpoint works
- [ ] Results endpoint returns data
- [ ] Background execution works
- [ ] Handles errors gracefully
- [ ] Tests passing

**Estimated Time**: 2 days

---

### Stage 7D-8: Frontend Build (Separate Project) ⚠️ **BUILT SEPARATELY**

**Status**: Frontend is built as a **separate standalone project**, not in this repository.

**📋 Complete Guide**: See `docs/build/FRONTEND_STANDALONE_BUILD.md` for:
- Complete frontend build instructions
- All UI mockups and "what users will see" sections
- API integration details
- Technology stack recommendations
- Step-by-step implementation guide
- Testing checklist

**What Frontend Developers Need:**
1. Backend API running at `http://localhost:8000`
2. API documentation at `http://localhost:8000/docs`
3. `FRONTEND_STANDALONE_BUILD.md` for complete specifications
4. All UI mockups and design requirements

**Backend Requirements (Completed in Stages 7D-1 through 7D-7):**
- ✅ All API endpoints implemented
- ✅ WebSocket real-time updates
- ✅ Complete API documentation
- ✅ CORS configured for frontend access

**Estimated Time**: 1-4 weeks (depending on framework choice)

---

### Stage 7D-9: Backend Integration Testing

**Dependencies**: Stages 7D-1 through 7D-7 (All backend endpoints)

**Goal**: Test backend API with frontend integration scenarios.

**Deliverables**:
1. Integration tests for all API endpoints
2. WebSocket connection testing
3. Error handling validation
4. Performance testing
5. CORS configuration verification
6. API documentation completeness check

**Files to Create/Modify**:
- `backend/tests/test_integration.py`
- `backend/tests/test_api_endpoints.py`
- `backend/tests/test_websocket.py`

**Acceptance Criteria**:
- [ ] All endpoints tested with realistic data
- [ ] WebSocket connections work reliably
- [ ] Error responses are correct
- [ ] Performance acceptable (<500ms for most endpoints)
- [ ] API docs are complete and accurate
- [ ] CORS allows frontend access

**Estimated Time**: 2-3 days

---

### Stage 7D-10: Documentation & Deployment

**Dependencies**: All previous stages

**Goal**: Complete backend documentation and deployment guide.

**Deliverables**:
1. Backend API documentation
2. Deployment guide for backend
3. Environment setup guide
4. Troubleshooting guide
5. Summary documentation

**Files to Create/Modify**:
- `docs/build/STAGE_7D_SUMMARY.md`
- `backend/README.md` (update)
- `docs/build/BACKEND_DEPLOYMENT.md`
- `README.md` (update with backend info)

**Acceptance Criteria**:
- [ ] Complete API documentation
- [ ] Deployment guide ready
- [ ] Environment setup documented
- [ ] Troubleshooting guide complete
- [ ] Summary documentation written

**Estimated Time**: 1-2 days

---

## 📊 Implementation Timeline

### Backend Only (This Repository):
- **Week 1**: Stages 7D-1 through 7D-7 (Backend + METAR + WebSocket)
- **Week 2**: Stages 7D-8 through 7D-10 (Testing + Documentation)

### Frontend (Separate Project):
- **Timeline**: 1-4 weeks (depending on framework)
- **See**: `docs/build/FRONTEND_STANDALONE_BUILD.md` for complete guide

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│        Frontend (Separate Project - Built Separately)       │
│  • Live dashboard                                           │
│  • Historical view                                          │
│  • Backtest runner                                          │
│  • See: FRONTEND_STANDALONE_BUILD.md                        │
└─────────────────────────────────────────────────────────────┘
                           │
                    HTTP + WebSocket
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│        FastAPI Backend (This Repository - Stage 7D)         │
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
│  │  • METARService (from venues/metar/)                │   │
│  │  • BacktestService                                  │   │
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
│  • METAR service (NEW - Stage 7D-1)                        │
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

### Main Hermes Repository (This Repo):

```
hermes-v1.0.0/                          # Main Hermes repository
├── core/                               # Existing - Trading engine
├── agents/                             # Existing - Trading logic
├── venues/                             # Existing - Market APIs
│   └── metar/                          # NEW - Stage 7D-1
│       ├── __init__.py
│       └── metar_service.py
│
├── backend/                            # NEW - FastAPI backend (Stage 7D)
│   ├── api/
│   │   ├── main.py                     # FastAPI app entry point
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── status.py
│   │   │   ├── edges.py
│   │   │   ├── trades.py
│   │   │   ├── snapshots.py
│   │   │   ├── logs.py
│   │   │   ├── metar.py
│   │   │   ├── backtest.py
│   │   │   └── websocket.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── status_service.py
│   │   │   ├── snapshot_service.py
│   │   │   ├── log_service.py
│   │   │   ├── trade_service.py
│   │   │   ├── metar_service.py        # Wrapper around venues/metar
│   │   │   └── backtest_service.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── schemas.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── file_utils.py
│   │       ├── path_utils.py
│   │       ├── file_watcher.py
│   │       └── job_queue.py
│   ├── tests/
│   ├── requirements.txt
│   └── README.md
│
└── data/                               # Existing - Data storage
```

### Frontend (Separate Project):

```
hermes-frontend/                        # SEPARATE PROJECT
├── src/                                # React or Streamlit
│   ├── components/
│   ├── pages/
│   ├── api/
│   └── App.tsx
├── package.json                        # (React)
├── requirements.txt                    # (Streamlit)
└── README.md

See: docs/build/FRONTEND_STANDALONE_BUILD.md for complete structure
```

---

## 🔌 API Endpoints Summary

### System Status
- `GET /api/status` - System status (Stage 7D-3)

### Edges & Trades
- `GET /api/edges/current` - Current edges (Stage 7D-3)
- `GET /api/trades/recent` - Recent trades (Stage 7D-3)

### Snapshots
- `GET /api/snapshots/zeus` - Zeus snapshots (Stage 7D-3)
- `GET /api/snapshots/polymarket` - Polymarket snapshots (Stage 7D-3)
- `GET /api/snapshots/decisions` - Decision snapshots (Stage 7D-3)

### Logs
- `GET /api/logs/activity` - Activity logs (Stage 7D-5)
- `GET /api/logs/available-dates` - Available dates (Stage 7D-5)

### METAR
- `GET /api/metar/observations` - METAR observations (Stage 7D-4)
- `GET /api/metar/daily-high` - Daily high (Stage 7D-4)
- `GET /api/compare/zeus-vs-metar` - Comparison (Stage 7D-4)

### Backtests
- `POST /api/backtest/run` - Run backtest (Stage 7D-7)
- `GET /api/backtest/status/{job_id}` - Job status (Stage 7D-7)
- `GET /api/backtest/results/{job_id}` - Results (Stage 7D-7)

### Real-Time
- `WS /ws/trading` - WebSocket updates (Stage 7D-6)

---

## ✅ Overall Acceptance Criteria

### Backend:
- [ ] All API endpoints implemented
- [ ] METAR integration working
- [ ] WebSocket real-time updates
- [ ] Backtest execution via API
- [ ] Filtering and pagination
- [ ] Error handling
- [ ] Tests passing
- [ ] Documentation complete

### Backend API:
- [ ] All endpoints return correct data
- [ ] WebSocket connections work
- [ ] Error handling comprehensive
- [ ] Performance acceptable
- [ ] API documentation complete
- [ ] CORS configured for frontend access
- [ ] Ready for frontend integration

---

## 🚀 Quick Start Commands

### Stage 7D-1: METAR Integration
```bash
# Create METAR module
mkdir -p venues/metar
touch venues/metar/__init__.py venues/metar/metar_service.py
```

### Stage 7D-2: Backend Setup
```bash
# Create backend structure
mkdir -p backend/api/{routes,services,models,utils}
mkdir -p backend/tests
touch backend/api/main.py backend/requirements.txt
```

### Frontend Build (Separate Project)
```bash
# See: docs/build/FRONTEND_STANDALONE_BUILD.md
# Frontend is built as a separate project
```

---

## 📚 Related Documentation

- **`docs/build/metar_integration.md`**: ⚠️ **REQUIRED REFERENCE** for Stage 7D-1
  - Complete AviationWeather.gov METAR API documentation
  - Endpoint specifications, parameters, response schema
  - Rate limits, error handling, best practices
  - Example API calls and Python mapping
  - **MUST be consulted when implementing METAR service**
- **`docs/build/FRONTEND_STANDALONE_BUILD.md`**: ⚠️ **COMPLETE FRONTEND BUILD GUIDE**
  - Standalone frontend build instructions
  - All UI mockups and "what users will see" sections
  - Complete API integration details
  - Technology stack recommendations
  - Step-by-step implementation guide
  - **Use this document to build the frontend separately**
- **`docs/build/FRONTEND.md`**: Original UI/UX design specifications (referenced in standalone guide)
- **`docs/build/FRONT_END_DEV.md`**: Original monorepo development guide (superseded by standalone guide)
- **`docs/build/STAGE_7C_SUMMARY.md`**: Dynamic trading engine (prerequisite)

---

## 🎯 Summary

**Stage 7D** breaks down into **10 sub-stages** (Backend Only):

1. **7D-1**: METAR API Integration (1 day) ⚠️ **START HERE**
2. **7D-2**: Backend Structure & Services (1-2 days)
3. **7D-3**: Basic API Endpoints (2-3 days)
4. **7D-4**: METAR Endpoints (1 day)
5. **7D-5**: Activity Logs (1-2 days)
6. **7D-6**: WebSocket (2 days)
7. **7D-7**: Backtest API (2 days)
8. **7D-8**: Frontend Build (Separate Project) - See `FRONTEND_STANDALONE_BUILD.md`
9. **7D-9**: Backend Integration Testing (2-3 days)
10. **7D-10**: Documentation & Deployment (1-2 days)

**Total Timeline**:
- **Backend Only**: ~2 weeks
- **Frontend** (Separate): 1-4 weeks (see `FRONTEND_STANDALONE_BUILD.md`)

**Next Step**: Start with **Stage 7D-1** (METAR API Integration)

**Note**: Frontend is built separately using `FRONTEND_STANDALONE_BUILD.md` as the complete guide.

---

**Author**: Hermes Development Team  
**Date**: November 13, 2025  
**Status**: Ready to implement
