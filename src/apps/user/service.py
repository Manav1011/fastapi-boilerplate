import hashlib
from datetime import datetime, timedelta
from uuid import UUID

from .exceptions import (
    DuplicateEmailException,
    InvalidCredentialsException,
    UserNotFoundException,
)
from .models import UserModel
from .repository import UserRepository
from auth.password import hash_password, verify_password
from auth.jwt import create_tokens
from exceptions import UnauthorizedError
from config import settings


class UserService:
    """Business logic for user operations."""

    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    async def get_self(self, user_id: UUID) -> UserModel:
        return await self.repository.get_by_id(user_id)

    async def login_user(self, email: str, password: str) -> dict[str, str]:
        user = await self.repository.get_by_email(email)
        if not user:
            raise InvalidCredentialsException

        if not await verify_password(hashed_password=user.password, plain_password=password):
            raise InvalidCredentialsException

        return await create_tokens(user_id=user.id)

    async def create_user(
        self,
        first_name: str,
        last_name: str,
        email: str,
        phone: str,
        password: str,
    ) -> UserModel:
        existing = await self.repository.get_by_email_or_phone(email, phone)
        if existing:
            raise DuplicateEmailException

        user = UserModel.create(
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            password=await hash_password(password),
            email=email,
        )
        self.repository.add(user)
        await self.repository.session.commit()
        await self.repository.session.refresh(user)
        return user

    async def get_user_by_id(self, user_id: UUID) -> UserModel:
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundException
        return user

    async def delete_user_by_id(self, user_id: UUID) -> UserModel:
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundException
        await self.repository.delete(user_id)
        await self.repository.session.commit()
        return user

    async def logout_user(self, refresh_token: str) -> None:
        """Revoke a refresh token (logout)."""
        token_hash = self._hash_token(refresh_token)
        await self.repository.revoke_refresh_token(token_hash)
        await self.repository.session.commit()

    async def refresh_user(self, refresh_token: str) -> dict[str, str]:
        """
        Validate refresh token and rotate: revoke old, issue new pair.
        Returns new TokenPair.
        Raises UnauthorizedError if token invalid/expired/revoked.
        """
        token_hash = self._hash_token(refresh_token)
        token_record = await self.repository.get_refresh_token(token_hash)

        if not token_record:
            raise UnauthorizedError(message="Invalid refresh token")

        if not token_record.is_active:
            raise UnauthorizedError(message="Refresh token expired or revoked")

        # Get user
        user = await self.repository.get_by_id(token_record.user_id)
        if not user:
            raise UnauthorizedError(message="User not found")

        # Revoke old token
        await self.repository.revoke_refresh_token(token_hash)

        # Issue new tokens
        new_tokens = await create_tokens(user.id)

        # Store new refresh token in DB
        await self.repository.create_refresh_token(
            token_hash=self._hash_token(new_tokens["refresh_token"]),
            user_id=user.id,
            expires_at=datetime.utcnow() + timedelta(seconds=int(settings.REFRESH_TOKEN_EXP)),
        )
        await self.repository.session.commit()

        return new_tokens

    @staticmethod
    def _hash_token(token: str) -> str:
        """Hash a refresh token for storage (never store plain)."""
        return hashlib.sha256(token.encode()).hexdigest()
