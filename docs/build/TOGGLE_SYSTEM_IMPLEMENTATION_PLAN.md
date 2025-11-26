# Station Calibration Toggle System - Implementation Plan

**Date**: 2025-11-21  
**Updated**: 2025-01-XX  
**Purpose**: Plan backend and frontend changes for toggling station calibration on/off  
**Priority**: **HIGH** - Enables feature testing and A/B comparison

---

## Overview

### Feature to Toggle

**Station Calibration**: Apply station-specific bias corrections from ERA5 analysis
- Uses month/hour-specific bias matrix (12×24)
- Includes elevation offset correction
- Applied to Zeus temperature predictions before probability calculation

### Requirements

- Toggle on/off for station calibration
- Updates apply to:
  - Live Dashboard (real-time)
  - Historical/Performance pages
  - Backtesting
- Calibration data loaded from separate tool output files

---

## Calibration Tool Output Format

### File Structure

**Location**: `output/station_calibration_{STATION_ID}.json`

**Available Files**:
- `output/station_calibration_EGLC.json` - London City Airport
- `output/station_calibration_KLGA.json` - LaGuardia Airport

### JSON Schema

```json
{
  "station": "EGLC",
  "version": "2025.1",
  "bias_model": {
    "monthly_bias": [0.9968, 1.0126, ..., 1.4029],      // 12 values (Jan-Dec)
    "hourly_bias": [1.5683, 1.5125, ..., 0.5331],       // 24 values (0-23 hours)
    "bias_matrix_raw": [                                // 12×24 matrix
      [0.87, 0.92, ..., 1.40],                          // January (24 hours)
      [0.88, 0.93, ..., 1.41],                          // February (24 hours)
      // ... 10 more months
    ],
    "bias_matrix_smoothed": [                           // 12×24 matrix (RECOMMENDED)
      [0.90, 0.94, ..., 1.38],                          // January (24 hours)
      [0.91, 0.95, ..., 1.39],                          // February (24 hours)
      // ... 10 more months
    ]
  },
  "elevation": {
    "station_elev_m": 6.0,
    "mean_era5_elev_m": 68.87,
    "elevation_offset_c": 0.4087
  }
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `station` | string | Station ID (e.g., "EGLC", "KLGA") |
| `version` | string | Model version (e.g., "2025.1") |
| `bias_model.monthly_bias` | array[12] | Median bias for each month (Jan=index 0, Dec=index 11) |
| `bias_model.hourly_bias` | array[24] | Median bias for each hour (0-23) |
| `bias_model.bias_matrix_raw` | array[12][24] | Raw bias matrix before smoothing |
| `bias_model.bias_matrix_smoothed` | array[12][24] | **RECOMMENDED:** Smoothed bias matrix |
| `elevation.station_elev_m` | float | Station elevation in meters |
| `elevation.mean_era5_elev_m` | float | Mean ERA5 grid point elevation in meters |
| `elevation.elevation_offset_c` | float | Temperature correction due to elevation difference (°C) |

### Application Method

**Total Correction = Bias + Elevation Offset**

1. Get bias from `bias_matrix_smoothed[month-1][hour]` (in °C)
2. Add `elevation_offset_c` (in °C)
3. Apply to Zeus temperature: `corrected_temp_c = zeus_temp_c + total_correction`
4. Convert to Fahrenheit for probability calculation

**Example**:
```python
# Zeus temp: 15.5°C, June 15 at 2 PM
month = 6  # June
hour = 14  # 2 PM

bias = bias_matrix_smoothed[5][14]  # 0-indexed: month-1, hour
elevation_offset = elevation['elevation_offset_c']
total_correction = bias + elevation_offset  # e.g., 0.5 + 0.4 = 0.9°C

corrected_temp_c = 15.5 + 0.9 = 16.4°C
```

**File Location**: `data/calibration/station_calibration_{STATION_ID}.json`

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

**Goal**: Load and apply station calibrations using bias matrix + elevation offset

**Files to Create/Modify**:

1. **`core/station_calibration.py`** (NEW)
   - Load calibration data from per-station JSON files
   - Apply bias matrix + elevation correction
   - Handle missing calibrations gracefully

2. **`data/calibration/`** (NEW DIRECTORY)
   - Copy calibration files from separate tool
   - `station_calibration_EGLC.json`
   - `station_calibration_KLGA.json`

**Implementation**:

```python
# core/station_calibration.py
from typing import Optional, Dict
from datetime import datetime
import json
from pathlib import Path
import logging

from .config import PROJECT_ROOT

logger = logging.getLogger(__name__)

class StationCalibration:
    """Load and apply station-specific bias corrections from ERA5 analysis."""
    
    def __init__(self, calibration_dir: Optional[Path] = None):
        if calibration_dir is None:
            calibration_dir = PROJECT_ROOT / "data" / "calibration"
        
        self.calibration_dir = calibration_dir
        self._models: Dict[str, dict] = {}
        self._load_all()
    
    def _load_all(self) -> None:
        """Load all calibration models from directory."""
        if not self.calibration_dir.exists():
            logger.warning(
                f"Calibration directory not found: {self.calibration_dir}. "
                "No calibrations will be applied."
            )
            return
        
        # Look for station_calibration_*.json files
        pattern = "station_calibration_*.json"
        calibration_files = list(self.calibration_dir.glob(pattern))
        
        for calib_file in calibration_files:
            try:
                with open(calib_file) as f:
                    model = json.load(f)
                
                station_code = model.get("station", "").upper()
                if station_code:
                    self._models[station_code] = model
                    logger.info(
                        f"Loaded calibration model for {station_code} "
                        f"(version {model.get('version', 'unknown')})"
                    )
            except Exception as e:
                logger.error(f"Failed to load calibration from {calib_file}: {e}")
        
        logger.info(f"Loaded {len(self._models)} station calibration models")
    
    def has_calibration(self, station_code: str) -> bool:
        """Check if calibration exists for a station."""
        return station_code.upper() in self._models
    
    def get_correction(
        self, 
        station_code: str, 
        month: int, 
        hour: int
    ) -> Optional[float]:
        """Get total correction (bias + elevation) for a station/month/hour.
        
        Args:
            station_code: Station code (e.g., "EGLC")
            month: Month (1-12, where 1=January)
            hour: Hour (0-23)
            
        Returns:
            Total correction in °C, or None if calibration not available
        """
        model = self._models.get(station_code.upper())
        if not model:
            return None
        
        try:
            # Get bias from smoothed matrix (recommended)
            bias_matrix = model["bias_model"]["bias_matrix_smoothed"]
            
            # Validate indices
            if not (1 <= month <= 12):
                logger.warning(f"Invalid month: {month}, must be 1-12")
                return None
            if not (0 <= hour <= 23):
                logger.warning(f"Invalid hour: {hour}, must be 0-23")
                return None
            
            # Get bias (month-1 because array is 0-indexed)
            bias = bias_matrix[month - 1][hour]
            
            # Get elevation offset
            elevation_offset = model["elevation"]["elevation_offset_c"]
            
            # Total correction
            total_correction = bias + elevation_offset
            
            return total_correction
            
        except (KeyError, IndexError) as e:
            logger.error(
                f"Error accessing calibration model for {station_code}: {e}"
            )
            return None
    
    def apply(
        self, 
        temp_c: float, 
        station_code: str, 
        timestamp: datetime
    ) -> float:
        """Apply calibration to a temperature prediction.
        
        Args:
            temp_c: Temperature in Celsius (from Zeus/ERA5)
            station_code: Station code
            timestamp: Datetime for month/hour lookup
            
        Returns:
            Corrected temperature in Celsius
        """
        if not self.has_calibration(station_code):
            return temp_c
        
        month = timestamp.month  # 1-12
        hour = timestamp.hour    # 0-23
        
        correction = self.get_correction(station_code, month, hour)
        if correction is None:
            return temp_c
        
        corrected_temp_c = temp_c + correction
        
        logger.debug(
            f"Applied calibration to {station_code}: "
            f"{temp_c:.2f}°C + {correction:.4f}°C = {corrected_temp_c:.2f}°C "
            f"(month={month}, hour={hour})"
        )
        
        return corrected_temp_c
    
    def apply_to_forecast_timeseries(
        self,
        temps_k: list[float],
        timestamps: list[datetime],
        station_code: str,
    ) -> list[float]:
        """Apply calibration to a list of temperatures with timestamps.
        
        Args:
            temps_k: List of temperatures in Kelvin
            timestamps: List of datetime objects (same length as temps_k)
            station_code: Station code
            
        Returns:
            List of corrected temperatures in Kelvin
        """
        from . import units
        
        if not self.has_calibration(station_code):
            return temps_k
        
        corrected_temps_k = []
        for temp_k, ts in zip(temps_k, timestamps):
            # Convert to Celsius
            temp_c = units.kelvin_to_celsius(temp_k)
            
            # Apply correction
            corrected_temp_c = self.apply(temp_c, station_code, ts)
            
            # Convert back to Kelvin
            corrected_temp_k = units.celsius_to_kelvin(corrected_temp_c)
            corrected_temps_k.append(corrected_temp_k)
        
        return corrected_temps_k
```

**Calibration File Location**:
```
data/calibration/station_calibration_EGLC.json
data/calibration/station_calibration_KLGA.json
```

**Time Estimate**: 3-4 hours

---

### Stage 3: Backend - Integrate Calibration into Probability Calculation

**Goal**: Apply calibration to Zeus forecasts before probability calculation

**Files to Modify**:

1. **`agents/prob_mapper.py`**
   - Accept `FeatureToggles` parameter
   - Apply calibration to forecast timeseries before computing daily high
   - Use `StationCalibration.apply_to_forecast_timeseries()`

2. **`agents/dynamic_trader/dynamic_engine.py`**
   - Load `FeatureToggles`
   - Pass to `map_daily_high()`
   - Apply calibration if enabled

**Implementation**:

```python
# agents/prob_mapper.py
from core.feature_toggles import FeatureToggles
from core.station_calibration import StationCalibration

class ProbabilityMapper:
    def __init__(
        self,
        sigma_default: float = 2.0,
        sigma_min: float = 0.5,
        sigma_max: float = 10.0,
    ):
        """Initialize probability mapper."""
        self.sigma_default = sigma_default
        self.sigma_min = sigma_min
        self.sigma_max = sigma_max
        self.calibration = StationCalibration()  # NEW
    
    def _compute_daily_high_mean(
        self, 
        forecast: ZeusForecast,
        station_code: str = None,
        feature_toggles: Optional[FeatureToggles] = None,  # NEW
    ) -> float:
        """Compute daily high mean, optionally applying calibration."""
        if not forecast.timeseries:
            raise ValueError("Forecast has no timeseries data")
        
        # Extract temperatures and timestamps
        temps_k = [point.temp_K for point in forecast.timeseries]
        timestamps = [point.time_utc for point in forecast.timeseries]
        
        # Apply calibration if enabled
        if feature_toggles and feature_toggles.station_calibration:
            if station_code:
                temps_k = self.calibration.apply_to_forecast_timeseries(
                    temps_k, timestamps, station_code
                )
                logger.debug(
                    f"Applied station calibration to {station_code} forecast"
                )
        
        # Convert to Fahrenheit
        temps_f = [units.kelvin_to_fahrenheit(t) for t in temps_k]
        
        # Daily high is the maximum
        mu = max(temps_f)
        
        logger.debug(
            f"Computed daily high μ = {mu:.2f}°F from {len(temps_f)} hourly forecasts"
        )
        
        return mu
    
    def map_daily_high(
        self,
        forecast: ZeusForecast,
        brackets: List[MarketBracket],
        station_code: str = None,
        venue: str = None,
        feature_toggles: Optional[FeatureToggles] = None,  # NEW
    ) -> List[BracketProb]:
        """Map daily high forecast to bracket probabilities."""
        if feature_toggles is None:
            feature_toggles = FeatureToggles()  # Default: all off
        
        # ✅ STEP 1: Apply calibration to timeseries, then compute daily high
        mu = self._compute_daily_high_mean(
            forecast,
            station_code=station_code,
            feature_toggles=feature_toggles,
        )
        
        # ✅ STEP 2: Compute spread (σ) using SAME calibrated temperatures
        sigma = self._estimate_sigma(
            forecast,
            mu,
            station_code=station_code,
            feature_toggles=feature_toggles,
        )
        
        # ✅ STEP 3: Compute bracket probabilities using calibrated μ and σ
        # (bracket probability calculation, etc.)
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
   - GET `/api/features/calibrations` - Get calibration status

2. **`backend/api/main.py`** (MODIFY)
   - Register features router

**Implementation**:

```python
# backend/api/routes/features.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from core.feature_toggles import FeatureToggles
from core.station_calibration import StationCalibration

router = APIRouter()

class ToggleUpdate(BaseModel):
    station_calibration: Optional[bool] = None

@router.get("/api/features/toggles")
def get_toggles():
    """Get current feature toggle states."""
    toggles = FeatureToggles.load()
    return toggles.to_dict()

@router.put("/api/features/toggles")
def update_toggles(update: ToggleUpdate):
    """Update feature toggle states."""
    toggles = FeatureToggles.load()
    
    if update.station_calibration is not None:
        toggles.station_calibration = update.station_calibration
    
    toggles.save()
    
    return {
        "status": "updated",
        "toggles": toggles.to_dict()
    }

@router.get("/api/features/calibrations")
def get_calibrations():
    """Get station calibration status."""
    calibration = StationCalibration()
    toggles = FeatureToggles.load()
    
    # Get list of stations with calibrations
    stations_with_cal = []
    for station_code in ["EGLC", "KLGA"]:  # Add more as needed
        if calibration.has_calibration(station_code):
            stations_with_cal.append(station_code)
    
    return {
        "enabled": toggles.station_calibration,
        "stations_with_calibration": stations_with_cal,
        "total_calibrations": len(stations_with_cal),
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
   - Apply calibration if enabled

**Implementation**:

```python
# agents/backtester.py
from core.feature_toggles import FeatureToggles

class Backtester:
    def __init__(
        self,
        bankroll_usd: float = 10000.0,
        edge_min: float = 0.05,
        fee_bp: int = 50,
        slippage_bp: int = 30,
        feature_toggles: Optional[FeatureToggles] = None,  # NEW
    ):
        """Initialize backtester."""
        self.bankroll_usd = bankroll_usd
        self.edge_min = edge_min
        self.fee_bp = fee_bp
        self.slippage_bp = slippage_bp
        self.feature_toggles = feature_toggles or FeatureToggles.load()  # NEW
        
        # Initialize components
        self.prob_mapper = ProbabilityMapper()
        # ... other components ...
    
    def _backtest_single_day(self, event_day: date, station_code: str):
        # ... fetch forecast ...
        
        # Use feature_toggles in probability calculations
        probs = self.prob_mapper.map_daily_high(
            forecast=forecast,
            brackets=brackets,
            station_code=station_code,
            venue="polymarket",
            feature_toggles=self.feature_toggles,  # NEW
        )
        # ... continue with backtest ...
```

**Time Estimate**: 2-3 hours

---

### Stage 8: Frontend - Toggle UI Components

**Goal**: Create toggle control for station calibration

**Files to Create**:

1. **`frontend/src/components/FeatureToggles.tsx`** (NEW)
   - Toggle switch for station calibration
   - Save/load toggle states
   - Visual feedback and status indicators

**Implementation**:

```typescript
// frontend/src/components/FeatureToggles.tsx
import { useState, useEffect } from 'react';
import { Switch } from '@/components/ui/switch';
import { InfoIcon } from 'lucide-react';

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

  useEffect(() => {
    fetchToggles();
    fetchCalibrationStatus();
  }, []);

  const fetchToggles = async () => {
    const res = await fetch('/api/features/toggles');
    const data = await res.json();
    setToggles(data);
    setLoading(false);
  };

  const fetchCalibrationStatus = async () => {
    const res = await fetch('/api/features/calibrations');
    const data = await res.json();
    setCalibrationStatus(data);
  };

  const updateToggle = async (value: boolean) => {
    setToggles({ station_calibration: value });

    await fetch('/api/features/toggles', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ station_calibration: value }),
    });

    // Trigger data refresh
    window.dispatchEvent(new CustomEvent('toggles-updated'));
  };

  return (
    <div className="feature-toggles p-4 border rounded-lg">
      <h3 className="text-lg font-semibold mb-4">Feature Toggles</h3>
      
      <div className="toggle-item space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <label className="font-medium">Station Calibration</label>
            <InfoIcon 
              className="w-4 h-4 text-gray-400 cursor-help" 
              title="Applies ERA5 bias corrections to Zeus predictions based on month and hour"
            />
          </div>
          <Switch
            checked={toggles.station_calibration}
            onCheckedChange={updateToggle}
            disabled={loading}
          />
        </div>
        
        {calibrationStatus && (
          <div className="text-sm text-gray-600 ml-6">
            {calibrationStatus.total_calibrations > 0 ? (
              <span>
                {calibrationStatus.total_calibrations} station(s) calibrated: {' '}
                {calibrationStatus.stations_with_calibration.join(', ')}
              </span>
            ) : (
              <span className="text-amber-600">
                No calibration files found
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
```

**Time Estimate**: 2-3 hours

---

### Stage 9: Frontend - Live Dashboard Integration

**Goal**: Update live dashboard when calibration toggle changes

**Files to Modify**:

1. **`frontend/src/pages/LiveDashboard.tsx`**
   - Listen for toggle updates
   - Refetch data when toggles change
   - Show calibration status indicator

**Implementation**:

```typescript
// frontend/src/pages/LiveDashboard.tsx
import { useEffect, useState } from 'react';

export function LiveDashboard() {
  const [calibrationEnabled, setCalibrationEnabled] = useState(false);
  
  useEffect(() => {
    // Fetch initial toggle state
    fetch('/api/features/toggles')
      .then(r => r.json())
      .then(data => setCalibrationEnabled(data.station_calibration));
    
    // Listen for toggle updates
    const handleToggleUpdate = () => {
      // Refetch all data with new toggles
      refetchZeus();
      refetchMarket();
      refetchComparison();
      
      // Update local state
      fetch('/api/features/toggles')
        .then(r => r.json())
        .then(data => setCalibrationEnabled(data.station_calibration));
    };

    window.addEventListener('toggles-updated', handleToggleUpdate);
    return () => window.removeEventListener('toggles-updated', handleToggleUpdate);
  }, []);

  // API calls automatically use current toggle state (backend loads it)
  const fetchComparison = async () => {
    const res = await fetch(
      `/api/compare/zeus-vs-metar?station=${station}&date=${date}`
    );
    // Backend automatically applies calibration if toggle is on
    // ...
  };

  return (
    <div>
      {/* Show calibration status badge */}
      {calibrationEnabled && (
        <div className="badge badge-info">
          Calibration Enabled
        </div>
      )}
      {/* ... rest of dashboard ... */}
    </div>
  );
}
```

**Note**: Backend automatically loads toggles, so frontend doesn't need to pass them explicitly. Just refetch data when toggles change.

**Time Estimate**: 2-3 hours

---

### Stage 10: Frontend - Historical Pages Integration

**Goal**: Update historical pages when calibration toggle changes

**Files to Modify**:

1. **`frontend/src/pages/PerformanceAnalysis.tsx`**
   - Listen for toggle updates
   - Refetch data when toggles change
   - Update graphs and accuracy cards
   - Show calibration status

**Implementation**:

```typescript
// frontend/src/pages/PerformanceAnalysis.tsx
export function PerformanceAnalysis() {
  const [calibrationEnabled, setCalibrationEnabled] = useState(false);
  
  useEffect(() => {
    // Fetch initial toggle state
    fetch('/api/features/toggles')
      .then(r => r.json())
      .then(data => setCalibrationEnabled(data.station_calibration));
    
    // Listen for toggle updates
    const handleToggleUpdate = () => {
      // Refetch all historical data
      refetchZeusSnapshots();
      refetchMarketSnapshots();
      refetchComparison();
      
      // Update local state
      fetch('/api/features/toggles')
        .then(r => r.json())
        .then(data => setCalibrationEnabled(data.station_calibration));
    };

    window.addEventListener('toggles-updated', handleToggleUpdate);
    return () => window.removeEventListener('toggles-updated', handleToggleUpdate);
  }, []);

  return (
    <div>
      {/* Show calibration status */}
      {calibrationEnabled && (
        <div className="alert alert-info">
          <InfoIcon className="w-4 h-4" />
          <span>Station calibration is enabled. All Zeus predictions are corrected.</span>
        </div>
      )}
      {/* ... graphs and cards ... */}
    </div>
  );
}
```

**Time Estimate**: 2-3 hours

---

### Stage 11: Frontend - Backtesting Integration

**Goal**: Show calibration status in backtesting UI

**Files to Modify**:

1. **`frontend/src/pages/Backtest.tsx`**
   - Display current toggle state
   - Show calibration status in results
   - Note: Backend automatically uses current toggle state

**Implementation**:

```typescript
// frontend/src/pages/Backtest.tsx
export function Backtest() {
  const [calibrationEnabled, setCalibrationEnabled] = useState(false);
  
  useEffect(() => {
    fetch('/api/features/toggles')
      .then(r => r.json())
      .then(data => setCalibrationEnabled(data.station_calibration));
  }, []);

  const runBacktest = async () => {
    // Backend automatically uses current toggle state
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
    // ...
  };

  return (
    <div>
      {/* Show calibration status */}
      {calibrationEnabled && (
        <div className="alert alert-info mb-4">
          Station calibration is enabled for this backtest
        </div>
      )}
      {/* ... backtest form and results ... */}
    </div>
  );
}
```

**Time Estimate**: 1-2 hours

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

