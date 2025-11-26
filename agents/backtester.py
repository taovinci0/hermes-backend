"""Backtester - validates strategy with historical data.

Stage 7 implementation.

Workflow:
1. For each date in range, fetch Zeus forecast (or use snapshot)
2. Discover Polymarket brackets
3. Get opening prices from price history
4. Run edge calculation with those prices
5. Determine what trades would have been made
6. Get closing prices to calculate realized P&L
7. Aggregate results and calculate metrics
"""

import csv
from dataclasses import dataclass
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Optional
from zoneinfo import ZoneInfo
import json

from core.config import PROJECT_ROOT
from core.logger import logger
from core.registry import StationRegistry
from core.types import BracketProb, EdgeDecision, MarketBracket
from agents.zeus_forecast import ZeusForecastAgent
from agents.prob_mapper import ProbabilityMapper
from agents.edge_and_sizing import Sizer
from venues.polymarket.discovery import PolyDiscovery
from venues.polymarket.pricing import PolyPricing
from venues.polymarket.resolution import PolyResolution
from core.feature_toggles import FeatureToggles


@dataclass
class BacktestTrade:
    """A single backtest trade result."""
    
    date: date
    station_code: str
    city: str
    bracket_name: str
    lower: Optional[int]
    upper: Optional[int]
    zeus_prob: float
    market_prob_open: float
    edge: float
    size_usd: float
    outcome: str  # 'win', 'loss', 'pending'
    realized_pnl: float
    market_prob_close: Optional[float] = None
    market_id: Optional[str] = None  # For resolution lookup
    winner_bracket: Optional[str] = None  # Actual winning bracket from Polymarket


@dataclass
class BacktestSummary:
    """Aggregated backtest results."""
    
    start_date: date
    end_date: date
    total_trades: int
    wins: int
    losses: int
    pending: int
    hit_rate: float
    total_risk: float
    total_pnl: float
    roi: float
    avg_edge: float
    avg_winning_pnl: float
    avg_losing_pnl: float
    largest_win: float
    largest_loss: float


class Backtester:
    """Validates trading strategy with historical data."""
    
    def __init__(
        self,
        bankroll_usd: float = 10000.0,
        edge_min: float = 0.05,
        fee_bp: int = 50,
        slippage_bp: int = 30,
        feature_toggles: Optional[FeatureToggles] = None,  # NEW
    ):
        """Initialize backtester.
        
        Args:
            bankroll_usd: Starting bankroll for simulation
            edge_min: Minimum edge threshold (default 5%)
            fee_bp: Fee in basis points (default 50bp)
            slippage_bp: Slippage in basis points (default 30bp)
            feature_toggles: Feature toggle configuration (if None, loads from file)
        """
        self.bankroll_usd = bankroll_usd
        self.edge_min = edge_min
        self.fee_bp = fee_bp
        self.slippage_bp = slippage_bp
        self.feature_toggles = feature_toggles or FeatureToggles.load()  # NEW
        
        # Initialize components
        self.registry = StationRegistry()
        self.zeus = ZeusForecastAgent()
        self.prob_mapper = ProbabilityMapper()
        self.sizer = Sizer(
            edge_min=edge_min,
            fee_bp=fee_bp,
            slippage_bp=slippage_bp,
        )
        self.discovery = PolyDiscovery()
        self.pricing = PolyPricing()
        self.resolution = PolyResolution()
        
        # Output directory
        self.runs_dir = PROJECT_ROOT / "data" / "runs" / "backtests"
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        
        # Price snapshots directory (from paper trading)
        self.price_snapshots_dir = PROJECT_ROOT / "data" / "price_snapshots"
    
    def run(
        self,
        start_date: date,
        end_date: date,
        stations: List[str],
    ) -> Path:
        """Run backtest across date range.
        
        Args:
            start_date: Start date for backtest (inclusive)
            end_date: End date for backtest (inclusive)
            stations: List of station codes to test
        
        Returns:
            Path to backtest results CSV
        """
        logger.info(
            f"Starting backtest: {start_date} to {end_date}, "
            f"stations={stations}"
        )
        
        # Collect all trades
        all_trades: List[BacktestTrade] = []
        
        # Iterate through each date
        current_date = start_date
        while current_date <= end_date:
            logger.info(f"Backtesting {current_date}...")
            
            for station_code in stations:
                station = self.registry.get(station_code)
                if not station:
                    logger.warning(f"Station {station_code} not found, skipping")
                    continue
                
                try:
                    # Run backtest for this date/station
                    trades = self._backtest_single_day(current_date, station_code)
                    all_trades.extend(trades)
                    
                except Exception as e:
                    logger.error(
                        f"Failed to backtest {station_code} on {current_date}: {e}"
                    )
            
            current_date += timedelta(days=1)
        
        # Save results
        output_path = self._save_results(start_date, end_date, all_trades)
        
        # For resolution-only backtests, also save a simple summary
        if all_trades and any(t.market_prob_open is None for t in all_trades):
            logger.info("Creating resolution-only summary...")
            summary_path = self._save_resolution_summary(all_trades, start_date, end_date)
            logger.info(f"📊 Resolution summary: {summary_path}")
        
        # Print summary
        summary = self._calculate_summary(start_date, end_date, all_trades)
        self._print_summary(summary)
        
        logger.info(f"Backtest complete! Results saved to {output_path}")
        
        return output_path
    
    def _backtest_single_day(
        self,
        trade_date: date,
        station_code: str,
    ) -> List[BacktestTrade]:
        """Backtest a single day for a single station.
        
        Args:
            trade_date: Date to backtest
            station_code: Station code
        
        Returns:
            List of BacktestTrade results for this day
        """
        station = self.registry.get(station_code)
        if not station:
            return []
        
        logger.debug(f"Backtesting {station.city} on {trade_date}")
        
        # 1. Get Zeus forecast for the full LOCAL day (midnight to midnight)
        # Convert local midnight to UTC, then fetch 24 hours from there
        # This ensures we get all 24 hours of the local date
        local_midnight = datetime.combine(
            trade_date,
            datetime.min.time()  # 00:00:00
        ).replace(tzinfo=ZoneInfo(station.time_zone))
        
        # Convert to UTC for Zeus API
        market_open = local_midnight.astimezone(ZoneInfo("UTC"))
        
        try:
            zeus_forecast = self.zeus.fetch(
                lat=station.lat,
                lon=station.lon,
                start_utc=market_open,
                hours=24,
                station_code=station_code,
            )
        except Exception as e:
            logger.error(f"Failed to fetch Zeus forecast: {e}")
            return []
        
        # 2. Discover Polymarket brackets
        try:
            brackets = self.discovery.list_temp_brackets(
                city=station.city,
                date_local=trade_date,
                save_snapshot=False,
            )
        except Exception as e:
            logger.error(f"Failed to discover brackets: {e}")
            return []
        
        if not brackets:
            logger.debug(f"No brackets found for {station.city} on {trade_date}")
            return []
        
        # 3. Map Zeus probabilities (with feature toggles)
        zeus_probs = self.prob_mapper.map_daily_high(
            zeus_forecast,
            brackets,
            station_code=station_code,  # NEW: Pass station code
            feature_toggles=self.feature_toggles,  # NEW: Pass feature toggles
        )
        
        # 4. Get opening prices (prioritize saved snapshots, then API, then resolution-only)
        market_probs_open = []
        
        # First, try to load saved prices from paper trading
        saved_prices = self._load_saved_prices(trade_date, station_code)
        
        for bracket in brackets:
            prob = None
            
            # Priority 1: Use saved prices from paper trading
            if saved_prices and bracket.market_id in saved_prices:
                prob = saved_prices[bracket.market_id]
                logger.debug(f"Using saved price for {bracket.name}: {prob:.4f}")
            
            # Priority 2: Try API (for closed markets use history, open markets use midpoint)
            elif bracket.closed:
                logger.debug(f"Market {bracket.name} is closed, trying price history")
                try:
                    prob = self.pricing.get_price_history(bracket)
                except Exception as e:
                    logger.debug(f"Price history unavailable for {bracket.name}: {e}")
            else:
                logger.debug(f"Market {bracket.name} is open, using midpoint")
                try:
                    prob = self.pricing.midprob(bracket, save_snapshot=False)
                except Exception as e:
                    logger.warning(f"Failed to get price for {bracket.name}: {e}")
            
            market_probs_open.append(prob)
        
        # Log price availability
        prices_found = sum(1 for p in market_probs_open if p is not None)
        logger.info(f"Prices available: {prices_found}/{len(brackets)} brackets")
        
        # 5. Merge Zeus + Market probabilities
        # Resolution-only mode: If NO prices available, still create records for resolution
        if prices_found == 0:
            logger.info("⚠️  No market prices available - using RESOLUTION-ONLY mode")
            logger.info("   Will validate Zeus accuracy without P&L calculation")
            
            # Create probs with None market prices (resolution-only)
            probs_with_market = []
            for zeus_prob in zeus_probs:
                probs_with_market.append(
                    BracketProb(
                        bracket=zeus_prob.bracket,
                        p_zeus=zeus_prob.p_zeus,
                        p_mkt=None,  # No market price available
                        sigma_z=zeus_prob.sigma_z,
                    )
                )
        else:
            # Normal mode: Merge Zeus + Market probabilities
            probs_with_market = []
            for zeus_prob, market_prob in zip(zeus_probs, market_probs_open):
                if market_prob is not None:
                    # Copy Zeus prob and add market prob
                    prob_copy = BracketProb(
                        bracket=zeus_prob.bracket,
                        p_zeus=zeus_prob.p_zeus,
                        p_mkt=market_prob,
                        sigma_z=zeus_prob.sigma_z,
                    )
                    probs_with_market.append(prob_copy)
        
        # 6. Calculate edges and sizes (only if we have prices)
        if prices_found > 0:
            # Normal mode: Calculate edges
            decisions = self.sizer.decide(
                probs=probs_with_market,
                bankroll_usd=self.bankroll_usd,
            )
            
            # Filter for positive edges
            trades_to_make = [d for d in decisions if d.edge > 0]
            
            if not trades_to_make:
                logger.debug(f"No edges found for {station.city} on {trade_date}")
                return []
        else:
            # Resolution-only mode: No edge calculation, just track brackets
            logger.info("   Resolution-only: Tracking all brackets for Zeus validation")
            trades_to_make = probs_with_market  # Use BracketProb objects directly
        
        # 7. Create backtest trades
        backtest_trades = []
        
        # Resolution-only mode: trades_to_make is List[BracketProb]
        if prices_found == 0:
            for bracket_prob in trades_to_make:
                trade = BacktestTrade(
                    date=trade_date,
                    station_code=station_code,
                    city=station.city,
                    bracket_name=bracket_prob.bracket.name,
                    lower=bracket_prob.bracket.lower_F,
                    upper=bracket_prob.bracket.upper_F,
                    zeus_prob=bracket_prob.p_zeus,
                    market_prob_open=None,  # No price data
                    edge=0.0,  # Can't calculate edge
                    size_usd=0.0,  # No trade sizing
                    outcome="pending",
                    realized_pnl=0.0,
                    market_prob_close=None,
                    market_id=bracket_prob.bracket.market_id,
                )
                backtest_trades.append(trade)
                
                logger.debug(
                    f"  Resolution-only: {trade.bracket_name} "
                    f"(Zeus: {trade.zeus_prob:.1%})"
                )
        
        # Normal mode: trades_to_make is List[EdgeDecision]
        else:
            # Create mapping from bracket to prob for lookup
            prob_map = {bp.bracket.market_id: bp for bp in probs_with_market}
            
            for decision in trades_to_make:
                # Get the corresponding BracketProb to access probabilities
                bracket_prob = prob_map.get(decision.bracket.market_id)
                if not bracket_prob:
                    logger.warning(f"Could not find prob for {decision.bracket.name}")
                    continue
                
                # Get closing price (end of day)
                try:
                    market_prob_close = self.pricing.midprob(
                        decision.bracket,
                        save_snapshot=False,
                    )
                except Exception:
                    market_prob_close = None
                
                # Mark as pending (will be resolved later)
                outcome = "pending"
                realized_pnl = 0.0
                
                trade = BacktestTrade(
                    date=trade_date,
                    station_code=station_code,
                    city=station.city,
                    bracket_name=decision.bracket.name,
                    lower=decision.bracket.lower_F,
                    upper=decision.bracket.upper_F,
                    zeus_prob=bracket_prob.p_zeus,
                    market_prob_open=bracket_prob.p_mkt,
                    edge=decision.edge,
                    size_usd=decision.size_usd,
                    outcome=outcome,
                    realized_pnl=realized_pnl,
                    market_prob_close=market_prob_close,
                    market_id=decision.bracket.market_id,
                )
                
                backtest_trades.append(trade)
                
                logger.info(
                    f"  Backtest trade: {trade.bracket_name} "
                    f"edge={trade.edge:.1%} size=${trade.size_usd:.2f}"
                )
        
        # Resolve trades using Polymarket outcomes (Stage 7A)
        self._resolve_trades(backtest_trades)
        
        return backtest_trades
    
    def _load_saved_prices(self, trade_date: date, station_code: str) -> Optional[dict]:
        """Load saved prices from paper trading runs.
        
        Args:
            trade_date: Date to load prices for
            station_code: Station code
        
        Returns:
            Dict mapping market_id → price, or None if not available
        """
        date_str = trade_date.isoformat()
        price_file = self.price_snapshots_dir / date_str / f"{station_code}_prices.json"
        
        if not price_file.exists():
            logger.debug(f"No saved prices found for {station_code} on {trade_date}")
            return None
        
        try:
            with open(price_file, "r") as f:
                prices_list = json.load(f)
            
            # Convert to dict: market_id → p_mkt
            prices_dict = {
                p["market_id"]: p["p_mkt"]
                for p in prices_list
                if "market_id" in p and "p_mkt" in p
            }
            
            logger.info(f"📂 Loaded {len(prices_dict)} saved prices for {station_code}")
            return prices_dict
            
        except Exception as e:
            logger.warning(f"Failed to load saved prices: {e}")
            return None
    
    def _resolve_trades(self, trades: List[BacktestTrade]) -> None:
        """Resolve trades using Polymarket outcomes via event outcomePrices.
        
        Fetches events from Polymarket Gamma API and determines winners
        by checking outcomePrices field (faster than waiting for resolved flag).
        
        Args:
            trades: List of BacktestTrade objects to resolve (modified in place)
        """
        if not trades:
            return
        
        logger.debug(f"Resolving {len(trades)} trades via Polymarket events")
        
        # Group trades by date and city to fetch events once
        from collections import defaultdict
        trades_by_event = defaultdict(list)
        
        for trade in trades:
            key = (trade.date, trade.city)
            trades_by_event[key].append(trade)
        
        # Resolve each event
        for (trade_date, city), event_trades in trades_by_event.items():
            logger.debug(f"Resolving {city} on {trade_date}")
            
            try:
                # Fetch event using discovery
                event_slug = self.discovery._generate_event_slugs(city, trade_date)
                
                event = None
                for slug in event_slug:
                    event = self.discovery.get_event_by_slug(slug, save_snapshot=False)
                    if event:
                        break
                
                if not event:
                    logger.debug(f"No event found for {city} on {trade_date}")
                    for trade in event_trades:
                        trade.outcome = "pending"
                    continue
                
                # Find winner using outcomePrices
                winner_bracket = self.resolution.get_winner_from_event(event)
                
                if not winner_bracket:
                    logger.debug(f"Event not resolved yet: {city} on {trade_date}")
                    for trade in event_trades:
                        trade.outcome = "pending"
                    continue
                
                logger.info(f"🏆 {city} {trade_date}: Winner = {winner_bracket}")
                
                # Apply winner to all trades from this event
                for trade in event_trades:
                    # Store actual winner for summary
                    trade.winner_bracket = winner_bracket
                    
                    # Check if this trade's bracket matches the winner
                    trade_bracket = trade.bracket_name
                    
                    # Normalize bracket names for comparison - need EXACT match
                    winner_normalized = winner_bracket.replace("°F", "").replace("≤", "").replace("≥", "").strip()
                    trade_normalized = trade_bracket.replace("°F", "").strip()
                    
                    if winner_normalized == trade_normalized:
                        # WIN!
                        trade.outcome = "win"
                        
                        # Calculate P&L only if we have prices
                        if trade.market_prob_open and trade.market_prob_open > 0:
                            trade.realized_pnl = round(
                                (1.0 / trade.market_prob_open - 1.0) * trade.size_usd,
                                2
                            )
                        else:
                            # Resolution-only mode (no prices)
                            trade.realized_pnl = 0.0
                        
                        logger.info(
                            f"✅ WIN: {trade.bracket_name} on {trade.date} "
                            f"(winner: {winner_bracket})"
                        )
                    else:
                        # LOSS
                        trade.outcome = "loss"
                        
                        if trade.market_prob_open and trade.size_usd > 0:
                            trade.realized_pnl = round(-trade.size_usd, 2)
                        else:
                            trade.realized_pnl = 0.0
                        
                        logger.debug(
                            f"❌ LOSS: {trade.bracket_name} on {trade.date} "
                            f"(winner: {winner_bracket})"
                        )
            
            except Exception as e:
                logger.error(f"Failed to resolve {city} on {trade_date}: {e}")
                for trade in event_trades:
                    trade.outcome = "pending"
                continue
    
    def _save_results(
        self,
        start_date: date,
        end_date: date,
        trades: List[BacktestTrade],
    ) -> Path:
        """Save backtest results to CSV.
        
        Args:
            start_date: Backtest start date
            end_date: Backtest end date
            trades: List of backtest trades
        
        Returns:
            Path to saved CSV file
        """
        # Create filename
        filename = f"{start_date}_to_{end_date}.csv"
        output_path = self.runs_dir / filename
        
        # Write CSV
        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                "date",
                "station_code",
                "city",
                "bracket_name",
                "lower",
                "upper",
                "zeus_prob",
                "market_prob_open",
                "market_prob_close",
                "edge",
                "size_usd",
                "outcome",
                "realized_pnl",
            ])
            
            # Data
            for trade in trades:
                writer.writerow([
                    trade.date.isoformat(),
                    trade.station_code,
                    trade.city,
                    trade.bracket_name,
                    trade.lower if trade.lower is not None else "",
                    trade.upper if trade.upper is not None else "",
                    f"{trade.zeus_prob:.4f}",
                    f"{trade.market_prob_open:.4f}" if trade.market_prob_open is not None else "",
                    f"{trade.market_prob_close:.4f}" if trade.market_prob_close is not None else "",
                    f"{trade.edge:.4f}",
                    f"{trade.size_usd:.2f}",
                    trade.outcome,
                    f"{trade.realized_pnl:.2f}",
                ])
        
        return output_path
    
    def _save_resolution_summary(
        self,
        trades: List[BacktestTrade],
        start_date: date,
        end_date: date,
    ) -> Path:
        """Save resolution-only summary: Zeus prediction vs actual outcome.
        
        For resolution-only backtests, create a simple summary showing:
        - Date, station, city
        - Zeus's predicted bracket (highest probability)
        - Actual winning bracket
        - Whether Zeus was correct
        
        Args:
            trades: All trades
            start_date: Start of backtest period
            end_date: End of backtest period
        
        Returns:
            Path to summary CSV
        """
        output_path = (
            self.runs_dir / 
            f"{start_date.isoformat()}_to_{end_date.isoformat()}_SUMMARY.csv"
        )
        
        # Group trades by day and station
        from collections import defaultdict
        daily_trades = defaultdict(list)
        
        for trade in trades:
            key = (trade.date, trade.station_code, trade.city)
            daily_trades[key].append(trade)
        
        # Write summary
        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                "date",
                "station_code", 
                "city",
                "zeus_prediction",  # Bracket Zeus chose (highest prob)
                "zeus_probability",  # Confidence level
                "actual_outcome",  # What actually happened
                "zeus_correct",  # YES/NO
            ])
            
            # Data: One row per day/station
            for (day, station, city), day_trades in sorted(daily_trades.items()):
                # Find Zeus's top pick (highest probability)
                zeus_pick = max(day_trades, key=lambda t: t.zeus_prob)
                
                # Find actual winner (if resolved)
                actual_outcome = None
                
                # Get the actual winner from any trade (they all have the same winner_bracket)
                for trade in day_trades:
                    if trade.winner_bracket:
                        actual_outcome = trade.winner_bracket
                        break
                
                # Determine if Zeus was correct by comparing Zeus's pick to actual outcome
                if actual_outcome:
                    # Normalize both for comparison
                    zeus_normalized = zeus_pick.bracket_name.replace("°F", "").replace("≤", "").replace("≥", "").strip()
                    actual_normalized = actual_outcome.replace("°F", "").replace("≤", "").replace("≥", "").strip()
                    
                    # Exact match required
                    if zeus_normalized == actual_normalized:
                        zeus_correct = "YES"
                    else:
                        zeus_correct = "NO"
                elif any(t.outcome == "loss" for t in day_trades):
                    # Resolved but no winner info
                    zeus_correct = "NO"
                    actual_outcome = "Resolved (outside tracked brackets)"
                else:
                    # Still pending
                    zeus_correct = "PENDING"
                    actual_outcome = "Not yet resolved"
                
                writer.writerow([
                    day.isoformat(),
                    station,
                    city,
                    zeus_pick.bracket_name,
                    f"{zeus_pick.zeus_prob:.1%}",
                    actual_outcome,
                    zeus_correct,
                ])
        
        logger.info(f"Resolution summary saved to {output_path}")
        return output_path
    
    def _calculate_summary(
        self,
        start_date: date,
        end_date: date,
        trades: List[BacktestTrade],
    ) -> BacktestSummary:
        """Calculate summary statistics.
        
        Args:
            start_date: Backtest start date
            end_date: Backtest end date
            trades: List of backtest trades
        
        Returns:
            BacktestSummary with aggregated metrics
        """
        if not trades:
            return BacktestSummary(
                start_date=start_date,
                end_date=end_date,
                total_trades=0,
                wins=0,
                losses=0,
                pending=0,
                hit_rate=0.0,
                total_risk=0.0,
                total_pnl=0.0,
                roi=0.0,
                avg_edge=0.0,
                avg_winning_pnl=0.0,
                avg_losing_pnl=0.0,
                largest_win=0.0,
                largest_loss=0.0,
            )
        
        # Count outcomes
        wins = sum(1 for t in trades if t.outcome == "win")
        losses = sum(1 for t in trades if t.outcome == "loss")
        pending = sum(1 for t in trades if t.outcome == "pending")
        
        # Calculate metrics
        total_risk = sum(t.size_usd for t in trades)
        total_pnl = sum(t.realized_pnl for t in trades)
        roi = (total_pnl / total_risk * 100) if total_risk > 0 else 0.0
        hit_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0.0
        avg_edge = sum(t.edge for t in trades) / len(trades)
        
        winning_trades = [t for t in trades if t.realized_pnl > 0]
        losing_trades = [t for t in trades if t.realized_pnl < 0]
        
        avg_winning_pnl = (
            sum(t.realized_pnl for t in winning_trades) / len(winning_trades)
            if winning_trades else 0.0
        )
        avg_losing_pnl = (
            sum(t.realized_pnl for t in losing_trades) / len(losing_trades)
            if losing_trades else 0.0
        )
        
        largest_win = max((t.realized_pnl for t in trades), default=0.0)
        largest_loss = min((t.realized_pnl for t in trades), default=0.0)
        
        return BacktestSummary(
            start_date=start_date,
            end_date=end_date,
            total_trades=len(trades),
            wins=wins,
            losses=losses,
            pending=pending,
            hit_rate=hit_rate,
            total_risk=total_risk,
            total_pnl=total_pnl,
            roi=roi,
            avg_edge=avg_edge * 100,  # Convert to percentage
            avg_winning_pnl=avg_winning_pnl,
            avg_losing_pnl=avg_losing_pnl,
            largest_win=largest_win,
            largest_loss=largest_loss,
        )
    
    def _print_summary(self, summary: BacktestSummary) -> None:
        """Print backtest summary to console.
        
        Args:
            summary: BacktestSummary to print
        """
        logger.info("\n" + "=" * 70)
        logger.info("BACKTEST SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Date Range: {summary.start_date} to {summary.end_date}")
        logger.info(f"Total Trades: {summary.total_trades}")
        logger.info(f"Wins: {summary.wins} | Losses: {summary.losses} | Pending: {summary.pending}")
        
        if summary.wins + summary.losses > 0:
            logger.info(f"Hit Rate: {summary.hit_rate:.1f}%")
        
        logger.info(f"Total Risk: ${summary.total_risk:,.2f}")
        logger.info(f"Total P&L: ${summary.total_pnl:,.2f}")
        logger.info(f"ROI: {summary.roi:.1f}%")
        logger.info(f"Avg Edge: {summary.avg_edge:.1f}%")
        
        if summary.avg_winning_pnl > 0:
            logger.info(f"Avg Win: ${summary.avg_winning_pnl:.2f}")
        if summary.avg_losing_pnl < 0:
            logger.info(f"Avg Loss: ${summary.avg_losing_pnl:.2f}")
        if summary.largest_win > 0:
            logger.info(f"Largest Win: ${summary.largest_win:.2f}")
        if summary.largest_loss < 0:
            logger.info(f"Largest Loss: ${summary.largest_loss:.2f}")
        
        logger.info("=" * 70 + "\n")

