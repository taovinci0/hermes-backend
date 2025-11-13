#!/usr/bin/env python3
"""Stage 3 Demo - Probability Mapping

Demonstrates the complete Zeus → Probability pipeline.
"""

from datetime import datetime, timezone
from agents.prob_mapper import ProbabilityMapper
from core.types import ZeusForecast, ForecastPoint, MarketBracket

print("=" * 70)
print("📊 STAGE 3 DEMO: PROBABILITY MAPPING")
print("=" * 70)
print()

# Create sample Zeus forecast (hourly temps for a day)
print("1. Creating sample Zeus forecast...")
sample_temps_k = [
    287.15,  # 57.2°F - early morning (cold)
    286.95,  # 56.8°F
    286.75,  # 56.5°F
    287.05,  # 57.0°F
    287.45,  # 57.7°F
    288.15,  # 59.0°F
    289.15,  # 60.8°F - warming up
    290.65,  # 63.5°F
    292.15,  # 66.4°F
    293.65,  # 68.9°F
    294.82,  # 71.0°F - peak (afternoon)
    294.65,  # 70.7°F
    294.15,  # 69.8°F
    293.45,  # 68.5°F
    292.65,  # 67.1°F
    291.75,  # 65.5°F
    290.85,  # 63.8°F
    289.95,  # 62.2°F
    289.15,  # 60.8°F
    288.45,  # 59.5°F
    287.95,  # 58.6°F
    287.55,  # 57.9°F
    287.25,  # 57.4°F
    287.05,  # 57.0°F
]

timeseries = [
    ForecastPoint(
        time_utc=datetime(2025, 11, 5, hour, 0, 0, tzinfo=timezone.utc),
        temp_K=temp,
    )
    for hour, temp in enumerate(sample_temps_k)
]

forecast = ZeusForecast(timeseries=timeseries, station_code="EGLC")
print(f"   ✅ Created forecast with {len(forecast.timeseries)} hourly points")
print()

# Convert temps to Fahrenheit for display
from core import units
temps_f = [units.kelvin_to_fahrenheit(p.temp_K) for p in forecast.timeseries]
print(f"2. Temperature range: {min(temps_f):.1f}°F - {max(temps_f):.1f}°F")
print(f"   Daily high (μ): {max(temps_f):.1f}°F")
print()

# Create market brackets
print("3. Creating market brackets...")
brackets = []
for lower_f in range(55, 75):
    brackets.append(
        MarketBracket(
            name=f"{lower_f}-{lower_f+1}°F",
            lower_F=lower_f,
            upper_F=lower_f + 1,
        )
    )
print(f"   ✅ Created {len(brackets)} brackets from 55-75°F")
print()

# Map probabilities
print("4. Mapping probabilities with ProbabilityMapper...")
mapper = ProbabilityMapper(sigma_default=2.0)
bracket_probs = mapper.map_daily_high(forecast, brackets)
print(f"   ✅ Mapped probabilities for {len(bracket_probs)} brackets")
print()

# Display results
print("5. Probability Distribution:")
print("   " + "=" * 66)
print(f"   {'Bracket':12s} {'p_zeus':>10s} {'Percentage':>12s} {'Bar':40s}")
print("   " + "-" * 66)

sorted_probs = sorted(bracket_probs, key=lambda bp: bp.p_zeus, reverse=True)
for i, bp in enumerate(sorted_probs[:10], 1):
    bar_len = int(bp.p_zeus * 100)  # Scale to 100 chars
    bar = "█" * bar_len
    print(
        f"   [{bp.bracket.lower_F:2d}-{bp.bracket.upper_F:2d}°F)  "
        f"{bp.p_zeus:8.4f}  "
        f"{bp.p_zeus*100:10.2f}%  "
        f"{bar}"
    )

print("   " + "-" * 66)
total = sum(bp.p_zeus for bp in bracket_probs)
print(f"   {'TOTAL':12s} {total:8.6f}  {total*100:10.4f}%")
print("   " + "=" * 66)
print()

# Statistics
print("6. Statistics:")
peak_bracket = sorted_probs[0]
sigma_used = bracket_probs[0].sigma_z

print(f"   Peak bracket: [{peak_bracket.bracket.lower_F}-{peak_bracket.bracket.upper_F}°F)")
print(f"   Peak probability: {peak_bracket.p_zeus:.4f} ({peak_bracket.p_zeus*100:.2f}%)")
print(f"   Forecast uncertainty: σ = {sigma_used:.2f}°F")
print(f"   Daily high (μ): {max(temps_f):.1f}°F")
print()

# Cumulative probabilities
print("7. Cumulative Probabilities:")
cumulative = 0.0
for bp in sorted(bracket_probs, key=lambda bp: bp.bracket.lower_F):
    cumulative += bp.p_zeus
    if bp.bracket.lower_F in [60, 65, 70]:
        print(f"   P(T < {bp.bracket.upper_F}°F) = {cumulative:.4f}")
print()

print("=" * 70)
print("✅ STAGE 3 DEMO COMPLETE")
print(f"   • Daily high: μ = {max(temps_f):.1f}°F")
print(f"   • Uncertainty: σ = {sigma_used:.2f}°F")
print(f"   • Peak bracket: [{peak_bracket.bracket.lower_F}-{peak_bracket.bracket.upper_F}°F) "
      f"with p = {peak_bracket.p_zeus:.4f}")
print(f"   • Probability sum: {total:.6f} ✅")
print("=" * 70)

