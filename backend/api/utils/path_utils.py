"""Path utilities for backend services."""

from pathlib import Path
from typing import Optional


# Project root (two levels up from this file: backend/api/utils -> backend -> root)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


def get_data_root() -> Path:
    """Get the data directory root."""
    return PROJECT_ROOT / "data"


def get_snapshots_dir() -> Path:
    """Get the snapshots directory."""
    return get_data_root() / "snapshots" / "dynamic"


def get_trades_dir() -> Path:
    """Get the trades directory."""
    return get_data_root() / "trades"


def get_logs_dir() -> Path:
    """Get the logs directory."""
    return PROJECT_ROOT / "logs"

