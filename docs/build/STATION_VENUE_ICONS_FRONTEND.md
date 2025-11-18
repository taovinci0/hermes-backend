# Station Venue Icons - Frontend Implementation Guide

**Purpose**: Frontend implementation guide for displaying Polymarket and Kalshi SVG icons next to station names  
**Status**: Backend API complete - Ready for frontend implementation  
**Date**: November 17, 2025

---

## 📋 Overview

Add venue icons (Polymarket and Kalshi SVG icons) next to station names in these locations:
1. ✅ Filters on live dashboard
2. ✅ Active filter label on live dashboard
3. ✅ Historical filters
4. ✅ Backtest station radio buttons
5. ✅ Active stations selector in config page

---

## 🔌 Backend API (Already Complete)

### Endpoints Available

**Base URL**: `http://localhost:8000`

#### Get All Stations
```
GET /api/stations/
```

**Response**:
```json
{
  "stations": [
    {
      "station_code": "EGLC",
      "city": "London",
      "station_name": "London City Airport",
      "venue": "polymarket",
      "venue_hint": "Polymarket London",
      "timezone": "Europe/London"
    },
    {
      "station_code": "KNYC",
      "city": "New York (City)",
      "station_name": "Central Park",
      "venue": "kalshi",
      "venue_hint": "Kalshi NYC",
      "timezone": "America/New_York"
    },
    ...
  ],
  "count": 9
}
```

#### Get Single Station
```
GET /api/stations/{station_code}
```

**Example**: `GET /api/stations/EGLC`

**Response**:
```json
{
  "station_code": "EGLC",
  "city": "London",
  "station_name": "London City Airport",
  "venue": "polymarket",
  "venue_hint": "Polymarket London",
  "timezone": "Europe/London"
}
```

### Venue Values

- `"polymarket"` - For Polymarket stations (EGLC, KLGA)
- `"kalshi"` - For Kalshi stations (KNYC, KLAX, KMIA, KPHL, KAUS, KDEN, KMDW)

---

## 🎨 Frontend Implementation

### Step 1: Add SVG Icon Files

**Location**: `frontend/src/assets/icons/` (or your assets directory)

**Files Needed**:
- `polymarket-icon.svg` - Your Polymarket square icon SVG
- `kalshi-icon.svg` - Your Kalshi square icon SVG

**Directory Structure**:
```
frontend/
  src/
    assets/
      icons/
        polymarket-icon.svg
        kalshi-icon.svg
```

**Note**: Make sure the SVG files are square format as you mentioned.

---

### Step 2: Create Venue Icon Component

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

**Alternative (if using React SVG imports)**:
```typescript
import React from 'react';
import { ReactComponent as PolymarketIcon } from '../assets/icons/polymarket-icon.svg';
import { ReactComponent as KalshiIcon } from '../assets/icons/kalshi-icon.svg';

export type Venue = 'polymarket' | 'kalshi';

interface VenueIconProps {
  venue: Venue;
  size?: number;
  className?: string;
}

export const VenueIcon: React.FC<VenueIconProps> = ({ 
  venue, 
  size = 20,
  className = '' 
}) => {
  const IconComponent = venue === 'polymarket' ? PolymarketIcon : KalshiIcon;
  
  return (
    <IconComponent 
      width={size}
      height={size}
      className={`venue-icon venue-icon-${venue} ${className}`}
      style={{ display: 'inline-block', verticalAlign: 'middle' }}
    />
  );
};
```

---

### Step 3: Create Station Display Component

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

---

### Step 4: Create Station Utility Functions

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

const API_BASE = 'http://localhost:8000';

/**
 * Fetch all stations from API and cache them
 */
export async function fetchStations(): Promise<StationInfo[]> {
  const response = await fetch(`${API_BASE}/api/stations/`);
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

---

### Step 5: Update Components

#### 5.1 Live Dashboard Filters

**File**: `frontend/src/components/LiveDashboard.tsx` (or similar)

**Example Implementation**:
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
    try {
      const stationList = await fetchStations();
      setStations(stationList);
    } catch (err) {
      console.error('Failed to load stations:', err);
    }
  };

  return (
    <div>
      {/* Station Filter Dropdown */}
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

      {/* Active Filter Label with Icon */}
      {selectedStation && (() => {
        const station = stations.find(s => s.station_code === selectedStation);
        return station ? (
          <div className="active-filter">
            <span>Active Filter: </span>
            <StationDisplay
              stationCode={station.station_code}
              stationName={station.city}
              venue={station.venue}
              iconSize={20}
            />
          </div>
        ) : null;
      })()}
    </div>
  );
};
```

#### 5.2 Historical Filters

**File**: `frontend/src/components/HistoricalData.tsx` (or similar)

**Example Implementation**:
```typescript
import React, { useState, useEffect } from 'react';
import { StationDisplay } from './StationDisplay';
import { fetchStations, StationInfo } from '../utils/stationUtils';

export const HistoricalData: React.FC = () => {
  const [stations, setStations] = useState<StationInfo[]>([]);
  const [selectedStation, setSelectedStation] = useState<string>('');

  useEffect(() => {
    loadStations();
  }, []);

  const loadStations = async () => {
    try {
      const stationList = await fetchStations();
      setStations(stationList);
    } catch (err) {
      console.error('Failed to load stations:', err);
    }
  };

  return (
    <div>
      <label>Filter by Station:</label>
      <select 
        value={selectedStation} 
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

#### 5.3 Backtest Station Radio Buttons

**File**: `frontend/src/components/BacktestConfig.tsx` (or similar)

**Example Implementation**:
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
    try {
      const stationList = await fetchStations();
      setStations(stationList);
    } catch (err) {
      console.error('Failed to load stations:', err);
    }
  };

  return (
    <div>
      <h3>Select Station</h3>
      <div className="station-radio-group">
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
    </div>
  );
};
```

#### 5.4 Config Page Station Selector

**File**: `frontend/src/components/ConfigPage.tsx` (or similar)

**Example Implementation**:
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
    try {
      const stationList = await fetchStations();
      setStations(stationList);
    } catch (err) {
      console.error('Failed to load stations:', err);
    }
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
      <div className="station-checkbox-group">
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
    </div>
  );
};
```

---

### Step 6: Add CSS Styling

**File**: `frontend/src/styles/venue-icons.css` (or add to existing CSS file)

**Implementation**:
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

.station-checkbox-group,
.station-radio-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* Active Filter Label */
.active-filter {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background-color: #f0f0f0;
  border-radius: 4px;
}
```

---

## ✅ Implementation Checklist

### Setup
- [ ] Add `polymarket-icon.svg` to `src/assets/icons/`
- [ ] Add `kalshi-icon.svg` to `src/assets/icons/`
- [ ] Create `VenueIcon` component
- [ ] Create `StationDisplay` component
- [ ] Create `stationUtils.ts` utility file
- [ ] Add CSS styling

### Component Updates
- [ ] Update Live Dashboard filters
- [ ] Update Live Dashboard active filter label
- [ ] Update Historical filters
- [ ] Update Backtest station radio buttons
- [ ] Update Config page station selector

### Testing
- [ ] Test all 5 locations display icons correctly
- [ ] Test icon sizes are appropriate
- [ ] Test icons align properly with text
- [ ] Test on different screen sizes
- [ ] Verify correct venue icons show for each station

---

## 📝 Notes

### API Base URL

Update `API_BASE` in `stationUtils.ts` if your backend runs on a different URL:
```typescript
const API_BASE = 'http://localhost:8000'; // Change if needed
```

### Caching Strategy

The `stationUtils.ts` caches station data after first fetch. This is acceptable because:
- Station list changes infrequently
- Cache is cleared on page refresh
- For production, consider adding cache expiration

### Icon Sizing

Default icon size is `20px`. You can customize per location:
- Filters: `20px` (default)
- Config page: `24px` (larger for better visibility)
- Active filter label: `20px` (default)

### Error Handling

Add error handling for API failures:
```typescript
try {
  const stations = await fetchStations();
  setStations(stations);
} catch (err) {
  console.error('Failed to load stations:', err);
  // Show error message to user
  // Fallback to empty array or cached data
}
```

---

## 🚀 Quick Start

1. **Add SVG files** to `src/assets/icons/`
2. **Create components** (`VenueIcon.tsx`, `StationDisplay.tsx`)
3. **Create utility** (`stationUtils.ts`)
4. **Update one component** (e.g., Live Dashboard) to test
5. **Verify icons display** correctly
6. **Update remaining components** using the same pattern

---

## 📞 Support

If you encounter issues:
1. Verify backend API is running at `http://localhost:8000`
2. Check browser console for API errors
3. Verify SVG files are in correct location
4. Check that SVG imports are configured correctly in your build system

---

**Estimated Time**: 3-4 hours  
**Priority**: Medium (UI enhancement)

