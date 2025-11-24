# Performance Page: Implementation Plan

**Purpose**: Staged implementation plan for the Performance page  
**Date**: November 18, 2025  
**Scope**: Overview, Historical, and Analytics views

**Note**: The Portfolio page already exists and is separate. This plan focuses only on the Performance page.

---

## 🎯 Overview

The Performance page consists of **three main views**:

1. **Overview** (Macro) - System-wide performance summary
2. **Historical** (Micro) - Day-by-day detailed analysis (partially implemented)
3. **Analytics** (Macro) - Specialized analysis dashboards

**⚠️ Important**: Both Zeus forecasts and Polymarket markets are **dynamic** - they change over time. The Performance page must analyze:
- **Forecast evolution**: How Zeus predictions change throughout the day
- **Market dynamics**: How Polymarket probabilities change over time
- **Optimal timing**: When to trade relative to forecast/market evolution
- **Post-trade analysis**: What happened after we traded

See `PERFORMANCE_PAGE_DYNAMIC_ANALYSIS.md` for detailed dynamic analysis requirements.

---

## 📋 Prerequisites

Before starting:
- ✅ Backend API is running (`http://localhost:8000`)
- ✅ Portfolio page exists (separate from Performance)
- ✅ Historical view partially implemented (three stacked graphs)
- ✅ Trade resolution service exists
- ✅ Performance and PnL services exist
- ✅ Frontend project is set up

---

## 🔧 Backend/API Implementation Stages

### Stage 1: Forecast Accuracy Service & Endpoints

**Goal**: Create service to calculate forecast accuracy metrics

**Estimated Time**: 4-5 hours

#### 1.1 Create Forecast Accuracy Service

**File**: `backend/api/services/forecast_accuracy_service.py`

**Implementation**:
```python
"""Service for calculating forecast accuracy metrics."""

from typing import List, Dict, Any, Optional
from datetime import date, datetime
from collections import defaultdict
import statistics
import math

from ..services.trade_service import TradeService
from ..utils.path_utils import get_snapshots_dir
from core.registry import StationRegistry

class ForecastAccuracyService:
    """Service for calculating forecast accuracy metrics."""
    
    def __init__(self):
        self.snapshots_dir = get_snapshots_dir()
        self.registry = StationRegistry()
    
    def get_accuracy_metrics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        station_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get forecast accuracy metrics.
        
        Calculates:
        - MAE (Mean Absolute Error)
        - RMSE (Root Mean Squared Error)
        - Mean Error (bias)
        - Correlation coefficient
        - Accuracy by forecast age
        - Accuracy by station
        """
        # Load Zeus snapshots
        zeus_snapshots = self._load_zeus_snapshots(
            start_date=start_date,
            end_date=end_date,
            station_code=station_code,
        )
        
        # Load METAR actuals
        metar_actuals = self._load_metar_actuals(
            start_date=start_date,
            end_date=end_date,
            station_code=station_code,
        )
        
        # Match predictions to actuals
        predictions = self._match_predictions_to_actuals(
            zeus_snapshots,
            metar_actuals,
        )
        
        if not predictions:
            return {
                "overall": {
                    "mae": 0.0,
                    "rmse": 0.0,
                    "mean_error": 0.0,
                    "correlation": 0.0,
                    "count": 0,
                },
                "by_station": {},
                "by_forecast_age": {},
                "predictions": [],
            }
        
        # Calculate overall metrics
        errors = [p["error_f"] for p in predictions]
        predicted = [p["predicted_high_f"] for p in predictions]
        actual = [p["actual_high_f"] for p in predictions]
        
        mae = statistics.mean([abs(e) for e in errors])
        rmse = math.sqrt(statistics.mean([e**2 for e in errors]))
        mean_error = statistics.mean(errors)
        
        # Correlation
        if len(predicted) > 1:
            correlation = self._calculate_correlation(predicted, actual)
        else:
            correlation = 0.0
        
        # By station
        by_station = self._calculate_by_station(predictions)
        
        # By forecast age
        by_forecast_age = self._calculate_by_forecast_age(predictions)
        
        return {
            "overall": {
                "mae": round(mae, 2),
                "rmse": round(rmse, 2),
                "mean_error": round(mean_error, 2),
                "correlation": round(correlation, 3),
                "count": len(predictions),
            },
            "by_station": by_station,
            "by_forecast_age": by_forecast_age,
            "predictions": predictions[:100],  # Limit for response size
        }
    
    def _load_zeus_snapshots(self, start_date, end_date, station_code):
        """Load Zeus snapshots from disk."""
        # Implementation: Load from data/snapshots/zeus/
        pass
    
    def _load_metar_actuals(self, start_date, end_date, station_code):
        """Load METAR actual daily highs from disk."""
        # Implementation: Load from data/snapshots/metar/
        # Calculate daily high for each day
        pass
    
    def _match_predictions_to_actuals(self, zeus_snapshots, metar_actuals):
        """Match Zeus predictions to METAR actuals."""
        # Match by date and station
        # Calculate forecast age (hours before event)
        pass
    
    def _calculate_correlation(self, x, y):
        """Calculate Pearson correlation coefficient."""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        # Implementation
        pass
    
    def _calculate_by_station(self, predictions):
        """Calculate accuracy metrics by station."""
        # Group by station, calculate metrics
        pass
    
    def _calculate_by_forecast_age(self, predictions):
        """Calculate accuracy metrics by forecast age."""
        # Group by forecast age buckets (0-6h, 6-12h, 12-24h, 24h+)
        pass
```

#### 1.2 Create Forecast Accuracy Endpoints

**File**: `backend/api/routes/forecast_accuracy.py`

**Implementation**:
```python
"""Forecast accuracy endpoints."""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import date

from ..services.forecast_accuracy_service import ForecastAccuracyService

router = APIRouter()
service = ForecastAccuracyService()

@router.get("/metrics")
async def get_accuracy_metrics(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    station_code: Optional[str] = Query(None, description="Station code filter"),
):
    """Get forecast accuracy metrics."""
    start_date_obj = None
    end_date_obj = None
    
    if start_date:
        try:
            start_date_obj = date.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format")
    
    if end_date:
        try:
            end_date_obj = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format")
    
    try:
        return service.get_accuracy_metrics(
            start_date=start_date_obj,
            end_date=end_date_obj,
            station_code=station_code,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate metrics: {str(e)}")
```

#### 1.3 Register Routes

**File**: `backend/api/main.py`

**Add**:
```python
from .routes import forecast_accuracy

app.include_router(forecast_accuracy.router, prefix="/api/forecast-accuracy", tags=["forecast-accuracy"])
```

**Testing**:
- Test with various date ranges
- Test with station filters
- Verify MAE, RMSE calculations
- Verify correlation calculation

---

### Stage 2: Timing Analysis Service & Endpoints

**Goal**: Create service to analyze trade timing and optimal entry windows

**Estimated Time**: 3-4 hours

#### 2.1 Create Timing Analysis Service

**File**: `backend/api/services/timing_analysis_service.py`

**Implementation**:
```python
"""Service for analyzing trade timing."""

from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
from collections import defaultdict
import statistics

from ..services.trade_service import TradeService
from ..models.schemas import Trade

class TimingAnalysisService:
    """Service for analyzing trade timing."""
    
    def __init__(self):
        self.trade_service = TradeService()
    
    def get_timing_analysis(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        station_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get timing analysis.
        
        Returns:
        - P&L by trade time (hours before event)
        - Win rate by market age
        - Edge decay over time
        - Optimal entry window
        """
        trades = self._get_trades_in_range(
            start_date=start_date,
            end_date=end_date,
            station_code=station_code,
        )
        
        # Calculate hours before event for each trade
        trades_with_timing = self._calculate_timing(trades)
        
        # P&L by trade time
        pnl_by_timing = self._calculate_pnl_by_timing(trades_with_timing)
        
        # Win rate by market age
        win_rate_by_age = self._calculate_win_rate_by_age(trades_with_timing)
        
        # Edge decay
        edge_decay = self._calculate_edge_decay(trades_with_timing)
        
        # Optimal entry window
        optimal_window = self._find_optimal_window(trades_with_timing)
        
        return {
            "pnl_by_timing": pnl_by_timing,
            "win_rate_by_age": win_rate_by_age,
            "edge_decay": edge_decay,
            "optimal_entry_window": optimal_window,
        }
    
    def _calculate_timing(self, trades):
        """Calculate hours before event for each trade."""
        # For each trade, calculate time difference between trade timestamp
        # and event day start (local midnight)
        pass
    
    def _calculate_pnl_by_timing(self, trades):
        """Calculate average P&L by time bucket."""
        # Group by time buckets: 0-12h, 12-24h, 24-36h, 36-48h, 48h+
        pass
    
    def _calculate_win_rate_by_age(self, trades):
        """Calculate win rate by market age."""
        pass
    
    def _calculate_edge_decay(self, trades):
        """Calculate how edges decay over time."""
        # Group by market age, calculate average edge
        pass
    
    def _find_optimal_window(self, trades):
        """Find optimal entry window based on P&L and win rate."""
        # Find time bucket with best combination of P&L and win rate
        pass
```

#### 2.2 Create Timing Analysis Endpoints

**File**: `backend/api/routes/timing_analysis.py`

**Implementation**: Similar to forecast_accuracy.py

**Register in main.py**

**Testing**: Verify timing calculations, edge decay analysis

---

### Stage 3: Enhanced Historical View Endpoints

**Goal**: Enhance existing Historical view with better data structure

**Estimated Time**: 2-3 hours

#### 3.1 Enhance Snapshot Endpoints

**File**: `backend/api/routes/snapshots.py`

**Add endpoints**:
- `/api/snapshots/zeus/{station_code}/{date}` - Get all snapshots for a day
- `/api/snapshots/polymarket/{station_code}/{date}` - Get all snapshots for a day
- `/api/snapshots/decisions/{station_code}/{date}` - Get all decisions for a day

**Enhancements**:
- Include actual daily high from METAR
- Include forecast accuracy for that day
- Include trade outcomes

#### 3.2 Create Historical Summary Endpoint

**File**: `backend/api/routes/performance.py` (new or existing)

**Endpoint**: `GET /api/performance/historical/{station_code}/{date}`

**Returns**:
- Summary metrics for that day
- Forecast accuracy
- Trade outcomes
- Key insights

**Testing**: Verify data structure matches frontend needs

---

### Stage 4: Dynamic Analysis Services (NEW - HIGH PRIORITY)

**Goal**: Create services for dynamic analysis of forecast and market evolution

**Estimated Time**: 8-10 hours

#### 4.1 Forecast Evolution Service

**File**: `backend/api/services/forecast_evolution_service.py`

**Features**:
- Forecast volatility (std dev of predictions over time)
- Forecast convergence (how confidence narrows)
- Forecast stability (consistency score)
- Forecast drift (total change from first to last)
- Post-trade forecast changes

**Metrics**:
- Volatility by forecast age
- Convergence rate
- Stability score
- Drift magnitude
- Last-minute changes

#### 4.2 Market Dynamics Service

**File**: `backend/api/services/market_dynamics_service.py`

**Features**:
- Market movement analysis (how probabilities change)
- Market efficiency (time to correction after trade)
- Price volatility (std dev of probabilities)
- Market convergence (movement toward outcome)
- Opportunity cost (best price vs. actual trade price)

**Metrics**:
- Price movement speed
- Correction time
- Volatility by market age
- Convergence rate
- Missed opportunities

#### 4.3 Dynamic Timing Service

**File**: `backend/api/services/dynamic_timing_service.py`

**Features**:
- Optimal entry window (forecast stable + market favorable)
- Forecast-Market correlation over time
- Convergence timing (when they align)
- Post-trade evolution analysis
- Trade timing score (how close to optimal)

**Metrics**:
- Optimal entry windows
- Correlation coefficients
- Convergence points
- Post-trade changes
- Timing performance

---

### Stage 5: Analytics Aggregation Services

**Goal**: Create services for Analytics sub-tabs

**Estimated Time**: 5-6 hours

#### 5.1 Risk Analysis Service

**File**: `backend/api/services/risk_analysis_service.py`

**Features**:
- Loss patterns analysis
- Large loss events
- Forecast error vs. Loss correlation
- Edge vs. Outcome analysis
- **Dynamic risk factors** (forecast volatility, market volatility)

#### 5.2 Bracket Analysis Service

**File**: `backend/api/services/bracket_analysis_service.py`

**Features**:
- P&L by bracket
- Win rate by bracket
- Edge by bracket
- Bracket frequency analysis

#### 5.3 Strategy Optimization Service

**File**: `backend/api/services/strategy_optimization_service.py`

**Features**:
- Parameter sensitivity analysis
- Model comparison (spread vs. bands)
- Backtest vs. Paper comparison

#### 5.4 Create Analytics Endpoints

**File**: `backend/api/routes/analytics.py`

**Endpoints**:
- `GET /api/analytics/forecast-evolution` (NEW)
- `GET /api/analytics/market-dynamics` (NEW)
- `GET /api/analytics/dynamic-timing` (NEW)
- `GET /api/analytics/risk`
- `GET /api/analytics/brackets`
- `GET /api/analytics/strategy`

**Testing**: Verify all analytics calculations, including dynamic metrics

---

### Stage 6: Export Functionality

**Goal**: Add export endpoints for LLM analysis

**Estimated Time**: 3-4 hours

#### 5.1 Create Export Service

**File**: `backend/api/services/export_service.py`

**Formats**:
- JSON (structured)
- CSV (tabular)
- Markdown (report)
- Text (prompt-ready)

#### 5.2 Create Export Endpoints

**File**: `backend/api/routes/export.py`

**Endpoint**: `GET /api/performance/export`

**Query params**:
- `format`: json | csv | markdown | text
- `start_date`, `end_date`
- `stations`: comma-separated
- `include`: comma-separated (forecast_accuracy, trading_performance, etc.)

**Testing**: Verify all export formats

---

## 🎨 Frontend Implementation Stages

### Stage 1: Navigation & Page Structure

**Goal**: Set up Performance page navigation and structure

**Estimated Time**: 2-3 hours

#### 1.1 Update Main Navigation

**File**: `frontend/src/components/Navigation.tsx` (or similar)

**Changes**:
- Add "Performance" dropdown to main nav
- Dropdown items: Overview, Historical, Analytics

#### 1.2 Create Performance Page Layout

**File**: `frontend/src/pages/Performance/PerformancePage.tsx`

**Structure**:
- Main container
- Tab navigation (Overview, Historical, Analytics)
- Content area (changes based on active tab)

#### 1.3 Create Route Structure

**File**: `frontend/src/App.tsx` (or router config)

**Routes**:
- `/performance/overview`
- `/performance/historical`
- `/performance/analytics`

**Testing**: Verify navigation works, routes load correctly

---

### Stage 2: Overview Page (Macro)

**Goal**: Implement Overview page with system-wide metrics

**Estimated Time**: 6-8 hours

#### 2.1 Summary Cards Component

**File**: `frontend/src/pages/Performance/Overview/SummaryCards.tsx`

**Features**:
- Forecast Accuracy card (MAE, RMSE, Correlation)
- Trading Performance card (P&L, Risk, ROI)
- Win Rate card
- ROI card

**Data Source**: `/api/performance/metrics`, `/api/forecast-accuracy/metrics`

#### 2.2 Station Comparison Chart

**File**: `frontend/src/pages/Performance/Overview/StationComparison.tsx`

**Features**:
- Bar chart showing ROI by station
- Clickable stations (navigate to station details)
- Color-coded by performance

**Data Source**: `/api/performance/metrics?by_station=true`

#### 2.3 Time Series Charts

**File**: `frontend/src/pages/Performance/Overview/TimeSeriesCharts.tsx`

**Features**:
- Forecast Accuracy Over Time (MAE, RMSE)
- P&L Over Time (cumulative)

**Data Source**: `/api/performance/metrics?group_by=date`

#### 2.4 Top Performers List

**File**: `frontend/src/pages/Performance/Overview/TopPerformers.tsx`

**Features**:
- Top performing brackets
- Top performing stations
- Clickable to view details

**Data Source**: `/api/analytics/brackets`, `/api/performance/metrics`

#### 2.5 Period Selection

**File**: `frontend/src/pages/Performance/Overview/PeriodSelector.tsx`

**Features**:
- Date range picker
- Quick selects (Last 7 days, 30 days, etc.)
- Station multi-select

**Testing**: Verify all components render, data loads correctly

---

### Stage 3: Historical Page Enhancements

**Goal**: Enhance existing Historical view

**Estimated Time**: 4-5 hours

#### 3.1 Update Historical Page

**File**: `frontend/src/pages/Performance/Historical/HistoricalPage.tsx`

**Enhancements**:
- Add actual daily high to Daily High Prediction panel
- Add accuracy indicator (✅/❌)
- Add error calculation
- Improve graph linking (Graphs 2 & 3)

#### 3.2 Enhance Graph 1

**File**: `frontend/src/pages/Performance/Historical/ZeusForecastGraph.tsx`

**Enhancements**:
- Show actual daily high in panel
- Show accuracy indicator
- Show error calculation

#### 3.3 Enhance Graphs 2 & 3

**File**: `frontend/src/pages/Performance/Historical/MarketTradesGraphs.tsx`

**Enhancements**:
- Ensure both use actual timeline (not time of day)
- Implement linked hover
- Show synchronized tooltips

**Testing**: Verify graphs display correctly, hover linking works

---

### Stage 4: Analytics Page

**Goal**: Implement Analytics page with sub-tabs

**Estimated Time**: 10-12 hours

#### 4.1 Analytics Page Layout

**File**: `frontend/src/pages/Performance/Analytics/AnalyticsPage.tsx`

**Structure**:
- Sub-tab navigation
- Content area (changes based on sub-tab)

#### 4.2 Forecast Accuracy Tab

**File**: `frontend/src/pages/Performance/Analytics/ForecastAccuracy.tsx`

**Components**:
- Predicted vs. Actual scatter plot
- Accuracy by Forecast Age heatmap
- Error Distribution by Station box plot
- Key Insights section

**Data Source**: `/api/forecast-accuracy/metrics`

#### 4.3 Timing Analysis Tab

**File**: `frontend/src/pages/Performance/Analytics/TimingAnalysis.tsx`

**Components**:
- P&L by Trade Time bar chart
- Win Rate by Market Age line chart
- Edge Decay Over Time line chart
- Key Insights section

**Data Source**: `/api/analytics/timing`

#### 4.4 Risk Analysis Tab

**File**: `frontend/src/pages/Performance/Analytics/RiskAnalysis.tsx`

**Components**:
- Loss Patterns scatter plot
- Large Loss Events timeline
- Edge vs. Outcome box plot
- Key Insights section

**Data Source**: `/api/analytics/risk`

#### 4.5 Bracket Analysis Tab

**File**: `frontend/src/pages/Performance/Analytics/BracketAnalysis.tsx`

**Components**:
- P&L by Bracket bar chart
- Win Rate vs. Edge scatter plot
- Bracket Performance heatmap
- Key Insights section

**Data Source**: `/api/analytics/brackets`

#### 4.6 Strategy Optimization Tab

**File**: `frontend/src/pages/Performance/Analytics/StrategyOptimization.tsx`

**Components**:
- Parameter Sensitivity charts
- Model Comparison chart
- Backtest vs. Paper comparison
- Recommendations section

**Data Source**: `/api/analytics/strategy`

**Testing**: Verify all tabs work, charts render correctly

---

### Stage 6: Export Functionality

**Goal**: Add export UI for LLM analysis

**Estimated Time**: 3-4 hours

#### 5.1 Export Modal

**File**: `frontend/src/pages/Performance/ExportModal.tsx`

**Features**:
- Format selection (JSON, CSV, Markdown, Text)
- Period selection
- Station selection
- Data section checkboxes
- Export button

#### 5.2 Export Service

**File**: `frontend/src/services/exportService.ts`

**Features**:
- Call export API
- Handle file download
- Show loading state
- Handle errors

**Testing**: Verify all export formats work

---

## 📊 Data Requirements

### Existing Data Sources
- ✅ Zeus snapshots (`data/snapshots/zeus/`)
- ✅ Polymarket snapshots (`data/snapshots/polymarket/`)
- ✅ METAR snapshots (`data/snapshots/metar/`)
- ✅ Decision snapshots (`data/snapshots/decisions/`)
- ✅ Paper trades (`data/trades/`)

### New Data Calculations Needed
- Forecast accuracy (predicted vs. actual)
- Trade timing (hours before event)
- Edge decay over time
- Bracket performance metrics
- Risk patterns

---

## 🔗 API Endpoints Summary

### New Endpoints Needed

**Forecast Accuracy**:
- `GET /api/forecast-accuracy/metrics`

**Timing Analysis**:
- `GET /api/analytics/timing`

**Risk Analysis**:
- `GET /api/analytics/risk`

**Bracket Analysis**:
- `GET /api/analytics/brackets`

**Strategy Optimization**:
- `GET /api/analytics/strategy`

**Export**:
- `GET /api/performance/export`

**Enhanced Historical**:
- `GET /api/performance/historical/{station_code}/{date}`

### Existing Endpoints (May Need Enhancements)
- `GET /api/performance/metrics` (exists, may need enhancements)
- `GET /api/performance/pnl` (exists)
- `GET /api/snapshots/*` (exists, may need enhancements)

---

## ✅ Testing Checklist

### Backend Testing
- [ ] Forecast accuracy calculations correct
- [ ] Timing analysis calculations correct
- [ ] Risk analysis calculations correct
- [ ] Bracket analysis calculations correct
- [ ] Export formats generate correctly
- [ ] All endpoints return correct data structure
- [ ] Error handling works correctly

### Frontend Testing
- [ ] Navigation works correctly
- [ ] Overview page displays all metrics
- [ ] Historical page enhancements work
- [ ] Analytics tabs all function
- [ ] Charts render correctly
- [ ] Export modal works
- [ ] Responsive design works
- [ ] Loading states work
- [ ] Error states work

---

## 📅 Implementation Timeline

### Phase 1: Foundation (Week 1)
- Stage 1: Forecast Accuracy Service
- Stage 2: Timing Analysis Service
- Stage 3: Enhanced Historical Endpoints

### Phase 2: Dynamic Analysis (Week 2) - HIGH PRIORITY
- Stage 4: Dynamic Analysis Services (Forecast Evolution, Market Dynamics, Dynamic Timing)
- This is critical - both Zeus and Polymarket are dynamic systems

### Phase 3: Analytics Services (Week 2-3)
- Stage 5: Analytics Aggregation Services (Risk, Bracket, Strategy)

### Phase 4: Frontend - Overview (Week 3)
- Stage 1: Navigation & Page Structure
- Stage 2: Overview Page (with dynamic metrics)

### Phase 5: Frontend - Historical & Analytics (Week 4-5)
- Stage 3: Historical Page Enhancements (with post-trade analysis)
- Stage 4: Analytics Page (including new dynamic tabs)

### Phase 6: Export & Polish (Week 5)
- Stage 6: Export Functionality (Backend & Frontend)
- Testing & Bug Fixes

**Total Estimated Time**: 5 weeks (with one developer)

**Note**: Dynamic analysis (Phase 2) is critical and should not be skipped. Both Zeus forecasts and Polymarket markets are dynamic systems that change over time.

---

## 🎯 Success Criteria

**We'll know the Performance page is complete when**:

1. ✅ All three views (Overview, Historical, Analytics) are functional
2. ✅ All charts and visualizations render correctly
3. ✅ Data loads and displays accurately
4. ✅ Export functionality works for all formats
5. ✅ Navigation is intuitive and works smoothly
6. ✅ Responsive design works on all screen sizes
7. ✅ All API endpoints are tested and documented
8. ✅ Performance is acceptable (page loads < 2 seconds)

---

**Last Updated**: November 18, 2025

