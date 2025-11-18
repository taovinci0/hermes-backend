# WebSocket for Frontend - Complete Guide

**Date**: November 17, 2025  
**Purpose**: Explain what WebSocket does for the frontend and how to use it

---

## 🎯 What is WebSocket?

**WebSocket** is a persistent, bidirectional connection between the frontend and backend that allows **real-time updates** without polling.

### Without WebSocket (Polling):
```typescript
// Frontend has to keep asking: "Any new data?"
setInterval(() => {
  fetch('/api/edges/current').then(updateUI);
}, 5000);  // Check every 5 seconds
```

**Problems**:
- ❌ Wastes bandwidth (checking even when nothing changed)
- ❌ Delayed updates (up to 5 seconds old)
- ❌ Server load (constant requests)
- ❌ Battery drain on mobile

### With WebSocket:
```typescript
// Backend pushes updates when they happen
const ws = new WebSocket('ws://localhost:8000/ws/trading');
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  updateUI(update);  // Instant update!
};
```

**Benefits**:
- ✅ Instant updates (no delay)
- ✅ Efficient (only sends when data changes)
- ✅ Lower server load
- ✅ Better user experience

---

## 📡 What Events Does WebSocket Broadcast?

The WebSocket broadcasts **3 main event types** when the trading engine creates new snapshots:

### 1. `cycle_complete`
**When**: A trading cycle finishes (every 15 minutes)

**Data**:
```json
{
  "type": "cycle_complete",
  "timestamp": "2025-11-17T20:30:00",
  "data": {
    "cycle_number": 45,
    "station_code": "EGLC",
    "event_day": "2025-11-17",
    "trades_count": 2,
    "cycle_duration": 97.5
  }
}
```

**Frontend Use**:
- Update cycle counter
- Refresh edges table
- Update Zeus forecast graph
- Add entry to activity log

---

### 2. `trade_placed`
**When**: A trade is executed (during a cycle)

**Data**:
```json
{
  "type": "trade_placed",
  "timestamp": "2025-11-17T20:30:15",
  "data": {
    "station_code": "EGLC",
    "event_day": "2025-11-17",
    "bracket": "58-59°F",
    "size_usd": 300.00,
    "edge_pct": 26.25
  }
}
```

**Frontend Use**:
- Show notification/toast
- Update trades table
- Update total trades counter
- Add entry to activity log
- Update P&L summary

---

### 3. `edges_updated`
**When**: New decision snapshot is saved (edges recalculated)

**Data**:
```json
{
  "type": "edges_updated",
  "timestamp": "2025-11-17T20:30:20",
  "data": {
    "station_code": "EGLC",
    "event_day": "2025-11-17",
    "edges_count": 3,
    "max_edge_pct": 26.25
  }
}
```

**Frontend Use**:
- Refresh edges table
- Update edge summary cards
- Highlight new/changed edges

---

## 🔄 How It Works (Behind the Scenes)

### Step 1: File Watcher Monitors Snapshots

The backend has a **file watcher** that monitors the `data/snapshots/dynamic/` directory:

```
data/snapshots/dynamic/
├── decisions/EGLC/2025-11-17/2025-11-17_20-30-20.json  ← New file created!
├── zeus/EGLC/2025-11-17/2025-11-17_20-30-15.json
└── polymarket/London/2025-11-17/2025-11-17_20-30-10.json
```

### Step 2: File Watcher Detects New File

When the trading engine saves a new snapshot, the file watcher detects it:

```python
# File watcher detects: decisions/EGLC/2025-11-17/2025-11-17_20-30-20.json
# Reads the file
# Determines event type: "trade_placed" (because trade_count > 0)
# Extracts metadata: station, event_day, bracket, size, edge
```

### Step 3: WebSocket Broadcasts Event

The file watcher broadcasts the event to all connected WebSocket clients:

```python
await websocket_service.broadcast_trade_placed(
    station_code="EGLC",
    event_day="2025-11-17",
    bracket="58-59°F",
    size_usd=300.00,
    edge_pct=26.25
)
```

### Step 4: Frontend Receives Update

All connected frontend clients receive the message instantly:

```typescript
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  // message.type = "trade_placed"
  // message.data = { station_code, event_day, bracket, size_usd, edge_pct }
  
  // Update UI immediately!
  showTradeNotification(message.data);
  updateTradesTable(message.data);
  refreshEdges();
};
```

---

## 💻 Frontend Implementation

### Basic WebSocket Connection

```typescript
// src/hooks/useWebSocket.ts
import { useEffect, useState, useRef } from 'react';

const WS_URL = 'ws://localhost:8000/ws/trading';

export function useTradingWebSocket() {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Connect to WebSocket
    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setLastMessage(message);
      
      // Handle different event types
      switch (message.type) {
        case 'cycle_complete':
          handleCycleComplete(message.data);
          break;
        case 'trade_placed':
          handleTradePlaced(message.data);
          break;
        case 'edges_updated':
          handleEdgesUpdated(message.data);
          break;
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
      // Reconnect after 3 seconds
      setTimeout(() => {
        wsRef.current = new WebSocket(WS_URL);
      }, 3000);
    };

    wsRef.current = ws;

    // Cleanup on unmount
    return () => {
      ws.close();
    };
  }, []);

  return { isConnected, lastMessage };
}
```

### Using in Components

```typescript
// src/components/Dashboard/LiveDashboard.tsx
import { useTradingWebSocket } from '../../hooks/useWebSocket';

function LiveDashboard() {
  const { isConnected, lastMessage } = useTradingWebSocket();
  const [trades, setTrades] = useState([]);
  const [edges, setEdges] = useState([]);

  // Handle WebSocket messages
  useEffect(() => {
    if (!lastMessage) return;

    switch (lastMessage.type) {
      case 'trade_placed':
        // Add new trade to list
        setTrades(prev => [lastMessage.data, ...prev]);
        // Show notification
        showToast(`New trade: ${lastMessage.data.bracket} @ $${lastMessage.data.size_usd}`);
        break;

      case 'edges_updated':
        // Refresh edges table
        fetchEdges().then(setEdges);
        break;

      case 'cycle_complete':
        // Refresh all data
        refreshDashboard();
        break;
    }
  }, [lastMessage]);

  return (
    <div>
      <div>Status: {isConnected ? '🟢 Connected' : '🔴 Disconnected'}</div>
      {/* Dashboard content */}
    </div>
  );
}
```

---

## 🎨 UI Updates from WebSocket Events

### When `cycle_complete` Event Received:

**Update**:
- ✅ Cycle counter: "Cycle #45"
- ✅ Last update time: "Last updated: 20:30"
- ✅ Refresh edges table (fetch new data)
- ✅ Update Zeus forecast graph (fetch new snapshot)
- ✅ Add log entry: "✅ Cycle #45 complete"

---

### When `trade_placed` Event Received:

**Update**:
- ✅ Show toast notification: "💰 Trade placed: 58-59°F @ $300 (26.25% edge)"
- ✅ Add trade to trades table (at top)
- ✅ Update total trades counter: "Today: 23 trades"
- ✅ Update total size: "Total: $6,900"
- ✅ Add log entry: "📝 Placed trade: 58-59°F @ $300"
- ✅ Highlight new trade row (flash green)

---

### When `edges_updated` Event Received:

**Update**:
- ✅ Refresh edges table (fetch latest edges)
- ✅ Update edge summary cards:
  - "Active Edges: 3"
  - "Max Edge: 26.25%"
  - "Total Size: $900"
- ✅ Highlight changed edges (flash blue)
- ✅ Add log entry: "🧮 Edges updated: 3 positive edges"

---

## 🔌 WebSocket Endpoint

**URL**: `ws://localhost:8000/ws/trading`

**Connection**:
```typescript
const ws = new WebSocket('ws://localhost:8000/ws/trading');
```

**Message Format**:
```json
{
  "type": "cycle_complete" | "trade_placed" | "edges_updated",
  "timestamp": "2025-11-17T20:30:00",
  "data": {
    // Event-specific data
  }
}
```

**Connection Status**:
- Check: `GET /ws/status` (returns connection count)

---

## ⚡ Real-Time Update Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ Trading Engine (Dynamic Paper Trading)                          │
│                                                                 │
│ 1. Fetches Zeus forecast                                        │
│ 2. Fetches Polymarket prices                                    │
│ 3. Calculates edges                                             │
│ 4. Places trades                                                │
│ 5. Saves snapshots to disk                                      │
│    └─> data/snapshots/dynamic/decisions/EGLC/2025-11-17/...    │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ File Watcher (Backend)                                          │
│                                                                 │
│ 1. Detects new snapshot file                                    │
│ 2. Reads file content                                           │
│ 3. Determines event type (cycle_complete, trade_placed, etc.)  │
│ 4. Extracts metadata                                            │
│ 5. Broadcasts via WebSocket                                     │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ WebSocket Service (Backend)                                     │
│                                                                 │
│ 1. Receives broadcast request                                   │
│ 2. Sends message to ALL connected clients                       │
│    └─> { type: "trade_placed", data: {...} }                   │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ Frontend (All Connected Clients)                                │
│                                                                 │
│ 1. Receives WebSocket message                                   │
│ 2. Parses JSON                                                  │
│ 3. Updates UI immediately:                                      │
│    • Show notification                                          │
│    • Update tables                                              │
│    • Refresh graphs                                             │
│    • Add to activity log                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Key Benefits for Frontend

### 1. **Instant Updates**
- No polling delay
- Users see trades/edges immediately
- Feels like a live system

### 2. **Efficient**
- Only sends data when something changes
- No wasted bandwidth
- Lower server load

### 3. **Better UX**
- Real-time notifications
- Live activity log
- Instant feedback

### 4. **Scalable**
- Multiple clients can connect
- Each gets updates independently
- No polling overhead

---

## 📋 Implementation Checklist

### Frontend
- [ ] Connect to WebSocket on component mount
- [ ] Handle connection/disconnection states
- [ ] Parse incoming messages
- [ ] Update UI for each event type:
  - [ ] `cycle_complete` → Refresh dashboard
  - [ ] `trade_placed` → Show notification, update tables
  - [ ] `edges_updated` → Refresh edges table
- [ ] Reconnect on disconnect
- [ ] Show connection status indicator
- [ ] Handle errors gracefully

### Backend (Already Implemented)
- [x] WebSocket endpoint (`/ws/trading`)
- [x] File watcher for snapshots
- [x] Event broadcasting
- [x] Connection management

---

## 🔧 Troubleshooting

### WebSocket Won't Connect

**Check**:
1. Backend is running: `curl http://localhost:8000/health`
2. WebSocket endpoint exists: `ws://localhost:8000/ws/trading`
3. Browser console for errors
4. Network tab for WebSocket connection

**Common Issues**:
- ❌ Wrong URL: `ws://127.0.0.1:8000` (use `localhost`)
- ❌ HTTPS page trying to connect to `ws://` (use `wss://` or HTTP)
- ❌ Firewall blocking WebSocket connections

---

### Not Receiving Messages

**Check**:
1. File watcher is running (check backend logs)
2. Snapshots are being created (check `data/snapshots/dynamic/`)
3. WebSocket connection is active (check connection status)
4. Browser console for received messages

**Debug**:
```typescript
ws.onmessage = (event) => {
  console.log('WebSocket message received:', event.data);
  // ... handle message
};
```

---

## ✅ Summary

**WebSocket provides real-time updates** to the frontend when:
- ✅ Trading cycles complete
- ✅ Trades are placed
- ✅ Edges are updated

**How it works**:
1. Trading engine saves snapshots to disk
2. File watcher detects new files
3. WebSocket broadcasts events to all connected clients
4. Frontend receives updates instantly and updates UI

**Result**: Live, real-time dashboard that updates automatically without polling!

---

**Last Updated**: November 17, 2025

