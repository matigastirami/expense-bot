import logging
from datetime import datetime
import json

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
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
    # Ensure user exists in database
    await ensure_user_exists(message)
    welcome_text = f"""
🤖 {hbold("Welcome to your Personal Finance AI Agent!")}

I can help you track your income, expenses, transfers, and currency conversions using natural language.

{hbold("Examples:")}
• "I received 6k USD salary via Deel"
• "I spent 400k ARS from my Galicia account"  
• "I transferred 1K USD to Astropay, received 992 USD"
• "I converted 10 USDT to ARS at 1350"

{hbold("Commands:")}
/balance - Show all account balances
/balance [account] - Show specific account balance
/report [YYYY-MM] - Monthly report
/help - Show this help message

Just type your transactions or questions in natural language!
"""
    await message.answer(welcome_text)


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    """Handle /help command."""
    # Ensure user exists in database
    await ensure_user_exists(message)
    help_text = f"""
{hbold("Personal Finance AI Agent Help")}

{hbold("Recording Transactions:")}
Just describe your financial activity naturally:
• "I got paid 5000 USD from my freelance client"
• "Bought groceries for 150 ARS cash"
• "Sent 2000 USD to my Astropay wallet"
• "Converted 50 USDT to ARS at rate 1400"

{hbold("Asking Questions:")}
• "What's my balance in [account name]?"
• "How much did I spend in August?"
• "Show my expenses between Sept 1 and 7"
• "What was my largest purchase last month?"
• "Show all my accounts"

{hbold("Commands:")}
/start - Welcome message
/balance - Show all balances
/balance [account] - Show specific account
/report [YYYY-MM] - Monthly report
/help - This help message

{hbold("Supported Currencies:")}
USD, ARS, USDT, USDC, BTC, ETH and more!

The AI will automatically:
✅ Create accounts when mentioned
✅ Fetch exchange rates when needed
✅ Keep accurate multi-currency balances
✅ Answer questions about your finances
"""
    await message.answer(help_text)


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
        await message.answer(response)
        
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
        await message.answer(response)
        
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
            
            await message.answer(response, reply_markup=keyboard, parse_mode="Markdown")
        else:
            # Regular response without confirmation
            if len(response) > 4000:
                for i in range(0, len(response), 4000):
                    await message.answer(response[i:i+4000])
            else:
                await message.answer(response)
            
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
    await dp.start_polling(bot)


async def stop_bot() -> None:
    """Stop the Telegram bot."""
    logger.info("Stopping Telegram bot...")
    await bot.session.close()