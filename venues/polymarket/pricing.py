"""Polymarket pricing - reads market-implied probabilities.

Stage 4 implementation.
"""

import json
from pathlib import Path
from typing import Dict, Optional, List

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from core.types import MarketBracket
from core.config import config, PROJECT_ROOT
from core.logger import logger
from .schemas import CLOBOrderBook, CLOBMidpoint, MarketDepth, PriceHistory


class PolymarketPricingError(Exception):
    """Exception raised for Polymarket pricing errors."""
    pass


class PolyPricing:
    """Reads prices and liquidity from Polymarket CLOB."""

    def __init__(self, clob_base: Optional[str] = None):
        """Initialize Polymarket pricing agent.

        Args:
            clob_base: CLOB API base URL (defaults to config)
        """
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
        """Call CLOB API with retry logic.

        Args:
            endpoint: API endpoint (e.g., '/midpoint', '/book')
            params: Optional query parameters

        Returns:
            JSON response from CLOB API

        Raises:
            PolymarketPricingError: If API call fails
        """
        url = f"{self.clob_base}{endpoint}"
        
        logger.debug(f"Calling CLOB API: {endpoint} with params {params}")
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logger.debug(f"CLOB API call successful")
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

    def _save_snapshot(
        self,
        data: dict,
        snapshot_type: str,
        identifier: str,
    ) -> Path:
        """Save CLOB API response to disk.

        Args:
            data: Raw JSON response
            snapshot_type: Type of data ('midpoint', 'book', etc.)
            identifier: Unique identifier for filename

        Returns:
            Path to saved snapshot
        """
        snapshot_dir = self.snapshot_dir / snapshot_type
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        snapshot_path = snapshot_dir / f"{identifier}.json"
        
        with open(snapshot_path, "w") as f:
            json.dump(data, f, indent=2)
        
        logger.debug(f"Saved CLOB snapshot to {snapshot_path}")
        return snapshot_path

    def midprob(
        self,
        bracket: MarketBracket,
        save_snapshot: bool = False,
    ) -> float:
        """Get market-implied probability from midprice.

        Args:
            bracket: Market bracket with market_id
            save_snapshot: Whether to save API response

        Returns:
            Probability (0-1) from midprice / 1.0

        Raises:
            PolymarketPricingError: If API call fails
            ValueError: If bracket has no market_id or invalid price
        """
        if not bracket.market_id:
            raise ValueError(f"Bracket {bracket.name} has no market_id")
        
        logger.debug(f"Fetching midprice for {bracket.name} (market_id: {bracket.market_id})")
        
        try:
            # Call CLOB /midpoint endpoint
            # Use token_id parameter (CLOB token, not market ID)
            token_id = bracket.token_id or bracket.market_id  # Fallback to market_id if no token_id
            
            data = self._call_clob_api(
                "/midpoint",
                params={"token_id": token_id}
            )
            
            if save_snapshot:
                self._save_snapshot(data, "midpoint", bracket.market_id)
            
            # Parse response
            if isinstance(data, dict):
                midpoint_data = data
            else:
                raise ValueError(f"Unexpected CLOB response format: {type(data)}")
            
            # Extract midprice
            mid = midpoint_data.get("mid")
            
            if mid is None:
                raise ValueError(f"No midprice in response for {bracket.name}")
            
            # Convert to probability (midprice is already 0-1)
            prob = float(mid)
            
            # Validate range
            if not 0.0 <= prob <= 1.0:
                logger.warning(f"Midprice {prob} out of range [0,1], clamping")
                prob = max(0.0, min(1.0, prob))
            
            logger.debug(f"Midprice for {bracket.name}: {prob:.4f}")
            
            return prob
            
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Failed to parse CLOB midprice: {e}")
            raise ValueError(f"Failed to parse CLOB midprice: {e}") from e

    def depth(
        self,
        bracket: MarketBracket,
        save_snapshot: bool = False,
    ) -> MarketDepth:
        """Get order book depth for liquidity estimation.

        Args:
            bracket: Market bracket with market_id
            save_snapshot: Whether to save API response

        Returns:
            MarketDepth with liquidity info

        Raises:
            PolymarketPricingError: If API call fails
            ValueError: If bracket has no market_id
        """
        if not bracket.market_id:
            raise ValueError(f"Bracket {bracket.name} has no market_id")
        
        logger.debug(f"Fetching order book for {bracket.name}")
        
        try:
            # Call CLOB /book endpoint
            data = self._call_clob_api(
                "/book",
                params={"token_id": bracket.market_id}
            )
            
            if save_snapshot:
                self._save_snapshot(data, "book", bracket.market_id)
            
            # Parse order book
            book = CLOBOrderBook(**data)
            
            # Calculate depth in USD
            bid_depth = sum(
                float(bid.price) * float(bid.size)
                for bid in book.bids
            )
            
            ask_depth = sum(
                float(ask.price) * float(ask.size)
                for ask in book.asks
            )
            
            # Calculate spread
            if book.bids and book.asks:
                best_bid = max(float(bid.price) for bid in book.bids)
                best_ask = min(float(ask.price) for ask in book.asks)
                mid = (best_bid + best_ask) / 2.0
                spread_bps = ((best_ask - best_bid) / mid) * 10000 if mid > 0 else None
            else:
                best_bid = best_ask = mid = None
                spread_bps = None
            
            depth = MarketDepth(
                token_id=bracket.market_id,
                bid_depth_usd=bid_depth,
                ask_depth_usd=ask_depth,
                spread_bps=spread_bps,
                mid_price=mid,
            )
            
            logger.debug(
                f"Depth for {bracket.name}: "
                f"bid=${bid_depth:.2f}, ask=${ask_depth:.2f}, "
                f"spread={spread_bps:.1f}bps" if spread_bps else "no spread"
            )
            
            return depth
            
        except Exception as e:
            logger.error(f"Failed to get order book depth: {e}")
            raise

    def get_price_history(
        self,
        bracket: MarketBracket,
        interval: str = "1h",
        fidelity: int = 24,
    ) -> Optional[float]:
        """Get historical opening price for backtesting.

        Uses Gamma API /prices-history endpoint for closed markets.

        Args:
            bracket: Market bracket with market_id
            interval: Time interval ('1m', '5m', '1h', '1d')
            fidelity: Number of data points to return

        Returns:
            Opening price (0-1) or None if not available

        Raises:
            PolymarketPricingError: If API call fails
        """
        if not bracket.market_id:
            logger.warning(f"Bracket {bracket.name} has no market_id")
            return None
        
        logger.debug(f"Fetching price history for {bracket.name} (token_id: {bracket.market_id})")
        
        try:
            # Use Gamma API for historical prices (not CLOB)
            gamma_base = config.polymarket.gamma_base
            url = f"{gamma_base}/prices-history"
            
            params = {
                "market": bracket.market_id,
                "interval": interval,
                "fidelity": fidelity,
            }
            
            import requests
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Parse response - expecting array of price points
            if isinstance(data, list) and data:
                # Get first (earliest) price point as opening price
                first_point = data[0]
                price = first_point.get("p") or first_point.get("price")
                
                if price is not None:
                    opening_price = float(price)
                    logger.debug(
                        f"Historical opening price for {bracket.name}: {opening_price:.4f}"
                    )
                    return opening_price
            
            logger.warning(f"No price history data for {bracket.name}")
            return None
            
        except Exception as e:
            logger.warning(f"Failed to get price history for {bracket.name}: {e}")
            return None

