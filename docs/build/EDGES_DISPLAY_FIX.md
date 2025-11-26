# Edges Display Fix - Summary

## Issues Fixed

### 1. ✅ Zeus % and Market % Now Included

**Problem:** Frontend showed "N/A" for Zeus % and Market % columns.

**Root Cause:** 
- `EdgeDecision` model doesn't include `p_zeus` or `p_mkt`
- Snapshotter wasn't saving these values
- Edge service wasn't returning them in API response

**Solution:**
1. Updated `snapshotter.py` to accept `probs_with_market` parameter
2. Creates mapping from `market_id` → `BracketProb` to look up probabilities
3. Saves `p_zeus` and `p_mkt` in decision snapshots
4. Updated `edge_service.py` to include these in API response

**Files Changed:**
- `agents/dynamic_trader/snapshotter.py`
- `agents/dynamic_trader/dynamic_engine.py`
- `backend/api/services/edge_service.py`

**Next Steps:**
- Restart dynamic trading engine to generate new snapshots with probabilities
- New API responses will include `p_zeus` and `p_mkt` fields
- Frontend should display these values (convert to percentages: `p_zeus * 100`)

### 2. ⚠️ Only 1 Edge Showing When 2 Trades Placed

**Problem:** User placed 2 trades but only 1 edge shows in the frontend.

**Root Cause:**
The edge service **deduplicates by (station, event_day, bracket)**. This means:
- If multiple trades are for the **SAME bracket**, only the most recent shows
- If trades are for **DIFFERENT brackets**, both should show

**Investigation:**
- Activity log shows: `[43-44°F): $300.00 @ edge=58.69%` and `[45-46°F): $300.00 @ edge=10.32%`
- These are **different brackets**, so both should appear
- But frontend is filtering by `event_day=2025-11-19`
- Decision snapshots for `2025-11-19` only show `44-45°F` (different bracket!)
- Decision snapshots for `2025-11-20` show `43-44°F` and other brackets

**Possible Causes:**
1. **Event Day Mismatch**: Trades might be for `2025-11-20` but frontend is showing `2025-11-19`
2. **Snapshot Timing**: The 2 trades might have been placed in different cycles, and only one snapshot is being read
3. **Edge Service Filtering**: The edge service might be filtering out one of the brackets

**How to Debug:**
1. Check which event day the frontend is filtering by
2. Check if trades are for the same event day as the filter
3. Check if both brackets appear in the decision snapshots for that event day
4. Test API directly: `curl "http://localhost:8000/api/edges/current?station_code=EGLC&event_day=2025-11-20"`

**Expected Behavior:**
- If 2 trades are for **different brackets** (e.g., 43-44°F and 45-46°F), both should show
- If 2 trades are for the **same bracket** (e.g., both 44-45°F), only the most recent shows
- Edge service shows the **most recent edge** for each unique (station, event_day, bracket) combination

## Testing

### Test Zeus % and Market %:
```bash
# After restarting engine, check a new snapshot
cat data/snapshots/dynamic/decisions/EGLC/2025-11-20/<latest>.json | jq '.decisions[0] | {bracket, p_zeus, p_mkt}'

# Check API response
curl "http://localhost:8000/api/edges/current?station_code=EGLC&event_day=2025-11-20" | jq '.edges[0] | {bracket, p_zeus, p_mkt}'
```

### Test Multiple Edges:
```bash
# Check if multiple brackets exist in snapshots
find data/snapshots/dynamic/decisions/EGLC/2025-11-20 -name "*.json" -exec sh -c 'echo "=== {} ===" && cat {} | jq ".decisions[].bracket"' \;

# Check API for all edges
curl "http://localhost:8000/api/edges/current?station_code=EGLC&event_day=2025-11-20" | jq '.edges[] | {bracket, edge_pct}'
```

## Frontend Updates Needed

1. **Display p_zeus and p_mkt:**
   - Convert to percentages: `p_zeus * 100` and `p_mkt * 100`
   - Format as: `"12.5%"` or `"N/A"` if null

2. **Event Day Selector:**
   - Make sure it includes all event days with open markets
   - Update to show edges for the selected event day
   - Consider showing edges for "most recent event day" by default

3. **Multiple Edges:**
   - If API returns multiple edges, display all of them
   - Don't filter client-side (backend already deduplicates)


