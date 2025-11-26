# Frontend Toggle System Implementation Guide

**Date**: 2025-11-21  
**Purpose**: Complete frontend implementation guide for station calibration toggle  
**Target**: Separate frontend project consuming backend API

---

## Overview

This guide covers the frontend implementation for the station calibration toggle system. The backend is complete and ready. The frontend needs to:

1. Create toggle UI components
2. Integrate with Live Dashboard
3. Integrate with Historical/Performance pages
4. Integrate with Backtesting UI

---

## API Endpoints Reference

### Get Toggle States
```
GET /api/features/toggles

Response:
{
  "station_calibration": false
}
```

### Update Toggle States
```
PUT /api/features/toggles

Request:
{
  "station_calibration": true
}

Response:
{
  "status": "updated",
  "toggles": {
    "station_calibration": true
  }
}
```

### Get Calibration Status
```
GET /api/features/calibrations

Response:
{
  "enabled": false,
  "stations_with_calibration": ["EGLC", "KLGA"],
  "total_calibrations": 2
}
```

---

## Stage 8: Toggle UI Components

### Component Structure

**File**: `src/components/FeatureToggles.tsx`

```typescript
import { useState, useEffect } from 'react';
import { Switch } from '@/components/ui/switch';
import { InfoIcon, CheckCircle2, AlertCircle } from 'lucide-react';

interface FeatureToggles {
  station_calibration: boolean;
}

interface CalibrationStatus {
  enabled: boolean;
  stations_with_calibration: string[];
  total_calibrations: number;
}

export function FeatureToggles() {
  const [toggles, setToggles] = useState<FeatureToggles>({
    station_calibration: false,
  });
  const [calibrationStatus, setCalibrationStatus] = useState<CalibrationStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchToggles();
    fetchCalibrationStatus();
  }, []);

  const fetchToggles = async () => {
    try {
      const res = await fetch('/api/features/toggles');
      if (!res.ok) throw new Error('Failed to fetch toggles');
      const data = await res.json();
      setToggles(data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching toggles:', error);
      setLoading(false);
    }
  };

  const fetchCalibrationStatus = async () => {
    try {
      const res = await fetch('/api/features/calibrations');
      if (!res.ok) throw new Error('Failed to fetch calibration status');
      const data = await res.json();
      setCalibrationStatus(data);
    } catch (error) {
      console.error('Error fetching calibration status:', error);
    }
  };

  const updateToggle = async (value: boolean) => {
    setSaving(true);
    try {
      const res = await fetch('/api/features/toggles', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ station_calibration: value }),
      });
      
      if (!res.ok) throw new Error('Failed to update toggle');
      
      const data = await res.json();
      setToggles(data.toggles);
      
      // Trigger data refresh event
      window.dispatchEvent(new CustomEvent('toggles-updated'));
      
      // Refresh calibration status
      await fetchCalibrationStatus();
    } catch (error) {
      console.error('Error updating toggle:', error);
      // Revert on error
      await fetchToggles();
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="feature-toggles p-4 border rounded-lg">
        <div className="animate-pulse">Loading...</div>
      </div>
    );
  }

  return (
    <div className="feature-toggles p-4 border rounded-lg bg-gray-50 dark:bg-gray-800">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        Feature Toggles
      </h3>
      
      <div className="space-y-4">
        {/* Station Calibration Toggle */}
        <div className="toggle-item space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <label className="font-medium cursor-pointer" htmlFor="calibration-toggle">
                Station Calibration
              </label>
              <InfoIcon 
                className="w-4 h-4 text-gray-400 cursor-help" 
                title="Applies ERA5 bias corrections to Zeus predictions based on month and hour. Improves accuracy by accounting for grid point offsets and terrain effects."
              />
            </div>
            <Switch
              id="calibration-toggle"
              checked={toggles.station_calibration}
              onCheckedChange={updateToggle}
              disabled={saving}
            />
          </div>
          
          {/* Calibration Status */}
          {calibrationStatus && (
            <div className="text-sm ml-6 space-y-1">
              {calibrationStatus.total_calibrations > 0 ? (
                <>
                  <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>
                      {calibrationStatus.total_calibrations} station(s) calibrated: {' '}
                      {calibrationStatus.stations_with_calibration.join(', ')}
                    </span>
                  </div>
                  {calibrationStatus.enabled && (
                    <div className="text-xs text-gray-600 dark:text-gray-400">
                      Calibration is active - all Zeus predictions are being corrected
                    </div>
                  )}
                </>
              ) : (
                <div className="flex items-center gap-2 text-amber-600 dark:text-amber-400">
                  <AlertCircle className="w-4 h-4" />
                  <span>No calibration files found</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
```

### Placement

**Recommended locations**:
1. **Settings/Configuration page** - Primary location
2. **Live Dashboard** - Quick access toggle (optional)
3. **Performance page** - Quick access toggle (optional)

---

## Stage 9: Live Dashboard Integration

### Update Live Dashboard Component

**File**: `src/pages/LiveDashboard.tsx` (or similar)

```typescript
import { useEffect, useState } from 'react';
import { FeatureToggles } from '@/components/FeatureToggles';

export function LiveDashboard() {
  const [calibrationEnabled, setCalibrationEnabled] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  
  useEffect(() => {
    // Fetch initial toggle state
    fetch('/api/features/toggles')
      .then(r => r.json())
      .then(data => setCalibrationEnabled(data.station_calibration))
      .catch(err => console.error('Error fetching toggles:', err));
    
    // Listen for toggle updates
    const handleToggleUpdate = () => {
      // Refetch toggle state
      fetch('/api/features/toggles')
        .then(r => r.json())
        .then(data => {
          setCalibrationEnabled(data.station_calibration);
          // Trigger data refresh by incrementing key
          setRefreshKey(prev => prev + 1);
        });
      
      // Refetch all data
      refetchZeus();
      refetchMarket();
      refetchComparison();
    };

    window.addEventListener('toggles-updated', handleToggleUpdate);
    return () => window.removeEventListener('toggles-updated', handleToggleUpdate);
  }, []);

  // Use refreshKey to force refetch when toggles change
  useEffect(() => {
    if (refreshKey > 0) {
      refetchZeus();
      refetchMarket();
      refetchComparison();
    }
  }, [refreshKey]);

  return (
    <div>
      {/* Optional: Show calibration status badge */}
      {calibrationEnabled && (
        <div className="mb-4 p-2 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
          <div className="flex items-center gap-2 text-sm text-blue-800 dark:text-blue-200">
            <InfoIcon className="w-4 h-4" />
            <span>
              Station calibration is enabled. All Zeus predictions are being corrected.
            </span>
          </div>
        </div>
      )}
      
      {/* Your existing dashboard content */}
      {/* Zeus forecast graph, market probabilities, etc. */}
    </div>
  );
}
```

### Data Fetching

**Important**: Backend automatically applies calibration based on current toggle state. Frontend doesn't need to pass toggles explicitly - just refetch data when toggles change.

```typescript
// Example: Fetching Zeus snapshots
const fetchZeusSnapshots = async () => {
  const res = await fetch(
    `/api/snapshots/zeus?station=${station}&date=${date}`
  );
  // Backend automatically uses current toggle state
  // If calibration is ON, snapshots will have corrected temperatures
  const data = await res.json();
  return data;
};

// Example: Fetching comparison data
const fetchComparison = async () => {
  const res = await fetch(
    `/api/compare/zeus-vs-metar?station=${station}&date=${date}`
  );
  // Backend automatically applies calibration if toggle is ON
  const data = await res.json();
  return data;
};
```

---

## Stage 10: Historical Pages Integration

### Update Performance Analysis Component

**File**: `src/pages/PerformanceAnalysis.tsx` (or similar)

```typescript
import { useEffect, useState } from 'react';
import { InfoIcon } from 'lucide-react';

export function PerformanceAnalysis() {
  const [calibrationEnabled, setCalibrationEnabled] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  
  useEffect(() => {
    // Fetch initial toggle state
    fetch('/api/features/toggles')
      .then(r => r.json())
      .then(data => setCalibrationEnabled(data.station_calibration))
      .catch(err => console.error('Error fetching toggles:', err));
    
    // Listen for toggle updates
    const handleToggleUpdate = () => {
      fetch('/api/features/toggles')
        .then(r => r.json())
        .then(data => {
          setCalibrationEnabled(data.station_calibration);
          setRefreshKey(prev => prev + 1);
        });
      
      // Refetch all historical data
      refetchZeusSnapshots();
      refetchMarketSnapshots();
      refetchComparison();
    };

    window.addEventListener('toggles-updated', handleToggleUpdate);
    return () => window.removeEventListener('toggles-updated', handleToggleUpdate);
  }, []);

  // Refetch when refreshKey changes
  useEffect(() => {
    if (refreshKey > 0) {
      refetchZeusSnapshots();
      refetchMarketSnapshots();
      refetchComparison();
    }
  }, [refreshKey]);

  return (
    <div>
      {/* Calibration Status Alert */}
      {calibrationEnabled && (
        <div className="mb-4 p-3 bg-info-50 dark:bg-info-900/20 border border-info-200 dark:border-info-800 rounded-lg">
          <div className="flex items-start gap-2 text-sm">
            <InfoIcon className="w-5 h-5 text-info-600 dark:text-info-400 mt-0.5" />
            <div>
              <div className="font-medium text-info-900 dark:text-info-100">
                Station Calibration Enabled
              </div>
              <div className="text-info-700 dark:text-info-300 mt-1">
                All Zeus predictions shown on this page are corrected using ERA5 bias models.
                This affects the accuracy card, forecast graphs, and all probability calculations.
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Your existing performance page content */}
      {/* Historical graphs, accuracy card, etc. */}
    </div>
  );
}
```

### Daily High Prediction Accuracy Card

**Update the accuracy card to show calibration status**:

```typescript
// In your accuracy card component
const AccuracyCard = ({ comparison, calibrationEnabled }) => {
  return (
    <div className="accuracy-card">
      <h4>Daily High Prediction Accuracy</h4>
      
      {calibrationEnabled && (
        <div className="text-xs text-gray-500 mb-2">
          * Using calibrated predictions
        </div>
      )}
      
      <div className="predicted-high">
        <span>Predicted High: {comparison.zeus_prediction_f}°F</span>
        {calibrationEnabled && (
          <span className="text-xs text-blue-600 ml-2">(calibrated)</span>
        )}
      </div>
      
      <div className="actual-high">
        Actual High: {comparison.metar_actual_f}°F
      </div>
      
      {/* Rest of card... */}
    </div>
  );
};
```

---

## Stage 11: Backtesting Integration

### Update Backtest Component

**File**: `src/pages/Backtest.tsx` (or similar)

```typescript
import { useEffect, useState } from 'react';
import { InfoIcon } from 'lucide-react';

export function Backtest() {
  const [calibrationEnabled, setCalibrationEnabled] = useState(false);
  
  useEffect(() => {
    // Fetch current toggle state
    fetch('/api/features/toggles')
      .then(r => r.json())
      .then(data => setCalibrationEnabled(data.station_calibration))
      .catch(err => console.error('Error fetching toggles:', err));
  }, []);

  const runBacktest = async () => {
    // Backend automatically uses current toggle state
    // No need to pass toggles explicitly
    const res = await fetch('/api/backtest/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        station: selectedStation,
        start_date: startDate,
        end_date: endDate,
        // Toggles are automatically loaded by backend
      }),
    });
    
    const data = await res.json();
    // Handle response...
  };

  return (
    <div>
      {/* Show calibration status */}
      {calibrationEnabled && (
        <div className="mb-4 p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
          <div className="flex items-start gap-2 text-sm">
            <InfoIcon className="w-5 h-5 text-amber-600 dark:text-amber-400 mt-0.5" />
            <div>
              <div className="font-medium text-amber-900 dark:text-amber-100">
                Station Calibration Enabled
              </div>
              <div className="text-amber-700 dark:text-amber-300 mt-1">
                This backtest will use calibrated Zeus predictions. 
                Results will reflect the impact of calibration on trading performance.
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Backtest form */}
      <form onSubmit={handleSubmit}>
        {/* Station, date range, etc. */}
        <button type="submit">Run Backtest</button>
      </form>
      
      {/* Backtest results */}
      {results && (
        <div className="results">
          {/* Show toggle state in results summary */}
          <div className="results-summary">
            <h3>Backtest Results</h3>
            {calibrationEnabled && (
              <div className="text-sm text-gray-600">
                Calibration: Enabled
              </div>
            )}
            {/* Rest of results... */}
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## Implementation Checklist

### Stage 8: Toggle UI Components
- [ ] Create `FeatureToggles.tsx` component
- [ ] Implement toggle switch for station calibration
- [ ] Fetch and display calibration status
- [ ] Handle toggle updates with API calls
- [ ] Dispatch `toggles-updated` event
- [ ] Add error handling and loading states
- [ ] Style component to match design system

### Stage 9: Live Dashboard Integration
- [ ] Add toggle state management to dashboard
- [ ] Listen for `toggles-updated` event
- [ ] Refetch data when toggles change
- [ ] Display calibration status badge/indicator
- [ ] Update Zeus forecast graph (automatic - backend handles it)
- [ ] Update daily high prediction (automatic - backend handles it)

### Stage 10: Historical Pages Integration
- [ ] Add toggle state management to performance page
- [ ] Listen for `toggles-updated` event
- [ ] Refetch historical data when toggles change
- [ ] Display calibration status alert
- [ ] Update accuracy card to show calibration status
- [ ] Update historical graphs (automatic - backend handles it)

### Stage 11: Backtesting Integration
- [ ] Add toggle state display to backtest page
- [ ] Show calibration status in backtest form
- [ ] Display calibration status in results summary
- [ ] Note: Backend automatically uses current toggle state

---

## Key Implementation Notes

### 1. Backend Handles Calibration Automatically

**Important**: The backend automatically applies calibration based on the current toggle state stored in `data/config/feature_toggles.json`. The frontend doesn't need to pass toggles to API endpoints - just refetch data when toggles change.

### 2. Event-Driven Updates

Use a custom event `toggles-updated` to notify all components when toggles change:

```typescript
// When toggle is updated
window.dispatchEvent(new CustomEvent('toggles-updated'));

// Components listen for updates
window.addEventListener('toggles-updated', handleUpdate);
```

### 3. Data Refresh Strategy

**Option A: Event-Based (Recommended)**
- Components listen for `toggles-updated` event
- Automatically refetch data when event fires
- Clean separation of concerns

**Option B: State Management**
- Use global state (Redux, Zustand, etc.)
- Update state when toggles change
- Components react to state changes

### 4. Visual Indicators

**When Calibration is Enabled**:
- Show badge/indicator on relevant pages
- Add tooltip explaining what calibration does
- Optionally show "calibrated" label next to predictions

**When Calibration is Disabled**:
- No special indicators needed
- Data shows raw Zeus predictions

### 5. Error Handling

```typescript
const updateToggle = async (value: boolean) => {
  try {
    // Optimistic update
    setToggles(prev => ({ ...prev, station_calibration: value }));
    
    const res = await fetch('/api/features/toggles', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ station_calibration: value }),
    });
    
    if (!res.ok) throw new Error('Update failed');
    
    // Confirm update
    const data = await res.json();
    setToggles(data.toggles);
    
    // Trigger refresh
    window.dispatchEvent(new CustomEvent('toggles-updated'));
  } catch (error) {
    // Revert on error
    await fetchToggles();
    showError('Failed to update toggle');
  }
};
```

---

## Testing Checklist

### Toggle Component
- [ ] Toggle switches correctly
- [ ] API calls succeed
- [ ] Error handling works
- [ ] Loading states display
- [ ] Calibration status displays correctly

### Live Dashboard
- [ ] Data refreshes when toggle changes
- [ ] Calibration status badge shows/hides
- [ ] Graphs update with calibrated data
- [ ] No duplicate API calls

### Historical Pages
- [ ] Data refreshes when toggle changes
- [ ] Accuracy card shows correct values
- [ ] Graphs update with calibrated data
- [ ] Calibration status alert displays

### Backtesting
- [ ] Calibration status shows in form
- [ ] Backtest uses current toggle state
- [ ] Results reflect calibration impact

---

## Example: Complete Integration

### App-Level Toggle State Management

```typescript
// src/contexts/ToggleContext.tsx
import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface ToggleContextType {
  toggles: { station_calibration: boolean };
  calibrationEnabled: boolean;
  refreshToggles: () => Promise<void>;
}

const ToggleContext = createContext<ToggleContextType | undefined>(undefined);

export function ToggleProvider({ children }: { children: ReactNode }) {
  const [toggles, setToggles] = useState({ station_calibration: false });
  
  const refreshToggles = async () => {
    const res = await fetch('/api/features/toggles');
    const data = await res.json();
    setToggles(data);
  };
  
  useEffect(() => {
    refreshToggles();
    
    const handleUpdate = () => refreshToggles();
    window.addEventListener('toggles-updated', handleUpdate);
    return () => window.removeEventListener('toggles-updated', handleUpdate);
  }, []);
  
  return (
    <ToggleContext.Provider value={{
      toggles,
      calibrationEnabled: toggles.station_calibration,
      refreshToggles,
    }}>
      {children}
    </ToggleContext.Provider>
  );
}

export function useToggles() {
  const context = useContext(ToggleContext);
  if (!context) throw new Error('useToggles must be used within ToggleProvider');
  return context;
}
```

### Usage in Components

```typescript
// In any component
import { useToggles } from '@/contexts/ToggleContext';

function MyComponent() {
  const { calibrationEnabled } = useToggles();
  
  return (
    <div>
      {calibrationEnabled && <Badge>Calibrated</Badge>}
      {/* Component content */}
    </div>
  );
}
```

---

## Summary

### What Frontend Needs to Do

1. **Create toggle UI** - Switch component to enable/disable calibration
2. **Listen for changes** - Refetch data when toggles update
3. **Show status** - Display calibration status on relevant pages
4. **Handle errors** - Graceful error handling and user feedback

### What Backend Handles Automatically

1. **Applies calibration** - All API endpoints use current toggle state
2. **No extra parameters** - Frontend doesn't need to pass toggles
3. **Consistent behavior** - Same toggle state used everywhere

### Key Files to Create/Modify

1. `src/components/FeatureToggles.tsx` - Toggle component
2. `src/pages/LiveDashboard.tsx` - Add toggle integration
3. `src/pages/PerformanceAnalysis.tsx` - Add toggle integration
4. `src/pages/Backtest.tsx` - Add toggle status display

---

**Status**: 📋 **Frontend Implementation Guide Complete** - Ready for frontend team


