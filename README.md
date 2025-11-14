# Hermes v1.0.0

**Weather→Markets Trading System** (Polymarket-first, Kalshi-ready)

Hermes ingests hourly Zeus weather forecasts, converts them into bracket probabilities for city temperature "daily high" markets, compares those to Polymarket's implied probabilities, sizes trades by edge & liquidity, and executes/monitors positions.

## Status: MVP Complete + Backend API! 🎉

**138 tests passing (100%)** • **7.5 stages complete** • **Production-ready paper trading + backtest with resolution + FastAPI backend**

## Features

- 🌡️ **Zeus Weather Integration**: Hourly temperature forecasts with 24h windows ✅
- 📊 **Probability Mapping**: Convert forecasts to market bracket probabilities ✅
- 🎯 **Market Discovery**: Automated Polymarket bracket detection ✅
- 💰 **Kelly Sizing**: Edge-based position sizing with liquidity awareness ✅
- 📝 **Paper Trading**: Complete end-to-end paper trading system ✅
- 📈 **Trade Logging**: Full CSV audit trail with all metadata ✅
- 🔄 **Dynamic Trading**: Continuous real-time trading loop with JIT fetching ✅
- 🌡️ **METAR Integration**: Actual temperature observations for validation ✅
- 🚀 **Backend API**: FastAPI REST API for dashboard and monitoring ✅
- 🔌 **Modular Design**: Clean architecture for easy extension

## Quick Start

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd hermes-v1.0.0
```

2. Install dependencies:
```bash
# Using uv (recommended)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"

# Or using pip
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

3. Configure environment:
```bash
# Create .env file with your Zeus API key
cat > .env << 'EOF'
ZEUS_API_BASE=https://api.zeussubnet.com
ZEUS_API_KEY=your_zeus_api_key_here
POLY_GAMMA_BASE=https://gamma-api.polymarket.com
POLY_CLOB_BASE=https://clob.polymarket.com
EXECUTION_MODE=paper
ACTIVE_STATIONS=EGLC,KLGA
EDGE_MIN=0.05
FEE_BP=50
SLIPPAGE_BP=30
KELLY_CAP=0.10
DAILY_BANKROLL_CAP=3000
PER_MARKET_CAP=500
LIQUIDITY_MIN_USD=1000
LOG_LEVEL=INFO
EOF

# Then edit .env to add your real Zeus API key
```

### Usage

#### Fetch Zeus forecast
```bash
python -m core.orchestrator --mode fetch --date 2025-10-27 --station EGLC
```

#### Map probabilities
```bash
python -m core.orchestrator --mode probmap --date 2025-10-27 --station EGLC
```

#### Run paper trading
```bash
python -m core.orchestrator --mode paper --stations EGLC,KLGA
```

#### Backtest historical data
```bash
python -m core.orchestrator --mode backtest --start 2025-10-01 --end 2025-10-31 --stations EGLC,KLGA
```

#### Run dynamic paper trading (continuous loop)
```bash
python -m core.orchestrator --mode dynamic-paper --stations EGLC,KLGA
```

#### Start backend API server
```bash
cd backend
pip install -r requirements.txt
python -m api.main
# Or: uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

## Project Structure

```
hermes/
├── core/              # Main orchestration and utilities
│   ├── orchestrator.py
│   ├── config.py
│   ├── time_utils.py
│   ├── units.py
│   ├── types.py
│   └── logger.py
├── agents/            # Forecast, probability mapping, sizing
│   ├── zeus_forecast.py
│   ├── prob_mapper.py
│   ├── edge_and_sizing.py
│   ├── backtester.py
│   ├── prob_models/   # Probability models (spread, bands)
│   └── dynamic_trader/ # Dynamic trading engine
├── venues/            # Market-specific adapters
│   ├── polymarket/
│   │   ├── discovery.py
│   │   ├── pricing.py
│   │   ├── execute.py
│   │   ├── resolution.py
│   │   └── schemas.py
│   └── metar/         # METAR weather observations
│       └── metar_service.py
├── backend/           # FastAPI backend API
│   ├── api/
│   │   ├── main.py
│   │   ├── routes/    # API endpoints
│   │   ├── services/  # Data services
│   │   ├── models/    # Pydantic schemas
│   │   └── utils/     # Utilities
│   └── requirements.txt
├── data/              # Data storage
│   ├── registry/
│   │   └── stations.csv    # 9 weather stations (Polymarket + Kalshi) ✅
│   ├── snapshots/     # Raw API pulls
│   │   ├── zeus/      # Zeus forecasts
│   │   ├── polymarket/ # Polymarket data
│   │   └── dynamic/   # Dynamic trading snapshots
│   ├── trades/        # Trade logs (CSV format)
│   └── runs/          # Backtest results
├── tests/             # Test suite (138 tests, 100% passing)
└── docs/
    └── build/         # Build documentation (stage details)
```

## Configuration

Key settings in `.env`:

- `ZEUS_API_KEY`: Your Zeus weather API key
- `EXECUTION_MODE`: `paper` or `live`
- `EDGE_MIN`: Minimum edge to trade (default 0.05 = 5%)
- `KELLY_CAP`: Max Kelly fraction per decision (default 0.10 = 10%)
- `DAILY_BANKROLL_CAP`: Daily capital limit (default $3000)
- `PER_MARKET_CAP`: Per-market position limit (default $500)
- `LIQUIDITY_MIN_USD`: Minimum market liquidity (default $1000)

For advanced configuration, create `config.local.yaml` to override defaults.

## Development

### Run tests
```bash
pytest  # 138 tests (Stages 0-7D-2 complete!)
# or: make test
```

### Format code
```bash
black .
ruff check --fix .
```

### Type checking
```bash
mypy core agents venues
```

## Roadmap

- [x] **Stage 0**: Repo bootstrap ✅
- [x] **Stage 1**: Data registry + utilities ✅
- [x] **Stage 2**: Zeus forecast agent ✅
- [x] **Stage 3**: Probability mapper ✅
- [x] **Stage 4**: Polymarket adapters ✅
- [x] **Stage 5**: Edge & Kelly sizing ✅
- [x] **Stage 6**: Paper execution loop ✅ **← MVP COMPLETE!**
- [x] **Stage 7**: Backtest harness ✅
- [x] **Stage 7A**: Resolution integration ✅
- [x] **Stage 7B**: Dual probability models ✅
- [x] **Stage 7C**: Dynamic trading engine ✅
- [x] **Stage 7D-1**: METAR integration ✅
- [x] **Stage 7D-2**: Backend API structure ✅
- [ ] **Stage 7D-3+**: Frontend dashboard (in progress)
- [ ] **Stage 8**: Live execution
- [ ] **Stage 9**: Post-trade metrics
- [ ] **Stage 10**: Resolution validation
- [ ] **Stage 11**: Kalshi adapter

**Progress**: 7.5/11 stages (68%) • **MVP + Backend API achieved!** 🎉

See [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) for detailed implementation plan.  
See `docs/build/` for complete stage-by-stage documentation.

## License

MIT License - see [LICENSE](LICENSE) file.

## Guardrails

- **Precision**: Final verification uses whole °F (nearest integer; 0.5 rounds up)
- **Timezones**: DST-aware UTC conversions for all market times
- **Liquidity**: Never exceed `PER_MARKET_CAP` or available depth
- **Snapshots**: All data written to disk for audit trails
- **Paper-first**: Defaults to paper trading; live requires explicit config

## Monitoring & Outputs

### When Running Paper Trading

The system generates multiple outputs for monitoring:

#### 1. Console Logs (Real-time)

Watch the pipeline progress with structured logging:

```
[INFO] 📄 Running paper trading for stations: EGLC, KLGA
[INFO] Execution mode: paper
[INFO] Bankroll: $3000.00

============================================================
Processing station: EGLC
============================================================
[INFO] Station: London (EGLC)

🌡️  Step 1: Fetching Zeus forecast...
[INFO] ✅ Fetched 24 hourly forecasts
[INFO] Temperature range: 57.2°F - 70.0°F

🔍 Step 2: Discovering Polymarket brackets...
[INFO] ✅ Discovered 12 brackets

📊 Step 3: Mapping Zeus probabilities...
[INFO] Daily high distribution: μ = 65.23°F, σ = 2.45°F
[INFO] ✅ Mapped probabilities for 12 brackets

💰 Step 4: Fetching market probabilities...
[INFO] ✅ Got prices for 12/12 brackets

⚖️  Step 5: Computing edge and sizing positions...
[INFO] ✅ Generated 3 trade decisions

Top trade opportunities:
  1. [65-66°F): edge=8.50%, size=$285.00
  2. [64-65°F): edge=6.20%, size=$210.00
  3. [66-67°F): edge=5.30%, size=$180.00

============================================================
📝 Executing Paper Trades
============================================================
[INFO] 📄 Placing 3 paper trades
[INFO]   📝 [65-66°F): $285.00 @ edge=8.50%
[INFO]   📝 [64-65°F): $210.00 @ edge=6.20%
[INFO]   📝 [66-67°F): $180.00 @ edge=5.30%
[INFO] ✅ Recorded 3 paper trades to data/trades/2025-11-05/paper_trades.csv

✅ Paper trading complete!
Total decisions: 3
Total size: $675.00
Average edge: 6.67%
```

#### 2. Trade Logs (CSV)

**Location**: `data/trades/{YYYY-MM-DD}/paper_trades.csv`

**Example**:
```csv
timestamp,station_code,bracket_name,bracket_lower_f,bracket_upper_f,market_id,edge,edge_pct,f_kelly,size_usd,p_zeus,p_mkt,sigma_z,reason
2025-11-05T09:15:23+00:00,EGLC,65-66°F,65,66,market_65_66,0.085000,8.5000,0.285000,285.00,,,,"strong_edge"
2025-11-05T09:15:23+00:00,EGLC,64-65°F,64,65,market_64_65,0.062000,6.2000,0.210000,210.00,,,,"kelly_capped"
```

**Monitor with**:
```bash
# View today's trades
cat data/trades/$(date +%Y-%m-%d)/paper_trades.csv

# Count trades
wc -l data/trades/$(date +%Y-%m-%d)/paper_trades.csv

# Watch in real-time
tail -f data/trades/$(date +%Y-%m-%d)/paper_trades.csv
```

#### 3. Data Snapshots

**Zeus Forecasts**: `data/snapshots/zeus/{YYYY-MM-DD}/{station}.json`
```json
{
  "forecast": [
    {"time": "2025-11-05T00:00:00Z", "temperature_k": 288.15},
    {"time": "2025-11-05T01:00:00Z", "temperature_k": 287.95},
    ...
  ]
}
```

**Polymarket Markets**: `data/snapshots/polymarket/markets/{city}_{date}.json`
```json
[
  {
    "id": "market_65_66",
    "question": "Will London high be 65-66°F?",
    "active": true
  }
]
```

**Polymarket Prices**: `data/snapshots/polymarket/midpoint/{market_id}.json`
```json
{
  "mid": 0.6234,
  "market": "market_65_66"
}
```

#### 4. Daily Summary (in logs)

At the end of each run:
```
✅ Paper trading complete!
Total decisions: 5
Total size: $1,250.00
Average edge: 7.34%
Trades logged to: data/trades/2025-11-05/paper_trades.csv
```

### Monitoring Script

Create a simple monitoring script:

```python
# monitor_trades.py
import pandas as pd
from pathlib import Path
from datetime import date

today = date.today().strftime("%Y-%m-%d")
csv_path = Path(f"data/trades/{today}/paper_trades.csv")

if csv_path.exists():
    df = pd.read_csv(csv_path)
    
    print(f"📊 Trading Summary for {today}")
    print(f"=" * 50)
    print(f"Total trades: {len(df)}")
    print(f"Total size: ${df['size_usd'].sum():.2f}")
    print(f"Average edge: {df['edge_pct'].mean():.2f}%")
    print(f"Max edge: {df['edge_pct'].max():.2f}%")
    print(f"Stations: {', '.join(df['station_code'].unique())}")
    print()
    print("Top 5 trades by edge:")
    print(df.nlargest(5, 'edge_pct')[['bracket_name', 'edge_pct', 'size_usd']])
else:
    print(f"No trades found for {today}")
```

### What to Watch For

**Good Signs** ✅:
- Forecasts fetched successfully (24 points per station)
- Brackets discovered (10-15 typical)
- Probabilities sum to 1.0
- Some edges > 5% (minimum threshold)
- Trades recorded to CSV

**Warning Signs** ⚠️:
- No brackets discovered → Check Polymarket has markets for that city/date
- No edges > 5% → Markets are efficient, no opportunities
- API errors → Check API keys and network

**Errors to Fix** ❌:
- "Station not found" → Check station code in registry
- "Zeus API error" → Check ZEUS_API_KEY in .env
- "No valid forecast points" → API response format changed

### Daily Operations

```bash
# Morning: Run paper trading
python -m core.orchestrator --mode paper --stations EGLC,KLGA

# Check results
cat data/trades/$(date +%Y-%m-%d)/paper_trades.csv

# Analyze
python monitor_trades.py

# Review snapshots (for debugging)
ls -lh data/snapshots/zeus/$(date +%Y-%m-%d)/
ls -lh data/snapshots/polymarket/markets/
```

## Backend API

The FastAPI backend provides REST endpoints for monitoring and dashboard integration.

### Starting the Server

```bash
cd backend
pip install -r requirements.txt
python -m api.main
# Or: uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

### API Endpoints

- **Health**: `GET /health` - Health check
- **Status**: `GET /api/status` - System status
- **Snapshots**: 
  - `GET /api/snapshots/zeus?station_code=EGLC&event_day=2025-11-13`
  - `GET /api/snapshots/polymarket?city=London&event_day=2025-11-13`
  - `GET /api/snapshots/decisions?station_code=EGLC&event_day=2025-11-13`
  - `GET /api/snapshots/metar?station_code=EGLC&event_day=2025-11-13`
- **Trades**: 
  - `GET /api/trades/recent?limit=100&station_code=EGLC`
  - `GET /api/trades/summary?trade_date=2025-11-13`
- **Logs**: `GET /api/logs/activity?limit=100&station_code=EGLC`

### Interactive API Documentation

Open http://localhost:8000/docs in your browser for interactive API documentation with "Try it out" buttons.

See `backend/README.md` for detailed API documentation.

## Support

For questions or issues, refer to the [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) documentation.

For detailed stage documentation, see `docs/build/` directory.

