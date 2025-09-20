"""
Telegram bot handlers for Financial Analysis Agent integration.

This module provides the Telegram bot interface for the Financial Analysis Agent,
including commands, callback handlers, and interactive confirmation flows.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.markdown import hbold, hcode

from src.agent.financial_agent import FinancialAnalysisAgent
from src.db.base import async_session_maker
from src.db.crud import UserCRUD, TransactionCRUD, AccountCRUD
from src.db.models import TransactionType, AccountType
from src.utils.language import detect_language, Messages
from src.telegram.states import TransactionStates

logger = logging.getLogger(__name__)

# Initialize router and agent
financial_router = Router()
financial_agent = FinancialAnalysisAgent()

# Store pending confirmations (in production, use Redis or database)
pending_confirmations: Dict[str, Dict[str, Any]] = {}


@financial_router.message(Command("analyze"))
async def cmd_analyze(message: Message, state: FSMContext):
    """Handle /analyze command for financial analysis."""
    try:
        # Get user from database
        async with async_session_maker() as session:
            user = await UserCRUD.get_by_telegram_id(session, str(message.from_user.id))
            if not user:
                await message.answer("❌ User not found. Please use /start first.")
                return

        # Extract period from command arguments
        args = message.text.split()[1:] if message.text else []
        period_text = " ".join(args) if args else "last month"

        # Generate analysis
        analysis = await financial_agent.analyze_period(period_text, user.id)

        # Format response
        response = _format_analysis_response(analysis)
        await message.answer(response, parse_mode="HTML")

        # Send recommendations if any
        if analysis["recommendations"]:
            rec_text = _format_recommendations(analysis["recommendations"], analysis["resolved_language"])
            await message.answer(rec_text, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Error in analyze command: {e}")
        language = detect_language(message.text or "")
        error_msg = Messages.get("error", "general_error", language, error=str(e))
        await message.answer(error_msg)


@financial_router.message(Command("expense"))
async def cmd_expense(message: Message, state: FSMContext):
    """Handle /expense command for quick expense entry."""
    try:
        # Get user from database
        async with async_session_maker() as session:
            user = await UserCRUD.get_by_telegram_id(session, str(message.from_user.id))
            if not user:
                await message.answer("❌ User not found. Please use /start first.")
                return

        # Parse command arguments
        args = message.text.split()[1:] if message.text else []
        if len(args) < 3:
            language = detect_language(message.text or "")
            if language == "es":
                await message.answer("Uso: /expense <cantidad> <moneda> <comercio> [descripción]\nEjemplo: /expense 50 USD Starbucks café de la mañana")
            else:
                await message.answer("Usage: /expense <amount> <currency> <merchant> [description]\nExample: /expense 50 USD Starbucks morning coffee")
            return

        amount = float(args[0])
        currency = args[1].upper()
        merchant = args[2]
        note = " ".join(args[3:]) if len(args) > 3 else ""

        # Process expense confirmation
        confirmation = await financial_agent.process_expense_confirmation(
            amount=amount,
            currency=currency,
            date=None,  # Use today
            merchant=merchant,
            note=note,
            user_id=user.id
        )

        # Store confirmation for callback
        confirmation_id = f"{user.id}_{int(datetime.now().timestamp())}"
        pending_confirmations[confirmation_id] = {
            "confirmation": confirmation,
            "user_id": user.id
        }

        # Send confirmation message with buttons
        keyboard = _build_expense_confirmation_keyboard(confirmation_id, confirmation)
        response = _format_expense_confirmation(confirmation)

        await message.answer(response, reply_markup=keyboard, parse_mode="HTML")

    except ValueError:
        language = detect_language(message.text or "")
        error_msg = Messages.get("error", "validation_error", language)
        await message.answer(error_msg)
    except Exception as e:
        logger.error(f"Error in expense command: {e}")
        language = detect_language(message.text or "")
        error_msg = Messages.get("error", "general_error", language, error=str(e))
        await message.answer(error_msg)


@financial_router.message(Command("budget"))
async def cmd_budget(message: Message, state: FSMContext):
    """Handle /budget command for budget management."""
    try:
        # Get user from database
        async with async_session_maker() as session:
            user = await UserCRUD.get_by_telegram_id(session, str(message.from_user.id))
            if not user:
                await message.answer("❌ User not found. Please use /start first.")
                return

        # Extract budget text from command arguments
        args = message.text.split()[1:] if message.text else []
        if not args:
            language = detect_language(message.text or "")
            if language == "es":
                await message.answer("Uso: /budget <porcentajes>\nEjemplo: /budget 50% fijo, 30% necesario, 20% discrecional")
            else:
                await message.answer("Usage: /budget <percentages>\nExample: /budget 50% fixed, 30% necessary, 20% discretionary")
            return

        budget_text = " ".join(args)

        # Update budget
        budget_update = await financial_agent.update_budget(budget_text, user.id)

        # Format response
        response = _format_budget_response(budget_update)
        await message.answer(response, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Error in budget command: {e}")
        language = detect_language(message.text or "")
        error_msg = Messages.get("error", "general_error", language, error=str(e))
        await message.answer(error_msg)


@financial_router.callback_query(F.data.startswith("expense_"))
async def handle_expense_callback(callback: CallbackQuery):
    """Handle expense confirmation callbacks."""
    try:
        data_parts = callback.data.split("_")
        action = data_parts[1]  # confirm, category, necessity
        confirmation_id = data_parts[2]

        if confirmation_id not in pending_confirmations:
            await callback.answer("❌ Confirmation expired. Please try again.")
            return

        pending_data = pending_confirmations[confirmation_id]
        confirmation = pending_data["confirmation"]
        user_id = pending_data["user_id"]

        if action == "confirm":
            # Create the transaction
            await _create_confirmed_transaction(confirmation, user_id)

            # Send success message
            language = confirmation["resolved_language"]
            expense = confirmation["expense"]
            if language == "es":
                success_msg = f"✅ Gasto registrado: -{expense['amount']:,.0f} {expense['currency']} en {expense['merchant']}"
            else:
                success_msg = f"✅ Expense registered: -{expense['amount']:,.0f} {expense['currency']} at {expense['merchant']}"

            await callback.message.edit_text(success_msg, parse_mode="HTML")
            await callback.answer("✅ Transaction confirmed!")

            # Clean up
            del pending_confirmations[confirmation_id]

        elif action == "category":
            # Show category selection
            alternatives = confirmation["classification"]["alternatives"]
            keyboard = _build_category_selection_keyboard(confirmation_id, alternatives)

            language = confirmation["resolved_language"]
            prompt = "Select category:" if language == "en" else "Selecciona categoría:"

            await callback.message.edit_reply_markup(reply_markup=keyboard)
            await callback.answer(prompt)

        elif action == "necessity":
            # Toggle necessity flag
            current_necessity = confirmation["classification"]["is_necessary"]
            confirmation["classification"]["is_necessary"] = not current_necessity

            # Update UI text
            new_text = _format_expense_confirmation(confirmation)
            keyboard = _build_expense_confirmation_keyboard(confirmation_id, confirmation)

            await callback.message.edit_text(new_text, reply_markup=keyboard, parse_mode="HTML")
            await callback.answer("✅ Necessity updated!")

        elif action.startswith("setcat"):
            # Set specific category
            category = action.replace("setcat", "").replace("_", " ")
            confirmation["classification"]["category"] = category

            # Update UI
            new_text = _format_expense_confirmation(confirmation)
            keyboard = _build_expense_confirmation_keyboard(confirmation_id, confirmation)

            await callback.message.edit_text(new_text, reply_markup=keyboard, parse_mode="HTML")
            await callback.answer(f"✅ Category set to {category}")

        elif action == "cancel":
            # Cancel the transaction
            language = confirmation["resolved_language"]
            cancel_msg = "❌ Transaction cancelled." if language == "en" else "❌ Transacción cancelada."

            await callback.message.edit_text(cancel_msg)
            await callback.answer("Transaction cancelled")

            # Clean up
            del pending_confirmations[confirmation_id]

    except Exception as e:
        logger.error(f"Error in expense callback: {e}")
        await callback.answer("❌ Error processing request")


def _build_expense_confirmation_keyboard(confirmation_id: str, confirmation: Dict[str, Any]) -> InlineKeyboardMarkup:
    """Build keyboard for expense confirmation."""
    language = confirmation["resolved_language"]

    buttons = [
        [
            InlineKeyboardButton(
                text="✅ Confirm" if language == "en" else "✅ Confirmar",
                callback_data=f"expense_confirm_{confirmation_id}"
            ),
            InlineKeyboardButton(
                text="🏷️ Category" if language == "en" else "🏷️ Categoría",
                callback_data=f"expense_category_{confirmation_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔄 Toggle Necessity" if language == "en" else "🔄 Cambiar Necesidad",
                callback_data=f"expense_necessity_{confirmation_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Cancel" if language == "en" else "❌ Cancelar",
                callback_data=f"expense_cancel_{confirmation_id}"
            )
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _build_category_selection_keyboard(confirmation_id: str, alternatives: list) -> InlineKeyboardMarkup:
    """Build keyboard for category selection."""
    buttons = []

    for alt in alternatives:
        category = alt["category"]
        # Replace spaces with underscores for callback data
        callback_category = category.replace(" ", "_")
        buttons.append([
            InlineKeyboardButton(
                text=f"🏷️ {category}",
                callback_data=f"expense_setcat{callback_category}_{confirmation_id}"
            )
        ])

    # Add back button
    buttons.append([
        InlineKeyboardButton(
            text="⬅️ Back",
            callback_data=f"expense_back_{confirmation_id}"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _format_expense_confirmation(confirmation: Dict[str, Any]) -> str:
    """Format expense confirmation message."""
    expense = confirmation["expense"]
    classification = confirmation["classification"]
    language = confirmation["resolved_language"]

    necessity_text = {
        "en": "necessary" if classification["is_necessary"] else "not necessary",
        "es": "necesario" if classification["is_necessary"] else "no necesario"
    }

    confidence_text = f"({classification['confidence']:.0%})"

    if language == "es":
        return f"""
🔔 <b>Confirmación de Gasto</b>

<b>Monto:</b> {expense['amount']:,.0f} {expense['currency']}
<b>Comercio:</b> {expense['merchant']}
<b>Descripción:</b> {expense['note'] or 'N/A'}
<b>Fecha:</b> {expense['date']}

<b>Categoría:</b> {classification['category']} {confidence_text}
<b>Necesidad:</b> {necessity_text[language]}

¿Confirmar esta transacción?
"""
    else:
        return f"""
🔔 <b>Expense Confirmation</b>

<b>Amount:</b> {expense['amount']:,.0f} {expense['currency']}
<b>Merchant:</b> {expense['merchant']}
<b>Description:</b> {expense['note'] or 'N/A'}
<b>Date:</b> {expense['date']}

<b>Category:</b> {classification['category']} {confidence_text}
<b>Necessity:</b> {necessity_text[language]}

Confirm this transaction?
"""


def _format_analysis_response(analysis: Dict[str, Any]) -> str:
    """Format financial analysis response."""
    language = analysis["resolved_language"]
    period = analysis["period"]
    totals = analysis["totals"]

    if language == "es":
        header = f"📊 <b>Análisis Financiero</b>\n<b>Período:</b> {period['start']} a {period['end']}\n"
    else:
        header = f"📊 <b>Financial Analysis</b>\n<b>Period:</b> {period['start']} to {period['end']}\n"

    # Add human summary
    summary = analysis["human_summary"]

    # Budget adherence
    targets = analysis["budget_targets_pct"]
    actual = analysis["budget_actual_pct"]

    if language == "es":
        budget_section = "\n<b>📋 Adherencia al Presupuesto:</b>\n"
        budget_section += f"• Fijo: {actual['fixed']:.1f}% (objetivo {targets['fixed']:.1f}%)\n"
        budget_section += f"• Variable necesario: {actual['variable_necessary']:.1f}% (objetivo {targets['variable_necessary']:.1f}%)\n"
        budget_section += f"• Discrecional: {actual['discretionary']:.1f}% (objetivo {targets['discretionary']:.1f}%)\n"
    else:
        budget_section = "\n<b>📋 Budget Adherence:</b>\n"
        budget_section += f"• Fixed: {actual['fixed']:.1f}% (target {targets['fixed']:.1f}%)\n"
        budget_section += f"• Variable necessary: {actual['variable_necessary']:.1f}% (target {targets['variable_necessary']:.1f}%)\n"
        budget_section += f"• Discretionary: {actual['discretionary']:.1f}% (target {targets['discretionary']:.1f}%)\n"

    return header + "\n" + summary + budget_section


def _format_recommendations(recommendations: list, language: str) -> str:
    """Format recommendations section."""
    if not recommendations:
        return ""

    if language == "es":
        header = "💡 <b>Recomendaciones:</b>\n\n"
    else:
        header = "💡 <b>Recommendations:</b>\n\n"

    formatted_recs = []
    for i, rec in enumerate(recommendations, 1):
        rec_text = f"<b>{i}. {rec['title']}</b>\n"
        rec_text += f"   {rec['rationale']}\n"

        if rec.get('est_monthly_savings'):
            if language == "es":
                rec_text += f"   💰 Ahorro estimado: ${rec['est_monthly_savings']:,.0f}/mes\n"
            else:
                rec_text += f"   💰 Estimated savings: ${rec['est_monthly_savings']:,.0f}/month\n"

        formatted_recs.append(rec_text)

    return header + "\n".join(formatted_recs)


def _format_budget_response(budget_update: Dict[str, Any]) -> str:
    """Format budget update response."""
    language = budget_update["resolved_language"]
    percentages = budget_update["normalized_percentages"]

    if language == "es":
        response = "💰 <b>Presupuesto Actualizado</b>\n\n"
        response += f"🏠 Fijo: {percentages['fixed']:.1f}%\n"
        response += f"🛒 Variable necesario: {percentages['variable_necessary']:.1f}%\n"
        response += f"🎯 Discrecional: {percentages['discretionary']:.1f}%\n"
    else:
        response = "💰 <b>Budget Updated</b>\n\n"
        response += f"🏠 Fixed: {percentages['fixed']:.1f}%\n"
        response += f"🛒 Variable necessary: {percentages['variable_necessary']:.1f}%\n"
        response += f"🎯 Discretionary: {percentages['discretionary']:.1f}%\n"

    # Add validation notes if any
    if budget_update["validation_notes"]:
        if language == "es":
            response += "\n<b>Notas:</b>\n"
        else:
            response += "\n<b>Notes:</b>\n"

        for note in budget_update["validation_notes"]:
            response += f"• {note}\n"

    return response


async def _create_confirmed_transaction(confirmation: Dict[str, Any], user_id: int) -> None:
    """Create a confirmed transaction in the database."""
    expense = confirmation["expense"]
    classification = confirmation["classification"]

    # Update user memory with any changes
    await financial_agent.update_user_memory(
        user_id=user_id,
        merchant=expense["merchant"],
        category=classification["category"],
        is_necessary=classification["is_necessary"]
    )

    # Create transaction in database
    async with async_session_maker() as session:
        # Get or create a default expense account
        account = await AccountCRUD.get_or_create(
            session=session,
            user_id=user_id,
            name="Default",
            account_type=AccountType.WALLET
        )

        # Create the transaction
        await TransactionCRUD.create(
            session=session,
            user_id=user_id,
            transaction_type=TransactionType.EXPENSE,
            currency=expense["currency"],
            amount=Decimal(str(expense["amount"])),
            date=datetime.strptime(expense["date"], "%Y-%m-%d"),
            account_from_id=account.id,
            description=f"{expense['merchant']} - {expense['note']}" if expense['note'] else expense['merchant']
        )
