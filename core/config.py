"""Configuration management for Hermes.

Loads settings from environment variables and optional config.local.yaml overrides.
"""

import os
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load .env file if present
load_dotenv()

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent


class ZeusConfig(BaseModel):
    """Zeus weather API configuration."""

    api_base: str = Field(default="https://api.zeussubnet.com")
    api_key: str = Field(default="")


class PolymarketConfig(BaseModel):
    """Polymarket API configuration."""

    gamma_base: str = Field(default="https://gamma-api.polymarket.com")
    clob_base: str = Field(default="https://clob.polymarket.com")


class TradingConfig(BaseModel):
    """Trading parameters and risk limits."""

    active_stations: list[str] = Field(default=["EGLC", "KLGA"])
    edge_min: float = Field(default=0.05, description="Minimum edge to trade (5%)")
    fee_bp: int = Field(default=50, description="Effective fees in basis points (0.50%)")
    slippage_bp: int = Field(default=30, description="Assumed slippage in basis points")
    kelly_cap: float = Field(
        default=0.10, description="Max Kelly fraction per decision (10% of bankroll)"
    )
    daily_bankroll_cap: float = Field(default=3000.0, description="Daily bankroll limit USD")
    per_market_cap: float = Field(default=500.0, description="Per-market position limit USD")
    liquidity_min_usd: float = Field(
        default=1000.0, description="Minimum liquidity required to trade"
    )


class Config(BaseModel):
    """Main Hermes configuration."""

    zeus: ZeusConfig = Field(default_factory=ZeusConfig)
    polymarket: PolymarketConfig = Field(default_factory=PolymarketConfig)
    trading: TradingConfig = Field(default_factory=TradingConfig)
    execution_mode: str = Field(default="paper", description="Execution mode: paper or live")
    log_level: str = Field(default="INFO")
    
    # Probability model configuration (Stage 7B)
    model_mode: str = Field(default="spread", description="Probability model: spread or bands")
    zeus_likely_pct: float = Field(default=0.80, description="Zeus likely confidence level (80%)")
    zeus_possible_pct: float = Field(default=0.95, description="Zeus possible confidence level (95%)")
    
    # Dynamic trading configuration (Stage 7C)
    dynamic_interval_seconds: int = Field(default=900, description="Dynamic evaluation interval (seconds)")
    dynamic_lookahead_days: int = Field(default=2, description="Days ahead to check for markets")

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "Config":
        """Load configuration from environment and optional YAML file.

        Args:
            config_path: Optional path to config.local.yaml for overrides

        Returns:
            Config instance with loaded settings
        """
        # Start with environment variables
        config_dict = {
            "zeus": {
                "api_base": os.getenv("ZEUS_API_BASE", "https://api.zeussubnet.com"),
                "api_key": os.getenv("ZEUS_API_KEY", ""),
            },
            "polymarket": {
                "gamma_base": os.getenv(
                    "POLY_GAMMA_BASE", "https://gamma-api.polymarket.com"
                ),
                "clob_base": os.getenv("POLY_CLOB_BASE", "https://clob.polymarket.com"),
            },
            "trading": {
                "active_stations": os.getenv("ACTIVE_STATIONS", "EGLC,KLGA").split(","),
                "edge_min": float(os.getenv("EDGE_MIN", "0.05")),
                "fee_bp": int(os.getenv("FEE_BP", "50")),
                "slippage_bp": int(os.getenv("SLIPPAGE_BP", "30")),
                "kelly_cap": float(os.getenv("KELLY_CAP", "0.10")),
                "daily_bankroll_cap": float(os.getenv("DAILY_BANKROLL_CAP", "3000")),
                "per_market_cap": float(os.getenv("PER_MARKET_CAP", "500")),
                "liquidity_min_usd": float(os.getenv("LIQUIDITY_MIN_USD", "1000")),
            },
            "execution_mode": os.getenv("EXECUTION_MODE", "paper"),
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
                # Probability model configuration (Stage 7B)
                "model_mode": os.getenv("MODEL_MODE", "spread").lower(),
                "zeus_likely_pct": float(os.getenv("ZEUS_LIKELY_PCT", "0.80")),
                "zeus_possible_pct": float(os.getenv("ZEUS_POSSIBLE_PCT", "0.95")),
                # Dynamic trading configuration (Stage 7C)
                "dynamic_interval_seconds": int(os.getenv("DYNAMIC_INTERVAL_SECONDS", "900")),
                "dynamic_lookahead_days": int(os.getenv("DYNAMIC_LOOKAHEAD_DAYS", "2")),
            }

        # Load overrides from config.local.yaml if present
        if config_path is None:
            config_path = PROJECT_ROOT / "config.local.yaml"

        if config_path.exists():
            with open(config_path, "r") as f:
                overrides = yaml.safe_load(f)
                if overrides:
                    _deep_update(config_dict, overrides)

        return cls(**config_dict)


def _deep_update(base: dict, updates: dict) -> None:
    """Recursively update nested dictionary."""
    for key, value in updates.items():
        if isinstance(value, dict) and key in base and isinstance(base[key], dict):
            _deep_update(base[key], value)
        else:
            base[key] = value


# Global config instance
config = Config.load()

