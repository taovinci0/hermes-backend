# Hermes v1 — Weather→Markets Trading System (Polymarket-first, Kalshi-ready)

## What we're building (in one paragraph)

Hermes ingests hourly Zeus weather forecasts, converts them into bracket probabilities for city temperature "daily high" markets, compares those to Polymarket's implied probabilities, sizes trades by edge & liquidity, and executes/monitors positions. It's modular: Polymarket is the first venue; Kalshi drops in later by adding a parallel adapter without touching core logic.

## High-level architecture

```
hermes/
  core/
    orchestrator.py        # main loop: pull → infer → decide → execute → log
    config.py              # ENV, locations, thresholds, fees, spreads
    time_utils.py          # tz/DST helpers
    units.py               # K↔°C↔°F, rounding & "resolve to whole °F" helpers
    types.py               # Typed models (pydantic/dataclasses) for I/O
    logger.py              # structured logging

  agents/
    zeus_forecast.py       # ZeusForecastAgent: fetch hourly temps (K), 24h window
    prob_mapper.py         # ProbabilityMapper: Zeus→p_zeus(brackets), σ_Z
    edge_and_sizing.py     # EV, Kelly, bankroll caps, min-liquidity filters

  venues/
    polymarket/
      discovery.py         # MarketDiscoveryAgent: Gamma /events, /markets
      pricing.py           # MarketPriceAgent: CLOB midprice, depth, price history
      execute.py           # Execution: paper first; live later
      schemas.py           # DTOs for Gamma & CLOB payloads
    # kalshi/
      # discovery.py, pricing.py, execute.py, schemas.py  (drop-in later)

  data/
    registry/              # stations.csv (EGLC, KLGA, etc.)
    snapshots/             # raw pulls (Zeus, market); auto-dated
    trades/                # fills/logs (CSV/Parquet)
    runs/                  # daily run folders (artifacts)

  tests/
    test_prob_mapper.py
    test_edge_and_sizing.py
```

## Stage-by-stage build plan (each stage is a small, testable PR)

### Stage 0 — Repo bootstrap

**Tasks**

- Create repo with the structure above.
- Add `pyproject.toml` (or `requirements.txt`) for: `pydantic`, `requests`, `pytz`, `python-dateutil`, `pandas`, `numpy`, `tenacity`, `websockets` (later), `pytest`, `rich`.
- Add `README.md` (use this plan), `LICENSE`, and a simple `Makefile` or `justfile`.

**Env & config**

`.env.sample`:
```bash
ZEUS_API_BASE=https://api.zeussubnet.com
ZEUS_API_KEY=changeme

POLY_GAMMA_BASE=https://gamma-api.polymarket.com
POLY_CLOB_BASE=https://clob.polymarket.com

# paper trading only for v1
EXECUTION_MODE=paper
```

`core/config.py` reads from env + a `config.local.yaml` (optional overrides).

### Stage 1 — Data registry + utilities

**Deliverables**

- `data/registry/stations.csv` with at least: `city,station_code,lat,lon,venue_slug_hint,time_zone`
  - Example rows:
    - `London,EGLC,51.505,0.05,London City Airport,Europe/London`
    - `New York,KLGA,40.7769,-73.8740,LaGuardia,America/New_York`
    - `NYC_CentralPark,CENTRAL_PARK,40.7789,-73.9692,Central Park,America/New_York`

- `core/units.py`: Kelvin↔°C↔°F, and "resolve to whole °F" helper (round to nearest integer; .5→round up since WU/NWS report whole °F).

- `core/time_utils.py`: helpers for "local day window" → UTC ISO start/end; DST-safe.

- `core/types.py`: typed models:
  - `ForecastPoint(time_utc: datetime, temp_K: float)`
  - `ZeusForecast(timeseries: list[ForecastPoint])`
  - `MarketBracket(name: str, lower_F: int, upper_F: int)` (upper exclusive for [59–60])
  - `BracketProb(bracket: MarketBracket, p_zeus: float, p_mkt: float | None)`
  - `EdgeDecision(bracket: MarketBracket, edge: float, f_kelly: float, size_usd: float)`

**Tests**

- `test_units.py` for conversions & rounding rules.

### Stage 2 — ZeusForecastAgent

**Goal**: For a given station & date, pull 24h hourly temps via Zeus `/forecast` using `start_time` + `predict_hours=24`.

**Implementation**

`agents/zeus_forecast.py`:
- `get_hourly_temp(lat, lon, start_time_utc, predict_hours=24) -> ZeusForecast`
- Persist raw JSON to `data/snapshots/zeus/{YYYY-MM-DD}/{station}.json`.

**Acceptance**

CLI scratch in `orchestrator.py` (temporary): fetch for EGLC & KLGA for a known date and store.

### Stage 3 — ProbabilityMapper (p₍Zeus₎) + σ_Z

**Goal**: Convert Zeus hourly temps into daily-high distribution over venue brackets.

**Implementation**

`agents/prob_mapper.py`:
- Compute daily high mean μ as the max of hourly temps (°F) after converting K→F.
- Estimate σ_Z from Zeus bands when present (your method A): derive σ from likely (≈80%) and possible (≈95%) upper bounds if available; otherwise fall back to a calibrated σ default per city/season.
- For each bracket [a,b] °F, compute:
  ```
  p_zeus = Φ((b-μ)/σ) - Φ((a-μ)/σ)
  ```
  (with guardrails: σ minimum, and mass rebalance to sum≈1 across bracket set).

**Tests**

`test_prob_mapper.py` with synthetic μ/σ and brackets to ensure probabilities sum ≈1 and behave monotonic.

### Stage 4 — Polymarket adapters (discovery + pricing)

**Goal**: Detect daily temp markets, map their brackets, and read market-implied probabilities.

**Implementation**

- `venues/polymarket/schemas.py`: DTOs for Gamma responses.

- `venues/polymarket/discovery.py`:
  - `list_daily_temp_markets(city, date_local) -> list[MarketBracket]`
  - (Use Gamma `/events` or `/markets` by slug/tag; parse bracket names like "59–60°F".)

- `venues/polymarket/pricing.py`:
  - `get_midprob_for_bracket(market_id) -> float` (midprice / 1.0)
  - Optional: `get_depth(market_id) -> dict(levels)` for liquidity proxy Lₚ.
  - Optional: `/prices-history` backfill for backtests.

**Snapshots**

Save Gamma & CLOB pulls to `data/snapshots/polymarket/...`.

### Stage 5 — Edge & Kelly sizing

**Goal**: Turn `(p_zeus, p_mkt, fees, spread, liquidity)` into sized orders.

**Implementation**

`agents/edge_and_sizing.py`:
- `compute_edge(p_zeus, p_mkt) -> float`
- `expected_value = (p_zeus - p_mkt) - fee - slip` (configurable)
- Kelly fraction for binary payoff `b=(1/price - 1)`: `f* = (b*p - q)/b`, clipped [0, f_max], then scaled by liquidity proxy Lₚ and bankroll rules.

Config thresholds in `core/config.py`: `EDGE_MIN`, `FEE`, `SLIPPAGE_BP`, `F_MAX`, `BANKROLL_DAILY_MAX`, `PER_MARKET_MAX`.

### Stage 6 — Paper execution loop (MVP)

**Goal**: Full pipeline without placing real orders.

**Implementation**

- `venues/polymarket/execute.py`:
  - `PaperBroker` that records "intended orders" with timestamp, bracket, price, size_usd, reason (edge, σ_Z).

- `core/orchestrator.py`:
```python
for station in active_stations:
  zeus = ZeusForecastAgent.fetch(station, local_date_today)
  brackets = Discovery.list_daily_temp_markets(station.city, date)
  p_zeus = ProbMapper.map(zeus, brackets)
  p_mkt  = Pricing.midprobs(brackets)
  decisions = Sizing.decide(p_zeus, p_mkt, liquidity)
  PaperBroker.place(decisions)
  Logger.write(trades + snapshot metrics)
```

Artifacts: write CSV to `data/trades/{YYYY-MM-DD}/paper_trades.csv`.

### Stage 7 — Backtest harness (realistic "as if at open")

**Goal**: Reproduce your manual workflow programmatically.

**Implementation**

- Use Polymarket `/prices-history` to pull opening midprices for each bracket; align with Zeus forecast snapshot from market open time (or defined entry window).
- Run across the date range (e.g., Oct 1–31) for London & NYC.
- Output summary: hit rate, ROI, EV by bracket, drawdowns. Save to `data/runs/backtests/...`.

**Acceptance**

A single CLI:
```bash
python -m core.orchestrator --mode backtest --start 2025-10-01 --end 2025-10-31 --cities EGLC,KLGA
```

### Stage 8 — Live execution (optional switch)

**Goal**: Swap `PaperBroker` to `LiveBroker` (once comfortable).

**Implementation**

- `venues/polymarket/execute.py`: add `LiveBroker` with authenticated calls (or py-clob-client), plus dry-run preview mode.
- Global `EXECUTION_MODE` switch.

### Stage 9 — Post-trade metrics & dashboards

**Deliverables**

- Daily summary CSV + small HTML report (P&L, hit rate, EV realized vs expected).
- Rolling accuracy table: Zeus vs resolution (add later via Stage 10).

### Stage 10 — Resolution validation (Aviation Weather, future)

**Goal**: Verify "true highs" from AviationWeather.gov (METAR/ASOS) instead of WU pages.

**Where it fits**

New agent `agents/resolution_awc.py`:
- `fetch_daily_observations(station_code, date_local) -> list[MetarObs]`
- `derive_daily_high_F(observations) -> int` (whole °F)

Consumed by backtests & daily auditing. Lives alongside Zeus & market snapshots.

### Stage 11 — Kalshi adapter (drop-in later)

- Add `venues/kalshi/{discovery,pricing,execute,schemas}.py`.
- Keep orchestrator venue-agnostic by routing via an interface.

## Configuration (minimum you need to run)

`core/config.py` (defaults, editable via env):

```python
ACTIVE_STATIONS = ["EGLC", "KLGA"]   # use data/registry/stations.csv
BRACKETS_F = [(59,60),(61,62),(63,64), ...]  # or parse from venue discovery
EDGE_MIN = 0.05             # 5% minimum edge
FEE_BP = 50                 # 0.50% effective fees
SLIPPAGE_BP = 30            # assumed
KELLY_CAP = 0.10            # max 10% of bankroll per decision (pre-liquidity)
DAILY_BANKROLL_CAP = 3000   # start; raise to 12k later
PER_MARKET_CAP = 500        # guardrail
LIQUIDITY_MIN_USD = 1000    # skip illiquid brackets
```

## How you'll actually use it (developer flow)

### Install & set env

```bash
uv venv && uv pip install -r requirements.txt  # or pip/poetry
cp .env.sample .env  # add ZEUS key
```

### Smoke test Zeus fetch

```bash
python -m core.orchestrator --mode fetch --date 2025-10-27 --station EGLC
```

### Map probabilities offline

```bash
python -m core.orchestrator --mode probmap --date 2025-10-27 --station EGLC
```

### Paper run (end-to-end)

```bash
python -m core.orchestrator --mode paper --stations EGLC,KLGA
```

### Backtest (Oct 1–31, London+NYC)

```bash
python -m core.orchestrator --mode backtest --start 2025-10-01 --end 2025-10-31 --stations EGLC,KLGA
```

### Inspect outputs

- Raw pulls in `data/snapshots/...`
- Paper trades in `data/trades/YYYY-MM-DD/paper_trades.csv`
- Backtest results in `data/runs/backtests/...`

## Minimal interfaces (so it stays modular)

```python
# agents/zeus_forecast.py
class ZeusForecastAgent:
    def fetch(self, lat: float, lon: float, start_utc: datetime, hours: int=24) -> ZeusForecast: ...

# agents/prob_mapper.py
class ProbabilityMapper:
    def map_daily_high(self, forecast: ZeusForecast, brackets: list[MarketBracket]) -> list[BracketProb]: ...

# venues/polymarket/discovery.py
class PolyDiscovery:
    def list_temp_brackets(self, city:str, date_local: date) -> list[MarketBracket]: ...

# venues/polymarket/pricing.py
class PolyPricing:
    def midprob(self, bracket: MarketBracket) -> float: ...
    def depth(self, bracket: MarketBracket) -> dict: ...  # optional

# agents/edge_and_sizing.py
class Sizer:
    def decide(self, probs: list[BracketProb], bankroll_usd: float) -> list[EdgeDecision]: ...

# venues/polymarket/execute.py
class Broker:
    def place(self, decisions: list[EdgeDecision]) -> None: ...
```

Kalshi later just implements the same 3: `Discovery`, `Pricing`, `Broker`.

## Test plan (tight & useful)

- `test_prob_mapper.py`: known μ/σ → bracket probabilities sum ≈1, shift correctly with μ.
- `test_edge_and_sizing.py`: EV & Kelly calculations for a few p_zeus/p_mkt combos, fee/slip sensitivity, caps.
- Quick integration test: mock Gamma payload for 3 brackets → ensure orchestrator produces N paper orders only when edge >= `EDGE_MIN` & Lₚ >= `LIQUIDITY_MIN_USD`.

## Guardrails & gotchas baked in

- **Precision/Resolution**: final verification uses whole °F (nearest integer; .5 rounds up).
- **Timezones/DST**: `time_utils` always converts local midnight → next midnight to UTC for Zeus fetch.
- **Liquidity awareness**: never size beyond `PER_MARKET_CAP` or top-of-book estimated fill.
- **Data snapshots**: everything is written to disk for audit and replays.
- **Live switch**: execution mode is a single toggle; defaults to paper.

## What's not in v1 (on purpose)

- LLMs (not required for this pipeline).
- Reward farming/LP making.
- Cross-venue hedging.
- UI (you can add a thin Streamlit later if you want visual controls).

