# Status API Usage - Frontend Implementation Guide

**Date**: November 17, 2025  
**Purpose**: Guide for frontend developers on how to use the `/api/status` endpoint

---

## 🔌 API Endpoint

```http
GET /api/status
```

**Response Structure:**

```json
{
  "timestamp": "2025-11-17T20:29:52.260046",
  "trading_engine": {
    "running": true,
    "pid_file_exists": true,
    "pid": 64926,
    "elapsed_time": "01-02:00:31"
  },
  "execution_mode": "PAPER",
  "cycle": {
    "interval_seconds": 900,
    "interval_minutes": 15.0,
    "last_cycle_time": "2025-11-17T20:15:30",
    "next_cycle_time": "2025-11-17T20:30:30",
    "seconds_until_next": 38
  },
  "data_collection": {
    "recent_snapshots_24h": 439,
    "snapshots_dir_exists": true,
    "trades_dir_exists": true
  }
}
```

---

## 📊 Frontend Usage

### 1. Execution Mode (PAPER/LIVE)

**Field**: `execution_mode`

**Values**: `"PAPER"` or `"LIVE"`

**Usage**:
```typescript
const { execution_mode } = await fetch('/api/status').then(r => r.json());

// Display mode badge
<Badge color={execution_mode === 'PAPER' ? 'blue' : 'red'}>
  {execution_mode}
</Badge>
```

**⚠️ DO NOT hardcode "PAPER"** - Always read from the API!

---

### 2. Countdown Timer

**Field**: `cycle.seconds_until_next`

**Description**: Number of seconds until the next trading cycle

**Usage**:
```typescript
const { cycle } = await fetch('/api/status').then(r => r.json());

// Format as MM:SS
const minutes = Math.floor(cycle.seconds_until_next / 60);
const seconds = cycle.seconds_until_next % 60;
const display = `${minutes}:${String(seconds).padStart(2, '0')}`;

// Display: "15:00", "14:59", "14:58", etc.
```

**⚠️ DO NOT hardcode a 5-second timer!** The timer should:
- Start from `cycle.seconds_until_next`
- Count down each second
- Reset when it reaches 0 (and fetch new status)

**Example Implementation**:
```typescript
function useCycleTimer() {
  const [secondsRemaining, setSecondsRemaining] = useState<number | null>(null);
  
  useEffect(() => {
    // Fetch initial status
    fetch('/api/status')
      .then(r => r.json())
      .then(data => {
        setSecondsRemaining(data.cycle.seconds_until_next);
      });
    
    // Update every second
    const interval = setInterval(() => {
      setSecondsRemaining(prev => {
        if (prev === null || prev <= 0) {
          // Timer expired - fetch new status
          fetch('/api/status')
            .then(r => r.json())
            .then(data => {
              setSecondsRemaining(data.cycle.seconds_until_next);
            });
          return null;
        }
        return prev - 1;
      });
    }, 1000);
    
    return () => clearInterval(interval);
  }, []);
  
  return secondsRemaining;
}
```

---

### 3. Next Cycle Time Display

**Field**: `cycle.next_cycle_time`

**Format**: ISO 8601 datetime string (e.g., `"2025-11-17T20:30:30"`)

**Usage**:
```typescript
const { cycle } = await fetch('/api/status').then(r => r.json());

if (cycle.next_cycle_time) {
  const nextCycle = new Date(cycle.next_cycle_time);
  const display = nextCycle.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  });
  
  // Display: "20:30" or "15:00"
  <span>Next: {display}</span>
}
```

---

### 4. Cycle Interval

**Fields**: 
- `cycle.interval_seconds` (e.g., `900`)
- `cycle.interval_minutes` (e.g., `15.0`)

**Usage**:
```typescript
const { cycle } = await fetch('/api/status').then(r => r.json());

// Display interval info
<span>Cycle interval: {cycle.interval_minutes} minutes</span>
```

---

### 5. Trading Engine Status

**Field**: `trading_engine.running`

**Usage**:
```typescript
const { trading_engine } = await fetch('/api/status').then(r => r.json());

// Display status indicator
{trading_engine.running ? (
  <Badge color="green">RUNNING</Badge>
) : (
  <Badge color="red">STOPPED</Badge>
)}
```

---

## 🔄 Polling Strategy

### Recommended Approach

1. **Initial Load**: Fetch status immediately
2. **Timer Updates**: Update countdown every second (client-side)
3. **Status Refresh**: Re-fetch status every 30-60 seconds (or when timer expires)

**Example**:
```typescript
function useSystemStatus() {
  const [status, setStatus] = useState(null);
  const [countdown, setCountdown] = useState(null);
  
  const fetchStatus = async () => {
    const data = await fetch('/api/status').then(r => r.json());
    setStatus(data);
    setCountdown(data.cycle.seconds_until_next);
  };
  
  useEffect(() => {
    // Initial fetch
    fetchStatus();
    
    // Refresh status every 30 seconds
    const statusInterval = setInterval(fetchStatus, 30000);
    
    // Update countdown every second
    const countdownInterval = setInterval(() => {
      setCountdown(prev => {
        if (prev === null || prev <= 0) {
          // Timer expired - refresh status
          fetchStatus();
          return null;
        }
        return prev - 1;
      });
    }, 1000);
    
    return () => {
      clearInterval(statusInterval);
      clearInterval(countdownInterval);
    };
  }, []);
  
  return { status, countdown };
}
```

---

## ❌ Common Mistakes to Avoid

### 1. Hardcoding Execution Mode
```typescript
// ❌ WRONG
const mode = "PAPER";

// ✅ CORRECT
const { execution_mode } = await fetch('/api/status').then(r => r.json());
```

### 2. Hardcoding Timer Interval
```typescript
// ❌ WRONG - Timer resets every 5 seconds
setInterval(() => {
  setCountdown(5);
}, 5000);

// ✅ CORRECT - Use seconds_until_next from API
const { cycle } = await fetch('/api/status').then(r => r.json());
setCountdown(cycle.seconds_until_next);
```

### 3. Not Refreshing Status
```typescript
// ❌ WRONG - Only fetch once
useEffect(() => {
  fetch('/api/status').then(r => r.json()).then(setStatus);
}, []);

// ✅ CORRECT - Refresh periodically
useEffect(() => {
  const interval = setInterval(() => {
    fetch('/api/status').then(r => r.json()).then(setStatus);
  }, 30000);
  return () => clearInterval(interval);
}, []);
```

---

## ✅ Verification Checklist

- [ ] Execution mode is read from API (not hardcoded)
- [ ] Countdown timer uses `cycle.seconds_until_next`
- [ ] Timer counts down correctly (not resetting every 5 seconds)
- [ ] Timer refreshes status when it reaches 0
- [ ] Next cycle time is displayed correctly
- [ ] Status is refreshed periodically (every 30-60 seconds)
- [ ] Trading engine status (RUNNING/STOPPED) is displayed

---

**Last Updated**: November 17, 2025

