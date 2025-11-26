# Portfolio Page: Simple Structure (Money Only)

**Date**: November 18, 2025  
**Purpose**: Simple Portfolio page structure - just money/account status

---

## 🎯 Simple Portfolio Structure

Since Portfolio = "our money", it should be simple:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Portfolio                                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ Mode: [Paper ▼] [Live ▼]                                                    │
│                                                                              │
│ ┌──────────────────────────────────────────────────────────────────────┐  │
│ │ Section 1: Account Status                                            │  │
│ │                                                                      │  │
│ │ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐              │  │
│ │ │ Account  │ │ Total    │ │ Win Rate │ │ ROI      │              │  │
│ │ │ Balance  │ │ P&L      │ │          │ │          │              │  │
│ │ │          │ │          │ │          │ │          │              │  │
│ │ │ $10,240  │ │ +$8,240  │ │ 63.12%   │ │ 17.61%   │              │  │
│ │ └──────────┘ └──────────┘ └──────────┘ └──────────┘              │  │
│ │                                                                      │  │
│ │ Period: [All Time ▼] [Last 30 Days ▼] [Last 7 Days ▼]            │  │
│ └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│ ┌──────────────────────────────────────────────────────────────────────┐  │
│ │ Section 2: Trade History                                            │  │
│ │                                                                      │  │
│ │ [Filterable, searchable trade history table]                        │  │
│ │ [Click row → Navigate to Performance page for that day]            │  │
│ └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│ [Export Data]                                                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

**That's it! Just 2 sections:**
1. Account Status (P&L, balances, metrics)
2. Trade History

---

## 🔌 Required API Endpoints

### **Section 1: Account Status**

**Endpoints Used**:
- `GET /api/performance/pnl` - For Total P&L, ROI
- `GET /api/performance/metrics` - For Win Rate, Total Trades

**Status**: ✅ Both endpoints exist and work

---

### **Section 2: Trade History**

**Endpoint Used**:
- `GET /api/trades/history` - For trade history table

**Status**: ✅ Endpoint exists and works

---

## 🐛 Network Error Diagnosis

If you're getting a network error between P&L and Trade History, it's likely:

1. **Performance Metrics Endpoint** (`/api/performance/metrics`)
   - **Check**: `curl http://localhost:8000/api/performance/metrics`
   - **Status**: ✅ Should work (we just tested it)

2. **P&L Endpoint** (`/api/performance/pnl`)
   - **Check**: `curl http://localhost:8000/api/performance/pnl`
   - **Status**: ✅ Should work

3. **Trade History Endpoint** (`/api/trades/history`)
   - **Check**: `curl http://localhost:8000/api/trades/history`
   - **Status**: ✅ Should work

---

## 🔍 What to Check

1. **Check Browser Console**: What exact endpoint is failing?
2. **Check Network Tab**: What's the error message?
3. **Check API Server**: Is it running? `curl http://localhost:8000/health`

---

## ✅ Expected Endpoints for Simple Portfolio

**Account Status Section**:
- `GET /api/performance/pnl?mode=paper` - P&L data
- `GET /api/performance/metrics?mode=paper` - Win rate, ROI, etc.

**Trade History Section**:
- `GET /api/trades/history?mode=paper&limit=100&offset=0` - Trade history

**That's it! No other endpoints needed for simple Portfolio page.**

---

**Last Updated**: November 18, 2025


