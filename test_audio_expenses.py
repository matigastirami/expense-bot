#!/usr/bin/env python3
"""
Test suite for audio expense functionality.

This file tests the voice message transcription and expense parsing capabilities.
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.telegram.financial_agent_handlers import _parse_voice_expense


class TestVoiceExpenseParsing:
    """Test cases for voice expense parsing."""

    @pytest.mark.asyncio
    async def test_simple_expense_english(self):
        """Test simple English expense parsing."""
        transcription = "I spent 50 dollars at Starbucks for coffee"
        result = await _parse_voice_expense(transcription, 1)

        assert result is not None
        assert result["amount"] == 50.0
        assert result["currency"] == "USD"
        assert "starbucks" in result["merchant"].lower()
        assert "coffee" in result["note"].lower()

    @pytest.mark.asyncio
    async def test_simple_expense_spanish(self):
        """Test simple Spanish expense parsing."""
        transcription = "Gasté 500 pesos en el supermercado para comida"
        result = await _parse_voice_expense(transcription, 1)

        assert result is not None
        assert result["amount"] == 500.0
        assert result["currency"] == "ARS"
        assert "supermercado" in result["merchant"].lower()
        assert "comida" in result["note"].lower()

    @pytest.mark.asyncio
    async def test_amount_with_k_multiplier(self):
        """Test parsing amounts with 'k' multiplier."""
        transcription = "I paid 5k USD for the new laptop"
        result = await _parse_voice_expense(transcription, 1)

        assert result is not None
        assert result["amount"] == 5000.0
        assert result["currency"] == "USD"
        assert "laptop" in result["merchant"].lower()

    @pytest.mark.asyncio
    async def test_different_currency_formats(self):
        """Test various currency format recognition."""
        test_cases = [
            ("50 USD at store", 50.0, "USD"),
            ("25 euros for lunch", 25.0, "EUR"),
            ("100 pesos cash", 100.0, "ARS"),
            ("$30 for groceries", 30.0, "USD"),
            ("0.01 BTC payment", 0.01, "BTC"),
        ]

        for transcription, expected_amount, expected_currency in test_cases:
            result = await _parse_voice_expense(transcription, 1)

            assert result is not None, f"Failed to parse: {transcription}"
            assert result["amount"] == expected_amount
            assert result["currency"] == expected_currency

    @pytest.mark.asyncio
    async def test_no_amount_found(self):
        """Test handling when no amount is found."""
        transcription = "I went to the store today"
        result = await _parse_voice_expense(transcription, 1)

        assert result is None

    @pytest.mark.asyncio
    async def test_merchant_extraction(self):
        """Test merchant name extraction."""
        test_cases = [
            ("50 USD at McDonald's", "mcdonald's"),
            ("Bought coffee at Starbucks for 5 dollars", "starbucks"),
            ("25 pesos en Cafe Martinez", "cafe martinez"),
            ("Spent 100 ARS grocery shopping", "grocery"),
        ]

        for transcription, expected_merchant in test_cases:
            result = await _parse_voice_expense(transcription, 1)

            assert result is not None
            assert expected_merchant.lower() in result["merchant"].lower()

    @pytest.mark.asyncio
    async def test_complex_expense_description(self):
        """Test parsing complex expense descriptions."""
        transcription = "I bought lunch for 25 dollars at the Italian restaurant downtown for my birthday celebration"
        result = await _parse_voice_expense(transcription, 1)

        assert result is not None
        assert result["amount"] == 25.0
        assert result["currency"] == "USD"
        assert "italian" in result["merchant"].lower() or "restaurant" in result["merchant"].lower()


class TestAudioTranscriptionService:
    """Test cases for the audio transcription service."""

    def test_service_initialization(self):
        """Test that the service initializes correctly."""
        from src.services.audio_transcription import AudioTranscriptionService

        # Test with no API key
        service = AudioTranscriptionService(openai_api_key=None)
        assert service.api_key is None

        # Test with API key
        service = AudioTranscriptionService(openai_api_key="test_key")
        assert service.api_key == "test_key"

    @pytest.mark.asyncio
    async def test_transcription_without_api_key(self):
        """Test transcription fails gracefully without API key."""
        from src.services.audio_transcription import AudioTranscriptionService

        service = AudioTranscriptionService(openai_api_key=None)
        result = await service.transcribe_voice_message("dummy_path")

        assert result is None


async def test_voice_parsing_examples():
    """Test various voice parsing examples manually."""
    print("🎤 Testing Voice Expense Parsing Examples")
    print("=" * 50)

    test_phrases = [
        # English examples
        "I spent 50 dollars at Starbucks for coffee",
        "Paid 25 USD for lunch at McDonald's",
        "Bought groceries for 150 dollars at Whole Foods",
        "5k USD for new laptop",
        "$30 gas station fill-up",

        # Spanish examples
        "Gasté 500 pesos en el supermercado",
        "Pagué 1000 ARS en la farmacia para medicinas",
        "Compré café por 200 pesos",
        "50k ARS en el shopping",

        # Mixed/complex examples
        "Coffee 5 dollars Starbucks morning",
        "Restaurant bill 80 euros dinner",
        "Grocery shopping 200 ARS cash",
    ]

    for phrase in test_phrases:
        try:
            result = await _parse_voice_expense(phrase, 1)

            if result:
                print(f"✅ '{phrase}'")
                print(f"   → {result['amount']} {result['currency']} at {result['merchant']}")
                if result['note']:
                    print(f"   → Note: {result['note']}")
            else:
                print(f"❌ '{phrase}' → Could not parse")

        except Exception as e:
            print(f"🔥 '{phrase}' → Error: {e}")

        print()


async def main():
    """Run audio expense tests."""
    print("🎤 Audio Expense Entry - Test Suite")
    print("=" * 50)

    # Test voice parsing examples
    await test_voice_parsing_examples()

    print("=" * 50)
    print("📋 Implementation Summary:")
    print()
    print("🎯 Audio Expense Entry Features:")
    print("• 🎤 Voice message transcription using OpenAI Whisper API")
    print("• 🌍 Bilingual support (English/Spanish)")
    print("• 💰 Smart amount and currency extraction")
    print("• 🏪 Merchant name detection")
    print("• 📝 Contextual note parsing")
    print("• ✅ Same confirmation flow as text expenses")
    print()
    print("💡 Usage Instructions:")
    print("1. Set OPENAI_API_KEY environment variable")
    print("2. Restart the bot to load audio handlers")
    print("3. Send voice messages describing expenses")
    print("4. Bot will transcribe and parse automatically")
    print()
    print("📱 Example Voice Messages:")
    print("• \"I spent 50 dollars at Starbucks for coffee\"")
    print("• \"Gasté 500 pesos en el supermercado\"")
    print("• \"Paid 25 euros for lunch at McDonald's\"")
    print("• \"5k USD for new laptop\"")
    print()
    print("⚙️ Technical Details:")
    print("• Uses OpenAI Whisper API for transcription")
    print("• Regex patterns for amount/currency extraction")
    print("• Natural language processing for merchant detection")
    print("• Supports currencies: USD, ARS, EUR, BTC, USDT")
    print("• Handles 'k' multipliers (5k = 5000)")
    print("• Graceful fallback when API key not configured")


if __name__ == "__main__":
    asyncio.run(main())
