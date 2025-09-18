import json
from datetime import datetime
from typing import List, Optional

import dateparser
from langchain_openai import ChatOpenAI

from src.agent.llm import get_llm
from src.agent.schemas import (
    BalanceInfo,
    MonthlyReport,
    ParsedQueryIntent,
    ParsedTransactionIntent,
    QueryIntent,
    TransactionIntent,
)
from src.db.models import TransactionType
from src.agent.tools.db_tool import (
    DbTool,
    QueryBalancesInput,
    QueryMonthlyReportInput,
    QueryTransactionsInput,
    RegisterTransactionInput,
)
from src.agent.tools.fx_tool import FxTool
from src.utils.timeparse import parse_date_range
from src.db.base import async_session_maker
from src.db.crud import AccountCRUD


class FinanceAgent:
    def __init__(self):
        self.llm = get_llm()
        self.db_tool = DbTool()
        self.fx_tool = FxTool()

        # Load system prompt
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_path = os.path.join(current_dir, "prompts", "system.md")
        with open(prompt_path, "r") as f:
            self.system_prompt = f.read()

    async def process_message(self, message: str, user_id: int) -> str:
        """Process a user message and return a response."""
        from src.utils.credits import UsageTracker

        # Track OpenAI API usage for this message
        message_preview = f"{message[:50]}{'...' if len(message) > 50 else ''}"
        async with UsageTracker("Message processing", message_preview) as tracker:
            # Store tracker reference for individual LLM calls
            self._usage_tracker = tracker
            try:
                # Detect language and validate support
                from src.utils.language import validate_supported_language, Messages, detect_language

                is_supported, detected_lang = validate_supported_language(message)
                if not is_supported:
                    return Messages.get("error", "unsupported_language", "en"), None

                self.user_language = detected_lang

                # First, try to parse as transaction intent
                transaction_intent = await self._extract_transaction_intent(message)
                if transaction_intent:
                    result = await self._handle_transaction(transaction_intent, user_id)
                    # Return tuple (confirmation_msg, transaction_data) for transactions
                    if isinstance(result, tuple):
                        return result
                    else:
                        return result, None

                # Then try to parse as query intent
                query_intent = await self._extract_query_intent(message)
                if query_intent:
                    return await self._handle_query(query_intent, user_id), None

                # If neither, provide general help
                return self._handle_general_message(message), None

            except Exception as e:
                # Return error in detected language
                lang = getattr(self, 'user_language', detect_language(message))
                return Messages.get("error", "general_error", lang, error=str(e)), None

    def _handle_general_message(self, message: str) -> str:
        """Handle general messages that aren't transactions or queries."""
        from src.utils.language import Messages
        lang = getattr(self, 'user_language', 'en')
        return Messages.get("help", "general_help", lang)

    async def _extract_transaction_intent(self, message: str) -> Optional[ParsedTransactionIntent]:
        """Extract transaction intent using structured output."""
        extraction_prompt = f"""
        Analyze this message in Spanish or English and determine if it describes a financial transaction.
        If it does, extract the structured information. If not, return null.

        Message: "{message}"

        Transaction types:
        - income: received money (recibí, cobré, ingreso, got paid, salary, freelance)
        - expense: spent money (gasté, pagué, compré, spent, bought, from/desde indicates source account)
        - transfer: moved money between accounts (transferí, envié, moved, de...a indicates from...to, cambié when moving between accounts)
        - conversion: exchanged currencies ONLY when explicitly converting currencies at exchange rates

        IMPORTANT: "efectivo" and "cash" are ACCOUNT NAMES, not currencies!
        IMPORTANT: "$" is a valid currency symbol that will be resolved to the account's primary currency (USD or ARS)

        Currency handling:
        - "$" can be used and will be resolved based on the account's primary currency
        - "USD", "ARS", "USDT", "USDC" are valid currency codes
        - Other symbols like "€", "£", "¥" are also valid and will be resolved
        - Generic terms like "pesos", "dollars" will be resolved to account's primary currency
        - IMPORTANT: Prefer specific currency codes (ARS, USD) over generic terms (pesos, dollars) when possible

        Spanish patterns:
        - "de mi cuenta de [account]" = account_from: [account] (for expenses)
        - "desde [account]" = account_from: [account]
        - "de [account] a [account]" = transfer from first to second
        - "en mi cuenta de [account]" = account_to for income
        - "en [place/store]" = description: [place/store] (NOT account)
        - "pagué X de [concept]" = expense with description: [concept]

        CASH/EFECTIVO patterns:
        - For EXPENSES: "en efectivo" = account_from: "Efectivo" (paid WITH cash)
        - For EXPENSES: "in cash" = account_from: "Cash" (paid WITH cash)
        - For TRANSFERS: "a [amount] en efectivo" = account_to: "Efectivo" (transfer TO cash)
        - For INCOME: "recibí en efectivo" = account_to: "Efectivo" (received TO cash)

        Critical: When someone SPENDS "en efectivo", the cash is the SOURCE (account_from)!

        Account name recognition:
        - "efectivo" → account name "Efectivo"
        - "cash" → account name "Cash"
        - "AstroPay", "Deel", "Galicia" → keep as-is
        - Physical cash is an account, not a currency!

        IMPORTANT:
        - "en supermercado" = description, NOT account
        - "de mi cuenta de AstroPay" = account_from: "AstroPay"
        - Places like "supermercado", "restaurant", "tienda" are descriptions, not accounts
        - Only "de mi cuenta de X" or "desde X" indicate accounts for expenses

        Spanish date patterns:
        - "31/08/2025" = August 31, 2025
        - "el día 31/08" = August 31, 2025 (use current year 2025, unless that would be a future date, then use 2024)

        IMPORTANT DATE LOGIC FOR DD/MM FORMAT:
        - Always use year 2025 for DD/MM dates UNLESS the date would be in the future
        - If DD/MM would create a future date, use year 2024 instead
        - Today is September 2025, so "05/08" = "05/08/2025" (August 5th, 2025 - past date)
        - Today is September 2025, so "25/09" = "25/09/2024" (September 25th would be future, so use 2024)

        Spanish number patterns:
        - "426 mil" = 426000 (mil = thousand)
        - "1.5 millones" = 1500000

        Return a JSON object with the transaction details or null if this is not a transaction.
        Use this exact format:
        {{
            "intent": "income|expense|transfer|conversion",
            "amount": number,
            "currency": "string",
            "account_from": "string or null",
            "account_to": "string or null",
            "amount_to": number or null,
            "currency_to": "string or null",
            "exchange_rate": number or null,
            "date": "ISO date string or null",
            "description": "string or null"
        }}

        Extract descriptions from context (prioritize meaningful context over generic terms):
        - "en el supermercado" → description: "supermercado"
        - "de gasolina" → description: "gasolina"
        - "salary" or "salario" → description: "salario"
        - "freelance" → description: "freelance"
        - "Le di 250 USD a Tami" → description: "250 USD a Tami"
        - "Pagué el alquiler" → description: "alquiler"
        - "Compré comida" → description: "comida"
        - "Transfer to savings" → description: "transfer to savings"
        - "Rent payment" → description: "rent payment"

        IMPORTANT Description Rules:
        - For "Le di X a [person]" → description: "X a [person]"
        - For "Gasté X en [place/thing]" → description: "[place/thing]"
        - For "Pagué X de [concept]" → description: "[concept]"
        - For "Compré [thing]" → description: "[thing]"
        - Extract the actual meaningful content, not generic terms like "expense" or "income"
        - Keep descriptions concise but informative
        - Preserve names and specific details when mentioned

        Examples:
        - "Recibí 6000 USD en mi cuenta de Deel el día 31/08/2025" → income, 6000, USD, account_to: "Deel", date: "2025-08-31", description: "6000 USD salary"
        - "Gasté 10 pesos en comida desde mercadopago el 05/08" → expense, 10, "ARS", account_from: "mercadopago", date: "2025-08-05", description: "comida"
        - "Gasté 400 ARS en el supermercado" → expense, 400, ARS, account_from: null, description: "supermercado"
        - "Gasté $400 de mercadopago" → expense, 400, "$", account_from: "mercadopago", description: "gasto"
        - "Gasté 426 mil ARS en supermercado becerra de mi cuenta de AstroPay" → expense, 426000, ARS, account_from: "AstroPay", description: "supermercado becerra"
        - "Le di 250 USD a Tami desde la cuenta de AstroPay" → expense, 250, USD, account_from: "AstroPay", description: "250 USD a Tami"
        - "Pagué 50000 ARS de alquiler desde Galicia" → expense, 50000, ARS, account_from: "Galicia", description: "alquiler"
        - "Gasté 50 mil ARS en flete de sillón en efectivo" → expense, 50000, ARS, account_from: "Efectivo", description: "flete de sillón"
        - "Spent 100 USD in cash on groceries" → expense, 100, USD, account_from: "Cash", description: "groceries"
        - "Transferí 1000 USD a mi cuenta de ahorros" → transfer, 1000, USD, account_to: "ahorros", description: "transfer a ahorros"
        - "Cambié Saldo de mi cuenta AstroPay a 150 mil ARS en efectivo" → transfer, 150000, ARS, account_from: "AstroPay", account_to: "Efectivo", description: "saldo a efectivo"
        - "Withdrew 200 USD in cash from Deel" → transfer, 200, USD, account_from: "Deel", account_to: "Cash", description: "withdrawal to cash"
        """

        try:
            response = await self.llm.ainvoke([{"role": "user", "content": extraction_prompt}])
            content = response.content.strip()

            # Track usage if tracker is available
            if hasattr(self, '_usage_tracker') and self._usage_tracker:
                from src.utils.credits import log_usage
                usage_data = getattr(response, 'usage_metadata', None)
                log_usage(usage_data, "Transaction intent extraction")
                if usage_data:
                    self._usage_tracker.add_usage(usage_data)

            if content.lower() in ["null", "none", ""] or not content:
                return None

            # Clean up the content - sometimes the LLM adds markdown formatting
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            if content.startswith("```"):
                content = content.replace("```", "").strip()

            # Parse JSON response
            data = json.loads(content)
            if not data or data == {}:
                return None

            # Parse date if provided
            if data.get("date"):
                parsed_date = None

                # First try manual parsing for DD/MM and DD/MM/YYYY formats to ensure consistent behavior
                try:
                    if "/" in data["date"]:
                        parts = data["date"].split("/")
                        if len(parts) == 3:
                            day, month, year = parts
                            parsed_date = datetime(int(year), int(month), int(day))
                        elif len(parts) == 2:
                            # Handle DD/MM format with smart year logic
                            day, month = parts
                            current_year = datetime.now().year
                            current_date = datetime.now()

                            # Try current year first
                            candidate_date = datetime(current_year, int(month), int(day))

                            # If the date would be in the future, use previous year
                            if candidate_date > current_date:
                                candidate_date = datetime(current_year - 1, int(month), int(day))

                            parsed_date = candidate_date
                except (ValueError, IndexError):
                    pass

                # If manual parsing failed, fall back to dateparser
                if not parsed_date:
                    parsed_date = dateparser.parse(data["date"], languages=['es', 'en'])

                if parsed_date:
                    data["date"] = parsed_date


            return ParsedTransactionIntent(**data)

        except Exception as e:
            print(f"Error extracting transaction intent: {e}")
            return None

    async def _extract_query_intent(self, message: str) -> Optional[ParsedQueryIntent]:
        """Extract query intent using structured output."""
        extraction_prompt = f"""
        Analyze this message in Spanish or English and determine if it's asking for financial information.
        Extract the structured query information with intelligent date parsing.

        Message: "{message}"

        Query types:
        - balance: asking for account balance (¿cuánto tengo?, balance, saldo, how much do I have)
        - expenses: asking for spending (¿cuánto gasté?, gastos, expenses, spending, spent)
        - income: asking for income (¿cuánto cobré?, ingresos, income, earned, received)
        - largest_purchase: largest transaction (mayor compra, largest purchase, biggest expense, gasto más grande)
        - savings: net savings (ahorros, savings, profit, ganancia)
        - monthly_report: monthly summary (reporte mensual, monthly report, resumen del mes)
        - monthly_report_pdf: PDF monthly summary (reporte mensual PDF, monthly report PDF, PDF report)
        - all_accounts: show all accounts (todas las cuentas, all accounts, mis cuentas)
        - all_transactions: list all transactions (listame las transacciones, list transactions, show transactions, transacciones, historial)
        - all_transactions_pdf: PDF transaction list (transacciones PDF, transaction PDF, PDF transactions)

        Date/Time parsing (be very smart about this):
        - "hoy/today" → today's date range
        - "ayer/yesterday" → yesterday's date range
        - "últimos X días/last X days" → last X days including today
        - "esta semana/this week" → current week (Monday to Sunday)
        - "la semana pasada/last week" → previous week
        - "este mes/this month" → current month
        - "el mes pasado/last month" → previous month
        - "enero/january", "febrero/february", etc. → specific month (assume current year or previous if future)
        - "agosto 2024/august 2024" → specific month and year
        - If no time period specified for expenses/income queries, assume "today"

        Account detection:
        - Look for account names like "Deel", "Galicia", "Astropay", "efectivo", "cash", etc.
        - Can be mentioned as "mi cuenta X", "from X", "en X", etc.

        Currency detection:
        - USD, ARS, EUR, USDT, USDC, BTC, ETH, etc.

        Return a JSON object with the query details or null if this is not a financial query.

        IMPORTANT: Do NOT generate specific dates! Only extract the date_expression and let the system parse it.

        Use this exact format:
        {{
            "intent": "balance|expenses|income|largest_purchase|savings|monthly_report|monthly_report_pdf|all_accounts|all_transactions|all_transactions_pdf",
            "account_name": "string or null",
            "currency": "string or null",
            "date_expression": "original date expression from user for parsing",
            "start_date": null,
            "end_date": null,
            "month": number or null,
            "year": number or null
        }}

        Examples:
        - "¿Cuánto tengo en mi cuenta Deel?" → {{"intent": "balance", "account_name": "Deel", "currency": null, "date_expression": null, "start_date": null, "end_date": null, "month": null, "year": null}}
        - "¿Cuánto gasté hoy?" → {{"intent": "expenses", "account_name": null, "currency": null, "date_expression": "hoy", "start_date": null, "end_date": null, "month": null, "year": null}}
        - "¿Cuánto gasté los últimos 7 días?" → {{"intent": "expenses", "account_name": null, "currency": null, "date_expression": "últimos 7 días", "start_date": null, "end_date": null, "month": null, "year": null}}
        - "listame las transacciones de los últimos 7 días" → {{"intent": "all_transactions", "account_name": null, "currency": null, "date_expression": "últimos 7 días", "start_date": null, "end_date": null, "month": null, "year": null}}
        - "¿Cuál fue mi gasto más grande en agosto?" → {{"intent": "largest_purchase", "account_name": null, "currency": null, "date_expression": "agosto", "start_date": null, "end_date": null, "month": null, "year": null}}
        - "How much did I spend yesterday?" → {{"intent": "expenses", "account_name": null, "currency": null, "date_expression": "yesterday", "start_date": null, "end_date": null, "month": null, "year": null}}
        - "Show my expenses this month in USD" → {{"intent": "expenses", "account_name": null, "currency": "USD", "date_expression": "this month", "start_date": null, "end_date": null, "month": null, "year": null}}
        - "List all transactions this week" → {{"intent": "all_transactions", "account_name": null, "currency": null, "date_expression": "this week", "start_date": null, "end_date": null, "month": null, "year": null}}
        """

        try:
            response = await self.llm.ainvoke([{"role": "user", "content": extraction_prompt}])
            content = response.content.strip()

            # Track usage if tracker is available
            if hasattr(self, '_usage_tracker') and self._usage_tracker:
                from src.utils.credits import log_usage
                usage_data = getattr(response, 'usage_metadata', None)
                log_usage(usage_data, "Query intent extraction")
                if usage_data:
                    self._usage_tracker.add_usage(usage_data)

            if content.lower() in ["null", "none", ""]:
                return None

            # Extract JSON from markdown code blocks if present
            if content.startswith("```json") and content.endswith("```"):
                content = content[7:-3].strip()
            elif content.startswith("```") and content.endswith("```"):
                content = content[3:-3].strip()

            # Parse JSON response
            data = json.loads(content)
            if not data:
                return None

            # Parse dates if provided
            if data.get("start_date"):
                parsed_date = dateparser.parse(data["start_date"])
                if parsed_date:
                    data["start_date"] = parsed_date

            if data.get("end_date"):
                parsed_date = dateparser.parse(data["end_date"])
                if parsed_date:
                    data["end_date"] = parsed_date

            # Use advanced date parsing if date_expression is provided
            if data.get("date_expression"):
                from src.utils.date_utils import parse_flexible_date
                date_range = parse_flexible_date(data["date_expression"])
                if date_range:
                    data["start_date"] = date_range[0]
                    data["end_date"] = date_range[1]

            return ParsedQueryIntent(**data)

        except Exception as e:
            print(f"Error extracting query intent: {e}")
            return None

    async def _handle_transaction(self, intent: ParsedTransactionIntent, user_id: int) -> str:
        """Handle transaction processing."""
        try:
            # Find similar existing accounts or normalize names
            if intent.account_from:
                intent.account_from = await self._find_similar_account(intent.account_from, user_id)
            if intent.account_to:
                intent.account_to = await self._find_similar_account(intent.account_to, user_id)

            # Resolve generic currency symbols based on account's primary currency
            intent.currency = await self._resolve_currency_symbol(intent.currency, intent.account_from, intent.account_to, user_id)
            if intent.currency == "ERROR_PESO_MISMATCH":
                from src.utils.language import Messages
                lang = getattr(self, 'user_language', 'es')
                if lang == 'es':
                    account_name = intent.account_from or intent.account_to or "la cuenta"
                    return f"❌ Error: La cuenta {account_name} no maneja pesos. Por favor especifica la moneda correcta (ej: USD, USDT, etc.)"
                else:
                    account_name = intent.account_from or intent.account_to or "the account"
                    return f"❌ Error: {account_name} doesn't handle pesos. Please specify the correct currency (e.g., USD, USDT, etc.)"

            if intent.currency_to:
                intent.currency_to = await self._resolve_currency_symbol(intent.currency_to, intent.account_from, intent.account_to, user_id)
                if intent.currency_to == "ERROR_PESO_MISMATCH":
                    from src.utils.language import Messages
                    lang = getattr(self, 'user_language', 'es')
                    if lang == 'es':
                        account_name = intent.account_from or intent.account_to or "la cuenta"
                        return f"❌ Error: La cuenta {account_name} no maneja pesos. Por favor especifica la moneda correcta (ej: USD, USDT, etc.)"
                    else:
                        account_name = intent.account_from or intent.account_to or "the account"
                        return f"❌ Error: {account_name} doesn't handle pesos. Please specify the correct currency (e.g., USD, USDT, etc.)"

            # If exchange rate is needed but not provided, fetch it
            if (intent.intent == TransactionIntent.CONVERSION and
                intent.currency_to and not intent.exchange_rate):

                rate = await self.fx_tool.get_rate_value(intent.currency, intent.currency_to)
                if rate:
                    intent.exchange_rate = rate
                    if not intent.amount_to:
                        intent.amount_to = intent.amount * rate
                else:
                    return f"❌ Could not fetch exchange rate for {intent.currency}/{intent.currency_to}"

            # Generate description if not provided
            description = intent.description
            if not description:
                description = self._generate_transaction_description(intent)

            # Create transaction data for confirmation
            transaction_data = {
                "transaction_type": intent.intent.value,
                "amount": float(intent.amount),
                "currency": intent.currency,
                "account_from": intent.account_from,
                "account_to": intent.account_to,
                "amount_to": float(intent.amount_to) if intent.amount_to else None,
                "currency_to": intent.currency_to,
                "exchange_rate": float(intent.exchange_rate) if intent.exchange_rate else None,
                "description": description,
                "date": intent.date,
                "user_id": user_id
            }

            # Return confirmation message with transaction data
            return (self._format_confirmation_message(transaction_data), transaction_data)

        except Exception as e:
            return f"❌ Error processing transaction: {str(e)}"

    async def _resolve_currency_symbol(self, currency: str, account_from: Optional[str], account_to: Optional[str], user_id: int) -> str:
        """
        Resolve generic currency symbols and names (like $, pesos, dollars) to actual currency codes based on account's primary currency.
        For expenses, check account_from. For income, check account_to.
        """
        if not currency:
            return "USD"  # Default fallback

        # Normalize currency for comparison
        currency_lower = currency.lower().strip()

        # Generic currency symbols and names that need resolution
        generic_currencies = ["$", "₱", "€", "£", "¥", "pesos", "peso", "dollars", "dollar", "dolares", "dolar"]

        if currency in ["$", "₱", "€", "£", "¥"] or currency_lower in ["pesos", "peso", "dollars", "dollar", "dolares", "dolar"]:
            # Determine which account to check based on transaction type
            account_to_check = None
            if account_from:  # For expenses/transfers from an account
                account_to_check = account_from
            elif account_to:  # For income/transfers to an account
                account_to_check = account_to

            if account_to_check:
                # Get the account's primary currency from its balances
                async with async_session_maker() as session:
                    account = await AccountCRUD.get_by_name(session, user_id, account_to_check)
                    if account and account.balances:
                        # Find the balance with the highest amount (primary currency)
                        primary_balance = max(account.balances, key=lambda b: b.balance)
                        resolved_currency = primary_balance.currency

                        # Map generic symbols and names to specific currencies based on account's currencies
                        if currency == "$" or currency_lower in ["dollars", "dollar", "dolares", "dolar"]:
                            # Check what dollar currencies the account has
                            account_currencies = [b.currency for b in account.balances if b.balance > 0]

                            # Priority order for $ symbol: USD > ARS > others
                            if "USD" in account_currencies:
                                return "USD"  # USD takes priority for $ symbol
                            elif "ARS" in account_currencies:
                                return "ARS"  # ARS second priority for $ in Spanish context
                            else:
                                return "USD"  # Default assumption for $ symbol
                        elif currency_lower in ["pesos", "peso"]:
                            # "pesos" should resolve to account's primary currency if it's a peso currency
                            account_currencies = [b.currency for b in account.balances if b.balance > 0]

                            # Check if account has peso currencies (ARS, MXN, COP, etc.)
                            peso_currencies = ["ARS", "MXN", "COP", "CLP", "UYU", "PEN"]  # Common peso currencies
                            for peso_curr in peso_currencies:
                                if peso_curr in account_currencies:
                                    return peso_curr

                            # If no peso currency found but account has other currencies, this might be an error
                            if account_currencies:
                                from src.utils.language import Messages
                                lang = getattr(self, 'user_language', 'es')
                                # Return an error indicator - we'll handle this in the calling function
                                return "ERROR_PESO_MISMATCH"
                            else:
                                return "ARS"  # Default assumption for pesos
                        elif currency == "€":
                            return "EUR"
                        elif currency == "£":
                            return "GBP"
                        elif currency == "¥":
                            return "JPY"
                        elif currency == "₱":
                            return "PHP"
                        else:
                            return resolved_currency  # Return account's primary currency

            # If no account specified or account not found, return defaults
            if currency == "$" or currency_lower in ["dollars", "dollar", "dolares", "dolar"]:
                return "USD"
            elif currency_lower in ["pesos", "peso"]:
                return "ARS"  # Default assumption for pesos when no account context
            elif currency == "€":
                return "EUR"
            elif currency == "£":
                return "GBP"
            elif currency == "¥":
                return "JPY"
            elif currency == "₱":
                return "PHP"
            else:
                return "USD"

        # Return the currency as-is if it's already a valid currency code
        return currency

    def _generate_transaction_description(self, intent: ParsedTransactionIntent) -> str:
        """Generate a meaningful description for transactions without explicit descriptions."""
        if intent.intent == TransactionIntent.INCOME:
            if intent.account_to:
                return f"{intent.amount:,.0f} {intent.currency} ingreso"
            else:
                return f"{intent.amount:,.0f} {intent.currency} ingreso"

        elif intent.intent == TransactionIntent.EXPENSE:
            if intent.account_from:
                return f"{intent.amount:,.0f} {intent.currency} gasto"
            else:
                return f"{intent.amount:,.0f} {intent.currency} gasto"

        elif intent.intent == TransactionIntent.TRANSFER:
            if intent.account_from and intent.account_to:
                return f"{intent.amount:,.0f} {intent.currency} a {intent.account_to}"
            elif intent.account_to:
                return f"{intent.amount:,.0f} {intent.currency} a {intent.account_to}"
            elif intent.account_from:
                return f"{intent.amount:,.0f} {intent.currency} desde {intent.account_from}"
            else:
                return f"{intent.amount:,.0f} {intent.currency} transferencia"

        elif intent.intent == TransactionIntent.CONVERSION:
            if intent.currency_to and intent.amount_to:
                return f"{intent.amount:,.0f} {intent.currency} → {intent.amount_to:,.0f} {intent.currency_to}"
            elif intent.currency_to:
                return f"{intent.amount:,.0f} {intent.currency} → {intent.currency_to}"
            else:
                return f"{intent.amount:,.0f} {intent.currency} conversión"

        return f"{intent.amount:,.0f} {intent.currency} {intent.intent.value}"

    def _normalize_account_name(self, account_name: str) -> str:
        """Normalize account names to handle variations and common patterns."""
        if not account_name:
            return account_name

        # Convert to lowercase for processing
        normalized = account_name.lower().strip()

        # Handle common Spanish variations
        if "mi cuenta del banco" in normalized or "cuenta del banco" in normalized:
            return "banco"
        elif "mi cuenta de" in normalized:
            # "mi cuenta de Galicia" -> "Galicia"
            return normalized.replace("mi cuenta de ", "").strip().title()
        elif "cuenta de" in normalized:
            # "cuenta de Galicia" -> "Galicia"
            return normalized.replace("cuenta de ", "").strip().title()
        elif "mi " in normalized and "cuenta" in normalized:
            # "mi Galicia cuenta" -> "Galicia"
            return normalized.replace("mi ", "").replace("cuenta", "").strip().title()
        elif normalized in ["banco", "el banco"]:
            return "banco"
        elif normalized in ["galicia", "banco galicia"]:
            return "Galicia"
        elif normalized in ["deel", "mi deel"]:
            return "Deel"
        elif normalized in ["astropay", "mi astropay"]:
            return "AstroPay"
        elif normalized in ["belo", "mi belo"]:
            return "Belo"
        else:
            # Return title case for other accounts
            return account_name.title()

    async def _find_similar_account(self, account_name: str, user_id: int) -> str:
        """Find existing account with similar name or return the normalized name."""
        if not account_name:
            return account_name

        normalized_input = account_name.lower().replace(" ", "").replace("-", "")

        # Get all existing accounts
        async with async_session_maker() as session:
            accounts = await AccountCRUD.get_all_with_balances(session, user_id)

            # Check for exact matches first
            for account in accounts:
                normalized_existing = account.name.lower().replace(" ", "").replace("-", "")
                if normalized_input == normalized_existing:
                    return account.name

            # Check for fuzzy matches (contains or very similar)
            for account in accounts:
                normalized_existing = account.name.lower().replace(" ", "").replace("-", "")
                # If input is contained in existing or vice versa
                if (normalized_input in normalized_existing or
                    normalized_existing in normalized_input):
                    # Prefer the existing account name
                    return account.name

            # No similar account found, return normalized input
            return self._normalize_account_name(account_name)

    def _format_confirmation_message(self, transaction_data: dict) -> str:
        """Format confirmation message for user approval."""
        from src.utils.language import Messages
        lang = getattr(self, 'user_language', 'en')

        if lang == 'es':
            lines = ["🔔 <b>Confirmación de transacción</b>", ""]

            # Transaction type
            type_map = {
                "income": "💰 Ingreso",
                "expense": "💸 Gasto",
                "transfer": "🔄 Transferencia",
                "conversion": "💱 Conversión"
            }
            lines.append(f"<b>Tipo:</b> {type_map.get(transaction_data['transaction_type'], 'Transacción')}")

            # Amount
            amount = transaction_data['amount']
            currency = transaction_data['currency']
            lines.append(f"<b>Monto:</b> {amount:,.0f} {currency}")

            # Accounts
            if transaction_data['account_from']:
                lines.append(f"<b>Desde:</b> {transaction_data['account_from']}")
            if transaction_data['account_to']:
                lines.append(f"<b>Hacia:</b> {transaction_data['account_to']}")

            # For conversions
            if transaction_data['currency_to'] and transaction_data['amount_to']:
                lines.append(f"<b>Resultado:</b> {transaction_data['amount_to']:,.0f} {transaction_data['currency_to']}")
                if transaction_data['exchange_rate']:
                    lines.append(f"<b>Tasa:</b> {transaction_data['exchange_rate']:,.2f}")

            # Description
            lines.append(f"<b>Descripción:</b> {transaction_data['description']}")

        else:  # English
            lines = ["🔔 <b>Transaction Confirmation</b>", ""]

            # Transaction type
            type_map = {
                "income": "💰 Income",
                "expense": "💸 Expense",
                "transfer": "🔄 Transfer",
                "conversion": "💱 Conversion"
            }
            lines.append(f"<b>Type:</b> {type_map.get(transaction_data['transaction_type'], 'Transaction')}")

            # Amount
            amount = transaction_data['amount']
            currency = transaction_data['currency']
            lines.append(f"<b>Amount:</b> {amount:,.0f} {currency}")

            # Accounts
            if transaction_data['account_from']:
                lines.append(f"<b>From:</b> {transaction_data['account_from']}")
            if transaction_data['account_to']:
                lines.append(f"<b>To:</b> {transaction_data['account_to']}")

            # For conversions
            if transaction_data['currency_to'] and transaction_data['amount_to']:
                lines.append(f"<b>Result:</b> {transaction_data['amount_to']:,.0f} {transaction_data['currency_to']}")
                if transaction_data['exchange_rate']:
                    lines.append(f"<b>Rate:</b> {transaction_data['exchange_rate']:,.2f}")

            # Description
            lines.append(f"<b>Description:</b> {transaction_data['description']}")

        # Date
        if transaction_data['date']:
            date_label = "<b>Fecha:</b>" if lang == 'es' else "<b>Date:</b>"
            lines.append(f"{date_label} {transaction_data['date'].strftime('%d/%m/%Y')}")

        # Confirmation question
        confirmation = "¿Confirmas esta transacción?" if lang == 'es' else "Do you confirm this transaction?"
        lines.extend(["", confirmation])

        return "\n".join(lines)

    async def confirm_transaction(self, transaction_data: dict) -> str:
        """Actually save the confirmed transaction."""
        try:
            from src.utils.language import Messages, detect_language

            db_input = RegisterTransactionInput(**transaction_data)
            result = await self.db_tool.register_transaction(db_input)

            if "registered successfully" in result.lower():
                return self._format_success_message(transaction_data)
            return result

        except Exception as e:
            # Get language from stored attribute or detect from error context
            lang = getattr(self, 'user_language', 'en')
            return Messages.get("error", "transaction_error", lang, error=str(e))

    def _format_success_message(self, transaction_data: dict) -> str:
        """Format success message after confirmation."""
        from src.utils.language import Messages
        lang = getattr(self, 'user_language', 'en')

        tx_type = transaction_data['transaction_type']
        amount = transaction_data['amount']
        currency = transaction_data['currency']

        if lang == 'es':
            if tx_type == "income":
                msg = f"✅ Ingreso registrado: +{amount:,.0f} {currency}"
                if transaction_data['account_to']:
                    msg += f"\n📍 Cuenta: {transaction_data['account_to']}"
            elif tx_type == "expense":
                msg = f"✅ Gasto registrado: -{amount:,.0f} {currency}"
                if transaction_data['account_from']:
                    msg += f"\n📍 Desde: {transaction_data['account_from']}"
            elif tx_type == "transfer":
                msg = f"✅ Transferencia registrada: {amount:,.0f} {currency}"
                if transaction_data['account_from'] and transaction_data['account_to']:
                    msg += f"\n📍 {transaction_data['account_from']} → {transaction_data['account_to']}"
            elif tx_type == "conversion":
                msg = f"✅ Conversión registrada: {amount:,.0f} {currency}"
                if transaction_data['currency_to'] and transaction_data['amount_to']:
                    msg += f"\n💱 → {transaction_data['amount_to']:,.0f} {transaction_data['currency_to']}"

            if transaction_data['date']:
                msg += f"\n📅 Fecha: {transaction_data['date'].strftime('%d/%m/%Y')}"
        else:
            if tx_type == "income":
                msg = f"✅ Income registered: +{amount:,.0f} {currency}"
                if transaction_data['account_to']:
                    msg += f"\n📍 Account: {transaction_data['account_to']}"
            elif tx_type == "expense":
                msg = f"✅ Expense registered: -{amount:,.0f} {currency}"
                if transaction_data['account_from']:
                    msg += f"\n📍 From: {transaction_data['account_from']}"
            elif tx_type == "transfer":
                msg = f"✅ Transfer registered: {amount:,.0f} {currency}"
                if transaction_data['account_from'] and transaction_data['account_to']:
                    msg += f"\n📍 {transaction_data['account_from']} → {transaction_data['account_to']}"
            elif tx_type == "conversion":
                msg = f"✅ Conversion registered: {amount:,.0f} {currency}"
                if transaction_data['currency_to'] and transaction_data['amount_to']:
                    msg += f"\n💱 → {transaction_data['amount_to']:,.0f} {transaction_data['currency_to']}"

            if transaction_data['date']:
                msg += f"\n📅 Date: {transaction_data['date'].strftime('%d/%m/%Y')}"

        return msg

    async def _handle_query(self, intent: ParsedQueryIntent, user_id: int) -> str:
        """Handle query processing."""
        try:
            if intent.intent == QueryIntent.BALANCE:
                # Apply account name normalization for queries too
                account_name = intent.account_name
                if account_name:
                    account_name = await self._find_similar_account(account_name, user_id)

                balances = await self.db_tool.query_balances(
                    QueryBalancesInput(account_name=account_name), user_id
                )
                return self._format_balances(balances)

            elif intent.intent == QueryIntent.ALL_ACCOUNTS:
                balances = await self.db_tool.query_balances(QueryBalancesInput(), user_id)
                return self._format_balances(balances)

            elif intent.intent in [QueryIntent.EXPENSES, QueryIntent.INCOME]:
                if not intent.start_date or not intent.end_date:
                    # If no date range, assume today
                    from datetime import datetime, timedelta
                    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    intent.start_date = today
                    intent.end_date = today + timedelta(days=1) - timedelta(microseconds=1)

                # Apply account name normalization for queries too
                account_name = intent.account_name
                if account_name:
                    account_name = await self._find_similar_account(account_name, user_id)

                transaction_type = "expense" if intent.intent == QueryIntent.EXPENSES else "income"
                transactions = await self.db_tool.query_transactions(
                    QueryTransactionsInput(
                        start_date=intent.start_date,
                        end_date=intent.end_date,
                        account_name=account_name,
                        transaction_type=transaction_type
                    ), user_id
                )

                total = sum(t.amount for t in transactions)

                # Format response with date context
                from src.utils.date_utils import format_date_range_spanish
                date_str = format_date_range_spanish(intent.start_date, intent.end_date)

                if intent.intent == QueryIntent.EXPENSES:
                    if total == 0:
                        return f"💰 No tuviste gastos {date_str}"
                    else:
                        currency = transactions[0].currency if transactions else "USD"
                        response = f"💸 <b>Gastos {date_str}:</b>\n"
                        response += f"<b>Total:</b> {total:,.2f} {currency}\n"
                        response += f"<b>Transacciones:</b> {len(transactions)}\n"

                        if len(transactions) <= 5:
                            response += "\n📋 <b>Detalle:</b>\n"
                            for tx in transactions:
                                account_info = f" desde {tx.account_from}" if tx.account_from else ""
                                response += f"• {tx.amount:,.2f} {tx.currency}{account_info} - {tx.description or 'Sin descripción'}\n"

                        return response
                else:  # Income
                    if total == 0:
                        return f"💰 No tuviste ingresos {date_str}"
                    else:
                        currency = transactions[0].currency if transactions else "USD"
                        response = f"💰 <b>Ingresos {date_str}:</b>\n"
                        response += f"<b>Total:</b> {total:,.2f} {currency}\n"
                        response += f"<b>Transacciones:</b> {len(transactions)}\n"

                        if len(transactions) <= 5:
                            response += "\n📋 <b>Detalle:</b>\n"
                            for tx in transactions:
                                account_info = f" hacia {tx.account_to}" if tx.account_to else ""
                                response += f"• {tx.amount:,.2f} {tx.currency}{account_info} - {tx.description or 'Sin descripción'}\n"

                        return response

            elif intent.intent == QueryIntent.LARGEST_PURCHASE:
                if not intent.start_date or not intent.end_date:
                    # If no date range, assume last 30 days
                    from datetime import datetime, timedelta
                    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    intent.start_date = today - timedelta(days=29)
                    intent.end_date = today + timedelta(days=1) - timedelta(microseconds=1)

                largest = await self.db_tool.get_largest_transaction(
                    user_id, intent.start_date, intent.end_date, TransactionType.EXPENSE
                )

                if largest:
                    from src.utils.date_utils import format_date_range_spanish
                    date_str = format_date_range_spanish(intent.start_date, intent.end_date)
                    account_info = f" desde {largest.account_from}" if largest.account_from else ""
                    date_info = largest.date.strftime('%d/%m/%Y')

                    response = f"💸 <b>Mayor gasto {date_str}:</b>\n"
                    response += f"<b>Monto:</b> {largest.amount:,.2f} {largest.currency}\n"
                    response += f"<b>Fecha:</b> {date_info}\n"
                    if largest.account_from:
                        response += f"<b>Cuenta:</b> {largest.account_from}\n"
                    if largest.description:
                        response += f"<b>Descripción:</b> {largest.description}\n"

                    return response
                else:
                    from src.utils.date_utils import format_date_range_spanish
                    date_str = format_date_range_spanish(intent.start_date, intent.end_date)
                    return f"❌ No se encontraron gastos {date_str}"

            elif intent.intent == QueryIntent.ALL_TRANSACTIONS:
                if not intent.start_date or not intent.end_date:
                    # If no date range, assume last 30 days
                    from datetime import datetime, timedelta
                    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    intent.start_date = today - timedelta(days=29)
                    intent.end_date = today + timedelta(days=1) - timedelta(microseconds=1)

                # Apply account name normalization for queries too
                account_name = intent.account_name
                if account_name:
                    account_name = await self._find_similar_account(account_name, user_id)

                transactions = await self.db_tool.query_transactions(
                    QueryTransactionsInput(
                        start_date=intent.start_date,
                        end_date=intent.end_date,
                        account_name=account_name,
                        transaction_type=None  # Get all transaction types
                    ), user_id
                )

                # Format response with date context
                from src.utils.date_utils import format_date_range_spanish
                date_str = format_date_range_spanish(intent.start_date, intent.end_date)

                if not transactions:
                    return f"💰 No tuviste transacciones {date_str}"

                # Group transactions by type for summary
                expenses = [t for t in transactions if t.type == 'expense']
                income = [t for t in transactions if t.type == 'income']
                transfers = [t for t in transactions if t.type == 'transfer']
                conversions = [t for t in transactions if t.type == 'conversion']

                # Calculate totals by currency
                def group_by_currency(transactions_list):
                    currency_totals = {}
                    for tx in transactions_list:
                        currency = tx.currency
                        if currency not in currency_totals:
                            currency_totals[currency] = 0
                        currency_totals[currency] += tx.amount
                    return currency_totals

                expense_totals = group_by_currency(expenses)
                income_totals = group_by_currency(income)

                # Build response
                lang = getattr(self, 'user_language', 'es')
                if lang == 'es':
                    response = f"💼 <b>Transacciones {date_str}:</b>\n"
                    response += f"<b>Total:</b> {len(transactions)} transacciones\n\n"

                    if expenses:
                        expense_summary = ", ".join([f"{amount:,.0f} {currency}" for currency, amount in expense_totals.items()])
                        response += f"💸 <b>Gastos:</b> {len(expenses)} transacciones - {expense_summary}\n"
                    if income:
                        income_summary = ", ".join([f"{amount:,.0f} {currency}" for currency, amount in income_totals.items()])
                        response += f"💰 <b>Ingresos:</b> {len(income)} transacciones - {income_summary}\n"
                    if transfers:
                        response += f"🔄 <b>Transferencias:</b> {len(transfers)} transacciones\n"
                    if conversions:
                        response += f"💱 <b>Conversiones:</b> {len(conversions)} transacciones\n"

                    response += "\n📋 <b>Detalle:</b>\n"
                    for tx in transactions[:10]:  # Show first 10 transactions
                        tx_type_icon = {'expense': '💸', 'income': '💰', 'transfer': '🔄', 'conversion': '💱'}.get(tx.type, '💼')
                        date_info = tx.date.strftime('%d/%m')
                        account_info = ""
                        if tx.account_from and tx.account_to:
                            account_info = f" ({tx.account_from} → {tx.account_to})"
                        elif tx.account_from:
                            account_info = f" (desde {tx.account_from})"
                        elif tx.account_to:
                            account_info = f" (hacia {tx.account_to})"

                        response += f"• {tx_type_icon} {date_info}: {tx.amount:,.0f} {tx.currency}{account_info} - {tx.description or 'Sin descripción'}\n"

                    if len(transactions) > 10:
                        response += f"\n... y {len(transactions) - 10} transacciones más"
                else:  # English
                    response = f"💼 <b>Transactions {date_str}:</b>\n"
                    response += f"<b>Total:</b> {len(transactions)} transactions\n\n"

                    if expenses:
                        expense_summary = ", ".join([f"{amount:,.0f} {currency}" for currency, amount in expense_totals.items()])
                        response += f"💸 <b>Expenses:</b> {len(expenses)} transactions - {expense_summary}\n"
                    if income:
                        income_summary = ", ".join([f"{amount:,.0f} {currency}" for currency, amount in income_totals.items()])
                        response += f"💰 <b>Income:</b> {len(income)} transactions - {income_summary}\n"
                    if transfers:
                        response += f"🔄 <b>Transfers:</b> {len(transfers)} transactions\n"
                    if conversions:
                        response += f"💱 <b>Conversions:</b> {len(conversions)} transactions\n"

                    response += "\n📋 <b>Details:</b>\n"
                    for tx in transactions[:10]:  # Show first 10 transactions
                        tx_type_icon = {'expense': '💸', 'income': '💰', 'transfer': '🔄', 'conversion': '💱'}.get(tx.type, '💼')
                        date_info = tx.date.strftime('%d/%m')
                        account_info = ""
                        if tx.account_from and tx.account_to:
                            account_info = f" ({tx.account_from} → {tx.account_to})"
                        elif tx.account_from:
                            account_info = f" (from {tx.account_from})"
                        elif tx.account_to:
                            account_info = f" (to {tx.account_to})"

                        response += f"• {tx_type_icon} {date_info}: {tx.amount:,.0f} {tx.currency}{account_info} - {tx.description or 'No description'}\n"

                    if len(transactions) > 10:
                        response += f"\n... and {len(transactions) - 10} more transactions"

                return response

            elif intent.intent == QueryIntent.MONTHLY_REPORT:
                month = intent.month or datetime.now().month
                year = intent.year or datetime.now().year

                report = await self.db_tool.generate_monthly_report(
                    QueryMonthlyReportInput(month=month, year=year), user_id
                )
                return self._format_monthly_report(report)

            elif intent.intent == QueryIntent.MONTHLY_REPORT_PDF:
                month = intent.month or datetime.now().month
                year = intent.year or datetime.now().year

                pdf_path = await self.db_tool.generate_monthly_report_pdf(
                    QueryMonthlyReportInput(month=month, year=year), user_id
                )
                return f"PDF_FILE:{pdf_path}"

            elif intent.intent == QueryIntent.ALL_TRANSACTIONS_PDF:
                if not intent.start_date or not intent.end_date:
                    # If no date range, assume last 30 days
                    from datetime import datetime, timedelta
                    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    intent.start_date = today - timedelta(days=29)
                    intent.end_date = today + timedelta(days=1) - timedelta(microseconds=1)

                # Apply account name normalization for PDF queries too
                account_name = intent.account_name
                if account_name:
                    account_name = await self._find_similar_account(account_name, user_id)

                pdf_path = await self.db_tool.generate_transactions_pdf(
                    QueryTransactionsInput(
                        start_date=intent.start_date,
                        end_date=intent.end_date,
                        account_name=account_name,
                        transaction_type=None  # Get all transaction types for PDF
                    ), user_id
                )
                return f"PDF_FILE:{pdf_path}"

            else:
                return "❌ Query type not yet implemented"

        except Exception as e:
            return f"❌ Error processing query: {str(e)}"

    def _format_balances(self, balances: List[BalanceInfo]) -> str:
        """Format balance information for display."""
        if not balances:
            return "No balances found."

        # Group by account
        accounts = {}
        for balance in balances:
            if balance.account_name not in accounts:
                accounts[balance.account_name] = []
            accounts[balance.account_name].append(balance)

        lines = []
        for account_name, account_balances in accounts.items():
            if len(account_balances) == 1:
                balance = account_balances[0]
                lines.append(f"* {account_name} – {balance.currency} {balance.balance:,.2f}")
            else:
                currencies = []
                for balance in account_balances:
                    currencies.append(f"{balance.currency} {balance.balance:,.2f}")
                lines.append(f"* {account_name} – {', '.join(currencies)}")

        return "\n".join(lines)

    def _format_monthly_report(self, report: MonthlyReport) -> str:
        """Format monthly report for display."""
        lines = [
            f"📊 <b>Monthly Report - {report.month:02d}/{report.year}</b>",
            "",
            f"💰 Total Income: {report.total_income:,.2f}",
            f"💸 Total Expenses: {report.total_expenses:,.2f}",
            f"💵 Net Savings: {report.net_savings:,.2f}",
            "",
        ]

        if report.largest_transaction:
            t = report.largest_transaction
            account_info = f" from {t.account_from}" if t.account_from else ""
            lines.append(f"🏆 Largest Transaction: {t.amount:,.2f} {t.currency}{account_info}")
            lines.append("")

        lines.append("🏦 <b>Current Balances:</b>")
        if report.balances:
            balance_text = self._format_balances(report.balances)
            lines.append(balance_text)
        else:
            lines.append("No balances found.")

        return "\n".join(lines)
