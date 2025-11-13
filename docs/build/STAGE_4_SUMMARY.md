# Stage 4 Summary - Polymarket Adapters

**Status**: ✅ COMPLETE  
**Date**: November 4, 2025  
**Tests**: 81/81 passing (100%)

---

## What Was Built

### 1. Market Discovery (`venues/polymarket/discovery.py`)

Discovers temperature markets from Polymarket Gamma API.

**Core Method**:
```python
from venues.polymarket.discovery import PolyDiscovery

discovery = PolyDiscovery()
brackets = discovery.list_temp_brackets(
    city="London",
    date_local=date(2025, 11, 5)
)

# Returns: List[MarketBracket] with market IDs
```

**Features**:
- Gamma `/markets` API search
- Multiple search term attempts
- Bracket name parsing (59-60°F, 59–60°F, etc.)
- Sorting by lower bound
- Snapshot persistence

### 2. Market Pricing (`venues/polymarket/pricing.py`)

Reads prices and liquidity from Polymarket CLOB.

**Key Methods**:

```python
from venues.polymarket.pricing import PolyPricing

pricing = PolyPricing()

# Get market probability
prob = pricing.midprob(bracket)  # Returns: 0-1

# Get liquidity
depth = pricing.depth(bracket)
# Returns: MarketDepth with bid/ask depth, spread

# Get price history (for backtesting)
history = pricing.get_price_history(bracket, interval="1h")
```

### 3. API Schemas (`venues/polymarket/schemas.py`)

Complete DTOs for both APIs:
- `GammaEvent`, `GammaMarket` - Gamma API
- `CLOBOrderBook`, `MarketDepth` - CLOB API
- `PriceHistory` - Historical data

### 4. Test Suite (21 tests)

- **Discovery**: 10 tests with API mocking
- **Pricing**: 11 tests with API mocking

All tests passing (100%).

---

## Test Results

```
Stage 1: 35 tests  ✅
Stage 2: 11 tests  ✅
Stage 3: 14 tests  ✅
Stage 4: 21 tests  ✅ NEW
───────────────────────
TOTAL:   81 tests  ✅  (100%)
```

---

## Usage Example: Complete Pipeline

```python
from datetime import date, datetime, timezone
from agents.zeus_forecast import ZeusForecastAgent
from agents.prob_mapper import ProbabilityMapper
from venues.polymarket.discovery import PolyDiscovery
from venues.polymarket.pricing import PolyPricing
from core.registry import get_registry

# 1. Get station
station = get_registry().get("EGLC")

# 2. Fetch Zeus forecast (Stage 2)
zeus = ZeusForecastAgent()
forecast = zeus.fetch(
    lat=station.lat,
    lon=station.lon,
    start_utc=datetime.now(timezone.utc),
    hours=24,
    station_code=station.station_code
)

# 3. Discover Polymarket brackets (Stage 4)
discovery = PolyDiscovery()
brackets = discovery.list_temp_brackets("London", date.today())

# 4. Map Zeus probabilities (Stage 3)
mapper = ProbabilityMapper()
bracket_probs = mapper.map_daily_high(forecast, brackets)

# 5. Get market probabilities (Stage 4)
pricing = PolyPricing()
for bp in bracket_probs:
    bp.p_mkt = pricing.midprob(bp.bracket)
    
    # Compare Zeus vs Market
    edge = bp.p_zeus - bp.p_mkt
    print(f"[{bp.bracket.lower_F}-{bp.bracket.upper_F}°F): "
          f"p_zeus={bp.p_zeus:.4f}, p_mkt={bp.p_mkt:.4f}, "
          f"edge={edge:+.4f}")
```

---

## Bracket Name Parsing

Supports multiple formats:
- `59-60°F` (hyphen)
- `59–60°F` (en dash)
- `59 - 60°F` (spaced)
- `59 to 60°F` (word format)
- `59 - 60 degrees`

**Validation**:
- Lower < Upper
- Range: 0-150°F
- Integer bounds only

---

## Liquidity Depth Calculation

From order book:
```python
depth = pricing.depth(bracket)

# Bid depth = Σ(price × size) for all bids
depth.bid_depth_usd  # Total USD available to buy

# Ask depth = Σ(price × size) for all asks
depth.ask_depth_usd  # Total USD available to sell

# Spread
depth.spread_bps  # (best_ask - best_bid) / mid × 10000

# Midprice
depth.mid_price  # (best_bid + best_ask) / 2
```

**Example**:
```
Bids: [0.60@100, 0.59@200]
Asks: [0.62@150, 0.63@250]

Bid depth: $178.00
Ask depth: $250.50
Midprice: 0.61
Spread: 327.87 bps
```

---

## Snapshot Storage

**Markets** (`data/snapshots/polymarket/markets/`):
- Discovery API responses
- Named: `{city}_{YYYY-MM-DD}.json`

**Midpoint** (`data/snapshots/polymarket/midpoint/`):
- Midprice API responses
- Named: `{market_id}.json`

**Books** (`data/snapshots/polymarket/book/`):
- Order book API responses
- Named: `{market_id}.json`

---

## Integration for Stage 5

Stage 5 will use Stage 4 outputs to compute edge and size positions:

```python
# Input: BracketProb with p_zeus and p_mkt filled
for bp in bracket_probs:
    # Stage 4 provides p_mkt
    assert bp.p_mkt is not None
    
    # Stage 5 will compute edge
    edge = (bp.p_zeus - bp.p_mkt) - fees - slippage
    
    if edge >= EDGE_MIN:
        # Get liquidity
        depth = pricing.depth(bp.bracket)
        
        # Size position with Kelly
        f_kelly = compute_kelly_fraction(bp.p_zeus, bp.p_mkt)
        size = min(
            f_kelly * bankroll,
            PER_MARKET_CAP,
            depth.bid_depth_usd
        )
```

---

## Files Summary

**Implementation** (3 files):
- ✅ `venues/polymarket/schemas.py` (98 lines)
- ✅ `venues/polymarket/discovery.py` (263 lines)
- ✅ `venues/polymarket/pricing.py` (295 lines)

**Tests** (2 files):
- ✅ `tests/test_polymarket_discovery.py` (10 tests)
- ✅ `tests/test_polymarket_pricing.py` (11 tests)

**Total**: ~656 lines of production code + tests

---

## Next Steps

**Stage 5**: Edge & Kelly Sizing
- Compute edge from p_zeus vs p_mkt
- Kelly fraction calculation
- Apply caps (EDGE_MIN, PER_MARKET_CAP, bankroll)
- Liquidity filtering

**Ready for production edge calculation!** 🎯

---

**Last Updated**: November 4, 2025  
**Version**: 1.0.0  
**Stage**: 4 (Complete)

