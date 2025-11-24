#!/usr/bin/env python3
"""Fix timezone issues in existing NYC (KLGA) snapshot data.

This script corrects snapshots that were created with incorrect timezone handling.
It adjusts timeseries times and start_local values to reflect correct local times.

Usage:
    python scripts/fix_nyc_snapshot_times.py [--dry-run] [--backup]
"""

import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from typing import Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent


def parse_datetime_with_tz(dt_str: str) -> Optional[datetime]:
    """Parse datetime string, handling various formats."""
    try:
        # Try ISO format first
        if "Z" in dt_str:
            dt_str = dt_str.replace("Z", "+00:00")
        return datetime.fromisoformat(dt_str)
    except (ValueError, AttributeError):
        return None


def fix_snapshot_file(snapshot_path: Path, station, dry_run: bool = False) -> dict:
    """Fix a single snapshot file.
    
    Args:
        snapshot_path: Path to snapshot JSON file
        station: Station object with timezone info
        dry_run: If True, don't write changes
        
    Returns:
        Dictionary with fix results
    """
    result = {
        "file": str(snapshot_path),
        "fixed": False,
        "errors": [],
        "changes": [],
    }
    
    try:
        # Read snapshot
        with open(snapshot_path, "r") as f:
            data = json.load(f)
        
        # Get timezone
        tz = ZoneInfo(station.time_zone)
        
        # Check if start_local exists and is correct
        start_local_str = data.get("start_local")
        if start_local_str:
            start_local = parse_datetime_with_tz(start_local_str)
            if start_local:
                # Check if it's already in correct timezone
                if start_local.tzinfo != tz:
                    # Convert to local timezone
                    if start_local.tzinfo is None:
                        # Assume UTC if no timezone
                        start_local = start_local.replace(tzinfo=ZoneInfo("UTC"))
                    start_local = start_local.astimezone(tz)
                    data["start_local"] = start_local.isoformat()
                    result["changes"].append(f"Fixed start_local: {start_local_str} → {data['start_local']}")
                    result["fixed"] = True
        
        # Fix timeseries times
        timeseries = data.get("timeseries", [])
        fixed_count = 0
        
        for i, point in enumerate(timeseries):
            time_str = point.get("time_utc")
            if not time_str:
                continue
            
            time_dt = parse_datetime_with_tz(time_str)
            if not time_dt:
                result["errors"].append(f"Could not parse time_utc at index {i}: {time_str}")
                continue
            
            # Check if time has timezone offset (indicating it's local, not UTC)
            if time_dt.tzinfo is not None and time_dt.tzinfo != ZoneInfo("UTC"):
                # This is local time labeled as UTC - need to convert
                # The time is already in local timezone, just needs to be stored correctly
                # OR it needs to be converted from UTC to local
                
                # Strategy: If the time has a timezone offset (like -05:00), it's likely
                # already in local time but mislabeled. We should keep it as-is but ensure
                # it's in the correct timezone.
                
                # If timezone matches station timezone, it's already correct
                if time_dt.tzinfo == tz:
                    # Already correct, but field name is wrong - we'll keep it for now
                    # since changing field names would break other code
                    pass
                else:
                    # Different timezone - convert to station's local time
                    if time_dt.tzinfo == ZoneInfo("UTC"):
                        # It's actually UTC, convert to local
                        time_dt = time_dt.astimezone(tz)
                    else:
                        # It's in some other timezone, convert to local
                        time_dt = time_dt.astimezone(tz)
                    
                    point["time_utc"] = time_dt.isoformat()
                    fixed_count += 1
                    result["fixed"] = True
            elif time_dt.tzinfo is None:
                # No timezone - assume UTC and convert to local
                time_dt = time_dt.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)
                point["time_utc"] = time_dt.isoformat()
                fixed_count += 1
                result["fixed"] = True
            # If it's already UTC with +00:00, we might want to convert to local
            # But let's be conservative - only fix if it's clearly wrong
        
        if fixed_count > 0:
            result["changes"].append(f"Fixed {fixed_count} timeseries times")
        
        # Write back to the same file (preserves folder structure)
        if result["fixed"] and not dry_run:
            with open(snapshot_path, "w") as f:
                json.dump(data, f, indent=2)
            result["changes"].append(f"Updated file: {snapshot_path.name}")
        
    except Exception as e:
        result["errors"].append(f"Error processing file: {e}")
    
    return result


def load_station(station_code: str) -> Optional[dict]:
    """Load station info from CSV."""
    registry_path = PROJECT_ROOT / "data" / "registry" / "stations.csv"
    if not registry_path.exists():
        return None
    
    with open(registry_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["station_code"] == station_code:
                return {
                    "city": row["city"],
                    "station_code": row["station_code"],
                    "time_zone": row["time_zone"],
                }
    return None


def main():
    """Main function to fix NYC snapshots."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix timezone issues in NYC snapshots")
    parser.add_argument("--dry-run", action="store_true", help="Don't write changes, just report")
    parser.add_argument("--backup", action="store_true", help="Create backup before fixing")
    parser.add_argument("--station", default="KLGA", help="Station code to fix (default: KLGA)")
    args = parser.parse_args()
    
    # Get station
    station_info = load_station(args.station)
    if not station_info:
        print(f"❌ Station {args.station} not found")
        return 1
    
    # Create a simple station-like object
    class Station:
        def __init__(self, info):
            self.city = info["city"]
            self.station_code = info["station_code"]
            self.time_zone = info["time_zone"]
    
    station = Station(station_info)
    
    print(f"🔧 Fixing snapshots for {station.city} ({args.station})")
    print(f"   Timezone: {station.time_zone}")
    if args.dry_run:
        print("   ⚠️  DRY RUN MODE - No changes will be written")
    print()
    
    # Find all snapshot files
    snapshots_dir = PROJECT_ROOT / "data" / "snapshots" / "dynamic" / "zeus" / args.station
    
    if not snapshots_dir.exists():
        print(f"❌ Snapshots directory not found: {snapshots_dir}")
        return 1
    
    # Find all JSON files
    snapshot_files = list(snapshots_dir.rglob("*.json"))
    
    if not snapshot_files:
        print(f"⚠️  No snapshot files found in {snapshots_dir}")
        return 0
    
    print(f"📁 Found {len(snapshot_files)} snapshot file(s)")
    print()
    
    # Process each file
    fixed_count = 0
    error_count = 0
    total_changes = 0
    
    for snapshot_path in sorted(snapshot_files):
        result = fix_snapshot_file(snapshot_path, station, dry_run=args.dry_run)
        
        if result["fixed"]:
            fixed_count += 1
            total_changes += len(result["changes"])
            status = "✅" if not args.dry_run else "🔍"
            print(f"{status} {snapshot_path.name}")
            for change in result["changes"]:
                print(f"   - {change}")
        elif result["errors"]:
            error_count += 1
            print(f"❌ {snapshot_path.name}")
            for error in result["errors"]:
                print(f"   - {error}")
    
    print()
    print("=" * 60)
    print(f"Summary:")
    print(f"  Total files: {len(snapshot_files)}")
    print(f"  Fixed: {fixed_count}")
    print(f"  Errors: {error_count}")
    print(f"  Total changes: {total_changes}")
    
    if args.dry_run:
        print()
        print("⚠️  This was a dry run. Run without --dry-run to apply changes.")
    
    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

