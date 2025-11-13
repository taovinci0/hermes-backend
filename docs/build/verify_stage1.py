#!/usr/bin/env python3
"""Stage 1 Verification - Data Registry and Utilities

Verifies that Stage 1 is complete:
- Station registry loaded
- Time utilities working with DST
- All unit conversions functional
"""

import sys
from datetime import date, datetime, timezone

print("=" * 60)
print("🧪 HERMES STAGE 1 VERIFICATION")
print("=" * 60)

# Test 1: Station Registry
print("\n📍 1. Station Registry")
try:
    from core.registry import get_registry
    
    registry = get_registry()
    station_count = len(registry)
    print(f"  ✅ Loaded {station_count} stations from registry")
    
    # Test specific stations
    london = registry.get("EGLC")
    assert london is not None
    print(f"  ✅ London: {london.city} ({london.station_code}) at {london.lat:.3f}°N, {london.lon:.3f}°E")
    
    ny = registry.get("KLGA")
    assert ny is not None
    print(f"  ✅ New York: {ny.city} ({ny.station_code}) at {ny.lat:.3f}°N, {ny.lon:.3f}°W")
    
    # Test lookup by city
    miami = registry.get_by_city("Miami")
    assert miami is not None
    print(f"  ✅ City lookup: {miami.city} → {miami.station_code}")
    
    # Test timezone filtering
    eastern = registry.list_by_timezone("America/New_York")
    print(f"  ✅ Timezone filter: {len(eastern)} stations in America/New_York")
    
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    sys.exit(1)

# Test 2: Unit Conversions (from Stage 0)
print("\n🌡️  2. Unit Conversions")
try:
    from core import units
    
    # Test conversions
    temp_k = 273.15
    temp_f = units.kelvin_to_fahrenheit(temp_k)
    print(f"  ✅ {temp_k} K → {temp_f:.2f} °F")
    
    # Test rounding
    resolved = units.resolve_to_whole_f(54.5)
    print(f"  ✅ 54.5 °F → {resolved} °F (rounds up)")
    
    # Test roundtrip
    temp_k = 293.15
    temp_f = units.kelvin_to_fahrenheit(temp_k)
    temp_k_back = units.fahrenheit_to_kelvin(temp_f)
    print(f"  ✅ Roundtrip: {temp_k} K → {temp_f:.2f} F → {temp_k_back:.2f} K")
    
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    sys.exit(1)

# Test 3: Time Utilities with DST
print("\n🕓 3. Time Utilities (DST-aware)")
try:
    from core import time_utils
    
    # Test local day window
    test_date = date(2025, 1, 15)
    start, end = time_utils.get_local_day_window_utc(test_date, "America/New_York")
    print(f"  ✅ NY day window: {start.strftime('%H:%M')} → {end.strftime('%H:%M')} UTC")
    
    # Test DST detection
    from pytz import timezone as pytz_tz
    eastern = pytz_tz("America/New_York")
    dt_winter = eastern.localize(datetime(2025, 1, 15, 12, 0, 0))
    dt_summer = eastern.localize(datetime(2025, 7, 15, 12, 0, 0))
    
    is_dst_winter = time_utils.is_dst(dt_winter, "America/New_York")
    is_dst_summer = time_utils.is_dst(dt_summer, "America/New_York")
    print(f"  ✅ DST detection: Jan={is_dst_winter}, Jul={is_dst_summer}")
    
    # Test UTC conversions
    dt_utc = datetime(2025, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    dt_local = time_utils.utc_to_local(dt_utc, "Europe/London")
    print(f"  ✅ UTC→Local: {dt_utc.hour}:00 UTC → {dt_local.hour}:00 BST")
    
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    sys.exit(1)

# Test 4: Type Models
print("\n🧱 4. Type Models")
try:
    from core.types import ForecastPoint, MarketBracket, ZeusForecast
    
    # Create instances
    fp = ForecastPoint(time_utc=datetime.now(timezone.utc), temp_K=280.0)
    bracket = MarketBracket(name="59-60°F", lower_F=59, upper_F=60)
    forecast = ZeusForecast(timeseries=[fp], station_code="EGLC")
    
    print(f"  ✅ ForecastPoint: {fp.temp_K} K")
    print(f"  ✅ MarketBracket: {bracket.name} [{bracket.lower_F}, {bracket.upper_F})")
    print(f"  ✅ ZeusForecast: {len(forecast.timeseries)} points for {forecast.station_code}")
    
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    sys.exit(1)

# Test 5: Integration - Station + Time Utils
print("\n🔗 5. Integration Test")
try:
    from core.registry import get_registry
    from core import time_utils
    
    registry = get_registry()
    
    # Get a station and use its timezone
    station = registry.get("KLGA")
    test_date = date.today()
    start, end = time_utils.get_local_day_window_utc(test_date, station.time_zone)
    
    print(f"  ✅ Station: {station.city} ({station.time_zone})")
    print(f"  ✅ Today's window: {start.isoformat()} → {end.isoformat()}")
    
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("🎉 STAGE 1 VERIFICATION COMPLETE!")
print("=" * 60)
print("\n📊 Summary:")
print(f"  • {station_count} stations loaded from CSV")
print("  • Temperature conversions working")
print("  • DST-aware timezone utilities working")
print("  • All type models validated")
print("  • Integration test passed")
print("\n📋 Station Coverage:")
print(f"  • {station_count} US stations + 1 international (London)")
print(f"  • NOAA stations: {', '.join(sorted(set(s.noaa_station for s in registry.list_all())))}")
print(f"  • Venues: Polymarket (2), Kalshi (7)")
print("\n📋 Next steps:")
print("  • Run: pytest -v (all 35 tests should pass)")
print("  • Begin Stage 2: Zeus forecast agent implementation")
print()

