# Portfolio Metrics Endpoint Troubleshooting

**Date**: November 18, 2025  
**Issue**: `/api/performance/metrics` failing with `ERR_BLOCKED_BY_CLIENT`

---

## 🐛 The Problem

The `/api/performance/metrics` endpoint is failing with:
- `ERR_BLOCKED_BY_CLIENT` - Browser/client is blocking the request
- `No response from server` - Request never reaches server

**Endpoint**: `GET /api/performance/metrics?mode=paper`

---

## ✅ Endpoint Status

**Backend Status**: ✅ **WORKING**
- Endpoint exists: `/api/performance/metrics`
- Service exists: `PerformanceService`
- Route registered: `backend/api/routes/performance.py`
- CORS configured: ✅ Allows all origins

**Test Result**:
```bash
curl http://localhost:8000/api/performance/metrics?mode=paper
# Returns: {"total_trades":1440,"resolved_trades":0,...}
```

**The endpoint works!** The issue is browser-side.

---

## 🔍 What's Supposed to Be There

Between **P&L** and **Trade History**, there should be a **Performance Metrics** section showing:

- **Win Rate** (e.g., 63.12%)
- **ROI** (e.g., 17.61%)
- **Total Trades** (e.g., 1440)
- **Resolved/Pending Trades**
- **Average Edge %**
- **Largest Win/Loss**
- **Sharpe Ratio**

This data comes from `/api/performance/metrics`.

---

## 🛠️ Troubleshooting Steps

### **Step 1: Check Browser Extensions**

`ERR_BLOCKED_BY_CLIENT` is usually caused by:
- **Ad blockers** (uBlock Origin, AdBlock Plus)
- **Privacy extensions** (Privacy Badger, Ghostery)
- **Security software** (antivirus, firewall)

**Solution**:
1. Disable ad blockers for `localhost:8000`
2. Add `localhost:8000` to whitelist
3. Try incognito/private mode (extensions often disabled)

---

### **Step 2: Check Browser Console**

Open browser DevTools → Console tab and look for:
- Exact error message
- Which extension is blocking
- CORS errors

---

### **Step 3: Check Network Tab**

Open browser DevTools → Network tab:
1. Filter by "metrics"
2. Click on the failed request
3. Check:
   - **Status**: What's the HTTP status?
   - **Headers**: Are CORS headers present?
   - **Response**: Any error message?

---

### **Step 4: Test Directly**

Test the endpoint directly in browser:
```
http://localhost:8000/api/performance/metrics?mode=paper
```

Should return JSON. If it works in browser but not from frontend, it's a CORS or frontend issue.

---

### **Step 5: Check Frontend Code**

Check `PerformanceMetrics.tsx` (line 29 where error occurs):
- Is the URL correct?
- Is the base URL correct?
- Are headers set correctly?

---

## 🔧 Quick Fixes

### **Fix 1: Disable Ad Blocker for localhost**

1. Open ad blocker settings
2. Add `localhost:8000` to whitelist
3. Refresh page

### **Fix 2: Try Different Browser**

Test in a different browser to rule out extension issues.

### **Fix 3: Check CORS Headers**

Verify CORS headers are present:
```bash
curl -v -H "Origin: http://localhost:3000" \
  http://localhost:8000/api/performance/metrics?mode=paper
```

Should see:
```
access-control-allow-origin: *
access-control-allow-credentials: true
```

---

## 📋 Expected Response

The endpoint should return:
```json
{
  "total_trades": 1440,
  "resolved_trades": 0,
  "pending_trades": 1440,
  "wins": 0,
  "losses": 0,
  "win_rate": 0.0,
  "total_risk": 416484.75,
  "total_pnl": 0,
  "roi": 0.0,
  "avg_edge_pct": 17.64,
  "largest_win": 0.0,
  "largest_loss": 0.0,
  "sharpe_ratio": 0.0,
  "by_station": {
    "UNKNOWN": {
      "trades": 1440,
      "wins": 0,
      "losses": 0,
      "win_rate": 0.0,
      "pnl": 0,
      "roi": 0.0
    }
  }
}
```

---

## ✅ Verification

**To verify the endpoint is working**:
```bash
# Test endpoint
curl http://localhost:8000/api/performance/metrics?mode=paper

# Should return JSON with metrics
```

**To verify CORS**:
```bash
curl -v -H "Origin: http://localhost:3000" \
  http://localhost:8000/api/performance/metrics?mode=paper

# Should see CORS headers in response
```

---

## 🎯 Summary

**The endpoint works!** The issue is:
- ✅ Backend: Working
- ✅ Endpoint: Exists and responds
- ✅ CORS: Configured correctly
- ❌ Browser: Blocking the request (likely extension)

**Solution**: Disable ad blocker/privacy extension for `localhost:8000` or add it to whitelist.

---

**Last Updated**: November 18, 2025


