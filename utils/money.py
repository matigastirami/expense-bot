from decimal import Decimal, ROUND_HALF_UP
from typing import Optional


def quantize_money(amount: Decimal, currency: str) -> Decimal:
    """
    Quantize monetary amount based on currency precision.
    Most fiat currencies use 2 decimal places.
    Crypto currencies may use more precision.
    """
    if currency.upper() in ["BTC", "ETH"]:
        # High precision for major cryptos
        return amount.quantize(Decimal("0.00000001"))
    elif currency.upper() in ["USDT", "USDC", "DAI", "BUSD"]:
        # Stablecoins typically use 6 decimals but we'll use 2 for display
        return amount.quantize(Decimal("0.01"))
    else:
        # Standard fiat precision
        return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def parse_amount(amount_str: str) -> Optional[Decimal]:
    """
    Parse amount string to Decimal, handling common formats.
    Examples: "1,000.50", "1000.50", "1K", "1k", "1M"
    """
    if not amount_str:
        return None
    
    # Clean up the string
    amount_str = amount_str.strip().upper()
    
    # Handle K/M suffixes
    multiplier = Decimal("1")
    if amount_str.endswith("K"):
        multiplier = Decimal("1000")
        amount_str = amount_str[:-1]
    elif amount_str.endswith("M"):
        multiplier = Decimal("1000000")
        amount_str = amount_str[:-1]
    
    # Remove commas
    amount_str = amount_str.replace(",", "")
    
    try:
        amount = Decimal(amount_str) * multiplier
        return amount if amount > 0 else None
    except (ValueError, TypeError):
        return None


def format_money(amount: Decimal, currency: str) -> str:
    """Format money amount for display."""
    quantized = quantize_money(amount, currency)
    
    # Format with commas for thousands
    if quantized >= Decimal("1000"):
        return f"{quantized:,.2f}"
    else:
        return str(quantized)


def is_crypto_currency(currency: str) -> bool:
    """Check if currency is a cryptocurrency."""
    crypto_currencies = {
        "BTC", "ETH", "USDT", "USDC", "DAI", "BUSD", 
        "BNB", "ADA", "DOT", "LINK", "UNI", "AAVE"
    }
    return currency.upper() in crypto_currencies


def is_fiat_currency(currency: str) -> bool:
    """Check if currency is fiat."""
    fiat_currencies = {
        "USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF",
        "ARS", "BRL", "CLP", "COP", "MXN", "PEN", "UYU"
    }
    return currency.upper() in fiat_currencies