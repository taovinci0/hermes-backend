#!/usr/bin/env python3
"""Monitor Hermes paper trading activity.

Quick summary of today's trades and recent activity.
"""

import sys
from datetime import date, timedelta
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    print("❌ pandas not installed. Install with: pip install pandas")
    sys.exit(1)


def summarize_trades(csv_path: Path) -> None:
    """Summarize trades from CSV file."""
    if not csv_path.exists():
        print(f"📭 No trades file found: {csv_path}")
        return
    
    df = pd.read_csv(csv_path)
    
    if len(df) == 0:
        print(f"📭 No trades in {csv_path.parent.name}")
        return
    
    print(f"\n📊 Trading Summary for {csv_path.parent.name}")
    print("=" * 60)
    print(f"Total trades: {len(df)}")
    print(f"Total size: ${df['size_usd'].sum():.2f}")
    print(f"Average edge: {df['edge_pct'].mean():.2f}%")
    print(f"Max edge: {df['edge_pct'].max():.2f}%")
    print(f"Min edge: {df['edge_pct'].min():.2f}%")
    
    if 'station_code' in df.columns:
        print(f"\nStations traded: {', '.join(df['station_code'].unique())}")
        print("\nTrades by station:")
        station_summary = df.groupby('station_code').agg({
            'size_usd': ['count', 'sum'],
            'edge_pct': 'mean'
        }).round(2)
        print(station_summary)
    
    print(f"\nTop 5 trades by edge:")
    top_trades = df.nlargest(5, 'edge_pct')[
        ['bracket_name', 'edge_pct', 'size_usd', 'reason']
    ]
    for idx, row in top_trades.iterrows():
        print(f"  {row['bracket_name']:10s} {row['edge_pct']:6.2f}% "
              f"${row['size_usd']:7.2f}  ({row['reason']})")
    
    print()


def main():
    """Monitor trades for today and recent days."""
    print("╔" + "═" * 62 + "╗")
    print("║" + " " * 62 + "║")
    print("║" + "  🔍 HERMES TRADE MONITOR".center(62) + "║")
    print("║" + " " * 62 + "║")
    print("╚" + "═" * 62 + "╝")
    
    trades_dir = Path("data/trades")
    
    if not trades_dir.exists():
        print("\n❌ No trades directory found. Run paper trading first:")
        print("   python -m core.orchestrator --mode paper --stations EGLC,KLGA")
        return
    
    # Check today
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    today_csv = trades_dir / today_str / "paper_trades.csv"
    
    print(f"\n📅 Today ({today_str}):")
    summarize_trades(today_csv)
    
    # Check yesterday
    yesterday = today - timedelta(days=1)
    yesterday_str = yesterday.strftime("%Y-%m-%d")
    yesterday_csv = trades_dir / yesterday_str / "paper_trades.csv"
    
    if yesterday_csv.exists():
        print(f"\n📅 Yesterday ({yesterday_str}):")
        summarize_trades(yesterday_csv)
    
    # Check all recent trades
    print("\n" + "=" * 64)
    print("📁 All Trade Files:")
    print("=" * 64)
    
    trade_files = sorted(trades_dir.glob("*/paper_trades.csv"), reverse=True)
    
    if trade_files:
        total_trades = 0
        total_size = 0.0
        
        for csv_file in trade_files[:7]:  # Last 7 days
            try:
                df = pd.read_csv(csv_file)
                trade_count = len(df)
                total_trades += trade_count
                total_size += df['size_usd'].sum()
                
                print(f"{csv_file.parent.name}: {trade_count:3d} trades, "
                      f"${df['size_usd'].sum():8.2f}, "
                      f"avg edge {df['edge_pct'].mean():5.2f}%")
            except Exception as e:
                print(f"{csv_file.parent.name}: Error reading file - {e}")
        
        print("=" * 64)
        print(f"Last 7 days: {total_trades} trades, ${total_size:.2f} total size")
    else:
        print("No trade files found yet.")
    
    print()


if __name__ == "__main__":
    main()

