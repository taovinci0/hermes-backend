# Importing Snapshotter Data into Main Hermes Project

**Date**: November 17, 2025  
**Purpose**: Guide for importing data collected by hermes-snapshotter into the main Hermes project

---

## 🎯 Overview

The **hermes-snapshotter** project collects Zeus, Polymarket, and METAR snapshots continuously. This data can be imported into the main Hermes project to:
- ✅ Populate historical data browser
- ✅ Enable backtesting with real historical data
- ✅ View data in the frontend dashboard
- ✅ Trigger WebSocket updates (if files are new)

---

## 📁 Directory Structure Comparison

### Snapshotter Project Structure:
```
hermes-snapshotter/
└── data/
    └── snapshots/
        └── dynamic/
            ├── zeus/
            │   └── {station}/
            │       └── {date}/
            │           └── {timestamp}.json
            ├── polymarket/
            │   └── {city}/
            │       └── {date}/
            │           └── {timestamp}.json
            └── metar/
                └── {station}/
                    └── {date}/
                        └── {observation_time}.json
```

### Main Hermes Project Structure:
```
hermes-v1.0.0/
└── data/
    └── snapshots/
        └── dynamic/
            ├── zeus/
            │   └── {station}/
            │       └── {event_day}/
            │           └── {timestamp}.json
            ├── polymarket/
            │   └── {city}/
            │       └── {event_day}/
            │           └── {timestamp}.json
            ├── metar/
            │   └── {station}/
            │       └── {event_day}/
            │           └── {observation_time}.json
            └── decisions/  ← Only created by trading engine
                └── {station}/
                    └── {event_day}/
                        └── {timestamp}.json
```

**✅ Good News**: The directory structures are **identical**! You can copy directly.

---

## 📋 Import Methods

### Method 1: Direct Copy (Recommended)

**When to use**: Importing all snapshotter data at once

**Steps**:

1. **Stop the main Hermes trading engine** (if running):
   ```bash
   # Find and stop the process
   pkill -f "dynamic_paper"
   ```

2. **Backup existing data** (optional but recommended):
   ```bash
   cd /Users/harveyando/Local\ Sites/hermes-v1.0.0
   cp -r data/snapshots/dynamic data/snapshots/dynamic.backup.$(date +%Y%m%d)
   ```

3. **Copy snapshotter data**:
   ```bash
   # From snapshotter project to main project
   cp -r /path/to/hermes-snapshotter/data/snapshots/dynamic/* \
         /Users/harveyando/Local\ Sites/hermes-v1.0.0/data/snapshots/dynamic/
   ```

   Or if you want to merge (keep existing + add new):
   ```bash
   # Merge: Copy but don't overwrite existing files
   rsync -av --ignore-existing \
         /path/to/hermes-snapshotter/data/snapshots/dynamic/ \
         /Users/harveyando/Local\ Sites/hermes-v1.0.0/data/snapshots/dynamic/
   ```

4. **Verify import**:
   ```bash
   # Count files
   find data/snapshots/dynamic -name "*.json" | wc -l
   
   # Check structure
   ls -la data/snapshots/dynamic/zeus/EGLC/
   ```

5. **Restart backend API** (if needed):
   ```bash
   # The file watcher will detect existing files won't trigger events
   # But the API will serve the data immediately
   ```

---

### Method 2: Merge (Keep Both)

**When to use**: You have data in both projects and want to keep all of it

**Steps**:

```bash
# Use rsync to merge without overwriting
rsync -av \
      /path/to/hermes-snapshotter/data/snapshots/dynamic/ \
      /Users/harveyando/Local\ Sites/hermes-v1.0.0/data/snapshots/dynamic/

# This will:
# - Copy new files
# - Skip files that already exist (won't overwrite)
# - Preserve timestamps
```

---

### Method 3: Selective Import

**When to use**: Import only specific stations or date ranges

**Example - Import only EGLC data**:
```bash
# Copy only EGLC snapshots
cp -r /path/to/hermes-snapshotter/data/snapshots/dynamic/zeus/EGLC \
      /Users/harveyando/Local\ Sites/hermes-v1.0.0/data/snapshots/dynamic/zeus/

cp -r /path/to/hermes-snapshotter/data/snapshots/dynamic/metar/EGLC \
      /Users/harveyando/Local\ Sites/hermes-v1.0.0/data/snapshots/dynamic/metar/
```

**Example - Import only recent dates**:
```bash
# Copy only November 2025 data
cp -r /path/to/hermes-snapshotter/data/snapshots/dynamic/zeus/EGLC/2025-11-* \
      /Users/harveyando/Local\ Sites/hermes-v1.0.0/data/snapshots/dynamic/zeus/EGLC/
```

---

## ⚠️ Important Notes

### 1. File Naming Compatibility

**Snapshotter** saves files as:
- Zeus: `{timestamp}.json` (e.g., `2025-11-17_20-30-15.json`)
- Polymarket: `{timestamp}.json`
- METAR: `{observation_time}.json` (e.g., `2025-11-17_14-30-00.json`)

**Main Project** uses the same format, so files are **fully compatible**.

---

### 2. WebSocket Updates

**Important**: The file watcher only triggers WebSocket events for **new files created after it starts**.

**If you copy existing files**:
- ✅ Files are immediately available via API
- ✅ Frontend can fetch and display them
- ❌ WebSocket won't broadcast events (files already exist)

**To trigger WebSocket events**:
- The file watcher monitors for **new file creation**
- Copying existing files won't trigger events
- Only new snapshots created by the trading engine will trigger events

**This is fine!** The data is still available via REST API endpoints.

---

### 3. Decisions Snapshots

**Note**: The snapshotter **does NOT** collect decision snapshots (those are only created by the trading engine when it makes trading decisions).

**After importing**:
- ✅ Zeus snapshots → Available for historical browser
- ✅ Polymarket snapshots → Available for historical browser
- ✅ METAR snapshots → Available for historical browser
- ❌ Decision snapshots → Only exist if trading engine ran

**To get decision snapshots**: Run the main trading engine, which will create decision snapshots based on the imported Zeus/Polymarket data.

---

## 🔍 Verification Steps

### 1. Check File Counts

```bash
# Count Zeus snapshots
find data/snapshots/dynamic/zeus -name "*.json" | wc -l

# Count Polymarket snapshots
find data/snapshots/dynamic/polymarket -name "*.json" | wc -l

# Count METAR snapshots
find data/snapshots/dynamic/metar -name "*.json" | wc -l
```

### 2. Test API Endpoints

```bash
# Test Zeus snapshots
curl "http://localhost:8000/api/snapshots/zeus?station_code=EGLC&event_day=2025-11-17" | jq '.count'

# Test Polymarket snapshots
curl "http://localhost:8000/api/snapshots/polymarket?city=London&event_day=2025-11-17" | jq '.count'

# Test METAR observations
curl "http://localhost:8000/api/metar/observations?station_code=EGLC&event_day=2025-11-17" | jq 'length'
```

### 3. Check Frontend

- Open frontend dashboard
- Select a date that has imported data
- Verify graphs show data
- Verify historical browser works

---

## 🚀 Quick Import Script

Create a helper script for easy importing:

```bash
#!/bin/bash
# import_snapshotter_data.sh

SNAPSHOTTER_DIR="/path/to/hermes-snapshotter"
HERMES_DIR="/Users/harveyando/Local Sites/hermes-v1.0.0"

echo "Importing snapshotter data..."

# Backup existing data
echo "Creating backup..."
cp -r "$HERMES_DIR/data/snapshots/dynamic" \
      "$HERMES_DIR/data/snapshots/dynamic.backup.$(date +%Y%m%d_%H%M%S)"

# Copy snapshotter data (merge, don't overwrite)
echo "Copying snapshots..."
rsync -av --ignore-existing \
      "$SNAPSHOTTER_DIR/data/snapshots/dynamic/" \
      "$HERMES_DIR/data/snapshots/dynamic/"

# Count files
echo ""
echo "Import complete!"
echo "Zeus snapshots: $(find "$HERMES_DIR/data/snapshots/dynamic/zeus" -name "*.json" | wc -l | tr -d ' ')"
echo "Polymarket snapshots: $(find "$HERMES_DIR/data/snapshots/dynamic/polymarket" -name "*.json" | wc -l | tr -d ' ')"
echo "METAR snapshots: $(find "$HERMES_DIR/data/snapshots/dynamic/metar" -name "*.json" | wc -l | tr -d ' ')"
```

**Usage**:
```bash
chmod +x import_snapshotter_data.sh
./import_snapshotter_data.sh
```

---

## 📊 Expected Results

### After Import:

**Frontend Dashboard**:
- ✅ Historical browser shows all imported dates
- ✅ Zeus forecast evolution graphs work
- ✅ Polymarket price graphs work
- ✅ METAR actual temperature graphs work
- ✅ Can select any date with imported data

**API Endpoints**:
- ✅ `/api/snapshots/zeus` returns imported snapshots
- ✅ `/api/snapshots/polymarket` returns imported snapshots
- ✅ `/api/metar/observations` returns imported observations
- ✅ `/api/edges/current` works (if decision snapshots exist)

**Backtesting**:
- ✅ Can backtest using imported Zeus/Polymarket data
- ✅ Historical data available for any imported date range

---

## ⚡ WebSocket Behavior

### What Happens:

1. **Existing Files** (copied from snapshotter):
   - ✅ Available via REST API immediately
   - ✅ Frontend can fetch and display
   - ❌ Won't trigger WebSocket events (files already exist)

2. **New Files** (created after import):
   - ✅ File watcher detects them
   - ✅ WebSocket broadcasts events
   - ✅ Frontend receives real-time updates

### To Get Real-Time Updates:

**Option 1**: Keep snapshotter running (it will create new files that trigger WebSocket events)

**Option 2**: Run main trading engine (it creates decision snapshots + new Zeus/Polymarket snapshots)

**Option 3**: Both! Snapshotter collects data, trading engine creates decisions

---

## ✅ Summary

**To import snapshotter data**:

1. **Copy files** from snapshotter to main project:
   ```bash
   cp -r /path/to/hermes-snapshotter/data/snapshots/dynamic/* \
         /Users/harveyando/Local\ Sites/hermes-v1.0.0/data/snapshots/dynamic/
   ```

2. **Verify import**:
   - Check file counts
   - Test API endpoints
   - Check frontend

3. **Result**:
   - ✅ All imported data available via API
   - ✅ Frontend can display historical data
   - ✅ Backtesting can use imported data
   - ⚠️ WebSocket only triggers for NEW files (created after import)

**The data structure is identical, so it's a simple copy operation!**

---

**Last Updated**: November 17, 2025

