"""Polymarket resolution - fetch winning outcomes for resolved markets.

Stage 7A implementation.
"""

import json
from pathlib import Path
from typing import Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config import config, PROJECT_ROOT
from core.logger import logger


class PolymarketResolutionError(Exception):
    """Exception raised for Polymarket resolution errors."""
    pass


class PolyResolution:
    """Fetch winning outcomes for resolved Polymarket markets."""
    
    def __init__(self, gamma_base: Optional[str] = None):
        """Initialize resolution fetcher.
        
        Args:
            gamma_base: Gamma API base URL (defaults to config)
        """
        self.gamma_base = gamma_base or config.polymarket.gamma_base
        self.snapshot_dir = PROJECT_ROOT / "data" / "snapshots" / "polymarket" / "resolution"
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def _call_gamma_api(self, market_id: str) -> dict:
        """Call Gamma API to fetch market details.
        
        Args:
            market_id: Market token ID
        
        Returns:
            JSON response from Gamma API
        
        Raises:
            PolymarketResolutionError: If API call fails
        """
        url = f"{self.gamma_base}/markets"
        params = {"id": market_id}
        
        logger.debug(f"Calling Gamma API for market resolution: {market_id}")
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logger.debug(f"Gamma API call successful for {market_id}")
            return data
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"Gamma API HTTP error for {market_id}: {e}")
            raise PolymarketResolutionError(f"Gamma API HTTP error: {e}") from e
        except requests.exceptions.Timeout as e:
            logger.error(f"Gamma API timeout for {market_id}: {e}")
            raise PolymarketResolutionError(f"Gamma API timeout: {e}") from e
        except requests.exceptions.RequestException as e:
            logger.error(f"Gamma API request error for {market_id}: {e}")
            raise PolymarketResolutionError(f"Gamma API request error: {e}") from e
        except json.JSONDecodeError as e:
            logger.error(f"Gamma API JSON decode error for {market_id}: {e}")
            raise PolymarketResolutionError(f"Gamma API JSON decode error: {e}") from e
    
    def _save_snapshot(self, data: dict, market_id: str) -> Path:
        """Save resolution response to disk.
        
        Args:
            data: Raw JSON response
            market_id: Market token ID
        
        Returns:
            Path to saved snapshot
        """
        snapshot_path = self.snapshot_dir / f"{market_id}.json"
        
        with open(snapshot_path, "w") as f:
            json.dump(data, f, indent=2)
        
        logger.debug(f"Saved resolution snapshot to {snapshot_path}")
        return snapshot_path
    
    def get_winner(self, market_id: str, save_snapshot: bool = True) -> dict:
        """Get winning outcome for a resolved market.
        
        Args:
            market_id: Market token ID
            save_snapshot: Whether to save API response
        
        Returns:
            Dictionary with:
            - resolved: bool (whether market is resolved)
            - winner: str or None (winning outcome/bracket name)
            - raw: dict (raw API response)
        
        Raises:
            PolymarketResolutionError: If API call fails
        """
        if not market_id:
            logger.warning("No market_id provided for resolution")
            return {"resolved": False, "winner": None, "raw": {}}
        
        logger.debug(f"Fetching resolution for market {market_id}")
        
        try:
            # Call Gamma API
            data = self._call_gamma_api(market_id)
            
            if save_snapshot:
                self._save_snapshot(data, market_id)
            
            # Parse response - handle both single market and array responses
            if isinstance(data, list):
                if not data:
                    logger.warning(f"Empty response for market {market_id}")
                    return {"resolved": False, "winner": None, "raw": data}
                market = data[0]
            elif isinstance(data, dict) and "markets" in data:
                markets = data.get("markets", [])
                if not markets:
                    logger.warning(f"No markets in response for {market_id}")
                    return {"resolved": False, "winner": None, "raw": data}
                market = markets[0]
            else:
                market = data
            
            # Check if market is resolved
            resolved = bool(
                market.get("resolved") 
                or market.get("closed")
                or market.get("status") in {"resolved", "closed"}
            )
            
            if not resolved:
                logger.debug(f"Market {market_id} not yet resolved")
                return {"resolved": False, "winner": None, "raw": market}
            
            # Extract winning outcome
            winner = None
            
            # Try multiple field names for winning outcome
            winner = (
                market.get("winning_outcome")
                or market.get("winningOutcome")
                or market.get("resolvedOutcome")
                or market.get("outcome")
            )
            
            # If not found in top level, check outcomes array
            if not winner and "outcomes" in market:
                for outcome in market.get("outcomes", []):
                    if (
                        outcome.get("winner")
                        or outcome.get("isWinner")
                        or str(outcome.get("payout")) == "1"
                        or str(outcome.get("payout")) == "1.0"
                    ):
                        winner = outcome.get("name") or outcome.get("title")
                        break
            
            # Clean up winner string (remove °F, extra spaces)
            if winner:
                winner = str(winner).replace("°F", "").replace("°", "").strip()
            
            logger.info(
                f"Market {market_id}: "
                f"resolved={resolved}, winner={winner or 'unknown'}"
            )
            
            return {
                "resolved": resolved,
                "winner": winner,
                "raw": market
            }
            
        except Exception as e:
            logger.error(f"Failed to get resolution for {market_id}: {e}")
            raise

