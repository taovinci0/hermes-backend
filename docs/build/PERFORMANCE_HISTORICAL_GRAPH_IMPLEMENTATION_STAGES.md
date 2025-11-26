# Performance Historical Graph: Implementation Stages

**Date**: November 18, 2025  
**Purpose**: Staged implementation plan for the historical 24-hour temperature forecast graph  
**Key Insight**: Most backend endpoints already exist! Minimal backend work needed.

---

## 🎯 What We Need

**Graph Data**:
- Zeus Latest curve (intraday forecast)
- Zeus Median curve
- METAR Actual temperatures
- Accuracy panel metrics

---

## ✅ Existing Backend Endpoints

### **Already Available**:

1. **Zeus Snapshots**: `GET /api/snapshots/zeus?station_code={STATION}&event_day={DATE}`
   - ✅ Returns all Zeus snapshots for a day
   - ✅ Includes timeseries (24 hourly points)
   - ✅ Includes daily_high

2. **METAR Observations**: `GET /api/metar/observations?station_code={STATION}&event_day={DATE}`
   - ✅ Returns all METAR observations for a day
   - ✅ Includes temperature and observation time

3. **Daily High**: `GET /api/metar/daily-high?station_code={STATION}&event_day={DATE}`
   - ✅ Returns maximum temperature from METAR

4. **Zeus vs METAR Comparison**: `GET /api/compare/zeus-vs-metar?station_code={STATION}&event_day={DATE}`
   - ✅ Compares Zeus predicted high vs METAR actual high
   - ✅ Calculates error

**All the data we need is already available!**

---

## 🔧 What We Need to Add (Minimal)

### **Option 1: Use Existing Endpoints (Recommended)**

**Frontend can call existing endpoints and combine data**:
- Call `/api/snapshots/zeus` for Zeus data
- Call `/api/metar/observations` for METAR data
- Call `/api/compare/zeus-vs-metar` for accuracy metrics

**Pros**: No backend changes needed  
**Cons**: Multiple API calls from frontend

**Time**: 0 hours (backend) | 4-6 hours (frontend)

---

### **Option 2: Create Combined Endpoint (Optional)**

**Single endpoint that returns everything**:
- `GET /api/performance/historical-forecast/{station_code}/{date}`

**Returns**:
- Zeus Latest curve
- Zeus Median curve
- METAR Actual temperatures
- Accuracy panel metrics (all in one response)

**Pros**: Single API call, cleaner frontend  
**Cons**: Requires backend work

**Time**: 3-4 hours (backend) | 3-4 hours (frontend)

---

## 📋 Recommended Approach: Use Existing Endpoints

**Why**: All data is already available via existing endpoints. No backend changes needed!

**Frontend Implementation**:
1. Call `/api/snapshots/zeus` → Get Zeus Latest + calculate Median
2. Call `/api/metar/observations` → Get METAR actual temperatures
3. Call `/api/compare/zeus-vs-metar` → Get accuracy metrics
4. Combine data in frontend
5. Reuse Live Dashboard graph component
6. Add METAR line
7. Add accuracy panel

---

## 🎨 Implementation Stages

### **Stage 1: Frontend - Reuse Live Dashboard Graph (Week 1)**

#### **1.1 Extract/Reuse Graph Component**
**File**: `frontend/src/components/TemperatureForecastGraph.tsx` (or similar)

**Tasks**:
- Extract Live Dashboard graph component (if not already separate)
- Make it reusable (accept props for data)
- Ensure it supports historical mode (no auto-updates)

**Time**: 2-3 hours

---

#### **1.2 Add METAR Line to Graph**
**File**: Same graph component

**Tasks**:
- Add METAR actual temperature line
- Use different color/style (orange with dots)
- Plot at actual observation times

**Time**: 2-3 hours

---

#### **1.3 Create Accuracy Panel Component**
**File**: `frontend/src/components/DailyHighAccuracyPanel.tsx`

**Tasks**:
- Create right-side panel component
- Display all 6 metrics:
  1. Predicted High
  2. Actual High
  3. Error (color-coded)
  4. Final Forecast Age
  5. Forecast Stability
  6. Final Updates
- Style to match Live Dashboard

**Time**: 3-4 hours

---

#### **1.4 Integrate into Performance Page**
**File**: `frontend/src/pages/Performance/PerformancePage.tsx`

**Tasks**:
- Add graph to Performance page
- Fetch data from existing endpoints
- Combine Zeus + METAR + accuracy data
- Replace existing Graph 1 with new component

**Time**: 2-3 hours

---

### **Stage 2: Data Processing & Calculations (Week 1)**

#### **2.1 Calculate Zeus Median**
**Location**: Frontend (or backend service if needed)

**Tasks**:
- Calculate median of all hourly temperatures across all snapshots
- Handle edge cases (single snapshot, no data)

**Time**: 1-2 hours

---

#### **2.2 Calculate Accuracy Metrics**
**Location**: Frontend (using `/api/compare/zeus-vs-metar` + additional calculations)

**Tasks**:
- Use `/api/compare/zeus-vs-metar` for basic comparison
- Calculate Final Forecast Age (time between last snapshot and event start)
- Calculate Forecast Stability (std dev of last 3-4 predicted highs)
- Extract Final Updates (last 3-4 predicted highs)

**Time**: 2-3 hours

---

### **Stage 3: Testing & Polish (Week 1-2)**

#### **3.1 Testing**
**Tasks**:
- Test with real historical data
- Test edge cases (no METAR, single snapshot, etc.)
- Verify accuracy calculations
- Verify graph matches Live Dashboard look/feel

**Time**: 2-3 hours

---

#### **3.2 Polish**
**Tasks**:
- Ensure styling matches Live Dashboard
- Verify color coding for accuracy
- Test responsive design
- Add loading states

**Time**: 1-2 hours

---

## 📋 Implementation Checklist

### **Backend** (Minimal - Optional)
- [ ] **Option 1**: Use existing endpoints (no backend work) ✅
- [ ] **Option 2**: Create combined endpoint (optional, 3-4 hours)

### **Frontend** (Required)
- [ ] Extract/reuse Live Dashboard graph component
- [ ] Add METAR actual line to graph
- [ ] Create Daily High Accuracy Panel component
- [ ] Integrate into Performance page
- [ ] Calculate Zeus Median (frontend)
- [ ] Calculate accuracy metrics (frontend)
- [ ] Test with real data
- [ ] Polish styling

---

## ⏱️ Timeline

### **Option 1: Use Existing Endpoints** (Recommended)
- **Backend**: 0 hours ✅
- **Frontend**: 10-15 hours
- **Total**: 1.5-2 days

### **Option 2: Create Combined Endpoint**
- **Backend**: 3-4 hours
- **Frontend**: 7-10 hours
- **Total**: 1.5-2 days

---

## 🎯 Recommended: Option 1 (Use Existing Endpoints)

**Why**:
- ✅ No backend changes needed
- ✅ Faster to implement
- ✅ All data already available
- ✅ Frontend can combine data easily

**Implementation**:
1. Frontend calls 3 existing endpoints
2. Combines data in frontend
3. Reuses Live Dashboard graph component
4. Adds METAR line and accuracy panel

**Total Time**: 1.5-2 days (frontend only)

---

## 📊 Data Flow

```
Frontend Performance Page
    ↓
1. GET /api/snapshots/zeus?station_code=EGLC&event_day=2025-11-16
   → Returns: All Zeus snapshots with timeseries
   → Frontend: Extract latest snapshot, calculate median
    ↓
2. GET /api/metar/observations?station_code=EGLC&event_day=2025-11-16
   → Returns: All METAR observations
   → Frontend: Extract temperatures and times
    ↓
3. GET /api/compare/zeus-vs-metar?station_code=EGLC&event_day=2025-11-16
   → Returns: Predicted high, actual high, error
   → Frontend: Use for accuracy panel
    ↓
4. Frontend combines data
   → Creates graph data structure
   → Calculates additional metrics (forecast age, stability, final updates)
    ↓
5. Render graph component
   → Reuse Live Dashboard component
   → Add METAR line
   → Add accuracy panel
```

---

## ✅ Summary

**Backend Work**: **NONE** (use existing endpoints) or **Optional** (create combined endpoint)

**Frontend Work**: **10-15 hours**
- Reuse Live Dashboard graph component
- Add METAR line
- Create accuracy panel
- Integrate into Performance page

**Total Time**: **1.5-2 days**

---

**Last Updated**: November 18, 2025


