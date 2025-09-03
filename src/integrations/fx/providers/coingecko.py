from decimal import Decimal
from typing import Dict, Optional, Tuple

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


class CoinGeckoProvider:
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    # Map common crypto symbols to CoinGecko IDs
    CRYPTO_MAPPING = {
        "BTC": "bitcoin",
        "ETH": "ethereum", 
        "USDT": "tether",
        "USDC": "usd-coin",
        "DAI": "dai",
        "BUSD": "binance-usd",
    }
    
    # Supported fiat currencies
    FIAT_CURRENCIES = {"USD", "EUR", "ARS", "BRL"}
    
    def __init__(self):
        self.session = httpx.AsyncClient(timeout=10.0)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def get_rate(self, base: str, quote: str) -> Tuple[Optional[Decimal], Optional[str]]:
        """
        Get exchange rate from base currency to quote currency.
        Returns (rate, source) or (None, None) if not available.
        """
        try:
            base = base.upper()
            quote = quote.upper()
            
            # Handle crypto to fiat
            if base in self.CRYPTO_MAPPING and quote in self.FIAT_CURRENCIES:
                return await self._get_crypto_to_fiat_rate(base, quote)
            
            # Handle fiat to crypto
            elif base in self.FIAT_CURRENCIES and quote in self.CRYPTO_MAPPING:
                rate, source = await self._get_crypto_to_fiat_rate(quote, base)
                if rate:
                    return Decimal("1") / rate, source
                return None, None
            
            # Handle crypto to crypto
            elif base in self.CRYPTO_MAPPING and quote in self.CRYPTO_MAPPING:
                return await self._get_crypto_to_crypto_rate(base, quote)
            
            # Unsupported pair
            return None, None
            
        except Exception as e:
            print(f"CoinGecko API error: {e}")
            return None, None
    
    async def _get_crypto_to_fiat_rate(self, crypto: str, fiat: str) -> Tuple[Optional[Decimal], Optional[str]]:
        crypto_id = self.CRYPTO_MAPPING.get(crypto)
        if not crypto_id:
            return None, None
        
        fiat_lower = fiat.lower()
        url = f"{self.BASE_URL}/simple/price"
        params = {
            "ids": crypto_id,
            "vs_currencies": fiat_lower,
        }
        
        response = await self.session.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        if crypto_id in data and fiat_lower in data[crypto_id]:
            rate = Decimal(str(data[crypto_id][fiat_lower]))
            return rate, "coingecko"
        
        return None, None
    
    async def _get_crypto_to_crypto_rate(self, base_crypto: str, quote_crypto: str) -> Tuple[Optional[Decimal], Optional[str]]:
        # Get both cryptos in USD and calculate cross rate
        base_rate, _ = await self._get_crypto_to_fiat_rate(base_crypto, "USD")
        quote_rate, _ = await self._get_crypto_to_fiat_rate(quote_crypto, "USD")
        
        if base_rate and quote_rate:
            rate = base_rate / quote_rate
            return rate, "coingecko"
        
        return None, None
    
    async def close(self):
        await self.session.aclose()