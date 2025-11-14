# Hermes v1.0.0 - Quick Reference Card

## 🚀 Setup (First Time)

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your Zeus API key

# 2. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -e ".[dev]"

# 4. Verify installation
python verify_stage0.py
pytest tests/test_units.py -v
```

## 📋 Daily Commands

```bash
# Activate environment (always do this first)
source .venv/bin/activate

# Run all tests
pytest -v
# or: make test

# Format code
make format

# Lint code
make lint

# Type check
make type-check

# Run all checks
make check
```

## 🎯 Orchestrator Modes

```bash
# Fetch Zeus forecast
python -m core.orchestrator --mode fetch \
  --date 2025-10-27 \
  --station EGLC

# Map probabilities
python -m core.orchestrator --mode probmap \
  --date 2025-10-27 \
  --station EGLC

# Paper trading (one-time run)
python -m core.orchestrator --mode paper \
  --stations EGLC,KLGA

# Dynamic paper trading (continuous loop)
python -m core.orchestrator --mode dynamic-paper \
  --stations EGLC,KLGA

# Backtest
python -m core.orchestrator --mode backtest \
  --start 2025-10-01 \
  --end 2025-10-31 \
  --stations EGLC,KLGA
```

## 📁 Key Files

| File | Purpose |
|------|---------|
| `core/config.py` | Configuration management |
| `core/orchestrator.py` | Main CLI entry point |
| `core/types.py` | Pydantic data models |
| `core/units.py` | Temperature conversions |
| `core/time_utils.py` | Timezone utilities |
| `agents/dynamic_trader/` | Dynamic trading engine |
| `backend/api/main.py` | FastAPI backend server |
| `.env` | Your local configuration (git-ignored) |
| `pyproject.toml` | Dependencies and project metadata |
| `Makefile` | Common tasks shortcuts |

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Zeus API
ZEUS_API_KEY=your-key-here

# Trading parameters
ACTIVE_STATIONS=EGLC,KLGA
EDGE_MIN=0.05              # 5% minimum edge
DAILY_BANKROLL_CAP=3000    # $3000 daily limit
PER_MARKET_CAP=500         # $500 per market
LIQUIDITY_MIN_USD=1000     # $1000 minimum liquidity

# Execution
EXECUTION_MODE=paper       # or "live"
LOG_LEVEL=INFO            # or "DEBUG"

# Dynamic trading (Stage 7C)
DYNAMIC_INTERVAL_SECONDS=900  # 15 minutes
DYNAMIC_LOOKAHEAD_DAYS=2      # Check today + tomorrow

# Probability models (Stage 7B)
MODEL_MODE=spread         # or "bands"
ZEUS_LIKELY_PCT=0.80      # 80% confidence
ZEUS_POSSIBLE_PCT=0.95    # 95% confidence
```

### Config Overrides (config.local.yaml)

```yaml
# Optional YAML overrides
trading:
  edge_min: 0.03
  daily_bankroll_cap: 5000.0

execution_mode: live
log_level: DEBUG
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_units.py -v

# Run with coverage
pytest --cov=core --cov=agents --cov=venues

# Run only fast tests (skip Stage 3+ stubs)
pytest -m "not skip"
```

## 📊 Project Status

| Stage | Status | Description |
|-------|--------|-------------|
| 0 | ✅ COMPLETE | Repo bootstrap |
| 1 | ✅ COMPLETE | Data registry + utilities |
| 2 | ✅ COMPLETE | Zeus forecast agent |
| 3 | ✅ COMPLETE | Probability mapper |
| 4 | ✅ COMPLETE | Polymarket adapters |
| 5 | ✅ COMPLETE | Edge & Kelly sizing |
| 6 | ✅ COMPLETE | Paper execution loop |
| 7 | ✅ COMPLETE | Backtest harness |
| 7A | ✅ COMPLETE | Resolution integration |
| 7B | ✅ COMPLETE | Dual probability models |
| 7C | ✅ COMPLETE | Dynamic trading engine |
| 7D-1 | ✅ COMPLETE | METAR integration |
| 7D-2 | ✅ COMPLETE | Backend API structure |
| 7D-3+ | 🔜 IN PROGRESS | Frontend dashboard |
| 8 | 🔜 TODO | Live execution |
| 9 | 🔜 TODO | Post-trade metrics |
| 10 | 🔜 TODO | Resolution validation |
| 11 | 🔜 TODO | Kalshi adapter |

## 🐛 Troubleshooting

### Import Errors
```bash
# Make sure you're in the virtual environment
source .venv/bin/activate

# Reinstall in editable mode
pip install -e .
```

### Config Not Loading
```bash
# Check .env exists
ls -la .env

# Verify config loads
python -c "from core.config import config; print(config.config)"
```

### Tests Failing
```bash
# Update dependencies
pip install --upgrade -e ".[dev]"

# Clear cache
make clean

# Run with verbose output
pytest -vv
```

## 🚀 Backend API

### Start Server
```bash
cd backend
pip install -r requirements.txt
python -m api.main
# Or: uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

### Quick API Tests
```bash
# Health check
curl http://localhost:8000/health

# Zeus snapshots
curl "http://localhost:8000/api/snapshots/zeus?station_code=EGLC&event_day=2025-11-13&limit=1"

# Recent trades
curl "http://localhost:8000/api/trades/recent?limit=5"

# Trade summary
curl "http://localhost:8000/api/trades/summary?trade_date=2025-11-13"
```

### Interactive Docs
Open http://localhost:8000/docs in your browser for interactive API documentation.

## 📚 Documentation

- **README.md** - Project overview and quick start
- **PROJECT_OVERVIEW.md** - Complete 11-stage implementation plan
- **QUICK_REFERENCE.md** - This file
- **docs/build/** - Detailed stage documentation
  - **STAGE_7D_SPECIFICATION.md** - Backend & frontend spec
  - **FRONTEND.md** - Frontend design and mockups
  - **HERMES_SNAPSHOTTER_SPEC.md** - Data collection side project

## 🔗 Useful Links

- Zeus API: `https://api.zeussubnet.com`
- Polymarket Gamma: `https://gamma-api.polymarket.com`
- Polymarket CLOB: `https://clob.polymarket.com`

## 💡 Tips

- **Always activate venv first**: `source .venv/bin/activate`
- **Use make commands**: Faster than typing full commands
- **Check logs**: Structured logging helps debug issues
- **Paper trade first**: Test strategies before going live
- **Keep data snapshots**: Everything saves to `data/` for audit

## 🔄 Dynamic Trading

### Start Dynamic Paper Trading
```bash
# Runs continuously, checking markets every 15 minutes
python -m core.orchestrator --mode dynamic-paper --stations EGLC,KLGA
```

### Monitor Dynamic Trading
```bash
# Check status
./check_dynamic.sh

# View logs
tail -f logs/dynamic_paper_*.log

# Monitor trades
python monitor_dynamic.py
```

### Dynamic Trading Features
- ✅ Just-in-time Zeus fetching (local time)
- ✅ Real-time Polymarket pricing
- ✅ METAR observation collection
- ✅ Timestamped snapshots
- ✅ Continuous evaluation loop

## 📊 Data Collection

### Snapshot Locations
- **Zeus**: `data/snapshots/dynamic/zeus/{station}/{date}/`
- **Polymarket**: `data/snapshots/dynamic/polymarket/{city}/{date}/`
- **Decisions**: `data/snapshots/dynamic/decisions/{station}/{date}/`
- **METAR**: `data/snapshots/dynamic/metar/{station}/{date}/`

### View Snapshots
```bash
# List Zeus snapshots for today
ls -lh data/snapshots/dynamic/zeus/EGLC/$(date +%Y-%m-%d)/

# View latest Zeus snapshot
cat data/snapshots/dynamic/zeus/EGLC/$(date +%Y-%m-%d)/*.json | tail -1 | jq .
```

---

**Last Updated**: November 14, 2025  
**Version**: 1.0.0  
**Stage**: 7D-2 (Backend API Complete)

