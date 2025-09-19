from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TransactionIntent(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    CONVERSION = "conversion"


class ParsedTransactionIntent(BaseModel):
    intent: TransactionIntent = Field(..., description="Type of transaction")
    amount: Decimal = Field(..., description="Amount of money in the transaction", gt=0)
    currency: str = Field(..., description="Currency code (e.g., USD, ARS, USDT)")
    account_from: Optional[str] = Field(None, description="Source account name")
    account_to: Optional[str] = Field(None, description="Destination account name")

    # For conversions
    amount_to: Optional[Decimal] = Field(None, description="Converted amount")
    currency_to: Optional[str] = Field(None, description="Target currency for conversion")
    exchange_rate: Optional[Decimal] = Field(None, description="Exchange rate used")

    # Optional fields
    date: Optional[datetime] = Field(None, description="Transaction date")
    description: Optional[str] = Field(None, description="Transaction description")

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat() if v else None,
        }


class QueryIntent(str, Enum):
    BALANCE = "balance"
    EXPENSES = "expenses"
    INCOME = "income"
    LARGEST_PURCHASE = "largest_purchase"
    SAVINGS = "savings"
    MONTHLY_REPORT = "monthly_report"
    MONTHLY_REPORT_PDF = "monthly_report_pdf"
    ALL_ACCOUNTS = "all_accounts"
    ALL_TRANSACTIONS = "all_transactions"
    ALL_TRANSACTIONS_PDF = "all_transactions_pdf"


class ParsedQueryIntent(BaseModel):
    intent: QueryIntent = Field(..., description="Type of query")
    account_name: Optional[str] = Field(None, description="Specific account to query")
    currency: Optional[str] = Field(None, description="Specific currency to filter by")
    date_expression: Optional[str] = Field(None, description="Original date expression for parsing")
    start_date: Optional[datetime] = Field(None, description="Start date for date range queries")
    end_date: Optional[datetime] = Field(None, description="End date for date range queries")
    month: Optional[int] = Field(None, description="Month for monthly queries (1-12)")
    year: Optional[int] = Field(None, description="Year for monthly queries")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
        }


class BalanceInfo(BaseModel):
    account_name: str
    currency: str
    balance: Decimal
    is_tracked: Optional[bool] = True  # Default to True for backward compatibility

    class Config:
        json_encoders = {Decimal: str}


class TransactionInfo(BaseModel):
    id: int
    type: str
    amount: Decimal
    currency: str
    account_from: Optional[str]
    account_to: Optional[str]
    description: Optional[str]
    date: datetime

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat(),
        }


class MonthlyReport(BaseModel):
    month: int
    year: int
    total_income: Decimal
    total_expenses: Decimal
    net_savings: Decimal
    largest_transaction: Optional[TransactionInfo]
    balances: list[BalanceInfo]

    class Config:
        json_encoders = {Decimal: str}
