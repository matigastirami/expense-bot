from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, Optional, Tuple
import os

from libs.db.base import async_session_maker
from libs.db.crud import ExchangeRateCRUD
from libs.integrations.fx.providers.ars_sources import ARSProvider
from libs.integrations.fx.providers.coingecko import CoinGeckoProvider


class FXService:
    def __init__(self):
        self.coingecko = CoinGeckoProvider()
        self.ars_provider = ARSProvider()
        self.cache: Dict[str, Tuple[Decimal, str, datetime]] = {}
        self.cache_duration = timedelta(minutes=5)  # 5-minute in-memory cache

    async def get_rate(self, base: str, quote: str) -> Tuple[Optional[Decimal], Optional[str]]:
        """
        Get exchange rate from base currency to quote currency.
        Returns (rate, source) or (None, None) if not available.
        """
        pair = f"{base.upper()}/{quote.upper()}"

        # Check in-memory cache first
        if pair in self.cache:
            rate, source, timestamp = self.cache[pair]
            current_time = datetime.now(timezone.utc)
            if current_time - timestamp < self.cache_duration:
                return rate, source

        # Check database cache (last 1 hour)
        async with async_session_maker() as session:
            db_rate = await ExchangeRateCRUD.get_latest_rate(session, pair)
            if db_rate and datetime.now(timezone.utc) - db_rate.fetched_at < timedelta(hours=1):
                self.cache[pair] = (db_rate.value, db_rate.source, db_rate.fetched_at)
                return db_rate.value, db_rate.source

        # Fetch fresh rate
        rate, source = await self._fetch_fresh_rate(base, quote)

        if rate and source:
            # Cache in memory
            timestamp = datetime.now(timezone.utc)
            self.cache[pair] = (rate, source, timestamp)

            # Cache in database
            async with async_session_maker() as session:
                await ExchangeRateCRUD.create(session, pair, rate, source, timestamp)

            return rate, source

        return None, None

    async def _fetch_fresh_rate(self, base: str, quote: str) -> Tuple[Optional[Decimal], Optional[str]]:
        """Fetch fresh exchange rate from external providers."""
        base_upper = base.upper()
        quote_upper = quote.upper()

        # Get ARS source from environment or use default
        ars_source = os.getenv("ARS_SOURCE", "blue")

        # Handle USD/ARS specifically
        if base_upper == "USD" and quote_upper == "ARS":
            return await self.ars_provider.get_rate(ars_source)

        # Handle ARS/USD (inverse)
        elif base_upper == "ARS" and quote_upper == "USD":
            rate, source = await self.ars_provider.get_rate(ars_source)
            if rate:
                return Decimal("1") / rate, source
            return None, None

        # Handle crypto and other currencies via CoinGecko
        else:
            return await self.coingecko.get_rate(base, quote)

    async def close(self):
        """Close all provider connections."""
        await self.coingecko.close()
        await self.ars_provider.close()


# Global FX service instance
fx_service = FXService()
