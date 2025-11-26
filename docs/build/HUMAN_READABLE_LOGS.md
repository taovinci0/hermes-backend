# Human-Readable Activity Logs

## Overview

The activity log system now includes a human-readable formatting option that cleans up technical noise and presents key information in an easy-to-read format.

## What Changed

### Before
```
Parsed 24 forecast points for EGLC INFO     ✅ Zeus: 24 points for London      fetchers.py:72 (fetched: 15:28:52 UTC) INFO     Discovering Polymarket temp      discovery.py:301 brackets for London on 2025-11-19 INFO     Found event:                     discovery.py:146 highest-temperature-in-london-on -november-19 INFO     Found event                      discovery.py:336 'highest-temperature-in-london-o n-november-19' with 7 markets INFO     ✅ Parsed 5 temperature brackets discovery.py:350 for London, range: [36-45°F) ERROR    CLOB API HTTP error: 404 Client     pricing.py:71 Error: Not Found for url: https://clob.polymarket.com/midpoin t?token_id=649520291477950651481866 90682817925190135922458018657756615 912738153144609592
```

### After
```
🌡️  Zeus forecast: 24 data points for EGLC
💰 Found 5 temperature brackets
❌ API Error: Resource not found (404) (+3 more)
```

## Features

### 1. Removes Technical Noise
- **File paths**: Removes `fetchers.py:72`, `discovery.py:301`, etc.
- **Long URLs**: Replaces with `...`
- **File system paths**: Replaces `/Users/.../data/trades/...` with `trade file`
- **Duplicate prefixes**: Removes repeated `INFO`, `ERROR`, etc.

### 2. Extracts Key Information
The formatter intelligently extracts and formats:
- **Cycles**: `🔄 Cycle 32 started`
- **Zeus Forecasts**: `🌡️  Zeus forecast: 24 data points for EGLC`
- **Polymarket Data**: `💰 Found 5 temperature brackets`
- **METAR Observations**: `🌤️  Retrieved 1 METAR observation(s)`
- **Probabilities**: `🧮 Probabilities (Spread): Peak 43-44°F at 26.2%`
- **Edges**: `✅ Edge: 47-48°F → 16.63% ($300.00)`
- **Trades**: `📝 Placed 2 paper trade(s)`
- **Errors**: `❌ API Error: Resource not found (404)`

### 3. Multiple Events
When a log entry contains multiple events, it shows the most important one and indicates there are more:
- `📝 Placed 2 paper trade(s) (+6 more)`
- `❌ API Error: Resource not found (404) (+3 more)`

### 4. Priority Order
Events are prioritized by importance:
1. **Trades** (📝) - Most important
2. **Edges** (✅)
3. **Errors** (❌)
4. **Cycles** (🔄)
5. **Polymarket** (💰)
6. **Probabilities** (🧮)
7. **Zeus** (🌡️)
8. **METAR** (🌤️)
9. **Snapshots** (💾)
10. **Events** (🔍)

## API Usage

### Enable Human-Readable Formatting (Default)
```bash
curl "http://localhost:8000/api/logs/activity?station_code=EGLC&event_day=2025-11-19&human_readable=true"
```

### Disable Formatting (Raw Logs)
```bash
curl "http://localhost:8000/api/logs/activity?station_code=EGLC&event_day=2025-11-19&human_readable=false"
```

## Response Format

### Formatted Entry
```json
{
  "timestamp": "2025-11-18T23:52:54",
  "log_file": "dynamic_paper_20251118_222941.log",
  "level": "INFO",
  "message": "📝 Placed 2 paper trade(s) (+6 more)",
  "station_code": "EGLC",
  "event_day": "2025-11-19",
  "action_type": "trade",
  "message_formatted": true
}
```

### Unformatted Entry
```json
{
  "timestamp": "2025-11-18T23:52:54",
  "log_file": "dynamic_paper_20251118_222941.log",
  "level": "INFO",
  "message": "Retrieved 1 valid METAR observations for EGLC INFO     Mapping forecast for EGLC (24  prob_mapper.py:240 points) to 5 brackets...",
  "station_code": "EGLC",
  "event_day": "2025-11-19",
  "action_type": "trade",
  "message_formatted": false
}
```

## Frontend Integration

The frontend should:
1. **Default to human-readable**: Use `human_readable=true` by default
2. **Show formatted indicator**: Display `message_formatted: true` entries with a different style
3. **Allow toggle**: Provide option to switch between formatted and raw logs
4. **Display emojis**: Render emojis properly (they're Unicode characters)

## Example Messages

### Cycle Start
```
🔄 Cycle 32 started
```

### Zeus Forecast
```
🌡️  Zeus forecast: 24 data points for EGLC
```

### Polymarket Brackets
```
💰 Found 5 temperature brackets
```

### Probability Calculation
```
🧮 Probabilities (Spread): Peak 43-44°F at 26.2%
```

### Edge Found
```
✅ Edge: 47-48°F → 16.63% ($300.00)
```

### Trade Placement
```
📝 Placed 2 paper trade(s)
```

### Multiple Events
```
📝 Placed 2 paper trade(s) (+6 more)
```

### Error
```
❌ API Error: Resource not found (404)
```

## Implementation Details

### Log Service Methods

1. **`_format_message_for_humans(entry)`**
   - Removes technical noise (file paths, URLs, etc.)
   - Cleans up spacing and formatting
   - Calls `_extract_key_info()` to format message

2. **`_extract_key_info(message, entry)`**
   - Extracts key information from log message
   - Formats with appropriate emoji
   - Handles multiple events in one message
   - Returns formatted string or None

### Pattern Matching

The formatter uses regex patterns to extract:
- Cycle numbers: `CYCLE\s+(\d+)`
- Data points: `(\d+)\s+points?`
- Brackets: `(\d+)\s+temperature\s+brackets?`
- Edges: `\[(\d+)-(\d+)°F\)[^:]*edge[=:]\s*([\d.]+)`
- Trades: `(\d+)\s+paper\s+trades?`
- Errors: HTTP status codes (404, 401, etc.)

## Benefits

1. **Readability**: Much easier to scan and understand
2. **Focus**: Highlights important information (trades, edges, errors)
3. **Clean**: Removes technical noise that doesn't help users
4. **Flexible**: Can toggle between formatted and raw logs
5. **Informative**: Shows multiple events when present

## Future Enhancements

Potential improvements:
- **Grouping**: Group related log entries by cycle
- **Collapsible**: Allow expanding to see all events in a message
- **Timeline**: Show relative time between events
- **Filtering**: Filter by event type (only show trades, only show errors, etc.)
- **Search**: Search within formatted messages


