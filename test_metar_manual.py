#!/usr/bin/env python3
"""Manual test script for METAR service.

Run this to verify METAR API integration is working with real data.
"""

from datetime import date, timedelta
from venues.metar import METARService

def test_metar_service():
    """Test METAR service with real API calls."""
    
    print("=" * 70)
    print("🧪 METAR Service Manual Test")
    print("=" * 70)
    print()
    
    # Initialize service
    service = METARService()
    print(f"✅ METAR Service initialized")
    print(f"   API Base: {service.api_base}")
    print(f"   User-Agent: {service.user_agent}")
    print()
    
    # Test stations (from your registry)
    test_stations = ["EGLC", "KLGA"]  # London, New York
    
    for station in test_stations:
        print("-" * 70)
        print(f"📍 Testing Station: {station}")
        print("-" * 70)
        
        try:
            # Test 1: Get latest observations (today)
            print(f"\n1️⃣  Fetching observations for {station} (today)...")
            observations = service.get_observations(
                station_code=station,
                event_date=date.today(),
                hours=24,
                save_snapshot=False
            )
            
            if observations:
                print(f"   ✅ Retrieved {len(observations)} observations")
                
                # Show first and last observations
                print(f"\n   First observation:")
                first = observations[0]
                print(f"      Time: {first.time}")
                print(f"      Temp: {first.temp_C:.1f}°C / {first.temp_F:.1f}°F")
                if first.raw:
                    print(f"      Raw: {first.raw[:60]}...")
                
                if len(observations) > 1:
                    print(f"\n   Last observation:")
                    last = observations[-1]
                    print(f"      Time: {last.time}")
                    print(f"      Temp: {last.temp_C:.1f}°C / {last.temp_F:.1f}°F")
                
                # Test 2: Get daily high
                print(f"\n2️⃣  Calculating daily high for {station}...")
                daily_high = service.get_daily_high(station_code=station)
                
                if daily_high:
                    print(f"   ✅ Daily High: {daily_high:.1f}°F")
                else:
                    print(f"   ⚠️  No daily high available")
                
                # Test 3: Get daily low
                print(f"\n3️⃣  Calculating daily low for {station}...")
                daily_low = service.get_daily_low(station_code=station)
                
                if daily_low:
                    print(f"   ✅ Daily Low: {daily_low:.1f}°F")
                    print(f"   📊 Temperature Range: {daily_low:.1f}°F - {daily_high:.1f}°F")
                else:
                    print(f"   ⚠️  No daily low available")
                
                # Show temperature distribution
                temps = [obs.temp_F for obs in observations if obs.temp_F is not None]
                if temps:
                    print(f"\n   📈 Temperature Stats:")
                    print(f"      Min: {min(temps):.1f}°F")
                    print(f"      Max: {max(temps):.1f}°F")
                    print(f"      Avg: {sum(temps)/len(temps):.1f}°F")
                    print(f"      Observations: {len(temps)}")
                
            else:
                print(f"   ⚠️  No observations returned")
                print(f"   (This might be normal if the station has no recent data)")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
            print(f"   Type: {type(e).__name__}")
        
        print()
    
    # Test 4: Historical data (yesterday)
    print("-" * 70)
    print("📅 Testing Historical Data (Yesterday)")
    print("-" * 70)
    
    yesterday = date.today() - timedelta(days=1)
    test_station = "EGLC"
    
    try:
        print(f"\n4️⃣  Fetching observations for {test_station} on {yesterday}...")
        observations = service.get_observations(
            station_code=test_station,
            event_date=yesterday,
            hours=24,
            save_snapshot=False
        )
        
        if observations:
            print(f"   ✅ Retrieved {len(observations)} observations")
            daily_high = service.get_daily_high(test_station, yesterday)
            if daily_high:
                print(f"   ✅ Daily High ({yesterday}): {daily_high:.1f}°F")
        else:
            print(f"   ⚠️  No observations for {yesterday}")
            print(f"   (Historical data may not be available)")
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print(f"   Type: {type(e).__name__}")
    
    print()
    print("=" * 70)
    print("✅ Manual test complete!")
    print("=" * 70)
    print()
    print("If you see observations and temperatures above, METAR integration is working! 🎉")
    print()

if __name__ == "__main__":
    test_metar_service()

