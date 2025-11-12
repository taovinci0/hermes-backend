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
    ):
        """Initialize backtester.
        
        Args:
            bankroll_usd: Starting bankroll for simulation
            edge_min: Minimum edge threshold (default 5%)
            fee_bp: Fee in basis points (default 50bp)
            slippage_bp: Slippage in basis points (default 30bp)
        """
        self.bankroll_usd = bankroll_usd
        self.edge_min = edge_min
        self.fee_bp = fee_bp
        self.slippage_bp = slippage_bp
        
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
        
        # 1. Get Zeus forecast for market open (assume 9am local time)
        market_open = datetime.combine(
            trade_date,
            datetime.min.time().replace(hour=9)
        )
        
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
        
        # 3. Map Zeus probabilities
        zeus_probs = self.prob_mapper.map_daily_high(zeus_forecast, brackets)
        
        # 4. Get opening prices (simulate market open)
        market_probs_open = []
        for bracket in brackets:
            try:
                # For closed markets, use price history (Gamma API)
                # For open markets, use current midpoint (CLOB API)
                if bracket.closed:
                    logger.debug(f"Market {bracket.name} is closed, using price history")
                    prob = self.pricing.get_price_history(bracket)
                else:
                    logger.debug(f"Market {bracket.name} is open, using midpoint")
                    prob = self.pricing.midprob(bracket, save_snapshot=False)
                
                market_probs_open.append(prob)
            except Exception as e:
                logger.warning(f"Failed to get price for {bracket.name}: {e}")
                market_probs_open.append(None)
        
        # 5. Merge Zeus + Market probabilities
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
        
        if not probs_with_market:
            logger.debug(f"No valid market prices for {station.city} on {trade_date}")
            return []
        
        # 6. Calculate edges and sizes
        decisions = self.sizer.decide(
            probs=probs_with_market,
            bankroll_usd=self.bankroll_usd,
        )
        
        # Filter for positive edges
        trades_to_make = [d for d in decisions if d.edge > 0]
        
        if not trades_to_make:
            logger.debug(f"No edges found for {station.city} on {trade_date}")
            return []
        
        # Create mapping from bracket to prob for lookup
        prob_map = {bp.bracket.market_id: bp for bp in probs_with_market}
        
        # 7. Simulate trades and calculate P&L
        backtest_trades = []
        
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
            
            # For now, mark as pending (would need actual outcomes)
            # In real backtest, we'd check if temperature hit the bracket
            outcome = "pending"
            realized_pnl = 0.0
            
            # TODO: Get actual temperature outcome and calculate real P&L
            # For MVP, we'll just track the edges
            
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
                market_id=decision.bracket.market_id,  # Store for resolution
            )
            
            backtest_trades.append(trade)
            
            logger.info(
                f"  Backtest trade: {trade.bracket_name} "
                f"edge={trade.edge:.1%} size=${trade.size_usd:.2f}"
            )
        
        # Resolve trades using Polymarket outcomes (Stage 7A)
        self._resolve_trades(backtest_trades)
        
        return backtest_trades
    
    def _resolve_trades(self, trades: List[BacktestTrade]) -> None:
        """Resolve trades using Polymarket outcomes.
        
        Fetches winning outcomes from Polymarket Gamma API and updates
        trade outcomes and realized P&L.
        
        Args:
            trades: List of BacktestTrade objects to resolve (modified in place)
        """
        if not trades:
            return
        
        logger.debug(f"Resolving {len(trades)} trades via Polymarket")
        
        for trade in trades:
            # Skip if no market_id
            if not trade.market_id:
                logger.debug(f"Trade {trade.bracket_name} has no market_id, keeping as pending")
                continue
            
            try:
                # Get resolution from Polymarket
                result = self.resolution.get_winner(trade.market_id, save_snapshot=True)
                
                if not result["resolved"]:
                    logger.debug(f"Market {trade.market_id} not yet resolved")
                    trade.outcome = "pending"
                    continue
                
                winner = result.get("winner")
                if not winner:
                    logger.warning(f"Market {trade.market_id} resolved but no winner found")
                    trade.outcome = "pending"
                    continue
                
                # Check if our bracket won
                # Winner format varies: could be "55-60" or "55-60°F" or just the bracket
                # Our bracket: lower=55, upper=60, name="55-60°F"
                winner_clean = str(winner).replace("°F", "").replace("°", "").strip()
                
                # Try to match on the bracket range
                bracket_range = f"{trade.lower}-{trade.upper}"
                
                if bracket_range in winner_clean or winner_clean in bracket_range:
                    # WIN!
                    trade.outcome = "win"
                    # Calculate P&L: (1/price - 1) * size
                    # If we bet $100 at price 0.60, we get $100/0.60 = $166.67 back
                    # Profit = $166.67 - $100 = $66.67
                    if trade.market_prob_open > 0:
                        trade.realized_pnl = round(
                            (1.0 / trade.market_prob_open - 1.0) * trade.size_usd,
                            2
                        )
                    else:
                        # Edge case: price was 0
                        trade.realized_pnl = trade.size_usd
                    
                    logger.info(
                        f"✅ WIN: {trade.bracket_name} on {trade.date} "
                        f"(winner: {winner}) → +${trade.realized_pnl:.2f}"
                    )
                else:
                    # LOSS
                    trade.outcome = "loss"
                    trade.realized_pnl = round(-trade.size_usd, 2)
                    
                    logger.info(
                        f"❌ LOSS: {trade.bracket_name} on {trade.date} "
                        f"(winner: {winner}) → ${trade.realized_pnl:.2f}"
                    )
            
            except Exception as e:
                logger.error(f"Failed to resolve trade {trade.bracket_name}: {e}")
                # Keep as pending if resolution fails
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
                    f"{trade.market_prob_open:.4f}",
                    f"{trade.market_prob_close:.4f}" if trade.market_prob_close else "",
                    f"{trade.edge:.4f}",
                    f"{trade.size_usd:.2f}",
                    trade.outcome,
                    f"{trade.realized_pnl:.2f}",
                ])
        
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

