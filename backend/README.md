# Hermes Backend API

FastAPI backend for the Hermes trading system dashboard.

## Setup

1. Install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. Run the server:
   ```bash
   python -m api.main
   # Or using uvicorn directly:
   uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. Access the API:
   - API: http://localhost:8000
   - OpenAPI docs: http://localhost:8000/docs
   - Health check: http://localhost:8000/health

## API Endpoints

### Status
- `GET /api/status` - System status

### Snapshots
- `GET /api/snapshots/zeus?station_code=EGLC&event_day=2025-11-13` - Zeus snapshots
- `GET /api/snapshots/polymarket?city=London&event_day=2025-11-13` - Polymarket snapshots
- `GET /api/snapshots/decisions?station_code=EGLC&event_day=2025-11-13` - Decision snapshots
- `GET /api/snapshots/metar?station_code=EGLC&event_day=2025-11-13` - METAR snapshots

### Trades
- `GET /api/trades/recent?trade_date=2025-11-13&station_code=EGLC` - Recent trades
- `GET /api/trades/summary?trade_date=2025-11-13` - Trade summary

### Logs
- `GET /api/logs/activity?limit=100&station_code=EGLC` - Activity logs

## Development

The backend reads data from the main project's `data/` directory:
- Snapshots: `data/snapshots/dynamic/`
- Trades: `data/trades/`
- Logs: `logs/`

Make sure the main project is running and generating data before testing the API.

