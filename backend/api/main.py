"""FastAPI main application."""

from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .models.schemas import HealthResponse
from .routes import status, snapshots, trades, logs, edges, metar, compare, websocket, backtest, engine, config, performance, stations

# Import file watcher (optional - only if watchdog is installed)
try:
    from .utils.file_watcher import snapshot_watcher
    FILE_WATCHER_AVAILABLE = True
except ImportError:
    FILE_WATCHER_AVAILABLE = False
    snapshot_watcher = None

# Create FastAPI app
app = FastAPI(
    title="Hermes Trading System API",
    description="Backend API for Hermes trading system dashboard",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(status.router, prefix="/api", tags=["status"])
app.include_router(snapshots.router, prefix="/api/snapshots", tags=["snapshots"])
app.include_router(trades.router, prefix="/api/trades", tags=["trades"])
app.include_router(logs.router, prefix="/api/logs", tags=["logs"])
app.include_router(edges.router, prefix="/api/edges", tags=["edges"])
app.include_router(metar.router, prefix="/api/metar", tags=["metar"])
app.include_router(compare.router, prefix="/api/compare", tags=["compare"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])
app.include_router(backtest.router, prefix="/api/backtest", tags=["backtest"])
app.include_router(engine.router, prefix="/api/engine", tags=["engine"])
app.include_router(config.router, prefix="/api/config", tags=["config"])
app.include_router(performance.router, prefix="/api/performance", tags=["performance"])
app.include_router(stations.router, prefix="/api/stations", tags=["stations"])


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check."""
    return HealthResponse(
        status="ok",
        timestamp=datetime.utcnow().isoformat(),
    )


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        timestamp=datetime.utcnow().isoformat(),
    )


@app.on_event("startup")
async def startup_event():
    """Startup event: initialize file watcher."""
    if FILE_WATCHER_AVAILABLE and snapshot_watcher:
        snapshot_watcher.start()


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event: stop file watcher."""
    if FILE_WATCHER_AVAILABLE and snapshot_watcher:
        snapshot_watcher.stop()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

