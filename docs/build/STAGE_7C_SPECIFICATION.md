# Stage 7C – Dynamic Forecast & Dynamic Pricing Trading Engine

**Project**: Hermes Prediction Market Agent  
**Stage**: 7C  
**Status**: Planned  
**Purpose**: Enable dynamic trading using continuously updating Zeus forecasts and Polymarket markets that open 1–2 days before event resolution.

---

## 🔷 Overview

Stage 7C upgrades Hermes from a static, once-per-day trader to a **dynamic real-time trading agent**.

### Hermes will now:

- ✅ Detect Polymarket markets as soon as they open (1–2 days early)
- ✅ Fetch Zeus forecasts **just-in-time** using **LOCAL start time**
- ✅ Fetch Polymarket pricing **just-in-time**
- ✅ Compute edge dynamically based on fresh data
- ✅ Execute paper trades dynamically throughout the pre-event window
- ✅ Store timestamped snapshots of Zeus, Polymarket pricing, and decisions
- ✅ Enable future full replay backtesting
- ✅ Continue using resolution-only backtesting (for now)

**Important**: This stage does not modify probability models, backtester, or resolution logic.
It adds a new dynamic execution engine alongside current systems.

---

## 🔷 Goals of Stage 7C

### 1. Add Polymarket early-market awareness

Hermes should begin analyzing markets as soon as they appear (T-2 → T).

**Current**: Only trades on event day (T)  
**New**: Monitors markets from T-2 to T (when they open)

### 2. Add dynamic Zeus + Polymarket fetching

Forecasts and prices update continuously — Hermes must use fresh data.

**Current**: Fetch once per day, use static data  
**New**: Fetch every evaluation cycle (e.g., every 15 minutes)

### 3. Add configurable dynamic paper trading loop

Hermes should:
- Evaluate markets on a configurable interval
- Place paper trades immediately after evaluation
- Save Zeus + Polymarket + decision snapshots each cycle

### 4. Prepare for future full historical backtesting

We must collect our own timestamped historical snapshots of:
- Zeus forecasts (with local start times)
- Polymarket pricing
- Decisions and edges

### 5. Preserve current backtesting

Resolution-only backtesting remains the only valid form until enough dynamic data is collected.

---

## 🔷 Architecture Additions

### Create New Module:

```
agents/dynamic_trader/
├── __init__.py
├── dynamic_engine.py    # Main loop orchestrator
├── fetchers.py          # JIT Zeus + Polymarket fetching
├── evaluators.py        # Fresh edge calculation
└── snapshotter.py       # Timestamped data persistence
```

### Add New Orchestrator Mode:

```bash
python -m core.orchestrator --mode dynamic-paper --stations EGLC,KLGA
```

This mode runs continuously until stopped (Ctrl+C).

---

## 🔷 Updated Requirements (With Your Adjustments)

### 1. Detect Polymarket Markets Early

**Add method:**
```python
def find_open_events_for_station(station, event_day):
    """Find Polymarket events for a station/day.
    
    Markets may have opened 1-2 days ago but are still trading.
    """
```

**Hermes now watches for:**
- Today's markets (T)
- Tomorrow's markets (T+1)
- Which may have opened 1–2 days earlier

---

### 2. Just-In-Time Zeus Fetching (LOCAL TIME)

**IMPORTANT (Your Update):**

**Zeus expects the start parameter in LOCAL time for that station.**
- **No timezone conversion**
- **No UTC conversion**
- If London → pass `2025-11-12T00:00:00+00:00`
- If NYC → pass `2025-11-12T00:00:00-05:00`

**Corrected Logic:**

```python
# Get local midnight for the event day
local_midnight = datetime.combine(
    event_day, 
    time(0, 0), 
    tzinfo=ZoneInfo(station.time_zone)
)

# Pass LOCAL time directly to Zeus (NO UTC conversion!)
zeus_forecast = zeus_agent.fetch(
    lat=station.lat,
    lon=station.lon,
    start_local=local_midnight,  # ← Used directly, no conversion to UTC
    hours=24,
)
```

**Snapshot Path:**
```
data/snapshots/dynamic/zeus/{station}/YYYY-MM-DD_HH-MM.json
```

**Snapshot Schema:**
```json
{
  "fetch_time_utc": "2025-11-12T14:30:00Z",
  "start_local": "2025-11-12T00:00:00-05:00",
  "forecast_for_local_day": "2025-11-12",
  "model_mode": "spread",
  "station_code": "KLGA",
  "data": {
    "2m_temperature": {...},
    "time": {...}
  }
}
```

---

### 3. Just-In-Time Polymarket Pricing

**Each cycle:**
- Fetch all open brackets for the event
- Fetch YES/NO prices, bids, asks, mid
- Save snapshot with timestamp

**Snapshot Path:**
```
data/snapshots/dynamic/polymarket/{event_slug}/YYYY-MM-DD_HH-MM.json
```

**Snapshot Schema:**
```json
{
  "fetch_time_utc": "2025-11-12T14:30:00Z",
  "event_slug": "highest-temperature-in-nyc-on-november-12",
  "markets": [
    {
      "market_id": "669642",
      "bracket": "58-59°F",
      "mid_price": 0.3456,
      "bid": 0.3401,
      "ask": 0.3512,
      "volume": 125000
    }
  ]
}
```

---

### 4. Dynamic Edge Evaluation

**Evaluator computes:**
- `p_zeus` from selected model (spread/bands)
- `p_market` from real-time Polymarket midprice
- `edge = p_zeus - p_market - fees`
- Kelly sizing
- Caps / liquidity checks

**Same output format as Stage 7A/7B.**

---

### 5. Dynamic Paper Trading Executor

**Executes trades immediately after edge evaluation to minimize data staleness.**

**Trade logs stored:**
```
data/trades/dynamic/YYYY-MM-DD/
└── EGLC_14-05-00.csv
```

**CSV Format:**
```csv
timestamp,station,city,event_day,bracket,p_zeus,p_market,edge,size_usd,model_mode
2025-11-12T14:05:00Z,EGLC,London,2025-11-12,58-59°F,0.3456,0.3201,0.0175,250.00,spread
```

---

### 6. Scheduler (Your Adjustment Included)

**Add to `.env`:**
```bash
# Dynamic Trading Configuration (Stage 7C)
DYNAMIC_INTERVAL_SECONDS=900    # Default: 15 minutes
DYNAMIC_LOOKAHEAD_DAYS=2        # Check today + tomorrow
MODEL_MODE=spread
```

**Hermes dynamic loop:**
```python
while True:
    # Check today + tomorrow's events
    event_days = [today + timedelta(days=i) for i in range(config.DYNAMIC_LOOKAHEAD_DAYS)]
    
    for station in stations:
        for event_day in event_days:
            evaluate_and_trade(station, event_day)
    
    sleep(config.DYNAMIC_INTERVAL_SECONDS)
```

---

## 🔷 Backtesting Strategy Update

### Resolution-Only Backtesting

**Status**: ✔ Remains valid  
**Implementation**: ✔ Already implemented (Stage 7A)  
**Usage**: ✔ Continue using for correctness validation

**What it does:**
- Validates Zeus forecast accuracy
- Shows: Zeus prediction vs actual outcome
- No P&L calculation (no historical prices)

---

### Full Replay Backtesting

**Status**: ❌ Not possible without historical data  
**Reason**: Need timestamped snapshots of:
- Zeus forecasts (with timestamps)
- Polymarket pricing (with timestamps)

**Stage 7C solves this:**

Hermes starts collecting timestamped historical data, enabling:
- ✅ Full replay backtesting
- ✅ Model comparison (spread vs bands)
- ✅ Edge tracking over time
- ✅ Forecast evolution analysis

**Timeline:**
```
Week 1: Implement Stage 7C
Week 2: Collect dynamic data (7 days)
Week 3: Run first full replay backtest on Week 2 data
```

---

## 🔷 File Changes Summary

### New Files

```
agents/dynamic_trader/
├── __init__.py
├── dynamic_engine.py     # Main loop orchestrator
├── fetchers.py           # JIT Zeus + Polymarket fetching
├── evaluators.py         # Fresh edge calculation
└── snapshotter.py        # Timestamped data persistence
```

### Existing Files to Update

- `core/orchestrator.py` → Add `--mode dynamic-paper`
- `.env` → Add dynamic interval config
- `venues/polymarket/discovery.py` → Early-event detection
- `agents/zeus_forecast.py` → Accept `start_local` parameter (no UTC conversion)

### Unchanged Files

- `prob_models/` (Stage 7A/7B) - No changes
- `backtester.py` - No changes
- `resolution.py` - No changes

---

## 🔷 Example Dynamic Execution Loop (Corrected to LOCAL Time)

```python
def dynamic_paper_runner(stations: List[str], interval_seconds: int):
    """
    Continuously evaluate and trade on open markets.
    
    Markets open 1-2 days before event, so we check:
    - Today's events (may have opened 1-2 days ago)
    - Tomorrow's events (may have opened yesterday)
    """
    logger.info("🔄 Starting dynamic paper trading loop")
    logger.info(f"Interval: {interval_seconds}s ({interval_seconds/60:.0f} minutes)")
    
    while True:
        cycle_start = datetime.now(UTC)
        logger.info(f"\n{'='*70}")
        logger.info(f"🔄 EVALUATION CYCLE: {cycle_start.isoformat()}")
        logger.info(f"{'='*70}")
        
        for station_code in stations:
            station = registry.get(station_code)
            
            # Check today + tomorrow (markets may be open already)
            event_days = [
                date.today(),
                date.today() + timedelta(days=1)
            ]
            
            for event_day in event_days:
                logger.info(f"\n📍 {station.city} - {event_day}")
                
                # Check if market exists and is open
                events = discovery.find_open_events_for_station(
                    station.city, 
                    event_day
                )
                
                if not events:
                    logger.debug(f"No open events for {station.city} on {event_day}")
                    continue
                
                logger.info(f"Found {len(events)} open events")
                
                # 1. Fetch Zeus using LOCAL time (CORRECTED!)
                local_midnight = datetime.combine(
                    event_day, 
                    time(0, 0), 
                    tzinfo=ZoneInfo(station.time_zone)
                )
                
                logger.debug(f"Fetching Zeus for local day: {local_midnight}")
                
                forecast = zeus_agent.fetch(
                    lat=station.lat,
                    lon=station.lon,
                    start_local=local_midnight,  # ← LOCAL time, no conversion!
                    hours=24,
                )
                
                # 2. Fetch Polymarket pricing (dynamic, fresh)
                brackets = discovery.list_temp_brackets(station.city, event_day)
                
                market_data = []
                for bracket in brackets:
                    try:
                        p_mkt = pricing.midprob(bracket, save_snapshot=False)
                        market_data.append({
                            'bracket': bracket,
                            'p_mkt': p_mkt,
                        })
                    except Exception as e:
                        logger.warning(f"Failed to get price for {bracket.name}: {e}")
                
                # 3. Compute fresh edges (both inputs just fetched!)
                probs = prob_mapper.map_daily_high(forecast, brackets)
                
                # Add market probabilities
                for prob, mkt in zip(probs, market_data):
                    prob.p_mkt = mkt['p_mkt']
                
                # Calculate edges
                edges = sizer.decide(probs, config.trading.daily_bankroll_cap)
                
                # 4. Execute trades immediately (minimize staleness)
                trades = [e for e in edges if e.edge > 0]
                
                if trades:
                    logger.info(f"💰 Executing {len(trades)} trades")
                    broker.place(trades)
                else:
                    logger.debug(f"No edges found")
                
                # 5. Save timestamped snapshots
                snapshotter.save_zeus_snapshot(forecast, cycle_start)
                snapshotter.save_market_snapshot(market_data, cycle_start, event_day)
                snapshotter.save_decision_snapshot(edges, cycle_start, event_day)
        
        # Wait for next cycle
        cycle_end = datetime.now(UTC)
        cycle_duration = (cycle_end - cycle_start).total_seconds()
        
        logger.info(f"\n✅ Cycle complete in {cycle_duration:.1f}s")
        logger.info(f"😴 Sleeping for {interval_seconds}s...")
        
        sleep(interval_seconds)
```

---

## 🔷 Acceptance Criteria

### Hermes must:

**Dynamic Trading:**
- ✅ Detect markets 1–2 days before resolution
- ✅ Fetch Zeus & Polymarket using fresh timestamps
- ✅ Use Zeus **local start times**, not UTC
- ✅ Evaluate & execute within a small staleness window
- ✅ Produce timestamps for all data collected

**Snapshotting:**
- ✅ Save Zeus (local start) + Polymarket snapshots every cycle
- ✅ Save paper trades every cycle
- ✅ Organize everything by station/event/date

**Safety:**
- ✅ No breaking changes to 7A/7B models
- ✅ No real-money interactions
- ✅ Backtesting unaffected
- ✅ Dynamic trader modular & isolated

---

## 🔷 Detailed Implementation Plan

### Part 1: Early Market Detection

**File**: `venues/polymarket/discovery.py`

**Add method:**
```python
def find_open_events_for_station(
    self,
    city: str,
    event_day: date,
) -> List[dict]:
    """Find open Polymarket events for a city/day.
    
    Markets typically open 1-2 days before event day.
    This method checks if markets exist and are still open.
    
    Args:
        city: City name (e.g., "London", "New York")
        event_day: Event date (e.g., 2025-11-12)
    
    Returns:
        List of event dicts that are open for trading
    """
    slugs = self._generate_event_slugs(city, event_day)
    
    for slug in slugs:
        event = self.get_event_by_slug(slug, save_snapshot=False)
        if event:
            # Check if any markets are still open
            markets = event.get('markets', [])
            open_markets = [m for m in markets if not m.get('closed')]
            
            if open_markets:
                logger.info(
                    f"Found open event: {slug} "
                    f"({len(open_markets)}/{len(markets)} markets still open)"
                )
                return [event]
    
    return []
```

---

### Part 2: Just-In-Time Fetchers

**File**: `agents/dynamic_trader/fetchers.py`

```python
"""Just-in-time data fetching for dynamic trading."""

from datetime import datetime, date, time
from zoneinfo import ZoneInfo
from typing import List, Tuple

from core.logger import logger
from core.registry import Station
from core.types import MarketBracket
from agents.zeus_forecast import ZeusForecastAgent, ZeusForecast
from venues.polymarket.discovery import PolyDiscovery
from venues.polymarket.pricing import PolyPricing


class DynamicFetcher:
    """Fetch Zeus forecasts and Polymarket prices just-in-time."""
    
    def __init__(self):
        self.zeus = ZeusForecastAgent()
        self.discovery = PolyDiscovery()
        self.pricing = PolyPricing()
    
    def fetch_zeus_jit(
        self,
        station: Station,
        event_day: date,
    ) -> ZeusForecast:
        """Fetch Zeus forecast for event day using LOCAL time.
        
        IMPORTANT: Zeus API expects LOCAL time, not UTC.
        
        Args:
            station: Weather station with timezone
            event_day: Event date (e.g., 2025-11-12)
        
        Returns:
            Fresh Zeus forecast
        """
        # Get local midnight for the event day
        local_midnight = datetime.combine(
            event_day,
            time(0, 0),
            tzinfo=ZoneInfo(station.time_zone)
        )
        
        logger.debug(
            f"Fetching Zeus for {station.city} {event_day} "
            f"(local start: {local_midnight})"
        )
        
        # Fetch using LOCAL time (no UTC conversion!)
        forecast = self.zeus.fetch(
            lat=station.lat,
            lon=station.lon,
            start_utc=local_midnight,  # Actually local, not UTC!
            hours=24,
            station_code=station.station_code,
        )
        
        logger.info(
            f"✅ Fetched {len(forecast.timeseries)} Zeus points "
            f"(fetch time: {datetime.now(ZoneInfo('UTC')).isoformat()})"
        )
        
        return forecast
    
    def fetch_polymarket_jit(
        self,
        city: str,
        event_day: date,
    ) -> Tuple[List[MarketBracket], List[float]]:
        """Fetch Polymarket brackets and current prices.
        
        Args:
            city: City name
            event_day: Event date
        
        Returns:
            (brackets, prices) - Lists of same length
        """
        # Get brackets
        brackets = self.discovery.list_temp_brackets(
            city=city,
            date_local=event_day,
            save_snapshot=False,
        )
        
        if not brackets:
            return [], []
        
        # Get current prices
        prices = []
        for bracket in brackets:
            try:
                p_mkt = self.pricing.midprob(bracket, save_snapshot=False)
                prices.append(p_mkt)
            except Exception as e:
                logger.warning(f"Failed to get price for {bracket.name}: {e}")
                prices.append(None)
        
        valid_count = sum(1 for p in prices if p is not None)
        logger.info(
            f"✅ Fetched prices for {valid_count}/{len(brackets)} brackets "
            f"(fetch time: {datetime.now(ZoneInfo('UTC')).isoformat()})"
        )
        
        return brackets, prices
```

---

### Part 3: Dynamic Engine

**File**: `agents/dynamic_trader/dynamic_engine.py`

```python
"""Dynamic trading engine - continuous evaluation loop."""

from datetime import datetime, date, timedelta
from time import sleep
from zoneinfo import ZoneInfo
from typing import List

from core.config import config
from core.logger import logger
from core.registry import StationRegistry
from agents.dynamic_trader.fetchers import DynamicFetcher
from agents.dynamic_trader.evaluators import DynamicEvaluator
from agents.dynamic_trader.snapshotter import DynamicSnapshotter
from agents.prob_mapper import ProbabilityMapper
from agents.edge_and_sizing import Sizer
from venues.polymarket.execute import PaperBroker


class DynamicTradingEngine:
    """Continuous trading engine with dynamic Zeus + Polymarket fetching."""
    
    def __init__(
        self,
        stations: List[str],
        interval_seconds: int = 900,  # 15 minutes default
        lookahead_days: int = 2,
    ):
        """Initialize dynamic trading engine.
        
        Args:
            stations: List of station codes (e.g., ['EGLC', 'KLGA'])
            interval_seconds: Time between evaluation cycles
            lookahead_days: How many days ahead to check (1 = today only, 2 = today+tomorrow)
        """
        self.stations = stations
        self.interval_seconds = interval_seconds
        self.lookahead_days = lookahead_days
        
        # Components
        self.registry = StationRegistry()
        self.fetcher = DynamicFetcher()
        self.prob_mapper = ProbabilityMapper()
        self.sizer = Sizer(
            edge_min=config.trading.edge_min,
            fee_bp=config.trading.fee_bp,
            slippage_bp=config.trading.slippage_bp,
            kelly_cap=config.trading.kelly_cap,
            per_market_cap=config.trading.per_market_cap,
        )
        self.broker = PaperBroker()
        self.snapshotter = DynamicSnapshotter()
        
        logger.info(f"🚀 Dynamic Trading Engine initialized")
        logger.info(f"   Stations: {', '.join(stations)}")
        logger.info(f"   Interval: {interval_seconds}s ({interval_seconds/60:.0f} min)")
        logger.info(f"   Lookahead: {lookahead_days} days")
    
    def run(self):
        """Run continuous trading loop."""
        logger.info(f"\n{'='*70}")
        logger.info(f"🔄 STARTING DYNAMIC PAPER TRADING")
        logger.info(f"{'='*70}")
        logger.info(f"Press Ctrl+C to stop\n")
        
        cycle_count = 0
        
        try:
            while True:
                cycle_count += 1
                cycle_start = datetime.now(ZoneInfo("UTC"))
                
                logger.info(f"\n{'='*70}")
                logger.info(f"🔄 CYCLE {cycle_count}: {cycle_start.isoformat()}")
                logger.info(f"{'='*70}")
                
                # Evaluate each station
                for station_code in self.stations:
                    station = self.registry.get(station_code)
                    if not station:
                        logger.warning(f"Station {station_code} not found")
                        continue
                    
                    # Check today + next N days
                    today = date.today()
                    event_days = [
                        today + timedelta(days=i) 
                        for i in range(self.lookahead_days)
                    ]
                    
                    for event_day in event_days:
                        self._evaluate_and_trade(station, event_day, cycle_start)
                
                # Wait for next cycle
                cycle_end = datetime.now(ZoneInfo("UTC"))
                cycle_duration = (cycle_end - cycle_start).total_seconds()
                
                logger.info(f"\n✅ Cycle {cycle_count} complete in {cycle_duration:.1f}s")
                logger.info(f"😴 Sleeping for {self.interval_seconds}s...")
                
                sleep(self.interval_seconds)
        
        except KeyboardInterrupt:
            logger.info(f"\n\n{'='*70}")
            logger.info(f"🛑 Dynamic trading stopped by user")
            logger.info(f"{'='*70}")
            logger.info(f"Total cycles: {cycle_count}")
    
    def _evaluate_and_trade(
        self,
        station: Station,
        event_day: date,
        cycle_time: datetime,
    ):
        """Evaluate and trade a single station/event.
        
        Args:
            station: Weather station
            event_day: Event date to trade
            cycle_time: Current cycle timestamp
        """
        logger.info(f"\n  📊 Evaluating {station.city} for {event_day}...")
        
        try:
            # 1. Fetch Zeus (JIT, using LOCAL time)
            forecast = self.fetcher.fetch_zeus_jit(station, event_day)
            
            # 2. Fetch Polymarket (JIT)
            brackets, prices = self.fetcher.fetch_polymarket_jit(station.city, event_day)
            
            if not brackets:
                logger.debug(f"  No brackets available")
                return
            
            # 3. Map probabilities
            probs = self.prob_mapper.map_daily_high(forecast, brackets)
            
            # 4. Add market prices
            for prob, p_mkt in zip(probs, prices):
                prob.p_mkt = p_mkt
            
            # Filter out None prices
            valid_probs = [p for p in probs if p.p_mkt is not None]
            
            if not valid_probs:
                logger.debug(f"  No valid market prices")
                return
            
            # 5. Calculate edges and sizes
            decisions = self.sizer.decide(
                probs=valid_probs,
                bankroll_usd=config.trading.daily_bankroll_cap,
            )
            
            # Filter positive edges
            trades = [d for d in decisions if d.edge > 0]
            
            if trades:
                logger.info(f"  💰 Found {len(trades)} positive edges")
                
                # Execute immediately
                self.broker.place(trades)
                
                # Save snapshots
                self.snapshotter.save_all(
                    forecast=forecast,
                    brackets=brackets,
                    prices=prices,
                    decisions=trades,
                    cycle_time=cycle_time,
                    event_day=event_day,
                    station=station,
                )
            else:
                logger.debug(f"  No positive edges")
        
        except Exception as e:
            logger.error(f"  ❌ Error evaluating {station.city} {event_day}: {e}")
```

---

### Part 4: Snapshotter

**File**: `agents/dynamic_trader/snapshotter.py`

```python
"""Save timestamped snapshots for replay backtesting."""

import json
from datetime import datetime, date
from pathlib import Path
from typing import List

from core.config import PROJECT_ROOT
from core.logger import logger
from core.registry import Station
from core.types import EdgeDecision, MarketBracket
from agents.zeus_forecast import ZeusForecast


class DynamicSnapshotter:
    """Save timestamped snapshots of Zeus, Polymarket, and decisions."""
    
    def __init__(self):
        self.base_dir = PROJECT_ROOT / "data" / "snapshots" / "dynamic"
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def save_all(
        self,
        forecast: ZeusForecast,
        brackets: List[MarketBracket],
        prices: List[float],
        decisions: List[EdgeDecision],
        cycle_time: datetime,
        event_day: date,
        station: Station,
    ):
        """Save complete snapshot for this evaluation cycle.
        
        Args:
            forecast: Zeus forecast
            brackets: Market brackets
            prices: Market prices (aligned with brackets)
            decisions: Trading decisions
            cycle_time: When this cycle ran
            event_day: Event date
            station: Weather station
        """
        # Create timestamp string for filenames
        timestamp = cycle_time.strftime("%Y-%m-%d_%H-%M-%S")
        
        # Save Zeus snapshot
        self._save_zeus(forecast, station, event_day, timestamp)
        
        # Save Polymarket snapshot
        self._save_polymarket(brackets, prices, station.city, event_day, timestamp)
        
        # Save decision snapshot
        self._save_decisions(decisions, station, event_day, timestamp)
    
    def _save_zeus(
        self,
        forecast: ZeusForecast,
        station: Station,
        event_day: date,
        timestamp: str,
    ):
        """Save Zeus forecast snapshot."""
        zeus_dir = self.base_dir / "zeus" / station.station_code / event_day.isoformat()
        zeus_dir.mkdir(parents=True, exist_ok=True)
        
        snapshot_path = zeus_dir / f"{timestamp}.json"
        
        snapshot_data = {
            "fetch_time_utc": datetime.now(ZoneInfo("UTC")).isoformat(),
            "forecast_for_local_day": event_day.isoformat(),
            "station_code": station.station_code,
            "city": station.city,
            "timezone": station.time_zone,
            "model_mode": config.model_mode,
            "timeseries_count": len(forecast.timeseries),
            "forecast": {
                "timeseries": [
                    {
                        "time_utc": point.time_utc.isoformat(),
                        "temp_K": point.temp_K,
                    }
                    for point in forecast.timeseries
                ],
            },
        }
        
        with open(snapshot_path, "w") as f:
            json.dump(snapshot_data, f, indent=2)
        
        logger.debug(f"Saved Zeus snapshot: {snapshot_path}")
    
    def _save_polymarket(
        self,
        brackets: List[MarketBracket],
        prices: List[float],
        city: str,
        event_day: date,
        timestamp: str,
    ):
        """Save Polymarket pricing snapshot."""
        poly_dir = self.base_dir / "polymarket" / city.replace(" ", "_") / event_day.isoformat()
        poly_dir.mkdir(parents=True, exist_ok=True)
        
        snapshot_path = poly_dir / f"{timestamp}.json"
        
        snapshot_data = {
            "fetch_time_utc": datetime.now(ZoneInfo("UTC")).isoformat(),
            "event_day": event_day.isoformat(),
            "city": city,
            "markets": [
                {
                    "market_id": bracket.market_id,
                    "bracket": bracket.name,
                    "lower_f": bracket.lower_F,
                    "upper_f": bracket.upper_F,
                    "mid_price": price,
                    "closed": bracket.closed,
                }
                for bracket, price in zip(brackets, prices)
            ],
        }
        
        with open(snapshot_path, "w") as f:
            json.dump(snapshot_data, f, indent=2)
        
        logger.debug(f"Saved Polymarket snapshot: {snapshot_path}")
    
    def _save_decisions(
        self,
        decisions: List[EdgeDecision],
        station: Station,
        event_day: date,
        timestamp: str,
    ):
        """Save trading decisions snapshot."""
        decisions_dir = self.base_dir / "decisions" / station.station_code / event_day.isoformat()
        decisions_dir.mkdir(parents=True, exist_ok=True)
        
        snapshot_path = decisions_dir / f"{timestamp}.json"
        
        snapshot_data = {
            "decision_time_utc": datetime.now(ZoneInfo("UTC")).isoformat(),
            "event_day": event_day.isoformat(),
            "station_code": station.station_code,
            "city": station.city,
            "model_mode": config.model_mode,
            "decisions": [
                {
                    "bracket": decision.bracket.name,
                    "lower_f": decision.bracket.lower_F,
                    "upper_f": decision.bracket.upper_F,
                    "market_id": decision.bracket.market_id,
                    "edge": decision.edge,
                    "f_kelly": decision.f_kelly,
                    "size_usd": decision.size_usd,
                    "reason": decision.reason,
                }
                for decision in decisions
            ],
        }
        
        with open(snapshot_path, "w") as f:
            json.dump(snapshot_data, f, indent=2)
        
        logger.debug(f"Saved decisions snapshot: {snapshot_path}")
```

---

### Part 5: Orchestrator Integration

**File**: `core/orchestrator.py`

**Add new mode:**
```python
def run_dynamic_paper(stations_str: str) -> None:
    """Run dynamic paper trading loop.
    
    Continuously evaluates markets and executes paper trades using
    just-in-time Zeus forecasts and Polymarket pricing.
    
    Markets open 1-2 days before event, so we check:
    - Today's events
    - Tomorrow's events
    
    Args:
        stations_str: Comma-separated station codes
    """
    from agents.dynamic_trader.dynamic_engine import DynamicTradingEngine
    
    stations = [s.strip() for s in stations_str.split(',')]
    
    logger.info(f"🚀 Launching dynamic paper trading")
    logger.info(f"Stations: {', '.join(stations)}")
    
    # Create engine
    engine = DynamicTradingEngine(
        stations=stations,
        interval_seconds=config.get('DYNAMIC_INTERVAL_SECONDS', 900),
        lookahead_days=config.get('DYNAMIC_LOOKAHEAD_DAYS', 2),
    )
    
    # Run (blocks until Ctrl+C)
    engine.run()


# In main():
if args.mode == 'dynamic-paper':
    run_dynamic_paper(args.stations)
```

---

## 🔷 Configuration Updates

### `.env` additions:

```bash
# ============================================================================
# Dynamic Trading Configuration (Stage 7C)
# ============================================================================

# Evaluation interval (seconds)
# How often to fetch fresh Zeus + Polymarket data and re-evaluate edges
# Default: 900 seconds (15 minutes)
DYNAMIC_INTERVAL_SECONDS=900

# Lookahead days
# How many days ahead to check for open markets
# 1 = today only, 2 = today + tomorrow
DYNAMIC_LOOKAHEAD_DAYS=2

# Continue using model mode from Stage 7B
# MODEL_MODE=spread  (already defined above)
```

---

## 🔷 Data Structure

### New Snapshot Organization:

```
data/snapshots/dynamic/
├── zeus/
│   ├── EGLC/
│   │   └── 2025-11-12/
│   │       ├── 2025-11-12_09-00-00.json  # Morning cycle
│   │       ├── 2025-11-12_09-15-00.json  # +15 min
│   │       ├── 2025-11-12_09-30-00.json  # +30 min
│   │       └── ...
│   └── KLGA/
│       └── 2025-11-12/
│           └── ...
├── polymarket/
│   ├── London/
│   │   └── 2025-11-12/
│   │       └── 2025-11-12_09-00-00.json
│   └── New_York/
│       └── ...
└── decisions/
    ├── EGLC/
    │   └── 2025-11-12/
    │       └── 2025-11-12_09-00-00.json
    └── KLGA/
        └── ...
```

**Benefits:**
- ✅ Complete historical record
- ✅ Multiple snapshots per day
- ✅ Can replay any evaluation cycle
- ✅ Track forecast evolution
- ✅ Enable full replay backtesting

---

## 🔷 Usage Examples

### Start Dynamic Paper Trading:

```bash
# Run continuous loop (15-minute intervals)
python -m core.orchestrator --mode dynamic-paper --stations EGLC,KLGA

# Will output:
🚀 Dynamic Trading Engine initialized
   Stations: EGLC, KLGA
   Interval: 900s (15 min)
   Lookahead: 2 days

🔄 STARTING DYNAMIC PAPER TRADING
Press Ctrl+C to stop

═══════════════════════════════════════════════════════════════
🔄 CYCLE 1: 2025-11-12T14:00:00Z
═══════════════════════════════════════════════════════════════

  📊 Evaluating London for 2025-11-12...
  ✅ Fetched 24 Zeus points (fetch time: 2025-11-12T14:00:05Z)
  ✅ Fetched prices for 5/5 brackets (fetch time: 2025-11-12T14:00:08Z)
  💰 Found 2 positive edges
  📝 Placed 2 paper trades
  
  📊 Evaluating London for 2025-11-13...
  No open events for London on 2025-11-13
  
  📊 Evaluating NYC for 2025-11-12...
  ✅ Fetched 24 Zeus points (fetch time: 2025-11-12T14:00:15Z)
  ✅ Fetched prices for 6/6 brackets (fetch time: 2025-11-12T14:00:18Z)
  💰 Found 1 positive edge
  📝 Placed 1 paper trade

✅ Cycle 1 complete in 21.3s
😴 Sleeping for 900s...
```

---

### Monitor Snapshots:

```bash
# Check how many snapshots collected
ls data/snapshots/dynamic/zeus/EGLC/2025-11-12/
# Output: Multiple JSON files with timestamps

# View a snapshot
cat data/snapshots/dynamic/zeus/EGLC/2025-11-12/2025-11-12_14-00-00.json

# Shows:
{
  "fetch_time_utc": "2025-11-12T14:00:05Z",
  "forecast_for_local_day": "2025-11-12",
  "station_code": "EGLC",
  "city": "London",
  "timezone": "Europe/London",
  "model_mode": "spread",
  "timeseries_count": 24,
  "forecast": {...}
}
```

---

### View Trade History:

```bash
# See all trades from dynamic mode
cat data/trades/dynamic/2025-11-12/EGLC_14-00-00.csv

# Shows trades placed at 14:00:00
```

---

## 🔷 Benefits Over Static Approach

| Aspect | Static (Current) | Dynamic (Stage 7C) |
|--------|-----------------|-------------------|
| **Zeus Fetch** | Once per day | Every 15 min (configurable) |
| **Price Fetch** | Once per day | Every 15 min (configurable) |
| **Edge Accuracy** | Moderate (stale data) | High (fresh data) |
| **Staleness** | Hours | Minutes |
| **Opportunities** | Misses intraday edges | Catches edges as they appear |
| **Backtesting** | Resolution-only (limited) | Full replay (when ready) |
| **Data Collection** | Single snapshot/day | Multiple snapshots/day |
| **Market Timing** | Event day only | 1-2 days before event |

---

## 🔷 Testing Plan

### Unit Tests:

**File**: `tests/test_dynamic_trader.py`

```python
def test_dynamic_fetcher_zeus_local_time():
    """Test that Zeus is fetched with LOCAL time, not UTC."""
    
def test_dynamic_fetcher_polymarket():
    """Test Polymarket pricing fetch."""

def test_dynamic_engine_evaluation_cycle():
    """Test complete evaluation cycle."""

def test_snapshotter_saves_timestamps():
    """Test snapshots include correct timestamps."""

def test_early_market_detection():
    """Test detection of markets 1-2 days before event."""
```

### Integration Tests:

```bash
# Run for 1 hour with 5-minute intervals
python -m core.orchestrator --mode dynamic-paper \
  --stations EGLC \
  --interval 300

# Should produce:
# - 12 evaluation cycles
# - 12 Zeus snapshots
# - 12 Polymarket snapshots
# - N decision snapshots (if edges found)
```

---

## 🔷 Success Criteria

### Stage 7C is complete when:

1. ✅ **Dynamic loop runs continuously** without crashes
2. ✅ **Zeus fetched with LOCAL time** (not UTC conversion)
3. ✅ **Markets detected 1-2 days early** when they open
4. ✅ **Snapshots saved with timestamps** for all data
5. ✅ **Edges calculated with fresh data** (< 5 min staleness)
6. ✅ **Paper trades executed dynamically** throughout the day
7. ✅ **All tests passing** (unit + integration)
8. ✅ **No breaking changes** to existing modes
9. ✅ **Configurable interval** via .env
10. ✅ **Documentation complete** with usage examples

---

## 🔷 Migration Strategy

### Phase 1: Implement (Week 1)
- Create dynamic_trader module
- Add orchestrator mode
- Implement JIT fetchers
- Add snapshotter

### Phase 2: Test (Week 2)
- Run dynamic mode for 1 week
- Collect snapshots
- Validate data quality
- Monitor staleness

### Phase 3: Analyze (Week 3)
- Analyze forecast evolution
- Compare static vs dynamic performance
- Validate snapshot completeness

### Phase 4: Full Deployment (Week 4)
- Switch to dynamic as primary mode
- Deprecate static mode
- Use dynamic snapshots for backtesting

---

## 🔷 Future Enhancements (Post-7C)

### Stage 8: Full Replay Backtesting
- Use dynamic snapshots for accurate backtests
- Replay any historical evaluation cycle
- Test different strategies on same data

### Stage 9: Continuous Monitoring
- Reduce interval to 5 minutes
- Add edge threshold alerts
- Automated trade execution on edge detection

### Stage 10: Live Trading
- Replace PaperBroker with LiveBroker
- Real order placement
- Risk management integration

---

## 🔷 Key Differences from Current System

### Current (Static):
```python
# Run once per day
fetch_zeus()              # Morning
calculate_edges()         # Using morning forecast
execute_all_trades()      # All at once
done()                    # Finished for the day
```

### Stage 7C (Dynamic):
```python
# Run continuously
while True:
    fetch_zeus()          # Fresh, right now
    fetch_prices()        # Fresh, right now
    calculate_edges()     # Using fresh data
    execute_trades()      # Immediately
    save_snapshots()      # With timestamps
    sleep(15 minutes)     # Configurable
```

**Key difference**: Fresh data every cycle, trades placed dynamically as edges appear.

---

## 🔷 Risk Mitigation

### Risks:

1. **API Rate Limits** - More frequent Zeus/Polymarket calls
2. **Data Storage** - Multiple snapshots per day
3. **Execution Complexity** - Continuous loop vs one-shot
4. **Debugging** - Harder to reproduce issues

### Mitigations:

1. ✅ Configurable interval (avoid rate limits)
2. ✅ Snapshot cleanup (auto-delete old data)
3. ✅ Comprehensive logging (track every cycle)
4. ✅ Timestamped snapshots (exact replay)

---

## 🔷 Summary

**Stage 7C upgrades Hermes to a living, dynamic agent:**

- ✅ Aware of early Polymarket market opens (1-2 days before)
- ✅ Fetches Zeus + pricing continuously
- ✅ Trades dynamically using fresh probabilities
- ✅ Stores timestamped data for future full backtesting
- ✅ Uses **local timestamps** for Zeus per official guidance
- ✅ Fully configurable evaluation interval
- ✅ Modular and isolated (no breaking changes)

**Enables:**
- More accurate edge calculations
- Better trade timing
- Future full replay backtesting
- Forecast evolution analysis

**Ready to implement when you are!** 🚀

---

**Author**: Hermes Development Team  
**Date**: November 13, 2025  
**Status**: Specification Complete, Implementation Pending

