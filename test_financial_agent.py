"""
Test suite for Financial Analysis Agent.

This file contains comprehensive tests for the Financial Analysis Agent
including expense classification, period resolution, user memory, and bilingual support.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from src.agent.financial_agent import FinancialAnalysisAgent


class TestFinancialAnalysisAgent:
    """Test cases for the Financial Analysis Agent."""

    def setup_method(self):
        """Set up test fixtures."""
        self.agent = FinancialAnalysisAgent()

    @pytest.mark.asyncio
    async def test_expense_classification_english(self):
        """Test expense classification with English input."""
        confirmation = await self.agent.process_expense_confirmation(
            amount=100.0,
            currency="USD",
            date=None,
            merchant="Whole Foods",
            note="weekly groceries",
            user_id=1
        )

        assert confirmation["type"] == "expense_confirmation"
        assert confirmation["resolved_language"] == "en"
        assert confirmation["classification"]["category"] == "Groceries"
        assert confirmation["classification"]["is_necessary"] == True
        assert confirmation["classification"]["confidence"] > 0.5
        assert "Change it?" in confirmation["ui_confirmation_text"]

    @pytest.mark.asyncio
    async def test_expense_classification_spanish(self):
        """Test expense classification with Spanish input."""
        confirmation = await self.agent.process_expense_confirmation(
            amount=50.0,
            currency="ARS",
            date=None,
            merchant="Cine",
            note="película con amigos",
            user_id=1
        )

        assert confirmation["type"] == "expense_confirmation"
        assert confirmation["resolved_language"] == "es"
        assert confirmation["classification"]["category"] == "Leisure/Entertainment"
        assert confirmation["classification"]["is_necessary"] == False
        assert "¿Cambiar?" in confirmation["ui_confirmation_text"]

    @pytest.mark.asyncio
    async def test_user_memory_learning(self):
        """Test that user memory learns from corrections."""
        user_id = 1

        # Initial classification
        confirmation1 = await self.agent.process_expense_confirmation(
            amount=50.0,
            currency="USD",
            date=None,
            merchant="Starbucks",
            note="coffee",
            user_id=user_id
        )

        # Should classify as Dining/Delivery initially
        assert confirmation1["classification"]["category"] == "Dining/Delivery"
        assert confirmation1["classification"]["is_necessary"] == False

        # User corrects to Groceries and marks as necessary
        await self.agent.update_user_memory(user_id, "Starbucks", "Groceries", True)

        # Second expense at same merchant should use learned preferences
        confirmation2 = await self.agent.process_expense_confirmation(
            amount=30.0,
            currency="USD",
            date=None,
            merchant="Starbucks",
            note="breakfast",
            user_id=user_id
        )

        assert confirmation2["classification"]["category"] == "Groceries"
        assert confirmation2["classification"]["is_necessary"] == True
        assert confirmation2["classification"]["confidence"] == 0.95  # High confidence for learned

    def test_period_resolution_english(self):
        """Test period resolution with English expressions."""
        # Test "last month"
        start, end = self.agent._parse_period("last month", "en")
        expected_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if expected_start.month == 1:
            expected_start = expected_start.replace(year=expected_start.year - 1, month=12)
        else:
            expected_start = expected_start.replace(month=expected_start.month - 1)

        # Allow some tolerance for timing
        assert abs((start - expected_start).total_seconds()) < 60

        # Test "last 7 days"
        start, end = self.agent._parse_period("last 7 days", "en")
        # Should span approximately 7 days (accounting for the time component)
        total_seconds = (end - start).total_seconds()
        expected_seconds = 7 * 24 * 3600  # 7 days in seconds
        assert abs(total_seconds - expected_seconds) < 3600  # Allow 1 hour tolerance

    def test_period_resolution_spanish(self):
        """Test period resolution with Spanish expressions."""
        # Test "el mes pasado"
        start, end = self.agent._parse_period("el mes pasado", "es")
        expected_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if expected_start.month == 1:
            expected_start = expected_start.replace(year=expected_start.year - 1, month=12)
        else:
            expected_start = expected_start.replace(month=expected_start.month - 1)

        # Allow some tolerance for timing
        assert abs((start - expected_start).total_seconds()) < 60

        # Test "últimos 7 días"
        start, end = self.agent._parse_period("últimos 7 días", "es")
        # Should span approximately 7 days (accounting for the time component)
        total_seconds = (end - start).total_seconds()
        expected_seconds = 7 * 24 * 3600  # 7 days in seconds
        assert abs(total_seconds - expected_seconds) < 3600  # Allow 1 hour tolerance

    def test_category_mappings(self):
        """Test that category mappings are properly structured."""
        mappings = self.agent._category_mappings

        # Should have all required categories
        categories = [m.category for m in mappings]
        expected_categories = [
            "Fixed", "Groceries", "Transport", "Health", "Education", "Childcare",
            "Dining/Delivery", "Leisure/Entertainment", "Shopping", "Travel",
            "Taxes/Fees", "Debt/Loans", "Gifts/Donations", "Business", "Misc"
        ]

        for expected in expected_categories:
            assert expected in categories, f"Missing category: {expected}"

        # Should have proper bucket assignments
        buckets = set()
        for mapping in mappings:
            buckets.add(mapping.bucket)
            assert mapping.bucket in ["fixed", "variable_necessary", "discretionary"]

        assert len(buckets) == 3  # Should have all three buckets

    def test_budget_percentage_parsing(self):
        """Test budget percentage parsing from various formats."""
        # Test standard format
        percentages = self.agent._parse_budget_percentages("50% fixed, 30% necessary, 20% discretionary")
        assert percentages["fixed"] == 50.0
        assert percentages["variable_necessary"] == 30.0
        assert percentages["discretionary"] == 20.0

        # Test Spanish format
        percentages = self.agent._parse_budget_percentages("50% fijo, 30% necesario, 20% discrecional")
        assert percentages["fixed"] == 50.0
        assert percentages["variable_necessary"] == 30.0
        assert percentages["discretionary"] == 20.0

        # Test without percent signs
        percentages = self.agent._parse_budget_percentages("60 fixed 25 necessary 15 discretionary")
        assert percentages["fixed"] == 60.0
        assert percentages["variable_necessary"] == 25.0
        assert percentages["discretionary"] == 15.0

    @pytest.mark.asyncio
    async def test_budget_update(self):
        """Test budget update functionality."""
        user_id = 1

        budget_update = await self.agent.update_budget(
            "60% fixed, 25% necessary, 15% discretionary",
            user_id
        )

        assert budget_update["type"] == "budget_update"
        assert budget_update["normalized_percentages"]["fixed"] == 60.0
        assert budget_update["normalized_percentages"]["variable_necessary"] == 25.0
        assert budget_update["normalized_percentages"]["discretionary"] == 15.0

        # Verify memory was updated
        user_memory = await self.agent._get_user_memory(user_id)
        assert user_memory["budget_targets"]["fixed"] == 60.0

    @pytest.mark.asyncio
    async def test_budget_normalization(self):
        """Test budget percentage normalization when they don't sum to 100%."""
        user_id = 1

        # Percentages that sum to 110%
        budget_update = await self.agent.update_budget(
            "60% fixed, 30% necessary, 20% discretionary",
            user_id
        )

        # Should normalize to 100%
        normalized = budget_update["normalized_percentages"]
        total = sum(normalized.values())
        assert abs(total - 100.0) < 0.1  # Allow small rounding errors

        # Should have validation note
        assert len(budget_update["validation_notes"]) > 0
        assert "normalizing" in budget_update["validation_notes"][0].lower()

    def test_alternative_categories(self):
        """Test alternative category suggestions."""
        alternatives = self.agent._get_alternative_categories("Groceries")

        # Should return list of alternatives
        assert isinstance(alternatives, list)
        assert len(alternatives) <= 3  # Should limit to 3

        # Each alternative should have category and reason
        for alt in alternatives:
            assert "category" in alt
            assert "reason" in alt
            assert alt["category"] != "Groceries"  # Should not include current category

    def test_classification_confidence(self):
        """Test that classification confidence scores are reasonable."""
        # High confidence case (clear keyword match)
        classification = self.agent._classify_expense(
            "Whole Foods", "groceries for the week", {}
        )
        assert classification["confidence"] > 0.5

        # Low confidence case (ambiguous)
        classification = self.agent._classify_expense(
            "Unknown Store", "stuff", {}
        )
        assert classification["confidence"] < 0.5
        assert classification["category"] == "Misc"  # Should default to Misc

    def test_confirmation_text_generation(self):
        """Test confirmation text generation in both languages."""
        # English
        text_en = self.agent._generate_confirmation_text("Groceries", True, "en")
        assert "I detected Groceries (necessary)" in text_en
        assert "Change it?" in text_en

        # Spanish
        text_es = self.agent._generate_confirmation_text("Groceries", False, "es")
        assert "Detecté Groceries (no necesario)" in text_es
        assert "¿Cambiar?" in text_es


class TestAsyncFunctionality:
    """Test async functionality that requires event loop."""

    def setup_method(self):
        """Set up test fixtures."""
        self.agent = FinancialAnalysisAgent()

    @pytest.mark.asyncio
    async def test_full_expense_flow(self):
        """Test complete expense processing flow."""
        user_id = 999  # Use high ID to avoid conflicts

        # Process expense
        confirmation = await self.agent.process_expense_confirmation(
            amount=75.50,
            currency="USD",
            date=datetime(2025, 9, 15),
            merchant="Amazon",
            note="office supplies",
            user_id=user_id
        )

        # Verify structure
        assert confirmation["type"] == "expense_confirmation"
        assert confirmation["expense"]["amount"] == 75.50
        assert confirmation["expense"]["merchant"] == "Amazon"
        assert confirmation["expense"]["date"] == "2025-09-15"

        # Simulate user correction
        await self.agent.update_user_memory(
            user_id, "Amazon", "Business", True
        )

        # Second transaction should use learned preference
        confirmation2 = await self.agent.process_expense_confirmation(
            amount=25.0,
            currency="USD",
            date=None,
            merchant="Amazon",
            note="more supplies",
            user_id=user_id
        )

        assert confirmation2["classification"]["category"] == "Business"
        assert confirmation2["classification"]["is_necessary"] == True


# Test runner for standalone execution
async def run_tests():
    """Run tests manually for development."""
    test_agent = TestFinancialAnalysisAgent()
    test_agent.setup_method()

    print("🧪 Running Financial Analysis Agent Tests...")

    # Test expense classification
    print("Testing expense classification...")
    await test_agent.test_expense_classification_english()
    print("✅ English classification test passed")

    await test_agent.test_expense_classification_spanish()
    print("✅ Spanish classification test passed")

    # Test user memory
    print("Testing user memory...")
    await test_agent.test_user_memory_learning()
    print("✅ User memory test passed")

    # Test period resolution
    print("Testing period resolution...")
    test_agent.test_period_resolution_english()
    print("✅ English period resolution test passed")

    test_agent.test_period_resolution_spanish()
    print("✅ Spanish period resolution test passed")

    # Test budget functionality
    print("Testing budget management...")
    await test_agent.test_budget_update()
    print("✅ Budget update test passed")

    await test_agent.test_budget_normalization()
    print("✅ Budget normalization test passed")

    print("\n🎉 All tests passed! Financial Analysis Agent is working correctly.")


if __name__ == "__main__":
    # Run tests if executed directly
    asyncio.run(run_tests())
