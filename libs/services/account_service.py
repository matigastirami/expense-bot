"""Account service for account management operations."""

from typing import Optional, List
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.crud import AccountCRUD, AccountBalanceCRUD
from libs.db.models import Account, AccountType, AccountBalance, BalanceTrackingMode, User
from libs.validators import validate_account_name, validate_account_type, validate_currency
from sqlalchemy import select


class AccountService:
    """Service for account-related operations."""

    @staticmethod
    async def create_account(
        session: AsyncSession,
        user_id: int,
        name: str,
        account_type: str,
        track_balance: Optional[bool] = None,
    ) -> tuple[Optional[Account], Optional[str]]:
        """
        Create a new account for a user.

        Args:
            session: Database session
            user_id: User ID
            name: Account name
            account_type: Account type (bank, wallet, cash, other)
            track_balance: Whether to track balance for this account (None = use user default)

        Returns:
            Tuple of (account, error_message). If successful, account is not None and error is None.
        """
        # Validate account name
        is_valid, error = validate_account_name(name)
        if not is_valid:
            return None, error

        # Validate account type
        is_valid, error = validate_account_type(account_type)
        if not is_valid:
            return None, error

        # Normalize name (strip whitespace)
        name = name.strip()

        # Check if account with this name already exists for this user
        existing_account = await AccountCRUD.get_by_name(session=session, user_id=user_id, name=name)
        if existing_account:
            return None, f"Account with name '{name}' already exists"

        # Create account
        account_type_enum = AccountType(account_type.lower())
        account = await AccountCRUD.create(
            session=session,
            user_id=user_id,
            name=name,
            account_type=account_type_enum,
        )

        # Set track_balance if provided
        if track_balance is not None:
            account.track_balance = track_balance
            await session.commit()
            await session.refresh(account)

        return account, None

    @staticmethod
    async def get_account_by_name(
        session: AsyncSession,
        user_id: int,
        name: str,
    ) -> Optional[Account]:
        """
        Get account by name for a specific user.

        Args:
            session: Database session
            user_id: User ID
            name: Account name

        Returns:
            Account if found, None otherwise
        """
        return await AccountCRUD.get_by_name(session=session, user_id=user_id, name=name.strip())

    @staticmethod
    async def get_or_create_account(
        session: AsyncSession,
        user_id: int,
        name: str,
        account_type: AccountType = AccountType.OTHER,
    ) -> Account:
        """
        Get existing account by name or create a new one.

        Args:
            session: Database session
            user_id: User ID
            name: Account name
            account_type: Account type (default: OTHER)

        Returns:
            Account (existing or newly created)
        """
        return await AccountCRUD.get_or_create(
            session=session,
            user_id=user_id,
            name=name.strip(),
            account_type=account_type,
        )

    @staticmethod
    async def list_accounts(
        session: AsyncSession,
        user_id: int,
        include_balances: bool = True,
    ) -> List[Account]:
        """
        List all accounts for a user.

        Args:
            session: Database session
            user_id: User ID
            include_balances: Whether to include balance information

        Returns:
            List of accounts
        """
        if include_balances:
            return await AccountCRUD.get_all_with_balances(session=session, user_id=user_id)
        else:
            result = await session.execute(
                select(Account).where(Account.user_id == user_id)
            )
            return list(result.scalars().all())

    @staticmethod
    async def get_account_balance(
        session: AsyncSession,
        account_id: int,
        currency: str,
    ) -> Optional[Decimal]:
        """
        Get balance for a specific account and currency.

        Args:
            session: Database session
            account_id: Account ID
            currency: Currency code

        Returns:
            Balance as Decimal if found, None otherwise
        """
        # Validate currency
        is_valid, error = validate_currency(currency)
        if not is_valid:
            return None

        balance = await AccountBalanceCRUD.get_balance(
            session=session,
            account_id=account_id,
            currency=currency.upper(),
        )

        return balance.balance if balance else None

    @staticmethod
    async def update_account_balance(
        session: AsyncSession,
        account_id: int,
        currency: str,
        amount: Decimal,
    ) -> tuple[Optional[AccountBalance], Optional[str]]:
        """
        Update (set) account balance to a specific amount.

        Args:
            session: Database session
            account_id: Account ID
            currency: Currency code
            amount: New balance amount

        Returns:
            Tuple of (account_balance, error_message)
        """
        # Validate currency
        is_valid, error = validate_currency(currency)
        if not is_valid:
            return None, error

        if amount < 0:
            return None, "Balance cannot be negative"

        balance = await AccountBalanceCRUD.update_balance(
            session=session,
            account_id=account_id,
            currency=currency.upper(),
            amount=amount,
        )

        return balance, None

    @staticmethod
    async def add_to_account_balance(
        session: AsyncSession,
        account_id: int,
        currency: str,
        amount: Decimal,
    ) -> tuple[Optional[AccountBalance], Optional[str]]:
        """
        Add to account balance (can be positive or negative).

        Args:
            session: Database session
            account_id: Account ID
            currency: Currency code
            amount: Amount to add (negative to subtract)

        Returns:
            Tuple of (account_balance, error_message)
        """
        # Validate currency
        is_valid, error = validate_currency(currency)
        if not is_valid:
            return None, error

        balance = await AccountBalanceCRUD.add_to_balance(
            session=session,
            account_id=account_id,
            currency=currency.upper(),
            amount=amount,
        )

        return balance, None

    @staticmethod
    async def should_track_balance(
        session: AsyncSession,
        user_id: int,
        account_id: int,
    ) -> bool:
        """
        Check if balance tracking should be enabled for an account.

        Args:
            session: Database session
            user_id: User ID
            account_id: Account ID

        Returns:
            True if balance should be tracked, False otherwise
        """
        # Get user's balance tracking mode
        user_result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one()

        # Get account's specific setting
        account_result = await session.execute(
            select(Account).where(Account.id == account_id)
        )
        account = account_result.scalar_one()

        # Account-specific setting overrides user setting
        if account.track_balance is not None:
            return account.track_balance
        else:
            # Fall back to user's general setting
            return str(user.balance_tracking_mode) == "strict"

    @staticmethod
    async def get_all_balances(
        session: AsyncSession,
        user_id: int,
        account_name: Optional[str] = None,
    ) -> List[dict]:
        """
        Get all balances for a user, optionally filtered by account.

        Args:
            session: Database session
            user_id: User ID
            account_name: Optional account name filter

        Returns:
            List of balance dictionaries with account info
        """
        if account_name:
            account = await AccountCRUD.get_by_name(session, user_id, account_name)
            if not account:
                return []
            accounts = [account]
        else:
            accounts = await AccountCRUD.get_all_with_balances(session, user_id)

        balances = []
        for account in accounts:
            should_track = await AccountService.should_track_balance(session, user_id, account.id)

            if should_track:
                # Show actual balances for tracked accounts
                for balance in account.balances:
                    if balance.balance > 0:  # Only show non-zero balances
                        balances.append({
                            "account_id": account.id,
                            "account_name": account.name,
                            "account_type": account.type,
                            "currency": balance.currency,
                            "balance": float(balance.balance),
                            "is_tracked": True,
                        })
            else:
                # Show "Not tracked" status for non-tracked accounts
                balances.append({
                    "account_id": account.id,
                    "account_name": account.name,
                    "account_type": account.type,
                    "currency": "N/A",
                    "balance": None,
                    "is_tracked": False,
                })

        return balances
