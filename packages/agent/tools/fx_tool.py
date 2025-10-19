from decimal import Decimal
from typing import Optional

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from src.integrations.fx.service import fx_service


class GetRateInput(BaseModel):
    base: str = Field(..., description="Base currency code (e.g., USD, USDT)")
    quote: str = Field(..., description="Quote currency code (e.g., ARS, USD)")


class FxTool(BaseTool):
    name: str = "fx_tool"
    description: str = "Foreign exchange tool for fetching real-time exchange rates between currencies including fiat, crypto, and stablecoins"
    args_schema: type = GetRateInput
    
    def _run(self, base: str, quote: str) -> str:
        # Synchronous wrapper - not used in async context
        return "Use async version"
    
    async def _arun(self, base: str, quote: str) -> str:
        """Get exchange rate from base currency to quote currency."""
        try:
            rate, source = await fx_service.get_rate(base, quote)
            
            if rate and source:
                return f"Exchange rate {base.upper()}/{quote.upper()}: {rate} (source: {source})"
            else:
                return f"Exchange rate not available for {base.upper()}/{quote.upper()}"
        
        except Exception as e:
            return f"Error fetching exchange rate: {str(e)}"
    
    async def get_rate_value(self, base: str, quote: str) -> Optional[Decimal]:
        """Get just the rate value without formatting."""
        try:
            rate, _ = await fx_service.get_rate(base, quote)
            return rate
        except Exception:
            return None