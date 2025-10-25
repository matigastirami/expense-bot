"""User service for authentication and user management."""

from typing import Optional
import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.crud import UserCRUD
from libs.db.models import User
from libs.validators import validate_email, validate_password


class UserService:
    """Service for user-related operations."""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt with salt rounds.

        Args:
            password: Plain text password

        Returns:
            Hashed password string
        """
        salt = bcrypt.gensalt(rounds=12)  # 12 salt rounds (good balance of security/performance)
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain password against a hashed password.

        Args:
            plain_password: Plain text password
            hashed_password: Hashed password from database

        Returns:
            True if password matches, False otherwise
        """
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )

    @staticmethod
    async def create_user(
        session: AsyncSession,
        email: str,
        password: str,
        language_code: Optional[str] = None,
    ) -> tuple[Optional[User], Optional[str]]:
        """
        Create a new user with email and password.

        Args:
            session: Database session
            email: User email address
            password: User password (will be hashed)
            language_code: Optional language code

        Returns:
            Tuple of (user, error_message). If successful, user is not None and error is None.
        """
        # Validate email
        is_valid, error = validate_email(email)
        if not is_valid:
            return None, error

        # Validate password
        is_valid, error = validate_password(password)
        if not is_valid:
            return None, error

        # Normalize email
        email = email.strip().lower()

        # Check if user already exists
        existing_user = await UserCRUD.get_by_email(session=session, email=email)
        if existing_user:
            return None, "User with this email already exists"

        # Hash password
        hashed_password = UserService.hash_password(password)

        # Create user
        user = await UserCRUD.create(
            session=session,
            email=email,
            password=hashed_password,
            language_code=language_code,
        )

        return user, None

    @staticmethod
    async def authenticate_user(
        session: AsyncSession,
        email: str,
        password: str,
    ) -> tuple[Optional[User], Optional[str]]:
        """
        Authenticate a user with email and password.

        Args:
            session: Database session
            email: User email address
            password: User password

        Returns:
            Tuple of (user, error_message). If successful, user is not None and error is None.
        """
        # Normalize email
        email = email.strip().lower()

        # Get user by email
        user = await UserCRUD.get_by_email(session=session, email=email)

        # Check if user exists and verify password
        if user is None or not UserService.verify_password(password, user.password):
            return None, "Invalid email or password"

        # Check if user is active
        if not user.is_active:
            return None, "User account is disabled"

        return user, None

    @staticmethod
    async def get_user_by_id(
        session: AsyncSession,
        user_id: int,
    ) -> Optional[User]:
        """
        Get user by ID.

        Args:
            session: Database session
            user_id: User ID

        Returns:
            User if found, None otherwise
        """
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_email(
        session: AsyncSession,
        email: str,
    ) -> Optional[User]:
        """
        Get user by email.

        Args:
            session: Database session
            email: User email address

        Returns:
            User if found, None otherwise
        """
        email = email.strip().lower()
        return await UserCRUD.get_by_email(session=session, email=email)

    @staticmethod
    async def get_user_by_telegram_id(
        session: AsyncSession,
        telegram_user_id: str,
    ) -> Optional[User]:
        """
        Get user by Telegram user ID.

        Args:
            session: Database session
            telegram_user_id: Telegram user ID

        Returns:
            User if found, None otherwise
        """
        return await UserCRUD.get_by_telegram_id(session=session, telegram_user_id=telegram_user_id)
