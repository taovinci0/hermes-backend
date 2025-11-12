"""Polymarket execution - paper and live order placement.

Stage 6 (paper) and Stage 8 (live) implementation.
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from core.types import EdgeDecision
from core.config import config, PROJECT_ROOT
from core.logger import logger


class Broker:
    """Base broker interface."""

    def place(self, decisions: List[EdgeDecision]) -> None:
        """Place orders for edge decisions.

        Args:
            decisions: List of sized EdgeDecision objects
        """
        raise NotImplementedError("Subclasses must implement place()")


class PaperBroker(Broker):
    """Paper trading broker - records intended orders without execution."""

    def __init__(self, trades_dir: Optional[Path] = None):
        """Initialize paper broker.

        Args:
            trades_dir: Directory for trade logs (defaults to data/trades/)
        """
        if trades_dir is None:
            trades_dir = PROJECT_ROOT / "data" / "trades"
        
        self.trades_dir = trades_dir
        self.trades_placed = []

    def place(self, decisions: List[EdgeDecision]) -> Path:
        """Record paper trades to CSV.

        Args:
            decisions: List of sized EdgeDecision objects

        Returns:
            Path to the CSV file where trades were recorded

        Raises:
            ValueError: If decisions list is empty
        """
        if not decisions:
            logger.warning("No decisions to place")
            return None
        
        logger.info(f"📄 Placing {len(decisions)} paper trades")
        
        # Create date-based directory
        today = datetime.now().strftime("%Y-%m-%d")
        date_dir = self.trades_dir / today
        date_dir.mkdir(parents=True, exist_ok=True)
        
        # CSV file path
        csv_path = date_dir / "paper_trades.csv"
        
        # Determine if we need to write header
        file_exists = csv_path.exists()
        
        # Open CSV in append mode
        with open(csv_path, "a", newline="") as f:
            fieldnames = [
                "timestamp",
                "station_code",
                "bracket_name",
                "bracket_lower_f",
                "bracket_upper_f",
                "market_id",
                "edge",
                "edge_pct",
                "f_kelly",
                "size_usd",
                "p_zeus",
                "p_mkt",
                "sigma_z",
                "reason",
            ]
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            # Write header if new file
            if not file_exists:
                writer.writeheader()
            
            # Write each decision
            for decision in decisions:
                # Extract station code from bracket if available
                station_code = getattr(decision.bracket, 'station_code', 'UNKNOWN')
                
                row = {
                    "timestamp": decision.timestamp.isoformat(),
                    "station_code": station_code,
                    "bracket_name": decision.bracket.name,
                    "bracket_lower_f": decision.bracket.lower_F,
                    "bracket_upper_f": decision.bracket.upper_F,
                    "market_id": decision.bracket.market_id or "",
                    "edge": f"{decision.edge:.6f}",
                    "edge_pct": f"{decision.edge * 100:.4f}",
                    "f_kelly": f"{decision.f_kelly:.6f}",
                    "size_usd": f"{decision.size_usd:.2f}",
                    "p_zeus": "",  # Will be filled if we track original BracketProb
                    "p_mkt": "",   # Will be filled if we track original BracketProb
                    "sigma_z": "",
                    "reason": decision.reason,
                }
                
                writer.writerow(row)
                self.trades_placed.append(decision)
                
                logger.info(
                    f"  📝 [{decision.bracket.lower_F}-{decision.bracket.upper_F}°F): "
                    f"${decision.size_usd:.2f} @ edge={decision.edge*100:.2f}%"
                )
        
        logger.info(f"✅ Recorded {len(decisions)} paper trades to {csv_path}")
        
        return csv_path

    def get_trades(self) -> List[EdgeDecision]:
        """Get list of trades placed in this session.

        Returns:
            List of EdgeDecision objects that were placed
        """
        return self.trades_placed.copy()


class LiveBroker(Broker):
    """Live trading broker - executes real orders on Polymarket."""

    def __init__(self, clob_base: Optional[str] = None):
        """Initialize live broker.

        Args:
            clob_base: CLOB API base URL (defaults to config)
        """
        self.clob_base = clob_base or config.polymarket.clob_base

    def place(self, decisions: List[EdgeDecision]) -> None:
        """Execute live orders on Polymarket.

        Args:
            decisions: List of sized EdgeDecision objects

        Raises:
            NotImplementedError: Stage 8 not yet implemented
        """
        raise NotImplementedError(
            "Stage 8 (LiveBroker) not yet implemented. "
            "Will use py-clob-client or direct API calls for authenticated orders."
        )

