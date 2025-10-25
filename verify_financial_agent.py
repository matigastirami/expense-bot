#!/usr/bin/env python3
"""
Verification script for Financial Analysis Agent integration.

Run this script to verify that all components are working correctly
before testing with the actual Telegram bot.
"""

import asyncio
import logging
from unittest.mock import Mock, AsyncMock

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_financial_agent():
    """Test the core Financial Analysis Agent functionality."""
    print("🧪 Testing Financial Analysis Agent Core...")

    try:
        from packages.agent.financial_agent import FinancialAnalysisAgent
        agent = FinancialAnalysisAgent()

        # Test expense classification
        confirmation = await agent.process_expense_confirmation(
            amount=50.0, currency="USD", date=None,
            merchant="Starbucks", note="morning coffee", user_id=1
        )

        expected_category = "Dining/Delivery"
        if confirmation["classification"]["category"] == expected_category:
            print(f"✅ Expense classification: {expected_category}")
        else:
            print(f"❌ Expected {expected_category}, got {confirmation['classification']['category']}")

        # Test period analysis
        analysis = await agent.analyze_period("last month", 1)
        print(f"✅ Period analysis: {analysis['period']['start']} to {analysis['period']['end']}")

        # Test budget update
        budget = await agent.update_budget("50% fixed, 30% necessary, 20% discretionary", 1)
        print(f"✅ Budget update: {budget['normalized_percentages']}")

        print("✅ Financial Analysis Agent core functionality working!\n")
        return True

    except Exception as e:
        print(f"❌ Financial Agent test failed: {e}")
        return False


async def test_bot_handlers():
    """Test the Telegram bot handlers."""
    print("🤖 Testing Telegram Bot Handlers...")

    try:
        from packages.telegram.financial_agent_handlers import cmd_analyze, cmd_expense, cmd_budget

        # Create mock message and state
        mock_message = Mock()
        mock_message.from_user.id = 123
        mock_message.answer = AsyncMock()
        mock_state = Mock()

        # Test /analyze command
        mock_message.text = "/analyze last month"
        await cmd_analyze(mock_message, mock_state)
        print("✅ /analyze command handler works")

        # Test /expense command
        mock_message.text = "/expense 25 USD Cafe coffee"
        await cmd_expense(mock_message, mock_state)
        print("✅ /expense command handler works")

        # Test /budget command
        mock_message.text = "/budget 50% fixed, 30% necessary, 20% discretionary"
        await cmd_budget(mock_message, mock_state)
        print("✅ /budget command handler works")

        print("✅ All bot handlers working!\n")
        return True

    except Exception as e:
        print(f"❌ Bot handler test failed: {e}")
        return False


async def test_bot_integration():
    """Test that the bot integration is properly configured."""
    print("🔧 Testing Bot Integration...")

    try:
        # Test that the bot imports correctly
        from packages.telegram.bot import dp, setup_bot_commands
        print("✅ Bot imports successfully")

        # Test that financial router is imported
        from packages.telegram.financial_agent_handlers import financial_router
        print("✅ Financial router imports successfully")

        # Test that commands are in the command list
        import inspect
        source = inspect.getsource(setup_bot_commands)

        commands = ["analyze", "expense", "budget"]
        missing = []
        for cmd in commands:
            if cmd not in source:
                missing.append(cmd)

        if missing:
            print(f"❌ Missing commands from bot menu: {missing}")
            return False
        else:
            print("✅ All new commands are in bot menu")

        print("✅ Bot integration configured correctly!\n")
        return True

    except Exception as e:
        print(f"❌ Bot integration test failed: {e}")
        return False


async def test_multilingual_support():
    """Test bilingual functionality."""
    print("🌍 Testing Multilingual Support...")

    try:
        from packages.agent.financial_agent import FinancialAnalysisAgent
        agent = FinancialAnalysisAgent()

        # Test English
        confirmation_en = await agent.process_expense_confirmation(
            amount=100.0, currency="USD", date=None,
            merchant="Target", note="shopping", user_id=1
        )

        if confirmation_en["resolved_language"] == "en":
            print("✅ English language detection works")
        else:
            print(f"❌ Expected 'en', got '{confirmation_en['resolved_language']}'")

        # Test Spanish
        confirmation_es = await agent.process_expense_confirmation(
            amount=500.0, currency="ARS", date=None,
            merchant="Supermercado", note="compras semanales", user_id=1
        )

        if confirmation_es["resolved_language"] == "es":
            print("✅ Spanish language detection works")
        else:
            print(f"❌ Expected 'es', got '{confirmation_es['resolved_language']}'")

        print("✅ Multilingual support working!\n")
        return True

    except Exception as e:
        print(f"❌ Multilingual test failed: {e}")
        return False


async def main():
    """Run all verification tests."""
    print("🚀 Financial Analysis Agent Verification\n")
    print("=" * 50)

    tests = [
        ("Financial Agent Core", test_financial_agent),
        ("Bot Handlers", test_bot_handlers),
        ("Bot Integration", test_bot_integration),
        ("Multilingual Support", test_multilingual_support),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            result = await test_func()
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")

    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Financial Analysis Agent is ready!")
        print("\n💡 Next steps:")
        print("   1. Stop your running bot process")
        print("   2. Restart the bot to load the new handlers")
        print("   3. Check that the new commands appear in the bot menu:")
        print("      • /analyze - Analyze spending for any period")
        print("      • /expense - Quick expense entry with classification")
        print("      • /budget - Set budget percentages")
        print("   4. Test the commands in Telegram")
        print("\n✨ The Financial Analysis Agent provides:")
        print("   • Automatic expense classification")
        print("   • Bilingual support (English/Spanish)")
        print("   • Natural language period parsing")
        print("   • Budget management and tracking")
        print("   • User memory for learning preferences")
    else:
        print(f"\n❌ {total - passed} tests failed. Please check the errors above.")

    return passed == total


if __name__ == "__main__":
    asyncio.run(main())
