# Calibration Tool Output - File Placement Guide

**Date**: 2025-01-XX  
**Purpose**: Instructions for placing calibration tool output files

---

## 📁 Where to Place Calibration Files

### Directory Location

```
data/calibration/
```

### Required Files

Place the output files from your calibration tool in this directory:

1. **`data/calibration/station_calibration_EGLC.json`**
   - London City Airport calibration model

2. **`data/calibration/station_calibration_KLGA.json`**
   - LaGuardia Airport calibration model

---

## 📋 File Format Requirements

Each file should match the structure documented in your calibration tool output guide:

```json
{
  "station": "EGLC",
  "version": "2025.1",
  "bias_model": {
    "monthly_bias": [...],
    "hourly_bias": [...],
    "bias_matrix_raw": [...],
    "bias_matrix_smoothed": [...]  // This is what we use
  },
  "elevation": {
    "station_elev_m": 6.0,
    "mean_era5_elev_m": 68.87,
    "elevation_offset_c": 0.4087
  }
}
```

---

## ✅ Verification

After placing the files, verify they're loaded correctly:

```python
from core.station_calibration import StationCalibration

calibration = StationCalibration()
print(f"Loaded {len(calibration._models)} calibration models")
# Should print: "Loaded 2 calibration models"
```

---

## 🔄 When to Update

- **After running calibration tool**: Copy new output files to `data/calibration/`
- **When adding new stations**: Add corresponding `station_calibration_{STATION_ID}.json` file
- **After calibration model updates**: Replace existing files with new versions

---

## 📝 Notes

- Files are loaded automatically when `StationCalibration` is initialized
- Missing files are handled gracefully (calibration simply won't be applied)
- The system looks for files matching pattern: `station_calibration_*.json`

---

**Status**: Ready for calibration tool output files


