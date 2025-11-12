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

# Paper trading
python -m core.orchestrator --mode paper \
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
| 1 | 📝 READY | Data registry + utilities |
| 2 | 🔜 TODO | Zeus forecast agent |
| 3 | 🔜 TODO | Probability mapper |
| 4 | 🔜 TODO | Polymarket adapters |
| 5 | 🔜 TODO | Edge & Kelly sizing |
| 6 | 🔜 TODO | Paper execution loop |
| 7 | 🔜 TODO | Backtest harness |
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

## 📚 Documentation

- **README.md** - Project overview and quick start
- **PROJECT_OVERVIEW.md** - Complete 11-stage implementation plan
- **STAGE_0_COMPLETE.md** - What was built in Stage 0
- **STAGE_0_VERIFICATION.md** - Detailed verification results
- **QUICK_REFERENCE.md** - This file

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

---

**Last Updated**: November 4, 2025  
**Version**: 1.0.0  
**Stage**: 0 (Complete)

