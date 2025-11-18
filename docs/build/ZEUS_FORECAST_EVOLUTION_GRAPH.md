# Zeus Forecast Evolution Graph - Implementation Guide

**Date**: November 16, 2025  
**Purpose**: Guide for implementing the Zeus forecast evolution graph in the frontend  
**Focus**: Temperature forecast visualization only (no trading/edges logic)

---

## 🎯 What This Graph Shows

The **Zeus Forecast Evolution Graph** displays how Zeus weather predictions change over time for a specific day and station.

**Key Concept**: Zeus forecasts are **dynamic** - they update every 15 minutes. This graph shows:
- How the predicted daily high temperature **evolved** throughout the day
- Multiple forecast snapshots taken at different times
- Visual representation of forecast confidence/consistency

---

## 📊 Visual Design

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 🌡️  ZEUS FORECAST EVOLUTION                                                        │
│ London (EGLC) - Nov 16, 2025 (Today)                                               │
│ Market Status: ✅ OPEN                                                              │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│   Temperature (°F)                                                                  │
│   60°F┤                                                                              │
│       │                                                                              │
│   58°F┤                                                ━━━━━━━━━━━━━━━━ Latest (19:36)│
│       │                                            ━━━━━━━━━━━━━━━━━━━              │
│   56°F┤                                        ━━━━━━━━━━━━━━━━━━━━━━━              │
│       │                                    ━━━━━━━━━━━━━━━━━━━━━━━━━━━              │
│   54°F┤                                ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━              │
│       │                            ┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅ 15min ago (19:19)│
│   52°F┤                        ┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅│
│       │                    ┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅│
│   50°F┤                ┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅│
│       │            ················································· 30min ago (19:02)│
│   48°F┤        ···································································│
│       │    ·······································································│
│   46°F┤··········································································│
│       └─────────────────────────────────────────────────────────────────────────────│
│        00:00   04:00   08:00   12:00   16:00   20:00   24:00                      │
│                                                                                     │
│ Legend:                                                                            │
│ ━━━ Current Zeus (19:36) - Predicted High: 53.2°F                                 │
│ ┅┅┅ Zeus 15min ago (19:19) - Predicted High: 53.1°F                               │
│ ··· Zeus 30min ago (19:02) - Predicted High: 52.8°F                               │
│                                                                                     │
│ Daily High Predictions:                                                            │
│ • 19:36 → 53.2°F                                                                   │
│ • 19:19 → 53.1°F (+0.1°F)                                                         │
│ • 19:02 → 52.8°F (+0.3°F)                                                         │
│ • 18:46 → 52.5°F (+0.3°F)                                                         │
│ • 18:29 → 52.2°F (+0.3°F)                                                         │
│ • 18:26 → 52.0°F (+0.2°F)                                                         │
│ • 18:09 → 51.8°F (+0.2°F)                                                         │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

**Key Visual Elements:**
- **X-axis**: Time of day (00:00 to 24:00)
- **Y-axis**: Temperature in Fahrenheit
- **Multiple lines**: 
  - **Zeus Latest** (solid blue) = Most recent forecast snapshot
  - **Zeus Median** (dashed blue) = Median of all daily high predictions from all snapshots (more stable metric)
  - **METAR Actual** (orange with dots) = Actual observed temperatures
- **Line styles**: 
  - Solid line = Latest forecast
  - Dashed line = Median forecast (calculated from all snapshots)
  - Orange line with dots = METAR actual observations
- **Legend**: Shows fetch time and predicted daily high for each snapshot

---

## 🔌 API Endpoint

### Get Zeus Snapshots

```http
GET /api/snapshots/zeus?station_code={STATION}&event_day={DATE}&limit={LIMIT}
```

**Parameters:**
- `station_code` (required): Station code, e.g., `EGLC`, `KLGA`
- `event_day` (optional): Date in `YYYY-MM-DD` format, e.g., `2025-11-16`
- `limit` (optional): Maximum number of snapshots to return (default: 100)

**Example Request:**
```bash
curl "http://localhost:8000/api/snapshots/zeus?station_code=EGLC&event_day=2025-11-16"
```

**Response Structure:**
```json
{
  "snapshots": [
    {
      "fetch_time_utc": "2025-11-16T19:36:23.837352+00:00",
      "forecast_for_local_day": "2025-11-16",
      "start_local": "2025-11-16T00:00:00+00:00",
      "station_code": "EGLC",
      "city": "London",
      "timezone": "Europe/London",
      "model_mode": "spread",
      "timeseries_count": 24,
      "timeseries": [
        {
          "time_utc": "2025-11-16T00:00:00+00:00",
          "temp_K": 284.0225524902344
        },
        {
          "time_utc": "2025-11-16T01:00:00+00:00",
          "temp_K": 283.8130798339844
        },
        // ... 22 more hourly points
      ]
    },
    // ... more snapshots
  ],
  "count": 7
}
```

---

## 📐 Data Processing

### Step 1: Fetch Snapshots

```typescript
// Fetch all Zeus snapshots for the day
const response = await fetch(
  `http://localhost:8000/api/snapshots/zeus?station_code=EGLC&event_day=2025-11-16`
);
const data = await response.json();
const snapshots = data.snapshots; // Array of snapshot objects
```

### Step 2: Calculate Daily High for Each Snapshot

Each snapshot contains a `timeseries` array with 24 hourly temperature points (in Kelvin). You need to:

1. Convert Kelvin to Fahrenheit
2. Find the maximum temperature (daily high)
3. Store with the fetch time

```typescript
interface ProcessedSnapshot {
  fetchTime: Date;
  fetchTimeLocal: string; // For display
  predictedHighF: number;
  timeseries: Array<{
    time: Date;
    tempF: number;
  }>;
}

function processSnapshot(snapshot: any): ProcessedSnapshot {
  // Convert Kelvin to Fahrenheit and find max
  const tempsF = snapshot.timeseries.map((point: any) => {
    const tempC = point.temp_K - 273.15;
    const tempF = (tempC * 9/5) + 32;
    return {
      time: new Date(point.time_utc),
      tempF: tempF
    };
  });
  
  const predictedHighF = Math.max(...tempsF.map(t => t.tempF));
  
  return {
    fetchTime: new Date(snapshot.fetch_time_utc),
    fetchTimeLocal: formatTime(snapshot.fetch_time_utc),
    predictedHighF: predictedHighF,
    timeseries: tempsF
  };
}

// Process all snapshots
const processedSnapshots = snapshots.map(processSnapshot);

// Sort by fetch time (oldest first for plotting)
processedSnapshots.sort((a, b) => 
  a.fetchTime.getTime() - b.fetchTime.getTime()
);
```

### Step 3: Calculate Zeus Median

**Zeus Median** is the median of all daily high predictions from all snapshots. This provides a more stable metric than just the latest forecast.

```typescript
function calculateZeusMedian(processedSnapshots: ProcessedSnapshot[]): number {
  if (processedSnapshots.length === 0) return 0;
  
  // Get all daily highs
  const dailyHighs = processedSnapshots.map(s => s.predictedHighF);
  
  // Sort to find median
  dailyHighs.sort((a, b) => a - b);
  const mid = Math.floor(dailyHighs.length / 2);
  
  if (dailyHighs.length % 2 === 0) {
    // Even number of snapshots - average the two middle values
    return (dailyHighs[mid - 1] + dailyHighs[mid]) / 2;
  } else {
    // Odd number - return middle value
    return dailyHighs[mid];
  }
}
```

### Step 4: Prepare Data for Chart

For the evolution graph, you need to plot the **full 24-hour forecast** from the latest snapshot, plus the median temperature for each hour.

```typescript
interface ChartDataPoint {
  time: string; // "00:00", "01:00", etc.
  latest: number | null;      // Latest forecast temp
  median: number | null;      // Median forecast temp (from all snapshots)
  metar: number | null;       // METAR actual temp (if available)
}

function prepareChartData(
  processedSnapshots: ProcessedSnapshot[],
  metarObservations: any[]
): ChartDataPoint[] {
  if (processedSnapshots.length === 0) return [];
  
  // Get the latest snapshot
  const latest = processedSnapshots[processedSnapshots.length - 1];
  
  // Calculate median for each hour across all snapshots
  const medianTemps: number[] = [];
  for (let hour = 0; hour < 24; hour++) {
    const tempsAtHour = processedSnapshots
      .map(s => s.timeseries[hour]?.tempF)
      .filter(t => t !== null && t !== undefined) as number[];
    
    if (tempsAtHour.length > 0) {
      tempsAtHour.sort((a, b) => a - b);
      const mid = Math.floor(tempsAtHour.length / 2);
      const median = tempsAtHour.length % 2 === 0
        ? (tempsAtHour[mid - 1] + tempsAtHour[mid]) / 2
        : tempsAtHour[mid];
      medianTemps.push(median);
    } else {
      medianTemps.push(null as any);
    }
  }
  
  // Match METAR observations to hours
  const metarByHour: (number | null)[] = new Array(24).fill(null);
  metarObservations.forEach(obs => {
    const obsTime = new Date(obs.observation_time_utc);
    const hour = obsTime.getUTCHours();
    metarByHour[hour] = obs.temp_F;
  });
  
  // Create data points for each hour (00:00 to 23:00)
  const chartData: ChartDataPoint[] = [];
  
  for (let hour = 0; hour < 24; hour++) {
    const timeStr = `${String(hour).padStart(2, '0')}:00`;
    
    chartData.push({
      time: timeStr,
      latest: latest.timeseries[hour]?.tempF || null,
      median: medianTemps[hour] || null,
      metar: metarByHour[hour] || null,
    });
  }
  
  return chartData;
}
```

---

## 📈 Chart Implementation

### React + Recharts Example

```typescript
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts';

function ZeusForecastEvolutionGraph({ 
  stationCode, 
  eventDay 
}: { 
  stationCode: string; 
  eventDay: string;
}) {
  const [chartData, setChartData] = useState<ChartDataPoint[]>([]);
  const [snapshots, setSnapshots] = useState<ProcessedSnapshot[]>([]);
  
  useEffect(() => {
    async function fetchData() {
      const response = await fetch(
        `/api/snapshots/zeus?station_code=${stationCode}&event_day=${eventDay}`
      );
      const data = await response.json();
      const processed = data.snapshots.map(processSnapshot);
      processed.sort((a, b) => a.fetchTime.getTime() - b.fetchTime.getTime());
      setSnapshots(processed);
      setChartData(prepareChartData(processed));
    }
    
    fetchData();
    // Refresh every 15 minutes
    const interval = setInterval(fetchData, 15 * 60 * 1000);
    return () => clearInterval(interval);
  }, [stationCode, eventDay]);
  
  if (chartData.length === 0) {
    return <div>Loading forecast data...</div>;
  }
  
  return (
    <div className="zeus-forecast-graph">
      <h3>🌡️ Zeus Forecast Evolution</h3>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={chartData}>
          <XAxis 
            dataKey="time" 
            label={{ value: 'Time of Day', position: 'insideBottom', offset: -5 }}
          />
          <YAxis 
            label={{ value: 'Temperature (°F)', angle: -90, position: 'insideLeft' }}
            domain={['dataMin - 2', 'dataMax + 2']}
          />
          <Tooltip />
          <Legend />
          
          {/* Latest forecast - solid line */}
          <Line 
            type="monotone" 
            dataKey="latest" 
            stroke="#2563eb" 
            strokeWidth={2}
            name={`Zeus Latest (${formatTime(snapshots[snapshots.length - 1]?.fetchTime)})`}
            dot={false}
          />
          
          {/* Median forecast - dashed line */}
          <Line 
            type="monotone" 
            dataKey="median" 
            stroke="#2563eb" 
            strokeWidth={1}
            strokeDasharray="5 5"
            strokeOpacity={0.7}
            name="Zeus Median (all snapshots)"
            dot={false}
          />
          
          {/* METAR actual - orange line with dots */}
          <Line 
            type="monotone" 
            dataKey="metar" 
            stroke="#f97316" 
            strokeWidth={2}
            name="METAR Actual"
            dot={{ fill: "#f97316", r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
      
      {/* Daily High Predictions List */}
      <div className="daily-high-predictions">
        <h4>Daily High Predictions:</h4>
        <ul>
          {snapshots.slice().reverse().map((snapshot, idx) => {
            const prevHigh = idx < snapshots.length - 1 
              ? snapshots[snapshots.length - 2 - idx]?.predictedHighF 
              : null;
            const diff = prevHigh ? snapshot.predictedHighF - prevHigh : 0;
            const diffStr = diff > 0 ? `+${diff.toFixed(1)}°F` : `${diff.toFixed(1)}°F`;
            
            return (
              <li key={snapshot.fetchTime.getTime()}>
                {formatTime(snapshot.fetchTime)} → {snapshot.predictedHighF.toFixed(1)}°F
                {idx < snapshots.length - 1 && ` (${diffStr})`}
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}

function formatTime(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleTimeString('en-US', { 
    hour: '2-digit', 
    minute: '2-digit',
    hour12: false 
  });
}
```

### Streamlit + Plotly Example

```python
import streamlit as st
import plotly.graph_objects as go
import requests
from datetime import datetime

def fetch_zeus_snapshots(station_code: str, event_day: str):
    """Fetch Zeus snapshots from API."""
    url = f"http://localhost:8000/api/snapshots/zeus"
    params = {
        "station_code": station_code,
        "event_day": event_day
    }
    response = requests.get(url, params=params)
    return response.json()["snapshots"]

def process_snapshot(snapshot):
    """Process a single snapshot to extract temperatures."""
    timeseries = snapshot["timeseries"]
    temps_f = []
    times = []
    
    for point in timeseries:
        temp_k = point["temp_K"]
        temp_c = temp_k - 273.15
        temp_f = (temp_c * 9/5) + 32
        temps_f.append(temp_f)
        
        # Extract hour from time_utc
        time_str = point["time_utc"][11:16]  # "HH:MM"
        times.append(time_str)
    
    predicted_high = max(temps_f)
    fetch_time = snapshot["fetch_time_utc"]
    
    return {
        "fetch_time": fetch_time,
        "times": times,
        "temps_f": temps_f,
        "predicted_high": predicted_high
    }

def create_evolution_graph(station_code: str, event_day: str):
    """Create the Zeus forecast evolution graph."""
    snapshots = fetch_zeus_snapshots(station_code, event_day)
    
    if not snapshots:
        st.warning("No Zeus forecast data available for this day.")
        return
    
    # Process all snapshots
    processed = [process_snapshot(s) for s in snapshots]
    processed.sort(key=lambda x: x["fetch_time"])  # Oldest first
    
    # Create figure
    fig = go.Figure()
    
    # Calculate median for each hour across all snapshots
    import statistics
    median_temps = []
    for hour in range(24):
        temps_at_hour = [p["temps_f"][hour] for p in processed if hour < len(p["temps_f"])]
        if temps_at_hour:
            median_temps.append(statistics.median(temps_at_hour))
        else:
            median_temps.append(None)
    
    # Plot latest forecast (solid line)
    latest = processed[-1]
    fig.add_trace(go.Scatter(
        x=latest["times"],
        y=latest["temps_f"],
        mode='lines',
        name=f'Zeus Latest ({latest["fetch_time"][11:16]})',
        line=dict(color='#2563eb', width=2)
    ))
    
    # Plot median forecast (dashed line)
    fig.add_trace(go.Scatter(
        x=latest["times"],
        y=median_temps,
        mode='lines',
        name='Zeus Median (all snapshots)',
        line=dict(color='#2563eb', width=1, dash='dash', opacity=0.7)
    ))
    
    # Plot METAR actual (orange line with markers)
    metar_times = [obs["observation_time_utc"][11:16] for obs in metar_observations]
    metar_temps = [obs["temp_F"] for obs in metar_observations]
    fig.add_trace(go.Scatter(
        x=metar_times,
        y=metar_temps,
        mode='lines+markers',
        name='METAR Actual',
        line=dict(color='#f97316', width=2),
        marker=dict(size=6, color='#f97316')
    ))
    
    # Update layout
    fig.update_layout(
        title=f'🌡️ Zeus Forecast Evolution - {station_code} ({event_day})',
        xaxis_title='Time of Day',
        yaxis_title='Temperature (°F)',
        hovermode='x unified',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Daily High Predictions
    st.subheader("Daily High Predictions:")
    for i, snapshot in enumerate(reversed(processed)):
        prev_high = processed[len(processed) - 2 - i]["predicted_high"] if i < len(processed) - 1 else None
        diff = snapshot["predicted_high"] - prev_high if prev_high else 0
        diff_str = f"+{diff:.1f}°F" if diff > 0 else f"{diff:.1f}°F"
        
        st.write(
            f"• {snapshot['fetch_time'][11:16]} → "
            f"{snapshot['predicted_high']:.1f}°F"
            + (f" ({diff_str})" if prev_high else "")
        )

# Usage in Streamlit
station_code = st.selectbox("Station", ["EGLC", "KLGA"])
event_day = st.date_input("Event Day", value=datetime.now().date())

create_evolution_graph(station_code, event_day.isoformat())
```

---

## 🎨 Styling Guidelines

### Color Scheme
- **Latest forecast**: Solid blue (`#2563eb`)
- **15 min ago**: Dashed blue, 70% opacity
- **30+ min ago**: Dotted blue, 50% opacity
- **Background**: Light gray or white
- **Grid**: Light gray, subtle

### Line Styles
- **Latest**: `strokeWidth: 2`, solid
- **15 min ago**: `strokeWidth: 1`, dashed (`strokeDasharray: "5 5"`)
- **30+ min ago**: `strokeWidth: 1`, dotted (`strokeDasharray: "2 2"`)

### Temperature Range
- Auto-scale Y-axis based on data: `domain={['dataMin - 2', 'dataMax + 2']}`
- Or use a fixed range if you know the typical range for the station

---

## 🔄 Real-Time Updates

The graph should automatically refresh every 15 minutes to show new forecast snapshots:

```typescript
// Refresh every 15 minutes
useEffect(() => {
  fetchData();
  const interval = setInterval(fetchData, 15 * 60 * 1000);
  return () => clearInterval(interval);
}, [stationCode, eventDay]);
```

---

## 📋 Data Requirements

### Minimum Data Needed
- At least **1 snapshot** to show a basic forecast line
- **2+ snapshots** to show evolution (comparison)
- **3+ snapshots** to show multiple historical lines

### What to Show When No Data
```typescript
if (snapshots.length === 0) {
  return (
    <div className="no-data">
      <p>⚠️ No Zeus forecast data available for {stationCode} on {eventDay}</p>
      <p>Forecasts will appear when the trading engine collects data.</p>
    </div>
  );
}
```

---

## ✅ Testing Checklist

- [ ] Graph displays when snapshots are available
- [ ] Multiple forecast lines show correctly (latest, 15min, 30min)
- [ ] Temperature conversion (Kelvin → Fahrenheit) is correct
- [ ] Daily high calculation is accurate
- [ ] Time axis shows correct hours (00:00 to 23:00)
- [ ] Legend shows correct fetch times
- [ ] Daily high predictions list displays correctly
- [ ] Graph updates automatically every 15 minutes
- [ ] Handles empty data gracefully
- [ ] Handles single snapshot (no evolution to show)

---

## 🔍 Example API Response

Here's what a real API response looks like:

```json
{
  "snapshots": [
    {
      "fetch_time_utc": "2025-11-16T19:36:23.837352+00:00",
      "forecast_for_local_day": "2025-11-16",
      "station_code": "EGLC",
      "city": "London",
      "timeseries_count": 24,
      "timeseries": [
        {"time_utc": "2025-11-16T00:00:00+00:00", "temp_K": 284.02},
        {"time_utc": "2025-11-16T01:00:00+00:00", "temp_K": 283.81},
        // ... 22 more points
        {"time_utc": "2025-11-16T23:00:00+00:00", "temp_K": 285.12}
      ]
    }
  ],
  "count": 7
}
```

**Key Points:**
- `fetch_time_utc`: When this forecast was fetched (use for X-axis labels)
- `timeseries`: Array of 24 hourly temperature points
- `temp_K`: Temperature in Kelvin (convert to Fahrenheit)
- `time_utc`: UTC time for each hourly point

---

## 🎯 Summary

**What this graph shows:**
- **Zeus Latest**: Most recent forecast snapshot (solid blue line)
- **Zeus Median**: Median of all hourly temperatures across all snapshots (dashed blue line) - provides a more stable, consensus view
- **METAR Actual**: Real observed temperatures (orange line with dots)
- Daily high temperature predictions with change indicators

**Why Zeus Median?**
- More stable than just the latest forecast
- Shows consensus across all predictions for the day
- Less affected by individual forecast fluctuations
- Better representation of forecast confidence

**What this graph does NOT show:**
- Trading edges or decisions
- Market prices
- Trade placements
- P&L or performance

**This is purely a weather forecast visualization.**

---

**Ready to implement!** Use the API endpoint `/api/snapshots/zeus` and process the `timeseries` data to create the evolution graph.

