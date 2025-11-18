# Activity Log Format - What the Frontend Should Display

**Date**: November 17, 2025  
**Purpose**: Document the expected format and content of activity logs for the frontend

---

## 📋 Expected Log Format

The activity log should display structured, readable entries showing what the trading engine is doing in real-time.

### Example Log Entry Format

```
[14:21:10] 🔄 Starting evaluation cycle #45
[14:21:12] 🌡️  Fetched Zeus forecast for EGLC (Nov 17) → High: 57.8°F
[14:21:14] 💰 Fetched Polymarket prices for London Nov 17 → 12 brackets
[14:21:16] 🧮 Calculated probabilities (spread model)
            • 58-59°F: p_zeus=28.3%, p_market=0.05%, edge=26.25% ✅
            • 60-61°F: p_zeus=33.5%, p_market=6.95%, edge=25.75% ✅
[14:21:18] 📝 Placed 2 paper trades → Total: $600.00
[14:21:18] 💾 Saved snapshots (zeus/polymarket/decisions)
[14:21:18] ✅ Cycle #45 complete. Next cycle in 15:00
```

---

## 🔍 What Each Log Entry Should Show

### 1. Cycle Start
- **Format**: `[HH:MM:SS] 🔄 Starting evaluation cycle #N`
- **Example**: `[14:21:10] 🔄 Starting evaluation cycle #45`
- **Action Type**: `cycle`
- **Level**: `INFO`

### 2. Zeus Forecast Fetch
- **Format**: `[HH:MM:SS] 🌡️  Fetched Zeus forecast for STATION (Date) → High: XX.X°F`
- **Example**: `[14:21:12] 🌡️  Fetched Zeus forecast for EGLC (Nov 17) → High: 57.8°F`
- **Action Type**: `fetch`
- **Level**: `INFO`
- **Station Code**: Extracted (e.g., `EGLC`)
- **Event Day**: Extracted (e.g., `2025-11-17`)

### 3. Polymarket Prices Fetch
- **Format**: `[HH:MM:SS] 💰 Fetched Polymarket prices for CITY Date → N brackets`
- **Example**: `[14:21:14] 💰 Fetched Polymarket prices for London Nov 17 → 12 brackets`
- **Action Type**: `fetch`
- **Level**: `INFO`

### 4. Probability Calculation
- **Format**: `[HH:MM:SS] 🧮 Calculated probabilities (model)`
- **Example**: `[14:21:16] 🧮 Calculated probabilities (spread model)`
- **Action Type**: `decision`
- **Level**: `INFO`
- **Note**: May include sub-entries showing individual bracket edges

### 5. Trade Placement
- **Format**: `[HH:MM:SS] 📝 Placed N paper trades → Total: $XXX.XX`
- **Example**: `[14:21:18] 📝 Placed 2 paper trades → Total: $600.00`
- **Action Type**: `trade`
- **Level**: `INFO`

### 6. Snapshot Save
- **Format**: `[HH:MM:SS] 💾 Saved snapshots (types)`
- **Example**: `[14:21:18] 💾 Saved snapshots (zeus/polymarket/decisions)`
- **Action Type**: `snapshot`
- **Level**: `INFO`

### 7. Cycle Complete
- **Format**: `[HH:MM:SS] ✅ Cycle #N complete. Next cycle in MM:SS`
- **Example**: `[14:21:18] ✅ Cycle #45 complete. Next cycle in 15:00`
- **Action Type**: `cycle`
- **Level**: `INFO`

---

## 🚫 What Should NOT Appear

The following should **NOT** be displayed as log entries:

- ❌ Empty lines
- ❌ Lines with only whitespace
- ❌ File paths (e.g., `pshots/zeus/2025-11-17/EGLC.`)
- ❌ Truncated messages (e.g., `pshots/zeus/2025-11-17/EGLC.`)
- ❌ Entries with `timestamp: null`
- ❌ Entries with `level: null` (unless it's a continuation line)
- ❌ Orphaned continuation lines without a parent entry

---

## 📊 API Response Structure

The `/api/logs/activity` endpoint returns:

```json
{
  "logs": [
    {
      "timestamp": "2025-11-17T14:21:10",
      "log_file": "dynamic_paper_20251117_142110.log",
      "level": "INFO",
      "message": "🔄 Starting evaluation cycle #45",
      "station_code": "EGLC",
      "event_day": "2025-11-17",
      "action_type": "cycle"
    },
    {
      "timestamp": "2025-11-17T14:21:12",
      "log_file": "dynamic_paper_20251117_142110.log",
      "level": "INFO",
      "message": "🌡️  Fetched Zeus forecast for EGLC (Nov 17) → High: 57.8°F",
      "station_code": "EGLC",
      "event_day": "2025-11-17",
      "action_type": "fetch"
    }
  ],
  "count": 2,
  "total": 150,
  "offset": 0,
  "limit": 20,
  "has_more": true
}
```

---

## 🎨 Frontend Display Recommendations

### Formatting
- **Timestamp**: Display as `[HH:MM:SS]` (local time, not UTC)
- **Level**: Color-code by level:
  - `INFO`: Blue/Default
  - `DEBUG`: Gray
  - `WARNING`: Yellow
  - `ERROR`: Red
  - `CRITICAL`: Red, bold
- **Message**: Display as-is (includes emojis)
- **Action Type**: Optional badge/icon

### Filtering
- **By Station**: Show only logs for selected station
- **By Event Day**: Show only logs for selected date
- **By Action Type**: Filter by `fetch`, `trade`, `decision`, `snapshot`, `cycle`, `error`
- **By Level**: Filter by log level

### Grouping (Optional)
- Group related entries (e.g., all entries from one cycle)
- Collapse/expand cycle groups
- Highlight cycle boundaries

---

## 🔧 Troubleshooting

### If logs show "N/A" or truncated messages:

1. **Check API Response**: Verify `/api/logs/activity` returns proper structure
2. **Check Timestamp Parsing**: Ensure timestamps are being extracted correctly
3. **Check Message Extraction**: Verify messages aren't being truncated
4. **Check Multi-line Handling**: Ensure continuation lines are being merged

### If logs are missing:

1. **Check Log Files**: Verify log files exist in `logs/` directory
2. **Check Filters**: Ensure filters aren't too restrictive
3. **Check Date Format**: Verify event day format matches `YYYY-MM-DD`

---

## ✅ Verification Checklist

- [ ] Logs display with proper timestamps
- [ ] Log levels are shown and color-coded
- [ ] Messages are complete (not truncated)
- [ ] Station codes are extracted and shown
- [ ] Event days are extracted and shown
- [ ] Action types are identified
- [ ] Filters work correctly
- [ ] No "N/A" entries appear
- [ ] No truncated file paths appear
- [ ] Multi-line messages are properly merged

---

**Last Updated**: November 17, 2025

