"""
Language detection and localization utilities for bilingual financial assistant.
"""

import re
from typing import Literal

LanguageCode = Literal["en", "es"]


def detect_language(text: str) -> LanguageCode:
    """
    Detect if text is in Spanish or English.
    Returns 'es' for Spanish, 'en' for English (default).
    """
    text_lower = text.lower().strip()
    
    # Spanish indicators (high confidence)
    spanish_indicators = [
        # Common Spanish words
        'gasté', 'recibí', 'pagué', 'compré', 'cobré', 'transferí', 'cambié',
        'cuanto', 'cuánto', 'cual', 'cuál', 'donde', 'dónde', 'como', 'cómo',
        'saldo', 'cuenta', 'efectivo', 'desde', 'hacia', 'último', 'últimos',
        'ayer', 'hoy', 'mañana', 'semana', 'mes', 'año', 'día', 'días',
        'tengo', 'tuve', 'fueron', 'está', 'estoy', 'son', 'fue',
        'mil', 'millones', 'pesos', 'dólares',
        # Simple greetings and common words
        'hola', 'gracias', 'por favor', 'sí', 'no', 'bueno', 'bien',
        'adiós', 'hasta', 'luego', 'disculpe', 'perdón',
        
        # Common Spanish phrases
        'en efectivo', 'mi cuenta', 'la cuenta', 'el banco', 'los últimos',
        'la semana', 'el mes', 'esta semana', 'este mes', 'el año',
        'de mi', 'en mi', 'desde mi', 'hacia mi', 'para mi'
    ]
    
    # English indicators (high confidence)
    english_indicators = [
        # Common English words specific to financial context
        'spent', 'received', 'paid', 'bought', 'earned', 'transferred', 'withdrew',
        'how much', 'what was', 'show me', 'my balance', 'my account', 'in cash',
        'from my', 'to my', 'last week', 'this week', 'last month', 'this month',
        'yesterday', 'today', 'tomorrow', 'dollars', 'cash', 'wallet',
        'largest', 'biggest', 'total', 'expenses', 'income', 'savings'
    ]
    
    # Count Spanish indicators
    spanish_score = 0
    for indicator in spanish_indicators:
        if indicator in text_lower:
            spanish_score += 1
    
    # Count English indicators  
    english_score = 0
    for indicator in english_indicators:
        if indicator in text_lower:
            english_score += 1
    
    # Spanish accented characters are a strong indicator
    if re.search(r'[áéíóúüñ¿¡]', text_lower):
        spanish_score += 2
    
    # Question patterns
    if text_lower.startswith('¿') or '¿' in text_lower:
        spanish_score += 2
    elif text_lower.startswith(('how', 'what', 'when', 'where', 'why', 'show')):
        english_score += 1
    
    # Verb conjugations (Spanish has more complex patterns)
    spanish_verb_patterns = [
        r'\b\w+é\b',      # -é endings (gasté, compré, etc.)
        r'\b\w+í\b',      # -í endings (recibí, etc.)
        r'\b\w+aste\b',   # -aste endings
        r'\b\w+ó\b',      # -ó endings
    ]
    
    for pattern in spanish_verb_patterns:
        if re.search(pattern, text_lower):
            spanish_score += 1
    
    # Default to Spanish if more Spanish indicators, otherwise English
    return "es" if spanish_score > english_score else "en"


def validate_supported_language(text: str) -> tuple[bool, LanguageCode | None]:
    """
    Check if the text is in a supported language (English or Spanish).
    Returns (is_supported, language_code).
    """
    detected_lang = detect_language(text)
    
    # Check for unsupported language indicators (excluding Spanish/English special chars)
    # Allow Latin basic + Latin-1 supplement + Latin Extended-A (covers Spanish accents)
    unsupported_pattern = r'[^\x00-\x7F\u00A0-\u017F\u2000-\u206F\u20A0-\u20CF\u2100-\u214F]'
    if re.search(unsupported_pattern, text):
        # Contains characters outside supported ranges
        return False, None
    
    # Spanish and English are both supported
    return True, detected_lang


class Messages:
    """Localized message templates."""
    
    ERROR_MESSAGES = {
        "en": {
            "transaction_error": "❌ Error registering transaction: {error}",
            "processing_error": "❌ Error processing transaction: {error}",
            "query_error": "❌ Error processing query: {error}",
            "general_error": "❌ Sorry, I encountered an error: {error}",
            "validation_error": "❌ Please check your input and try again",
            "unsupported_language": "❌ I only support English and Spanish. Please write your message in one of these languages.",
            "no_transactions": "💰 You had no {transaction_type} {period}",
            "no_balances": "❌ No balances found. Start by recording some transactions!",
            "no_balance_account": "❌ No balance found for account: {account}",
        },
        "es": {
            "transaction_error": "❌ Error registrando transacción: {error}",
            "processing_error": "❌ Error procesando transacción: {error}",
            "query_error": "❌ Error procesando consulta: {error}",
            "general_error": "❌ Lo siento, encontré un error: {error}",
            "validation_error": "❌ Por favor revisa tu entrada e intenta de nuevo",
            "unsupported_language": "❌ Solo soporto inglés y español. Por favor escribe tu mensaje en uno de estos idiomas.",
            "no_transactions": "💰 No tuviste {transaction_type} {period}",
            "no_balances": "❌ No se encontraron balances. ¡Comienza registrando algunas transacciones!",
            "no_balance_account": "❌ No se encontró balance para la cuenta: {account}",
        }
    }
    
    SUCCESS_MESSAGES = {
        "en": {
            "income_registered": "✅ Income registered: +{amount:,.0f} {currency}",
            "expense_registered": "✅ Expense registered: -{amount:,.0f} {currency}",
            "transfer_registered": "✅ Transfer registered: {amount:,.0f} {currency}",
            "conversion_registered": "✅ Conversion registered: {amount:,.0f} {currency}",
        },
        "es": {
            "income_registered": "✅ Ingreso registrado: +{amount:,.0f} {currency}",
            "expense_registered": "✅ Gasto registrado: -{amount:,.0f} {currency}",
            "transfer_registered": "✅ Transferencia registrada: {amount:,.0f} {currency}",
            "conversion_registered": "✅ Conversión registrada: {amount:,.0f} {currency}",
        }
    }
    
    CONFIRMATION_MESSAGES = {
        "en": {
            "transaction_confirmation": "🔔 **Transaction Confirmation**\n\n**Type:** {type_icon} {type_name}\n**Amount:** {amount:,.0f} {currency}\n**From:** {account_from}\n**To:** {account_to}\n**Description:** {description}\n\nDo you confirm this transaction?",
        },
        "es": {
            "transaction_confirmation": "🔔 **Confirmación de transacción**\n\n**Tipo:** {type_icon} {type_name}\n**Monto:** {amount:,.0f} {currency}\n**Desde:** {account_from}\n**Hacia:** {account_to}\n**Descripción:** {description}\n\n¿Confirmas esta transacción?",
        }
    }
    
    HELP_MESSAGES = {
        "en": {
            "general_help": """
I'm your personal finance AI assistant! I can help you with:

💰 **Recording transactions** (in Spanish or English):
• "I received 6000 USD in my Deel account"
• "I spent 400 ARS at the supermarket"
• "I transferred 1000 USD to Astropay"

📊 **Checking balances and reports**:
• "How much do I have in my Deel account?"
• "Show my balance in Astropay"
• "/balance" - See all balances
• "/report" - Monthly report

Try describing a financial transaction or asking about your accounts!
""",
        },
        "es": {
            "general_help": """
¡Soy tu asistente de finanzas personales con IA! Te puedo ayudar con:

💰 **Registrar transacciones** (en español o inglés):
• "Recibí 6000 USD en mi cuenta de Deel"
• "Gasté 400 ARS en el supermercado"
• "Transferí 1000 USD a Astropay"

📊 **Consultar balances y reportes**:
• "¿Cuánto tengo en mi cuenta Deel?"
• "Muestra mi balance en Astropay"
• "/balance" - Ver todos los balances
• "/report" - Reporte mensual

¡Intenta describir una transacción financiera o preguntar sobre tus cuentas!
""",
        }
    }

    @classmethod
    def get(cls, category: str, key: str, lang: LanguageCode, **kwargs) -> str:
        """Get a localized message with formatting."""
        messages = getattr(cls, category.upper() + "_MESSAGES", {})
        template = messages.get(lang, {}).get(key, messages.get("en", {}).get(key, ""))
        
        if template and kwargs:
            try:
                return template.format(**kwargs)
            except (KeyError, ValueError):
                return template
        return template