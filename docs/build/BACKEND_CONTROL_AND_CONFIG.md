# Backend Control & Configuration Management

**Date**: November 17, 2025  
**Purpose**: Specification for frontend control of backend services and configuration management

---

## 🎯 Overview

This document outlines:
1. **Current capabilities** - What's available now
2. **Missing controls** - What needs to be added for frontend control
3. **Configuration management** - What can be configured from the frontend
4. **Future features** - Polymarket account setup and live trading mode

---

## 📋 Current State

### ✅ What's Available Now

#### 1. **Status Monitoring** (Already Implemented)
- **Endpoint**: `GET /api/status`
- **Returns**:
  - Trading engine running status (PID, elapsed time)
  - Execution mode (PAPER/LIVE)
  - Cycle interval and next cycle time
  - Data collection status
- **Frontend Access**: ✅ Yes

#### 2. **Backtest Control** (Already Implemented)
- **Endpoint**: `POST /api/backtest/run`
- **Accepts**: All trading and probability model parameters
- **Returns**: Job ID, status, results
- **Frontend Access**: ✅ Yes
- **Note**: Backtest accepts parameters per-run, but paper/live trading uses global config

#### 3. **Configuration Reading** (Partial)
- **Current**: Config is read from `.env` and `config.local.yaml` at startup
- **Frontend Access**: ❌ No direct API endpoint
- **Workaround**: Status endpoint returns some config values (execution_mode, interval_seconds)
- **Problem**: Paper/live trading engine uses global config that can't be changed without restart

### ⚠️ **Key Issue: Configuration Mismatch**

**Backtesting**:
- ✅ Accepts all parameters per-run (model_mode, zeus_likely_pct, edge_min, kelly_cap, etc.)
- ✅ Can test different configurations without changing global settings

**Paper/Live Trading**:
- ❌ Uses global config from `.env` file
- ❌ Can't change settings without editing `.env` and restarting engine
- ❌ No way to adjust probability model or trading parameters from frontend

**Solution Needed**:
- ✅ Make paper/live trading use the same configuration options as backtesting
- ✅ Allow changing these settings from the frontend config page
- ✅ Apply changes to running engine (or require restart with new settings)

---

## ❌ Missing Controls (Need to Add)

### 1. **Trading Engine Control**

**Current**: Engine must be started/stopped manually via command line, uses global config

**Needed**:
- ✅ Start dynamic trading engine **with configuration parameters**
- ✅ Stop dynamic trading engine
- ✅ Restart dynamic trading engine **with new configuration**
- ✅ Get engine status (already exists)
- ✅ Apply configuration changes to running engine (or require restart)

**Implementation**:
```python
# backend/api/services/engine_service.py
class EngineService:
    def start_engine(
        self,
        stations: List[str],
        interval_seconds: int,
        lookahead_days: int,
        # Trading parameters (same as backtest)
        edge_min: float,
        fee_bp: int,
        slippage_bp: int,
        kelly_cap: float,
        per_market_cap: float,
        liquidity_min_usd: float,
        daily_bankroll_cap: float,
        # Probability model parameters (same as backtest)
        model_mode: str,
        zeus_likely_pct: float,
        zeus_possible_pct: float,
    ) -> Dict
    
    def stop_engine(self) -> Dict
    
    def restart_engine(self, **config_params) -> Dict  # Same params as start
```

**API Endpoints**:
- `POST /api/engine/start` - Start trading engine with full configuration
- `POST /api/engine/stop` - Stop trading engine
- `POST /api/engine/restart` - Restart trading engine with new configuration
- `GET /api/engine/status` - Get engine status (already exists via `/api/status`)
- `GET /api/engine/config` - Get current engine configuration (what it's using now)

---

### 2. **Configuration Management**

**Current**: Configuration is read-only from `.env` file

**Needed**:
- ✅ Read current configuration
- ✅ Update configuration values
- ✅ Validate configuration before saving
- ✅ Reload configuration without restart

**Implementation**:
```python
# backend/api/services/config_service.py
class ConfigService:
    def get_config(self) -> Dict[str, Any]
    def update_config(self, updates: Dict[str, Any]) -> Dict[str, Any]
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]
    def reload_config(self) -> Dict[str, Any]
```

**API Endpoints**:
- `GET /api/config` - Get current configuration
- `PUT /api/config` - Update configuration
- `POST /api/config/reload` - Reload configuration from disk
- `POST /api/config/validate` - Validate configuration without saving

---

### 3. **Polymarket Account Configuration** (Future)

**Current**: Not implemented

**Needed**:
- ✅ Store Polymarket API credentials
- ✅ Test connection to Polymarket
- ✅ Validate wallet address
- ✅ Switch between paper and live trading

**Implementation**:
```python
# backend/api/services/polymarket_service.py
class PolymarketConfigService:
    def get_account_config(self) -> Dict[str, Any]
    def update_account_config(self, api_key: str, private_key: str, wallet_address: str) -> Dict
    def test_connection(self) -> Dict[str, Any]
    def validate_wallet(self, wallet_address: str) -> Dict[str, Any]
```

**API Endpoints**:
- `GET /api/polymarket/config` - Get Polymarket account config
- `PUT /api/polymarket/config` - Update Polymarket account config
- `POST /api/polymarket/test` - Test Polymarket connection
- `POST /api/polymarket/validate-wallet` - Validate wallet address

---

## 🔧 Configuration Options

### Trading Configuration

| Option | Type | Default | Description | Editable |
|--------|------|---------|-------------|----------|
| `active_stations` | `List[str]` | `["EGLC", "KLGA"]` | Stations to trade | ✅ Yes |
| `edge_min` | `float` | `0.05` | Minimum edge to trade (5%) | ✅ Yes |
| `fee_bp` | `int` | `50` | Fees in basis points (0.50%) | ✅ Yes |
| `slippage_bp` | `int` | `30` | Slippage in basis points | ✅ Yes |
| `kelly_cap` | `float` | `0.10` | Max Kelly fraction (10%) | ✅ Yes |
| `daily_bankroll_cap` | `float` | `3000.0` | Daily bankroll limit (USD) | ✅ Yes |
| `per_market_cap` | `float` | `500.0` | Per-market position limit (USD) | ✅ Yes |
| `liquidity_min_usd` | `float` | `1000.0` | Minimum liquidity required (USD) | ✅ Yes |

### Probability Model Configuration

| Option | Type | Default | Description | Editable |
|--------|------|---------|-------------|----------|
| `model_mode` | `str` | `"spread"` | Probability model: `spread` or `bands` | ✅ Yes |
| `zeus_likely_pct` | `float` | `0.80` | Zeus likely confidence level (80%) | ✅ Yes |
| `zeus_possible_pct` | `float` | `0.95` | Zeus possible confidence level (95%) | ✅ Yes |
| `sigma_default` | `float` | `2.0` | Default uncertainty (std dev in °F) | ✅ Yes |
| `sigma_min` | `float` | `0.5` | Minimum allowed sigma | ✅ Yes |
| `sigma_max` | `float` | `10.0` | Maximum allowed sigma | ✅ Yes |

### Dynamic Trading Configuration

| Option | Type | Default | Description | Editable |
|--------|------|---------|-------------|----------|
| `dynamic_interval_seconds` | `int` | `900` | Evaluation interval (15 minutes) | ✅ Yes |
| `dynamic_lookahead_days` | `int` | `2` | Days ahead to check for markets | ✅ Yes |

### Execution Mode

| Option | Type | Default | Description | Editable |
|--------|------|---------|-------------|----------|
| `execution_mode` | `str` | `"paper"` | Execution mode: `paper` or `live` | ✅ Yes (with validation) |

### API Keys (Sensitive)

| Option | Type | Default | Description | Editable |
|--------|------|---------|-------------|----------|
| `zeus_api_key` | `str` | `""` | Zeus API key | ✅ Yes (masked) |
| `polymarket_api_key` | `str` | `""` | Polymarket API key | ✅ Yes (masked) |
| `polymarket_private_key` | `str` | `""` | Polymarket private key | ✅ Yes (masked) |
| `polymarket_wallet_address` | `str` | `""` | Polymarket wallet address | ✅ Yes |

---

## 🎨 Frontend Config Page Design

### Page Structure

```
┌─────────────────────────────────────────────────────────────┐
│  Configuration                                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─ Trading Settings ───────────────────────────────────┐  │
│  │                                                       │  │
│  │  Active Stations: [EGLC] [KLGA] [+ Add]             │  │
│  │  Minimum Edge: [5.0] %  ⓘ                           │  │
│  │  Fee (bp): [50]  ⓘ                                   │  │
│  │  Slippage (bp): [30]  ⓘ                             │  │
│  │  Kelly Cap: [10.0] %  ⓘ                             │  │
│  │  Daily Bankroll Cap: [$3000.00]  ⓘ                  │  │
│  │  Per-Market Cap: [$500.00]  ⓘ                       │  │
│  │  Min Liquidity: [$1000.00]  ⓘ                       │  │
│  │                                                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─ Probability Model ──────────────────────────────────┐  │
│  │                                                       │  │
│  │  Model Mode: [Spread ▼]  ⓘ                          │  │
│  │  Zeus Likely %: [80.0] %  ⓘ                         │  │
│  │  Zeus Possible %: [95.0] %  ⓘ                       │  │
│  │  Sigma Default: [2.0] °F  ⓘ                         │  │
│  │  Sigma Min: [0.5] °F  ⓘ                             │  │
│  │  Sigma Max: [10.0] °F  ⓘ                            │  │
│  │                                                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─ Dynamic Trading ────────────────────────────────────┐  │
│  │                                                       │  │
│  │  Evaluation Interval: [15] minutes  ⓘ               │  │
│  │  Lookahead Days: [2] days  ⓘ                        │  │
│  │                                                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─ Execution Mode ─────────────────────────────────────┐  │
│  │                                                       │  │
│  │  Mode: ○ Paper  ● Live  ⓘ                           │  │
│  │  ⚠️  Live trading requires Polymarket account setup  │  │
│  │                                                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─ API Keys (Sensitive) ───────────────────────────────┐  │
│  │                                                       │  │
│  │  Zeus API Key: [••••••••••••] [Show] [Test]         │  │
│  │  Polymarket API Key: [••••••••••••] [Show] [Test]   │  │
│  │  Polymarket Private Key: [••••••••••••] [Show]      │  │
│  │  Wallet Address: [0x...] [Validate]                 │  │
│  │                                                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─ Trading Engine Control ─────────────────────────────┐  │
│  │                                                       │  │
│  │  Status: ● RUNNING (PID: 12345)                      │  │
│  │  [Stop] [Restart]                                    │  │
│  │                                                       │  │
│  │  Or:                                                 │  │
│  │  Status: ○ STOPPED                                   │  │
│  │  [Start]                                             │  │
│  │                                                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  [Save Configuration] [Reset to Defaults] [Reload from Disk]│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔐 Security Considerations

### 1. **API Key Storage**
- ✅ Store in `.env` file (git-ignored)
- ✅ Mask in API responses (show only last 4 characters)
- ✅ Require authentication for updates
- ✅ Validate format before saving

### 2. **Live Trading Mode**
- ✅ Require explicit confirmation before enabling
- ✅ Require Polymarket account setup
- ✅ Show warning banner when live mode is active
- ✅ Log all configuration changes

### 3. **Configuration Validation**
- ✅ Validate all numeric ranges
- ✅ Validate station codes against registry
- ✅ Test API connections before saving
- ✅ Prevent invalid combinations (e.g., live mode without API keys)

---

## 📝 Implementation Plan

### Phase 1: Engine Control (Immediate)

**Files to Create**:
- `backend/api/services/engine_service.py` - Engine control logic
- `backend/api/routes/engine.py` - Engine control endpoints

**Files to Modify**:
- `backend/api/main.py` - Register new router

**Endpoints**:
- `POST /api/engine/start`
- `POST /api/engine/stop`
- `POST /api/engine/restart`

---

### Phase 2: Configuration Management (Immediate)

**Files to Create**:
- `backend/api/services/config_service.py` - Config read/write logic
- `backend/api/routes/config.py` - Config endpoints

**Files to Modify**:
- `core/config.py` - Add `reload()` method
- `backend/api/main.py` - Register new router

**Endpoints**:
- `GET /api/config`
- `PUT /api/config`
- `POST /api/config/reload`
- `POST /api/config/validate`

---

### Phase 3: Frontend Config Page (Immediate)

**Components**:
- Config page with all sections
- Form validation
- Save/Reset/Reload buttons
- Engine control panel
- API key management (masked)

---

### Phase 4: Polymarket Account Setup (Future)

**Files to Create**:
- `backend/api/services/polymarket_service.py` - Polymarket account management
- `backend/api/routes/polymarket_config.py` - Polymarket config endpoints

**Endpoints**:
- `GET /api/polymarket/config`
- `PUT /api/polymarket/config`
- `POST /api/polymarket/test`
- `POST /api/polymarket/validate-wallet`

---

## 🚀 API Endpoint Specifications

### Engine Control

#### Start Engine
```http
POST /api/engine/start
Content-Type: application/json

{
  "stations": ["EGLC", "KLGA"],
  "interval_seconds": 900,
  "lookahead_days": 2,
  // Trading parameters (same as backtest)
  "edge_min": 0.05,
  "fee_bp": 50,
  "slippage_bp": 30,
  "kelly_cap": 0.10,
  "per_market_cap": 500.0,
  "liquidity_min_usd": 1000.0,
  "daily_bankroll_cap": 3000.0,
  // Probability model parameters (same as backtest)
  "model_mode": "spread",
  "zeus_likely_pct": 0.80,
  "zeus_possible_pct": 0.95
}

Response:
{
  "success": true,
  "message": "Trading engine started",
  "pid": 12345,
  "status": "running",
  "config": {
    // Echo back the configuration being used
  }
}
```

#### Stop Engine
```http
POST /api/engine/stop

Response:
{
  "success": true,
  "message": "Trading engine stopped",
  "pid": 12345
}
```

#### Restart Engine
```http
POST /api/engine/restart
Content-Type: application/json

{
  "stations": ["EGLC", "KLGA"],
  "interval_seconds": 900,
  "lookahead_days": 2,
  // Trading parameters (same as backtest)
  "edge_min": 0.05,
  "fee_bp": 50,
  "slippage_bp": 30,
  "kelly_cap": 0.10,
  "per_market_cap": 500.0,
  "liquidity_min_usd": 1000.0,
  "daily_bankroll_cap": 3000.0,
  // Probability model parameters (same as backtest)
  "model_mode": "spread",
  "zeus_likely_pct": 0.80,
  "zeus_possible_pct": 0.95
}

Response:
{
  "success": true,
  "message": "Trading engine restarted with new configuration",
  "pid": 12346,
  "status": "running",
  "config": {
    // Echo back the configuration being used
  }
}
```

#### Get Engine Configuration
```http
GET /api/engine/config

Response:
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
```

---

### Configuration Management

#### Get Configuration
```http
GET /api/config

Response:
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
    "zeus_api_key": "****1234",  // Masked
    "polymarket_api_key": "****5678",  // Masked
    "polymarket_private_key": "****9012",  // Masked
    "polymarket_wallet_address": "0x1234..."  // Full address
  }
}
```

#### Update Configuration
```http
PUT /api/config
Content-Type: application/json

{
  "trading": {
    "edge_min": 0.06,
    "kelly_cap": 0.12
  },
  "dynamic_trading": {
    "interval_seconds": 1800
  }
}

Response:
{
  "success": true,
  "message": "Configuration updated",
  "requires_restart": false,  // or true if engine needs restart
  "updated_fields": ["trading.edge_min", "trading.kelly_cap", "dynamic_trading.interval_seconds"]
}
```

#### Validate Configuration
```http
POST /api/config/validate
Content-Type: application/json

{
  "trading": {
    "edge_min": 0.06
  }
}

Response:
{
  "valid": true,
  "errors": []
}

// Or if invalid:
{
  "valid": false,
  "errors": [
    "edge_min must be between 0.01 and 0.50",
    "kelly_cap must be between 0.01 and 0.50"
  ]
}
```

---

## ✅ Summary

### What We Have:
- ✅ Status monitoring (`/api/status`)
- ✅ Backtest control (`/api/backtest/run`) - **Accepts all parameters per-run**
- ⚠️ Paper/live trading - **Uses global config only, can't change without restart**

### What We Need to Add:
- ❌ Engine control (start/stop/restart) - **With full configuration parameters**
- ❌ Configuration read/write - **For both global config and engine config**
- ❌ Configuration validation - **Same validation as backtest**
- ❌ Frontend config page - **Same fields as backtest config UI**
- ❌ Apply config to running engine - **Or require restart with new settings**

### Key Requirement:
**Paper/live trading must use the same configuration options as backtesting:**
- Probability model settings (model_mode, zeus_likely_pct, zeus_possible_pct)
- Trading parameters (edge_min, fee_bp, slippage_bp, kelly_cap, etc.)
- Risk limits (per_market_cap, liquidity_min_usd, daily_bankroll_cap)

### Future Features:
- 🔮 Polymarket account setup
- 🔮 Live trading mode switch
- 🔮 API key management UI
- 🔮 Configuration change history

---

**Next Steps**:
1. Implement `EngineService` and endpoints
2. Implement `ConfigService` and endpoints
3. Build frontend config page
4. Add validation and security
5. Test end-to-end

---

**Last Updated**: November 17, 2025

