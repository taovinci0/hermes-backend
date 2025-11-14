"""Dynamic trading engine - continuous evaluation loop.

Continuously fetches fresh Zeus forecasts and Polymarket prices,
calculates edges, and executes paper trades.
"""

from datetime import datetime, date, timedelta
from time import sleep
from zoneinfo import ZoneInfo
from typing import List

from core.config import config
from core.logger import logger
from core.registry import StationRegistry
from core.types import BracketProb
from agents.dynamic_trader.fetchers import DynamicFetcher
from agents.dynamic_trader.snapshotter import DynamicSnapshotter
from agents.prob_mapper import ProbabilityMapper
from agents.edge_and_sizing import Sizer
from venues.polymarket.execute import PaperBroker


class DynamicTradingEngine:
    """Continuous trading engine with dynamic Zeus + Polymarket fetching."""
    
    def __init__(
        self,
        stations: List[str],
        interval_seconds: int = 900,  # 15 minutes default
        lookahead_days: int = 2,
    ):
        """Initialize dynamic trading engine.
        
        Args:
            stations: List of station codes (e.g., ['EGLC', 'KLGA'])
            interval_seconds: Time between evaluation cycles (default 900 = 15 min)
            lookahead_days: How many days ahead to check (2 = today + tomorrow)
        """
        self.stations = stations
        self.interval_seconds = interval_seconds
        self.lookahead_days = lookahead_days
        
        # Components
        self.registry = StationRegistry()
        self.fetcher = DynamicFetcher()
        self.prob_mapper = ProbabilityMapper()
        self.sizer = Sizer(
            edge_min=config.trading.edge_min,
            fee_bp=config.trading.fee_bp,
            slippage_bp=config.trading.slippage_bp,
            kelly_cap=config.trading.kelly_cap,
            per_market_cap=config.trading.per_market_cap,
        )
        self.broker = PaperBroker(save_prices=False)  # Dynamic mode handles own snapshots
        self.snapshotter = DynamicSnapshotter()
        
        logger.info(f"🚀 Dynamic Trading Engine initialized")
        logger.info(f"   Stations: {', '.join(stations)}")
        logger.info(f"   Interval: {interval_seconds}s ({interval_seconds/60:.0f} min)")
        logger.info(f"   Lookahead: {lookahead_days} days")
        logger.info(f"   Model: {config.model_mode}")
    
    def run(self):
        """Run continuous trading loop.
        
        Evaluates markets at regular intervals until interrupted.
        Markets are checked for today + lookahead days.
        
        Press Ctrl+C to stop.
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"🔄 STARTING DYNAMIC PAPER TRADING")
        logger.info(f"{'='*70}")
        logger.info(f"Markets open 1-2 days before event, so we check multiple days")
        logger.info(f"Press Ctrl+C to stop\n")
        
        cycle_count = 0
        total_trades = 0
        
        try:
            while True:
                cycle_count += 1
                cycle_start = datetime.now(ZoneInfo("UTC"))
                
                logger.info(f"\n{'='*70}")
                logger.info(f"🔄 CYCLE {cycle_count}: {cycle_start.strftime('%Y-%m-%d %H:%M:%S')} UTC")
                logger.info(f"{'='*70}")
                
                cycle_trades = 0
                
                # Evaluate each station
                for station_code in self.stations:
                    station = self.registry.get(station_code)
                    if not station:
                        logger.warning(f"Station {station_code} not found")
                        continue
                    
                    # Check today + next N days (markets may already be open)
                    today = date.today()
                    event_days = [
                        today + timedelta(days=i) 
                        for i in range(self.lookahead_days)
                    ]
                    
                    for event_day in event_days:
                        trades = self._evaluate_and_trade(station, event_day, cycle_start)
                        cycle_trades += trades
                
                total_trades += cycle_trades
                
                # Wait for next cycle
                cycle_end = datetime.now(ZoneInfo("UTC"))
                cycle_duration = (cycle_end - cycle_start).total_seconds()
                
                logger.info(f"\n✅ Cycle {cycle_count} complete in {cycle_duration:.1f}s")
                logger.info(f"   Trades this cycle: {cycle_trades}")
                logger.info(f"   Total trades: {total_trades}")
                logger.info(f"😴 Sleeping for {self.interval_seconds}s ({self.interval_seconds/60:.0f} min)...")
                
                sleep(self.interval_seconds)
        
        except KeyboardInterrupt:
            logger.info(f"\n\n{'='*70}")
            logger.info(f"🛑 Dynamic trading stopped by user")
            logger.info(f"{'='*70}")
            logger.info(f"Total cycles: {cycle_count}")
            logger.info(f"Total trades: {total_trades}")
            logger.info(f"Avg trades/cycle: {total_trades/max(1, cycle_count):.1f}")
    
    def _evaluate_and_trade(
        self,
        station,
        event_day: date,
        cycle_time: datetime,
    ) -> int:
        """Evaluate and trade a single station/event.
        
        Args:
            station: Weather station
            event_day: Event date to trade
            cycle_time: Current cycle timestamp (UTC)
        
        Returns:
            Number of trades placed
        """
        logger.info(f"\n  📊 {station.city} → {event_day}")
        
        try:
            # Check if markets are open for this event
            has_open_markets = self.fetcher.check_open_events(station.city, event_day)
            
            if not has_open_markets:
                logger.debug(f"     No open markets")
                return 0
            
            # 1. Fetch Zeus (JIT, using LOCAL time)
            logger.debug(f"     Fetching Zeus...")
            forecast = self.fetcher.fetch_zeus_jit(station, event_day)
            
            # 2. Fetch Polymarket (JIT)
            logger.debug(f"     Fetching Polymarket...")
            brackets, prices = self.fetcher.fetch_polymarket_jit(station.city, event_day)
            
            if not brackets:
                logger.debug(f"     No brackets available")
                return 0
            
            # 2b. Fetch METAR (JIT, only for today's events)
            logger.debug(f"     Fetching METAR...")
            metar_observations = self.fetcher.fetch_metar_jit(station, event_day)
            
            # 3. Map Zeus probabilities
            logger.debug(f"     Mapping probabilities...")
            probs = self.prob_mapper.map_daily_high(forecast, brackets)
            
            # 4. Add market prices
            probs_with_market = []
            for prob, p_mkt in zip(probs, prices):
                if p_mkt is not None:
                    # Create new BracketProb with market price
                    prob_with_mkt = BracketProb(
                        bracket=prob.bracket,
                        p_zeus=prob.p_zeus,
                        p_mkt=p_mkt,
                        sigma_z=prob.sigma_z,
                    )
                    probs_with_market.append(prob_with_mkt)
            
            if not probs_with_market:
                logger.debug(f"     No valid market prices")
                return 0
            
            # 5. Calculate edges and sizes
            logger.debug(f"     Calculating edges...")
            decisions = self.sizer.decide(
                probs=probs_with_market,
                bankroll_usd=config.trading.daily_bankroll_cap,
            )
            
            # Filter positive edges
            trades = [d for d in decisions if d.edge > 0]
            
            if trades:
                logger.info(f"     💰 {len(trades)} positive edges found")
                
                # Log trade details
                for trade in trades:
                    logger.info(
                        f"        {trade.bracket.name}: "
                        f"edge={trade.edge*100:.2f}% size=${trade.size_usd:.2f}"
                    )
                
                # Execute immediately (minimal staleness)
                self.broker.place(trades)
                
                # Save timestamped snapshots
                self.snapshotter.save_all(
                    forecast=forecast,
                    brackets=brackets,
                    prices=prices,
                    decisions=trades,
                    cycle_time=cycle_time,
                    event_day=event_day,
                    station=station,
                    metar_observations=metar_observations,
                )
                
                return len(trades)
            else:
                logger.debug(f"     No positive edges")
                
                # Still save snapshots even if no trades (for analysis)
                self.snapshotter.save_all(
                    forecast=forecast,
                    brackets=brackets,
                    prices=prices,
                    decisions=[],
                    cycle_time=cycle_time,
                    event_day=event_day,
                    station=station,
                    metar_observations=metar_observations,
                )
                
                return 0
        
        except Exception as e:
            logger.error(f"     ❌ Error: {e}", exc_info=False)
            return 0

