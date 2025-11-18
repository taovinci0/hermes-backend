# Performance & Portfolio Page - Frontend Implementation Guide

**Purpose**: Complete frontend implementation guide for the Performance & Portfolio page  
**Status**: Ready for frontend developer  
**Backend Status**: ✅ All backend/API stages complete

---

## 📋 Overview

This document provides a complete implementation guide for building the Performance & Portfolio page frontend. All backend/API endpoints are complete and ready to use.

### What's Already Built (Backend/API)

✅ **All backend/API stages are complete:**
- ✅ Trade Resolution Service (`/api/trades/resolve`)
- ✅ P&L Aggregation Service (`/api/performance/pnl`)
- ✅ Performance Metrics Service (`/api/performance/metrics`)
- ✅ Enhanced Trade History (`/api/trades/history`)

### What Needs to Be Built (Frontend)

🎨 **5 frontend stages:**
1. Basic Page Structure & Mode Toggle
2. Account Balances Section
3. P&L Dashboard Section
4. Performance Metrics Section
5. Trade History Table

---

## 🔌 API Endpoints Reference

### Base URL
```
http://localhost:8000
```

### Available Endpoints

#### 1. Get P&L Data
```
GET /api/performance/pnl
Query Parameters:
  - mode: 'paper' | 'live' (default: 'paper')
  - start_date?: string (YYYY-MM-DD)
  - end_date?: string (YYYY-MM-DD)
  - station_code?: string
  - venue?: string ('polymarket', 'kalshi')

Response:
{
  "total_pnl": number,
  "total_risk": number,
  "roi": number,
  "by_station": {
    "EGLC": { "pnl": number, "risk": number, "roi": number, "trades": number },
    ...
  },
  "by_venue": {
    "polymarket": { "pnl": number, "risk": number, "roi": number, "trades": number },
    ...
  },
  "by_period": {
    "today": { "pnl": number, "risk": number, "roi": number },
    "week": { "pnl": number, "risk": number, "roi": number },
    "month": { "pnl": number, "risk": number, "roi": number },
    "year": { "pnl": number, "risk": number, "roi": number },
    "all_time": { "pnl": number, "risk": number, "roi": number }
  }
}
```

#### 2. Get Performance Metrics
```
GET /api/performance/metrics
Query Parameters:
  - mode: 'paper' | 'live' (default: 'paper')
  - start_date?: string (YYYY-MM-DD)
  - end_date?: string (YYYY-MM-DD)
  - station_code?: string

Response:
{
  "total_trades": number,
  "resolved_trades": number,
  "pending_trades": number,
  "wins": number,
  "losses": number,
  "win_rate": number,
  "total_risk": number,
  "total_pnl": number,
  "roi": number,
  "avg_edge_pct": number,
  "largest_win": number,
  "largest_loss": number,
  "sharpe_ratio": number,
  "by_station": {
    "EGLC": {
      "trades": number,
      "wins": number,
      "losses": number,
      "win_rate": number,
      "pnl": number,
      "roi": number
    },
    ...
  }
}
```

#### 3. Get Trade History
```
GET /api/trades/history
Query Parameters:
  - mode: 'paper' | 'live' (default: 'paper')
  - start_date?: string (YYYY-MM-DD)
  - end_date?: string (YYYY-MM-DD)
  - station_code?: string
  - venue?: string
  - outcome?: string ('win', 'loss', 'pending')
  - limit?: number (default: 100)
  - offset?: number (default: 0)

Response:
{
  "trades": [
    {
      "timestamp": string,
      "station_code": string,
      "bracket_name": string,
      "bracket_lower_f": number,
      "bracket_upper_f": number,
      "market_id": string,
      "edge": number,
      "edge_pct": number,
      "f_kelly": number,
      "size_usd": number,
      "p_zeus": number | null,
      "p_mkt": number | null,
      "outcome": string | null,  // 'win', 'loss', 'pending'
      "realized_pnl": number | null,
      "venue": string | null,  // 'polymarket', 'kalshi'
      "resolved_at": string | null,
      "winner_bracket": string | null
    },
    ...
  ],
  "total": number,
  "limit": number,
  "offset": number,
  "has_more": boolean
}
```

#### 4. Resolve Trades
```
POST /api/trades/resolve
Query Parameters:
  - trade_date?: string (YYYY-MM-DD, defaults to today)
  - station_code?: string

Response:
{
  "success": true,
  "message": string,
  "resolved": number,
  "pending": number,
  "wins": number,
  "losses": number,
  "total_pnl": number,
  "trade_date": string
}
```

#### 5. Get Execution Mode (for mode detection)
```
GET /api/status
Response:
{
  ...
  "execution_mode": "paper" | "live",
  ...
}
```

---

## 🎨 Frontend Implementation Stages

### Stage 1: Basic Page Structure & Mode Toggle

**Goal**: Create page structure with mode toggle

**Estimated Time**: 2-3 hours

#### 1.1 Create Performance Page Component

**File**: `src/pages/PerformancePage.tsx`

**Basic Structure**:
```typescript
import React, { useState, useEffect } from 'react';
import { fetchExecutionMode } from '../services/api';

export const PerformancePage: React.FC = () => {
  const [mode, setMode] = useState<'paper' | 'live'>('paper');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadExecutionMode();
  }, []);

  const loadExecutionMode = async () => {
    try {
      const status = await fetchExecutionMode();
      setMode(status.execution_mode || 'paper');
    } catch (err) {
      // Default to paper
      setMode('paper');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="performance-page">
      <h1>💰 Performance & Portfolio Overview</h1>
      
      <div className="mode-selector">
        <button
          className={mode === 'paper' ? 'active' : ''}
          onClick={() => setMode('paper')}
        >
          ⚠️ Paper Trading
        </button>
        <button
          className={mode === 'live' ? 'active' : ''}
          onClick={() => setMode('live')}
        >
          ✅ Live Trading
        </button>
      </div>

      {mode === 'paper' && (
        <div className="paper-mode-warning">
          ⚠️ Paper Trading Mode: Showing simulated trades and theoretical P&L
        </div>
      )}

      {mode === 'live' && (
        <div className="live-mode-info">
          ✅ Live Trading Mode: Showing real trades and actual account balances
        </div>
      )}

      {/* Sections will be added in later stages */}
    </div>
  );
};
```

#### 1.2 Create API Service

**File**: `src/services/performanceApi.ts`

**Implementation**:
```typescript
const API_BASE = 'http://localhost:8000';

export interface PnLData {
  total_pnl: number;
  total_risk: number;
  roi: number;
  by_station: Record<string, { pnl: number; risk: number; roi: number; trades: number }>;
  by_venue: Record<string, { pnl: number; risk: number; roi: number; trades: number }>;
  by_period: {
    today: { pnl: number; risk: number; roi: number };
    week: { pnl: number; risk: number; roi: number };
    month: { pnl: number; risk: number; roi: number };
    year: { pnl: number; risk: number; roi: number };
    all_time: { pnl: number; risk: number; roi: number };
  };
}

export interface PerformanceMetrics {
  total_trades: number;
  resolved_trades: number;
  pending_trades: number;
  wins: number;
  losses: number;
  win_rate: number;
  total_risk: number;
  total_pnl: number;
  roi: number;
  avg_edge_pct: number;
  largest_win: number;
  largest_loss: number;
  sharpe_ratio: number;
  by_station: Record<string, {
    trades: number;
    wins: number;
    losses: number;
    win_rate: number;
    pnl: number;
    roi: number;
  }>;
}

export interface TradeHistoryResponse {
  trades: Trade[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface Trade {
  timestamp: string;
  station_code: string;
  bracket_name: string;
  bracket_lower_f: number;
  bracket_upper_f: number;
  market_id: string;
  edge: number;
  edge_pct: number;
  f_kelly: number;
  size_usd: number;
  p_zeus?: number;
  p_mkt?: number;
  outcome?: string;
  realized_pnl?: number;
  venue?: string;
  resolved_at?: string;
  winner_bracket?: string;
}

// Get P&L data
export const fetchPnL = async (
  mode: 'paper' | 'live' = 'paper',
  params?: {
    start_date?: string;
    end_date?: string;
    station_code?: string;
    venue?: string;
  }
): Promise<PnLData> => {
  const queryParams = new URLSearchParams({ mode, ...params });
  const response = await fetch(`${API_BASE}/api/performance/pnl?${queryParams}`);
  if (!response.ok) throw new Error('Failed to fetch P&L');
  return response.json();
};

// Get performance metrics
export const fetchMetrics = async (
  mode: 'paper' | 'live' = 'paper',
  params?: {
    start_date?: string;
    end_date?: string;
    station_code?: string;
  }
): Promise<PerformanceMetrics> => {
  const queryParams = new URLSearchParams({ mode, ...params });
  const response = await fetch(`${API_BASE}/api/performance/metrics?${queryParams}`);
  if (!response.ok) throw new Error('Failed to fetch metrics');
  return response.json();
};

// Get trade history
export const fetchTradeHistory = async (
  mode: 'paper' | 'live' = 'paper',
  params?: {
    start_date?: string;
    end_date?: string;
    station_code?: string;
    venue?: string;
    outcome?: string;
    limit?: number;
    offset?: number;
  }
): Promise<TradeHistoryResponse> => {
  const queryParams = new URLSearchParams({ mode, ...params });
  const response = await fetch(`${API_BASE}/api/trades/history?${queryParams}`);
  if (!response.ok) throw new Error('Failed to fetch trade history');
  return response.json();
};

// Resolve trades
export const resolveTrades = async (
  trade_date?: string,
  station_code?: string
): Promise<any> => {
  const queryParams = new URLSearchParams();
  if (trade_date) queryParams.set('trade_date', trade_date);
  if (station_code) queryParams.set('station_code', station_code);
  
  const response = await fetch(`${API_BASE}/api/trades/resolve?${queryParams}`, {
    method: 'POST',
  });
  if (!response.ok) throw new Error('Failed to resolve trades');
  return response.json();
};
```

#### 1.3 Testing

**Manual Testing**:
1. Test mode toggle
2. Test page loads correctly
3. Test mode detection from API
4. Verify warnings/info messages display

**Expected Results**:
- ✅ Mode toggle works
- ✅ Page loads without errors
- ✅ Mode is detected from API
- ✅ Appropriate messages are shown

---

### Stage 2: Account Balances Section

**Goal**: Display account balances (simulated for paper, real for live)

**Estimated Time**: 2-3 hours

#### 2.1 Create Account Balances Component

**File**: `src/components/AccountBalances.tsx`

**Implementation**:
```typescript
import React, { useState, useEffect } from 'react';
import { fetchPnL } from '../services/performanceApi';
import { fetchConfig } from '../services/configApi';

interface AccountBalancesProps {
  mode: 'paper' | 'live';
}

export const AccountBalances: React.FC<AccountBalancesProps> = ({ mode }) => {
  const [pnl, setPnl] = useState<any>(null);
  const [startingBalance, setStartingBalance] = useState<number>(10000);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [mode]);

  const loadData = async () => {
    setLoading(true);
    try {
      const pnlData = await fetchPnL(mode, {});
      setPnl(pnlData);
      
      if (mode === 'paper') {
        // Get starting balance from config
        const config = await fetchConfig();
        setStartingBalance(config.trading?.daily_bankroll_cap || 10000);
      }
    } catch (err) {
      console.error('Failed to load balances:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading balances...</div>;

  if (mode === 'paper') {
    const currentBalance = startingBalance + (pnl?.total_pnl || 0);
    
    return (
      <div className="account-balances paper-mode">
        <h2>📊 Account Balances (Paper Trading)</h2>
        <div className="warning">
          ⚠️ Paper Trading Mode - No Real Account Balances
        </div>
        <div className="balance-display">
          <div className="balance-item">
            <label>Simulated Starting Balance:</label>
            <span>${startingBalance.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
          </div>
          <div className="balance-item">
            <label>Current Simulated Balance:</label>
            <span className={pnl?.total_pnl >= 0 ? 'positive' : 'negative'}>
              ${currentBalance.toLocaleString('en-US', { minimumFractionDigits: 2 })}
              {pnl?.total_pnl !== 0 && (
                <span> ({pnl?.total_pnl >= 0 ? '+' : ''}${pnl?.total_pnl.toFixed(2)})</span>
              )}
            </span>
          </div>
          <div className="balance-item">
            <label>Total P&L (Theoretical):</label>
            <span className={pnl?.total_pnl >= 0 ? 'positive' : 'negative'}>
              {pnl?.total_pnl >= 0 ? '+' : ''}${pnl?.total_pnl.toFixed(2)}
            </span>
          </div>
        </div>
        <div className="note">
          Note: These are simulated balances for testing purposes only.
        </div>
      </div>
    );
  }

  // Live mode - will be implemented when account APIs are available
  return (
    <div className="account-balances live-mode">
      <h2>📊 Account Balances (Live Trading)</h2>
      <div className="info">
        ✅ Live Trading Mode - Real Account Balances
      </div>
      <div className="coming-soon">
        Account balance integration coming soon.
        <br />
        This will show real balances from Polymarket and Kalshi APIs.
      </div>
    </div>
  );
};
```

#### 2.2 Testing

**Manual Testing**:
1. Test paper mode balances
2. Test live mode placeholder
3. Test balance calculation
4. Verify formatting

**Expected Results**:
- ✅ Paper balances display correctly
- ✅ Live mode shows placeholder
- ✅ Calculations are accurate
- ✅ Formatting is correct

---

### Stage 3: P&L Dashboard Section

**Goal**: Display P&L with period selector and breakdowns

**Estimated Time**: 3-4 hours

#### 3.1 Create P&L Dashboard Component

**File**: `src/components/PnLDashboard.tsx`

**Implementation**:
```typescript
import React, { useState, useEffect } from 'react';
import { fetchPnL, PnLData } from '../services/performanceApi';

interface PnLDashboardProps {
  mode: 'paper' | 'live';
}

type Period = 'today' | 'week' | 'month' | 'year' | 'all_time';

export const PnLDashboard: React.FC<PnLDashboardProps> = ({ mode }) => {
  const [period, setPeriod] = useState<Period>('all_time');
  const [pnl, setPnl] = useState<PnLData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPnL();
  }, [mode, period]);

  const loadPnL = async () => {
    setLoading(true);
    try {
      const data = await fetchPnL(mode);
      setPnl(data);
    } catch (err) {
      console.error('Failed to load P&L:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading P&L...</div>;
  if (!pnl) return <div>No P&L data available</div>;

  const periodData = pnl.by_period[period];

  return (
    <div className="pnl-dashboard">
      <h2>📈 Profit & Loss</h2>
      
      {mode === 'paper' && (
        <div className="warning">
          ⚠️ Theoretical P&L (Based on resolved outcomes)
        </div>
      )}

      {mode === 'live' && (
        <div className="info">
          ✅ Real P&L (From actual trade execution and settlement)
        </div>
      )}

      <div className="period-selector">
        {(['today', 'week', 'month', 'year', 'all_time'] as Period[]).map((p) => (
          <button
            key={p}
            className={period === p ? 'active' : ''}
            onClick={() => setPeriod(p)}
          >
            {p === 'all_time' ? 'All Time' : p.charAt(0).toUpperCase() + p.slice(1)}
          </button>
        ))}
      </div>

      <div className="pnl-summary">
        <div className="pnl-item">
          <label>Total P&L:</label>
          <span className={periodData.pnl >= 0 ? 'positive' : 'negative'}>
            {periodData.pnl >= 0 ? '+' : ''}${periodData.pnl.toFixed(2)}
            <span className="roi"> ({periodData.roi >= 0 ? '+' : ''}{periodData.roi.toFixed(2)}%)</span>
          </span>
        </div>
        <div className="pnl-item">
          <label>Total Risk:</label>
          <span>${periodData.risk.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
        </div>
        <div className="pnl-item">
          <label>ROI:</label>
          <span className={periodData.roi >= 0 ? 'positive' : 'negative'}>
            {periodData.roi >= 0 ? '+' : ''}{periodData.roi.toFixed(2)}%
          </span>
        </div>
      </div>

      <div className="breakdown">
        <h3>Breakdown by Venue</h3>
        <div className="venue-breakdown">
          {Object.entries(pnl.by_venue).map(([venue, data]) => (
            <div key={venue} className="venue-item">
              <span className="venue-name">{venue.charAt(0).toUpperCase() + venue.slice(1)}:</span>
              <span className={data.pnl >= 0 ? 'positive' : 'negative'}>
                {data.pnl >= 0 ? '+' : ''}${data.pnl.toFixed(2)}
              </span>
              <span className="roi">(ROI: {data.roi >= 0 ? '+' : ''}{data.roi.toFixed(2)}%)</span>
            </div>
          ))}
        </div>

        <h3>Breakdown by Station</h3>
        <div className="station-breakdown">
          {Object.entries(pnl.by_station).map(([station, data]) => (
            <div key={station} className="station-item">
              <span className="station-name">{station}:</span>
              <span className={data.pnl >= 0 ? 'positive' : 'negative'}>
                {data.pnl >= 0 ? '+' : ''}${data.pnl.toFixed(2)}
              </span>
              <span className="roi">(ROI: {data.roi >= 0 ? '+' : ''}{data.roi.toFixed(2)}%)</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
```

#### 3.2 Testing

**Manual Testing**:
1. Test period selector
2. Test P&L display
3. Test breakdowns
4. Verify calculations

**Expected Results**:
- ✅ Period selector works
- ✅ P&L displays correctly
- ✅ Breakdowns are accurate
- ✅ Formatting is correct

---

### Stage 4: Performance Metrics Section

**Goal**: Display performance metrics (win rate, ROI, etc.)

**Estimated Time**: 2-3 hours

#### 4.1 Create Performance Metrics Component

**File**: `src/components/PerformanceMetrics.tsx`

**Implementation**:
```typescript
import React, { useState, useEffect } from 'react';
import { fetchMetrics, PerformanceMetrics as Metrics } from '../services/performanceApi';

interface PerformanceMetricsProps {
  mode: 'paper' | 'live';
}

export const PerformanceMetrics: React.FC<PerformanceMetricsProps> = ({ mode }) => {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMetrics();
  }, [mode]);

  const loadMetrics = async () => {
    setLoading(true);
    try {
      const data = await fetchMetrics(mode);
      setMetrics(data);
    } catch (err) {
      console.error('Failed to load metrics:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading metrics...</div>;
  if (!metrics) return <div>No metrics available</div>;

  return (
    <div className="performance-metrics">
      <h2>📊 Performance Metrics</h2>
      
      {mode === 'paper' && (
        <div className="warning">
          ⚠️ Theoretical Performance (Based on resolved outcomes)
        </div>
      )}

      {mode === 'live' && (
        <div className="info">
          ✅ Actual Performance (From real trade execution)
        </div>
      )}

      <div className="metrics-grid">
        <div className="metric-item">
          <label>Total Trades:</label>
          <span>{metrics.total_trades}</span>
        </div>
        <div className="metric-item">
          <label>Resolved:</label>
          <span>{metrics.resolved_trades} ({((metrics.resolved_trades / metrics.total_trades) * 100).toFixed(1)}%)</span>
        </div>
        <div className="metric-item">
          <label>Pending:</label>
          <span>{metrics.pending_trades} ({((metrics.pending_trades / metrics.total_trades) * 100).toFixed(1)}%)</span>
        </div>
        <div className="metric-item">
          <label>Win Rate:</label>
          <span className="highlight">{metrics.win_rate.toFixed(2)}% ({metrics.wins} wins / {metrics.resolved_trades} resolved)</span>
        </div>
        <div className="metric-item">
          <label>Average Edge:</label>
          <span>{metrics.avg_edge_pct.toFixed(2)}%</span>
        </div>
        <div className="metric-item">
          <label>ROI:</label>
          <span className={metrics.roi >= 0 ? 'positive' : 'negative'}>
            {metrics.roi >= 0 ? '+' : ''}{metrics.roi.toFixed(2)}%
          </span>
        </div>
        <div className="metric-item">
          <label>Sharpe Ratio:</label>
          <span>{metrics.sharpe_ratio.toFixed(2)}</span>
        </div>
        <div className="metric-item">
          <label>Largest Win:</label>
          <span className="positive">+${metrics.largest_win.toFixed(2)}</span>
        </div>
        <div className="metric-item">
          <label>Largest Loss:</label>
          <span className="negative">${metrics.largest_loss.toFixed(2)}</span>
        </div>
      </div>

      <div className="station-breakdown">
        <h3>By Station</h3>
        {Object.entries(metrics.by_station).map(([station, data]) => (
          <div key={station} className="station-metrics">
            <h4>{station}</h4>
            <div className="metrics-row">
              <span>Trades: {data.trades}</span>
              <span>Wins: {data.wins}</span>
              <span>Losses: {data.losses}</span>
              <span>Win Rate: {data.win_rate.toFixed(2)}%</span>
              <span>P&L: <span className={data.pnl >= 0 ? 'positive' : 'negative'}>{data.pnl >= 0 ? '+' : ''}${data.pnl.toFixed(2)}</span></span>
              <span>ROI: <span className={data.roi >= 0 ? 'positive' : 'negative'}>{data.roi >= 0 ? '+' : ''}{data.roi.toFixed(2)}%</span></span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
```

#### 4.2 Testing

**Manual Testing**:
1. Test metrics display
2. Test win rate calculation
3. Test station breakdowns
4. Verify all metrics are shown

**Expected Results**:
- ✅ All metrics display correctly
- ✅ Win rate is accurate
- ✅ Station breakdowns work
- ✅ Formatting is correct

---

### Stage 5: Trade History Table

**Goal**: Display trade history with filtering and pagination

**Estimated Time**: 4-5 hours

#### 5.1 Create Trade History Component

**File**: `src/components/TradeHistory.tsx`

**Implementation**:
```typescript
import React, { useState, useEffect } from 'react';
import { fetchTradeHistory, Trade, TradeHistoryResponse } from '../services/performanceApi';

interface TradeHistoryProps {
  mode: 'paper' | 'live';
}

export const TradeHistory: React.FC<TradeHistoryProps> = ({ mode }) => {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    start_date: '',
    end_date: '',
    station_code: '',
    venue: '',
    outcome: '',
  });
  const [pagination, setPagination] = useState({
    limit: 50,
    offset: 0,
  });

  useEffect(() => {
    loadTrades();
  }, [mode, filters, pagination]);

  const loadTrades = async () => {
    setLoading(true);
    try {
      const response = await fetchTradeHistory(mode, {
        ...filters,
        ...pagination,
      });
      setTrades(response.trades);
      setTotal(response.total);
    } catch (err) {
      console.error('Failed to load trades:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key: string, value: string) => {
    setFilters({ ...filters, [key]: value });
    setPagination({ ...pagination, offset: 0 }); // Reset to first page
  };

  const getOutcomeIcon = (outcome?: string) => {
    if (!outcome || outcome === 'pending') return '⏳';
    if (outcome === 'win') return '✅';
    if (outcome === 'loss') return '❌';
    return '❓';
  };

  const getOutcomeLabel = (outcome?: string) => {
    if (!outcome || outcome === 'pending') return 'Pending';
    if (outcome === 'win') return 'Win';
    if (outcome === 'loss') return 'Loss';
    return 'Unknown';
  };

  return (
    <div className="trade-history">
      <h2>📝 Trade History</h2>
      
      {mode === 'paper' && (
        <div className="warning">
          ⚠️ Simulated Trades - No Real Execution
        </div>
      )}

      {mode === 'live' && (
        <div className="info">
          ✅ Real Trades - Executed on Exchange
        </div>
      )}

      <div className="filters">
        <div className="filter-group">
          <label>Start Date:</label>
          <input
            type="date"
            value={filters.start_date}
            onChange={(e) => handleFilterChange('start_date', e.target.value)}
          />
        </div>
        <div className="filter-group">
          <label>End Date:</label>
          <input
            type="date"
            value={filters.end_date}
            onChange={(e) => handleFilterChange('end_date', e.target.value)}
          />
        </div>
        <div className="filter-group">
          <label>Station:</label>
          <select
            value={filters.station_code}
            onChange={(e) => handleFilterChange('station_code', e.target.value)}
          >
            <option value="">All</option>
            <option value="EGLC">EGLC</option>
            <option value="KLGA">KLGA</option>
            {/* Add more stations */}
          </select>
        </div>
        <div className="filter-group">
          <label>Venue:</label>
          <select
            value={filters.venue}
            onChange={(e) => handleFilterChange('venue', e.target.value)}
          >
            <option value="">All</option>
            <option value="polymarket">Polymarket</option>
            <option value="kalshi">Kalshi</option>
          </select>
        </div>
        <div className="filter-group">
          <label>Outcome:</label>
          <select
            value={filters.outcome}
            onChange={(e) => handleFilterChange('outcome', e.target.value)}
          >
            <option value="">All</option>
            <option value="win">Win</option>
            <option value="loss">Loss</option>
            <option value="pending">Pending</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div>Loading trades...</div>
      ) : (
        <>
          <div className="trade-table">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Station</th>
                  <th>Bracket</th>
                  <th>Size</th>
                  <th>Edge</th>
                  <th>Outcome</th>
                  <th>P&L</th>
                  <th>Venue</th>
                </tr>
              </thead>
              <tbody>
                {trades.map((trade, idx) => (
                  <tr key={idx}>
                    <td>{new Date(trade.timestamp).toLocaleString()}</td>
                    <td>{trade.station_code}</td>
                    <td>{trade.bracket_name}</td>
                    <td>${trade.size_usd.toFixed(2)}</td>
                    <td>{trade.edge_pct.toFixed(2)}%</td>
                    <td>
                      {getOutcomeIcon(trade.outcome)} {getOutcomeLabel(trade.outcome)}
                      {mode === 'paper' && <span className="badge">Paper</span>}
                      {mode === 'live' && <span className="badge">Live</span>}
                    </td>
                    <td className={trade.realized_pnl && trade.realized_pnl >= 0 ? 'positive' : 'negative'}>
                      {trade.realized_pnl !== null && trade.realized_pnl !== undefined
                        ? `${trade.realized_pnl >= 0 ? '+' : ''}$${trade.realized_pnl.toFixed(2)}`
                        : '-'}
                    </td>
                    <td>{trade.venue || 'polymarket'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="pagination">
            <button
              disabled={pagination.offset === 0}
              onClick={() => setPagination({ ...pagination, offset: pagination.offset - pagination.limit })}
            >
              ◀ Previous
            </button>
            <span>
              Showing {pagination.offset + 1}-{Math.min(pagination.offset + pagination.limit, total)} of {total} trades
            </span>
            <button
              disabled={pagination.offset + pagination.limit >= total}
              onClick={() => setPagination({ ...pagination, offset: pagination.offset + pagination.limit })}
            >
              Next ▶
            </button>
          </div>
        </>
      )}
    </div>
  );
};
```

#### 5.2 Testing

**Manual Testing**:
1. Test table display
2. Test filtering
3. Test pagination
4. Test sorting (if implemented)
5. Test outcome indicators

**Expected Results**:
- ✅ Table displays correctly
- ✅ Filters work
- ✅ Pagination works
- ✅ Outcome indicators are clear
- ✅ Mode badges are shown

---

## ✅ Implementation Checklist

### Frontend
- [ ] **Stage 1**: Basic Page Structure
  - [ ] Create PerformancePage component
  - [ ] Create API service
  - [ ] Test mode toggle

- [ ] **Stage 2**: Account Balances
  - [ ] Create AccountBalances component
  - [ ] Test paper mode
  - [ ] Prepare live mode placeholder

- [ ] **Stage 3**: P&L Dashboard
  - [ ] Create PnLDashboard component
  - [ ] Test period selector
  - [ ] Test breakdowns

- [ ] **Stage 4**: Performance Metrics
  - [ ] Create PerformanceMetrics component
  - [ ] Test metrics display

- [ ] **Stage 5**: Trade History Table
  - [ ] Create TradeHistory component
  - [ ] Test filtering
  - [ ] Test pagination

---

## 🚀 Future Enhancements

### Phase 2: Live Trading Support
- [ ] Account balance API integration (Polymarket)
- [ ] Account balance API integration (Kalshi)
- [ ] Live trade execution tracking
- [ ] Exchange settlement integration

### Phase 3: Advanced Features
- [ ] P&L over time chart
- [ ] Export to CSV/PDF
- [ ] Performance comparison (this month vs last month)
- [ ] Risk metrics (VaR, max drawdown)

---

## 📝 Notes

### Paper vs Live Trading

**Paper Trading Mode:**
- Shows simulated trades and theoretical P&L
- Account balances are calculated from starting balance + P&L
- All data comes from paper trade CSVs
- Outcomes are resolved using Polymarket event data

**Live Trading Mode:**
- Will show real trades and actual account balances
- Account balances will come from exchange APIs (future)
- Trade data will come from exchange APIs (future)
- Currently shows placeholder

### Resolving Trades

Trades can be resolved by calling the `/api/trades/resolve` endpoint. This:
- Fetches Polymarket events for the specified date
- Determines winning brackets using `outcomePrices`
- Updates trade CSVs with outcomes and P&L
- Returns summary of resolved trades

**Total Estimated Time**: 13-17 hours

**Priority**: High (MVP feature for portfolio tracking)

