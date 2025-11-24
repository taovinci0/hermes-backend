# Strategy Page - Frontend Implementation Specification

**Date**: 2025-11-21  
**Purpose**: Frontend implementation guide for Strategy Page

---

## Overview

The Strategy Page displays:
1. **Current Strategy Documentation** - Simple English explanations of probability models and trading strategies
2. **Strategy Changelog** - Complete history of all changes to models, features, and configurations

---

## API Endpoints

### Base URL
All endpoints are under `/api/strategy`

### 1. Get Strategy Documentation

**Endpoint**: `GET /api/strategy`

**Description**: Returns current strategy documentation including models and trading strategy.

**Response**:
```json
{
  "version": "1.0.0",
  "last_updated": "2025-11-21T00:00:00Z",
  "models": {
    "spread_model": {
      "name": "Spread Model",
      "status": "active",
      "default": true,
      "description": "Uses the variation in hourly temperature forecasts to estimate uncertainty...",
      "how_it_works": {
        "step_1": "We take all 24 hourly temperature forecasts from Zeus and find the maximum...",
        "step_2": "We calculate how much the hourly temperatures vary...",
        "step_3": "We use a normal distribution...",
        "step_4": "The probabilities are normalized..."
      },
      "when_to_use": "This is our default model. Use it when you want a proven, conservative approach...",
      "parameters": {
        "sigma_default": {
          "value": 2.0,
          "unit": "°F",
          "description": "Default uncertainty when we can't calculate from spread"
        },
        "sigma_min": {
          "value": 0.5,
          "unit": "°F",
          "description": "Minimum uncertainty to prevent extreme predictions"
        },
        "sigma_max": {
          "value": 10.0,
          "unit": "°F",
          "description": "Maximum uncertainty to prevent overly wide distributions"
        }
      },
      "implementation_file": "agents/prob_models/spread_model.py"
    },
    "bands_model": {
      "name": "Bands Model",
      "status": "available",
      "default": false,
      "description": "Uses Zeus confidence intervals...",
      "how_it_works": {
        "step_1": "...",
        "step_2": "...",
        "fallback": "Currently, Zeus API doesn't provide confidence bands..."
      },
      "when_to_use": "Use this model when Zeus API starts providing confidence bands...",
      "parameters": {
        "zeus_likely_pct": {
          "value": 0.80,
          "unit": "percentage",
          "description": "Zeus 'likely' confidence level (80%)"
        }
      },
      "implementation_file": "agents/prob_models/bands_model.py"
    }
  },
  "trading_strategy": {
    "edge_calculation": {
      "description": "We calculate edge as the difference between our Zeus probability and the market probability, minus fees and slippage.",
      "formula": "Edge = (p_zeus - p_market) - fees - slippage",
      "minimum_edge": {
        "value": 0.05,
        "unit": "decimal (5%)",
        "description": "We only trade when edge is at least 5%"
      }
    },
    "position_sizing": {
      "description": "We use the Kelly Criterion to determine how much to bet on each opportunity, with multiple safety caps.",
      "kelly_formula": "f* = (b×p - q) / b, where b = (1/price - 1), p = our probability, q = 1 - p",
      "caps": {
        "kelly_cap": {
          "value": 0.10,
          "unit": "decimal (10%)",
          "description": "Maximum Kelly fraction per trade (10% of bankroll)"
        },
        "per_market_cap": {
          "value": 500.0,
          "unit": "USD",
          "description": "Maximum position size per market"
        },
        "daily_bankroll_cap": {
          "value": 3000.0,
          "unit": "USD",
          "description": "Maximum total bankroll per day"
        }
      }
    },
    "liquidity_requirements": {
      "minimum_liquidity": {
        "value": 1000.0,
        "unit": "USD",
        "description": "We only trade markets with at least $1000 of available liquidity"
      },
      "description": "We check market depth to ensure we can enter and exit positions without significant slippage."
    }
  }
}
```

---

### 2. Get Strategy Changelog

**Endpoint**: `GET /api/strategy/changelog`

**Query Parameters**:
- `limit` (optional, integer): Maximum number of entries to return
- `category` (optional, string): Filter by category (`model`, `configuration`, `feature`, `documentation`)
- `type_filter` (optional, string): Filter by type (`added`, `changed`, `removed`, `fixed`, `initial`)

**Description**: Returns all changelog entries with optional filtering.

**Example Requests**:
```
GET /api/strategy/changelog
GET /api/strategy/changelog?limit=10
GET /api/strategy/changelog?category=model
GET /api/strategy/changelog?category=configuration&limit=20
GET /api/strategy/changelog?category=model&type_filter=changed
```

**Response**:
```json
{
  "version": "1.0.0",
  "total_entries": 15,
  "filtered_entries": 10,
  "entries": [
    {
      "id": "2025-11-21-1",
      "date": "2025-11-21T14:30:00Z",
      "type": "changed",
      "category": "model",
      "title": "Updated spread model sigma calculation",
      "description": "Changed sigma calculation to use sqrt(2) multiplier for better uncertainty estimation",
      "affected_components": ["spread_model"],
      "changes": [
        {
          "component": "spread_model",
          "change": "Updated sigma calculation formula",
          "old_value": "sigma = empirical_std",
          "new_value": "sigma = empirical_std * sqrt(2.0)"
        }
      ],
      "author": "optional author name"
    },
    {
      "id": "2025-11-21-2",
      "date": "2025-11-21T10:15:00Z",
      "type": "changed",
      "category": "configuration",
      "title": "Configuration Change: trading.edge_min",
      "description": "Updated trading or model configuration. 1 parameter(s) changed.",
      "affected_components": ["trading.edge_min"],
      "changes": [
        {
          "component": "trading.edge_min",
          "change": "Changed from 0.05 to 0.06",
          "old_value": "0.05",
          "new_value": "0.06"
        }
      ]
    }
  ]
}
```

---

### 3. Get Configuration Changelog Only

**Endpoint**: `GET /api/strategy/changelog/configuration`

**Query Parameters**:
- `limit` (optional, integer): Maximum number of entries to return

**Description**: Returns only configuration changes (separate from model/feature changes).

**Response**: Same structure as `/api/strategy/changelog`, but only includes entries where `category === "configuration"`.

---

### 4. Add Changelog Entry (Optional)

**Endpoint**: `POST /api/strategy/changelog`

**Description**: Manually add a changelog entry (for model/feature changes). Configuration changes are automatically logged.

**Request Body**:
```json
{
  "title": "Updated spread model calculation",
  "description": "Changed sigma calculation to improve uncertainty estimation",
  "category": "model",
  "entry_type": "changed",
  "affected_components": ["spread_model"],
  "changes": [
    {
      "component": "spread_model",
      "change": "Updated sigma formula"
    }
  ],
  "author": "optional author name"
}
```

**Response**: Returns the created changelog entry (same structure as entries in GET response).

**Note**: This endpoint is optional for the frontend - it's mainly for backend/CLI use. You may want to include a form for manual logging, but it's not required.

---

## UI/UX Requirements

### Page Structure

The Strategy Page should have two main sections:

#### 1. Strategy Documentation Section

**Title**: "Trading Strategy"

**Subsections**:

1. **Probability Models**
   - Display each model in a card/panel
   - Show model name, status badges (Active, Default, Available)
   - Display description
   - Show "How It Works" as a numbered list
   - Display "When to Use" information
   - Show parameters in a table with:
     - Parameter name (code style)
     - Value + unit
     - Description

2. **Trading Strategy**
   - **Edge Calculation**:
     - Description
     - Formula (display in code/monospace font)
     - Minimum edge value and description
   - **Position Sizing**:
     - Description
     - Kelly formula (display in code/monospace font)
     - Position size caps in a table
   - **Liquidity Requirements**:
     - Description
     - Minimum liquidity value and description

#### 2. Changelog Section

**Title**: "Strategy Changelog"

**Features**:
- Filter tabs/buttons:
  - All Changes (default)
  - Models
  - Configuration
  - Features
  - Documentation
- Display entries in reverse chronological order (newest first)
- Each entry should show:
  - Date/time (formatted nicely)
  - Title
  - Type badge (added, changed, removed, fixed)
  - Category badge/color coding
  - Description
  - Affected components (if any)
  - Detailed changes list (if any)
  - Author (if present)

**Visual Design Suggestions**:
- Use color coding for categories:
  - Model: Blue
  - Configuration: Red
  - Feature: Green
  - Documentation: Purple
- Use badges for types:
  - Added: Green
  - Changed: Yellow/Orange
  - Removed: Red
  - Fixed: Blue
- Use left border or background color to indicate category
- Show "Default" badge prominently for default model

---

## Data Display Guidelines

### Model Status Badges

- **Active**: Green badge - "Active"
- **Default**: Yellow/Orange badge - "Default" (only one model should have this)
- **Available**: Blue badge - "Available"

### Changelog Entry Types

- **added**: New model/feature added
- **changed**: Existing model/feature modified
- **removed**: Model/feature removed
- **fixed**: Bug fix
- **initial**: Initial documentation/entry

### Date Formatting

Format dates in a user-friendly way:
- Relative time for recent entries: "2 hours ago", "Yesterday"
- Absolute date for older entries: "Nov 21, 2025 at 2:30 PM"

### Formula Display

Display formulas in a monospace/code font, centered or in a highlighted box:
- `Edge = (p_zeus - p_market) - fees - slippage`
- `f* = (b×p - q) / b`

---

## Example Component Structure

### React Example (pseudo-code)

```jsx
<StrategyPage>
  <StrategyDocumentation>
    <ModelsSection>
      {models.map(model => (
        <ModelCard>
          <ModelHeader>
            <ModelName />
            <StatusBadges />
          </ModelHeader>
          <Description />
          <HowItWorks steps={model.how_it_works} />
          <WhenToUse />
          <ParametersTable parameters={model.parameters} />
        </ModelCard>
      ))}
    </ModelsSection>
    
    <TradingStrategySection>
      <EdgeCalculation />
      <PositionSizing />
      <LiquidityRequirements />
    </TradingStrategySection>
  </StrategyDocumentation>
  
  <ChangelogSection>
    <FilterTabs 
      categories={['all', 'model', 'configuration', 'feature', 'documentation']}
      onFilterChange={handleFilter}
    />
    <ChangelogEntries>
      {entries.map(entry => (
        <ChangelogEntry 
          entry={entry}
          category={entry.category}
          type={entry.type}
        />
      ))}
    </ChangelogEntries>
  </ChangelogSection>
</StrategyPage>
```

---

## Error Handling

Handle these error cases:

1. **API Error (500)**: Show error message: "Failed to load strategy documentation" or "Failed to load changelog"
2. **Network Error**: Show connection error message
3. **Empty Data**: Show "No changelog entries found" or "No strategy documentation available"
4. **Loading States**: Show loading spinners/skeletons while fetching data

---

## API Response Notes

### Strategy Documentation
- `models` object contains all available models (currently `spread_model` and `bands_model`)
- `trading_strategy` contains edge calculation, position sizing, and liquidity requirements
- All text fields are in simple English (no technical jargon)

### Changelog
- Entries are sorted by date (newest first) by the backend
- `total_entries` = total in database
- `filtered_entries` = entries after filtering
- `changes` array may be empty for some entries
- `old_value` and `new_value` are only present for configuration changes

---

## Testing Checklist

- [ ] Strategy documentation loads and displays correctly
- [ ] All models are displayed with correct information
- [ ] Trading strategy section displays all subsections
- [ ] Changelog loads and displays entries
- [ ] Filter tabs work correctly (all, model, configuration, feature, documentation)
- [ ] Date formatting is user-friendly
- [ ] Status badges display correctly
- [ ] Type badges display correctly
- [ ] Error states are handled gracefully
- [ ] Loading states are shown during API calls
- [ ] Empty states are handled (no entries, no models, etc.)
- [ ] Responsive design works on mobile/tablet

---

## Additional Notes

1. **Configuration Changes**: These are automatically logged by the backend when config is updated via `POST /api/config`. No frontend action needed.

2. **Manual Logging**: The `POST /api/strategy/changelog` endpoint is available if you want to add a form for manually logging model/feature changes, but it's optional.

3. **Real-time Updates**: Consider polling or websocket updates if you want the changelog to update in real-time when new entries are added.

4. **Search/Filter**: Consider adding a search box to filter changelog entries by title/description if there are many entries.

5. **Export**: Consider adding export functionality (CSV/JSON) for the changelog if needed.

---

## Questions?

If you need clarification on any endpoint or data structure, refer to:
- Backend API docs: `http://localhost:8000/docs` (Swagger UI)
- Implementation details: `docs/build/STRATEGY_PAGE_IMPLEMENTATION.md`

