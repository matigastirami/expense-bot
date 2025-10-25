"""
Telegram bot handlers for Financial Analysis Agent integration.

This module provides the Telegram bot interface for the Financial Analysis Agent,
including commands, callback handlers, interactive confirmation flows, and audio expense entry.
"""

import logging
import os
import tempfile
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Voice,
)
from aiogram.utils.markdown import hbold, hcode

from packages.agent.financial_agent import FinancialAnalysisAgent
from libs.db.base import async_session_maker
from libs.db.crud import UserCRUD, TransactionCRUD, AccountCRUD
from libs.db.models import TransactionType, AccountType
from libs.utils.language import detect_language, Messages
from packages.telegram.states import TransactionStates

logger = logging.getLogger(__name__)

# Initialize router and agent
financial_router = Router()
financial_agent = FinancialAnalysisAgent()

# Store pending confirmations (in production, use Redis or database)
pending_confirmations: Dict[str, Dict[str, Any]] = {}


def cleanup_expired_confirmations():
    """Clean up confirmations older than 10 minutes to prevent memory leaks."""
    from datetime import timedelta

    now = datetime.now()
    expired_ids = []

    for conf_id, data in pending_confirmations.items():
        if "created_at" in data:
            age = now - data["created_at"]
            if age > timedelta(minutes=10):  # 10 minute expiration
                expired_ids.append(conf_id)

    for conf_id in expired_ids:
        del pending_confirmations[conf_id]
        logger.info(f"Cleaned up expired confirmation: {conf_id}")

    if expired_ids:
        logger.info(f"Cleaned up {len(expired_ids)} expired confirmations")


# Initialize audio transcription service
try:
    from libs.services.audio_transcription import audio_service
except ImportError:
    logger.warning("⚠️ Audio transcription service not available")
    audio_service = None


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
            rec_text = _format_recommendations(
                analysis["recommendations"], analysis["resolved_language"]
            )
            await message.answer(rec_text, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Error in analyze command: {e}")
        language = detect_language(message.text or "")
        error_msg = Messages.get("error", "general_error", language, error=str(e))
        await message.answer(error_msg)


@financial_router.message(F.voice)
async def handle_voice_expense(message: Message, state: FSMContext):
    """Handle voice messages for expense entry."""
    try:
        # Check if audio transcription is available
        if not audio_service or not audio_service.api_key:
            language = detect_language(message.from_user.language_code or "en")
            if language == "es":
                await message.answer(
                    "🎤 ¡Me encantaría procesar tu mensaje de voz!\n\n"
                    "Para habilitar esta función, necesitas configurar una clave API de OpenAI.\n"
                    "Por ahora, puedes escribir tu gasto de estas formas:\n\n"
                    "• /expense 50 USD Starbucks café\n"
                    '• "Gasté 50 dólares en Starbucks para café"\n'
                    '• "50 USD Starbucks - café de la mañana"'
                )
            else:
                await message.answer(
                    "🎤 I'd love to process your voice message!\n\n"
                    "To enable this feature, you need to configure an OpenAI API key.\n"
                    "For now, you can enter expenses by typing:\n\n"
                    "• /expense 50 USD Starbucks coffee\n"
                    '• "Spent 50 dollars at Starbucks for coffee"\n'
                    '• "50 USD Starbucks - morning coffee"'
                )
            return

        # Get user from database
        async with async_session_maker() as session:
            user = await UserCRUD.get_by_telegram_id(session, str(message.from_user.id))
            if not user:
                await message.answer("❌ User not found. Please use /start first.")
                return

        # Determine language hint from user's language or previous messages
        language_hint = None
        user_language = "en"  # Default
        if message.from_user.language_code:
            if message.from_user.language_code.startswith("es"):
                language_hint = "es"
                user_language = "es"
            elif message.from_user.language_code.startswith("en"):
                language_hint = "en"
                user_language = "en"

        # Show processing indicator in user's language
        if user_language == "es":
            processing_msg = await message.answer("🎤 Procesando mensaje de voz...")
        else:
            processing_msg = await message.answer("🎤 Processing voice message...")

        try:
            # Transcribe the voice message
            transcription = await audio_service.download_and_transcribe_telegram_voice(
                bot=message.bot, voice=message.voice, language=language_hint
            )

            if not transcription:
                if user_language == "es":
                    await processing_msg.edit_text(
                        "❌ No pude transcribir el mensaje de voz.\n\n"
                        "Intenta:\n"
                        "• Hablar más claro\n"
                        "• Reducir el ruido de fondo\n"
                        "• Escribir el gasto manualmente"
                    )
                else:
                    await processing_msg.edit_text(
                        "❌ Could not transcribe the voice message.\n\n"
                        "Try:\n"
                        "• Speaking more clearly\n"
                        "• Reducing background noise\n"
                        "• Typing the expense manually"
                    )
                return

            # Edit the processing message to show transcription
            transcription_preview = (
                transcription[:100] + "..."
                if len(transcription) > 100
                else transcription
            )
            if user_language == "es":
                await processing_msg.edit_text(
                    f'🎤➡️📝 Transcrito: "{transcription_preview}"'
                )
            else:
                await processing_msg.edit_text(
                    f'🎤➡️📝 Transcribed: "{transcription_preview}"'
                )

            # Parse the transcription for expense information
            expense_data = await _parse_voice_expense(transcription, user.id)

            if not expense_data:
                if user_language == "es":
                    await message.answer(
                        f"🤔 No pude encontrar información de gasto en:\n\n"
                        f'"{transcription}"\n\n'
                        "Intenta incluir:\n"
                        "• Cantidad (ej: 50 pesos, 25 dólares)\n"
                        "• Lugar o descripción (ej: supermercado, café)\n\n"
                        'Ejemplo: "Gasté 50 dólares en Starbucks para café"'
                    )
                else:
                    await message.answer(
                        f"🤔 I couldn't find expense information in:\n\n"
                        f'"{transcription}"\n\n'
                        "Try including:\n"
                        "• Amount (e.g., 50 dollars, 25 euros)\n"
                        "• Place or description (e.g., grocery store, coffee)\n\n"
                        'Example: "I spent 50 dollars at Starbucks for coffee"'
                    )
                return

            # Process the expense using the financial agent
            # Detect language from the actual transcription text (not user settings)
            # This handles cases where Whisper transcribes Spanish -> English
            from libs.utils.language import detect_language
            detected_lang = detect_language(transcription)
            expense_data["language"] = detected_lang
            confirmation = await financial_agent.process_expense_confirmation(
                **expense_data
            )

            # Store confirmation for callback with more unique ID
            import time

            confirmation_id = f"{user.id}_{int(time.time() * 1000)}"  # Use milliseconds for better uniqueness
            pending_confirmations[confirmation_id] = {
                "confirmation": confirmation,
                "user_id": user.id,
                "original_transcription": transcription,
                "created_at": datetime.now(),
            }
            logger.info(f"Stored confirmation with ID: {confirmation_id}")

            # Send confirmation message with buttons
            keyboard = _build_expense_confirmation_keyboard(
                confirmation_id, confirmation
            )
            response = _format_expense_confirmation(confirmation)

            # Add transcription info to the response
            language = confirmation["resolved_language"]
            if language == "es":
                transcription_info = f'🎤 Mensaje de voz: "{transcription}"\n\n'
            else:
                transcription_info = f'🎤 Voice message: "{transcription}"\n\n'

            full_response = transcription_info + response

            await message.answer(
                full_response, reply_markup=keyboard, parse_mode="HTML"
            )

        except Exception as e:
            logger.error(f"Error processing voice message: {e}")
            error_msg = (
                "❌ Error al procesar mensaje de voz"
                if user_language == "es"
                else "❌ Error processing voice message"
            )
            await processing_msg.edit_text(f"{error_msg}: {str(e)}")

    except Exception as e:
        logger.error(f"Error in voice handler: {e}")
        error_msg = (
            "❌ Error procesando audio"
            if user_language == "es"
            else "❌ Error processing audio"
        )
        await message.answer(error_msg)


# DISABLED: Interferes with Spanish processing
# @financial_router.message(F.text & ~F.text.startswith("/"))
async def handle_text_expense(message: Message, state: FSMContext):
    """Handle text messages that might be expenses for enhanced processing."""
    # DISABLED: Return early to prevent interference
    return
    try:
        # Check if this looks like an expense message, but ONLY process very specific patterns
        # to avoid interfering with the original agent that handles Spanish well
        text = message.text.lower()

        # Only process messages that explicitly mention specific analysis keywords
        # This prevents interference with the original agent's Spanish processing
        analysis_indicators = [
            "analyze",
            "análisis",
            "analizar",
            "categorize",
            "categorizar",
            "budget",
            "presupuesto",
            "classify",
            "clasificar",
        ]

        # Check for explicit Financial Analysis Agent keywords
        should_use_financial_agent = any(
            indicator in text for indicator in analysis_indicators
        )

        # If this doesn't contain analysis keywords, let the original agent handle it
        if not should_use_financial_agent:
            # Get user from database
            async with async_session_maker() as session:
                user = await UserCRUD.get_by_telegram_id(
                    session, str(message.from_user.id)
                )
                if not user:
                    await message.answer("❌ User not found. Please use /start first.")
                    return

            # Show processing indicator
            language = detect_language(message.text)
            if language == "es":
                processing_msg = await message.answer("💭 Procesando gasto...")
            else:
                processing_msg = await message.answer("💭 Processing expense...")

            # Parse the text for expense information
            logger.info(f"Parsing text expense: '{message.text}' for user {user.id}")
            expense_data = await _parse_text_expense(message.text, user.id)
            logger.info(f"Parsed expense data: {expense_data}")

            if not expense_data:
                logger.info(
                    "No expense data extracted, falling back to original bot processing"
                )
                # Delete processing message and fall back to original bot processing
                await processing_msg.delete()
                return

            # Process the expense using the financial agent
            logger.info(f"Processing expense data: {expense_data}")
            try:
                # Add language to expense_data
                expense_data["language"] = language
                confirmation = await financial_agent.process_expense_confirmation(
                    **expense_data
                )
                logger.info(
                    f"Expense confirmation received: {confirmation.get('type', 'unknown')}"
                )
            except Exception as e:
                logger.error(f"Error in process_expense_confirmation: {e}")
                await processing_msg.edit_text(
                    f"❌ Error al procesar el gasto: {str(e)}"
                )
                return

            # Store confirmation for callback with more unique ID
            import time

            confirmation_id = f"{user.id}_{int(time.time() * 1000)}"
            pending_confirmations[confirmation_id] = {
                "confirmation": confirmation,
                "user_id": user.id,
                "created_at": datetime.now(),
                "original_text": message.text,
            }
            logger.info(f"Stored text expense confirmation with ID: {confirmation_id}")

            # Send confirmation message with enhanced buttons
            keyboard = _build_expense_confirmation_keyboard(
                confirmation_id, confirmation
            )
            response = _format_expense_confirmation(confirmation)

            # Add text source info to the response
            language = confirmation["resolved_language"]
            if language == "es":
                text_info = f'📝 Mensaje: "{message.text}"\n\n'
            else:
                text_info = f'📝 Text message: "{message.text}"\n\n'

            full_response = text_info + response

            # Delete the processing message and send the confirmation
            await processing_msg.delete()
            await message.answer(
                full_response, reply_markup=keyboard, parse_mode="HTML"
            )
            return

        # If not an expense, let the original bot handle it by not handling the message

    except Exception as e:
        logger.error(f"Error in text expense handler: {e}")
        # Show error to user instead of silently failing
        try:
            if "processing_msg" in locals():
                await processing_msg.edit_text(f"❌ Error procesando gasto: {str(e)}")
            else:
                await message.answer(f"❌ Error procesando gasto: {str(e)}")
        except:
            # If even error reporting fails, try basic message
            try:
                await message.answer("❌ Error interno procesando gasto")
            except:
                pass


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
                await message.answer(
                    "Uso: /expense <cantidad> <moneda> <comercio> [descripción]\nEjemplo: /expense 50 USD Starbucks café de la mañana"
                )
            else:
                await message.answer(
                    "Usage: /expense <amount> <currency> <merchant> [description]\nExample: /expense 50 USD Starbucks morning coffee"
                )
            return

        amount = float(args[0])
        currency = args[1].upper()
        merchant = args[2]
        note = " ".join(args[3:]) if len(args) > 3 else ""

        # Detect language from the command text
        language = detect_language(message.text or "")

        # Process expense confirmation
        confirmation = await financial_agent.process_expense_confirmation(
            amount=amount,
            currency=currency,
            date=None,  # Use today
            merchant=merchant,
            note=note,
            user_id=user.id,
            language=language,
        )

        # Store confirmation for callback with more unique ID
        import time

        confirmation_id = f"{user.id}_{int(time.time() * 1000)}"  # Use milliseconds for better uniqueness
        pending_confirmations[confirmation_id] = {
            "confirmation": confirmation,
            "user_id": user.id,
            "created_at": datetime.now(),
        }
        logger.info(f"Stored confirmation with ID: {confirmation_id}")

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
                await message.answer(
                    "Uso: /budget <porcentajes>\nEjemplo: /budget 50% fijo, 30% necesario, 20% discrecional"
                )
            else:
                await message.answer(
                    "Usage: /budget <percentages>\nExample: /budget 50% fixed, 30% necessary, 20% discretionary"
                )
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
        data_parts = callback.data.split("_", 2)  # Split only on first 2 underscores
        action = data_parts[1]  # confirm, category, necessity
        confirmation_id = data_parts[
            2
        ]  # This will be the full confirmation_id including underscores

        logger.info(
            f"Callback received: action={action}, confirmation_id={confirmation_id}"
        )

        # Clean up any expired confirmations
        cleanup_expired_confirmations()

        logger.info(f"Available confirmations: {list(pending_confirmations.keys())}")

        if confirmation_id not in pending_confirmations:
            logger.warning(
                f"Confirmation ID {confirmation_id} not found in pending confirmations"
            )
            # Try to detect language for error message
            language = (
                "es"
                if callback.from_user.language_code
                and callback.from_user.language_code.startswith("es")
                else "en"
            )
            error_msg = (
                "❌ Confirmación expiró. Intenta de nuevo."
                if language == "es"
                else "❌ Confirmation expired. Please try again."
            )
            await callback.answer(error_msg)
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
            keyboard = _build_expense_confirmation_keyboard(
                confirmation_id, confirmation
            )

            await callback.message.edit_text(
                new_text, reply_markup=keyboard, parse_mode="HTML"
            )
            await callback.answer("✅ Necessity updated!")

        elif action.startswith("setcat"):
            # Set specific category
            category = action.replace("setcat", "").replace("_", " ")
            confirmation["classification"]["category"] = category

            # Update UI
            new_text = _format_expense_confirmation(confirmation)
            keyboard = _build_expense_confirmation_keyboard(
                confirmation_id, confirmation
            )

            await callback.message.edit_text(
                new_text, reply_markup=keyboard, parse_mode="HTML"
            )
            await callback.answer(f"✅ Category set to {category}")

        elif action == "cancel":
            # Cancel the transaction
            language = confirmation["resolved_language"]
            cancel_msg = (
                "❌ Transaction cancelled."
                if language == "en"
                else "❌ Transacción cancelada."
            )

            await callback.message.edit_text(cancel_msg)
            await callback.answer("Transaction cancelled")

            # Clean up
            del pending_confirmations[confirmation_id]

    except Exception as e:
        logger.error(f"Error in expense callback: {e}")
        await callback.answer("❌ Error processing request")


def _build_expense_confirmation_keyboard(
    confirmation_id: str, confirmation: Dict[str, Any]
) -> InlineKeyboardMarkup:
    """Build keyboard for expense confirmation."""
    language = confirmation["resolved_language"]

    buttons = [
        [
            InlineKeyboardButton(
                text="✅ Confirm" if language == "en" else "✅ Confirmar",
                callback_data=f"expense_confirm_{confirmation_id}",
            ),
            InlineKeyboardButton(
                text="🏷️ Category" if language == "en" else "🏷️ Categoría",
                callback_data=f"expense_category_{confirmation_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔄 Toggle Necessity"
                if language == "en"
                else "🔄 Cambiar Necesidad",
                callback_data=f"expense_necessity_{confirmation_id}",
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Cancel" if language == "en" else "❌ Cancelar",
                callback_data=f"expense_cancel_{confirmation_id}",
            )
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _build_category_selection_keyboard(
    confirmation_id: str, alternatives: list
) -> InlineKeyboardMarkup:
    """Build keyboard for category selection."""
    buttons = []

    for alt in alternatives:
        category = alt["category"]
        # Replace spaces with underscores for callback data
        callback_category = category.replace(" ", "_")
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"🏷️ {category}",
                    callback_data=f"expense_setcat{callback_category}_{confirmation_id}",
                )
            ]
        )

    # Add back button
    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Back", callback_data=f"expense_back_{confirmation_id}"
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _format_expense_confirmation(confirmation: Dict[str, Any]) -> str:
    """Format expense confirmation message."""
    expense = confirmation["expense"]
    classification = confirmation["classification"]
    language = confirmation["resolved_language"]

    necessity_text = {
        "en": "necessary" if classification["is_necessary"] else "not necessary",
        "es": "necesario" if classification["is_necessary"] else "no necesario",
    }

    confidence_text = f"({classification['confidence']:.0%})"

    if language == "es":
        return f"""
🔔 <b>Confirmación de Gasto</b>

<b>Monto:</b> {expense["amount"]:,.0f} {expense["currency"]}
<b>Comercio:</b> {expense["merchant"]}
<b>Descripción:</b> {expense["note"] or "N/A"}
<b>Fecha:</b> {expense["date"]}

<b>Categoría:</b> {classification["category"]} {confidence_text}
<b>Necesidad:</b> {necessity_text[language]}

¿Confirmar esta transacción?
"""
    else:
        return f"""
🔔 <b>Expense Confirmation</b>

<b>Amount:</b> {expense["amount"]:,.0f} {expense["currency"]}
<b>Merchant:</b> {expense["merchant"]}
<b>Description:</b> {expense["note"] or "N/A"}
<b>Date:</b> {expense["date"]}

<b>Category:</b> {classification["category"]} {confidence_text}
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
        budget_section += (
            f"• Fijo: {actual['fixed']:.1f}% (objetivo {targets['fixed']:.1f}%)\n"
        )
        budget_section += f"• Variable necesario: {actual['variable_necessary']:.1f}% (objetivo {targets['variable_necessary']:.1f}%)\n"
        budget_section += f"• Discrecional: {actual['discretionary']:.1f}% (objetivo {targets['discretionary']:.1f}%)\n"
    else:
        budget_section = "\n<b>📋 Budget Adherence:</b>\n"
        budget_section += (
            f"• Fixed: {actual['fixed']:.1f}% (target {targets['fixed']:.1f}%)\n"
        )
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

        if rec.get("est_monthly_savings"):
            if language == "es":
                rec_text += (
                    f"   💰 Ahorro estimado: ${rec['est_monthly_savings']:,.0f}/mes\n"
                )
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


async def _parse_text_expense(text: str, user_id: int) -> Optional[Dict[str, Any]]:
    """
    Parse text message to extract expense information.

    This is similar to _parse_voice_expense but optimized for typed text.

    Args:
        text: The text message
        user_id: User identifier

    Returns:
        Dictionary with expense data or None if parsing fails
    """
    # Reuse the voice parsing logic since text and voice expenses have similar patterns
    return await _parse_voice_expense(text, user_id)


async def _parse_voice_expense(
    transcription: str, user_id: int
) -> Optional[Dict[str, Any]]:
    """
    Parse voice transcription to extract expense information.

    Args:
        transcription: The transcribed text from voice message
        user_id: User identifier

    Returns:
        Dictionary with expense data or None if parsing fails
    """
    import re
    from decimal import Decimal

    text = transcription.lower().strip()

    # Currency patterns - support both symbols and names
    # Order matters: check specific tokens before generic ones
    currency_patterns = {
        "usdt": r"(?:usdt|tether)",  # Check USDT before USD
        "btc": r"(?:btc|bitcoin)",
        "usd": r"(?:usd|dollars?|bucks?|\$)",
        "ars": r"(?:ars|pesos?|peso)",
        "eur": r"(?:eur|euros?)",
    }

    # Amount patterns - support various formats
    amount_patterns = [
        r"(\d+(?:[.,]\d+)?)\s*k\s*({currencies})",  # "50k USD"
        r"(\d+(?:[.,]\d+)?)\s*({currencies})",  # "50 USD"
        r"({currencies})\s*(\d+(?:[.,]\d+)?)",  # "USD 50"
        r"(\d+(?:[.,]\d+)?)(?:\s*(?:dollars?|pesos?|euros?))",  # "50 dollars"
    ]

    # Create combined currency pattern
    all_currencies = "|".join(currency_patterns.values())

    amount = None
    currency = "USD"  # Default currency

    # Try to find amount and currency
    for pattern in amount_patterns:
        pattern_with_currencies = pattern.format(currencies=all_currencies)
        match = re.search(pattern_with_currencies, text, re.IGNORECASE)

        if match:
            groups = match.groups()

            # Extract amount (could be in group 1 or 2)
            amount_str = None
            currency_str = None

            for group in groups:
                if re.match(r"\d+(?:[.,]\d+)?", group):
                    amount_str = group.replace(",", ".")
                else:
                    # Check if this group contains currency info
                    for curr_code, pattern in currency_patterns.items():
                        if re.search(pattern, group, re.IGNORECASE):
                            currency_str = group.lower()
                            currency = curr_code.upper()
                            break

            if amount_str:
                try:
                    amount = float(amount_str)

                    # Handle "k" multiplier
                    if "k" in match.group(0).lower():
                        amount *= 1000

                    # If no currency detected in groups, search the whole match
                    if currency == "USD":  # Still default
                        for curr_code, pattern in currency_patterns.items():
                            if re.search(pattern, match.group(0), re.IGNORECASE):
                                currency = curr_code.upper()
                                break

                    break
                except ValueError:
                    continue

    if not amount:
        return None

    # Extract merchant/location information
    merchant = ""
    note = ""

    # Common spending phrases in English and Spanish
    spending_patterns = [
        r"(?:spent|paid|bought|purchased)\s+.*?(?:at|from|in)\s+([^,.]+)",  # "spent 50 at Starbucks"
        r"(?:gasté|pagué|compré)\s+.*?(?:en|de)\s+([^,.]+)",  # "gasté 50 en Starbucks"
        r"(?:at|en)\s+([^,.]+)",  # "at Starbucks"
        r"(?:from|de)\s+([^,.]+)",  # "from my account"
        r"(?:for|para)\s+([^,.]+)",  # "for coffee"
    ]

    for pattern in spending_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            extracted = match.group(1).strip()

            # Skip if it's just a currency or amount
            if not re.match(
                r"^\d+|usd|ars|eur|dollars?|pesos?", extracted, re.IGNORECASE
            ):
                if not merchant:
                    merchant = extracted
                elif extracted not in merchant.lower():
                    note = extracted
                break

    # If no merchant found, try to extract from general context
    if not merchant:
        # Look for standalone words that could be merchants
        words = text.split()
        potential_merchants = []

        for word in words:
            # Skip common words and currencies
            if (
                len(word) > 2
                and word
                not in [
                    "the",
                    "and",
                    "for",
                    "from",
                    "with",
                    "spent",
                    "paid",
                    "bought",
                    "gasté",
                    "pagué",
                    "compré",
                    "para",
                    "con",
                    "desde",
                ]
                and not re.match(r"^\d+|usd|ars|eur", word, re.IGNORECASE)
            ):
                potential_merchants.append(word.title())

        if potential_merchants:
            merchant = " ".join(potential_merchants[:2])  # Take first 2 words

    # Create note from remaining context
    if not note:
        # Look for descriptive phrases
        descriptive_patterns = [
            r"(?:for|para)\s+([^,.]+)",
            r"(?:buying|comprando)\s+([^,.]+)",
        ]

        for pattern in descriptive_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                note = match.group(1).strip()
                break

    # If still no merchant, use a generic description
    if not merchant:
        merchant = "Voice Expense"
        note = transcription[:50] + "..." if len(transcription) > 50 else transcription

    return {
        "amount": amount,
        "currency": currency,
        "date": None,  # Will use today
        "merchant": merchant,
        "note": note,
        "user_id": user_id,
    }


async def _create_confirmed_transaction(
    confirmation: Dict[str, Any], user_id: int
) -> None:
    """Create a confirmed transaction in the database."""
    expense = confirmation["expense"]
    classification = confirmation["classification"]

    # Update user memory with any changes
    await financial_agent.update_user_memory(
        user_id=user_id,
        merchant=expense["merchant"],
        category=classification["category"],
        is_necessary=classification["is_necessary"],
    )

    # Create transaction in database
    async with async_session_maker() as session:
        # Get or create a default expense account
        account = await AccountCRUD.get_or_create(
            session=session,
            user_id=user_id,
            name="Default",
            account_type=AccountType.WALLET,
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
            description=f"{expense['merchant']} - {expense['note']}"
            if expense["note"]
            else expense["merchant"],
        )
