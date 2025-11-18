# Station Venue Icons Implementation Guide

**Purpose**: Guide for implementing Polymarket and Kalshi SVG icons next to station names throughout the frontend  
**Date**: November 17, 2025

---

## 📋 Overview

You want to display venue icons (Polymarket and Kalshi SVG icons) next to station names in multiple locations:
1. Filters on live dashboard
2. Active filter label on live dashboard
3. Historical filters
4. Backtest station radio buttons
5. Active stations selector in config page

---

## 🔍 Current State Analysis

### Backend: Station Registry

**Location**: `core/registry.py`

The backend has a `StationRegistry` that loads stations from `data/registry/stations.csv`. Each station has:
- `station_code` (e.g., "EGLC", "KLGA")
- `city` (e.g., "London", "New York")
- `venue_hint` (e.g., "Polymarket London", "Kalshi NYC")

**Key Finding**: The `venue_hint` field contains venue information, but it's a descriptive string, not a normalized venue identifier.

### Frontend: Current State

**Question**: Does the frontend know which stations are from which platform?

**Answer**: **Not directly**. The frontend currently receives:
- Station codes (e.g., "EGLC", "KLGA")
- Station names/cities
- But **NOT** venue/platform information in API responses

---

## 🎯 Recommended Approach

### **Hybrid Approach: Backend + Frontend**

**Best Practice**: 
1. **Backend**: Expose venue/platform information in API responses
2. **Frontend**: Store SVG icons as assets and render them based on venue data

**Why This Approach?**
- ✅ **Separation of Concerns**: Backend provides data, frontend handles presentation
- ✅ **Single Source of Truth**: Venue mapping lives in backend (station registry)
- ✅ **Maintainability**: If venue assignments change, only backend needs updating
- ✅ **Performance**: Icons are static assets, no need to fetch from backend
- ✅ **Flexibility**: Frontend can cache venue mappings, handle edge cases

---

## 📐 Implementation Plan

### Phase 1: Backend Enhancement (Required)

#### 1.1 Create Stations API Endpoint

**File**: `backend/api/routes/stations.py` (NEW)

**Purpose**: Expose station list with venue information

**Implementation**:
```python
"""Station endpoints."""

from fastapi import APIRouter
from typing import List, Dict, Any
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from core.registry import StationRegistry

router = APIRouter()
registry = StationRegistry()


@router.get("/")
async def get_stations() -> Dict[str, Any]:
    """Get all stations with venue information.
    
    Returns:
        Dictionary with stations list, each containing:
        - station_code
        - city
        - station_name
        - venue: normalized venue identifier ('polymarket' or 'kalshi')
        - venue_hint: original venue hint string
    """
    stations = registry.list_all()
    
    # Normalize venue from venue_hint
    def normalize_venue(venue_hint: str) -> str:
        """Extract venue platform from venue_hint."""
        hint_lower = venue_hint.lower()
        if 'polymarket' in hint_lower:
            return 'polymarket'
        elif 'kalshi' in hint_lower:
            return 'kalshi'
        else:
            # Default fallback
            return 'polymarket'  # Most stations are Polymarket
    
    station_list = []
    for station in stations:
        venue = normalize_venue(station.venue_hint)
        station_list.append({
            "station_code": station.station_code,
            "city": station.city,
            "station_name": station.station_name,
            "venue": venue,
            "venue_hint": station.venue_hint,
            "timezone": station.time_zone,
        })
    
    return {
        "stations": station_list,
        "count": len(station_list),
    }


@router.get("/{station_code}")
async def get_station(station_code: str) -> Dict[str, Any]:
    """Get single station by code.
    
    Args:
        station_code: Station code (e.g., "EGLC")
    
    Returns:
        Station information with venue
    """
    station = registry.get(station_code.upper())
    
    if not station:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Station {station_code} not found")
    
    def normalize_venue(venue_hint: str) -> str:
        hint_lower = venue_hint.lower()
        if 'polymarket' in hint_lower:
            return 'polymarket'
        elif 'kalshi' in hint_lower:
            return 'kalshi'
        else:
            return 'polymarket'
    
    return {
        "station_code": station.station_code,
        "city": station.city,
        "station_name": station.station_name,
        "venue": normalize_venue(station.venue_hint),
        "venue_hint": station.venue_hint,
        "timezone": station.time_zone,
    }
```

#### 1.2 Register Stations Router

**File**: `backend/api/main.py`

**Add**:
```python
from .routes import status, snapshots, trades, logs, edges, metar, compare, websocket, backtest, engine, config, performance, stations

# ...

app.include_router(stations.router, prefix="/api/stations", tags=["stations"])
```

#### 1.3 Enhance Existing Endpoints (Optional but Recommended)

**Enhance endpoints that return station codes to also include venue information:**

**Example**: `backend/api/routes/status.py`

Add venue information to status response:
```python
# In get_status() method
from core.registry import StationRegistry

registry = StationRegistry()

# When building active_stations list:
active_stations = []
for station_code in active_stations_list:
    station = registry.get(station_code)
    if station:
        venue = normalize_venue(station.venue_hint)  # Use same function
        active_stations.append({
            "code": station_code,
            "venue": venue,
        })
```

**Note**: This is optional. The frontend can fetch station details separately if needed.

---

### Phase 2: Frontend Implementation

#### 2.1 Store SVG Icons

**Location**: `frontend/src/assets/icons/` (or similar)

**Files**:
- `polymarket-icon.svg`
- `kalshi-icon.svg`

**Structure**:
```
frontend/
  src/
    assets/
      icons/
        polymarket-icon.svg
        kalshi-icon.svg
```

#### 2.2 Create Venue Icon Component

**File**: `frontend/src/components/VenueIcon.tsx`

**Implementation**:
```typescript
import React from 'react';
import PolymarketIcon from '../assets/icons/polymarket-icon.svg';
import KalshiIcon from '../assets/icons/kalshi-icon.svg';

export type Venue = 'polymarket' | 'kalshi';

interface VenueIconProps {
  venue: Venue;
  size?: number; // Optional size in pixels
  className?: string;
}

export const VenueIcon: React.FC<VenueIconProps> = ({ 
  venue, 
  size = 20,
  className = '' 
}) => {
  const iconSrc = venue === 'polymarket' ? PolymarketIcon : KalshiIcon;
  
  return (
    <img 
      src={iconSrc} 
      alt={`${venue} icon`}
      width={size}
      height={size}
      className={`venue-icon venue-icon-${venue} ${className}`}
      style={{ display: 'inline-block', verticalAlign: 'middle' }}
    />
  );
};
```

#### 2.3 Create Station Display Component

**File**: `frontend/src/components/StationDisplay.tsx`

**Implementation**:
```typescript
import React from 'react';
import { VenueIcon, Venue } from './VenueIcon';

interface StationDisplayProps {
  stationCode: string;
  stationName?: string;
  venue: Venue;
  showIcon?: boolean;
  iconSize?: number;
  className?: string;
}

export const StationDisplay: React.FC<StationDisplayProps> = ({
  stationCode,
  stationName,
  venue,
  showIcon = true,
  iconSize = 20,
  className = '',
}) => {
  return (
    <span className={`station-display ${className}`}>
      {showIcon && (
        <VenueIcon venue={venue} size={iconSize} className="mr-2" />
      )}
      <span className="station-code">{stationCode}</span>
      {stationName && (
        <span className="station-name ml-1">({stationName})</span>
      )}
    </span>
  );
};
```

#### 2.4 Create Station/Venue Mapping Utility

**File**: `frontend/src/utils/stationUtils.ts`

**Implementation**:
```typescript
import { Venue } from '../components/VenueIcon';

export interface StationInfo {
  station_code: string;
  city: string;
  station_name: string;
  venue: Venue;
  venue_hint: string;
  timezone: string;
}

// Cache for station data
let stationCache: Map<string, StationInfo> | null = null;

/**
 * Fetch all stations from API and cache them
 */
export async function fetchStations(): Promise<StationInfo[]> {
  const response = await fetch('http://localhost:8000/api/stations');
  if (!response.ok) {
    throw new Error('Failed to fetch stations');
  }
  const data = await response.json();
  
  // Build cache
  stationCache = new Map();
  data.stations.forEach((station: StationInfo) => {
    stationCache!.set(station.station_code, station);
  });
  
  return data.stations;
}

/**
 * Get station info by code (uses cache if available)
 */
export async function getStationInfo(stationCode: string): Promise<StationInfo | null> {
  // If cache is empty, fetch stations first
  if (!stationCache) {
    await fetchStations();
  }
  
  return stationCache?.get(stationCode.toUpperCase()) || null;
}

/**
 * Get venue for a station code
 */
export async function getStationVenue(stationCode: string): Promise<Venue> {
  const station = await getStationInfo(stationCode);
  return station?.venue || 'polymarket'; // Default fallback
}

/**
 * Get all stations grouped by venue
 */
export async function getStationsByVenue(): Promise<Record<Venue, StationInfo[]>> {
  const stations = await fetchStations();
  
  const grouped: Record<Venue, StationInfo[]> = {
    polymarket: [],
    kalshi: [],
  };
  
  stations.forEach(station => {
    grouped[station.venue].push(station);
  });
  
  return grouped;
}
```

#### 2.5 Update Components to Use Icons

**Example 1: Live Dashboard Filters**

**File**: `frontend/src/components/LiveDashboard.tsx` (or similar)

```typescript
import React, { useState, useEffect } from 'react';
import { StationDisplay } from './StationDisplay';
import { fetchStations, StationInfo } from '../utils/stationUtils';

export const LiveDashboard: React.FC = () => {
  const [stations, setStations] = useState<StationInfo[]>([]);
  const [selectedStation, setSelectedStation] = useState<string | null>(null);

  useEffect(() => {
    loadStations();
  }, []);

  const loadStations = async () => {
    const stationList = await fetchStations();
    setStations(stationList);
  };

  return (
    <div>
      <select 
        value={selectedStation || ''} 
        onChange={(e) => setSelectedStation(e.target.value)}
      >
        <option value="">All Stations</option>
        {stations.map(station => (
          <option key={station.station_code} value={station.station_code}>
            {station.station_code} - {station.city}
          </option>
        ))}
      </select>

      {/* Display selected station with icon */}
      {selectedStation && (() => {
        const station = stations.find(s => s.station_code === selectedStation);
        return station ? (
          <StationDisplay
            stationCode={station.station_code}
            stationName={station.city}
            venue={station.venue}
          />
        ) : null;
      })()}
    </div>
  );
};
```

**Example 2: Config Page Station Selector**

```typescript
import React, { useState, useEffect } from 'react';
import { StationDisplay } from './StationDisplay';
import { fetchStations, StationInfo } from '../utils/stationUtils';

export const ConfigPage: React.FC = () => {
  const [stations, setStations] = useState<StationInfo[]>([]);
  const [selectedStations, setSelectedStations] = useState<string[]>([]);

  useEffect(() => {
    loadStations();
  }, []);

  const loadStations = async () => {
    const stationList = await fetchStations();
    setStations(stationList);
  };

  const toggleStation = (stationCode: string) => {
    setSelectedStations(prev => 
      prev.includes(stationCode)
        ? prev.filter(s => s !== stationCode)
        : [...prev, stationCode]
    );
  };

  return (
    <div>
      <h3>Active Stations</h3>
      {stations.map(station => (
        <label key={station.station_code} className="station-checkbox">
          <input
            type="checkbox"
            checked={selectedStations.includes(station.station_code)}
            onChange={() => toggleStation(station.station_code)}
          />
          <StationDisplay
            stationCode={station.station_code}
            stationName={station.city}
            venue={station.venue}
            iconSize={24}
          />
        </label>
      ))}
    </div>
  );
};
```

**Example 3: Backtest Station Radio Buttons**

```typescript
import React, { useState, useEffect } from 'react';
import { StationDisplay } from './StationDisplay';
import { fetchStations, StationInfo } from '../utils/stationUtils';

export const BacktestConfig: React.FC = () => {
  const [stations, setStations] = useState<StationInfo[]>([]);
  const [selectedStation, setSelectedStation] = useState<string>('');

  useEffect(() => {
    loadStations();
  }, []);

  const loadStations = async () => {
    const stationList = await fetchStations();
    setStations(stationList);
  };

  return (
    <div>
      <h3>Select Station</h3>
      {stations.map(station => (
        <label key={station.station_code} className="station-radio">
          <input
            type="radio"
            name="station"
            value={station.station_code}
            checked={selectedStation === station.station_code}
            onChange={(e) => setSelectedStation(e.target.value)}
          />
          <StationDisplay
            stationCode={station.station_code}
            stationName={station.city}
            venue={station.venue}
            iconSize={20}
          />
        </label>
      ))}
    </div>
  );
};
```

---

## 🎨 CSS Styling Recommendations

**File**: `frontend/src/styles/venue-icons.css` (or add to existing CSS)

```css
/* Venue Icon Base Styles */
.venue-icon {
  display: inline-block;
  vertical-align: middle;
  margin-right: 4px;
  flex-shrink: 0;
}

.venue-icon-polymarket {
  /* Polymarket-specific styles if needed */
}

.venue-icon-kalshi {
  /* Kalshi-specific styles if needed */
}

/* Station Display Component */
.station-display {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.station-code {
  font-weight: 600;
  font-family: monospace;
}

.station-name {
  color: #666;
  font-size: 0.9em;
}

/* Filter/Select Styling */
.station-checkbox,
.station-radio {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  cursor: pointer;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.station-checkbox:hover,
.station-radio:hover {
  background-color: #f5f5f5;
}

.station-checkbox input[type="checkbox"],
.station-radio input[type="radio"] {
  margin: 0;
  cursor: pointer;
}
```

---

## ✅ Implementation Checklist

### Backend
- [ ] Create `backend/api/routes/stations.py`
- [ ] Implement `normalize_venue()` function
- [ ] Register stations router in `main.py`
- [ ] Test `/api/stations` endpoint
- [ ] Test `/api/stations/{station_code}` endpoint
- [ ] Verify venue normalization works correctly

### Frontend
- [ ] Add SVG icon files to `src/assets/icons/`
- [ ] Create `VenueIcon` component
- [ ] Create `StationDisplay` component
- [ ] Create `stationUtils.ts` utility
- [ ] Update Live Dashboard filters
- [ ] Update Live Dashboard active filter label
- [ ] Update Historical filters
- [ ] Update Backtest station radio buttons
- [ ] Update Config page station selector
- [ ] Add CSS styling
- [ ] Test all locations display icons correctly

---

## 🔄 Alternative Approaches (Not Recommended)

### ❌ Option 1: Frontend-Only Mapping
**Why Not**: Requires maintaining duplicate mapping logic, harder to keep in sync with backend changes.

### ❌ Option 2: Backend Serves SVG Icons
**Why Not**: Unnecessary network overhead, icons are static assets that should be bundled.

### ❌ Option 3: Hardcode Venue Mapping in Frontend
**Why Not**: Violates single source of truth principle, requires frontend updates when stations change.

---

## 📝 Notes

### Venue Normalization Logic

The `normalize_venue()` function extracts venue from `venue_hint`:
- If `venue_hint` contains "polymarket" → `'polymarket'`
- If `venue_hint` contains "kalshi" → `'kalshi'`
- Default fallback → `'polymarket'`

**Example `venue_hint` values**:
- "Polymarket London" → `'polymarket'`
- "Kalshi NYC" → `'kalshi'`
- "Polymarket New York" → `'polymarket'`

### Caching Strategy

The frontend utility caches station data after first fetch to avoid repeated API calls. This is acceptable because:
- Station list changes infrequently
- Cache can be invalidated on page refresh
- For production, consider adding cache expiration or refresh mechanism

### Performance Considerations

- **Initial Load**: One API call to fetch all stations (acceptable)
- **Subsequent Renders**: Uses cached data (fast)
- **Icon Loading**: SVG files are small and can be inlined or bundled

---

## 🚀 Future Enhancements

1. **Icon Inlining**: Consider inlining SVG icons as React components for better performance
2. **Lazy Loading**: Load station data only when needed
3. **Error Handling**: Add fallback icons if venue is unknown
4. **Accessibility**: Add proper ARIA labels for screen readers
5. **Tooltips**: Show venue name on icon hover

---

**Total Estimated Time**: 4-6 hours
- Backend: 1-2 hours
- Frontend: 3-4 hours

**Priority**: Medium (UI enhancement, not critical functionality)

