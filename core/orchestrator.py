"""Main orchestrator for Hermes trading system.

Coordinates the pipeline: pull → infer → decide → execute → log
"""

import argparse
from datetime import date, datetime
from pathlib import Path

from .config import config
from .logger import logger


def main() -> None:
    """Main entry point for Hermes orchestrator."""
    parser = argparse.ArgumentParser(
        description="Hermes v1.0.0 - Weather→Markets Trading System"
    )
    parser.add_argument(
        "--mode",
        choices=["fetch", "probmap", "paper", "backtest"],
        required=True,
        help="Operation mode",
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Date for fetch/probmap mode (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--station",
        type=str,
        help="Station code for fetch mode (e.g., EGLC)",
    )
    parser.add_argument(
        "--stations",
        type=str,
        help="Comma-separated station codes (e.g., EGLC,KLGA)",
    )
    parser.add_argument(
        "--start",
        type=str,
        help="Start date for backtest mode (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end",
        type=str,
        help="End date for backtest mode (YYYY-MM-DD)",
    )

    args = parser.parse_args()

    logger.info(f"🚀 Hermes v1.0.0 starting in [bold]{args.mode}[/bold] mode")
    logger.info(f"Execution mode: [bold]{config.execution_mode}[/bold]")

    if args.mode == "fetch":
        if not args.date or not args.station:
            logger.error("--date and --station required for fetch mode")
            return
        run_fetch(args.date, args.station)

    elif args.mode == "probmap":
        if not args.date or not args.station:
            logger.error("--date and --station required for probmap mode")
            return
        run_probmap(args.date, args.station)

    elif args.mode == "paper":
        stations = args.stations.split(",") if args.stations else config.trading.active_stations
        run_paper(stations)

    elif args.mode == "backtest":
        if not args.start or not args.end or not args.stations:
            logger.error("--start, --end, and --stations required for backtest mode")
            return
        stations = args.stations.split(",")
        run_backtest(args.start, args.end, stations)


def run_fetch(date_str: str, station: str) -> None:
    """Fetch Zeus forecast for a station and date.

    Args:
        date_str: Date in YYYY-MM-DD format
        station: Station code (e.g., EGLC)
    """
    from agents.zeus_forecast import ZeusForecastAgent
    from core.registry import get_registry
    from core import time_utils
    
    logger.info(f"📡 Fetching Zeus forecast for {station} on {date_str}")
    
    # Get station from registry
    registry = get_registry()
    station_obj = registry.get(station)
    
    if not station_obj:
        logger.error(f"Station {station} not found in registry")
        return
    
    # Parse date and get local day window
    try:
        forecast_date = date.fromisoformat(date_str)
    except ValueError as e:
        logger.error(f"Invalid date format '{date_str}': {e}")
        return
    
    # Get UTC window for the local day
    start_utc, end_utc = time_utils.get_local_day_window_utc(
        forecast_date,
        station_obj.time_zone
    )
    
    logger.info(
        f"Station: {station_obj.city} ({station_obj.station_code})"
    )
    logger.info(
        f"Coordinates: {station_obj.lat:.4f}°N, {station_obj.lon:.4f}°E"
    )
    logger.info(
        f"Local date: {date_str} ({station_obj.time_zone})"
    )
    logger.info(
        f"UTC window: {start_utc.isoformat()} → {end_utc.isoformat()}"
    )
    
    # Fetch forecast
    agent = ZeusForecastAgent()
    try:
        forecast = agent.fetch(
            lat=station_obj.lat,
            lon=station_obj.lon,
            start_utc=start_utc,
            hours=24,
            station_code=station_obj.station_code,
        )
        
        logger.info(f"✅ Successfully fetched {len(forecast.timeseries)} forecast points")
        logger.info(f"Temperature range: {min(p.temp_K for p in forecast.timeseries):.2f}K - {max(p.temp_K for p in forecast.timeseries):.2f}K")
        
        # Convert to Fahrenheit for display
        from core import units
        temps_f = [units.kelvin_to_fahrenheit(p.temp_K) for p in forecast.timeseries]
        logger.info(f"Temperature range: {min(temps_f):.1f}°F - {max(temps_f):.1f}°F")
        
    except Exception as e:
        logger.error(f"Failed to fetch Zeus forecast: {e}")
        raise


def run_probmap(date_str: str, station: str) -> None:
    """Map Zeus forecast to bracket probabilities.

    Args:
        date_str: Date in YYYY-MM-DD format
        station: Station code (e.g., EGLC)
    """
    from agents.zeus_forecast import ZeusForecastAgent
    from agents.prob_mapper import ProbabilityMapper
    from core.registry import get_registry
    from core import time_utils
    
    logger.info(f"📊 Mapping probabilities for {station} on {date_str}")
    
    # Get station from registry
    registry = get_registry()
    station_obj = registry.get(station)
    
    if not station_obj:
        logger.error(f"Station {station} not found in registry")
        return
    
    # Parse date
    try:
        forecast_date = date.fromisoformat(date_str)
    except ValueError as e:
        logger.error(f"Invalid date format '{date_str}': {e}")
        return
    
    # Get UTC window for the local day
    start_utc, end_utc = time_utils.get_local_day_window_utc(
        forecast_date,
        station_obj.time_zone
    )
    
    logger.info(f"Station: {station_obj.city} ({station_obj.station_code})")
    
    # Fetch Zeus forecast
    zeus_agent = ZeusForecastAgent()
    try:
        forecast = zeus_agent.fetch(
            lat=station_obj.lat,
            lon=station_obj.lon,
            start_utc=start_utc,
            hours=24,
            station_code=station_obj.station_code,
        )
        logger.info(f"✅ Fetched {len(forecast.timeseries)} forecast points")
    except Exception as e:
        logger.error(f"Failed to fetch Zeus forecast: {e}")
        return
    
    # Create sample brackets (will use market discovery in Stage 4)
    # For now, use typical 1°F brackets around forecast range
    from core import units
    temps_f = [units.kelvin_to_fahrenheit(p.temp_K) for p in forecast.timeseries]
    min_temp = int(min(temps_f)) - 3
    max_temp = int(max(temps_f)) + 4
    
    brackets = [
        MarketBracket(name=f"{i}-{i+1}°F", lower_F=i, upper_F=i+1)
        for i in range(min_temp, max_temp)
    ]
    
    logger.info(f"Using {len(brackets)} brackets from {min_temp}°F to {max_temp}°F")
    
    # Map probabilities
    mapper = ProbabilityMapper()
    try:
        bracket_probs = mapper.map_daily_high(forecast, brackets)
        
        logger.info(f"✅ Mapped probabilities for {len(bracket_probs)} brackets")
        
        # Display top 5 most likely brackets
        sorted_probs = sorted(bracket_probs, key=lambda bp: bp.p_zeus, reverse=True)
        logger.info("Top 5 most likely brackets:")
        for i, bp in enumerate(sorted_probs[:5], 1):
            logger.info(
                f"  {i}. [{bp.bracket.lower_F}-{bp.bracket.upper_F}°F): "
                f"p_zeus = {bp.p_zeus:.4f} ({bp.p_zeus*100:.2f}%)"
            )
        
        # Summary statistics
        total_prob = sum(bp.p_zeus for bp in bracket_probs)
        logger.info(f"Probability sum: {total_prob:.6f}")
        logger.info(f"Forecast uncertainty (σ): {bracket_probs[0].sigma_z:.2f}°F")
        
    except Exception as e:
        logger.error(f"Failed to map probabilities: {e}")
        raise


def run_paper(stations: list[str]) -> None:
    """Run paper trading for specified stations.

    Complete pipeline: fetch → infer → decide → execute → log

    Args:
        stations: List of station codes
    """
    from datetime import date
    from agents.zeus_forecast import ZeusForecastAgent
    from agents.prob_mapper import ProbabilityMapper
    from agents.edge_and_sizing import Sizer
    from venues.polymarket.discovery import PolyDiscovery
    from venues.polymarket.pricing import PolyPricing
    from venues.polymarket.execute import PaperBroker
    from core.registry import get_registry
    from core import time_utils
    
    logger.info(f"📄 Running paper trading for stations: {', '.join(stations)}")
    logger.info(f"Execution mode: {config.execution_mode}")
    logger.info(f"Bankroll: ${config.trading.daily_bankroll_cap:.2f}")
    
    # Initialize agents
    registry = get_registry()
    zeus_agent = ZeusForecastAgent()
    mapper = ProbabilityMapper()
    sizer = Sizer()
    discovery = PolyDiscovery()
    pricing = PolyPricing()
    broker = PaperBroker()
    
    today = date.today()
    all_decisions = []
    
    # Process each station
    for station_code in stations:
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing station: {station_code}")
        logger.info(f"{'='*60}")
        
        # Get station from registry
        station = registry.get(station_code)
        if not station:
            logger.error(f"Station {station_code} not found in registry")
            continue
        
        logger.info(f"Station: {station.city} ({station.station_code})")
        logger.info(f"Coordinates: {station.lat:.4f}°N, {station.lon:.4f}°E")
        logger.info(f"Timezone: {station.time_zone}")
        
        try:
            # Step 1: Fetch Zeus forecast
            logger.info("\n🌡️  Step 1: Fetching Zeus forecast...")
            start_utc, end_utc = time_utils.get_local_day_window_utc(today, station.time_zone)
            
            forecast = zeus_agent.fetch(
                lat=station.lat,
                lon=station.lon,
                start_utc=start_utc,
                hours=24,
                station_code=station.station_code,
            )
            logger.info(f"✅ Fetched {len(forecast.timeseries)} hourly forecasts")
            
            # Step 2: Discover market brackets
            logger.info("\n🔍 Step 2: Discovering Polymarket brackets...")
            brackets = discovery.list_temp_brackets(station.city, today, save_snapshot=True)
            
            if not brackets:
                logger.warning(f"No brackets found for {station.city}, skipping")
                continue
            
            logger.info(f"✅ Discovered {len(brackets)} brackets")
            
            # Step 3: Map Zeus probabilities
            logger.info("\n📊 Step 3: Mapping Zeus probabilities...")
            bracket_probs = mapper.map_daily_high(forecast, brackets)
            logger.info(f"✅ Mapped probabilities for {len(bracket_probs)} brackets")
            
            # Step 4: Get market probabilities
            logger.info("\n💰 Step 4: Fetching market probabilities...")
            for bp in bracket_probs:
                try:
                    bp.p_mkt = pricing.midprob(bp.bracket, save_snapshot=False)
                except Exception as e:
                    logger.warning(f"Failed to get price for {bp.bracket.name}: {e}")
                    bp.p_mkt = None
            
            filled_count = sum(1 for bp in bracket_probs if bp.p_mkt is not None)
            logger.info(f"✅ Got prices for {filled_count}/{len(bracket_probs)} brackets")
            
            # Step 5: Compute edge and size positions
            logger.info("\n⚖️  Step 5: Computing edge and sizing positions...")
            decisions = sizer.decide(
                bracket_probs,
                bankroll_usd=config.trading.daily_bankroll_cap,
                depth_data=None,  # TODO: Fetch depth in future enhancement
            )
            
            logger.info(f"✅ Generated {len(decisions)} trade decisions")
            
            if decisions:
                all_decisions.extend(decisions)
                
                # Display top decisions
                logger.info("\nTop trade opportunities:")
                for i, d in enumerate(sorted(decisions, key=lambda x: x.edge, reverse=True)[:3], 1):
                    logger.info(
                        f"  {i}. [{d.bracket.lower_F}-{d.bracket.upper_F}°F): "
                        f"edge={d.edge*100:.2f}%, size=${d.size_usd:.2f}"
                    )
            else:
                logger.info("No tradeable opportunities found (edge < minimum)")
            
        except Exception as e:
            logger.error(f"Error processing {station_code}: {e}", exc_info=True)
            continue
    
    # Step 6: Execute paper trades
    if all_decisions:
        logger.info(f"\n{'='*60}")
        logger.info(f"📝 Executing Paper Trades")
        logger.info(f"{'='*60}")
        
        csv_path = broker.place(all_decisions)
        
        # Summary
        total_size = sum(d.size_usd for d in all_decisions)
        avg_edge = sum(d.edge for d in all_decisions) / len(all_decisions)
        
        logger.info(f"\n✅ Paper trading complete!")
        logger.info(f"Total decisions: {len(all_decisions)}")
        logger.info(f"Total size: ${total_size:.2f}")
        logger.info(f"Average edge: {avg_edge*100:.2f}%")
        logger.info(f"Trades logged to: {csv_path}")
    else:
        logger.info("\n⚠️  No tradeable opportunities found across all stations")


def run_backtest(start_str: str, end_str: str, stations: list[str]) -> None:
    """Run backtest across date range.

    Args:
        start_str: Start date in YYYY-MM-DD format
        end_str: End date in YYYY-MM-DD format
        stations: List of station codes
    """
    from datetime import date
    from agents.backtester import Backtester
    
    logger.info(f"📈 Running backtest from {start_str} to {end_str}")
    logger.info(f"Stations: {', '.join(stations)}")
    
    # Parse dates
    try:
        start_date = date.fromisoformat(start_str)
        end_date = date.fromisoformat(end_str)
    except ValueError as e:
        logger.error(f"Invalid date format: {e}")
        logger.error("Expected format: YYYY-MM-DD")
        return
    
    # Validate date range (Zeus API only supports last 7 days)
    today = date.today()
    days_ago = (today - start_date).days
    
    if days_ago > 7:
        logger.warning(
            f"⚠️  Zeus API only supports last 7 days. "
            f"Start date {start_date} is {days_ago} days ago."
        )
        logger.warning("Results may be incomplete or fail.")
    
    # Initialize backtester
    backtester = Backtester(
        bankroll_usd=config.trading.daily_bankroll_cap,
        edge_min=config.trading.edge_min,
        fee_bp=config.trading.fee_bp,
        slippage_bp=config.trading.slippage_bp,
    )
    
    # Run backtest
    try:
        output_path = backtester.run(start_date, end_date, stations)
        
        logger.info(f"\n✅ Backtest complete!")
        logger.info(f"Results saved to: {output_path}")
        
    except Exception as e:
        logger.error(f"Backtest failed: {e}", exc_info=True)


if __name__ == "__main__":
    main()

