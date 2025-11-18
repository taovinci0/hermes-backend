"""Engine control endpoints."""

from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel

from ..services.engine_service import EngineService

router = APIRouter()
engine_service = EngineService()


class TradingConfig(BaseModel):
    """Trading parameters."""
    edge_min: float
    fee_bp: int
    slippage_bp: int
    kelly_cap: float
    per_market_cap: float
    liquidity_min_usd: float
    daily_bankroll_cap: float


class ProbabilityModelConfig(BaseModel):
    """Probability model parameters."""
    model_mode: str
    zeus_likely_pct: float
    zeus_possible_pct: float


class StartEngineRequest(BaseModel):
    """Request to start engine."""
    stations: List[str]
    interval_seconds: int
    lookahead_days: int
    trading: TradingConfig
    probability_model: ProbabilityModelConfig


@router.post("/start")
async def start_engine(request: StartEngineRequest):
    """Start trading engine with configuration.
    
    Args:
        request: Engine start request with configuration
        
    Returns:
        Dictionary with success status, PID, and configuration
    """
    result = engine_service.start_engine(
        stations=request.stations,
        interval_seconds=request.interval_seconds,
        lookahead_days=request.lookahead_days,
        trading_config=request.trading.model_dump(),
        probability_model_config=request.probability_model.model_dump(),
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.post("/stop")
async def stop_engine():
    """Stop trading engine gracefully.
    
    Returns:
        Dictionary with success status and message
    """
    result = engine_service.stop_engine()
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.post("/restart")
async def restart_engine(request: StartEngineRequest):
    """Restart trading engine with new configuration.
    
    Args:
        request: Engine restart request with configuration
        
    Returns:
        Dictionary with success status, PID, and configuration
    """
    result = engine_service.restart_engine(
        stations=request.stations,
        interval_seconds=request.interval_seconds,
        lookahead_days=request.lookahead_days,
        trading_config=request.trading.model_dump(),
        probability_model_config=request.probability_model.model_dump(),
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.get("/config")
async def get_engine_config():
    """Get current engine configuration.
    
    Returns:
        Engine configuration dictionary
        
    Raises:
        HTTPException: If engine is not running or no config found
    """
    config = engine_service.get_engine_config()
    
    if config is None:
        raise HTTPException(
            status_code=404,
            detail="Engine not running or no config found"
        )
    
    return config

