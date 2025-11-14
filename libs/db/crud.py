from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import and_, desc, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from libs.db.models import (
    Account,
    AccountBalance,
    AccountType,
    Category,
    CategoryType,
    ExchangeRate,
    Merchant,
    PendingTransaction,
    Transaction,
    TransactionType,
    User,
)


class UserCRUD:
    @staticmethod
    async def get_by_telegram_id(
        session: AsyncSession, telegram_user_id: str
    ) -> Optional[User]:
        result = await session.execute(
            select(User).where(User.telegram_user_id == telegram_user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        session: AsyncSession,
        telegram_user_id: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        username: Optional[str] = None,
        language_code: Optional[str] = None,
        email: Optional[str] = None,
        phone_number: Optional[str] = None,
        password: Optional[str] = None
    ) -> User:
        user = User(
            telegram_user_id=telegram_user_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
            language_code=language_code,
            email=email,
            phone_number=phone_number,
            password=password
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    @staticmethod
    async def get_or_create(
        session: AsyncSession,
        telegram_user_id: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        username: Optional[str] = None,
        language_code: Optional[str] = None,
    ) -> User:
        user = await UserCRUD.get_by_telegram_id(session, telegram_user_id)
        if not user:
            user = await UserCRUD.create(
                session,
                telegram_user_id,
                first_name,
                last_name,
                username,
                language_code,
            )
        return user

    @staticmethod
    async def get_by_email(session: AsyncSession, email: int) -> Optional[User]:
        result = await session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_last_activity(session: AsyncSession, user_id: int) -> None:
        await session.execute(
            update(User).where(User.id == user_id).values(updated_at=func.now())
        )
        await session.commit()


class AccountCRUD:
    @staticmethod
    async def get_by_name(
        session: AsyncSession, user_id: int, name: str
    ) -> Optional[Account]:
        result = await session.execute(
            select(Account)
            .where(and_(Account.user_id == user_id, Account.name == name))
            .options(selectinload(Account.balances))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        session: AsyncSession, user_id: int, name: str, account_type: AccountType
    ) -> Account:
        # Use the enum value (string) instead of the enum itself
        account = Account(user_id=user_id, name=name, type=account_type.value)
        session.add(account)
        await session.commit()
        await session.refresh(account)
        return account

    @staticmethod
    async def get_all_with_balances(
        session: AsyncSession, user_id: int
    ) -> List[Account]:
        result = await session.execute(
            select(Account)
            .where(Account.user_id == user_id)
            .options(selectinload(Account.balances))
        )
        return result.scalars().all()

    @staticmethod
    async def get_or_create(
        session: AsyncSession,
        user_id: int,
        name: str,
        account_type: AccountType = AccountType.OTHER,
    ) -> Account:
        account = await AccountCRUD.get_by_name(session, user_id, name)
        if not account:
            account = await AccountCRUD.create(session, user_id, name, account_type)
        return account


class AccountBalanceCRUD:
    @staticmethod
    async def get_balance(
        session: AsyncSession, account_id: int, currency: str
    ) -> Optional[AccountBalance]:
        result = await session.execute(
            select(AccountBalance).where(
                and_(
                    AccountBalance.account_id == account_id,
                    AccountBalance.currency == currency,
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_balance(
        session: AsyncSession, account_id: int, currency: str, amount: Decimal
    ) -> AccountBalance:
        balance = await AccountBalanceCRUD.get_balance(session, account_id, currency)

        if balance:
            balance.balance = amount
            balance.updated_at = func.now()
        else:
            balance = AccountBalance(
                account_id=account_id, currency=currency, balance=amount
            )
            session.add(balance)

        await session.commit()
        await session.refresh(balance)
        return balance

    @staticmethod
    async def add_to_balance(
        session: AsyncSession, account_id: int, currency: str, amount: Decimal
    ) -> AccountBalance:
        balance = await AccountBalanceCRUD.get_balance(session, account_id, currency)

        if balance:
            balance.balance += amount
            balance.updated_at = func.now()
        else:
            balance = AccountBalance(
                account_id=account_id, currency=currency, balance=amount
            )
            session.add(balance)

        await session.commit()
        await session.refresh(balance)
        return balance


class TransactionCRUD:
    @staticmethod
    async def create(
        session: AsyncSession,
        user_id: int,
        transaction_type: TransactionType,
        currency: str,
        amount: Decimal,
        date: datetime,
        account_from_id: Optional[int] = None,
        account_to_id: Optional[int] = None,
        category_id: Optional[int] = None,
        merchant_id: Optional[int] = None,
        currency_to: Optional[str] = None,
        amount_to: Optional[Decimal] = None,
        exchange_rate: Optional[Decimal] = None,
        description: Optional[str] = None,
        is_necessary: Optional[bool] = None,
    ) -> Transaction:
        transaction = Transaction(
            user_id=user_id,
            type=transaction_type,
            account_from_id=account_from_id,
            account_to_id=account_to_id,
            category_id=category_id,
            merchant_id=merchant_id,
            currency=currency,
            amount=amount,
            currency_to=currency_to,
            amount_to=amount_to,
            exchange_rate=exchange_rate,
            description=description,
            is_necessary=is_necessary,
            date=date,
        )
        session.add(transaction)
        await session.commit()

        # Eagerly load relationships to avoid lazy loading issues
        result = await session.execute(
            select(Transaction)
            .where(Transaction.id == transaction.id)
            .options(
                selectinload(Transaction.account_from),
                selectinload(Transaction.account_to),
                selectinload(Transaction.category),
                selectinload(Transaction.merchant),
            )
        )
        return result.scalar_one()

    @staticmethod
    async def get_by_date_range(
        session: AsyncSession,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        account_id: Optional[int] = None,
        limit: Optional[int] = 10,
        offset: Optional[int] = 0,
    ) -> List[Transaction]:
        query = (
            select(Transaction)
            .where(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.date >= start_date,
                    Transaction.date <= end_date,
                )
            )
            .options(
                selectinload(Transaction.account_from),
                selectinload(Transaction.account_to),
                selectinload(Transaction.category),
                selectinload(Transaction.merchant),
            )
            .order_by(desc(Transaction.date))
            .limit(limit)
            .offset(offset)
        )

        if account_id:
            query = query.where(
                or_(
                    Transaction.account_from_id == account_id,
                    Transaction.account_to_id == account_id,
                )
            )

        result = await session.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_largest_in_period(
        session: AsyncSession,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        transaction_type: Optional[TransactionType] = None,
    ) -> Optional[Transaction]:
        query = (
            select(Transaction)
            .where(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.date >= start_date,
                    Transaction.date <= end_date,
                )
            )
            .options(
                selectinload(Transaction.account_from),
                selectinload(Transaction.account_to),
            )
            .order_by(desc(Transaction.amount))
            .limit(1)
        )

        if transaction_type:
            query = query.where(Transaction.type == transaction_type)

        result = await session.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_total_by_type(
        session: AsyncSession,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        transaction_type: TransactionType,
        currency: Optional[str] = None,
    ) -> Decimal:
        query = select(func.sum(Transaction.amount)).where(
            and_(
                Transaction.user_id == user_id,
                Transaction.date >= start_date,
                Transaction.date <= end_date,
                Transaction.type == transaction_type,
            )
        )

        if currency:
            query = query.where(Transaction.currency == currency)

        result = await session.execute(query)
        total = result.scalar()
        return total or Decimal("0")


class ExchangeRateCRUD:
    @staticmethod
    async def get_latest_rate(
        session: AsyncSession, pair: str
    ) -> Optional[ExchangeRate]:
        result = await session.execute(
            select(ExchangeRate)
            .where(ExchangeRate.pair == pair)
            .order_by(desc(ExchangeRate.fetched_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        session: AsyncSession,
        pair: str,
        value: Decimal,
        source: str,
        fetched_at: datetime,
    ) -> ExchangeRate:
        rate = ExchangeRate(
            pair=pair, value=value, source=source, fetched_at=fetched_at
        )
        session.add(rate)
        await session.commit()
        await session.refresh(rate)
        return rate


class PendingTransactionCRUD:
    @staticmethod
    async def create(
        session: AsyncSession,
        user_id: int,
        transaction_type: TransactionType,
        currency: str,
        amount: Decimal,
        date: datetime,
        account_from_id: Optional[int] = None,
        account_to_id: Optional[int] = None,
        category_id: Optional[int] = None,
        merchant_id: Optional[int] = None,
        currency_to: Optional[str] = None,
        amount_to: Optional[Decimal] = None,
        exchange_rate: Optional[Decimal] = None,
        description: Optional[str] = None,
        is_necessary: Optional[bool] = None,
        last_error: Optional[str] = None,
    ) -> PendingTransaction:
        pending_tx = PendingTransaction(
            user_id=user_id,
            transaction_type=transaction_type,
            account_from_id=account_from_id,
            account_to_id=account_to_id,
            category_id=category_id,
            merchant_id=merchant_id,
            currency=currency,
            amount=amount,
            currency_to=currency_to,
            amount_to=amount_to,
            exchange_rate=exchange_rate,
            description=description,
            is_necessary=is_necessary,
            date=date,
            retry_count=0,
            last_error=last_error,
        )
        session.add(pending_tx)
        await session.commit()
        await session.refresh(pending_tx)
        return pending_tx

    @staticmethod
    async def get_pending_with_low_retry_count(
        session: AsyncSession, max_retry_count: int = 10, user_id: Optional[int] = None
    ) -> List[PendingTransaction]:
        query = (
            select(PendingTransaction)
            .where(PendingTransaction.retry_count < max_retry_count)
            .options(
                selectinload(PendingTransaction.account_from),
                selectinload(PendingTransaction.account_to),
            )
            .order_by(PendingTransaction.created_at)
        )

        if user_id:
            query = query.where(PendingTransaction.user_id == user_id)

        result = await session.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update_retry_info(
        session: AsyncSession,
        pending_id: int,
        retry_count: int,
        last_error: Optional[str] = None,
    ) -> None:
        await session.execute(
            update(PendingTransaction)
            .where(PendingTransaction.id == pending_id)
            .values(
                retry_count=retry_count,
                last_error=last_error,
                updated_at=func.now(),
            )
        )
        await session.commit()

    @staticmethod
    async def delete(session: AsyncSession, pending_id: int) -> None:
        result = await session.execute(
            select(PendingTransaction).where(PendingTransaction.id == pending_id)
        )
        pending_tx = result.scalar_one_or_none()
        if pending_tx:
            await session.delete(pending_tx)
            await session.commit()


class CategoryCRUD:
    @staticmethod
    async def get_all(session: AsyncSession, user_id: int) -> List[Category]:
        result = await session.execute(
            select(Category)
            .where(Category.user_id == user_id)
            .order_by(Category.type, Category.name)
        )
        return result.scalars().all()

    @staticmethod
    async def get_by_id(
        session: AsyncSession, user_id: int, category_id: int
    ) -> Optional[Category]:
        result = await session.execute(
            select(Category).where(
                and_(Category.id == category_id, Category.user_id == user_id)
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_name(
        session: AsyncSession, user_id: int, name: str
    ) -> Optional[Category]:
        result = await session.execute(
            select(Category).where(
                and_(Category.user_id == user_id, Category.name == name)
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        session: AsyncSession, user_id: int, name: str, category_type: CategoryType
    ) -> Category:
        category = Category(
            user_id=user_id,
            name=name,
            type=category_type.value if isinstance(category_type, CategoryType) else category_type
        )
        session.add(category)
        await session.commit()
        await session.refresh(category)
        return category

    @staticmethod
    async def update(
        session: AsyncSession,
        category_id: int,
        user_id: int,
        name: Optional[str] = None,
        category_type: Optional[CategoryType] = None,
    ) -> Optional[Category]:
        category = await CategoryCRUD.get_by_id(session, user_id, category_id)
        if not category:
            return None

        if name is not None:
            category.name = name
        if category_type is not None:
            category.type = category_type.value if isinstance(category_type, CategoryType) else category_type

        await session.commit()
        await session.refresh(category)
        return category

    @staticmethod
    async def delete(session: AsyncSession, category_id: int, user_id: int) -> bool:
        category = await CategoryCRUD.get_by_id(session, user_id, category_id)
        if not category:
            return False

        await session.delete(category)
        await session.commit()
        return True


class MerchantCRUD:
    @staticmethod
    async def get_all(session: AsyncSession, user_id: int) -> List[Merchant]:
        result = await session.execute(
            select(Merchant)
            .where(Merchant.user_id == user_id)
            .order_by(Merchant.name)
        )
        return result.scalars().all()

    @staticmethod
    async def get_by_id(
        session: AsyncSession, user_id: int, merchant_id: int
    ) -> Optional[Merchant]:
        result = await session.execute(
            select(Merchant).where(
                and_(Merchant.id == merchant_id, Merchant.user_id == user_id)
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_name(
        session: AsyncSession, user_id: int, name: str
    ) -> Optional[Merchant]:
        result = await session.execute(
            select(Merchant).where(
                and_(Merchant.user_id == user_id, Merchant.name == name)
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        session: AsyncSession, user_id: int, name: str
    ) -> Merchant:
        merchant = Merchant(user_id=user_id, name=name)
        session.add(merchant)
        await session.commit()
        await session.refresh(merchant)
        return merchant

    @staticmethod
    async def update(
        session: AsyncSession,
        merchant_id: int,
        user_id: int,
        name: str,
    ) -> Optional[Merchant]:
        merchant = await MerchantCRUD.get_by_id(session, user_id, merchant_id)
        if not merchant:
            return None

        merchant.name = name
        await session.commit()
        await session.refresh(merchant)
        return merchant

    @staticmethod
    async def delete(session: AsyncSession, merchant_id: int, user_id: int) -> bool:
        merchant = await MerchantCRUD.get_by_id(session, user_id, merchant_id)
        if not merchant:
            return False

        await session.delete(merchant)
        await session.commit()
        return True
