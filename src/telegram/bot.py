import logging
from datetime import datetime
import json

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from aiogram.utils.markdown import hbold

from src.agent.agent import FinanceAgent
from src.agent.tools.db_tool import QueryBalancesInput, QueryMonthlyReportInput
from src.telegram.states import TransactionStates
from src.config import settings
from src.db.base import async_session_maker
from src.db.crud import UserCRUD

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher with state storage
storage = MemoryStorage()
bot = Bot(token=settings.telegram_bot_token)
dp = Dispatcher(storage=storage)
router = Router()

# Initialize finance agent
finance_agent = FinanceAgent()


async def setup_bot_commands():
    """Set up bot commands for the Telegram menu."""
    commands = [
        BotCommand(command="start", description="🎉 Welcome & getting started guide"),
        BotCommand(command="help", description="📚 Complete guide with examples"),
        BotCommand(command="balance", description="💰 Show account balances"),
        BotCommand(command="report", description="📊 Monthly financial report"),
    ]
    await bot.set_my_commands(commands)
    logger.info("Bot commands registered successfully")


async def ensure_user_exists(message: Message) -> int:
    """Ensure user exists in database and return user_id."""
    async with async_session_maker() as session:
        user = await UserCRUD.get_or_create(
            session,
            telegram_user_id=str(message.from_user.id),
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            username=message.from_user.username,
            language_code=message.from_user.language_code,
        )
        return user.id


@router.message(Command("start"))
async def start_command(message: Message) -> None:
    """Handle /start command."""
    try:
        logger.info(f"Start command received from user {message.from_user.id}")

        # Ensure user exists in database
        await ensure_user_exists(message)
        logger.info("User ensured in database")

        # Show comprehensive welcome message
        welcome_text = """🎉 <b>Welcome to your Personal Finance AI Agent!</b>

I'm your intelligent financial assistant that understands natural language in both English and Spanish. No complex commands needed - just talk to me naturally!

<b>🚀 Quick Start - Try These Examples:</b>

<b>💰 Record Income:</b>
• "I received 6000 USD salary via Deel"
• "Got paid $1500 freelance to my bank account"
• "Recibí 500k ARS en efectivo"

<b>💸 Record Expenses:</b>
• "Spent 150 ARS on groceries with cash"
• "Gasté $400 de MercadoPago en compras online"
• "Bought coffee for 5 USD from my wallet"

<b>🔄 Record Transfers:</b>
• "Transferred 1000 USD from Deel to AstroPay"
• "Moved $500 from checking to savings"

<b>💱 Record Currency Conversions:</b>
• "Converted 100 USDT to ARS at rate 1350"
• "Changed 500 USD to 680k ARS"

<b>🏦 How Accounts Work:</b>
✅ Just mention any account name - I'll create it automatically
✅ Examples: Deel, AstroPay, MercadoPago, Galicia, Cash, etc.
✅ Each account can hold multiple currencies (USD, ARS, BTC, etc.)
✅ Smart matching: "astropay" = "AstroPay", "galicia" = "Galicia"

<b>💰 Check Your Finances:</b>
• Type: "What's my balance?" or "¿Cuánto tengo?"
• Use: /balance (all accounts) or /balance AstroPay (specific account)
• Ask: "How much did I spend this week?" or "Show my expenses"

<b>📊 Generate Reports:</b>
• Use: /report (current month) or /report 2024-09 (specific month)
• Ask: "What was my biggest expense last month?"

<b>🌍 Multi-Currency &amp; Multi-Language:</b>
✅ Supports 15+ fiat currencies (USD, EUR, ARS, etc.)
✅ Supports 12+ cryptocurrencies (BTC, ETH, USDT, etc.)
✅ Automatic exchange rate fetching
✅ Speak English, Spanish, or mix both languages freely

<b>💡 Pro Tips:</b>
• Use "K" for thousands: "5K USD" = $5,000
• Be conversational: "I bought lunch today for about 20 bucks"
• Mix languages: "Gasté 50K ARS from my USD account"
• Natural dates work: "yesterday", "last week", "this month"

<b>🎯 Ready to Start?</b>
Just describe your first transaction naturally! For example:
• "I have 1000 USD in my checking account"
• "Tengo $50000 ARS en efectivo"
• "Got $2000 in my crypto wallet"

Type /help anytime for the complete guide! 📚"""

        await message.answer(welcome_text, parse_mode="HTML")
        logger.info("Start message sent successfully")

    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await message.answer("❌ Error processing start command. Please try again.")


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    """Handle /help command."""
    # Ensure user exists in database
    await ensure_user_exists(message)
    help_text = """<b>💰 Personal Finance AI Agent - Complete Guide</b>

<b>🎯 How It Works:</b>
I understand natural language in both English and Spanish. Just describe your financial activities conversationally - no need to learn specific commands!

<b>💳 Recording Transactions:</b>

<b>💰 Income Examples:</b>
• "I received 6000 USD salary via Deel"
• "Recibí $500 de freelance en mi cuenta"
• "Got paid 2500 ARS cash today"

<b>💸 Expense Examples:</b>
• "Spent 150 ARS on groceries with cash"
• "Gasté $400 de MercadoPago en compras"
• "Bought coffee for 5 USD from my wallet"

<b>🔄 Transfer Examples:</b>
• "Transferred 1000 USD from Deel to AstroPay"
• "Moved $500 from savings to checking"
• "Sent 200k ARS to my Galicia account"

<b>💱 Currency Conversion Examples:</b>
• "Converted 100 USDT to ARS at rate 1350"
• "Changed 500 USD to 680k ARS"
• "Exchanged 1 BTC for USDT at 45000"

<b>🏦 Account Management:</b>
• Accounts are automatically created when you mention them
• Supported types: Banks (Galicia, BBVA), Wallets (AstroPay, MercadoPago), Cash, Crypto
• Each account can hold multiple currencies
• Smart account name matching (e.g., "astropay" = "AstroPay")

<b>💰 Checking Balances:</b>

<b>Commands:</b>
• /balance - Show all account balances
• /balance AstroPay - Show specific account balance
• /balance Galicia - Show bank account balance

<b>Natural Language:</b>
• "What's my balance?"
• "How much do I have in AstroPay?"
• "Show my cash balance"
• "¿Cuánto tengo en Galicia?"

<b>📊 Reports &amp; Analysis:</b>

<b>Monthly Reports:</b>
• /report - Current month report
• /report 2024-08 - Specific month report
• Shows: Total income, expenses, net savings, largest transactions

<b>Query Examples:</b>
• "How much did I spend last week?"
• "What was my biggest expense in August?"
• "Show expenses between Sept 1 and 7"
• "¿Cuánto gasté el mes pasado?"
• "Show all my transactions this month"

<b>💱 Supported Currencies:</b>

<b>Fiat:</b> USD, EUR, GBP, ARS, BRL, CLP, COP, MXN, JPY, AUD, CAD, CHF
<b>Crypto:</b> BTC, ETH, USDT, USDC, DAI, BUSD, BNB, ADA, DOT, LINK

<b>🔄 Smart Features:</b>
✅ Automatic exchange rate fetching (including Blue Dollar for ARS)
✅ Multi-currency account support
✅ Bilingual support (English/Spanish)
✅ Smart currency symbol resolution ($ = USD or ARS based on context)
✅ Fuzzy account name matching
✅ Transaction confirmation system
✅ Pending transaction queue when rates unavailable

<b>📝 Pro Tips:</b>
• Use "K" for thousands: "5K USD" = $5,000
• Use "M" for millions: "1.5M ARS" = $1,500,000
• Natural dates work: "yesterday", "last week", "this month"
• Mix languages freely: "Gasté 400k ARS from my USD account"
• Be conversational: "I bought groceries today for about 150 pesos cash"

<b>🚀 Getting Started:</b>
1. Just start describing your transactions naturally
2. Accounts will be created automatically
3. Check your balance with /balance
4. Generate reports with /report
5. Ask me anything about your finances!

Type anything to get started! 💬"""
    await message.answer(help_text, parse_mode="HTML")


@router.message(Command("balance"))
async def balance_command(message: Message) -> None:
    """Handle /balance command."""
    try:
        # Ensure user exists in database
        user_id = await ensure_user_exists(message)

        # Extract account name from command args
        args = message.text.split(maxsplit=1)
        account_name = args[1] if len(args) > 1 else None

        balances = await finance_agent.db_tool.query_balances(
            QueryBalancesInput(account_name=account_name), user_id
        )

        if not balances:
            if account_name:
                await message.answer(f"❌ No balance found for account: {account_name}")
            else:
                await message.answer("❌ No balances found. Start by recording some transactions!")
            return

        response = finance_agent._format_balances(balances)
        await message.answer(response, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Error in balance command: {e}")
        await message.answer("❌ Error retrieving balances. Please try again.")


@router.message(Command("report"))
async def report_command(message: Message) -> None:
    """Handle /report command."""
    try:
        # Ensure user exists in database
        user_id = await ensure_user_exists(message)

        # Extract month/year from command args
        args = message.text.split(maxsplit=1)

        if len(args) > 1:
            date_str = args[1]
            try:
                date_parts = date_str.split("-")
                if len(date_parts) == 2:
                    year = int(date_parts[0])
                    month = int(date_parts[1])
                else:
                    raise ValueError("Invalid format")
            except (ValueError, IndexError):
                await message.answer("❌ Invalid date format. Use YYYY-MM (e.g., 2024-08)")
                return
        else:
            # Default to current month
            now = datetime.now()
            month = now.month
            year = now.year

        report = await finance_agent.db_tool.generate_monthly_report(
            QueryMonthlyReportInput(month=month, year=year), user_id
        )

        response = finance_agent._format_monthly_report(report)
        await message.answer(response, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Error in report command: {e}")
        await message.answer("❌ Error generating report. Please try again.")


@router.message(F.text)
async def process_text(message: Message, state: FSMContext) -> None:
    """Handle all other text messages."""
    try:
        # Ensure user exists in database
        user_id = await ensure_user_exists(message)

        # Show typing indicator
        await message.bot.send_chat_action(message.chat.id, "typing")

        # Process message with finance agent
        response, transaction_data = await finance_agent.process_message(message.text, user_id)

        # If this is a transaction that needs confirmation
        if transaction_data is not None:
            # Add user_id to transaction data
            transaction_data['user_id'] = user_id

            # Save transaction data in state
            await state.set_data(transaction_data)
            await state.set_state(TransactionStates.waiting_confirmation)

            # Create confirmation keyboard
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Confirmar", callback_data="confirm_transaction"),
                    InlineKeyboardButton(text="❌ Cancelar", callback_data="cancel_transaction")
                ]
            ])

            await message.answer(response, reply_markup=keyboard, parse_mode="HTML")
        else:
            # Regular response without confirmation
            if len(response) > 4000:
                for i in range(0, len(response), 4000):
                    await message.answer(response[i:i+4000], parse_mode="HTML")
            else:
                await message.answer(response, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await message.answer("❌ Sorry, I encountered an error processing your request. Please try again.")


@router.callback_query(F.data == "confirm_transaction")
async def confirm_transaction_callback(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle transaction confirmation."""
    try:
        # Get transaction data from state
        transaction_data = await state.get_data()

        if not transaction_data:
            await callback.answer("❌ No hay transacción pendiente")
            return

        # Confirm the transaction
        result = await finance_agent.confirm_transaction(transaction_data)

        # Clear state
        await state.clear()

        # Edit the message to show the result
        await callback.message.edit_text(result, reply_markup=None)
        await callback.answer("✅ Transacción confirmada")

    except Exception as e:
        logger.error(f"Error confirming transaction: {e}")
        await callback.answer("❌ Error al confirmar la transacción")
        await state.clear()


@router.callback_query(F.data == "cancel_transaction")
async def cancel_transaction_callback(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle transaction cancellation."""
    try:
        # Clear state
        await state.clear()

        # Edit the message
        await callback.message.edit_text(
            "❌ Transacción cancelada.\n\n"
            "Si algo estaba incorrecto, por favor describe la transacción nuevamente con más detalles.",
            reply_markup=None
        )
        await callback.answer("Transacción cancelada")

    except Exception as e:
        logger.error(f"Error canceling transaction: {e}")
        await callback.answer("❌ Error al cancelar")


# Register router
dp.include_router(router)


async def start_bot() -> None:
    """Start the Telegram bot."""
    logger.info("Starting Telegram bot...")

    # Set up bot commands
    await setup_bot_commands()

    await dp.start_polling(bot)


async def stop_bot() -> None:
    """Stop the Telegram bot."""
    logger.info("Stopping Telegram bot...")
    await bot.session.close()
