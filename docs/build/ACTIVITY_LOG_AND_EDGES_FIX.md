# Activity Log and Edges Display Fix

## Issues Identified

1. **Activity Log Only Showing One Cycle**
   - The log file contained 37 cycles, but the frontend was only showing one
   - Root cause: Log parser wasn't extracting station codes from city names (e.g., "London" → "EGLC")
   - Root cause: Event days weren't being extracted from multi-line log entries

2. **Edges Not Showing**
   - Edges were being saved correctly to decision snapshots
   - API endpoint `/api/edges/current` was working correctly
   - Issue was likely frontend display or filtering

## Fixes Applied

### 1. Enhanced Log Parser (`backend/api/services/log_service.py`)

**Station Code Extraction:**
- Added city name to station code mapping using `StationRegistry`
- Pattern matching: `"City → YYYY-MM-DD"` or `"City → event"`
- Falls back to 4-letter code pattern if city name not found

**Event Day Extraction:**
- Extracts from message content (YYYY-MM-DD format)
- Falls back to timestamp date if not found in message
- Works with continuation lines

**Multi-line Log Entries:**
- Properly combines continuation lines with timestamped entries
- Re-parses full message after combining to extract station/date
- Preserves timestamp and log level from original entry

### 2. Edge Service Verification

The edge service was already working correctly:
- Decision snapshots are saved to `data/snapshots/dynamic/decisions/`
- Edge service reads from correct path: `snapshots_dir / "decisions"`
- API endpoint `/api/edges/current?station_code=EGLC&event_day=2025-11-19` returns edges correctly

## Test Results

### Activity Logs
```bash
curl "http://localhost:8000/api/logs/activity?station_code=EGLC&event_day=2025-11-19&limit=5"
```

**Result:** Now returns 18 log entries (previously 0)
- Station codes correctly extracted: `"station_code": "EGLC"`
- Event days correctly extracted: `"event_day": "2025-11-19"`
- Multiple cycles visible in results

### Edges
```bash
curl "http://localhost:8000/api/edges/current?station_code=EGLC&event_day=2025-11-19"
```

**Result:** Returns 1 edge correctly
- Edge data includes: bracket, edge_pct, size_usd, reason
- Example: `"edge_pct": 9.62, "size_usd": 300.0`

## Expected Frontend Behavior

### Activity Log Panel
- Should now show **multiple cycles** (not just one)
- Should show **all log entries** for the selected station/date
- Should correctly filter by station code and event day

### Current Edges Panel
- Should display edges from the latest decision snapshots
- Should show bracket, edge percentage, size, and reason
- Should update when new decision snapshots are created

## Verification Steps

1. **Check Activity Log:**
   - Navigate to Live Dashboard
   - Select station: EGLC
   - Select event day: 2025-11-19
   - Verify multiple log entries are displayed

2. **Check Edges:**
   - Navigate to Live Dashboard
   - Select station: EGLC
   - Select event day: 2025-11-19
   - Verify edges are displayed in "Current Edges" panel

3. **Check API Directly:**
   ```bash
   # Activity logs
   curl "http://localhost:8000/api/logs/activity?station_code=EGLC&event_day=2025-11-19&limit=10"
   
   # Edges
   curl "http://localhost:8000/api/edges/current?station_code=EGLC&event_day=2025-11-19"
   ```

## Notes

- **FastAPI Server Restart:** Changes to `log_service.py` require a FastAPI server restart to take effect
- **Log File Format:** The parser handles Rich console output format with multi-line continuation
- **Station Registry:** Uses `core.registry.StationRegistry` to map city names to station codes

## Related Files

- `backend/api/services/log_service.py` - Log parsing and filtering
- `backend/api/services/edge_service.py` - Edge retrieval from decision snapshots
- `backend/api/routes/logs.py` - Activity log API endpoints
- `backend/api/routes/edges.py` - Edge API endpoints
- `agents/dynamic_trader/snapshotter.py` - Decision snapshot saving


