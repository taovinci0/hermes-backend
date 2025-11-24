# METAR Data Format

**Date**: 2025-11-21  
**Purpose**: Document the format of METAR data from Aviation Weather Center API

---

## API Source

**Aviation Weather Center Data API**  
**URL**: `https://aviationweather.gov/api/data/metar`  
**Format**: JSON (we request `format=json`)

---

## Response Format

### Response Structure

The API returns either:
- **Array of observations**: `[{...}, {...}, ...]`
- **Single observation**: `{...}` (wrapped in array by our code)

### Example API Response

```json
[
  {
    "station": "EGLC",
    "icaoId": "EGLC",
    "time": "2025-11-16T15:50:00Z",
    "obsTime": "2025-11-16T15:50:00Z",
    "reportTime": "2025-11-16T15:50:00Z",
    "temp": 10.3,
    "dewpoint": 8.0,
    "dewp": 8.0,
    "windDir": 220,
    "wdir": 220,
    "windSpeed": 10,
    "wspd": 10,
    "altim": 30.05,
    "rawOb": "EGLC 161550Z 22010KT 9999 FEW020 10/08 Q1018",
    "name": "LONDON CITY AIRPORT",
    "lat": 51.505,
    "lon": 0.05,
    "elev": 19
  }
]
```

---

## Key Fields

### Temperature Data

| Field | Type | Units | Description | Example |
|-------|------|-------|-------------|---------|
| `temp` | `number` | **°C** | Air temperature in **Celsius** | `10.3` |

**Important Notes**:
- ✅ Temperature is in **Celsius**
- ✅ Temperature is **already rounded** to 1 decimal by NOAA/METAR API
- ✅ Example: `10.3°C` (not `10.34°C` or `10.256°C`)

### Station Identification

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `station` | `string` | ICAO station code | `"EGLC"` |
| `icaoId` | `string` | Alternative field name | `"EGLC"` |

**Our Code**: Uses `obs_data.get("station") or obs_data.get("icaoId", "")`

### Time Fields

| Field | Type | Format | Description |
|-------|------|--------|-------------|
| `time` | `string` | ISO8601 UTC | Observation timestamp |
| `obsTime` | `string` | ISO8601 UTC | Alternative field name |
| `reportTime` | `string` | ISO8601 UTC | Report timestamp |

**Our Code**: Uses `obs_data.get("time") or obs_data.get("obsTime")`

**Format**: `"2025-11-16T15:50:00Z"` (ISO8601 UTC)

### Optional Fields

| Field | Type | Units | Description |
|-------|------|-------|-------------|
| `dewpoint` / `dewp` | `number` | °C | Dew point temperature |
| `windDir` / `wdir` | `integer` | degrees | Wind direction |
| `windSpeed` / `wspd` | `integer` | knots | Wind speed |
| `rawOb` | `string` | — | Raw METAR text |
| `altim` | `number` | inHg | Altimeter setting |

---

## Our Processing

### Step 1: Parse from API Response

**File**: `venues/metar/metar_service.py` - `_parse_observation()`

```python
# Get temperature in Celsius (already rounded to 1 decimal by API)
temp_C = obs_data.get("temp")  # e.g., 10.3°C

# Convert to Fahrenheit and round to 1 decimal
temp_F = round((temp_C * 9 / 5) + 32, 1)  # e.g., 50.5°F
```

**Example**:
- API provides: `temp: 10.3` (Celsius, already rounded)
- We convert: `(10.3 * 9/5) + 32 = 50.54°F`
- We round: `round(50.54, 1) = 50.5°F`

### Step 2: Store in MetarObservation

```python
return MetarObservation(
    station_code=station,  # "EGLC"
    time=time_utc,  # datetime object
    temp_C=round(temp_C, 1),  # 10.3°C (already rounded, round again for consistency)
    temp_F=temp_F,  # 50.5°F (1 decimal)
    dewpoint_C=round(dewpoint_C, 1) if dewpoint_C else None,
    wind_dir=wind_dir,
    wind_speed=wind_speed,
    raw=raw,
)
```

### Step 3: Save to Snapshot

**File**: `agents/dynamic_trader/snapshotter.py` - `_save_metar()`

```python
snapshot_data = {
    "observation_time_utc": obs.time.isoformat(),  # "2025-11-16T15:50:00+00:00"
    "fetch_time_utc": datetime.now(ZoneInfo("UTC")).isoformat(),
    "station_code": obs.station_code,  # "EGLC"
    "event_day": event_day.isoformat(),  # "2025-11-16"
    "temp_C": obs.temp_C,  # 10.3
    "temp_F": obs.temp_F,  # 50.5
    "dewpoint_C": obs.dewpoint_C,
    "wind_dir": obs.wind_dir,
    "wind_speed": obs.wind_speed,
    "raw": obs.raw,
}
```

---

## Temperature Precision

### API Response

**Temperature in Celsius**: Already rounded to **1 decimal place**

**Examples**:
- `10.3°C` (not `10.34°C`)
- `15.0°C` (not `15.02°C`)
- `8.7°C` (not `8.73°C`)

**Source**: NOAA/METAR API rounds Celsius to 1 decimal before sending

---

### Our Conversion

**Step 1**: Get Celsius (already rounded)
```python
temp_C = 10.3  # From API, already rounded
```

**Step 2**: Convert to Fahrenheit
```python
temp_F_unrounded = (10.3 * 9 / 5) + 32  # 50.54°F (precise calculation)
```

**Step 3**: Round to 1 decimal
```python
temp_F = round(temp_F_unrounded, 1)  # 50.5°F (rounded to 1 decimal)
```

**Result**: Fahrenheit is also rounded to **1 decimal place**

---

## Rounding Chain for Polymarket

### METAR's Complete Process

1. **API provides**: `temp: 10.3°C` (already rounded to 1 decimal)
2. **We convert**: `(10.3 * 9/5) + 32 = 50.54°F` (precise calculation)
3. **We round**: `round(50.54, 1) = 50.5°F` (1 decimal)
4. **For Polymarket**: `resolve_to_whole_f(50.5) = 51°F` (whole degree)

**Complete Chain**: `Celsius (1 decimal) → Fahrenheit (1 decimal) → Whole degree`

---

## Comparison: METAR vs Zeus

### METAR Data Format

**Source**: Aviation Weather Center API  
**Temperature Unit**: Celsius  
**Precision**: 1 decimal (already rounded by API)  
**Example**: `10.3°C`

**Processing**:
1. Get `temp: 10.3°C` (already rounded)
2. Convert: `50.54°F` (precise)
3. Round: `50.5°F` (1 decimal)
4. For Polymarket: `51°F` (whole degree)

---

### Zeus Data Format

**Source**: Zeus API  
**Temperature Unit**: Kelvin  
**Precision**: Precise (not rounded)  
**Example**: `280.15K` (precise)

**Processing** (Current):
1. Get `temp_K: 280.15K` (precise)
2. Convert: `44.6°F` (precise)
3. For Polymarket: `45°F` (direct round to whole)

**Processing** (Proposed - Match METAR):
1. Get `temp_K: 280.15K` (precise)
2. Convert: `44.6°F` (precise)
3. Round: `44.6°F` (1 decimal) ← **Add this step**
4. For Polymarket: `45°F` (whole degree)

---

## Key Insight

**METAR**: 
- Celsius is **already rounded** (1 decimal) by the API
- We convert to Fahrenheit and round to 1 decimal
- Then round to whole degree for Polymarket

**Zeus**: 
- Kelvin is **precise** (not rounded)
- We convert to Fahrenheit (precise)
- **Should round to 1 decimal first** (matching METAR's intermediate step)
- Then round to whole degree for Polymarket

**Conclusion**: To match METAR's process, Zeus should include the intermediate 1-decimal rounding step.

---

## API Response Example (Full)

```json
[
  {
    "receiptTime": "2025-11-16T15:52:00Z",
    "obsTime": "2025-11-16T15:50:00Z",
    "reportTime": "2025-11-16T15:50:00Z",
    "temp": 10.3,
    "dewpoint": 8.0,
    "wdir": 220,
    "wspd": 10,
    "wgst": null,
    "visib": "9999",
    "altim": 30.05,
    "slp": null,
    "qc": "V",
    "wx": null,
    "skyc1": "FEW",
    "skylev1": 2000,
    "rawOb": "EGLC 161550Z 22010KT 9999 FEW020 10/08 Q1018",
    "name": "LONDON CITY AIRPORT",
    "icaoId": "EGLC",
    "lat": 51.505,
    "lon": 0.05,
    "elev": 19
  }
]
```

---

## Summary

### METAR Data Format

**Temperature**:
- **Unit**: Celsius (°C)
- **Precision**: 1 decimal (already rounded by API)
- **Example**: `10.3°C`

**Other Fields**:
- Station: `station` or `icaoId`
- Time: `time` or `obsTime` (ISO8601 UTC)
- Optional: `dewpoint`, `windDir`, `windSpeed`, `rawOb`, etc.

### Rounding Process

**METAR**: `Celsius (1 decimal) → Fahrenheit (1 decimal) → Whole degree`  
**Zeus (Current)**: `Kelvin (precise) → Fahrenheit (precise) → Whole degree`  
**Zeus (Proposed)**: `Kelvin (precise) → Fahrenheit (1 decimal) → Whole degree`

**Key Point**: METAR's Celsius is already rounded, so we only round Fahrenheit once (to 1 decimal), then once more (to whole degree) for Polymarket.

---

**Status**: ✅ **METAR Data Format Documented** - Temperature comes in Celsius, already rounded to 1 decimal

