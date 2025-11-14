"""Status endpoints."""

from fastapi import APIRouter
from datetime import datetime

from ..models.schemas import HealthResponse
from ..services.status_service import StatusService

router = APIRouter()
status_service = StatusService()


@router.get("/status")
async def get_status():
    """Get system status including trading engine state."""
    return status_service.get_system_status()


@router.get("/status/health", response_model=HealthResponse)
async def get_health():
    """Get basic health check."""
    return HealthResponse(
        status="ok",
        timestamp=datetime.utcnow().isoformat(),
    )

