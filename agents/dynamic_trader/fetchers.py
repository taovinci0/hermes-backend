"""Just-in-time data fetching for dynamic trading.

Fetches Zeus forecasts and Polymarket prices with minimal staleness.
"""

from datetime import datetime, date, time
from zoneinfo import ZoneInfo
from typing import List, Tuple, Optional

from core.logger import logger
from core.registry import Station
from core.types import MarketBracket
from agents.zeus_forecast import ZeusForecastAgent, ZeusForecast
from venues.polymarket.discovery import PolyDiscovery
from venues.polymarket.pricing import PolyPricing
from venues.metar import METARService, MetarObservation


class DynamicFetcher:
    """Fetch Zeus forecasts and Polymarket prices just-in-time."""
    
    def __init__(self):
        """Initialize fetcher with API clients."""
        self.zeus = ZeusForecastAgent()
        self.discovery = PolyDiscovery()
        self.pricing = PolyPricing()
        self.metar = METARService()
    
    def fetch_zeus_jit(
        self,
        station: Station,
        event_day: date,
    ) -> ZeusForecast:
        """Fetch Zeus forecast for event day using LOCAL time.
        
        IMPORTANT: Zeus API expects LOCAL time, not UTC!
        - London: 2025-11-12T00:00:00+00:00 (local)
        - NYC: 2025-11-12T00:00:00-05:00 (local)
        
        Args:
            station: Weather station with timezone
            event_day: Event date (e.g., 2025-11-12)
        
        Returns:
            Fresh Zeus forecast
        
        Raises:
            Exception: If Zeus API call fails
        """
        # Get local midnight for the event day (NO UTC conversion!)
        local_midnight = datetime.combine(
            event_day,
            time(0, 0),
            tzinfo=ZoneInfo(station.time_zone)
        )
        
        logger.debug(
            f"Fetching Zeus for {station.city} {event_day} "
            f"(local start: {local_midnight.isoformat()})"
        )
        
        # Fetch using LOCAL time
        forecast = self.zeus.fetch(
            lat=station.lat,
            lon=station.lon,
            start_utc=local_midnight,  # Actually local, not UTC (param name is legacy)
            hours=24,
            station_code=station.station_code,
        )
        
        fetch_time = datetime.now(ZoneInfo("UTC"))
        logger.info(
            f"✅ Zeus: {len(forecast.timeseries)} points for {station.city} "
            f"(fetched: {fetch_time.strftime('%H:%M:%S')} UTC)"
        )
        
        return forecast
    
    def fetch_polymarket_jit(
        self,
        city: str,
        event_day: date,
    ) -> Tuple[List[MarketBracket], List[Optional[float]]]:
        """Fetch Polymarket brackets and current prices.
        
        Args:
            city: City name
            event_day: Event date
        
        Returns:
            (brackets, prices) - Lists of same length
            prices[i] may be None if fetch failed
        """
        fetch_time = datetime.now(ZoneInfo("UTC"))
        
        # Get brackets (discover markets)
        brackets = self.discovery.list_temp_brackets(
            city=city,
            date_local=event_day,
            save_snapshot=False,
        )
        
        if not brackets:
            logger.debug(f"No brackets available for {city} on {event_day}")
            return [], []
        
        # Get current prices for each bracket
        prices = []
        for bracket in brackets:
            try:
                p_mkt = self.pricing.midprob(bracket, save_snapshot=False)
                prices.append(p_mkt)
            except Exception as e:
                logger.warning(f"Failed to get price for {bracket.name}: {e}")
                prices.append(None)
        
        valid_count = sum(1 for p in prices if p is not None)
        logger.info(
            f"✅ Polymarket: {valid_count}/{len(brackets)} prices for {city} "
            f"(fetched: {fetch_time.strftime('%H:%M:%S')} UTC)"
        )
        
        return brackets, prices
    
    def check_open_events(
        self,
        city: str,
        event_day: date,
    ) -> bool:
        """Check if markets exist and are open for an event.
        
        Markets typically open 1-2 days before event day.
        
        Args:
            city: City name
            event_day: Event date
        
        Returns:
            True if open markets found, False otherwise
        """
        try:
            # Try to find event
            slugs = self.discovery._generate_event_slugs(city, event_day)
            
            for slug in slugs:
                event = self.discovery.get_event_by_slug(slug, save_snapshot=False)
                if event:
                    # Check if any markets are still open
                    markets = event.get('markets', [])
                    open_markets = [m for m in markets if not m.get('closed')]
                    
                    if open_markets:
                        logger.debug(
                            f"Found open event for {city} {event_day}: "
                            f"{len(open_markets)}/{len(markets)} markets open"
                        )
                        return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Error checking events for {city} {event_day}: {e}")
            return False
    
    def fetch_metar_jit(
        self,
        station: Station,
        event_day: date,
    ) -> List[MetarObservation]:
        """Fetch latest METAR observations for a station.
        
        Only fetches if event_day is today (METAR only has current data).
        Returns only NEW observations that haven't been seen before.
        
        Args:
            station: Weather station
            event_day: Event date (only fetches if today)
        
        Returns:
            List of NEW MetarObservation objects (empty if no new data)
        """
        # Only fetch METAR for today's events (METAR doesn't have future data)
        today = date.today()
        if event_day != today:
            logger.debug(f"Skipping METAR for {event_day} (not today, METAR only has current data)")
            return []
        
        try:
            # Fetch latest observations (last 24 hours)
            observations = self.metar.get_observations(
                station_code=station.station_code,
                event_date=event_day,
                hours=24,
                save_snapshot=False,
            )
            
            if observations:
                logger.debug(
                    f"✅ METAR: {len(observations)} observations for {station.city} "
                    f"(latest: {observations[-1].time.strftime('%H:%M')} UTC)"
                )
            
            return observations
            
        except Exception as e:
            logger.warning(f"Failed to fetch METAR for {station.city}: {e}")
            return []

