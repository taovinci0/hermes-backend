"""Polymarket market discovery - finds temperature brackets.

Stage 4 implementation.
"""

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
from .schemas import GammaEvent, GammaMarket


class PolymarketAPIError(Exception):
    """Exception raised for Polymarket API errors."""
    pass


class PolyDiscovery:
    """Discovers daily temperature markets on Polymarket."""

    def __init__(self, gamma_base: Optional[str] = None):
        """Initialize Polymarket discovery agent.

        Args:
            gamma_base: Gamma API base URL (defaults to config)
        """
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
        """Call Gamma API with retry logic.

        Args:
            endpoint: API endpoint (e.g., '/events', '/markets')
            params: Optional query parameters

        Returns:
            JSON response from Gamma API

        Raises:
            PolymarketAPIError: If API call fails
        """
        url = f"{self.gamma_base}{endpoint}"
        
        logger.debug(f"Calling Gamma API: {endpoint} with params {params}")
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logger.debug(f"Gamma API call successful")
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

    def _save_snapshot(
        self,
        data: dict,
        snapshot_type: str,
        identifier: str,
    ) -> Path:
        """Save Gamma API response to disk.

        Args:
            data: Raw JSON response
            snapshot_type: Type of data ('events', 'markets', etc.)
            identifier: Unique identifier for filename

        Returns:
            Path to saved snapshot
        """
        snapshot_dir = self.snapshot_dir / snapshot_type
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        snapshot_path = snapshot_dir / f"{identifier}.json"
        
        with open(snapshot_path, "w") as f:
            json.dump(data, f, indent=2)
        
        logger.debug(f"Saved Gamma snapshot to {snapshot_path}")
        return snapshot_path
    
    def get_event_by_slug(self, slug: str, save_snapshot: bool = True) -> Optional[dict]:
        """Fetch a Polymarket event (and its markets) by slug.
        
        Args:
            slug: Event slug (e.g., "highest-temperature-in-london-on-november-11")
            save_snapshot: Whether to save API response
        
        Returns:
            Event data with markets, or None if not found
        
        Raises:
            PolymarketAPIError: If API call fails (except 404)
        """
        logger.debug(f"Fetching event by slug: {slug}")
        
        try:
            # Call Gamma API: /events/slug/{slug}
            endpoint = f"/events/slug/{slug}"
            data = self._call_gamma_api(endpoint)
            
            # Handle both array and single object responses
            if isinstance(data, list):
                if not data:
                    logger.debug(f"Empty response for event: {slug}")
                    return None
                event = data[0]  # Take first event from array
            else:
                event = data
            
            if save_snapshot:
                # Save event snapshot
                identifier = slug.replace("/", "_")
                self._save_snapshot(event, "events", identifier)
            
            logger.info(f"Found event: {slug}")
            return event
            
        except PolymarketAPIError as e:
            if "404" in str(e) or "Not Found" in str(e):
                logger.debug(f"Event not found: {slug}")
                return None
            raise
    
    def _generate_event_slugs(self, city: str, date_local: date) -> List[str]:
        """Generate possible event slugs for a city/date combination.
        
        Args:
            city: City name (e.g., "London", "New York (Airport)")
            date_local: Local date
        
        Returns:
            List of possible slug patterns to try
        """
        # Clean city name for slug
        city_clean = city.lower().replace(" (airport)", "").replace(" (city)", "")
        city_slug = city_clean.replace(" ", "-")
        
        # Format date parts
        month = date_local.strftime("%B").lower()  # "november"
        day = date_local.day  # 11
        
        # Try multiple slug patterns
        patterns = [
            f"highest-temperature-in-{city_slug}-on-{month}-{day}",
            f"temperature-in-{city_slug}-on-{month}-{day}",
            f"high-temperature-in-{city_slug}-on-{month}-{day}",
            f"{city_slug}-temperature-on-{month}-{day}",
        ]
        
        # NYC special cases
        if "new york" in city_clean or "nyc" in city_clean:
            patterns.extend([
                f"highest-temperature-in-nyc-on-{month}-{day}",
                f"temperature-in-nyc-on-{month}-{day}",
                f"high-temperature-in-nyc-on-{month}-{day}",
            ])
        
        return patterns

    def _parse_bracket_from_name(self, name: str) -> Optional[tuple[int, int]]:
        """Parse temperature bracket from market name.

        Supports formats like:
        - "59-60°F"
        - "59–60°F" (en dash)
        - "59 - 60°F"
        - "59 to 60°F"

        Args:
            name: Market question or outcome name

        Returns:
            Tuple of (lower_F, upper_F) or None if not parseable
        """
        # Try various bracket patterns
        patterns = [
            r'(\d+)\s*[-–—]\s*(\d+)\s*°?F',  # 59-60°F or 59–60°F
            r'(\d+)\s+to\s+(\d+)\s*°?F',     # 59 to 60°F
            r'(\d+)\s*-\s*(\d+)\s*degrees',   # 59 - 60 degrees
        ]
        
        for pattern in patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                lower = int(match.group(1))
                upper = int(match.group(2))
                
                # Validate bounds make sense
                if lower < upper and 0 < lower < 150 and 0 < upper < 150:
                    return (lower, upper)
        
        return None
    
    def _parse_bracket_from_market(self, market_data: dict) -> Optional[MarketBracket]:
        """Parse a MarketBracket from Polymarket market object.
        
        Args:
            market_data: Market dict from Gamma API
        
        Returns:
            MarketBracket or None if not parseable
        """
        try:
            # Get market question
            question = market_data.get("question", "")
            
            # Extract both types of IDs:
            # - market_id: for Gamma API (resolution, market info)
            # - clob_token_id: for CLOB API (pricing, order book)
            market_id = market_data.get("id")
            
            clob_ids = market_data.get("clobTokenIds")
            clob_token_id = None
            if isinstance(clob_ids, list) and clob_ids:
                clob_token_id = clob_ids[0]  # First token ID (YES outcome)
            elif isinstance(clob_ids, str):
                clob_token_id = clob_ids.split(",")[0].strip().strip('"[]')
            
            if not question or not market_id:
                logger.debug(f"Market missing question or ID: {market_data.get('id', 'unknown')}")
                return None
            
            # Parse bracket from question
            bracket_tuple = self._parse_bracket_from_name(question)
            if not bracket_tuple:
                logger.debug(f"Could not parse bracket from: {question}")
                return None
            
            lower_F, upper_F = bracket_tuple
            
            # Check if market is closed
            closed = market_data.get("closed", False)
            
            return MarketBracket(
                name=f"{lower_F}-{upper_F}°F",
                lower_F=lower_F,
                upper_F=upper_F,
                market_id=market_id,  # For resolution
                token_id=clob_token_id,  # For pricing
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
        """List temperature brackets for a city and date.

        Queries Gamma API /events or /markets by slug/tag.
        Parses bracket names like "59-60°F" into MarketBracket objects.

        Args:
            city: City name (e.g., "London", "New York")
            date_local: Local date for the market
            save_snapshot: Whether to save API response

        Returns:
            List of MarketBracket with parsed bounds and market IDs

        Raises:
            PolymarketAPIError: If API call fails
            ValueError: If no markets found or parsing fails
        """
        logger.info(f"Discovering Polymarket temp brackets for {city} on {date_local}")
        
        # Generate possible event slugs
        slugs = self._generate_event_slugs(city, date_local)
        
        # Try each slug until we find an event
        event = None
        successful_slug = None
        
        for slug in slugs:
            logger.debug(f"Trying event slug: {slug}")
            event = self.get_event_by_slug(slug, save_snapshot=False)
            if event:
                successful_slug = slug
                break
        
        if not event:
            logger.warning(
                f"No event found for {city} on {date_local}. "
                f"Tried slugs: {', '.join(slugs[:3])}..."
            )
            return []
        
        # Save event snapshot with markets
        if save_snapshot:
            identifier = f"{city.replace(' ', '_')}_{date_local}"
            self._save_snapshot(event, "events", identifier)
        
        # Extract markets from event
        markets_data = event.get("markets", [])
        
        if not markets_data:
            logger.warning(f"Event {successful_slug} has no markets")
            return []
        
        logger.info(
            f"Found event '{successful_slug}' with {len(markets_data)} markets"
        )
        
        # Parse brackets from markets
        brackets = []
        for market_data in markets_data:
            bracket = self._parse_bracket_from_market(market_data)
            if bracket:
                brackets.append(bracket)
        
        if brackets:
            # Sort brackets by lower bound
            brackets.sort(key=lambda b: b.lower_F)
            logger.info(
                f"✅ Parsed {len(brackets)} temperature brackets for {city}, "
                f"range: [{brackets[0].lower_F}-{brackets[-1].upper_F}°F)"
            )
        else:
            logger.warning(f"No valid temperature brackets found in event markets")
        
        return brackets

