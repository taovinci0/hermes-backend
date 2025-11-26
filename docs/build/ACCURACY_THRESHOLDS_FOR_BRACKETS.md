# Accuracy Thresholds for Temperature Brackets

**Date**: November 18, 2025  
**Purpose**: Define what "accurate" means when comparing METAR vs Zeus in the context of Polymarket brackets

---

## 🎯 The Key Question

**What is "accurate" for trading purposes?**

For trading, accuracy isn't just about raw temperature error - it's about whether Zeus predicted the **CORRECT BRACKET**.

---

## 📊 Bracket Structure

### **Bracket Width**
- **Standard brackets**: 1°F wide (e.g., 42-43°F, 44-45°F, 59-60°F)
- **Bounds**: Lower inclusive, upper exclusive
  - `[42-43)` means: `42.0 ≤ temp < 43.0`
  - `[44-45)` means: `44.0 ≤ temp < 45.0`

### **Polymarket Rounding**
- Polymarket rounds temperatures to determine bracket
- Example: `41.6°F` → rounds to `42°F` → bracket `[42-43)°F`
- Example: `44.3°F` → rounds to `44°F` → bracket `[44-45)°F`
- Example: `44.7°F` → rounds to `45°F` → bracket `[45-46)°F`

**Key Insight**: Rounding means temperatures near bracket boundaries can be tricky!

---

## ✅ What "Accurate" Means for Trading

### **Bracket Accuracy (What Matters for Trading)**

**Zeus is "accurate" if it predicted the CORRECT BRACKET**, regardless of raw temperature error.

**Examples**:

1. **Same Bracket = Accurate** ✅
   - Zeus predicts: `44.5°F` → bracket `[44-45)°F`
   - Actual: `44.8°F` → bracket `[44-45)°F`
   - Raw error: `0.3°F`
   - **Result**: ✅ Accurate (same bracket)

2. **Different Bracket = Inaccurate** ❌
   - Zeus predicts: `44.9°F` → bracket `[44-45)°F`
   - Actual: `45.1°F` → bracket `[45-46)°F`
   - Raw error: `0.2°F` (small!)
   - **Result**: ❌ Inaccurate (different bracket)

3. **Near Boundary = Borderline** ⚠️
   - Zeus predicts: `44.4°F` → bracket `[44-45)°F`
   - Actual: `45.0°F` → bracket `[45-46)°F`
   - Raw error: `0.6°F`
   - **Result**: ⚠️ Borderline (near boundary, different bracket)

---

## 🎯 Recommended Accuracy Thresholds

### **Option 1: Bracket-Based Accuracy (Recommended)**

**Most relevant for trading** - focuses on whether Zeus got the bracket right.

**Thresholds**:
- ✅ **Accurate**: Same bracket (regardless of raw error)
- ⚠️ **Acceptable**: Adjacent bracket (1 bracket off)
- ❌ **Inaccurate**: 2+ brackets off

**Color Coding**:
- ✅ **Green**: Same bracket
- ⚠️ **Yellow**: Adjacent bracket (1 bracket off)
- ❌ **Red**: 2+ brackets off

**Example**:
- Predicted: `44.5°F` → `[44-45)°F`
- Actual: `44.8°F` → `[44-45)°F`
- **Result**: ✅ Green (same bracket)

---

### **Option 2: Temperature Error with Bracket Context**

**Shows both raw error AND bracket accuracy**.

**Thresholds** (based on 1°F bracket width):
- ✅ **Accurate**: Error ≤ 0.5°F AND same bracket
- ⚠️ **Acceptable**: Error 0.5-1.0°F OR adjacent bracket
- ❌ **Inaccurate**: Error > 1.0°F OR 2+ brackets off

**Color Coding**:
- ✅ **Green**: Error ≤ 0.5°F AND same bracket
- ⚠️ **Yellow**: Error 0.5-1.0°F OR adjacent bracket
- ❌ **Red**: Error > 1.0°F OR 2+ brackets off

**Example**:
- Predicted: `44.5°F` → `[44-45)°F`
- Actual: `45.2°F` → `[45-46)°F`
- Error: `0.7°F`
- **Result**: ⚠️ Yellow (adjacent bracket, error < 1°F)

---

### **Option 3: Hybrid (Recommended for Display)**

**Show both metrics**:
1. **Bracket Accuracy** (primary): Same/Adjacent/Different
2. **Raw Error** (secondary): Temperature difference

**Display**:
```
Error: +0.3°F ✅ (Same Bracket)
Error: +0.7°F ⚠️ (Adjacent Bracket)
Error: +1.5°F ❌ (2 Brackets Off)
```

---

## 📋 Implementation Recommendation

### **For Performance Page Accuracy Panel**

**Show Both**:
1. **Bracket Accuracy** (primary indicator)
   - ✅ Same bracket
   - ⚠️ Adjacent bracket
   - ❌ 2+ brackets off

2. **Raw Error** (secondary metric)
   - Display as `+0.3°F` or `-0.5°F`
   - For reference, not primary indicator

**Color Coding**:
- ✅ **Green**: Same bracket
- ⚠️ **Yellow**: Adjacent bracket
- ❌ **Red**: 2+ brackets off

**Example Display**:
```
Predicted High: 44.6°F → [44-45)°F
Actual High: 44.8°F → [44-45)°F
Error: +0.2°F ✅ (Same Bracket)
```

---

## 🔧 Calculation Logic

### **Step 1: Determine Brackets**

```python
def get_bracket(temp_F: float) -> tuple[int, int]:
    """Get bracket for a temperature.
    
    Polymarket rounds, so:
    - 41.6°F → 42°F → [42-43)°F
    - 44.3°F → 44°F → [44-45)°F
    - 44.7°F → 45°F → [45-46)°F
    """
    rounded = round(temp_F)  # Round to nearest integer
    lower = int(rounded)  # Lower bound
    upper = lower + 1    # Upper bound (exclusive)
    return (lower, upper)
```

### **Step 2: Compare Brackets**

```python
def compare_brackets(predicted_F: float, actual_F: float) -> dict:
    """Compare predicted vs actual bracket.
    
    Returns:
        {
            "predicted_bracket": (44, 45),
            "actual_bracket": (44, 45),
            "bracket_match": True,
            "bracket_distance": 0,  # 0 = same, 1 = adjacent, 2+ = far
            "raw_error": 0.2,
            "accuracy_category": "accurate"  # "accurate", "acceptable", "inaccurate"
        }
    """
    pred_bracket = get_bracket(predicted_F)
    actual_bracket = get_bracket(actual_F)
    
    # Calculate bracket distance
    pred_lower = pred_bracket[0]
    actual_lower = actual_bracket[0]
    bracket_distance = abs(pred_lower - actual_lower)
    
    # Determine category
    if bracket_distance == 0:
        category = "accurate"
    elif bracket_distance == 1:
        category = "acceptable"
    else:
        category = "inaccurate"
    
    return {
        "predicted_bracket": pred_bracket,
        "actual_bracket": actual_bracket,
        "bracket_match": bracket_distance == 0,
        "bracket_distance": bracket_distance,
        "raw_error": actual_F - predicted_F,
        "accuracy_category": category,
    }
```

---

## 📊 Updated Accuracy Panel Design

### **Right-Side Panel: Daily High Prediction Accuracy**

**Metrics**:

1. **Predicted High**
   - Value: `44.6°F`
   - Bracket: `[44-45)°F`

2. **Actual High**
   - Value: `44.8°F`
   - Bracket: `[44-45)°F`

3. **Error**
   - Raw: `+0.2°F`
   - **Bracket Accuracy**: ✅ Same Bracket
   - **Color**: Green

4. **Final Forecast Age**
   - `2.5 hours before event`

5. **Forecast Stability**
   - `±0.4°F`

6. **Final Updates**
   - Last 3-4 predicted highs

---

## ✅ Final Recommendation

**Use Bracket-Based Accuracy** as the primary indicator:

- ✅ **Green**: Same bracket (regardless of raw error)
- ⚠️ **Yellow**: Adjacent bracket (1 bracket off)
- ❌ **Red**: 2+ brackets off

**Show raw error as secondary metric** for reference.

**Why This Works**:
- ✅ Focuses on what matters for trading (bracket accuracy)
- ✅ Accounts for Polymarket rounding behavior
- ✅ Handles boundary cases correctly
- ✅ More meaningful than arbitrary temperature thresholds

---

**Last Updated**: November 18, 2025


