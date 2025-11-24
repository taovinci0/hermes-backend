# API 404 Error Reduction

## Problem

The activity logs were showing an unusually high number of 404 API errors, making it difficult to see important information. The logs were cluttered with entries like:

```
❌ API Error: Resource not found (404) (+3 more)
❌ API Error: Resource not found (404) (+4 more)
```

## Root Cause

The system uses a **slug discovery pattern** to find Polymarket events. For each city/date combination, it tries multiple event slug patterns (4-7 different variations) to find the correct event:

1. `highest-temperature-in-{city}-on-{month}-{day}`
2. `temperature-in-{city}-on-{month}-{day}`
3. `high-temperature-in-{city}-on-{month}-{day}`
4. `{city}-temperature-on-{month}-{day}`
5. (Plus NYC-specific variations)

**Most of these patterns will return 404** because only one pattern will match the actual event slug on Polymarket. This is **expected behavior**, but the 404s were being logged as ERROR level, creating noise in the logs.

## Solution

### 1. Gamma API (Event Discovery)

**File**: `venues/polymarket/discovery.py`

**Change**: 404 errors are now logged as **DEBUG** instead of **ERROR** since they're expected when trying multiple slug patterns.

```python
except requests.exceptions.HTTPError as e:
    # 404 errors are expected when trying multiple event slug patterns
    # Only log them as DEBUG, not ERROR
    if hasattr(e.response, 'status_code') and e.response.status_code == 404:
        logger.debug(f"Gamma API 404 (expected): {endpoint}")
    else:
        logger.error(f"Gamma API HTTP error: {e}")
    raise PolymarketAPIError(f"Gamma API HTTP error: {e}") from e
```

### 2. CLOB API (Pricing)

**File**: `venues/polymarket/pricing.py`

**Change**: 404 errors are now logged as **WARNING** instead of **ERROR** since they can occur for closed markets or invalid token IDs (which is somewhat expected).

```python
except requests.exceptions.HTTPError as e:
    # 404 errors can occur for closed markets or invalid token IDs
    # Log as WARNING instead of ERROR to reduce noise
    if hasattr(e.response, 'status_code') and e.response.status_code == 404:
        logger.warning(f"CLOB API 404: {endpoint} (market may be closed or invalid)")
    else:
        logger.error(f"CLOB API HTTP error: {e}")
    raise PolymarketPricingError(f"CLOB API HTTP error: {e}") from e
```

## Impact

### Before
- **ERROR level**: 404s logged as errors, cluttering activity logs
- **User experience**: Difficult to see important information
- **Log noise**: Many false-positive errors

### After
- **DEBUG level**: 404s from event discovery logged as debug (not shown in activity logs)
- **WARNING level**: 404s from pricing logged as warnings (less prominent)
- **User experience**: Cleaner logs, easier to see actual issues
- **Log noise**: Significantly reduced

## Expected Behavior

### Event Discovery
- System tries 4-7 slug patterns per city/date
- Most will 404 (expected)
- Only one will succeed (the correct event)
- 404s are now logged as DEBUG (not shown in activity logs)

### Pricing
- Some markets may be closed or have invalid token IDs
- 404s are now logged as WARNING (less prominent than ERROR)
- System continues gracefully (prices set to None)

## Log Levels

### DEBUG (Not shown in activity logs)
- 404 errors from event discovery (expected)
- Successful API calls
- Detailed debugging information

### WARNING (Shown but less prominent)
- 404 errors from pricing (closed/invalid markets)
- Failed price fetches (non-critical)

### ERROR (Shown prominently)
- Non-404 HTTP errors (500, 401, etc.)
- Timeouts
- Network errors
- JSON decode errors

## Verification

After these changes, you should see:
- ✅ **Fewer ERROR entries** in activity logs
- ✅ **Cleaner logs** focused on important information
- ✅ **404s still handled correctly** (system continues to work)
- ✅ **Actual errors still visible** (non-404 errors still logged as ERROR)

## Related Files

- `venues/polymarket/discovery.py` - Event discovery with slug patterns
- `venues/polymarket/pricing.py` - Market pricing
- `agents/dynamic_trader/fetchers.py` - Uses discovery to find events
- `backend/api/services/log_service.py` - Log formatting and filtering

## Notes

- The system still handles 404s correctly (returns None, continues gracefully)
- Only the **log level** changed, not the behavior
- 404s are still available in DEBUG logs if needed for troubleshooting
- The human-readable log formatter will now show fewer error entries

