# Hermes v1.0.0 - Functionality Overview

**Date**: November 11, 2025  
**Version**: v1.0.0

## ✅ Status: 7/11 Stages Complete (64%)
**123 tests passing** • **Paper trading + Backtest ready** • **Zeus API integrated**

---

## 🎯 What The System Does

**Hermes trades weather prediction markets by:**
1. Fetching Zeus temperature forecasts (hourly, 24h windows)
2. Converting forecasts to bracket probabilities (normal distribution)
3. Finding Polymarket temperature markets
4. Calculating edge (Zeus prob - Market prob - fees)
5. Sizing positions using Kelly criterion
6. Executing trades (paper mode) or simulating historical performance (backtest)

---

## 🛠️ Core Features

### **Data & Forecasting**
- ✅ 9 weather stations configured (London, NYC, LA, Miami, Philly, Austin, Denver, Chicago)
- ✅ Zeus API integration (hourly temperature forecasts)
- ✅ Unit conversions (Kelvin ↔ Celsius ↔ Fahrenheit)
- ✅ DST-aware timezone handling
- ✅ Probability mapping (forecast → bracket probabilities)

### **Market Integration**
- ✅ Polymarket Gamma API (market discovery)
- ✅ Polymarket CLOB API (pricing, order book depth)
- ✅ Bracket parsing (temperature ranges from market names)
- ✅ Historical price support (for backtesting)

### **Trading Logic**
- ✅ Edge calculation (after fees & slippage)
- ✅ Kelly position sizing with caps
- ✅ Liquidity-aware sizing
- ✅ Per-market position limits
- ✅ Daily bankroll caps

### **Execution & Monitoring**
- ✅ Paper trading (CSV output, full audit trail)
- ✅ Backtest harness (7-day rolling window)
- ✅ Trade monitoring script
- ✅ Snapshot persistence (Zeus forecasts, Polymarket data)

---

## 📋 Commands Available

```bash
# Fetch Zeus forecast
python -m core.orchestrator --mode fetch --station EGLC --date 2025-11-11

# Map probabilities
python -m core.orchestrator --mode probmap --station EGLC --date 2025-11-11

# Paper trading (today)
python -m core.orchestrator --mode paper --stations EGLC,KLGA

# Backtest (last 7 days max)
python -m core.orchestrator --mode backtest \
  --start 2025-11-05 --end 2025-11-11 --stations EGLC,KLGA

# Monitor trades
python monitor_trades.py
```

---

## 📁 Outputs

```
data/
├── trades/{date}/paper_trades.csv        # Paper trade decisions
├── runs/backtests/{date}_to_{date}.csv   # Backtest results
└── snapshots/
    ├── zeus/{date}/{station}.json        # Weather forecasts
    └── polymarket/markets/{city}_{date}.json  # Market data
```

---

## 🔮 Not Yet Built (Stages 8-11)

❌ **Stage 8**: Live execution (real money, Polymarket orders)  
❌ **Stage 9**: Post-trade metrics (P&L tracking, performance analysis)  
❌ **Stage 10**: Dashboard (web UI for monitoring)  
❌ **Stage 11**: Multi-venue (Kalshi support)

---

## ⚙️ Configuration (.env)

```bash
# Zeus Weather API
ZEUS_API_BASE=https://api.zeussubnet.com
ZEUS_API_KEY=6Vrl9kTZt0M9NsqQsd0T2DZELG0IBJ  # ✅ Working

# Polymarket API (Public - No Auth Required)
POLY_GAMMA_BASE=https://gamma-api.polymarket.com
POLY_CLOB_BASE=https://clob.polymarket.com

# Execution Mode
EXECUTION_MODE=paper

# Trading Configuration
ACTIVE_STATIONS=EGLC,KLGA
EDGE_MIN=0.05              # Min 5% edge to trade
FEE_BP=50                  # 50 basis points (0.5%)
SLIPPAGE_BP=30             # 30 basis points (0.3%)
KELLY_CAP=0.10             # Max 10% Kelly sizing
DAILY_BANKROLL_CAP=3000    # Max $3k/day
PER_MARKET_CAP=500         # Max $500/market
LIQUIDITY_MIN_USD=1000     # Min $1k liquidity required

# Logging
LOG_LEVEL=INFO
```

---

## 📊 Project Structure

```
hermes-v1.0.0/
├── core/                  # Core utilities
│   ├── orchestrator.py    # CLI entry point
│   ├── config.py          # Configuration management
│   ├── logger.py          # Structured logging
│   ├── registry.py        # Station registry
│   ├── time_utils.py      # Timezone handling
│   ├── types.py           # Data models
│   └── units.py           # Unit conversions
├── agents/                # Trading agents
│   ├── zeus_forecast.py   # Weather forecasts
│   ├── prob_mapper.py     # Probability mapping
│   ├── edge_and_sizing.py # Kelly sizing
│   └── backtester.py      # Backtest harness
├── venues/                # Venue adapters
│   └── polymarket/
│       ├── discovery.py   # Market discovery
│       ├── pricing.py     # Price fetching
│       ├── execute.py     # Paper/live execution
│       └── schemas.py     # API models
├── tests/                 # 123 tests (100% passing)
├── data/                  # Data storage
│   ├── registry/          # Station metadata
│   ├── snapshots/         # API responses
│   ├── trades/            # Trade logs
│   └── runs/              # Backtest results
└── docs/build/            # Documentation
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific module
pytest tests/test_zeus_forecast.py -v

# Run with coverage
pytest --cov=. --cov-report=term-missing
```

**Test Coverage**: 123 tests, 100% passing
- 16 tests: Units & time utilities
- 13 tests: Registry
- 11 tests: Zeus forecast
- 14 tests: Probability mapper
- 10 tests: Polymarket discovery
- 11 tests: Polymarket pricing
- 20 tests: Edge & sizing
- 10 tests: Paper execution
- 12 tests: Backtester
- 6 tests: Integration

---

## 📈 Stages Completed

### ✅ Stage 0: Project Scaffold
- Directory structure
- Dependency management
- Configuration system

### ✅ Stage 1: Data Registry & Utilities
- 9 weather stations
- Unit conversions
- DST-aware timezone handling

### ✅ Stage 2: Zeus Forecast Agent
- API integration (array-based format)
- Retry logic with tenacity
- Snapshot persistence

### ✅ Stage 3: Probability Mapper
- Normal CDF probability mapping
- Sigma estimation
- Bracket probability normalization

### ✅ Stage 4: Polymarket Adapters
- Gamma API (market discovery)
- CLOB API (pricing)
- Bracket parsing from market names

### ✅ Stage 5: Edge Calculation & Kelly Sizing
- Edge calculation (Zeus - Market - Fees)
- Kelly fraction computation
- Position sizing with caps

### ✅ Stage 6: Paper Execution Loop (MVP)
- End-to-end paper trading
- CSV trade logging
- Trade monitoring script

### ✅ Stage 7: Backtest Harness
- Historical simulation
- 7-day rolling window (Zeus API limit)
- Summary statistics

---

## 🚀 Next Steps

### Immediate (Stage 8 - Live Execution)
**Requirements**:
- Polymarket account with funds
- Wallet private key
- py-clob-client library
- Polygon mainnet access

**Implementation**:
- `LiveBroker` class
- CLOB authentication
- Order placement
- Position tracking
- Emergency stop mechanism
- Dry-run preview mode

**Risk**: ⚠️ REAL MONEY

**Recommendation**: Run paper trading for 1-2 weeks + daily backtests before going live

---

## 📝 Key Decisions & Constraints

### Zeus API
- **Limitation**: Only supports last 7 days
- **Impact**: Backtest limited to rolling 7-day window
- **Mitigation**: Run daily backtests, accumulate results over time

### Polymarket
- **Public APIs**: No authentication required for discovery/pricing
- **Private APIs**: Need wallet private key for live trading (Stage 8)

### Position Sizing
- **Kelly Cap**: 10% max (conservative)
- **Per-Market**: $500 max (risk control)
- **Daily Total**: $3,000 max (bankroll management)

### Edge Threshold
- **Minimum**: 5% (after fees & slippage)
- **Rationale**: Ensures meaningful edge after 0.5% fees + 0.3% slippage

---

## 🎯 Success Metrics

### Current (Paper Trading)
- Tracks: Trades placed, edge identified, position sizes
- Outputs: CSV logs with full audit trail
- Monitoring: Real-time console logs + trade summary script

### Future (Live Trading - Stage 9)
- Hit rate vs forecast accuracy
- Realized P&L vs expected edge
- Sharpe ratio
- Maximum drawdown
- ROI by bracket type
- Edge realization percentage

---

## 🔗 Related Documentation

- `PROJECT_OVERVIEW.md` - Complete 11-stage roadmap
- `QUICK_REFERENCE.md` - Quick start guide
- `STAGE_7_SUMMARY.md` - Stage 7 detailed documentation
- `docs/build/` - All stage summaries and verification checklists

---

**Bottom Line**: Fully functional paper trading system with backtesting capability. System has been validated with real Zeus API integration. Ready to run paper trades and validate strategy before proceeding to live execution (Stage 8).

**Status**: ✅ Production-ready for paper trading  
**Next Milestone**: Stage 8 (Live Execution with real money)

---

*Last Updated: November 11, 2025*  
*Documentation: Harvey Ando*  
*Implementation: Hermes v1.0.0*

