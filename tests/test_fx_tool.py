import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from src.agent.tools.fx_tool import FxTool


@pytest.fixture
def fx_tool():
    return FxTool()


@pytest.mark.asyncio
async def test_get_rate_success(fx_tool):
    """Test successful rate retrieval."""
    with patch('src.integrations.fx.service.fx_service.get_rate') as mock_get_rate:
        mock_get_rate.return_value = (Decimal("1350.00"), "coingecko")
        
        result = await fx_tool._arun("USDT", "ARS")
        
        assert "1350.00" in result
        assert "coingecko" in result
        assert "USDT/ARS" in result
        mock_get_rate.assert_called_once_with("USDT", "ARS")


@pytest.mark.asyncio
async def test_get_rate_not_available(fx_tool):
    """Test handling when rate is not available."""
    with patch('src.integrations.fx.service.fx_service.get_rate') as mock_get_rate:
        mock_get_rate.return_value = (None, None)
        
        result = await fx_tool._arun("INVALID", "CURRENCY")
        
        assert "not available" in result
        assert "INVALID/CURRENCY" in result


@pytest.mark.asyncio
async def test_get_rate_error(fx_tool):
    """Test error handling in rate retrieval."""
    with patch('src.integrations.fx.service.fx_service.get_rate') as mock_get_rate:
        mock_get_rate.side_effect = Exception("API Error")
        
        result = await fx_tool._arun("USD", "ARS")
        
        assert "Error fetching" in result


@pytest.mark.asyncio
async def test_get_rate_value_success(fx_tool):
    """Test get_rate_value method returns just the Decimal."""
    with patch('src.integrations.fx.service.fx_service.get_rate') as mock_get_rate:
        expected_rate = Decimal("1200.50")
        mock_get_rate.return_value = (expected_rate, "source")
        
        result = await fx_tool.get_rate_value("USD", "ARS")
        
        assert result == expected_rate
        assert isinstance(result, Decimal)


@pytest.mark.asyncio
async def test_get_rate_value_none(fx_tool):
    """Test get_rate_value returns None when rate unavailable."""
    with patch('src.integrations.fx.service.fx_service.get_rate') as mock_get_rate:
        mock_get_rate.return_value = (None, None)
        
        result = await fx_tool.get_rate_value("INVALID", "CURRENCY")
        
        assert result is None


@pytest.mark.asyncio
async def test_get_rate_value_exception(fx_tool):
    """Test get_rate_value returns None on exception."""
    with patch('src.integrations.fx.service.fx_service.get_rate') as mock_get_rate:
        mock_get_rate.side_effect = Exception("Network error")
        
        result = await fx_tool.get_rate_value("USD", "EUR")
        
        assert result is None


@pytest.mark.asyncio
async def test_common_currency_pairs():
    """Test common currency pair requests."""
    fx_tool = FxTool()
    
    test_pairs = [
        ("USD", "ARS"),
        ("USDT", "USD"),
        ("BTC", "USD"),
        ("EUR", "USD")
    ]
    
    for base, quote in test_pairs:
        with patch('src.integrations.fx.service.fx_service.get_rate') as mock_get_rate:
            mock_get_rate.return_value = (Decimal("100.00"), "mock_source")
            
            result = await fx_tool._arun(base, quote)
            
            assert f"{base}/{quote}" in result
            assert "100.00" in result
            assert "mock_source" in result