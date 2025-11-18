# Frontend Configuration Page Implementation - Staged Approach

**Date**: November 17, 2025  
**Purpose**: Detailed staged implementation plan for frontend configuration management page

**Backend Status**: ✅ Complete (Stages 1-4 implemented)  
**API Endpoints**: All endpoints available and tested

---

## 🎯 Overview

This document outlines the frontend implementation in **5 stages**, building from basic UI to advanced features.

**Stages**:
1. **Stage 1**: Basic Configuration Page Structure & API Integration
2. **Stage 2**: Engine Control Component
3. **Stage 3**: Configuration Forms (Collapsible Sections)
4. **Stage 4**: Form Validation & Error Handling
5. **Stage 5**: Real-time Updates & Polish

---

## 📋 Prerequisites

Before starting, ensure:
- ✅ Backend API is running (`http://localhost:8000`)
- ✅ All backend endpoints are available (see `/docs`)
- ✅ Frontend project is set up (React/Streamlit/etc.)
- ✅ API client library is configured (fetch/axios/etc.)

---

## 🚀 Stage 1: Basic Configuration Page Structure & API Integration

**Goal**: Create basic page structure and connect to backend API

**Estimated Time**: 2-3 hours

### 1.1 Create Configuration Page Component

**File**: `src/pages/ConfigurationPage.tsx` (or equivalent)

**Basic Structure**:
```typescript
import React, { useState, useEffect } from 'react';
import { fetchConfig, updateConfig } from '../services/api';

export const ConfigurationPage: React.FC = () => {
  const [config, setConfig] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      setLoading(true);
      const data = await fetchConfig();
      setConfig(data);
      setError(null);
    } catch (err) {
      setError('Failed to load configuration');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!config) return <div>No configuration available</div>;

  return (
    <div className="config-page">
      <h1>Configuration</h1>
      {/* Content will be added in later stages */}
    </div>
  );
};
```

### 1.2 Create API Service

**File**: `src/services/configApi.ts` (or equivalent)

**Implementation**:
```typescript
const API_BASE = 'http://localhost:8000';

export interface TradingConfig {
  active_stations: string[];
  edge_min: number;
  fee_bp: number;
  slippage_bp: number;
  kelly_cap: number;
  per_market_cap: number;
  liquidity_min_usd: number;
  daily_bankroll_cap: number;
}

export interface ProbabilityModelConfig {
  model_mode: 'spread' | 'bands';
  zeus_likely_pct: number;
  zeus_possible_pct: number;
  sigma_default?: number;
  sigma_min?: number;
  sigma_max?: number;
}

export interface DynamicTradingConfig {
  interval_seconds: number;
  lookahead_days: number;
}

export interface FullConfig {
  trading: TradingConfig;
  probability_model: ProbabilityModelConfig;
  dynamic_trading: DynamicTradingConfig;
  execution_mode: 'paper' | 'live';
  api_keys: {
    zeus_api_key: string;
    polymarket_api_key: string;
    polymarket_private_key: string;
    polymarket_wallet_address: string;
  };
}

// Get current configuration
export const fetchConfig = async (): Promise<FullConfig> => {
  const response = await fetch(`${API_BASE}/api/config`);
  if (!response.ok) throw new Error('Failed to fetch config');
  return response.json();
};

// Update configuration
export const updateConfig = async (updates: Partial<FullConfig>): Promise<any> => {
  const response = await fetch(`${API_BASE}/api/config`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail?.message || 'Failed to update config');
  }
  return response.json();
};

// Validate configuration
export const validateConfig = async (config: Partial<FullConfig>): Promise<{ valid: boolean; errors: string[] }> => {
  const response = await fetch(`${API_BASE}/api/config/validate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  });
  if (!response.ok) throw new Error('Failed to validate config');
  return response.json();
};

// Get default configuration
export const fetchDefaultConfig = async (): Promise<FullConfig> => {
  const response = await fetch(`${API_BASE}/api/config/defaults`);
  if (!response.ok) throw new Error('Failed to fetch defaults');
  return response.json();
};

// Reset to defaults
export const resetConfig = async (): Promise<any> => {
  const response = await fetch(`${API_BASE}/api/config/reset`, {
    method: 'POST',
  });
  if (!response.ok) throw new Error('Failed to reset config');
  return response.json();
};
```

### 1.3 Create Engine Control API Service

**File**: `src/services/engineApi.ts` (or equivalent)

**Implementation**:
```typescript
const API_BASE = 'http://localhost:8000';

export interface StartEngineRequest {
  stations: string[];
  interval_seconds: number;
  lookahead_days: number;
  trading: {
    edge_min: number;
    fee_bp: number;
    slippage_bp: number;
    kelly_cap: number;
    per_market_cap: number;
    liquidity_min_usd: number;
    daily_bankroll_cap: number;
  };
  probability_model: {
    model_mode: 'spread' | 'bands';
    zeus_likely_pct: number;
    zeus_possible_pct: number;
  };
}

// Start engine
export const startEngine = async (request: StartEngineRequest): Promise<any> => {
  const response = await fetch(`${API_BASE}/api/engine/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to start engine');
  }
  return response.json();
};

// Stop engine
export const stopEngine = async (): Promise<any> => {
  const response = await fetch(`${API_BASE}/api/engine/stop`, {
    method: 'POST',
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to stop engine');
  }
  return response.json();
};

// Restart engine
export const restartEngine = async (request: StartEngineRequest): Promise<any> => {
  const response = await fetch(`${API_BASE}/api/engine/restart`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to restart engine');
  }
  return response.json();
};

// Get engine configuration
export const fetchEngineConfig = async (): Promise<any> => {
  const response = await fetch(`${API_BASE}/api/engine/config`);
  if (!response.ok) {
    if (response.status === 404) return null;
    throw new Error('Failed to fetch engine config');
  }
  return response.json();
};

// Get engine status (from status endpoint)
export const fetchEngineStatus = async (): Promise<any> => {
  const response = await fetch(`${API_BASE}/api/status`);
  if (!response.ok) throw new Error('Failed to fetch status');
  return response.json();
};
```

### 1.4 Testing

**Manual Testing**:
1. Load configuration page
2. Verify API calls are made
3. Verify configuration data is displayed
4. Check error handling for API failures

**Expected Results**:
- ✅ Page loads and fetches configuration
- ✅ Configuration data is displayed
- ✅ Error messages shown on API failure
- ✅ Loading states work correctly

---

## 🎛️ Stage 2: Engine Control Component

**Goal**: Create engine control UI with start/stop/restart functionality

**Estimated Time**: 2-3 hours

### 2.1 Create Engine Control Component

**File**: `src/components/EngineControl.tsx`

**Implementation**:
```typescript
import React, { useState, useEffect } from 'react';
import { fetchEngineStatus, startEngine, stopEngine, restartEngine } from '../services/engineApi';
import { fetchConfig } from '../services/configApi';
import { FullConfig } from '../services/configApi';

export const EngineControl: React.FC = () => {
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [config, setConfig] = useState<FullConfig | null>(null);

  useEffect(() => {
    loadStatus();
    loadConfig();
    // Poll status every 5 seconds
    const interval = setInterval(loadStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadStatus = async () => {
    try {
      const data = await fetchEngineStatus();
      setStatus(data);
      setError(null);
    } catch (err) {
      setError('Failed to load engine status');
    }
  };

  const loadConfig = async () => {
    try {
      const data = await fetchConfig();
      setConfig(data);
    } catch (err) {
      // Handle error
    }
  };

  const handleStart = async () => {
    if (!config) return;
    
    setLoading(true);
    setError(null);
    try {
      const request = {
        stations: config.trading.active_stations,
        interval_seconds: config.dynamic_trading.interval_seconds,
        lookahead_days: config.dynamic_trading.lookahead_days,
        trading: config.trading,
        probability_model: config.probability_model,
      };
      await startEngine(request);
      await loadStatus();
    } catch (err: any) {
      setError(err.message || 'Failed to start engine');
    } finally {
      setLoading(false);
    }
  };

  const handleStop = async () => {
    if (!confirm('Are you sure you want to stop the trading engine?')) return;
    
    setLoading(true);
    setError(null);
    try {
      await stopEngine();
      await loadStatus();
    } catch (err: any) {
      setError(err.message || 'Failed to stop engine');
    } finally {
      setLoading(false);
    }
  };

  const handleRestart = async () => {
    if (!config) return;
    if (!confirm('Are you sure you want to restart the trading engine?')) return;
    
    setLoading(true);
    setError(null);
    try {
      const request = {
        stations: config.trading.active_stations,
        interval_seconds: config.dynamic_trading.interval_seconds,
        lookahead_days: config.dynamic_trading.lookahead_days,
        trading: config.trading,
        probability_model: config.probability_model,
      };
      await restartEngine(request);
      await loadStatus();
    } catch (err: any) {
      setError(err.message || 'Failed to restart engine');
    } finally {
      setLoading(false);
    }
  };

  const isRunning = status?.trading_engine?.running || false;
  const executionMode = status?.execution_mode || 'PAPER';
  const nextCycleSeconds = status?.cycle?.seconds_until_next;

  return (
    <div className="engine-control">
      <h2>⚙️ Trading Engine Control</h2>
      
      <div className="status-display">
        <div className="status-indicator">
          <span className={`status-dot ${isRunning ? 'running' : 'stopped'}`}>
            {isRunning ? '●' : '○'}
          </span>
          <span className="status-text">
            {isRunning ? 'RUNNING' : 'STOPPED'}
            {status?.trading_engine?.pid && ` (PID: ${status.trading_engine.pid})`}
          </span>
        </div>
        
        <div className="execution-mode">
          Mode: <strong>{executionMode}</strong>
        </div>
        
        {isRunning && nextCycleSeconds !== null && (
          <div className="next-cycle">
            Next cycle in: <strong>{formatSeconds(nextCycleSeconds)}</strong>
          </div>
        )}
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <div className="control-buttons">
        {isRunning ? (
          <>
            <button onClick={handleStop} disabled={loading}>
              {loading ? 'Stopping...' : 'Stop Engine'}
            </button>
            <button onClick={handleRestart} disabled={loading}>
              {loading ? 'Restarting...' : 'Restart Engine'}
            </button>
          </>
        ) : (
          <button onClick={handleStart} disabled={loading || !config}>
            {loading ? 'Starting...' : 'Start Engine'}
          </button>
        )}
      </div>
    </div>
  );
};

const formatSeconds = (seconds: number): string => {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}m ${secs}s`;
};
```

### 2.2 Add to Configuration Page

**Update**: `src/pages/ConfigurationPage.tsx`

```typescript
import { EngineControl } from '../components/EngineControl';

// Add to return statement:
<EngineControl />
```

### 2.3 Testing

**Manual Testing**:
1. Test start engine button
2. Test stop engine button
3. Test restart engine button
4. Verify status updates in real-time
5. Test error handling

**Expected Results**:
- ✅ Engine can be started/stopped/restarted
- ✅ Status updates correctly
- ✅ Buttons are disabled during operations
- ✅ Error messages are displayed
- ✅ Confirmation dialogs work

---

## 📝 Stage 3: Configuration Forms (Collapsible Sections)

**Goal**: Create collapsible form sections for all configuration options

**Estimated Time**: 4-5 hours

### 3.1 Create Collapsible Section Component

**File**: `src/components/CollapsibleSection.tsx`

**Implementation**:
```typescript
import React, { useState } from 'react';

interface CollapsibleSectionProps {
  title: string;
  defaultExpanded?: boolean;
  summary?: string;
  children: React.ReactNode;
}

export const CollapsibleSection: React.FC<CollapsibleSectionProps> = ({
  title,
  defaultExpanded = false,
  summary,
  children,
}) => {
  const [expanded, setExpanded] = useState(defaultExpanded);

  return (
    <div className="collapsible-section">
      <div 
        className="section-header"
        onClick={() => setExpanded(!expanded)}
        style={{ cursor: 'pointer' }}
      >
        <span className="section-icon">{expanded ? '▲' : '▼'}</span>
        <span className="section-title">{title}</span>
        {!expanded && summary && (
          <span className="section-summary">{summary}</span>
        )}
      </div>
      
      {expanded && (
        <div className="section-content">
          {children}
        </div>
      )}
    </div>
  );
};
```

### 3.2 Create Trading Parameters Form

**File**: `src/components/TradingParamsForm.tsx`

**Implementation**:
```typescript
import React from 'react';
import { TradingConfig } from '../services/configApi';

interface TradingParamsFormProps {
  config: TradingConfig;
  onChange: (updates: Partial<TradingConfig>) => void;
  errors?: Record<string, string>;
}

export const TradingParamsForm: React.FC<TradingParamsFormProps> = ({
  config,
  onChange,
  errors = {},
}) => {
  const summary = `Edge: ${(config.edge_min * 100).toFixed(1)}%, Kelly: ${(config.kelly_cap * 100).toFixed(1)}%`;

  return (
    <div className="trading-params-form">
      <div className="form-group">
        <label>
          Active Stations
          <span className="tooltip-icon" title="Comma-separated station codes (e.g., EGLC,KLGA)">
            ⓘ
          </span>
        </label>
        <input
          type="text"
          value={config.active_stations.join(',')}
          onChange={(e) => onChange({
            active_stations: e.target.value.split(',').map(s => s.trim()).filter(Boolean)
          })}
        />
        {errors.active_stations && (
          <span className="error">{errors.active_stations}</span>
        )}
      </div>

      <div className="form-group">
        <label>
          Minimum Edge (%)
          <span className="tooltip-icon" title="Minimum edge required to place a trade (0.01 = 1%, 0.05 = 5%)">
            ⓘ
          </span>
        </label>
        <input
          type="number"
          step="0.01"
          min="0.01"
          max="0.50"
          value={config.edge_min}
          onChange={(e) => onChange({ edge_min: parseFloat(e.target.value) })}
        />
        {errors.edge_min && (
          <span className="error">{errors.edge_min}</span>
        )}
      </div>

      <div className="form-group">
        <label>
          Fee (basis points)
          <span className="tooltip-icon" title="Effective trading fees in basis points (50 = 0.50%)">
            ⓘ
          </span>
        </label>
        <input
          type="number"
          min="0"
          max="1000"
          value={config.fee_bp}
          onChange={(e) => onChange({ fee_bp: parseInt(e.target.value) })}
        />
        {errors.fee_bp && (
          <span className="error">{errors.fee_bp}</span>
        )}
      </div>

      <div className="form-group">
        <label>
          Slippage (basis points)
          <span className="tooltip-icon" title="Assumed slippage in basis points (30 = 0.30%)">
            ⓘ
          </span>
        </label>
        <input
          type="number"
          min="0"
          max="1000"
          value={config.slippage_bp}
          onChange={(e) => onChange({ slippage_bp: parseInt(e.target.value) })}
        />
        {errors.slippage_bp && (
          <span className="error">{errors.slippage_bp}</span>
        )}
      </div>

      <div className="form-group">
        <label>
          Kelly Cap (%)
          <span className="tooltip-icon" title="Maximum Kelly fraction per decision (0.10 = 10% of bankroll)">
            ⓘ
          </span>
        </label>
        <input
          type="number"
          step="0.01"
          min="0.01"
          max="0.50"
          value={config.kelly_cap}
          onChange={(e) => onChange({ kelly_cap: parseFloat(e.target.value) })}
        />
        {errors.kelly_cap && (
          <span className="error">{errors.kelly_cap}</span>
        )}
      </div>

      <div className="form-group">
        <label>
          Daily Bankroll Cap ($)
          <span className="tooltip-icon" title="Daily bankroll limit in USD">
            ⓘ
          </span>
        </label>
        <input
          type="number"
          step="0.01"
          min="0"
          value={config.daily_bankroll_cap}
          onChange={(e) => onChange({ daily_bankroll_cap: parseFloat(e.target.value) })}
        />
        {errors.daily_bankroll_cap && (
          <span className="error">{errors.daily_bankroll_cap}</span>
        )}
      </div>

      <div className="form-group">
        <label>
          Per-Market Cap ($)
          <span className="tooltip-icon" title="Per-market position limit in USD">
            ⓘ
          </span>
        </label>
        <input
          type="number"
          step="0.01"
          min="0"
          value={config.per_market_cap}
          onChange={(e) => onChange({ per_market_cap: parseFloat(e.target.value) })}
        />
        {errors.per_market_cap && (
          <span className="error">{errors.per_market_cap}</span>
        )}
      </div>

      <div className="form-group">
        <label>
          Min Liquidity ($)
          <span className="tooltip-icon" title="Minimum market liquidity required to trade (USD)">
            ⓘ
          </span>
        </label>
        <input
          type="number"
          step="0.01"
          min="0"
          value={config.liquidity_min_usd}
          onChange={(e) => onChange({ liquidity_min_usd: parseFloat(e.target.value) })}
        />
        {errors.liquidity_min_usd && (
          <span className="error">{errors.liquidity_min_usd}</span>
        )}
      </div>
    </div>
  );
};
```

### 3.3 Create Probability Model Form

**File**: `src/components/ProbabilityModelForm.tsx`

**Implementation**:
```typescript
import React from 'react';
import { ProbabilityModelConfig } from '../services/configApi';

interface ProbabilityModelFormProps {
  config: ProbabilityModelConfig;
  onChange: (updates: Partial<ProbabilityModelConfig>) => void;
  errors?: Record<string, string>;
}

export const ProbabilityModelForm: React.FC<ProbabilityModelFormProps> = ({
  config,
  onChange,
  errors = {},
}) => {
  const summary = `Model: ${config.model_mode}, Likely: ${(config.zeus_likely_pct * 100).toFixed(0)}%`;

  return (
    <div className="probability-model-form">
      <div className="form-group">
        <label>
          Model Mode
          <span className="tooltip-icon" title="Probability model: 'spread' uses hourly spread, 'bands' uses Zeus confidence intervals">
            ⓘ
          </span>
        </label>
        <select
          value={config.model_mode}
          onChange={(e) => onChange({ model_mode: e.target.value as 'spread' | 'bands' })}
        >
          <option value="spread">Spread</option>
          <option value="bands">Bands</option>
        </select>
        {errors.model_mode && (
          <span className="error">{errors.model_mode}</span>
        )}
      </div>

      <div className="form-group">
        <label>
          Zeus Likely % (for bands model)
          <span className="tooltip-icon" title="Zeus likely confidence level (0.80 = 80%)">
            ⓘ
          </span>
        </label>
        <input
          type="number"
          step="0.01"
          min="0.50"
          max="0.99"
          value={config.zeus_likely_pct}
          onChange={(e) => onChange({ zeus_likely_pct: parseFloat(e.target.value) })}
        />
        {errors.zeus_likely_pct && (
          <span className="error">{errors.zeus_likely_pct}</span>
        )}
      </div>

      <div className="form-group">
        <label>
          Zeus Possible % (for bands model)
          <span className="tooltip-icon" title="Zeus possible confidence level (0.95 = 95%)">
            ⓘ
          </span>
        </label>
        <input
          type="number"
          step="0.01"
          min="0.80"
          max="0.99"
          value={config.zeus_possible_pct}
          onChange={(e) => onChange({ zeus_possible_pct: parseFloat(e.target.value) })}
        />
        {errors.zeus_possible_pct && (
          <span className="error">{errors.zeus_possible_pct}</span>
        )}
      </div>

      {config.sigma_default !== undefined && (
        <>
          <div className="form-group">
            <label>
              Sigma Default (°F)
              <span className="tooltip-icon" title="Default uncertainty (std dev in °F) when Zeus bands unavailable">
                ⓘ
              </span>
            </label>
            <input
              type="number"
              step="0.1"
              min="0.5"
              max="10.0"
              value={config.sigma_default}
              onChange={(e) => onChange({ sigma_default: parseFloat(e.target.value) })}
            />
          </div>

          <div className="form-group">
            <label>
              Sigma Min (°F)
              <span className="tooltip-icon" title="Minimum allowed sigma (prevents division by zero)">
                ⓘ
              </span>
            </label>
            <input
              type="number"
              step="0.1"
              min="0.1"
              max="5.0"
              value={config.sigma_min}
              onChange={(e) => onChange({ sigma_min: parseFloat(e.target.value) })}
            />
          </div>

          <div className="form-group">
            <label>
              Sigma Max (°F)
              <span className="tooltip-icon" title="Maximum allowed sigma (prevents extreme distributions)">
                ⓘ
              </span>
            </label>
            <input
              type="number"
              step="0.1"
              min="5.0"
              max="20.0"
              value={config.sigma_max}
              onChange={(e) => onChange({ sigma_max: parseFloat(e.target.value) })}
            />
          </div>
        </>
      )}
    </div>
  );
};
```

### 3.4 Create Dynamic Trading Form

**File**: `src/components/DynamicTradingForm.tsx`

**Implementation**:
```typescript
import React from 'react';
import { DynamicTradingConfig } from '../services/configApi';

interface DynamicTradingFormProps {
  config: DynamicTradingConfig;
  onChange: (updates: Partial<DynamicTradingConfig>) => void;
  errors?: Record<string, string>;
}

export const DynamicTradingForm: React.FC<DynamicTradingFormProps> = ({
  config,
  onChange,
  errors = {},
}) => {
  return (
    <div className="dynamic-trading-form">
      <div className="form-group">
        <label>
          Evaluation Interval (minutes)
          <span className="tooltip-icon" title="Time between evaluation cycles (15 = 15 minutes)">
            ⓘ
          </span>
        </label>
        <input
          type="number"
          min="1"
          max="60"
          value={config.interval_seconds / 60}
          onChange={(e) => onChange({ interval_seconds: parseInt(e.target.value) * 60 })}
        />
        {errors.interval_seconds && (
          <span className="error">{errors.interval_seconds}</span>
        )}
      </div>

      <div className="form-group">
        <label>
          Lookahead Days
          <span className="tooltip-icon" title="Days ahead to check for markets (2 = today + tomorrow)">
            ⓘ
          </span>
        </label>
        <input
          type="number"
          min="1"
          max="7"
          value={config.lookahead_days}
          onChange={(e) => onChange({ lookahead_days: parseInt(e.target.value) })}
        />
        {errors.lookahead_days && (
          <span className="error">{errors.lookahead_days}</span>
        )}
      </div>
    </div>
  );
};
```

### 3.5 Create Execution Mode Form

**File**: `src/components/ExecutionModeForm.tsx`

**Implementation**:
```typescript
import React from 'react';

interface ExecutionModeFormProps {
  mode: 'paper' | 'live';
  onChange: (mode: 'paper' | 'live') => void;
  error?: string;
}

export const ExecutionModeForm: React.FC<ExecutionModeFormProps> = ({
  mode,
  onChange,
  error,
}) => {
  return (
    <div className="execution-mode-form">
      <label>
        Execution Mode
        <span className="tooltip-icon" title="Paper mode simulates trades, Live mode executes real trades">
          ⓘ
        </span>
      </label>
      
      <div className="radio-group">
        <label>
          <input
            type="radio"
            value="paper"
            checked={mode === 'paper'}
            onChange={() => onChange('paper')}
          />
          Paper
        </label>
        <label>
          <input
            type="radio"
            value="live"
            checked={mode === 'live'}
            onChange={() => onChange('live')}
          />
          Live
        </label>
      </div>

      {mode === 'live' && (
        <div className="warning">
          ⚠️ Live trading requires Polymarket account setup
        </div>
      )}

      {error && (
        <span className="error">{error}</span>
      )}
    </div>
  );
};
```

### 3.6 Integrate Forms into Configuration Page

**Update**: `src/pages/ConfigurationPage.tsx`

```typescript
import { CollapsibleSection } from '../components/CollapsibleSection';
import { TradingParamsForm } from '../components/TradingParamsForm';
import { ProbabilityModelForm } from '../components/ProbabilityModelForm';
import { DynamicTradingForm } from '../components/DynamicTradingForm';
import { ExecutionModeForm } from '../components/ExecutionModeForm';

// In the component:
const [localConfig, setLocalConfig] = useState<FullConfig | null>(null);
const [isDirty, setIsDirty] = useState(false);

// Update handlers
const handleTradingChange = (updates: Partial<TradingConfig>) => {
  if (!localConfig) return;
  setLocalConfig({
    ...localConfig,
    trading: { ...localConfig.trading, ...updates },
  });
  setIsDirty(true);
};

// Similar handlers for other sections...

// In return:
<CollapsibleSection title="Execution Mode" defaultExpanded={true}>
  <ExecutionModeForm
    mode={localConfig.execution_mode}
    onChange={(mode) => {
      setLocalConfig({ ...localConfig, execution_mode: mode });
      setIsDirty(true);
    }}
  />
</CollapsibleSection>

<CollapsibleSection title="Dynamic Trading Settings" defaultExpanded={true}>
  <DynamicTradingForm
    config={localConfig.dynamic_trading}
    onChange={handleDynamicTradingChange}
  />
</CollapsibleSection>

<CollapsibleSection 
  title="Trading Parameters" 
  summary={`Edge: ${(localConfig.trading.edge_min * 100).toFixed(1)}%, Kelly: ${(localConfig.trading.kelly_cap * 100).toFixed(1)}%`}
>
  <TradingParamsForm
    config={localConfig.trading}
    onChange={handleTradingChange}
  />
</CollapsibleSection>

<CollapsibleSection 
  title="Probability Model"
  summary={`Model: ${localConfig.probability_model.model_mode}, Likely: ${(localConfig.probability_model.zeus_likely_pct * 100).toFixed(0)}%`}
>
  <ProbabilityModelForm
    config={localConfig.probability_model}
    onChange={handleProbabilityModelChange}
  />
</CollapsibleSection>
```

### 3.7 Testing

**Manual Testing**:
1. Test collapsible sections expand/collapse
2. Test form inputs update state
3. Test summary displays when collapsed
4. Verify all fields are present
5. Test tooltips display correctly

**Expected Results**:
- ✅ All sections are collapsible
- ✅ Summary shows when collapsed
- ✅ Forms update state correctly
- ✅ All fields have tooltips
- ✅ Forms are organized and readable

---

## ✅ Stage 4: Form Validation & Error Handling

**Goal**: Add client-side and server-side validation

**Estimated Time**: 2-3 hours

### 4.1 Create Validation Utilities

**File**: `src/utils/validation.ts`

**Implementation**:
```typescript
export interface ValidationErrors {
  [key: string]: string;
}

export const validateTradingConfig = (config: any): ValidationErrors => {
  const errors: ValidationErrors = {};

  if (config.edge_min < 0.01 || config.edge_min > 0.50) {
    errors.edge_min = 'Edge min must be between 0.01 and 0.50';
  }

  if (config.fee_bp < 0 || config.fee_bp > 1000) {
    errors.fee_bp = 'Fee must be between 0 and 1000 basis points';
  }

  if (config.slippage_bp < 0 || config.slippage_bp > 1000) {
    errors.slippage_bp = 'Slippage must be between 0 and 1000 basis points';
  }

  if (config.kelly_cap < 0.01 || config.kelly_cap > 0.50) {
    errors.kelly_cap = 'Kelly cap must be between 0.01 and 0.50';
  }

  if (config.daily_bankroll_cap < 0) {
    errors.daily_bankroll_cap = 'Daily bankroll cap must be >= 0';
  }

  if (config.per_market_cap < 0) {
    errors.per_market_cap = 'Per-market cap must be >= 0';
  }

  if (config.liquidity_min_usd < 0) {
    errors.liquidity_min_usd = 'Min liquidity must be >= 0';
  }

  if (!config.active_stations || config.active_stations.length === 0) {
    errors.active_stations = 'At least one station is required';
  }

  return errors;
};

export const validateProbabilityModel = (config: any): ValidationErrors => {
  const errors: ValidationErrors = {};

  if (config.model_mode !== 'spread' && config.model_mode !== 'bands') {
    errors.model_mode = 'Model mode must be "spread" or "bands"';
  }

  if (config.zeus_likely_pct < 0.50 || config.zeus_likely_pct > 0.99) {
    errors.zeus_likely_pct = 'Zeus likely % must be between 0.50 and 0.99';
  }

  if (config.zeus_possible_pct < 0.80 || config.zeus_possible_pct > 0.99) {
    errors.zeus_possible_pct = 'Zeus possible % must be between 0.80 and 0.99';
  }

  if (config.zeus_possible_pct <= config.zeus_likely_pct) {
    errors.zeus_possible_pct = 'Zeus possible % must be greater than likely %';
  }

  return errors;
};

export const validateDynamicTrading = (config: any): ValidationErrors => {
  const errors: ValidationErrors = {};

  if (config.interval_seconds < 60 || config.interval_seconds > 3600) {
    errors.interval_seconds = 'Interval must be between 60 and 3600 seconds';
  }

  if (config.lookahead_days < 1 || config.lookahead_days > 7) {
    errors.lookahead_days = 'Lookahead days must be between 1 and 7';
  }

  return errors;
};
```

### 4.2 Add Validation to Forms

**Update**: Form components to use validation

```typescript
// In ConfigurationPage.tsx
const [errors, setErrors] = useState<Record<string, ValidationErrors>>({});

const validateAll = (): boolean => {
  if (!localConfig) return false;

  const tradingErrors = validateTradingConfig(localConfig.trading);
  const probErrors = validateProbabilityModel(localConfig.probability_model);
  const dynErrors = validateDynamicTrading(localConfig.dynamic_trading);

  setErrors({
    trading: tradingErrors,
    probability_model: probErrors,
    dynamic_trading: dynErrors,
  });

  return Object.keys(tradingErrors).length === 0 &&
         Object.keys(probErrors).length === 0 &&
         Object.keys(dynErrors).length === 0;
};

// Pass errors to form components
<TradingParamsForm
  config={localConfig.trading}
  onChange={handleTradingChange}
  errors={errors.trading || {}}
/>
```

### 4.3 Add Save/Reset Functionality

**Update**: `src/pages/ConfigurationPage.tsx`

```typescript
const handleSave = async () => {
  if (!localConfig) return;

  // Client-side validation
  if (!validateAll()) {
    setError('Please fix validation errors before saving');
    return;
  }

  setLoading(true);
  setError(null);

  try {
    // Server-side validation
    const validation = await validateConfig(localConfig);
    if (!validation.valid) {
      setError(`Validation failed: ${validation.errors.join(', ')}`);
      return;
    }

    // Save configuration
    const result = await updateConfig(localConfig);
    
    if (result.requires_restart) {
      setError('Configuration saved. Engine restart required to apply changes.');
    } else {
      setError(null);
      setIsDirty(false);
      // Show success message
    }
  } catch (err: any) {
    setError(err.message || 'Failed to save configuration');
  } finally {
    setLoading(false);
  }
};

const handleReset = async () => {
  if (!confirm('Are you sure you want to reset to defaults?')) return;

  setLoading(true);
  setError(null);

  try {
    await resetConfig();
    await loadConfig();
    setIsDirty(false);
  } catch (err: any) {
    setError(err.message || 'Failed to reset configuration');
  } finally {
    setLoading(false);
  }
};

// Add buttons to UI
<div className="action-buttons">
  <button 
    onClick={handleSave} 
    disabled={!isDirty || loading}
  >
    {loading ? 'Saving...' : 'Save Configuration'}
  </button>
  <button 
    onClick={handleReset} 
    disabled={loading}
  >
    Reset to Defaults
  </button>
  <button 
    onClick={loadConfig} 
    disabled={loading}
  >
    Reload from Disk
  </button>
</div>
```

### 4.4 Testing

**Manual Testing**:
1. Test client-side validation
2. Test server-side validation
3. Test save functionality
4. Test reset functionality
5. Test error display

**Expected Results**:
- ✅ Validation errors shown inline
- ✅ Save button disabled when invalid
- ✅ Server validation errors displayed
- ✅ Save/Reset/Reload work correctly
- ✅ Success/error messages displayed

---

## 🎨 Stage 5: Real-time Updates & Polish

**Goal**: Add real-time status updates and polish UI

**Estimated Time**: 2-3 hours

### 5.1 Add WebSocket Integration (Optional)

**File**: `src/services/websocketService.ts`

**Implementation**:
```typescript
export class WebSocketService {
  private ws: WebSocket | null = null;
  private listeners: Map<string, Set<(data: any) => void>> = new Map();

  connect() {
    this.ws = new WebSocket('ws://localhost:8000/ws/trading');

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      const listeners = this.listeners.get(message.type);
      if (listeners) {
        listeners.forEach(listener => listener(message.data));
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      // Reconnect after 5 seconds
      setTimeout(() => this.connect(), 5000);
    };
  }

  subscribe(eventType: string, callback: (data: any) => void) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }
    this.listeners.get(eventType)!.add(callback);

    return () => {
      this.listeners.get(eventType)?.delete(callback);
    };
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}
```

### 5.2 Add Real-time Status Updates

**Update**: `EngineControl.tsx`

```typescript
import { WebSocketService } from '../services/websocketService';

// In component:
useEffect(() => {
  const ws = new WebSocketService();
  ws.connect();

  const unsubscribe = ws.subscribe('cycle_complete', (data) => {
    loadStatus(); // Refresh status on cycle complete
  });

  return () => {
    unsubscribe();
    ws.disconnect();
  };
}, []);
```

### 5.3 Add Countdown Timer

**Update**: `EngineControl.tsx`

```typescript
const [countdown, setCountdown] = useState<number | null>(null);

useEffect(() => {
  if (!isRunning || nextCycleSeconds === null) {
    setCountdown(null);
    return;
  }

  setCountdown(nextCycleSeconds);

  const interval = setInterval(() => {
    setCountdown(prev => {
      if (prev === null || prev <= 0) {
        loadStatus(); // Refresh to get new countdown
        return null;
      }
      return prev - 1;
    });
  }, 1000);

  return () => clearInterval(interval);
}, [isRunning, nextCycleSeconds]);

// Display countdown
{countdown !== null && (
  <div className="countdown">
    Next cycle in: <strong>{formatSeconds(countdown)}</strong>
  </div>
)}
```

### 5.4 Add Styling & Polish

**File**: `src/styles/ConfigurationPage.css` (or equivalent)

**Key Styles**:
- Collapsible section animations
- Form field styling
- Error message styling
- Button states (disabled, loading)
- Status indicators (running/stopped)
- Tooltip styling

### 5.5 Testing

**Manual Testing**:
1. Test real-time status updates
2. Test countdown timer
3. Test WebSocket reconnection
4. Verify UI polish and styling
5. Test on different screen sizes

**Expected Results**:
- ✅ Status updates in real-time
- ✅ Countdown timer works correctly
- ✅ UI is polished and professional
- ✅ Responsive design works
- ✅ All interactions are smooth

---

## ✅ Implementation Checklist

### Stage 1: Basic Structure
- [ ] Create ConfigurationPage component
- [ ] Create API service files
- [ ] Test API integration
- [ ] Test error handling

### Stage 2: Engine Control
- [ ] Create EngineControl component
- [ ] Implement start/stop/restart
- [ ] Add status polling
- [ ] Test engine control

### Stage 3: Configuration Forms
- [ ] Create CollapsibleSection component
- [ ] Create TradingParamsForm
- [ ] Create ProbabilityModelForm
- [ ] Create DynamicTradingForm
- [ ] Create ExecutionModeForm
- [ ] Integrate all forms
- [ ] Test collapsible sections

### Stage 4: Validation
- [ ] Create validation utilities
- [ ] Add client-side validation
- [ ] Add server-side validation
- [ ] Implement save/reset/reload
- [ ] Test validation

### Stage 5: Polish
- [ ] Add WebSocket integration (optional)
- [ ] Add real-time updates
- [ ] Add countdown timer
- [ ] Add styling
- [ ] Test polish

---

## 🎨 UI/UX Guidelines

### Collapsible Sections
- **Default State**: Advanced sections collapsed
- **Summary View**: Show key values when collapsed
- **Animation**: Smooth slide-down animation
- **Icon**: ▼ when collapsed, ▲ when expanded

### Form Fields
- **Tooltips**: ⓘ icon with explanation
- **Validation**: Show errors inline below fields
- **Input Types**: Use appropriate inputs (number, select, text)
- **Formatting**: Format currency, percentages appropriately

### Engine Control
- **Status Indicator**: Color-coded (green = running, red = stopped)
- **Action Buttons**: Disable when appropriate
- **Confirmation Dialogs**: For destructive actions
- **Loading States**: Show spinner during operations

### Save/Reset Actions
- **Save Button**: Only enabled when form is dirty
- **Reset Button**: Show confirmation dialog
- **Reload Button**: Fetch latest from disk
- **Success Feedback**: Toast notification or inline message

---

## 📝 API Endpoint Reference

### Configuration Endpoints
- `GET /api/config` - Get current configuration
- `PUT /api/config` - Update configuration
- `POST /api/config/validate` - Validate configuration
- `POST /api/config/reload` - Reload from disk
- `GET /api/config/defaults` - Get default values
- `POST /api/config/reset` - Reset to defaults

### Engine Control Endpoints
- `POST /api/engine/start` - Start engine with configuration
- `POST /api/engine/stop` - Stop engine
- `POST /api/engine/restart` - Restart engine with new configuration
- `GET /api/engine/config` - Get current engine configuration
- `GET /api/status` - Get system status (includes engine status)

### WebSocket
- `ws://localhost:8000/ws/trading` - Real-time updates
  - Events: `cycle_complete`, `trade_placed`, `edges_updated`

---

## 🚀 Deployment Notes

### After Implementation

1. **Test All Flows**:
   - Start engine with custom config
   - Update configuration
   - Stop/restart engine
   - Validate all forms

2. **Error Handling**:
   - Test API failures
   - Test validation errors
   - Test network errors

3. **User Experience**:
   - Verify all tooltips work
   - Verify all animations are smooth
   - Verify responsive design

---

**Last Updated**: November 17, 2025

