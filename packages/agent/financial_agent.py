"""
Financial Analysis Agent - Comprehensive bilingual expense tracking and analysis system.

This module implements the requirements specified in the Financial Agent guide:
- Expense Classification with learning capabilities
- Budget Management with percentage-based tracking
- Financial Analysis with period-based insights
- User Memory for learning corrections and preferences
- Bilingual Support (English/Spanish)
- Period Resolution for natural language date parsing
"""

import re
import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any, TypedDict
from dataclasses import dataclass

from src.utils.language import detect_language, LanguageCode
from src.db.base import async_session_maker
from src.db.crud import TransactionCRUD, UserCRUD, AccountCRUD
from src.db.models import TransactionType


class ExpenseConfirmation(TypedDict):
    """Response schema for expense confirmation requests."""

    type: str  # "expense_confirmation"
    resolved_language: LanguageCode
    expense: Dict[str, Any]
    classification: Dict[str, Any]
    memory_updates_if_user_confirms_changes: Dict[str, Any]
    ui_confirmation_text: str


class AnalysisReport(TypedDict):
    """Response schema for financial analysis reports."""

    type: str  # "analysis_report"
    resolved_language: LanguageCode
    period: Dict[str, str]
    totals: Dict[str, Any]
    budget_targets_pct: Dict[str, float]
    budget_actual_pct: Dict[str, float]
    signals: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    human_summary: str


class BudgetUpdate(TypedDict):
    """Response schema for budget updates."""

    type: str  # "budget_update"
    resolved_language: LanguageCode
    normalized_percentages: Dict[str, float]
    validation_notes: List[str]
    confirmation_text: str


@dataclass
class CategoryMapping:
    """Maps expense categories to buckets and keywords."""

    category: str
    bucket: str
    keywords: List[str]
    necessity: bool  # Default necessity flag


class FinancialAnalysisAgent:
    """
    Main Financial Analysis Agent class implementing comprehensive expense tracking.

    Features:
    - Automatic expense classification with 14+ categories
    - Bucket-based budgeting (Fixed, Variable Necessary, Discretionary)
    - Natural language period parsing in English and Spanish
    - User memory system for learning preferences
    - Bilingual analysis and recommendations
    """

    def __init__(self):
        """Initialize the Financial Analysis Agent with category mappings and user memory."""
        self._category_mappings = self._build_category_mappings()
        self._user_memory: Dict[int, Dict[str, Any]] = {}

    def _build_category_mappings(self) -> List[CategoryMapping]:
        """Build the predefined category mappings with keywords and bucket assignments."""
        return [
            # Fixed bucket
            CategoryMapping(
                "Fixed",
                "fixed",
                [
                    "rent",
                    "alquiler",
                    "utilities",
                    "servicios",
                    "insurance",
                    "seguro",
                    "subscription",
                    "suscripcion",
                    "mortgage",
                    "hipoteca",
                ],
                True,
            ),
            CategoryMapping(
                "Taxes/Fees",
                "fixed",
                [
                    "tax",
                    "impuesto",
                    "fee",
                    "tasa",
                    "government",
                    "gobierno",
                    "iva",
                    "ganancias",
                ],
                True,
            ),
            CategoryMapping(
                "Debt/Loans",
                "fixed",
                [
                    "credit",
                    "credito",
                    "loan",
                    "prestamo",
                    "debt",
                    "deuda",
                    "payment",
                    "cuota",
                ],
                True,
            ),
            # Variable Necessary bucket
            CategoryMapping(
                "Groceries",
                "variable_necessary",
                [
                    "grocery",
                    "groceries",
                    "food",
                    "comida",
                    "supermercado",
                    "supermarket",
                    "verduleria",
                    "carniceria",
                    "almacen",
                ],
                True,
            ),
            CategoryMapping(
                "Transport",
                "variable_necessary",
                [
                    "taxi",
                    "uber",
                    "gas",
                    "nafta",
                    "transport",
                    "transporte",
                    "bus",
                    "colectivo",
                    "subway",
                    "subte",
                    "train",
                    "tren",
                    "parking",
                    "estacionamiento",
                ],
                True,
            ),
            CategoryMapping(
                "Health",
                "variable_necessary",
                [
                    "medical",
                    "medico",
                    "health",
                    "salud",
                    "pharmacy",
                    "farmacia",
                    "doctor",
                    "hospital",
                    "medicine",
                    "medicina",
                    "dental",
                    "odonto",
                ],
                True,
            ),
            CategoryMapping(
                "Education",
                "variable_necessary",
                [
                    "school",
                    "colegio",
                    "course",
                    "curso",
                    "education",
                    "educacion",
                    "university",
                    "universidad",
                    "book",
                    "libro",
                    "tuition",
                    "matricula",
                ],
                True,
            ),
            CategoryMapping(
                "Childcare",
                "variable_necessary",
                [
                    "childcare",
                    "guarderia",
                    "daycare",
                    "nanny",
                    "niñera",
                    "school",
                    "colegio",
                ],
                True,
            ),
            CategoryMapping(
                "Business",
                "variable_necessary",
                [
                    "office",
                    "oficina",
                    "work",
                    "trabajo",
                    "business",
                    "negocio",
                    "professional",
                    "profesional",
                    "meeting",
                    "reunion",
                ],
                True,
            ),
            # Discretionary bucket
            CategoryMapping(
                "Dining/Delivery",
                "discretionary",
                [
                    "restaurant",
                    "restaurante",
                    "delivery",
                    "pedidos",
                    "cafe",
                    "bar",
                    "pizza",
                    "mcdonalds",
                    "starbucks",
                    "burger",
                    "hamburgesa",
                    "rappi",
                    "uber eats",
                    "coffee",
                ],
                False,
            ),
            CategoryMapping(
                "Leisure/Entertainment",
                "discretionary",
                [
                    "movie",
                    "cine",
                    "games",
                    "juegos",
                    "entertainment",
                    "entretenimiento",
                    "sport",
                    "deporte",
                    "gym",
                    "gimnasio",
                    "netflix",
                    "spotify",
                    "concert",
                ],
                False,
            ),
            CategoryMapping(
                "Shopping",
                "discretionary",
                [
                    "clothes",
                    "ropa",
                    "electronics",
                    "electronica",
                    "shopping",
                    "compras",
                    "amazon",
                    "mercadolibre",
                    "store",
                    "tienda",
                    "mall",
                ],
                False,
            ),
            CategoryMapping(
                "Travel",
                "discretionary",
                [
                    "hotel",
                    "flight",
                    "vuelo",
                    "travel",
                    "viaje",
                    "vacation",
                    "vacaciones",
                    "airbnb",
                    "booking",
                    "trip",
                ],
                False,
            ),
            CategoryMapping(
                "Gifts/Donations",
                "discretionary",
                [
                    "gift",
                    "regalo",
                    "charity",
                    "caridad",
                    "donation",
                    "donacion",
                    "birthday",
                    "cumpleanos",
                    "present",
                ],
                False,
            ),
            CategoryMapping(
                "Misc",
                "discretionary",
                ["other", "otro", "miscellaneous", "varios", "misc"],
                False,
            ),
        ]

    async def process_expense_confirmation(
        self,
        amount: float,
        currency: str,
        date: Optional[datetime],
        merchant: str,
        note: str,
        user_id: int,
        language: Optional[str] = None,
    ) -> ExpenseConfirmation:
        """
        Process an expense and return confirmation details with classification.

        Args:
            amount: Transaction amount
            currency: Currency code (USD, ARS, etc.)
            date: Transaction date (uses today if None)
            merchant: Merchant/vendor name
            note: Additional description
            user_id: User identifier
            language: Optional language code (es/en). If not provided, will auto-detect.

        Returns:
            ExpenseConfirmation with detected language, classification, and UI text
        """
        # Detect language from combined text if not provided
        if not language:
            combined_text = f"{merchant} {note}".strip()
            language = detect_language(combined_text)

        # Use today if no date provided
        if date is None:
            date = datetime.now()

        # Get user memory
        user_memory = await self._get_user_memory(user_id)

        # Classify the expense
        classification = self._classify_expense(merchant, note, user_memory)

        # Build expense object
        expense = {
            "amount": amount,
            "currency": currency,
            "date": date.strftime("%Y-%m-%d"),
            "merchant": merchant,
            "note": note,
        }

        # Generate confirmation text
        ui_text = self._generate_confirmation_text(
            classification["category"], classification["is_necessary"], language
        )

        return ExpenseConfirmation(
            type="expense_confirmation",
            resolved_language=language,
            expense=expense,
            classification=classification,
            memory_updates_if_user_confirms_changes={
                "merchant_to_category": None,
                "merchant_necessity_override": classification["is_necessary"],
            },
            ui_confirmation_text=ui_text,
        )

    def _classify_expense(
        self, merchant: str, note: str, user_memory: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Classify an expense based on merchant, note, and user memory.

        Returns classification with category, necessity flag, confidence, and alternatives.
        """
        combined_text = f"{merchant} {note}".lower()

        # Check user memory first
        merchant_lower = merchant.lower()
        if merchant_lower in user_memory.get("merchant_to_category", {}):
            learned_category = user_memory["merchant_to_category"][merchant_lower]
            learned_necessity = user_memory.get("merchant_necessity_override", {}).get(
                merchant_lower, True
            )

            return {
                "category": learned_category,
                "is_necessary": learned_necessity,
                "confidence": 0.95,  # High confidence for learned preferences
                "alternatives": self._get_alternative_categories(learned_category),
            }

        # Find best matching category
        best_match = None
        best_score = 0
        keyword_matches = 0

        for mapping in self._category_mappings:
            score = 0
            matches = 0
            for keyword in mapping.keywords:
                # Use word boundaries to avoid partial matches like "tax" in "Starbucks"
                pattern = r"\b" + re.escape(keyword) + r"\b"
                if re.search(pattern, combined_text, re.IGNORECASE):
                    score += 1
                    matches += 1

            if score > best_score:
                best_score = score
                best_match = mapping
                keyword_matches = matches

        # Use best match or default to Misc
        if best_match and best_score > 0:
            category = best_match.category
            is_necessary = best_match.necessity
            # Better confidence calculation based on number of matches
            confidence = min(0.9, 0.5 + (keyword_matches * 0.2))
        else:
            category = "Misc"
            is_necessary = False
            confidence = 0.3  # Low confidence for fallback

        return {
            "category": category,
            "is_necessary": is_necessary,
            "confidence": confidence,
            "alternatives": self._get_alternative_categories(category),
        }

    def _get_alternative_categories(
        self, current_category: str
    ) -> List[Dict[str, str]]:
        """Get alternative category suggestions."""
        alternatives = []

        # Get categories from same bucket
        current_bucket = None
        for mapping in self._category_mappings:
            if mapping.category == current_category:
                current_bucket = mapping.bucket
                break

        if current_bucket:
            for mapping in self._category_mappings:
                if (
                    mapping.bucket == current_bucket
                    and mapping.category != current_category
                ):
                    alternatives.append(
                        {
                            "category": mapping.category,
                            "reason": f"Same bucket ({current_bucket})",
                        }
                    )

        # Add some cross-bucket alternatives
        if len(alternatives) < 3:
            common_alternatives = [
                "Groceries",
                "Dining/Delivery",
                "Shopping",
                "Transport",
            ]
            for cat in common_alternatives:
                if cat != current_category and not any(
                    alt["category"] == cat for alt in alternatives
                ):
                    alternatives.append(
                        {
                            "category": cat,
                            "reason": f"Common alternative to {current_category}",
                        }
                    )
                    if len(alternatives) >= 3:
                        break

        return alternatives[:3]  # Limit to 3 alternatives

    def _generate_confirmation_text(
        self, category: str, is_necessary: bool, language: LanguageCode
    ) -> str:
        """Generate confirmation text in the appropriate language."""
        necessity_text = {
            "en": "necessary" if is_necessary else "not necessary",
            "es": "necesario" if is_necessary else "no necesario",
        }

        base_text = {
            "en": f"I detected {category} ({necessity_text[language]}). Change it?",
            "es": f"Detecté {category} ({necessity_text[language]}). ¿Cambiar?",
        }

        return base_text[language]

    async def analyze_period(self, period_text: str, user_id: int) -> AnalysisReport:
        """
        Analyze financial data for a specified period.

        Args:
            period_text: Natural language period description
            user_id: User identifier

        Returns:
            AnalysisReport with comprehensive financial analysis
        """
        # Detect language and parse period
        language = detect_language(period_text)
        start_date, end_date = self._parse_period(period_text, language)

        # Get user memory for budget targets
        user_memory = await self._get_user_memory(user_id)
        budget_targets = user_memory.get(
            "budget_targets",
            {"fixed": 50.0, "variable_necessary": 30.0, "discretionary": 20.0},
        )

        # Query transactions for the period
        async with async_session_maker() as session:
            transactions = await TransactionCRUD.get_by_date_range(
                session, user_id, start_date, end_date
            )

        # Analyze transactions
        analysis = self._analyze_transactions(transactions, budget_targets, language)

        # Generate insights and recommendations
        signals = self._generate_signals(transactions, language)
        recommendations = self._generate_recommendations(analysis, signals, language)

        # Create human-readable summary
        human_summary = self._generate_human_summary(analysis, language)

        return AnalysisReport(
            type="analysis_report",
            resolved_language=language,
            period={
                "start": start_date.strftime("%Y-%m-%d"),
                "end": end_date.strftime("%Y-%m-%d"),
            },
            totals=analysis["totals"],
            budget_targets_pct=budget_targets,
            budget_actual_pct=analysis["actual_pct"],
            signals=signals,
            recommendations=recommendations,
            human_summary=human_summary,
        )

    def _parse_period(
        self, period_text: str, language: LanguageCode
    ) -> Tuple[datetime, datetime]:
        """
        Parse natural language period descriptions into date ranges.

        Supports both English and Spanish:
        - "last month" / "el mes pasado"
        - "this week" / "esta semana"
        - "last 7 days" / "últimos 7 días"
        - Month names: "january" / "enero"
        - Date ranges: "from 2025-08-10 to 2025-08-31"
        """
        period_lower = period_text.lower().strip()
        now = datetime.now()

        # Date range patterns (YYYY-MM-DD format)
        date_range_patterns = [
            r"from\s+(\d{4}-\d{2}-\d{2})\s+to\s+(\d{4}-\d{2}-\d{2})",
            r"desde\s+(\d{4}-\d{2}-\d{2})\s+hasta\s+(\d{4}-\d{2}-\d{2})",
        ]

        for pattern in date_range_patterns:
            match = re.search(pattern, period_lower)
            if match:
                start_str, end_str = match.groups()
                start_date = datetime.strptime(start_str, "%Y-%m-%d")
                end_date = datetime.strptime(end_str, "%Y-%m-%d")
                return start_date, end_date

        # Relative time patterns
        if language == "es":
            return self._parse_spanish_period(period_lower, now)
        else:
            return self._parse_english_period(period_lower, now)

    def _parse_spanish_period(
        self, period_lower: str, now: datetime
    ) -> Tuple[datetime, datetime]:
        """Parse Spanish period expressions."""
        if "hoy" in period_lower:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
            return start, end

        if "ayer" in period_lower:
            start = (now - timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            end = start + timedelta(days=1)
            return start, end

        # "últimos X días"
        match = re.search(r"últimos?\s+(\d+)\s+días?", period_lower)
        if match:
            days = int(match.group(1))
            end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            start = (now - timedelta(days=days - 1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            return start, end

        # Week patterns
        if "esta semana" in period_lower:
            start = now - timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=7)
            return start, end

        if "la semana pasada" in period_lower or "semana anterior" in period_lower:
            current_week_start = now - timedelta(days=now.weekday())
            start = current_week_start - timedelta(days=7)
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=7)
            return start, end

        # Month patterns
        if "este mes" in period_lower:
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                end = start.replace(year=start.year + 1, month=1)
            else:
                end = start.replace(month=start.month + 1)
            return start, end

        if "el mes pasado" in period_lower or "mes anterior" in period_lower:
            if now.month == 1:
                start = now.replace(
                    year=now.year - 1,
                    month=12,
                    day=1,
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=0,
                )
                end = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                start = now.replace(
                    month=now.month - 1,
                    day=1,
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=0,
                )
                end = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            return start, end

        # Year patterns
        if "este año" in period_lower:
            start = now.replace(
                month=1, day=1, hour=0, minute=0, second=0, microsecond=0
            )
            end = start.replace(year=start.year + 1)
            return start, end

        if "el año pasado" in period_lower or "año anterior" in period_lower:
            start = now.replace(
                year=now.year - 1,
                month=1,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )
            end = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            return start, end

        # Spanish month names
        spanish_months = {
            "enero": 1,
            "febrero": 2,
            "marzo": 3,
            "abril": 4,
            "mayo": 5,
            "junio": 6,
            "julio": 7,
            "agosto": 8,
            "septiembre": 9,
            "octubre": 10,
            "noviembre": 11,
            "diciembre": 12,
        }

        for month_name, month_num in spanish_months.items():
            if month_name in period_lower:
                year = now.year
                if month_num > now.month:  # If month is in the future, assume last year
                    year = now.year - 1
                start = datetime(year, month_num, 1)
                if month_num == 12:
                    end = datetime(year + 1, 1, 1)
                else:
                    end = datetime(year, month_num + 1, 1)
                return start, end

        # Default to last 30 days
        end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        start = (now - timedelta(days=29)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        return start, end

    def _parse_english_period(
        self, period_lower: str, now: datetime
    ) -> Tuple[datetime, datetime]:
        """Parse English period expressions."""
        if "today" in period_lower:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
            return start, end

        if "yesterday" in period_lower:
            start = (now - timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            end = start + timedelta(days=1)
            return start, end

        # "last X days"
        match = re.search(r"last\s+(\d+)\s+days?", period_lower)
        if match:
            days = int(match.group(1))
            end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            start = (now - timedelta(days=days - 1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            return start, end

        # Week patterns
        if "this week" in period_lower:
            start = now - timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=7)
            return start, end

        if "last week" in period_lower:
            current_week_start = now - timedelta(days=now.weekday())
            start = current_week_start - timedelta(days=7)
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=7)
            return start, end

        # Month patterns
        if "this month" in period_lower:
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                end = start.replace(year=start.year + 1, month=1)
            else:
                end = start.replace(month=start.month + 1)
            return start, end

        if "last month" in period_lower:
            if now.month == 1:
                start = now.replace(
                    year=now.year - 1,
                    month=12,
                    day=1,
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=0,
                )
                end = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                start = now.replace(
                    month=now.month - 1,
                    day=1,
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=0,
                )
                end = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            return start, end

        # Year patterns
        if "this year" in period_lower:
            start = now.replace(
                month=1, day=1, hour=0, minute=0, second=0, microsecond=0
            )
            end = start.replace(year=start.year + 1)
            return start, end

        if "last year" in period_lower:
            start = now.replace(
                year=now.year - 1,
                month=1,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )
            end = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            return start, end

        # English month names
        english_months = {
            "january": 1,
            "february": 2,
            "march": 3,
            "april": 4,
            "may": 5,
            "june": 6,
            "july": 7,
            "august": 8,
            "september": 9,
            "october": 10,
            "november": 11,
            "december": 12,
        }

        for month_name, month_num in english_months.items():
            if month_name in period_lower:
                year = now.year
                if month_num > now.month:  # If month is in the future, assume last year
                    year = now.year - 1
                start = datetime(year, month_num, 1)
                if month_num == 12:
                    end = datetime(year + 1, 1, 1)
                else:
                    end = datetime(year, month_num + 1, 1)
                return start, end

        # Default to last 30 days
        end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        start = (now - timedelta(days=29)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        return start, end

    def _analyze_transactions(
        self,
        transactions: List,
        budget_targets: Dict[str, float],
        language: LanguageCode,
    ) -> Dict[str, Any]:
        """Analyze transactions and calculate spending by category and bucket."""
        by_category = {}
        by_bucket = {
            "fixed": Decimal("0"),
            "variable_necessary": Decimal("0"),
            "discretionary": Decimal("0"),
        }
        total_expenses = Decimal("0")
        currency = "USD"  # Default currency

        for transaction in transactions:
            if transaction.type == TransactionType.EXPENSE:
                amount = transaction.amount
                total_expenses += amount

                # Use first transaction's currency as reference
                if currency == "USD":
                    currency = transaction.currency

                # Classify transaction (simplified for now - could use description)
                category = self._classify_transaction_to_category(transaction)
                bucket = self._get_bucket_for_category(category)

                # Update totals
                if category not in by_category:
                    by_category[category] = Decimal("0")
                by_category[category] += amount
                by_bucket[bucket] += amount

        # Calculate percentages
        actual_pct = {}
        if total_expenses > 0:
            for bucket, amount in by_bucket.items():
                actual_pct[bucket] = float((amount / total_expenses) * 100)
        else:
            actual_pct = {"fixed": 0.0, "variable_necessary": 0.0, "discretionary": 0.0}

        return {
            "totals": {
                "currency": currency,
                "total_expenses": float(total_expenses),
                "by_bucket": {k: float(v) for k, v in by_bucket.items()},
                "by_category": {k: float(v) for k, v in by_category.items()},
            },
            "actual_pct": actual_pct,
        }

    def _classify_transaction_to_category(self, transaction) -> str:
        """Classify a transaction to a category based on description."""
        description = (transaction.description or "").lower()

        # Simple keyword matching
        for mapping in self._category_mappings:
            for keyword in mapping.keywords:
                if keyword in description:
                    return mapping.category

        return "Misc"

    def _get_bucket_for_category(self, category: str) -> str:
        """Get the bucket for a given category."""
        for mapping in self._category_mappings:
            if mapping.category == category:
                return mapping.bucket
        return "discretionary"  # Default bucket

    def _generate_signals(
        self, transactions: List, language: LanguageCode
    ) -> Dict[str, Any]:
        """Generate financial signals and insights from transaction data."""
        return {
            "outliers": [],
            "small_leaks": [],
            "recurring_merchants": [],
            "possible_duplicates": [],
            "trends_vs_prev_period": {"total_delta_pct": 0.0},
        }

    def _generate_recommendations(
        self, analysis: Dict[str, Any], signals: Dict[str, Any], language: LanguageCode
    ) -> List[Dict[str, Any]]:
        """Generate actionable financial recommendations."""
        recommendations = []

        # Budget adherence recommendations
        totals = analysis["totals"]
        if totals["total_expenses"] > 0:
            discretionary_amount = totals["by_bucket"].get("discretionary", 0)
            if discretionary_amount > totals["total_expenses"] * 0.25:  # More than 25%
                rec = {
                    "title": "Reduce discretionary spending"
                    if language == "en"
                    else "Reducir gastos discrecionales",
                    "rationale": "You're spending more than recommended on discretionary items"
                    if language == "en"
                    else "Estás gastando más de lo recomendado en artículos discrecionales",
                    "est_monthly_savings": discretionary_amount * 0.1,
                    "est_annual_savings": discretionary_amount * 0.1 * 12,
                    "category": "discretionary",
                    "action_steps": [
                        "Review recent transactions in this category"
                        if language == "en"
                        else "Revisar transacciones recientes en esta categoría",
                        "Set spending alerts"
                        if language == "en"
                        else "Configurar alertas de gasto",
                        "Find cheaper alternatives"
                        if language == "en"
                        else "Buscar alternativas más baratas",
                    ],
                }
                recommendations.append(rec)

        return recommendations

    def _generate_human_summary(
        self, analysis: Dict[str, Any], language: LanguageCode
    ) -> str:
        """Generate a human-readable summary of the financial analysis."""
        totals = analysis["totals"]
        currency = totals["currency"]
        total = totals["total_expenses"]

        if language == "es":
            lines = [
                f"• Total de gastos: {total:,.0f} {currency}",
                f"• Fijos: {totals['by_bucket']['fixed']:,.0f} {currency} ({analysis['actual_pct']['fixed']:.0f}%)",
                f"• Variables necesarios: {totals['by_bucket']['variable_necessary']:,.0f} {currency} ({analysis['actual_pct']['variable_necessary']:.0f}%)",
                f"• Discrecionales: {totals['by_bucket']['discretionary']:,.0f} {currency} ({analysis['actual_pct']['discretionary']:.0f}%)",
            ]
        else:
            lines = [
                f"• Total expenses: {currency} {total:,.0f}",
                f"• Fixed: {currency} {totals['by_bucket']['fixed']:,.0f} ({analysis['actual_pct']['fixed']:.0f}%)",
                f"• Variable necessary: {currency} {totals['by_bucket']['variable_necessary']:,.0f} ({analysis['actual_pct']['variable_necessary']:.0f}%)",
                f"• Discretionary: {currency} {totals['by_bucket']['discretionary']:,.0f} ({analysis['actual_pct']['discretionary']:.0f}%)",
            ]

        return "\n".join(lines)

    async def update_budget(self, budget_text: str, user_id: int) -> BudgetUpdate:
        """
        Update user's budget targets from natural language input.

        Args:
            budget_text: Budget description like "50% fixed, 30% necessary, 20% discretionary"
            user_id: User identifier

        Returns:
            BudgetUpdate with normalized percentages and validation
        """
        language = detect_language(budget_text)

        # Parse budget percentages
        percentages = self._parse_budget_percentages(budget_text)

        # Validate and normalize
        validation_notes = []
        total_pct = sum(percentages.values())

        if abs(total_pct - 100.0) > 0.1:  # Allow small rounding errors
            validation_notes.append(
                f"Percentages sum to {total_pct:.1f}%, normalizing to 100%"
                if language == "en"
                else f"Los porcentajes suman {total_pct:.1f}%, normalizando a 100%"
            )

            # Normalize
            if total_pct > 0:
                for bucket in percentages:
                    percentages[bucket] = (percentages[bucket] / total_pct) * 100.0

        # Update user memory
        user_memory = await self._get_user_memory(user_id)
        user_memory["budget_targets"] = percentages
        await self._save_user_memory(user_id, user_memory)

        # Generate confirmation
        confirmation_text = self._format_budget_confirmation(percentages, language)

        return BudgetUpdate(
            type="budget_update",
            resolved_language=language,
            normalized_percentages=percentages,
            validation_notes=validation_notes,
            confirmation_text=confirmation_text,
        )

    def _parse_budget_percentages(self, budget_text: str) -> Dict[str, float]:
        """Parse budget percentages from text input."""
        percentages = {
            "fixed": 50.0,
            "variable_necessary": 30.0,
            "discretionary": 20.0,
        }  # Defaults

        # Extract percentages with various patterns
        patterns = [
            (r"(\d+(?:\.\d+)?)%?\s*(?:fixed|fijo)", "fixed"),
            (
                r"(\d+(?:\.\d+)?)%?\s*(?:necessary|necesario|variable)",
                "variable_necessary",
            ),
            (
                r"(\d+(?:\.\d+)?)%?\s*(?:discretionary|discrecional|optional)",
                "discretionary",
            ),
        ]

        text_lower = budget_text.lower()
        for pattern, bucket in patterns:
            match = re.search(pattern, text_lower)
            if match:
                percentages[bucket] = float(match.group(1))

        return percentages

    def _format_budget_confirmation(
        self, percentages: Dict[str, float], language: LanguageCode
    ) -> str:
        """Format budget confirmation message."""
        if language == "es":
            return (
                f"Presupuesto actualizado: {percentages['fixed']:.1f}% fijo, "
                f"{percentages['variable_necessary']:.1f}% variable necesario, "
                f"{percentages['discretionary']:.1f}% discrecional"
            )
        else:
            return (
                f"Budget updated: {percentages['fixed']:.1f}% fixed, "
                f"{percentages['variable_necessary']:.1f}% variable necessary, "
                f"{percentages['discretionary']:.1f}% discretionary"
            )

    async def update_user_memory(
        self, user_id: int, merchant: str, category: str, is_necessary: bool
    ) -> None:
        """
        Update user memory with learning corrections.

        Args:
            user_id: User identifier
            merchant: Merchant name that was corrected
            category: Corrected category
            is_necessary: Corrected necessity flag
        """
        user_memory = await self._get_user_memory(user_id)

        # Update category mapping
        if "merchant_to_category" not in user_memory:
            user_memory["merchant_to_category"] = {}
        user_memory["merchant_to_category"][merchant.lower()] = category

        # Update necessity override
        if "merchant_necessity_override" not in user_memory:
            user_memory["merchant_necessity_override"] = {}
        user_memory["merchant_necessity_override"][merchant.lower()] = is_necessary

        await self._save_user_memory(user_id, user_memory)

    async def _get_user_memory(self, user_id: int) -> Dict[str, Any]:
        """Get user memory from storage (in-memory for now)."""
        if user_id not in self._user_memory:
            self._user_memory[user_id] = {
                "merchant_to_category": {},
                "merchant_necessity_override": {},
                "budget_targets": {
                    "fixed": 50.0,
                    "variable_necessary": 30.0,
                    "discretionary": 20.0,
                },
            }
        return self._user_memory[user_id]

    async def _save_user_memory(self, user_id: int, memory: Dict[str, Any]) -> None:
        """Save user memory to storage (in-memory for now)."""
        self._user_memory[user_id] = memory
