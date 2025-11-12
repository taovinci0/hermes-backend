"""Edge calculation and Kelly position sizing.

Stage 5 implementation.
"""

from typing import List, Optional

from core.types import BracketProb, EdgeDecision
from core.config import config
from core.logger import logger
from venues.polymarket.schemas import MarketDepth


class Sizer:
    """Computes edge and sizes positions using Kelly criterion."""

    def __init__(
        self,
        edge_min: float = config.trading.edge_min,
        fee_bp: int = config.trading.fee_bp,
        slippage_bp: int = config.trading.slippage_bp,
        kelly_cap: float = config.trading.kelly_cap,
        per_market_cap: float = config.trading.per_market_cap,
        liquidity_min_usd: float = config.trading.liquidity_min_usd,
    ):
        """Initialize position sizer.

        Args:
            edge_min: Minimum edge to trade (0.05 = 5%)
            fee_bp: Effective fees in basis points (50 = 0.50%)
            slippage_bp: Assumed slippage in basis points
            kelly_cap: Max Kelly fraction per decision (0.10 = 10%)
            per_market_cap: Per-market position limit in USD
            liquidity_min_usd: Minimum market liquidity required
        """
        self.edge_min = edge_min
        self.fee_bp = fee_bp
        self.slippage_bp = slippage_bp
        self.kelly_cap = kelly_cap
        self.per_market_cap = per_market_cap
        self.liquidity_min_usd = liquidity_min_usd

    def compute_edge(
        self,
        p_zeus: float,
        p_mkt: float,
    ) -> float:
        """Compute expected edge after costs.

        Edge = (p_zeus - p_mkt) - fees - slippage

        Args:
            p_zeus: Zeus-derived probability (0-1)
            p_mkt: Market-implied probability (0-1)

        Returns:
            Edge as a decimal (0.05 = 5% edge)
        """
        # Convert basis points to decimal
        fee_decimal = self.fee_bp / 10000.0
        slip_decimal = self.slippage_bp / 10000.0
        
        # Calculate edge
        edge = (p_zeus - p_mkt) - fee_decimal - slip_decimal
        
        logger.debug(
            f"Edge: p_zeus={p_zeus:.4f}, p_mkt={p_mkt:.4f}, "
            f"fees={fee_decimal:.4f}, slip={slip_decimal:.4f}, "
            f"edge={edge:.4f}"
        )
        
        return edge

    def compute_kelly_fraction(
        self,
        p_zeus: float,
        price: float,
    ) -> float:
        """Compute Kelly fraction for binary outcome.

        For a binary bet with payoff b = (1/price - 1):
        f* = (b*p - q) / b
        where p = p_zeus, q = 1 - p_zeus

        Args:
            p_zeus: True probability (Zeus-derived)
            price: Market price (0-1)

        Returns:
            Kelly fraction (0-1), or 0 if negative
        """
        if price <= 0 or price >= 1:
            logger.warning(f"Invalid price {price}, returning 0 Kelly fraction")
            return 0.0
        
        # Payoff multiplier: b = (1/price - 1)
        # If you bet $1 at price 0.60, you get $1/0.60 = $1.67 if you win
        # Profit is $1.67 - $1 = $0.67, so b = 0.67
        b = (1.0 / price) - 1.0
        
        # Kelly fraction: f* = (b*p - q) / b
        # where p = p_zeus (our edge probability)
        # and q = 1 - p_zeus
        p = p_zeus
        q = 1.0 - p_zeus
        
        f_kelly = (b * p - q) / b if b > 0 else 0.0
        
        # Kelly can be negative if we have negative edge
        # In that case, we shouldn't bet
        if f_kelly < 0:
            f_kelly = 0.0
        
        logger.debug(
            f"Kelly: p={p:.4f}, price={price:.4f}, b={b:.4f}, "
            f"f*={f_kelly:.4f}"
        )
        
        return f_kelly

    def _apply_caps(
        self,
        kelly_size: float,
        bankroll: float,
        liquidity_available: Optional[float] = None,
    ) -> float:
        """Apply position size caps.

        Args:
            kelly_size: Raw Kelly-suggested size in USD
            bankroll: Available bankroll
            liquidity_available: Available market liquidity (optional)

        Returns:
            Capped position size in USD
        """
        # Start with Kelly size
        size = kelly_size
        reason_parts = []
        
        # Cap 1: Kelly cap (e.g., 10% of bankroll)
        kelly_capped = bankroll * self.kelly_cap
        if size > kelly_capped:
            size = kelly_capped
            reason_parts.append(f"kelly_cap({self.kelly_cap*100:.0f}%)")
        
        # Cap 2: Per-market cap
        if size > self.per_market_cap:
            size = self.per_market_cap
            reason_parts.append(f"per_market_cap(${self.per_market_cap})")
        
        # Cap 3: Available liquidity
        if liquidity_available is not None and size > liquidity_available:
            size = liquidity_available
            reason_parts.append(f"liquidity(${liquidity_available:.0f})")
        
        if reason_parts:
            logger.debug(f"Applied caps: {', '.join(reason_parts)}")
        
        return size

    def decide(
        self,
        probs: List[BracketProb],
        bankroll_usd: float,
        depth_data: Optional[dict] = None,
    ) -> List[EdgeDecision]:
        """Compute edge and size positions for bracket probabilities.

        For each bracket:
        1. Calculate edge = (p_zeus - p_mkt) - fees - slippage
        2. If edge < edge_min, skip
        3. Compute Kelly fraction: f* = (b*p - q)/b where b = (1/price - 1)
        4. Apply caps: kelly_cap, per_market_cap, liquidity constraints
        5. Return EdgeDecision with sized order

        Args:
            probs: List of BracketProb with Zeus and market probabilities
            bankroll_usd: Available bankroll for sizing
            depth_data: Optional dict mapping market_id -> MarketDepth

        Returns:
            List of EdgeDecision for brackets with positive edge

        Raises:
            ValueError: If probs is empty or missing required data
        """
        if not probs:
            raise ValueError("No bracket probabilities provided")
        
        logger.info(
            f"Sizing positions: {len(probs)} brackets, "
            f"bankroll=${bankroll_usd:.2f}"
        )
        
        decisions = []
        
        for bp in probs:
            # Skip if missing market probability
            if bp.p_mkt is None:
                logger.debug(
                    f"Skipping {bp.bracket.name}: no market probability"
                )
                continue
            
            # Step 1: Compute edge
            edge = self.compute_edge(bp.p_zeus, bp.p_mkt)
            
            # Step 2: Filter by minimum edge
            if edge < self.edge_min:
                logger.debug(
                    f"Skipping {bp.bracket.name}: edge {edge:.4f} < min {self.edge_min}"
                )
                continue
            
            # Step 3: Compute Kelly fraction
            # Use p_mkt as price (it's the market-implied probability)
            f_kelly = self.compute_kelly_fraction(bp.p_zeus, bp.p_mkt)
            
            if f_kelly <= 0:
                logger.debug(
                    f"Skipping {bp.bracket.name}: Kelly fraction {f_kelly:.4f} <= 0"
                )
                continue
            
            # Step 4: Compute raw Kelly size
            kelly_size_usd = f_kelly * bankroll_usd
            
            # Step 5: Get liquidity if available
            liquidity_available = None
            if depth_data and bp.bracket.market_id in depth_data:
                depth = depth_data[bp.bracket.market_id]
                # Use bid depth as liquidity proxy (we'd be buying)
                liquidity_available = depth.bid_depth_usd
                
                # Filter by minimum liquidity
                if liquidity_available < self.liquidity_min_usd:
                    logger.debug(
                        f"Skipping {bp.bracket.name}: "
                        f"liquidity ${liquidity_available:.2f} < min ${self.liquidity_min_usd}"
                    )
                    continue
            
            # Step 6: Apply caps
            final_size = self._apply_caps(
                kelly_size_usd,
                bankroll_usd,
                liquidity_available
            )
            
            # Create decision
            reason_parts = []
            if edge >= self.edge_min * 2:
                reason_parts.append("strong_edge")
            if f_kelly >= self.kelly_cap:
                reason_parts.append("kelly_capped")
            if liquidity_available and liquidity_available < kelly_size_usd:
                reason_parts.append("liquidity_limited")
            
            reason = ", ".join(reason_parts) if reason_parts else "standard"
            
            decision = EdgeDecision(
                bracket=bp.bracket,
                edge=edge,
                f_kelly=f_kelly,
                size_usd=final_size,
                reason=reason,
            )
            
            decisions.append(decision)
            
            logger.info(
                f"✅ [{bp.bracket.lower_F}-{bp.bracket.upper_F}°F): "
                f"edge={edge:.4f} ({edge*100:.2f}%), "
                f"f*={f_kelly:.4f}, "
                f"size=${final_size:.2f} ({reason})"
            )
        
        logger.info(
            f"Generated {len(decisions)} trade decisions "
            f"from {len(probs)} brackets"
        )
        
        return decisions

