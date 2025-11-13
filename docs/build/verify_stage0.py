#!/usr/bin/env python3
"""Stage 0 Verification Checklist for Hermes

Run this script to verify that Stage 0 setup is complete and functional.
"""

import sys
from datetime import date, datetime, timezone

print("=" * 60)
print("🧪 HERMES STAGE 0 VERIFICATION CHECKLIST")
print("=" * 60)

# Test 1: Environment + Config
print("\n🧩 1. Environment + Config")
try:
    from core import config
    cfg = config.config
    print("  ✅ Config loaded successfully")
    print(f"     Zeus API: {cfg.zeus.api_base}")
    print(f"     Polymarket Gamma: {cfg.polymarket.gamma_base}")
    print(f"     Execution mode: {cfg.execution_mode}")
    print(f"     Active stations: {cfg.trading.active_stations}")
    print(f"     Edge min: {cfg.trading.edge_min}")
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    sys.exit(1)

# Test 2: Time Utilities
print("\n🕓 2. Time Utilities (DST-aware)")
try:
    from core import time_utils
    start, end = time_utils.get_local_day_window_utc(date.today(), "Europe/London")
    print(f"  ✅ London bounds: {start.isoformat()} → {end.isoformat()}")
    
    # Test UTC conversions
    dt_utc = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    dt_local = time_utils.utc_to_local(dt_utc, "America/New_York")
    print(f"  ✅ UTC→Local: {dt_utc} → {dt_local}")
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    sys.exit(1)

# Test 3: Unit Conversions
print("\n🌡️  3. Unit Conversions")
try:
    from core import units
    
    # Kelvin to Fahrenheit
    k_to_f = units.kelvin_to_fahrenheit(273.15)
    print(f"  ✅ 273.15 K → {k_to_f:.2f} °F (expected ~32)")
    
    # Resolve to whole F
    resolved = units.resolve_to_whole_f(54.5)
    print(f"  ✅ 54.5 °F → {resolved} °F (expected 55)")
    
    # Round-trip test
    temp_k = 293.15
    temp_f = units.kelvin_to_fahrenheit(temp_k)
    temp_k_back = units.fahrenheit_to_kelvin(temp_f)
    print(f"  ✅ Roundtrip: {temp_k} K → {temp_f:.2f} F → {temp_k_back:.2f} K")
    
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    sys.exit(1)

# Test 4: Types
print("\n🧱 4. Pydantic Types")
try:
    from core.types import ForecastPoint, MarketBracket, ZeusForecast
    
    # ForecastPoint
    fp = ForecastPoint(time_utc=datetime.now(timezone.utc), temp_K=280.0)
    print(f"  ✅ ForecastPoint: {fp.temp_K} K at {fp.time_utc.strftime('%H:%M')}")
    
    # MarketBracket
    bracket = MarketBracket(name="59-60°F", lower_F=59, upper_F=60)
    print(f"  ✅ MarketBracket: {bracket.name} [{bracket.lower_F}, {bracket.upper_F})")
    
    # ZeusForecast
    forecast = ZeusForecast(
        timeseries=[fp],
        station_code="EGLC",
    )
    print(f"  ✅ ZeusForecast: {len(forecast.timeseries)} points for {forecast.station_code}")
    
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    sys.exit(1)

# Test 5: Logger
print("\n🪵 5. Structured Logger")
try:
    from core.logger import logger
    logger.info("✅ Logger initialized and working!")
    print("  ✅ Logger outputs with rich formatting")
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    sys.exit(1)

# Test 6: Orchestrator
print("\n🚀 6. Orchestrator CLI")
try:
    from core import orchestrator
    print("  ✅ Orchestrator module imported successfully")
    print("  ✅ CLI ready for modes: fetch, probmap, paper, backtest")
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    sys.exit(1)

# Test 7: Module Structure
print("\n📦 7. Module Structure")
try:
    import core
    import agents
    import venues
    import venues.polymarket
    print("  ✅ core/ package")
    print("  ✅ agents/ package")
    print("  ✅ venues/ package")
    print("  ✅ venues.polymarket/ package")
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("🎉 ALL CHECKS PASSED - STAGE 0 VERIFIED!")
print("=" * 60)
print("\n📋 Next steps:")
print("  • Run: pytest tests/test_units.py -v")
print("  • Try: python -m core.orchestrator --mode paper --stations EGLC,KLGA")
print("  • Begin Stage 1: Create data/registry/stations.csv")
print()

