# Toggle System & Calibration Implementation Plan

**Date**: 2025-11-21  
**Purpose**: Plan backend and frontend changes for toggling venue/station rules and calibration  
**Priority**: **HIGH** - Enables feature testing and A/B comparison

---

## Overview

### Features to Toggle

1. **Polymarket Double Rounding**: Match Polymarket's exact rounding chain
2. **Station Calibration**: Apply station-specific calibration adjustments from ERA5 analysis

### Requirements

- Toggle on/off for each feature
- Updates apply to:
  - Live Dashboard (real-time)
  - Historical/Performance pages
  - Backtesting
- Calibration tool outputs per-station adjustment values

---

## Calibration Tool Output Format

### Option 1: Percentage Adjustment (Recommended)

**Format**: JSON file with per-station calibration percentages

```json
{
  "version": "1.0",
  "generated_date": "2025-11-21",
  "calibrations": {
    "EGLC": {
      "station_code": "EGLC",
      "station_name": "London City Airport",
      "calibration_pct": 2.5,
      "confidence": 0.95,
      "sample_size": 1825,
      "notes": "ERA5 grid point offset + terrain adjustment"
    },
    "KLGA": {
      "station_code": "KLGA",
      "station_name": "LaGuardia Airport",
      "calibration_pct": -1.2,
      "confidence": 0.92,
      "sample_size": 1825,
      "notes": "ERA5 grid point offset + terrain adjustment"
    }
  }
}
```

**Application**:
- `calibration_pct: 2.5` means multiply Zeus prediction by `1.025` (add 2.5%)
- `calibration_pct: -1.2` means multiply by `0.988` (subtract 1.2%)

**Pros**:
- Simple percentage-based adjustment
- Easy to understand and apply
- Works well for multiplicative corrections

**Cons**:
- Percentage might not be ideal for temperature (absolute offset might be better)

---

### Option 2: Absolute Temperature Offset (Alternative)

**Format**: JSON file with per-station offsets in Fahrenheit

```json
{
  "version": "1.0",
  "generated_date": "2025-11-21",
  "calibrations": {
    "EGLC": {
      "station_code": "EGLC",
      "calibration_offset_f": 0.5,
      "confidence": 0.95,
      "sample_size": 1825
    },
    "KLGA": {
      "station_code": "KLGA",
      "calibration_offset_f": -0.3,
      "confidence": 0.92,
      "sample_size": 1825
    }
  }
}
```

**Application**:
- `calibration_offset_f: 0.5` means add `0.5°F` to Zeus prediction
- `calibration_offset_f: -0.3` means subtract `0.3°F`

**Pros**:
- More intuitive for temperature (absolute degrees)
- Easier to reason about impact

**Cons**:
- Might not scale well if error varies with temperature

---

### Option 3: Hybrid (Percentage + Offset)

**Format**: Both percentage and offset

```json
{
  "calibrations": {
    "EGLC": {
      "calibration_pct": 1.5,
      "calibration_offset_f": 0.2,
      "application": "pct_then_offset"  // or "offset_then_pct"
    }
  }
}
```

**Application**:
- Apply percentage first, then offset: `(temp * 1.015) + 0.2`
- Or offset first, then percentage: `(temp + 0.2) * 1.015`

**Pros**:
- Most flexible
- Can handle both multiplicative and additive corrections

**Cons**:
- More complex
- Requires order specification

---

### Recommendation: **Option 1 (Percentage)**

**Rationale**:
- ERA5 grid point offsets are likely multiplicative (terrain effects scale with temperature)
- Simpler to implement and understand
- Easy to backtest and validate
- Can be converted to offset if needed: `offset = temp * (pct / 100)`

**File Location**: `data/calibration/station_calibrations.json`

---

## Stage-by-Stage Implementation Plan

### Stage 1: Backend - Configuration System

**Goal**: Create toggle configuration system

**Files to Create/Modify**:

1. **`core/feature_toggles.py`** (NEW)
   - Dataclass for feature toggles
   - Load/save toggle states
   - Default values

2. **`core/config.py`** (MODIFY)
   - Add feature toggles to Config class
   - Load toggles from config file

3. **`data/config/feature_toggles.json`** (NEW)
   - Store toggle states
   - Default: all off

**Implementation**:

```python
# core/feature_toggles.py
from dataclasses import dataclass
from typing import Optional
import json
from pathlib import Path

@dataclass
class FeatureToggles:
    """Feature toggle configuration."""
    polymarket_double_rounding: bool = False
    station_calibration: bool = False
    
    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "FeatureToggles":
        """Load toggles from JSON file."""
        if config_path is None:
            config_path = Path("data/config/feature_toggles.json")
        
        if not config_path.exists():
            # Create default
            toggles = cls()
            toggles.save(config_path)
            return toggles
        
        with open(config_path) as f:
            data = json.load(f)
        
        return cls(**data)
    
    def save(self, config_path: Optional[Path] = None) -> None:
        """Save toggles to JSON file."""
        if config_path is None:
            config_path = Path("data/config/feature_toggles.json")
        
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, "w") as f:
            json.dump({
                "polymarket_double_rounding": self.polymarket_double_rounding,
                "station_calibration": self.station_calibration,
            }, f, indent=2)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "polymarket_double_rounding": self.polymarket_double_rounding,
            "station_calibration": self.station_calibration,
        }
```

**Default Config File**:
```json
{
  "polymarket_double_rounding": false,
  "station_calibration": false
}
```

**Time Estimate**: 2-3 hours

---

### Stage 2: Backend - Calibration System

**Goal**: Load and apply station calibrations

**Files to Create/Modify**:

1. **`core/station_calibration.py`** (NEW)
   - Load calibration data
   - Apply calibration to temperature predictions
   - Handle missing calibrations gracefully

2. **`data/calibration/station_calibrations.json`** (NEW)
   - Output from calibration tool
   - Per-station calibration percentages

**Implementation**:

```python
# core/station_calibration.py
from typing import Optional, Dict
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class StationCalibration:
    """Load and apply station-specific calibrations."""
    
    def __init__(self, calibration_path: Optional[Path] = None):
        if calibration_path is None:
            calibration_path = Path("data/calibration/station_calibrations.json")
        
        self.calibration_path = calibration_path
        self._calibrations: Dict[str, float] = {}
        self._load()
    
    def _load(self) -> None:
        """Load calibration data from JSON file."""
        if not self.calibration_path.exists():
            logger.warning(
                f"Calibration file not found: {self.calibration_path}. "
                "No calibrations will be applied."
            )
            return
        
        try:
            with open(self.calibration_path) as f:
                data = json.load(f)
            
            # Extract calibration percentages
            calibrations = data.get("calibrations", {})
            for station_code, calib_data in calibrations.items():
                if isinstance(calib_data, dict):
                    pct = calib_data.get("calibration_pct", 0.0)
                else:
                    # Backward compatibility: direct percentage value
                    pct = calib_data
                
                self._calibrations[station_code.upper()] = float(pct)
            
            logger.info(
                f"Loaded {len(self._calibrations)} station calibrations from "
                f"{self.calibration_path}"
            )
        except Exception as e:
            logger.error(f"Failed to load calibrations: {e}")
            self._calibrations = {}
    
    def get_calibration(self, station_code: str) -> float:
        """Get calibration percentage for a station.
        
        Args:
            station_code: Station code (e.g., "EGLC")
            
        Returns:
            Calibration percentage (0.0 if not found)
        """
        return self._calibrations.get(station_code.upper(), 0.0)
    
    def apply(self, temp_f: float, station_code: str) -> float:
        """Apply calibration to a temperature prediction.
        
        Args:
            temp_f: Temperature in Fahrenheit
            station_code: Station code
            
        Returns:
            Calibrated temperature in Fahrenheit
        """
        pct = self.get_calibration(station_code)
        if pct == 0.0:
            return temp_f
        
        # Apply percentage: multiply by (1 + pct/100)
        multiplier = 1.0 + (pct / 100.0)
        calibrated = temp_f * multiplier
        
        logger.debug(
            f"Applied calibration to {station_code}: "
            f"{temp_f:.2f}°F * {multiplier:.4f} = {calibrated:.2f}°F "
            f"(calibration: {pct:+.2f}%)"
        )
        
        return calibrated
    
    def has_calibration(self, station_code: str) -> bool:
        """Check if calibration exists for a station."""
        return station_code.upper() in self._calibrations
```

**Calibration File Format**:
```json
{
  "version": "1.0",
  "generated_date": "2025-11-21",
  "calibrations": {
    "EGLC": {
      "station_code": "EGLC",
      "calibration_pct": 2.5,
      "confidence": 0.95,
      "sample_size": 1825
    },
    "KLGA": {
      "station_code": "KLGA",
      "calibration_pct": -1.2,
      "confidence": 0.92,
      "sample_size": 1825
    }
  }
}
```

**Time Estimate**: 2-3 hours

---

### Stage 3: Backend - Double Rounding Implementation

**Goal**: Implement Polymarket double rounding (from previous plan)

**Files to Modify**:

1. **`agents/prob_mapper.py`**
   - Add `match_polymarket_chain` parameter
   - Implement Celsius → Round whole → Fahrenheit → Round whole

2. **`agents/dynamic_trader/dynamic_engine.py`**
   - Pass toggle state to `map_daily_high()`
   - Check `FeatureToggles.polymarket_double_rounding`

**Implementation**:

```python
# agents/prob_mapper.py
def _compute_daily_high_mean(
    self, 
    forecast: ZeusForecast,
    match_polymarket_chain: bool = False,
) -> float:
    """Compute daily high mean, optionally matching Polymarket's rounding chain."""
    temps_k = [point.temp_K for point in forecast.timeseries]
    
    if match_polymarket_chain:
        # Match Polymarket: Kelvin → Celsius → Round whole → Fahrenheit → Round whole
        temps_f = []
        for temp_k in temps_k:
            temp_c = units.kelvin_to_celsius(temp_k)
            temp_c_whole = round(temp_c)  # Round to whole
            temp_f_precise = units.celsius_to_fahrenheit(temp_c_whole)
            temp_f_whole = round(temp_f_precise)  # Round to whole
            temps_f.append(temp_f_whole)
    else:
        temps_f = [units.kelvin_to_fahrenheit(t) for t in temps_k]
    
    return max(temps_f)

def map_daily_high(
    self,
    forecast: ZeusForecast,
    brackets: List[MarketBracket],
    station_code: str = None,
    venue: str = None,
    match_polymarket_chain: bool = False,  # NEW
) -> List[BracketProb]:
    # Apply Polymarket rounding if enabled
    match_polymarket = match_polymarket_chain and (venue == "polymarket")
    
    mu = self._compute_daily_high_mean(
        forecast, 
        match_polymarket_chain=match_polymarket
    )
    
    # mu is already whole number if matching Polymarket
    mu_for_prob = mu
    
    # Continue with probability calculation...
```

**Time Estimate**: 3-4 hours

---

### Stage 4: Backend - Integrate Toggles into Probability Calculation

**Goal**: Apply toggles in probability mapping

**Files to Modify**:

1. **`agents/prob_mapper.py`**
   - Accept `FeatureToggles` parameter
   - Apply calibration if enabled
   - Apply double rounding if enabled

2. **`agents/dynamic_trader/dynamic_engine.py`**
   - Load `FeatureToggles`
   - Pass to `map_daily_high()`
   - Apply calibration before probability calculation

**Implementation**:

```python
# agents/prob_mapper.py
from core.feature_toggles import FeatureToggles
from core.station_calibration import StationCalibration

class ProbMapper:
    def __init__(self):
        self.calibration = StationCalibration()
    
    def map_daily_high(
        self,
        forecast: ZeusForecast,
        brackets: List[MarketBracket],
        station_code: str = None,
        venue: str = None,
        feature_toggles: Optional[FeatureToggles] = None,  # NEW
    ) -> List[BracketProb]:
        if feature_toggles is None:
            feature_toggles = FeatureToggles()  # Default: all off
        
        # Step 1: Get raw daily high
        match_polymarket = (
            feature_toggles.polymarket_double_rounding 
            and venue == "polymarket"
        )
        
        mu = self._compute_daily_high_mean(
            forecast, 
            match_polymarket_chain=match_polymarket
        )
        
        # Step 2: Apply calibration if enabled
        if feature_toggles.station_calibration and station_code:
            mu = self.calibration.apply(mu, station_code)
            logger.debug(
                f"Applied station calibration to {station_code}: "
                f"daily high = {mu:.2f}°F"
            )
        
        # Step 3: Round to whole for Polymarket (if matching chain, already whole)
        if match_polymarket:
            mu_for_prob = mu  # Already whole
        elif venue == "polymarket":
            mu_for_prob = resolve_to_whole_f(mu)
        else:
            mu_for_prob = mu
        
        # Continue with probability calculation using mu_for_prob...
```

**Time Estimate**: 2-3 hours

---

### Stage 5: Backend - API Endpoints for Toggles

**Goal**: Expose toggle management via API

**Files to Create/Modify**:

1. **`backend/api/routes/features.py`** (NEW)
   - GET `/api/features/toggles` - Get current toggle states
   - PUT `/api/features/toggles` - Update toggle states
   - GET `/api/features/calibrations` - Get calibration data

2. **`backend/api/main.py`** (MODIFY)
   - Register features router

**Implementation**:

```python
# backend/api/routes/features.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.feature_toggles import FeatureToggles
from core.station_calibration import StationCalibration

router = APIRouter()

class ToggleUpdate(BaseModel):
    polymarket_double_rounding: bool = None
    station_calibration: bool = None

@router.get("/api/features/toggles")
def get_toggles():
    """Get current feature toggle states."""
    toggles = FeatureToggles.load()
    return toggles.to_dict()

@router.put("/api/features/toggles")
def update_toggles(update: ToggleUpdate):
    """Update feature toggle states."""
    toggles = FeatureToggles.load()
    
    if update.polymarket_double_rounding is not None:
        toggles.polymarket_double_rounding = update.polymarket_double_rounding
    
    if update.station_calibration is not None:
        toggles.station_calibration = update.station_calibration
    
    toggles.save()
    
    return {
        "status": "updated",
        "toggles": toggles.to_dict()
    }

@router.get("/api/features/calibrations")
def get_calibrations():
    """Get station calibration data."""
    calibration = StationCalibration()
    
    calibrations = {}
    # Load and return calibration data
    # ...
    
    return {
        "calibrations": calibrations,
        "enabled": FeatureToggles.load().station_calibration
    }
```

**Time Estimate**: 2-3 hours

---

### Stage 6: Backend - Update Comparison Endpoints

**Goal**: Pass toggles to comparison endpoints

**Files to Modify**:

1. **`backend/api/services/metar_service.py`**
   - Accept `feature_toggles` parameter
   - Apply toggles in `compare_zeus_vs_metar()`

2. **`backend/api/routes/compare.py`**
   - Load toggles and pass to service

**Implementation**:

```python
# backend/api/services/metar_service.py
def compare_zeus_vs_metar(
    self,
    station_code: str,
    event_day: Optional[date] = None,
    feature_toggles: Optional[FeatureToggles] = None,  # NEW
) -> Optional[Dict[str, Any]]:
    if feature_toggles is None:
        feature_toggles = FeatureToggles.load()
    
    # Get Zeus daily high
    zeus_high = ...  # Get from snapshot
    
    # Apply calibration if enabled
    if feature_toggles.station_calibration:
        calibration = StationCalibration()
        zeus_high = calibration.apply(zeus_high, station_code)
    
    # Apply double rounding if enabled
    if feature_toggles.polymarket_double_rounding:
        # Apply Polymarket rounding chain
        # ...
    
    # Continue with comparison...
```

**Time Estimate**: 2-3 hours

---

### Stage 7: Backend - Update Backtester

**Goal**: Apply toggles in backtesting

**Files to Modify**:

1. **`agents/backtester.py`**
   - Load `FeatureToggles`
   - Pass to probability calculation
   - Apply calibration and double rounding

**Implementation**:

```python
# agents/backtester.py
from core.feature_toggles import FeatureToggles

class Backtester:
    def __init__(self, feature_toggles: Optional[FeatureToggles] = None):
        self.feature_toggles = feature_toggles or FeatureToggles.load()
        self.prob_mapper = ProbMapper()
    
    def run_backtest(self, ...):
        # Use self.feature_toggles in probability calculations
        probs = self.prob_mapper.map_daily_high(
            forecast,
            brackets,
            station_code=station_code,
            venue=venue,
            feature_toggles=self.feature_toggles,
        )
        # ...
```

**Time Estimate**: 2-3 hours

---

### Stage 8: Frontend - Toggle UI Components

**Goal**: Create toggle controls

**Files to Create**:

1. **`frontend/src/components/FeatureToggles.tsx`** (NEW)
   - Toggle switches for each feature
   - Save/load toggle states
   - Visual feedback

**Implementation**:

```typescript
// frontend/src/components/FeatureToggles.tsx
import { useState, useEffect } from 'react';
import { Switch } from '@/components/ui/switch';

interface FeatureToggles {
  polymarket_double_rounding: boolean;
  station_calibration: boolean;
}

export function FeatureToggles() {
  const [toggles, setToggles] = useState<FeatureToggles>({
    polymarket_double_rounding: false,
    station_calibration: false,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchToggles();
  }, []);

  const fetchToggles = async () => {
    const res = await fetch('/api/features/toggles');
    const data = await res.json();
    setToggles(data);
    setLoading(false);
  };

  const updateToggle = async (key: keyof FeatureToggles, value: boolean) => {
    const newToggles = { ...toggles, [key]: value };
    setToggles(newToggles);

    await fetch('/api/features/toggles', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ [key]: value }),
    });

    // Trigger data refresh
    window.dispatchEvent(new CustomEvent('toggles-updated'));
  };

  return (
    <div className="feature-toggles">
      <h3>Feature Toggles</h3>
      <div className="toggle-item">
        <label>Polymarket Double Rounding</label>
        <Switch
          checked={toggles.polymarket_double_rounding}
          onCheckedChange={(checked) =>
            updateToggle('polymarket_double_rounding', checked)
          }
        />
      </div>
      <div className="toggle-item">
        <label>Station Calibration</label>
        <Switch
          checked={toggles.station_calibration}
          onCheckedChange={(checked) =>
            updateToggle('station_calibration', checked)
          }
        />
      </div>
    </div>
  );
}
```

**Time Estimate**: 3-4 hours

---

### Stage 9: Frontend - Live Dashboard Integration

**Goal**: Update live dashboard when toggles change

**Files to Modify**:

1. **`frontend/src/pages/LiveDashboard.tsx`**
   - Listen for toggle updates
   - Refetch data when toggles change
   - Pass toggles to API calls

**Implementation**:

```typescript
// frontend/src/pages/LiveDashboard.tsx
useEffect(() => {
  const handleToggleUpdate = () => {
    // Refetch all data with new toggles
    refetchZeus();
    refetchMarket();
    refetchComparison();
  };

  window.addEventListener('toggles-updated', handleToggleUpdate);
  return () => window.removeEventListener('toggles-updated', handleToggleUpdate);
}, []);

// Pass toggles to API
const fetchComparison = async () => {
  const toggles = await fetch('/api/features/toggles').then(r => r.json());
  const res = await fetch(
    `/api/compare/zeus-vs-metar?station=${station}&date=${date}`,
    {
      headers: {
        'X-Feature-Toggles': JSON.stringify(toggles),
      },
    }
  );
  // ...
};
```

**Time Estimate**: 2-3 hours

---

### Stage 10: Frontend - Historical Pages Integration

**Goal**: Update historical pages when toggles change

**Files to Modify**:

1. **`frontend/src/pages/PerformanceAnalysis.tsx`**
   - Listen for toggle updates
   - Refetch data with new toggles
   - Update graphs and cards

**Implementation**:

Similar to Stage 9, but for historical data endpoints.

**Time Estimate**: 2-3 hours

---

### Stage 11: Frontend - Backtesting Integration

**Goal**: Apply toggles in backtesting UI

**Files to Modify**:

1. **`frontend/src/pages/Backtest.tsx`**
   - Include toggles in backtest parameters
   - Send toggles to backtest API
   - Display toggle states in results

**Implementation**:

```typescript
// frontend/src/pages/Backtest.tsx
const runBacktest = async () => {
  const toggles = await fetch('/api/features/toggles').then(r => r.json());
  
  const res = await fetch('/api/backtest/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      station: selectedStation,
      start_date: startDate,
      end_date: endDate,
      feature_toggles: toggles,  // Include toggles
    }),
  });
  // ...
};
```

**Time Estimate**: 2-3 hours

---

## Summary

### Backend Stages (Total: ~20-25 hours)

1. ✅ Configuration System (2-3h)
2. ✅ Calibration System (2-3h)
3. ✅ Double Rounding Implementation (3-4h)
4. ✅ Integrate Toggles (2-3h)
5. ✅ API Endpoints (2-3h)
6. ✅ Update Comparison Endpoints (2-3h)
7. ✅ Update Backtester (2-3h)

### Frontend Stages (Total: ~9-13 hours)

8. ✅ Toggle UI Components (3-4h)
9. ✅ Live Dashboard Integration (2-3h)
10. ✅ Historical Pages Integration (2-3h)
11. ✅ Backtesting Integration (2-3h)

### Calibration Tool Output Format

**Recommended**: Percentage-based adjustment

**File**: `data/calibration/station_calibrations.json`

**Format**:
```json
{
  "version": "1.0",
  "generated_date": "2025-11-21",
  "calibrations": {
    "EGLC": {
      "station_code": "EGLC",
      "calibration_pct": 2.5,
      "confidence": 0.95,
      "sample_size": 1825
    }
  }
}
```

**Application**: `calibrated_temp = original_temp * (1 + calibration_pct / 100)`

---

## Testing Strategy

### Unit Tests

1. Test calibration application (positive, negative, zero)
2. Test double rounding chain
3. Test toggle loading/saving
4. Test probability calculation with toggles

### Integration Tests

1. Test API endpoints with toggles
2. Test backtester with toggles on/off
3. Test live dashboard data refresh

### Manual Testing

1. Toggle features on/off, verify data updates
2. Compare results with/without toggles
3. Verify calibration file loading

---

**Status**: 📋 **Implementation Plan Complete** - Ready for staged implementation

