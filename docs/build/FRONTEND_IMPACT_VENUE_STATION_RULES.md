# Frontend Impact: Venue & Station Rules + Double Rounding

**Date**: 2025-11-21  
**Purpose**: Analyze how introducing venue/station rules and double rounding affects the frontend  
**Scope**: Live Dashboard, Performance Pages, Historical Pages

---

## Executive Summary

**Current State**: Frontend displays simple edge calculations and basic trading data

**Proposed Changes**: 
- Add microstructure adjustments to edge calculations
- Display rounding risk indicators
- Show METAR update timing information
- Display cross-day bleed warnings
- Enhanced trade decision context

**Impact Level**: **Medium** - New data fields and visual indicators, but existing functionality remains intact

---

## Current Frontend Data Flow

### Live Dashboard

**API Endpoints Used**:
- `GET /api/edges/current` - Current trading edges
- `GET /api/trades/recent` - Recent trades
- `GET /api/status` - System status
- `WebSocket /ws/trading` - Real-time updates

**Current Data Structure** (from `/api/edges/current`):
```json
{
  "edges": [
    {
      "bracket_name": "46-47°F",
      "bracket_lower_f": 46,
      "bracket_upper_f": 47,
      "p_zeus": 0.35,
      "p_mkt": 0.28,
      "edge": 0.07,
      "edge_pct": 7.0,
      "f_kelly": 0.12,
      "size_usd": 360.0,
      "station_code": "EGLC",
      "event_day": "2025-11-21"
    }
  ]
}
```

**Current Display**:
- Edge percentage
- Position size
- Zeus vs Market probability
- Basic trade information

---

### Performance/Historical Pages

**API Endpoints Used**:
- `GET /api/compare/zeus-vs-metar` - Zeus vs METAR comparison
- `GET /api/snapshots/zeus` - Zeus forecast snapshots
- `GET /api/snapshots/polymarket` - Polymarket price snapshots
- `GET /api/snapshots/decisions` - Trading decision snapshots
- `GET /api/metar/observations` - METAR observations
- `GET /api/trades/history` - Trade history

**Current Data Structure** (from `/api/compare/zeus-vs-metar`):
```json
{
  "station_code": "EGLC",
  "event_day": "2025-11-16",
  "zeus_prediction_f": 51.5,
  "metar_actual_f": 50.0,
  "error_f": 1.5,
  "error_pct": 3.0,
  "rounded_prediction_f": 52,
  "rounded_actual_f": 50,
  "winning_bracket": "50-51°F",
  "is_correct": false,
  "correctness_status": "Incorrect"
}
```

**Current Display**:
- Daily High Prediction Accuracy card
- Temperature graphs (Zeus, METAR, Polymarket)
- Trade history table
- Performance metrics

---

## Proposed Changes: New Data Fields

### 1. Enhanced Edge Calculation Response

**New Fields Added to `/api/edges/current`**:

```json
{
  "edges": [
    {
      // Existing fields
      "bracket_name": "46-47°F",
      "p_zeus": 0.35,
      "p_mkt": 0.28,
      "edge": 0.07,
      
      // NEW: Microstructure adjustments
      "p_zeus_base": 0.35,  // Original Zeus probability
      "p_zeus_adjusted": 0.38,  // After microstructure adjustments
      "adjustments": {
        "rounding_adjustment": 0.02,
        "rounding_reason": "moderate_rounding_risk",
        "metar_adjustment": 0.01,
        "metar_reason": "metar_trend_up_update_in_3min",
        "bleed_adjustment": 0.0,
        "bleed_reason": "no_bleed",
        "total_adjustment": 0.03
      },
      
      // NEW: Rounding risk indicator
      "rounding_risk": {
        "is_fragile_boundary": true,
        "boundary_distance": 0.05,  // °F from boundary
        "risk_level": "moderate",  // "low", "moderate", "high"
        "expected_volatility": 0.15  // Probability swing range
      },
      
      // NEW: METAR update timing
      "metar_update_info": {
        "next_update_minutes": 3,
        "is_near_update": true,
        "update_times": [20, 50],  // Minutes past hour
        "trend_direction": "up",
        "trend_strength": 0.6
      },
      
      // NEW: Cross-day bleed warning
      "cross_day_bleed": {
        "is_bleeding": false,
        "previous_day_high": null,
        "current_temp": null,
        "warning": null
      }
    }
  ]
}
```

---

### 2. Enhanced Trade History Response

**New Fields Added to `/api/trades/history`**:

```json
{
  "trades": [
    {
      // Existing fields
      "timestamp": "2025-11-21T10:30:00Z",
      "bracket_name": "46-47°F",
      "edge": 0.07,
      "size_usd": 360.0,
      
      // NEW: Adjustment context
      "adjustments_applied": {
        "rounding_adjustment": 0.02,
        "metar_adjustment": 0.01,
        "bleed_adjustment": 0.0,
        "total_adjustment": 0.03
      },
      
      // NEW: Rounding risk at time of trade
      "rounding_risk_at_trade": {
        "is_fragile_boundary": true,
        "risk_level": "moderate"
      },
      
      // NEW: METAR update context
      "metar_context": {
        "traded_near_update": true,
        "minutes_before_update": 2,
        "trend_direction": "up"
      }
    }
  ]
}
```

---

### 3. Enhanced Decision Snapshots

**New Fields Added to `/api/snapshots/decisions`**:

```json
{
  "snapshots": [
    {
      // Existing fields
      "timestamp": "2025-11-21T10:30:00Z",
      "decisions": [
        {
          "bracket_name": "46-47°F",
          "edge": 0.07,
          "size_usd": 360.0
        }
      ],
      
      // NEW: Microstructure context
      "microstructure_context": {
        "station_code": "EGLC",
        "metar_update_times": [20, 50],
        "minutes_until_next_update": 3,
        "rounding_risks": [
          {
            "bracket": "46-47°F",
            "is_fragile": true,
            "risk_level": "moderate"
          }
        ]
      }
    }
  ]
}
```

---

## Frontend Impact Analysis

### Impact 1: Live Dashboard

#### Current Display
- Simple edge percentage
- Position size
- Basic trade information

#### New Display Requirements

**1. Edge Display Enhancement**:
```
Current: Edge: 7.0%
New:     Edge: 7.0% (Base: 5.0% + Adjustments: +2.0%)
         └─ Rounding: +1.5% (moderate risk)
         └─ METAR: +0.5% (update in 3min)
```

**2. Rounding Risk Indicator**:
```
Visual indicator (icon/badge):
- 🟢 Low risk (far from boundary)
- 🟡 Moderate risk (near boundary)
- 🔴 High risk (very close to boundary)

Tooltip: "Temperature near rounding boundary (50.05°F). 
         Small changes could flip bracket."
```

**3. METAR Update Timer**:
```
Countdown display:
"Next METAR update: 3 minutes"
"Trend: ↑ Warming (strength: 60%)"

Visual indicator when < 5 minutes to update
```

**4. Cross-Day Bleed Warning**:
```
Alert banner (if applicable):
"⚠️ Early morning: Overnight temp (51.8°F) near previous day's high.
   Zeus predicts higher afternoon high (52.5°F). 
   Potential mispricing opportunity."
```

---

### Impact 2: Performance/Historical Pages

#### Current Display
- Daily High Prediction Accuracy card
- Temperature graphs
- Trade history table

#### New Display Requirements

**1. Enhanced Accuracy Card**:
```
Current:
- Predicted High: 51.5°F
- Actual High: 50.0°F
- Error: +1.5°F
- Correct/Incorrect: ❌ Incorrect

New (add):
- Rounding Risk: 🟡 Moderate (predicted: 51.5°F → 52°F, actual: 50.0°F → 50°F)
- Adjustment Impact: "Base edge: 5.0%, Adjusted: 7.0% (+2.0% from rounding)"
```

**2. Trade History Table Enhancement**:
```
Add columns:
- "Adjustments" (tooltip with breakdown)
- "Rounding Risk" (icon indicator)
- "METAR Context" (if traded near update)

Example row:
| Bracket | Edge | Size | Adjustments | Rounding | METAR |
|---------|------|------|-------------|----------|-------|
| 46-47°F | 7.0% | $360 | +2.0%       | 🟡 Mod  | 3min  |
```

**3. Historical Analysis Enhancement**:
```
New section: "Microstructure Analysis"
- Rounding risk distribution over time
- METAR update timing impact on trades
- Cross-day bleed occurrences
- Adjustment contribution to edge
```

---

## API Changes Required

### 1. Enhance Edge Endpoint

**File**: `backend/api/routes/edges.py`

**Current Response**:
```python
{
  "edges": [
    {
      "bracket_name": "...",
      "edge": 0.07,
      ...
    }
  ]
}
```

**Enhanced Response** (add new fields):
```python
{
  "edges": [
    {
      # Existing fields
      "bracket_name": "...",
      "edge": 0.07,
      
      # NEW fields
      "p_zeus_base": 0.35,
      "p_zeus_adjusted": 0.38,
      "adjustments": {...},
      "rounding_risk": {...},
      "metar_update_info": {...},
      "cross_day_bleed": {...}
    }
  ]
}
```

**Backend Changes**:
- Modify `EdgeService` to calculate adjustments
- Include adjustment breakdown in response
- Add rounding risk analysis
- Add METAR update timing
- Add cross-day bleed detection

---

### 2. Enhance Trade History Endpoint

**File**: `backend/api/routes/trades.py`

**Current Response**:
```python
{
  "trades": [
    {
      "timestamp": "...",
      "edge": 0.07,
      ...
    }
  ]
}
```

**Enhanced Response** (add new fields):
```python
{
  "trades": [
    {
      # Existing fields
      "timestamp": "...",
      "edge": 0.07,
      
      # NEW fields
      "adjustments_applied": {...},
      "rounding_risk_at_trade": {...},
      "metar_context": {...}
    }
  ]
}
```

**Backend Changes**:
- Store adjustment data in trade CSV files
- Include adjustment context in response
- Add rounding risk at time of trade
- Add METAR context at time of trade

---

### 3. Enhance Decision Snapshots

**File**: `backend/api/routes/snapshots.py`

**Current Response**:
```python
{
  "snapshots": [
    {
      "timestamp": "...",
      "decisions": [...]
    }
  ]
}
```

**Enhanced Response** (add new fields):
```python
{
  "snapshots": [
    {
      # Existing fields
      "timestamp": "...",
      "decisions": [...],
      
      # NEW fields
      "microstructure_context": {...}
    }
  ]
}
```

**Backend Changes**:
- Include microstructure context in snapshot files
- Add to response when available

---

## Frontend Implementation Plan

### Phase 1: API Integration (Week 1)

**Tasks**:
1. Update API client to handle new fields
2. Add TypeScript interfaces for new data structures
3. Update API calls to request new fields
4. Handle backward compatibility (fields may be null for old data)

**Time**: 4-6 hours

---

### Phase 2: Live Dashboard Enhancements (Week 1-2)

**Tasks**:
1. **Edge Display Enhancement**:
   - Show base vs adjusted edge
   - Display adjustment breakdown (tooltip or expandable)
   - Visual indicator for adjustments

2. **Rounding Risk Indicator**:
   - Add risk level badge/icon
   - Tooltip with explanation
   - Color coding (green/yellow/red)

3. **METAR Update Timer**:
   - Countdown display
   - Trend indicator
   - Visual alert when < 5 minutes

4. **Cross-Day Bleed Warning**:
   - Alert banner component
   - Show when applicable
   - Dismissible

**Time**: 8-12 hours

---

### Phase 3: Performance Page Enhancements (Week 2)

**Tasks**:
1. **Enhanced Accuracy Card**:
   - Add rounding risk indicator
   - Show adjustment impact
   - Visual breakdown of adjustments

2. **Trade History Table**:
   - Add "Adjustments" column
   - Add "Rounding Risk" column
   - Add "METAR Context" column
   - Tooltips for details

3. **Historical Analysis Section**:
   - New "Microstructure Analysis" section
   - Charts showing:
     - Rounding risk distribution
     - METAR update timing impact
     - Adjustment contribution over time

**Time**: 12-16 hours

---

### Phase 4: Historical Page Enhancements (Week 2-3)

**Tasks**:
1. **Graph Enhancements**:
   - Add fragile boundary markers on temperature graph
   - Show METAR update times as vertical lines
   - Highlight cross-day bleed periods

2. **Decision Snapshot Display**:
   - Show microstructure context
   - Display adjustment breakdown
   - Show rounding risk at decision time

**Time**: 8-10 hours

---

## UI/UX Design Considerations

### 1. Information Density

**Challenge**: Adding new data without overwhelming the UI

**Solution**:
- Use collapsible sections for detailed breakdowns
- Tooltips for additional context
- Progressive disclosure (show summary, expand for details)
- Visual indicators (icons, colors) instead of text where possible

---

### 2. Backward Compatibility

**Challenge**: Old data won't have new fields

**Solution**:
- All new fields optional (nullable)
- Graceful degradation (hide sections if data unavailable)
- Show "N/A" or "Not available" for missing data
- Don't break existing functionality

---

### 3. Visual Hierarchy

**Priority Levels**:
1. **High**: Edge adjustments (affects trading decisions)
2. **Medium**: Rounding risk (important for understanding)
3. **Low**: METAR update timing (nice to have)
4. **Info**: Cross-day bleed (contextual)

**Visual Treatment**:
- High priority: Prominent display, color coding
- Medium priority: Icons/badges, tooltips
- Low priority: Small text, expandable sections
- Info: Alert banners, dismissible

---

## Component Structure

### New Components Needed

1. **AdjustmentBreakdown**:
   - Shows base vs adjusted edge
   - Breakdown of adjustments
   - Visual indicators

2. **RoundingRiskIndicator**:
   - Risk level badge
   - Tooltip with explanation
   - Color coding

3. **MetarUpdateTimer**:
   - Countdown display
   - Trend indicator
   - Visual alerts

4. **CrossDayBleedWarning**:
   - Alert banner
   - Contextual information
   - Dismissible

5. **MicrostructureAnalysis**:
   - Historical charts
   - Distribution analysis
   - Impact metrics

---

## Data Migration Considerations

### Historical Data

**Issue**: Old trades/snapshots won't have adjustment data

**Solution**:
- New fields are optional (nullable)
- Frontend handles missing data gracefully
- Can retroactively calculate some adjustments (rounding risk) if needed
- Don't require data migration for existing records

---

### Backward Compatibility

**Strategy**:
- API returns new fields when available
- Frontend checks for field existence before displaying
- Fallback to old display if new fields missing
- No breaking changes to existing API contracts

---

## Testing Strategy

### Unit Tests

1. **Component Tests**:
   - Test components with new data
   - Test components with missing data (backward compatibility)
   - Test visual indicators

2. **API Client Tests**:
   - Test new field parsing
   - Test backward compatibility
   - Test error handling

---

### Integration Tests

1. **Live Dashboard**:
   - Test with new data
   - Test with old data (backward compatibility)
   - Test real-time updates

2. **Performance Pages**:
   - Test enhanced accuracy card
   - Test trade history table
   - Test historical analysis

---

## Rollout Plan

### Phase 1: Backend Only (Week 1)

- Implement backend changes
- Add new fields to API responses
- Ensure backward compatibility
- Test API endpoints

**Frontend**: No changes yet, but new fields available

---

### Phase 2: Frontend - Live Dashboard (Week 2)

- Update API client
- Add new components
- Enhance edge display
- Add rounding risk indicators
- Add METAR update timer

**Rollout**: Feature flag to enable/disable new features

---

### Phase 3: Frontend - Performance Pages (Week 3)

- Enhance accuracy card
- Update trade history table
- Add microstructure analysis section

**Rollout**: Gradual rollout, monitor for issues

---

### Phase 4: Frontend - Historical Pages (Week 3-4)

- Enhance graphs
- Add decision snapshot context
- Add historical analysis

**Rollout**: Full rollout after testing

---

## Summary

### Impact Assessment

**Live Dashboard**:
- **Impact**: Medium
- **Changes**: Enhanced edge display, new indicators, update timer
- **Time**: 8-12 hours

**Performance Pages**:
- **Impact**: Medium
- **Changes**: Enhanced accuracy card, trade history table, new analysis section
- **Time**: 12-16 hours

**Historical Pages**:
- **Impact**: Low-Medium
- **Changes**: Graph enhancements, decision context
- **Time**: 8-10 hours

**Total Frontend Time**: 28-38 hours (3.5-5 days)

---

### Key Considerations

1. **Backward Compatibility**: All new fields optional, graceful degradation
2. **Information Density**: Use progressive disclosure, tooltips, collapsible sections
3. **Visual Hierarchy**: Prioritize important information, use visual indicators
4. **Gradual Rollout**: Feature flags, phased implementation

---

### Benefits

1. **Better Decision Making**: Users see why trades were made
2. **Risk Awareness**: Rounding risk and update timing visible
3. **Performance Analysis**: Understand impact of microstructure adjustments
4. **Transparency**: Full context for trading decisions

---

**Status**: 📋 **Frontend Impact Analysis Complete** - Ready for implementation planning

