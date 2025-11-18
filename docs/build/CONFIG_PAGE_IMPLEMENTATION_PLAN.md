# Configuration Page Implementation Plan

**Date**: November 17, 2025  
**Purpose**: Detailed plan for implementing backend/API and frontend configuration management

---

## 🎯 Overview

This document outlines what needs to be built for:
1. **Backend/API** - Services and endpoints for configuration management
2. **Frontend** - Configuration page UI with organized, collapsible sections

**Key Design Decision**: Trading config and model fields should be in collapsible sections/dropdowns to avoid overwhelming the page and allow for future expansion.

---

## 📋 Backend/API Requirements

### 1. Engine Control Service

**File**: `backend/api/services/engine_service.py`

**Responsibilities**:
- Start/stop/restart trading engine
- Manage engine process (PID file, subprocess)
- Pass configuration to engine on start
- Track engine state

**Methods**:
```python
class EngineService:
    def start_engine(
        self,
        stations: List[str],
        interval_seconds: int,
        lookahead_days: int,
        # Trading parameters
        edge_min: float,
        fee_bp: int,
        slippage_bp: int,
        kelly_cap: float,
        per_market_cap: float,
        liquidity_min_usd: float,
        daily_bankroll_cap: float,
        # Probability model parameters
        model_mode: str,
        zeus_likely_pct: float,
        zeus_possible_pct: float,
    ) -> Dict[str, Any]
    
    def stop_engine(self) -> Dict[str, Any]
    
    def restart_engine(self, **config_params) -> Dict[str, Any]
    
    def get_engine_config(self) -> Optional[Dict[str, Any]]
    
    def is_running(self) -> bool
```

**Implementation Notes**:
- Use subprocess to start engine with environment variables or config file
- Store engine config in a JSON file when engine starts (for retrieval)
- Use PID file to track running process
- Send SIGINT to stop gracefully

---

### 2. Configuration Service

**File**: `backend/api/services/config_service.py`

**Responsibilities**:
- Read/write global configuration
- Validate configuration values
- Reload configuration from disk
- Manage `.env` file or `config.local.yaml`

**Methods**:
```python
class ConfigService:
    def get_config(self) -> Dict[str, Any]
    
    def update_config(self, updates: Dict[str, Any]) -> Dict[str, Any]
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]
    
    def reload_config(self) -> Dict[str, Any]
    
    def get_default_config(self) -> Dict[str, Any]
    
    def reset_to_defaults(self) -> Dict[str, Any]
```

**Configuration Structure**:
```python
{
    "trading": {
        "active_stations": ["EGLC", "KLGA"],
        "edge_min": 0.05,
        "fee_bp": 50,
        "slippage_bp": 30,
        "kelly_cap": 0.10,
        "daily_bankroll_cap": 3000.0,
        "per_market_cap": 500.0,
        "liquidity_min_usd": 1000.0
    },
    "probability_model": {
        "model_mode": "spread",
        "zeus_likely_pct": 0.80,
        "zeus_possible_pct": 0.95,
        "sigma_default": 2.0,
        "sigma_min": 0.5,
        "sigma_max": 10.0
    },
    "dynamic_trading": {
        "interval_seconds": 900,
        "lookahead_days": 2
    },
    "execution_mode": "paper",
    "api_keys": {
        "zeus_api_key": "****1234",  # Masked
        "polymarket_api_key": "****5678",  # Masked
        "polymarket_private_key": "****9012",  # Masked
        "polymarket_wallet_address": "0x1234..."
    }
}
```

**Validation Rules**:
- `edge_min`: 0.01 to 0.50 (1% to 50%)
- `fee_bp`: 0 to 1000 (0% to 10%)
- `slippage_bp`: 0 to 1000
- `kelly_cap`: 0.01 to 0.50 (1% to 50%)
- `model_mode`: "spread" or "bands"
- `zeus_likely_pct`: 0.50 to 0.99
- `zeus_possible_pct`: 0.80 to 0.99
- `interval_seconds`: 60 to 3600 (1 min to 1 hour)
- `lookahead_days`: 1 to 7
- `execution_mode`: "paper" or "live"
- Station codes must exist in registry

---

### 3. API Endpoints

**File**: `backend/api/routes/engine.py`

**Endpoints**:
```python
POST /api/engine/start
POST /api/engine/stop
POST /api/engine/restart
GET /api/engine/config
GET /api/engine/status  # Already exists via /api/status
```

**File**: `backend/api/routes/config.py`

**Endpoints**:
```python
GET /api/config
PUT /api/config
POST /api/config/reload
POST /api/config/validate
GET /api/config/defaults
POST /api/config/reset
```

**Request/Response Examples**:

#### Start Engine
```http
POST /api/engine/start
Content-Type: application/json

{
  "stations": ["EGLC", "KLGA"],
  "interval_seconds": 900,
  "lookahead_days": 2,
  "trading": {
    "edge_min": 0.05,
    "fee_bp": 50,
    "slippage_bp": 30,
    "kelly_cap": 0.10,
    "per_market_cap": 500.0,
    "liquidity_min_usd": 1000.0,
    "daily_bankroll_cap": 3000.0
  },
  "probability_model": {
    "model_mode": "spread",
    "zeus_likely_pct": 0.80,
    "zeus_possible_pct": 0.95
  }
}

Response:
{
  "success": true,
  "message": "Trading engine started",
  "pid": 12345,
  "status": "running",
  "config": { /* echo back config */ }
}
```

#### Get Configuration
```http
GET /api/config

Response:
{
  "trading": { /* ... */ },
  "probability_model": { /* ... */ },
  "dynamic_trading": { /* ... */ },
  "execution_mode": "paper",
  "api_keys": { /* masked */ }
}
```

#### Update Configuration
```http
PUT /api/config
Content-Type: application/json

{
  "trading": {
    "edge_min": 0.06
  },
  "dynamic_trading": {
    "interval_seconds": 1800
  }
}

Response:
{
  "success": true,
  "message": "Configuration updated",
  "requires_restart": false,
  "updated_fields": ["trading.edge_min", "dynamic_trading.interval_seconds"]
}
```

---

### 4. Modify Dynamic Engine

**File**: `agents/dynamic_trader/dynamic_engine.py`

**Changes Needed**:
- Accept configuration parameters in `__init__` instead of reading from global `config`
- Store configuration for later retrieval
- Allow configuration to be passed when starting engine

**Current**:
```python
self.sizer = Sizer(
    edge_min=config.trading.edge_min,
    fee_bp=config.trading.fee_bp,
    # ...
)
```

**New**:
```python
def __init__(
    self,
    stations: List[str],
    interval_seconds: int,
    lookahead_days: int,
    trading_config: Dict[str, Any],
    probability_model_config: Dict[str, Any],
):
    self.trading_config = trading_config
    self.probability_model_config = probability_model_config
    
    self.sizer = Sizer(
        edge_min=trading_config["edge_min"],
        fee_bp=trading_config["fee_bp"],
        # ...
    )
```

---

## 🎨 Frontend Requirements

### 1. Configuration Page Structure

**Page Layout** (Collapsible Sections):

```
┌─────────────────────────────────────────────────────────────┐
│  Configuration                                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─ ⚙️  Trading Engine Control ─────────────────────────┐  │
│  │                                                       │  │
│  │  Status: ● RUNNING (PID: 12345)                      │  │
│  │  [Stop] [Restart]                                    │  │
│  │                                                       │  │
│  │  Or:                                                 │  │
│  │  Status: ○ STOPPED                                   │  │
│  │  [Start Engine]                                      │  │
│  │                                                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─ 📊 Execution Mode ──────────────────────────────────┐  │
│  │                                                       │  │
│  │  Mode: ○ Paper  ● Live  ⓘ                           │  │
│  │  ⚠️  Live trading requires Polymarket account setup  │  │
│  │                                                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─ 🔄 Dynamic Trading Settings ────────────────────────┐  │
│  │                                                       │  │
│  │  Evaluation Interval: [15] minutes  ⓘ               │  │
│  │  Lookahead Days: [2] days  ⓘ                        │  │
│  │  Active Stations: [EGLC] [KLGA] [+ Add]             │  │
│  │                                                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─ ▼ Trading Parameters ───────────────────────────────┐  │
│  │  (Collapsible - click to expand)                     │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─ ▼ Probability Model ────────────────────────────────┐  │
│  │  (Collapsible - click to expand)                     │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─ ▼ API Keys (Sensitive) ─────────────────────────────┐  │
│  │  (Collapsible - click to expand)                     │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─ ▼ Polymarket Account (Future) ──────────────────────┐  │
│  │  (Collapsible - click to expand)                     │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  [Save Configuration] [Reset to Defaults] [Reload from Disk]│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### 2. Collapsible Sections

**Trading Parameters** (Collapsed by default):
```
┌─ ▼ Trading Parameters ────────────────────────────────┐
│  Minimum Edge: 5.0%                                    │
│  Fee (bp): 50                                          │
│  Slippage (bp): 30                                     │
│  Kelly Cap: 10.0%                                      │
│  Daily Bankroll Cap: $3,000.00                         │
│  Per-Market Cap: $500.00                               │
│  Min Liquidity: $1,000.00                              │
└────────────────────────────────────────────────────────┘
```

**When Expanded**:
```
┌─ ▲ Trading Parameters ────────────────────────────────┐
│                                                       │
│  Minimum Edge: [5.0] %  ⓘ                           │
│  Fee (bp): [50]  ⓘ                                   │
│  Slippage (bp): [30]  ⓘ                             │
│  Kelly Cap: [10.0] %  ⓘ                             │
│  Daily Bankroll Cap: [$3000.00]  ⓘ                  │
│  Per-Market Cap: [$500.00]  ⓘ                       │
│  Min Liquidity: [$1000.00]  ⓘ                       │
│                                                       │
└───────────────────────────────────────────────────────┘
```

**Probability Model** (Collapsed by default):
```
┌─ ▼ Probability Model ────────────────────────────────┐
│  Model Mode: Spread                                    │
│  Zeus Likely %: 80.0%                                 │
│  Zeus Possible %: 95.0%                               │
└────────────────────────────────────────────────────────┘
```

**When Expanded**:
```
┌─ ▲ Probability Model ────────────────────────────────┐
│                                                       │
│  Model Mode: [Spread ▼]  ⓘ                          │
│  Zeus Likely %: [80.0] %  ⓘ                         │
│  Zeus Possible %: [95.0] %  ⓘ                       │
│  Sigma Default: [2.0] °F  ⓘ                         │
│  Sigma Min: [0.5] °F  ⓘ                             │
│  Sigma Max: [10.0] °F  ⓘ                            │
│                                                       │
└───────────────────────────────────────────────────────┘
```

---

### 3. Frontend Components

#### Main Config Page Component
```typescript
// ConfigPage.tsx
- State management for all config sections
- Collapsible section handlers
- Form validation
- Save/Reset/Reload handlers
- Engine control integration
```

#### Collapsible Section Component
```typescript
// CollapsibleSection.tsx
Props:
- title: string
- defaultExpanded?: boolean
- children: ReactNode
- summary?: string (shown when collapsed)

Features:
- Expand/collapse animation
- Summary view when collapsed
- Full form when expanded
```

#### Engine Control Component
```typescript
// EngineControl.tsx
- Display engine status
- Start/Stop/Restart buttons
- Loading states
- Error handling
- Status polling
```

#### Config Form Sections
```typescript
// TradingParamsForm.tsx
// ProbabilityModelForm.tsx
// DynamicTradingForm.tsx
// ApiKeysForm.tsx
// ExecutionModeForm.tsx
```

---

### 4. Frontend State Management

**State Structure**:
```typescript
interface ConfigState {
  // Engine control
  engineStatus: {
    running: boolean;
    pid?: number;
    config?: EngineConfig;
  };
  
  // Configuration sections
  trading: TradingConfig;
  probabilityModel: ProbabilityModelConfig;
  dynamicTrading: DynamicTradingConfig;
  executionMode: "paper" | "live";
  apiKeys: ApiKeysConfig;
  
  // UI state
  expandedSections: {
    trading: boolean;
    probabilityModel: boolean;
    apiKeys: boolean;
    polymarket: boolean;
  };
  
  // Form state
  isDirty: boolean;
  isSaving: boolean;
  errors: Record<string, string>;
}
```

---

### 5. API Integration

**API Calls**:
```typescript
// Get current configuration
GET /api/config

// Get engine status and config
GET /api/engine/config
GET /api/status

// Update configuration
PUT /api/config

// Validate configuration
POST /api/config/validate

// Engine control
POST /api/engine/start
POST /api/engine/stop
POST /api/engine/restart

// Utility
POST /api/config/reload
POST /api/config/reset
GET /api/config/defaults
```

**Error Handling**:
- Show validation errors inline
- Display API errors in toast/alert
- Handle network errors gracefully
- Show loading states during operations

---

### 6. User Experience Flow

#### Loading Configuration
1. Page loads → Show loading spinner
2. Fetch `/api/config` and `/api/engine/config`
3. Populate form fields
4. Show collapsed sections with summaries
5. Display engine status

#### Updating Configuration
1. User expands section
2. User modifies values
3. Form validates on blur/change
4. "Save" button becomes enabled (isDirty = true)
5. User clicks "Save"
6. Show loading state
7. Validate via `/api/config/validate`
8. If valid, save via `PUT /api/config`
9. Show success message
10. If engine running, show "Restart required" notice

#### Starting Engine
1. User configures settings
2. User clicks "Start Engine"
3. Show confirmation dialog with config summary
4. Send `POST /api/engine/start` with full config
5. Show loading state
6. Poll `/api/status` until engine is running
7. Show success message
8. Update engine status display

#### Stopping Engine
1. User clicks "Stop Engine"
2. Show confirmation dialog
3. Send `POST /api/engine/stop`
4. Show loading state
5. Poll `/api/status` until engine is stopped
6. Show success message

---

## 📝 Implementation Checklist

### Backend/API
- [ ] Create `EngineService` class
- [ ] Implement engine start/stop/restart logic
- [ ] Create `ConfigService` class
- [ ] Implement config read/write/validate
- [ ] Create `/api/engine/*` endpoints
- [ ] Create `/api/config/*` endpoints
- [ ] Modify `DynamicTradingEngine` to accept config params
- [ ] Add config storage (JSON file for engine config)
- [ ] Add validation rules
- [ ] Add error handling
- [ ] Write unit tests

### Frontend
- [ ] Create `ConfigPage` component
- [ ] Create `CollapsibleSection` component
- [ ] Create `EngineControl` component
- [ ] Create form components for each section
- [ ] Implement state management
- [ ] Implement API integration
- [ ] Add form validation
- [ ] Add error handling
- [ ] Add loading states
- [ ] Add success/error notifications
- [ ] Style collapsible sections
- [ ] Add tooltips for all fields
- [ ] Test all user flows

---

## 🎨 UI/UX Considerations

### Collapsible Sections
- **Default State**: All advanced sections collapsed
- **Summary View**: Show key values when collapsed (e.g., "Edge: 5.0%, Kelly: 10.0%")
- **Expand Animation**: Smooth slide-down animation
- **Icon**: ▼ when collapsed, ▲ when expanded
- **Visual Hierarchy**: Use different background colors or borders

### Form Fields
- **Tooltips**: ⓘ icon next to each field with explanation
- **Validation**: Show errors inline below fields
- **Input Types**: Use appropriate inputs (number, select, text, etc.)
- **Formatting**: Format currency, percentages appropriately
- **Placeholders**: Show default values or examples

### Engine Control
- **Status Indicator**: Color-coded (green = running, red = stopped)
- **Action Buttons**: Disable when appropriate (e.g., can't stop if not running)
- **Confirmation Dialogs**: For destructive actions (stop, restart)
- **Loading States**: Show spinner during operations
- **Real-time Updates**: Poll status or use WebSocket for updates

### Save/Reset Actions
- **Save Button**: Only enabled when form is dirty
- **Reset Button**: Show confirmation dialog
- **Reload Button**: Fetch latest from disk
- **Success Feedback**: Toast notification or inline message
- **Error Feedback**: Show error message with details

---

## 🔐 Security Considerations

### API Key Handling
- **Masking**: Show only last 4 characters (e.g., `****1234`)
- **Show/Hide Toggle**: Allow user to reveal full key
- **No Logging**: Never log full API keys
- **Secure Storage**: Store in `.env` file (git-ignored)

### Validation
- **Client-side**: Immediate feedback for user
- **Server-side**: Always validate on backend
- **Sanitization**: Sanitize all inputs
- **Type Checking**: Validate types and ranges

### Permissions
- **Future**: Add authentication/authorization
- **Audit Log**: Log all configuration changes
- **Change History**: Track who changed what and when

---

## 🚀 Future Enhancements

### Phase 2
- [ ] Configuration presets (e.g., "Conservative", "Aggressive")
- [ ] Configuration import/export (JSON)
- [ ] Configuration change history
- [ ] Rollback to previous configuration

### Phase 3
- [ ] Polymarket account setup UI
- [ ] Live trading mode switch with validation
- [ ] API key rotation
- [ ] Multi-user support with permissions

---

## ✅ Success Criteria

### Backend
- ✅ Can start/stop/restart engine with configuration
- ✅ Can read/write configuration via API
- ✅ Configuration validation works correctly
- ✅ Engine uses provided configuration (not global config)
- ✅ All endpoints return proper errors

### Frontend
- ✅ Configuration page loads and displays current settings
- ✅ Collapsible sections work smoothly
- ✅ Can update configuration and save
- ✅ Can start/stop/restart engine from UI
- ✅ Form validation provides clear feedback
- ✅ All tooltips and help text are present
- ✅ Error handling is user-friendly

---

**Last Updated**: November 17, 2025

