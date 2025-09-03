from decimal import Decimal
from typing import Optional, Tuple

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


class ARSProvider:
    """Provider for USD/ARS exchange rates from various Argentine sources."""
    
    def __init__(self):
        self.session = httpx.AsyncClient(timeout=10.0)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def get_rate(self, source: str = "blue") -> Tuple[Optional[Decimal], Optional[str]]:
        """
        Get USD/ARS exchange rate from specified source.
        Available sources: 'blue', 'official', 'mep'
        """
        try:
            if source == "blue":
                return await self._get_blue_rate()
            elif source == "official":
                return await self._get_official_rate()
            elif source == "mep":
                return await self._get_mep_rate()
            else:
                return None, None
        except Exception as e:
            print(f"ARS provider error: {e}")
            return None, None
    
    async def _get_blue_rate(self) -> Tuple[Optional[Decimal], Optional[str]]:
        """Get blue dollar rate from dolarapi.com"""
        url = "https://dolarapi.com/v1/dolares/blue"
        
        response = await self.session.get(url)
        response.raise_for_status()
        
        data = response.json()
        if "venta" in data:
            rate = Decimal(str(data["venta"]))
            return rate, "dolarapi_blue"
        
        return None, None
    
    async def _get_official_rate(self) -> Tuple[Optional[Decimal], Optional[str]]:
        """Get official dollar rate from dolarapi.com"""
        url = "https://dolarapi.com/v1/dolares/oficial"
        
        response = await self.session.get(url)
        response.raise_for_status()
        
        data = response.json()
        if "venta" in data:
            rate = Decimal(str(data["venta"]))
            return rate, "dolarapi_official"
        
        return None, None
    
    async def _get_mep_rate(self) -> Tuple[Optional[Decimal], Optional[str]]:
        """Get MEP dollar rate from dolarapi.com"""
        url = "https://dolarapi.com/v1/dolares/bolsa"
        
        response = await self.session.get(url)
        response.raise_for_status()
        
        data = response.json()
        if "venta" in data:
            rate = Decimal(str(data["venta"]))
            return rate, "dolarapi_mep"
        
        return None, None
    
    async def close(self):
        await self.session.aclose()