from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Enum as SQLEnum

from src.db.base import Base


class AccountType(str, Enum):
    BANK = "bank"
    WALLET = "wallet"
    CASH = "cash"
    OTHER = "other"


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    CONVERSION = "conversion"


class BalanceTrackingMode(str, Enum):
    STRICT = "strict"
    LOGGING = "logging"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_user_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    language_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    balance_tracking_mode: Mapped[str] = mapped_column(
        SQLEnum('strict', 'logging', name='balancetrackingmode', native_enum=True),
        default=BalanceTrackingMode.STRICT,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    accounts: Mapped[list["Account"]] = relationship(
        "Account", back_populates="user", cascade="all, delete-orphan"
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction", back_populates="user", cascade="all, delete-orphan"
    )
    pending_transactions: Mapped[list["PendingTransaction"]] = relationship(
        "PendingTransaction", back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_users_telegram_user_id", "telegram_user_id"),
    )


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(SQLEnum('bank', 'wallet', 'cash', 'other', name='accounttype', native_enum=True), nullable=False)
    track_balance: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="accounts")
    balances: Mapped[list["AccountBalance"]] = relationship(
        "AccountBalance", back_populates="account", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_user_account_name"),
        Index("ix_accounts_user_id", "user_id"),
    )


class AccountBalance(Base):
    __tablename__ = "account_balances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("accounts.id"), nullable=False
    )
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    balance: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=8), nullable=False, default=0
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    account: Mapped["Account"] = relationship("Account", back_populates="balances")

    __table_args__ = (
        UniqueConstraint("account_id", "currency", name="uq_account_currency"),
        Index("ix_account_balances_account_id", "account_id"),
        CheckConstraint("balance >= 0", name="ck_balance_non_negative"),
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    type: Mapped[str] = mapped_column(
        SQLEnum('income', 'expense', 'transfer', 'conversion', name='transactiontype', native_enum=True), nullable=False
    )
    account_from_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("accounts.id"), nullable=True
    )
    account_to_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("accounts.id"), nullable=True
    )
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=8), nullable=False
    )
    currency_to: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    amount_to: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=20, scale=8), nullable=True
    )
    exchange_rate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=20, scale=8), nullable=True
    )
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="transactions")
    account_from: Mapped[Optional["Account"]] = relationship(
        "Account", foreign_keys=[account_from_id]
    )
    account_to: Mapped[Optional["Account"]] = relationship(
        "Account", foreign_keys=[account_to_id]
    )

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_amount_positive"),
        CheckConstraint(
            "amount_to IS NULL OR amount_to > 0", name="ck_amount_to_positive"
        ),
        CheckConstraint(
            "exchange_rate IS NULL OR exchange_rate > 0", name="ck_rate_positive"
        ),
        Index("ix_transactions_user_id", "user_id"),
        Index("ix_transactions_date", "date"),
        Index("ix_transactions_type", "type"),
    )


class ExchangeRate(Base):
    __tablename__ = "exchange_rates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pair: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g., "USDT/ARS"
    value: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=8), nullable=False
    )
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        CheckConstraint("value > 0", name="ck_rate_value_positive"),
        Index("ix_exchange_rates_pair", "pair"),
        Index("ix_exchange_rates_fetched_at", "fetched_at"),
    )


class PendingTransaction(Base):
    __tablename__ = "pending_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    transaction_type: Mapped[str] = mapped_column(
        SQLEnum('income', 'expense', 'transfer', 'conversion', name='transactiontype', native_enum=True), nullable=False
    )
    account_from_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("accounts.id"), nullable=True
    )
    account_to_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("accounts.id"), nullable=True
    )
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=8), nullable=False
    )
    currency_to: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    amount_to: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=20, scale=8), nullable=True
    )
    exchange_rate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=20, scale=8), nullable=True
    )
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="pending_transactions")
    account_from: Mapped[Optional["Account"]] = relationship(
        "Account", foreign_keys=[account_from_id]
    )
    account_to: Mapped[Optional["Account"]] = relationship(
        "Account", foreign_keys=[account_to_id]
    )

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_pending_amount_positive"),
        CheckConstraint(
            "amount_to IS NULL OR amount_to > 0", name="ck_pending_amount_to_positive"
        ),
        CheckConstraint("retry_count >= 0", name="ck_pending_retry_count_non_negative"),
        Index("ix_pending_transactions_user_id", "user_id"),
        Index("ix_pending_transactions_created_at", "created_at"),
        Index("ix_pending_transactions_retry_count", "retry_count"),
    )
