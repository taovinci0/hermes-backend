#!/usr/bin/env python3
"""Monitor dynamic paper trading progress.

Shows:
- How many cycles have run
- How many snapshots created
- How many paper trades placed
- Latest cycle activity
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent

print("\n" + "="*70)
print("📊 DYNAMIC PAPER TRADING MONITOR")
print("="*70)

# Check if running
pid_file = PROJECT_ROOT / "logs" / "dynamic_paper.pid"
if pid_file.exists():
    pid = pid_file.read_text().strip()
    import subprocess
    try:
        subprocess.run(["ps", "-p", pid], check=True, capture_output=True)
        print(f"\n✅ Dynamic mode RUNNING (PID: {pid})")
    except subprocess.CalledProcessError:
        print(f"\n⚠️  Dynamic mode NOT running (PID {pid} not found)")
else:
    print(f"\n⚠️  No PID file found")

# Count snapshots
snapshots_dir = PROJECT_ROOT / "data" / "snapshots" / "dynamic"

if not snapshots_dir.exists():
    print("\n❌ No dynamic snapshots directory found")
    exit()

# Count by type
zeus_snapshots = list(snapshots_dir.glob("zeus/*/*/*.json"))
poly_snapshots = list(snapshots_dir.glob("polymarket/*/*/*.json"))
decision_snapshots = list(snapshots_dir.glob("decisions/*/*/*.json"))

print(f"\n📁 SNAPSHOTS COLLECTED:")
print(f"   Zeus:        {len(zeus_snapshots)}")
print(f"   Polymarket:  {len(poly_snapshots)}")
print(f"   Decisions:   {len(decision_snapshots)}")

# Estimate cycles
cycles = len(zeus_snapshots) // 2  # 2 stations or 2 days
print(f"\n🔄 Estimated cycles run: ~{cycles}")

# Count trades
total_trades = 0
trades_by_day = defaultdict(int)

for decision_file in decision_snapshots:
    with open(decision_file) as f:
        data = json.load(f)
        trade_count = data.get("trade_count", 0)
        total_trades += trade_count
        
        event_day = data.get("event_day", "unknown")
        trades_by_day[event_day] += trade_count

print(f"\n💰 PAPER TRADES PLACED:")
print(f"   Total: {total_trades}")
if trades_by_day:
    for day, count in sorted(trades_by_day.items()):
        print(f"   {day}: {count} trades")

# Latest activity
if decision_snapshots:
    latest = max(decision_snapshots, key=lambda p: p.stat().st_mtime)
    
    with open(latest) as f:
        data = json.load(f)
    
    print(f"\n📈 LATEST ACTIVITY:")
    print(f"   Time: {data['decision_time_utc']}")
    print(f"   Station: {data['station_code']} ({data['city']})")
    print(f"   Event: {data['event_day']}")
    print(f"   Model: {data['model_mode']}")
    print(f"   Trades: {data['trade_count']}")
    
    if data.get('decisions'):
        print(f"\n   Latest trades:")
        for d in data['decisions'][:3]:
            print(f"      {d['bracket']}: edge={d['edge_pct']:.2f}% size=${d['size_usd']:.2f}")

# Check paper trades CSV
trades_dir = PROJECT_ROOT / "data" / "trades"
if trades_dir.exists():
    csv_files = list(trades_dir.glob("*/paper_trades.csv"))
    if csv_files:
        print(f"\n📝 PAPER TRADE LOGS:")
        for csv_file in sorted(csv_files)[-3:]:
            date = csv_file.parent.name
            lines = len(csv_file.read_text().strip().split('\n')) - 1  # Exclude header
            print(f"   {date}: {lines} trades")

# Latest snapshots
print(f"\n📸 LATEST SNAPSHOTS:")
if zeus_snapshots:
    latest_zeus = max(zeus_snapshots, key=lambda p: p.stat().st_mtime)
    print(f"   Zeus: {latest_zeus.name}")

if poly_snapshots:
    latest_poly = max(poly_snapshots, key=lambda p: p.stat().st_mtime)
    print(f"   Polymarket: {latest_poly.name}")

# Time range
if zeus_snapshots:
    timestamps = [p.stem for p in zeus_snapshots]
    if timestamps:
        first = min(timestamps)
        last = max(timestamps)
        print(f"\n⏰ TIME RANGE:")
        print(f"   First snapshot: {first}")
        print(f"   Last snapshot:  {last}")

print("\n" + "="*70)
print("To view live log:")
print("   tail -f logs/dynamic_paper_*.log")
print("")
print("To stop dynamic mode:")
print("   kill -INT $(cat logs/dynamic_paper.pid)")
print("="*70 + "\n")

