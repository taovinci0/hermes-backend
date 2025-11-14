# Hermes Snapshotter - Standalone Data Collection Project

**Date**: November 13, 2025  
**Purpose**: Independent data collection daemon to gather valuable trading data  
**Status**: Complete Standalone Specification

---

## 🎯 Objective

Create a **standalone, independent project** (`hermes-snapshotter`) that continuously collects:
- **Zeus forecasts** (hourly temperature predictions)
- **Polymarket pricing** (market-implied probabilities)
- **METAR observations** (actual temperatures)

This runs **24/7** to collect valuable historical data for trading system development.

---

## 📋 Overview

### What We're Building:

A **lightweight data collection daemon** that:
- Runs continuously (every 15 minutes by default)
- Fetches Zeus, Polymarket, and METAR data
- Saves snapshots to disk
- **Does NOT** make trading decisions or execute trades
- **Does NOT** collect decision snapshots (can be backtested later)

### Key Features:

✅ **Standalone** - No dependencies on other projects  
✅ **Self-contained** - All code included in this specification  
✅ **Simple** - Focused only on data collection  
✅ **Robust** - Retry logic, error handling, deduplication

---

## 🏗️ Project Structure

```
hermes-snapshotter/
├── README.md
├── .env                                # API keys (create from .env.sample)
├── .env.sample                         # Template
├── requirements.txt                    # Python dependencies
├── pyproject.toml                      # Optional: Python project config
│
├── snapshotter/                        # Core collection logic
│   ├── __init__.py
│   ├── collector.py                    # Main collection loop
│   └── config.py                       # Configuration
│
├── core/                               # Core utilities
│   ├── __init__.py
│   ├── config.py                       # Config management
│   ├── logger.py                       # Logging
│   ├── registry.py                     # Station registry
│   └── types.py                        # Data types
│
├── agents/                             # Data fetching agents
│   ├── __init__.py
│   └── zeus_forecast.py                # Zeus API client
│
├── venues/                             # External data sources
│   ├── __init__.py
│   ├── polymarket/
│   │   ├── __init__.py
│   │   ├── discovery.py                # Market discovery
│   │   ├── pricing.py                  # Price fetching
│   │   └── schemas.py                  # Data models
│   └── metar/
│       ├── __init__.py
│       └── metar_service.py            # METAR API client
│
├── data/                               # Data storage
│   ├── registry/
│   │   └── stations.csv                # Weather station metadata
│   └── snapshots/
│       └── dynamic/                    # Collected snapshots
│           ├── zeus/
│           ├── polymarket/
│           └── metar/
│
└── run_snapshotter.py                  # Main entry point
```

---

## 📦 Complete Implementation

### Step 1: Create Project Structure

```bash
# Create project directory
mkdir hermes-snapshotter
cd hermes-snapshotter

# Create directory structure
mkdir -p snapshotter core agents venues/{polymarket,metar} data/registry data/snapshots/dynamic/{zeus,polymarket,metar}

# Initialize Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 2: Create requirements.txt

**File: `requirements.txt`**
```
requests>=2.31.0
tenacity>=8.2.0
pydantic>=2.0.0
python-dotenv>=1.0.0
pyyaml>=6.0
rich>=13.0.0
```

### Step 3: Create Core Files

**File: `core/__init__.py`**
```python
"""Core utilities for Hermes Snapshotter."""

from . import config, logger, registry, types

__all__ = ["config", "logger", "registry", "types"]
```

**File: `core/config.py`**
```python
"""Configuration management for Hermes Snapshotter."""

import os
from pathlib import Path
from typing import Optional

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


class METARConfig(BaseModel):
    """METAR API configuration."""

    api_base: str = Field(default="https://aviationweather.gov/api/data/metar")
    user_agent: str = Field(default="HermesSnapshotter/1.0")


class Config(BaseModel):
    """Main configuration."""

    zeus: ZeusConfig = Field(default_factory=ZeusConfig)
    polymarket: PolymarketConfig = Field(default_factory=PolymarketConfig)
    metar: METARConfig = Field(default_factory=METARConfig)
    log_level: str = Field(default="INFO")

    @classmethod
    def load(cls) -> "Config":
        """Load configuration from environment variables."""
        return cls(
            zeus=ZeusConfig(
                api_base=os.getenv("ZEUS_API_BASE", "https://api.zeussubnet.com"),
                api_key=os.getenv("ZEUS_API_KEY", ""),
            ),
            polymarket=PolymarketConfig(
                gamma_base=os.getenv(
                    "POLY_GAMMA_BASE", "https://gamma-api.polymarket.com"
                ),
                clob_base=os.getenv("POLY_CLOB_BASE", "https://clob.polymarket.com"),
            ),
            metar=METARConfig(
                api_base=os.getenv(
                    "METAR_API_BASE", "https://aviationweather.gov/api/data/metar"
                ),
                user_agent=os.getenv("METAR_USER_AGENT", "HermesSnapshotter/1.0"),
            ),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )


# Global config instance
config = Config.load()
```

**File: `core/logger.py`**
```python
"""Structured logging for Hermes Snapshotter."""

import logging
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler

from .config import config, PROJECT_ROOT


def setup_logger(
    name: str = "hermes-snapshotter",
    level: Optional[str] = None,
    log_file: Optional[Path] = None,
) -> logging.Logger:
    """Configure and return a logger instance."""
    if level is None:
        level = config.log_level

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    logger.handlers.clear()

    # Rich console handler for terminal output
    console = Console(stderr=True)
    rich_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=True,
        markup=True,
        rich_tracebacks=True,
    )
    rich_handler.setFormatter(
        logging.Formatter(
            fmt="%(message)s",
            datefmt="[%Y-%m-%d %H:%M:%S]",
        )
    )
    logger.addHandler(rich_handler)

    # Optional file handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(file_handler)

    return logger


# Default logger instance
logger = setup_logger()
```

**File: `core/types.py`**
```python
"""Type definitions for Hermes Snapshotter."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ForecastPoint(BaseModel):
    """Single point in a temperature forecast timeseries."""

    time_utc: datetime = Field(description="Forecast timestamp in UTC")
    temp_K: float = Field(description="Temperature in Kelvin")


class ZeusForecast(BaseModel):
    """Complete Zeus weather forecast for a location."""

    timeseries: list[ForecastPoint] = Field(description="Hourly forecast points")
    station_code: str = Field(description="Weather station identifier")
    lat: Optional[float] = None
    lon: Optional[float] = None
    fetch_time: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this forecast was retrieved"
    )


class MarketBracket(BaseModel):
    """Temperature bracket for a prediction market."""

    name: str = Field(description="Bracket display name, e.g., '59-60°F'")
    lower_F: int = Field(description="Lower bound in °F (inclusive)")
    upper_F: int = Field(description="Upper bound in °F (exclusive)")
    market_id: Optional[str] = Field(default=None, description="Market ID for resolution")
    token_id: Optional[str] = Field(default=None, description="CLOB token ID for pricing")
    closed: Optional[bool] = Field(default=None, description="Whether market is closed/resolved")
```

**File: `core/registry.py`**
```python
"""Station registry management."""

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .config import PROJECT_ROOT
from .logger import logger


@dataclass
class Station:
    """Weather station metadata."""

    city: str
    station_name: str
    station_code: str
    lat: float
    lon: float
    noaa_station: str
    venue_hint: str
    time_zone: str

    def __repr__(self) -> str:
        return f"Station({self.city}, {self.station_code}, tz={self.time_zone})"


class StationRegistry:
    """Registry of weather stations for trading."""

    def __init__(self, registry_path: Optional[Path] = None):
        """Initialize station registry."""
        if registry_path is None:
            registry_path = PROJECT_ROOT / "data" / "registry" / "stations.csv"

        self.registry_path = registry_path
        self.stations: dict[str, Station] = {}
        self._load()

    def _load(self) -> None:
        """Load stations from CSV file."""
        if not self.registry_path.exists():
            logger.warning(
                f"Station registry not found at {self.registry_path}. "
                "Registry will be empty."
            )
            return

        try:
            with open(self.registry_path, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    station = Station(
                        city=row["city"],
                        station_name=row["station_name"],
                        station_code=row["station_code"],
                        lat=float(row["lat"]),
                        lon=float(row["lon"]),
                        noaa_station=row["noaa_station"],
                        venue_hint=row["venue_hint"],
                        time_zone=row["time_zone"],
                    )
                    self.stations[station.station_code] = station

            logger.info(f"Loaded {len(self.stations)} stations from registry")

        except Exception as e:
            logger.error(f"Failed to load station registry: {e}")
            raise

    def get(self, station_code: str) -> Optional[Station]:
        """Get station by code."""
        return self.stations.get(station_code)

    def list_all(self) -> list[Station]:
        """Get all stations."""
        return list(self.stations.values())
```

### Step 4: Create Agent Files

**File: `agents/__init__.py`**
```python
"""Data fetching agents."""

from .zeus_forecast import ZeusForecastAgent, ZeusForecast, ZeusAPIError

__all__ = ["ZeusForecastAgent", "ZeusForecast", "ZeusAPIError"]
```

**File: `agents/zeus_forecast.py`**
```python
"""Zeus weather forecast agent."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from core.types import ZeusForecast, ForecastPoint
from core.config import config, PROJECT_ROOT
from core.logger import logger


class ZeusAPIError(Exception):
    """Exception raised for Zeus API errors."""
    pass


class ZeusForecastAgent:
    """Agent for fetching Zeus weather forecasts."""

    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None):
        """Initialize Zeus forecast agent."""
        self.api_key = api_key or config.zeus.api_key
        self.api_base = api_base or config.zeus.api_base
        self.snapshot_dir = PROJECT_ROOT / "data" / "snapshots" / "zeus"

        if not self.api_key or self.api_key == "changeme":
            logger.warning("⚠️  Zeus API key not configured")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def _call_zeus_api(
        self,
        lat: float,
        lon: float,
        start_utc: datetime,
        predict_hours: int,
    ) -> dict:
        """Call Zeus API with retry logic."""
        url = f"{self.api_base}/forecast"
        
        start_time_str = start_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        params = {
            "latitude": lat,
            "longitude": lon,
            "variable": "2m_temperature",
            "start_time": start_time_str,
            "predict_hours": predict_hours,
        }
        
        logger.info(
            f"Calling Zeus API: lat={lat:.4f}, lon={lon:.4f}, "
            f"start={start_time_str}, hours={predict_hours}"
        )
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Zeus API call successful")
            return data
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"Zeus API HTTP error: {e}")
            raise ZeusAPIError(f"Zeus API HTTP error: {e}") from e
        except requests.exceptions.Timeout as e:
            logger.error(f"Zeus API timeout: {e}")
            raise ZeusAPIError(f"Zeus API timeout: {e}") from e
        except requests.exceptions.RequestException as e:
            logger.error(f"Zeus API request error: {e}")
            raise ZeusAPIError(f"Zeus API request error: {e}") from e
        except json.JSONDecodeError as e:
            logger.error(f"Zeus API JSON decode error: {e}")
            raise ZeusAPIError(f"Zeus API JSON decode error: {e}") from e

    def fetch(
        self,
        lat: float,
        lon: float,
        start_utc: datetime,
        hours: int = 24,
        station_code: Optional[str] = None,
    ) -> ZeusForecast:
        """Fetch hourly temperature forecast from Zeus."""
        raw_data = self._call_zeus_api(lat, lon, start_utc, hours)
        
        # Parse response into ForecastPoint objects
        try:
            timeseries = []
            
            # Zeus API format: separate arrays for temperature and time
            if "2m_temperature" in raw_data and "time" in raw_data:
                logger.debug("Using Zeus API array format (2m_temperature + time)")
                
                temp_data = raw_data["2m_temperature"]
                time_data = raw_data["time"]
                
                if not isinstance(temp_data, dict) or "data" not in temp_data:
                    raise ValueError("2m_temperature must have 'data' field")
                
                if not isinstance(time_data, dict) or "data" not in time_data:
                    raise ValueError("time must have 'data' field")
                
                temperatures = temp_data["data"]
                timestamps = time_data["data"]
                
                if len(temperatures) != len(timestamps):
                    raise ValueError("Temperature and time arrays must have same length")
                
                for temp_k, timestamp in zip(temperatures, timestamps):
                    # Parse timestamp
                    if isinstance(timestamp, str):
                        time_utc = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    elif isinstance(timestamp, (int, float)):
                        time_utc = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                    else:
                        time_utc = timestamp
                    
                    timeseries.append(
                        ForecastPoint(
                            time_utc=time_utc,
                            temp_K=float(temp_k),
                        )
                    )
            
            # Fallback: object-based format
            else:
                logger.debug("Using object-based forecast format")
                forecast_data = raw_data.get("forecast", [])
                
                if not forecast_data:
                    raise ValueError("No forecast data in Zeus API response")
                
                for point in forecast_data:
                    time_str = point.get("time") or point.get("timestamp")
                    if not time_str:
                        continue
                    
                    time_utc = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
                    temp_k = point.get("temperature_k") or point.get("temp_k") or point.get("temperature")
                    if temp_k is None:
                        continue
                    
                    timeseries.append(
                        ForecastPoint(
                            time_utc=time_utc,
                            temp_K=float(temp_k),
                        )
                    )
            
            if not timeseries:
                raise ValueError("No valid forecast points parsed from Zeus response")
            
            forecast = ZeusForecast(
                timeseries=timeseries,
                station_code=station_code or "UNKNOWN",
                lat=lat,
                lon=lon,
            )
            
            logger.info(
                f"Parsed {len(forecast.timeseries)} forecast points "
                f"for {forecast.station_code}"
            )
            
            return forecast
            
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Failed to parse Zeus API response: {e}")
            raise ValueError(f"Failed to parse Zeus API response: {e}") from e
```

### Step 5: Create Venue Files

**File: `venues/__init__.py`**
```python
"""External data source integrations."""
```

**File: `venues/polymarket/__init__.py`**
```python
"""Polymarket integration."""

from .discovery import PolyDiscovery, PolymarketAPIError
from .pricing import PolyPricing, PolymarketPricingError

__all__ = ["PolyDiscovery", "PolyPricing", "PolymarketAPIError", "PolymarketPricingError"]
```

**File: `venues/polymarket/schemas.py`**
```python
"""Polymarket API schemas."""

from typing import Optional, List
from pydantic import BaseModel, Field


class CLOBBook(BaseModel):
    """CLOB order book side (bids or asks)."""

    price: str
    size: str


class CLOBOrderBook(BaseModel):
    """CLOB order book response."""

    market: str
    asset_id: Optional[str] = None
    bids: List[CLOBBook] = Field(default_factory=list)
    asks: List[CLOBBook] = Field(default_factory=list)
    timestamp: Optional[int] = None


class MarketDepth(BaseModel):
    """Aggregated market depth/liquidity."""

    token_id: str
    bid_depth_usd: float = Field(default=0.0)
    ask_depth_usd: float = Field(default=0.0)
    spread_bps: Optional[float] = None
    mid_price: Optional[float] = None
```

**File: `venues/polymarket/discovery.py`**
```python
"""Polymarket market discovery."""

import json
import re
from datetime import date
from pathlib import Path
from typing import List, Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from core.types import MarketBracket
from core.config import config, PROJECT_ROOT
from core.logger import logger


class PolymarketAPIError(Exception):
    """Exception raised for Polymarket API errors."""
    pass


class PolyDiscovery:
    """Discovers daily temperature markets on Polymarket."""

    def __init__(self, gamma_base: Optional[str] = None):
        """Initialize Polymarket discovery agent."""
        self.gamma_base = gamma_base or config.polymarket.gamma_base
        self.snapshot_dir = PROJECT_ROOT / "data" / "snapshots" / "polymarket"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def _call_gamma_api(
        self,
        endpoint: str,
        params: Optional[dict] = None,
    ) -> dict:
        """Call Gamma API with retry logic."""
        url = f"{self.gamma_base}{endpoint}"
        
        logger.debug(f"Calling Gamma API: {endpoint}")
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"Gamma API HTTP error: {e}")
            raise PolymarketAPIError(f"Gamma API HTTP error: {e}") from e
        except requests.exceptions.Timeout as e:
            logger.error(f"Gamma API timeout: {e}")
            raise PolymarketAPIError(f"Gamma API timeout: {e}") from e
        except requests.exceptions.RequestException as e:
            logger.error(f"Gamma API request error: {e}")
            raise PolymarketAPIError(f"Gamma API request error: {e}") from e
        except json.JSONDecodeError as e:
            logger.error(f"Gamma API JSON decode error: {e}")
            raise PolymarketAPIError(f"Gamma API JSON decode error: {e}") from e
    
    def get_event_by_slug(self, slug: str, save_snapshot: bool = True) -> Optional[dict]:
        """Fetch a Polymarket event (and its markets) by slug."""
        logger.debug(f"Fetching event by slug: {slug}")
        
        try:
            endpoint = f"/events/slug/{slug}"
            data = self._call_gamma_api(endpoint)
            
            # Handle both array and single object responses
            if isinstance(data, list):
                if not data:
                    return None
                event = data[0]
            else:
                event = data
            
            logger.info(f"Found event: {slug}")
            return event
            
        except PolymarketAPIError as e:
            if "404" in str(e) or "Not Found" in str(e):
                logger.debug(f"Event not found: {slug}")
                return None
            raise
    
    def _generate_event_slugs(self, city: str, date_local: date) -> List[str]:
        """Generate possible event slugs for a city/date combination."""
        city_clean = city.lower().replace(" (airport)", "").replace(" (city)", "")
        city_slug = city_clean.replace(" ", "-")
        
        month = date_local.strftime("%B").lower()
        day = date_local.day
        
        patterns = [
            f"highest-temperature-in-{city_slug}-on-{month}-{day}",
            f"temperature-in-{city_slug}-on-{month}-{day}",
            f"high-temperature-in-{city_slug}-on-{month}-{day}",
        ]
        
        # NYC special cases
        if "new york" in city_clean or "nyc" in city_clean:
            patterns.extend([
                f"highest-temperature-in-nyc-on-{month}-{day}",
                f"temperature-in-nyc-on-{month}-{day}",
            ])
        
        return patterns

    def _parse_bracket_from_name(self, name: str) -> Optional[tuple[int, int]]:
        """Parse temperature bracket from market name."""
        patterns = [
            r'(\d+)\s*[-–—]\s*(\d+)\s*°?F',
            r'(\d+)\s+to\s+(\d+)\s*°?F',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                lower = int(match.group(1))
                upper = int(match.group(2))
                
                if lower < upper and 0 < lower < 150 and 0 < upper < 150:
                    return (lower, upper)
        
        return None
    
    def _parse_bracket_from_market(self, market_data: dict) -> Optional[MarketBracket]:
        """Parse a MarketBracket from Polymarket market object."""
        try:
            question = market_data.get("question", "")
            market_id = market_data.get("id")
            
            clob_ids = market_data.get("clobTokenIds")
            clob_token_id = None
            if isinstance(clob_ids, list) and clob_ids:
                clob_token_id = clob_ids[0]
            elif isinstance(clob_ids, str):
                clob_token_id = clob_ids.split(",")[0].strip().strip('"[]')
            
            if not question or not market_id:
                return None
            
            bracket_tuple = self._parse_bracket_from_name(question)
            if not bracket_tuple:
                return None
            
            lower_F, upper_F = bracket_tuple
            closed = market_data.get("closed", False)
            
            return MarketBracket(
                name=f"{lower_F}-{upper_F}°F",
                lower_F=lower_F,
                upper_F=upper_F,
                market_id=market_id,
                token_id=clob_token_id,
                closed=closed,
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse market bracket: {e}")
            return None

    def list_temp_brackets(
        self,
        city: str,
        date_local: date,
        save_snapshot: bool = True,
    ) -> List[MarketBracket]:
        """List temperature brackets for a city and date."""
        logger.info(f"Discovering Polymarket temp brackets for {city} on {date_local}")
        
        slugs = self._generate_event_slugs(city, date_local)
        
        event = None
        successful_slug = None
        
        for slug in slugs:
            logger.debug(f"Trying event slug: {slug}")
            event = self.get_event_by_slug(slug, save_snapshot=False)
            if event:
                successful_slug = slug
                break
        
        if not event:
            logger.warning(f"No event found for {city} on {date_local}")
            return []
        
        markets_data = event.get("markets", [])
        
        if not markets_data:
            logger.warning(f"Event {successful_slug} has no markets")
            return []
        
        logger.info(f"Found event '{successful_slug}' with {len(markets_data)} markets")
        
        brackets = []
        for market_data in markets_data:
            bracket = self._parse_bracket_from_market(market_data)
            if bracket:
                brackets.append(bracket)
        
        if brackets:
            brackets.sort(key=lambda b: b.lower_F)
            logger.info(
                f"✅ Parsed {len(brackets)} temperature brackets for {city}, "
                f"range: [{brackets[0].lower_F}-{brackets[-1].upper_F}°F)"
            )
        
        return brackets
```

**File: `venues/polymarket/pricing.py`**
```python
"""Polymarket pricing."""

import json
from pathlib import Path
from typing import Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from core.types import MarketBracket
from core.config import config, PROJECT_ROOT
from core.logger import logger


class PolymarketPricingError(Exception):
    """Exception raised for Polymarket pricing errors."""
    pass


class PolyPricing:
    """Reads prices from Polymarket CLOB."""

    def __init__(self, clob_base: Optional[str] = None):
        """Initialize Polymarket pricing agent."""
        self.clob_base = clob_base or config.polymarket.clob_base
        self.snapshot_dir = PROJECT_ROOT / "data" / "snapshots" / "polymarket"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def _call_clob_api(
        self,
        endpoint: str,
        params: Optional[dict] = None,
    ) -> dict:
        """Call CLOB API with retry logic."""
        url = f"{self.clob_base}{endpoint}"
        
        logger.debug(f"Calling CLOB API: {endpoint}")
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"CLOB API HTTP error: {e}")
            raise PolymarketPricingError(f"CLOB API HTTP error: {e}") from e
        except requests.exceptions.Timeout as e:
            logger.error(f"CLOB API timeout: {e}")
            raise PolymarketPricingError(f"CLOB API timeout: {e}") from e
        except requests.exceptions.RequestException as e:
            logger.error(f"CLOB API request error: {e}")
            raise PolymarketPricingError(f"CLOB API request error: {e}") from e
        except json.JSONDecodeError as e:
            logger.error(f"CLOB API JSON decode error: {e}")
            raise PolymarketPricingError(f"CLOB API JSON decode error: {e}") from e

    def midprob(
        self,
        bracket: MarketBracket,
        save_snapshot: bool = False,
    ) -> float:
        """Get market-implied probability from midprice."""
        if not bracket.market_id:
            raise ValueError(f"Bracket {bracket.name} has no market_id")
        
        logger.debug(f"Fetching midprice for {bracket.name}")
        
        try:
            token_id = bracket.token_id or bracket.market_id
            
            data = self._call_clob_api(
                "/midpoint",
                params={"token_id": token_id}
            )
            
            if isinstance(data, dict):
                mid = data.get("mid")
                
                if mid is None:
                    raise ValueError(f"No midprice in response for {bracket.name}")
                
                prob = float(mid)
                
                if not 0.0 <= prob <= 1.0:
                    logger.warning(f"Midprice {prob} out of range [0,1], clamping")
                    prob = max(0.0, min(1.0, prob))
                
                logger.debug(f"Midprice for {bracket.name}: {prob:.4f}")
                return prob
            else:
                raise ValueError(f"Unexpected CLOB response format: {type(data)}")
            
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Failed to parse CLOB midprice: {e}")
            raise ValueError(f"Failed to parse CLOB midprice: {e}") from e
```

**File: `venues/metar/__init__.py`**
```python
"""METAR integration."""

from .metar_service import METARService, METARServiceError, MetarObservation

__all__ = ["METARService", "METARServiceError", "MetarObservation"]
```

**File: `venues/metar/metar_service.py`**
```python
"""METAR service - fetches actual temperature observations."""

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config import config, PROJECT_ROOT
from core.logger import logger


class METARServiceError(Exception):
    """Exception raised for METAR API errors."""
    pass


class MetarObservation:
    """A single METAR observation."""

    def __init__(
        self,
        station_code: str,
        time: datetime,
        temp_C: float,
        temp_F: float,
        raw: Optional[str] = None,
        dewpoint_C: Optional[float] = None,
        wind_dir: Optional[int] = None,
        wind_speed: Optional[int] = None,
    ):
        self.station_code = station_code
        self.time = time
        self.temp_C = temp_C
        self.temp_F = temp_F
        self.raw = raw
        self.dewpoint_C = dewpoint_C
        self.wind_dir = wind_dir
        self.wind_speed = wind_speed

    def __repr__(self) -> str:
        return f"MetarObservation(station={self.station_code}, time={self.time}, temp_F={self.temp_F:.1f})"


class METARService:
    """Fetch METAR observations from Aviation Weather Center API."""

    def __init__(self, api_base: Optional[str] = None, user_agent: Optional[str] = None):
        """Initialize METAR service."""
        self.api_base = api_base or config.metar.api_base
        self.user_agent = user_agent or config.metar.user_agent
        self.snapshot_dir = PROJECT_ROOT / "data" / "snapshots" / "metar"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def _call_metar_api(
        self,
        params: dict,
    ) -> List[dict]:
        """Call METAR API with retry logic."""
        params = {**params, "format": "json"}

        logger.debug(f"Calling METAR API with params {params}")

        try:
            headers = {"User-Agent": self.user_agent}
            response = requests.get(
                self.api_base,
                params=params,
                headers=headers,
                timeout=30,
            )

            if response.status_code == 204:
                logger.debug("METAR API returned 204 (no data available)")
                return []

            response.raise_for_status()
            data = response.json()

            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return [data]
            else:
                return []

        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                raise METARServiceError("METAR API rate limit exceeded") from e
            raise METARServiceError(f"METAR API HTTP error: {e}") from e
        except requests.exceptions.Timeout as e:
            raise METARServiceError(f"METAR API timeout: {e}") from e
        except requests.exceptions.RequestException as e:
            raise METARServiceError(f"METAR API request error: {e}") from e
        except json.JSONDecodeError as e:
            raise METARServiceError(f"METAR API JSON decode error: {e}") from e

    def _parse_observation(self, obs_data: dict) -> Optional[MetarObservation]:
        """Parse a single METAR observation from API response."""
        try:
            station = obs_data.get("station") or obs_data.get("icaoId", "")
            time_utc = None
            time_str = obs_data.get("time") or obs_data.get("obsTime")
            
            if time_str:
                if isinstance(time_str, str):
                    try:
                        time_utc = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
                    except (ValueError, AttributeError):
                        pass
                elif isinstance(time_str, (int, float)):
                    try:
                        time_utc = datetime.fromtimestamp(time_str, tz=timezone.utc)
                    except (ValueError, OSError):
                        pass

            if not station or not time_utc:
                return None

            temp_C = obs_data.get("temp")
            if temp_C is None:
                return None

            temp_F = round((temp_C * 9 / 5) + 32, 1)

            dewpoint_C = obs_data.get("dewpoint") or obs_data.get("dewp")
            wind_dir = obs_data.get("windDir") or obs_data.get("wdir")
            wind_speed = obs_data.get("windSpeed") or obs_data.get("wspd")
            raw = obs_data.get("rawOb") or obs_data.get("rawOb")

            return MetarObservation(
                station_code=station,
                time=time_utc,
                temp_C=round(temp_C, 1),
                temp_F=temp_F,
                raw=raw,
                dewpoint_C=round(dewpoint_C, 1) if dewpoint_C is not None else None,
                wind_dir=wind_dir,
                wind_speed=wind_speed,
            )

        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"Failed to parse observation: {e}")
            return None

    def get_observations(
        self,
        station_code: str,
        event_date: Optional[date] = None,
        hours: int = 24,
        save_snapshot: bool = False,
    ) -> List[MetarObservation]:
        """Fetch METAR observations for a station."""
        if event_date is None:
            event_date = date.today()

        start_time = datetime.combine(event_date, datetime.min.time()).replace(tzinfo=None)
        end_time = start_time + timedelta(hours=hours)

        start_str = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_str = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        params = {
            "ids": station_code,
            "start": start_str,
            "end": end_str,
        }

        logger.info(f"Fetching METAR observations for {station_code} from {start_str} to {end_str}")

        try:
            raw_data = self._call_metar_api(params)

            observations = []
            for obs_data in raw_data:
                obs = self._parse_observation(obs_data)
                if obs:
                    observations.append(obs)

            logger.info(f"Retrieved {len(observations)} valid METAR observations for {station_code}")
            return observations

        except METARServiceError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching METAR data: {e}")
            raise METARServiceError(f"Unexpected error: {e}") from e
```

### Step 6: Create Snapshotter Files

**File: `snapshotter/__init__.py`**
```python
"""Hermes Snapshotter - Data collection daemon."""

from .collector import DataCollector
from .config import SnapshotterConfig

__all__ = ["DataCollector", "SnapshotterConfig"]
```

**File: `snapshotter/config.py`**
```python
"""Configuration for Hermes Snapshotter."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Stations to collect data for
STATIONS = ["EGLC", "KLGA"]  # London, New York

# Collection interval (seconds)
COLLECTION_INTERVAL = int(os.getenv("COLLECTION_INTERVAL", "900"))  # 15 minutes

# Lookahead days (how many days ahead to check)
LOOKAHEAD_DAYS = int(os.getenv("LOOKAHEAD_DAYS", "2"))  # Today + tomorrow


class SnapshotterConfig:
    """Snapshotter configuration."""
    
    def __init__(self):
        self.stations = STATIONS
        self.collection_interval = COLLECTION_INTERVAL
        self.lookahead_days = LOOKAHEAD_DAYS
        self.project_root = PROJECT_ROOT
```

**File: `snapshotter/collector.py`**
```python
"""Data collection loop for Hermes Snapshotter."""

from datetime import datetime, date, timedelta, time
from time import sleep
from zoneinfo import ZoneInfo
from pathlib import Path
import json

from core.logger import logger
from core.registry import StationRegistry
from agents.zeus_forecast import ZeusForecastAgent
from venues.polymarket.discovery import PolyDiscovery
from venues.polymarket.pricing import PolyPricing
from venues.metar import METARService
from snapshotter.config import SnapshotterConfig, PROJECT_ROOT


class DataCollector:
    """Collect Zeus, Polymarket, and METAR snapshots."""
    
    def __init__(self):
        """Initialize collector with API clients."""
        self.config = SnapshotterConfig()
        self.registry = StationRegistry()
        self.zeus = ZeusForecastAgent()
        self.discovery = PolyDiscovery()
        self.pricing = PolyPricing()
        self.metar = METARService()
        
        self.base_dir = PROJECT_ROOT / "data" / "snapshots" / "dynamic"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Track saved METAR observations (for deduplication)
        self._saved_metar_obs = {}
        
        logger.info("📊 Hermes Snapshotter initialized")
        logger.info(f"   Stations: {', '.join(self.config.stations)}")
        logger.info(f"   Interval: {self.config.collection_interval}s ({self.config.collection_interval/60:.0f} min)")
    
    def run(self):
        """Run continuous collection loop."""
        logger.info(f"\n{'='*70}")
        logger.info(f"🔄 STARTING DATA COLLECTION")
        logger.info(f"{'='*70}")
        logger.info(f"Press Ctrl+C to stop\n")
        
        cycle_count = 0
        
        try:
            while True:
                cycle_count += 1
                cycle_start = datetime.now(ZoneInfo("UTC"))
                
                logger.info(f"\n{'='*70}")
                logger.info(f"🔄 CYCLE {cycle_count}: {cycle_start.strftime('%Y-%m-%d %H:%M:%S')} UTC")
                logger.info(f"{'='*70}")
                
                # Collect data for each station
                for station_code in self.config.stations:
                    station = self.registry.get(station_code)
                    if not station:
                        logger.warning(f"Station {station_code} not found")
                        continue
                    
                    # Check today + next N days
                    today = date.today()
                    event_days = [
                        today + timedelta(days=i) 
                        for i in range(self.config.lookahead_days)
                    ]
                    
                    for event_day in event_days:
                        self._collect_for_station(station, event_day, cycle_start)
                
                # Wait for next cycle
                cycle_end = datetime.now(ZoneInfo("UTC"))
                cycle_duration = (cycle_end - cycle_start).total_seconds()
                
                logger.info(f"\n✅ Cycle {cycle_count} complete in {cycle_duration:.1f}s")
                logger.info(f"😴 Sleeping for {self.config.collection_interval}s ({self.config.collection_interval/60:.0f} min)...")
                
                sleep(self.config.collection_interval)
        
        except KeyboardInterrupt:
            logger.info(f"\n\n{'='*70}")
            logger.info(f"🛑 Data collection stopped by user")
            logger.info(f"{'='*70}")
            logger.info(f"Total cycles: {cycle_count}")
    
    def _collect_for_station(
        self,
        station,
        event_day: date,
        cycle_time: datetime,
    ):
        """Collect all data for a station/event day."""
        logger.info(f"\n  📊 {station.city} → {event_day}")
        
        try:
            # 1. Check if markets exist
            has_markets = self._check_markets(station.city, event_day)
            
            # 2. Collect Zeus forecast
            self._collect_zeus(station, event_day, cycle_time)
            
            # 3. Collect Polymarket data (if markets exist)
            if has_markets:
                self._collect_polymarket(station.city, event_day, cycle_time)
            
            # 4. Collect METAR (only for today)
            if event_day == date.today():
                self._collect_metar(station, event_day)
        
        except Exception as e:
            logger.error(f"     ❌ Error: {e}", exc_info=False)
    
    def _check_markets(self, city: str, event_day: date) -> bool:
        """Check if markets exist for this event."""
        try:
            slugs = self.discovery._generate_event_slugs(city, event_day)
            for slug in slugs:
                event = self.discovery.get_event_by_slug(slug, save_snapshot=False)
                if event:
                    markets = event.get('markets', [])
                    open_markets = [m for m in markets if not m.get('closed')]
                    if open_markets:
                        return True
            return False
        except Exception:
            return False
    
    def _collect_zeus(self, station, event_day: date, cycle_time: datetime):
        """Collect Zeus forecast snapshot."""
        try:
            # Get local midnight for event day
            local_midnight = datetime.combine(
                event_day,
                time(0, 0),
                tzinfo=ZoneInfo(station.time_zone)
            )
            
            # Fetch forecast
            forecast = self.zeus.fetch(
                lat=station.lat,
                lon=station.lon,
                start_utc=local_midnight,
                hours=24,
                station_code=station.station_code,
            )
            
            # Save snapshot
            timestamp = cycle_time.strftime("%Y-%m-%d_%H-%M-%S")
            zeus_dir = self.base_dir / "zeus" / station.station_code / event_day.isoformat()
            zeus_dir.mkdir(parents=True, exist_ok=True)
            
            snapshot_path = zeus_dir / f"{timestamp}.json"
            
            snapshot_data = {
                "fetch_time_utc": cycle_time.isoformat(),
                "forecast_for_local_day": event_day.isoformat(),
                "start_local": local_midnight.isoformat(),
                "station_code": station.station_code,
                "city": station.city,
                "timezone": station.time_zone,
                "timeseries_count": len(forecast.timeseries),
                "timeseries": [
                    {
                        "time_utc": point.time_utc.isoformat(),
                        "temp_K": point.temp_K,
                    }
                    for point in forecast.timeseries
                ],
            }
            
            with open(snapshot_path, "w") as f:
                json.dump(snapshot_data, f, indent=2)
            
            logger.info(f"     ✅ Zeus: Saved {len(forecast.timeseries)} points")
        
        except Exception as e:
            logger.warning(f"     ⚠️  Zeus fetch failed: {e}")
    
    def _collect_polymarket(self, city: str, event_day: date, cycle_time: datetime):
        """Collect Polymarket pricing snapshot."""
        try:
            # Get brackets
            brackets = self.discovery.list_temp_brackets(
                city=city,
                date_local=event_day,
                save_snapshot=False,
            )
            
            if not brackets:
                logger.debug(f"     No brackets available")
                return
            
            # Get prices
            prices = []
            for bracket in brackets:
                try:
                    p_mkt = self.pricing.midprob(bracket, save_snapshot=False)
                    prices.append(p_mkt)
                except Exception:
                    prices.append(None)
            
            # Save snapshot
            timestamp = cycle_time.strftime("%Y-%m-%d_%H-%M-%S")
            poly_dir = self.base_dir / "polymarket" / city.replace(" ", "_") / event_day.isoformat()
            poly_dir.mkdir(parents=True, exist_ok=True)
            
            snapshot_path = poly_dir / f"{timestamp}.json"
            
            snapshot_data = {
                "fetch_time_utc": cycle_time.isoformat(),
                "event_day": event_day.isoformat(),
                "city": city,
                "markets": [
                    {
                        "market_id": bracket.market_id,
                        "bracket": bracket.name,
                        "lower_f": bracket.lower_F,
                        "upper_f": bracket.upper_F,
                        "mid_price": price,
                        "closed": bracket.closed,
                    }
                    for bracket, price in zip(brackets, prices)
                ],
            }
            
            with open(snapshot_path, "w") as f:
                json.dump(snapshot_data, f, indent=2)
            
            valid_prices = sum(1 for p in prices if p is not None)
            logger.info(f"     ✅ Polymarket: Saved {valid_prices}/{len(brackets)} prices")
        
        except Exception as e:
            logger.warning(f"     ⚠️  Polymarket fetch failed: {e}")
    
    def _collect_metar(self, station, event_day: date):
        """Collect METAR observations (only NEW ones)."""
        try:
            # Fetch observations
            observations = self.metar.get_observations(
                station_code=station.station_code,
                event_date=event_day,
                hours=24,
                save_snapshot=False,
            )
            
            if not observations:
                return
            
            # Save only NEW observations
            metar_dir = self.base_dir / "metar" / station.station_code / event_day.isoformat()
            metar_dir.mkdir(parents=True, exist_ok=True)
            
            # Load existing observation times
            existing_times = self._load_existing_metar_times(metar_dir)
            
            new_count = 0
            
            for obs in observations:
                obs_key = (station.station_code, obs.time.isoformat())
                
                # Skip if already saved
                if obs_key in self._saved_metar_obs or obs.time.isoformat() in existing_times:
                    continue
                
                # Save snapshot
                obs_time_str = obs.time.strftime("%Y-%m-%d_%H-%M-%S")
                snapshot_path = metar_dir / f"{obs_time_str}.json"
                
                if snapshot_path.exists():
                    self._saved_metar_obs[obs_key] = True
                    continue
                
                snapshot_data = {
                    "observation_time_utc": obs.time.isoformat(),
                    "fetch_time_utc": datetime.now(ZoneInfo("UTC")).isoformat(),
                    "station_code": obs.station_code,
                    "event_day": event_day.isoformat(),
                    "temp_C": obs.temp_C,
                    "temp_F": obs.temp_F,
                    "dewpoint_C": obs.dewpoint_C,
                    "wind_dir": obs.wind_dir,
                    "wind_speed": obs.wind_speed,
                    "raw": obs.raw,
                }
                
                with open(snapshot_path, "w") as f:
                    json.dump(snapshot_data, f, indent=2)
                
                self._saved_metar_obs[obs_key] = True
                existing_times.add(obs.time.isoformat())
                new_count += 1
            
            if new_count > 0:
                logger.info(f"     ✅ METAR: Saved {new_count} new observation(s)")
        
        except Exception as e:
            logger.warning(f"     ⚠️  METAR fetch failed: {e}")
    
    def _load_existing_metar_times(self, metar_dir: Path) -> set[str]:
        """Load existing METAR observation times from disk."""
        existing_times = set()
        
        if not metar_dir.exists():
            return existing_times
        
        for snapshot_file in metar_dir.glob("*.json"):
            try:
                with open(snapshot_file) as f:
                    data = json.load(f)
                    obs_time = data.get("observation_time_utc")
                    if obs_time:
                        existing_times.add(obs_time)
            except (json.JSONDecodeError, KeyError, IOError):
                continue
        
        return existing_times
```

### Step 7: Create Main Entry Point

**File: `run_snapshotter.py`**
```python
#!/usr/bin/env python3
"""Main entry point for Hermes Snapshotter."""

from snapshotter.collector import DataCollector

if __name__ == "__main__":
    collector = DataCollector()
    collector.run()
```

### Step 8: Create Data Files

**File: `data/registry/stations.csv`**
```csv
city,station_name,station_code,lat,lon,noaa_station,venue_hint,time_zone
London,London City Airport,EGLC,51.505,0.05,UKMO,Polymarket London,Europe/London
New York (Airport),LaGuardia Airport,KLGA,40.7769,-73.8740,KOKX,Polymarket NYC,America/New_York
```

### Step 9: Create Configuration Files

**File: `.env.sample`**
```bash
# Zeus API
ZEUS_API_BASE=https://api.zeussubnet.com
ZEUS_API_KEY=your_zeus_api_key_here

# Polymarket API (no key needed)
POLY_GAMMA_BASE=https://gamma-api.polymarket.com
POLY_CLOB_BASE=https://clob.polymarket.com

# METAR API (no key needed)
METAR_API_BASE=https://aviationweather.gov/api/data/metar
METAR_USER_AGENT=HermesSnapshotter/1.0

# Snapshotter Configuration
COLLECTION_INTERVAL=900
LOOKAHEAD_DAYS=2

# Logging
LOG_LEVEL=INFO
```

**File: `README.md`**
```markdown
# Hermes Snapshotter

Lightweight data collection daemon for trading system development.

## Purpose

Collects valuable historical data (Zeus forecasts, Polymarket prices, METAR observations) continuously for trading system development and backtesting.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment:
   ```bash
   cp .env.sample .env
   # Edit .env with your API keys
   ```

3. Run:
   ```bash
   python run_snapshotter.py
   ```

## Configuration

- `COLLECTION_INTERVAL`: Seconds between collection cycles (default: 900 = 15 min)
- `LOOKAHEAD_DAYS`: Days ahead to check for markets (default: 2)
- `ZEUS_API_KEY`: Your Zeus API key (required)

## Data Storage

Snapshots saved to: `data/snapshots/dynamic/`
- `zeus/{station}/{date}/{timestamp}.json`
- `polymarket/{city}/{date}/{timestamp}.json`
- `metar/{station}/{date}/{observation_time}.json`

## Usage

Run continuously:
```bash
python run_snapshotter.py
```

Run in background:
```bash
nohup python run_snapshotter.py > snapshotter.log 2>&1 &
```

## Expected Data Volume

- Daily: ~1-2 MB
- Monthly: ~30-60 MB
- Zeus: ~384 snapshots/day
- Polymarket: ~192-384 snapshots/day
- METAR: ~24-48 snapshots/day (deduplicated)
```

---

## 🚀 Quick Start

1. **Create project structure** (see Step 1)
2. **Create all files** (copy code from Steps 2-9 above)
3. **Install dependencies**: `pip install -r requirements.txt`
4. **Configure**: Copy `.env.sample` to `.env` and add your Zeus API key
5. **Run**: `python run_snapshotter.py`

---

## ✅ Success Criteria

- [ ] All files created with code from specification
- [ ] Dependencies installed
- [ ] `.env` configured with API keys
- [ ] Can run `python run_snapshotter.py` without errors
- [ ] Zeus snapshots being saved
- [ ] Polymarket snapshots being saved
- [ ] METAR snapshots being saved (deduplicated)
- [ ] Runs continuously without errors

---

## 📝 Notes

- **Standalone**: This project has no dependencies on other projects
- **Self-contained**: All code is included in this specification
- **Simple**: Focused only on data collection
- **Robust**: Includes retry logic, error handling, and deduplication

---

**Author**: Hermes Development Team  
**Date**: November 13, 2025  
**Status**: Complete Standalone Specification
