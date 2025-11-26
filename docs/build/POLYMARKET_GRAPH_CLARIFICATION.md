# Polymarket Graph Clarification

**Date**: November 18, 2025  
**Issue**: Clarifying what data we snapshot vs. what we display

---

## 🔍 What We're Actually Snapshotting

**Polymarket Snapshots contain**:
```json
{
  "fetch_time_utc": "2025-11-13T12:12:35.453684+00:00",
  "markets": [
    {
      "market_id": "676331",
      "bracket": "58-59°F",
      "mid_price": 0.0005,  // ← This is the PRICE
      "closed": false
    },
    {
      "market_id": "676333",
      "bracket": "60-61°F",
      "mid_price": 0.0695,  // ← This is the PRICE
      "closed": false
    },
    {
      "market_id": "676335",
      "bracket": "62-63°F",
      "mid_price": 0.85,    // ← This is the PRICE
      "closed": false
    }
  ]
}
```

**Key Point**: We're snapshotting `mid_price` (the actual price from Polymarket CLOB API).

---

## 💡 Understanding Polymarket Prices

**In Polymarket, the price IS the probability**:
- Price of "Yes" token = Market-implied probability
- `mid_price: 0.85` = 85% probability
- `mid_price: 0.0695` = 6.95% probability
- `mid_price: 0.0005` = 0.05% probability

**So**:
- ✅ We ARE snapshotting prices
- ✅ Prices ARE probabilities (just in decimal form)
- ✅ We should show BOTH: price AND percentage

---

## 📊 What Graph 2 Should Display

### **Option 1: Show Prices (Recommended)**

**Title**: "Polymarket Price History"  
**Y-Axis**: "Price" (0.0 to 1.0)  
**Data**: Plot `mid_price` values directly

**Why**:
- ✅ Shows actual prices we snapshot
- ✅ More precise (0.85 vs 85%)
- ✅ Matches what we're storing

**Display**:
- Tooltip shows: `Price: 0.85 (85%)`
- Or dual Y-axis: Left = Price (0-1), Right = Probability (0-100%)

---

### **Option 2: Show Probabilities**

**Title**: "Polymarket Implied Probabilities"  
**Y-Axis**: "Probability (%)" (0 to 100)  
**Data**: Plot `mid_price * 100` (convert to percentage)

**Why**:
- ✅ More intuitive for users
- ✅ Easier to read (85% vs 0.85)

**Display**:
- Tooltip shows: `Probability: 85% (Price: 0.85)`

---

### **Option 3: Show Both (Best UX)**

**Title**: "Polymarket Price History"  
**Y-Axis**: Dual axis
- Left: Price (0.0 to 1.0)
- Right: Probability (0% to 100%)

**Data**: Plot prices, show percentages in tooltip

**Why**:
- ✅ Shows both price and probability
- ✅ Most informative
- ✅ Tooltip can show: `Price: 0.85 | Probability: 85%`

---

## 🎯 Recommended: Show Prices with Percentage Tooltip

**Graph Title**: "Polymarket Price History"  
**Subtitle**: "Market prices (Yes token) for each temperature bracket. Price = implied probability."

**Y-Axis**: "Price" (0.0 to 1.0)

**Tooltip**:
```
Time: 12:00
44-45°F: 0.1382 (13.82%)
45-46°F: 0.2430 (24.30%)
46-47°F: 0.2278 (22.78%)
47-48°F: 0.2929 (29.29%)
48-49°F: 0.4186 (41.86%)
```

**Why This Works**:
- ✅ Shows actual prices we snapshot
- ✅ Tooltip shows percentage for readability
- ✅ Accurate representation of data
- ✅ Clear that price = probability

---

## ⚠️ X-Axis Issue

**Current**: Showing 24-hour axis (00:00 to 24:00)  
**Should Be**: Market open → close timeline

**Correct X-Axis**:
- Start: Market open (2 days before event at 4pm UTC)
- End: Market close (event day local midnight)
- Example: Nov 18 16:00 UTC → Nov 20 00:00 Local

**Not**: 00:00 to 24:00 (this is wrong for multi-day markets)

---

## 📋 Implementation Changes Needed

### **Backend** (No changes needed)
- ✅ Already returning `mid_price` in snapshots
- ✅ Data is correct

### **Frontend** (Changes needed)

1. **Graph Title**:
   - Change: "Polymarket Implied Probabilities"
   - To: "Polymarket Price History"

2. **Y-Axis**:
   - Change: "Probability (%)" (0-100)
   - To: "Price" (0.0-1.0)
   - Or: Dual axis (Price 0-1, Probability 0-100%)

3. **Data Mapping**:
   - Use `mid_price` directly (not `mid_price * 100`)
   - Show percentage in tooltip

4. **X-Axis**:
   - Change: 24-hour day (00:00 to 24:00)
   - To: Market timeline (market open → close)
   - Use `/api/performance/market-timeline` endpoint

5. **Tooltip**:
   - Show: `Price: 0.85 (85%)`
   - Or: `Price: 0.85 | Probability: 85%`

---

## ✅ Summary

**What We Snapshot**: `mid_price` (actual Polymarket price)  
**What Price Represents**: Market-implied probability (price = probability)  
**What to Display**: Prices (0.0-1.0) with percentage in tooltip  
**X-Axis**: Market open → close timeline (not 24-hour day)

**Key Insight**: In Polymarket, price IS probability, so showing prices is correct. Just make it clear in the UI that price = probability.

---

**Last Updated**: November 18, 2025


