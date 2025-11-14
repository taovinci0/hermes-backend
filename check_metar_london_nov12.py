#!/usr/bin/env python3
"""Fetch and display hourly METAR temperatures for London (EGLC) on November 12, 2025."""

from datetime import date, datetime, timezone
from venues.metar import METARService

def main():
    """Fetch and display METAR data for London on Nov 12."""
    
    print("=" * 70)
    print("🌡️  METAR Data: London (EGLC) - November 12, 2025")
    print("=" * 70)
    print()
    
    service = METARService()
    station = "EGLC"
    target_date = date(2025, 11, 12)
    
    print(f"Fetching observations for {station} on {target_date}...")
    print()
    print("⚠️  Note: METAR API may have limited historical data.")
    print("   If only recent observations are returned, the API may not")
    print("   have full historical data for this date.")
    print()
    
    try:
        observations = service.get_observations(
            station_code=station,
            event_date=target_date,
            hours=24,
            save_snapshot=False
        )
        
        if not observations:
            print("❌ No observations found for this date.")
            print("   The METAR API may not have historical data for November 12, 2025.")
            print("   Historical data is typically available for the last 15 days.")
            return
        
        print(f"✅ Retrieved {len(observations)} observations")
        print()
        
        # Check if observations are actually from the target date
        target_obs = [obs for obs in observations if obs.time.date() == target_date]
        other_obs = [obs for obs in observations if obs.time.date() != target_date]
        
        if target_obs:
            print(f"📅 Observations from {target_date}: {len(target_obs)}")
        if other_obs:
            print(f"⚠️  Observations from other dates: {len(other_obs)}")
            print(f"   (These may be the only data available)")
        print()
        
        print("-" * 70)
        print("📊 All Available Observations (Sorted by Time)")
        print("-" * 70)
        print()
        print(f"{'Date':<12} {'Time (UTC)':<12} {'Temp (°C)':<12} {'Temp (°F)':<12} {'Raw METAR':<35}")
        print("-" * 70)
        
        # Sort by time
        sorted_obs = sorted(observations, key=lambda x: x.time)
        
        for obs in sorted_obs:
            date_str = obs.time.date().isoformat()
            time_str = obs.time.strftime("%H:%M")
            temp_c = f"{obs.temp_C:.1f}°C"
            temp_f = f"{obs.temp_F:.1f}°F"
            raw_preview = obs.raw[:33] + "..." if obs.raw and len(obs.raw) > 33 else (obs.raw or "N/A")
            
            print(f"{date_str:<12} {time_str:<12} {temp_c:<12} {temp_f:<12} {raw_preview:<35}")
        
        print("-" * 70)
        print()
        
        # Calculate statistics for target date only
        if target_obs:
            temps_f = [obs.temp_F for obs in target_obs if obs.temp_F is not None]
            if temps_f:
                print(f"📈 Statistics for {target_date}:")
                print(f"   Total Observations: {len(target_obs)}")
                print(f"   Daily High: {max(temps_f):.1f}°F")
                print(f"   Daily Low:  {min(temps_f):.1f}°F")
                print(f"   Average:    {sum(temps_f)/len(temps_f):.1f}°F")
                print()
        
        # Show all observations stats
        all_temps_f = [obs.temp_F for obs in observations if obs.temp_F is not None]
        if all_temps_f:
            print(f"📊 Statistics for All Observations:")
            print(f"   Total Observations: {len(observations)}")
            print(f"   Date Range: {sorted_obs[0].time.date()} to {sorted_obs[-1].time.date()}")
            print(f"   High: {max(all_temps_f):.1f}°F")
            print(f"   Low:  {min(all_temps_f):.1f}°F")
            print(f"   Average: {sum(all_temps_f)/len(all_temps_f):.1f}°F")
            print()
        
        # Verify with get_daily_high method
        daily_high = service.get_daily_high(station, target_date)
        daily_low = service.get_daily_low(station, target_date)
        
        if daily_high or daily_low:
            print("🔍 Verification (using get_daily_high/low methods):")
            if daily_high:
                print(f"   Daily High: {daily_high:.1f}°F")
            if daily_low:
                print(f"   Daily Low:  {daily_low:.1f}°F")
            print()
        
        print("=" * 70)
        print("✅ Data retrieval complete!")
        print("=" * 70)
        print()
        
        if not target_obs:
            print("⚠️  WARNING: No observations found for November 12, 2025.")
            print("   The METAR API may not have historical data for this date.")
            print("   Historical data is typically available for the last 15 days.")
            print()
            print("   You can verify this by checking:")
            print("   • AviationWeather.gov website")
            print("   • The raw API response (see debug_metar_api.py)")
            print()
        else:
            print("You can now manually verify these temperatures against:")
            print("  • AviationWeather.gov website")
            print("  • Other weather sources")
            print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"   Type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
