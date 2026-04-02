from typing import Optional, TYPE_CHECKING
from uuid import UUID
from datetime import datetime

from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only

from .models import UserModel, RefreshTokenModel
from auth.role_types import RoleType

if TYPE_CHECKING:
    from .service import UserService


class UserRepository:
    """Data access layer for UserModel."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @property
    def session(self) -> AsyncSession:
        return self._session

    async def get_by_id(self, user_id: UUID) -> Optional[UserModel]:
        return await self._session.scalar(
            select(UserModel)
            .options(load_only(UserModel.id, UserModel.email, UserModel.first_name, UserModel.last_name))
            .where(UserModel.id == user_id)
        )

    async def get_by_email(self, email: str) -> Optional[UserModel]:
        return await self._session.scalar(
            select(UserModel).where(UserModel.email == email)
        )

    async def get_by_email_or_phone(self, email: str, phone: str) -> Optional[UserModel]:
        return await self._session.scalar(
            select(UserModel)
            .options(load_only(UserModel.email))
            .where(or_(UserModel.email == email, UserModel.phone == phone))
        )

    async def get_by_email_role(self, email: str, role: RoleType) -> Optional[UserModel]:
        return await self._session.scalar(
            select(UserModel).where(
                and_(UserModel.email == email, UserModel.role == role)
            )
        )

    async def delete(self, user_id: UUID) -> None:
        user = await self._session.scalar(
            select(UserModel).where(UserModel.id == user_id)
        )
        if user:
            await self._session.delete(user)

    def add(self, user: UserModel) -> None:
        self._session.add(user)

    async def create_refresh_token(
        self, token_hash: str, user_id: UUID, expires_at: datetime
    ) -> RefreshTokenModel:
        """Create a new refresh token record."""
        token = RefreshTokenModel(
            token_hash=token_hash,
            user_id=user_id,
            expires_at=expires_at,
            revoked=False,
        )
        self._session.add(token)
        await self._session.flush()
        return token

    async def get_refresh_token(self, token_hash: str) -> Optional[RefreshTokenModel]:
        """Get refresh token by hash if it exists and is active."""
        return await self._session.scalar(
            select(RefreshTokenModel).where(
                and_(
                    RefreshTokenModel.token_hash == token_hash,
                    RefreshTokenModel.revoked == False,
                )
            )
        )

    async def revoke_refresh_token(self, token_hash: str) -> None:
        """Mark a refresh token as revoked."""
        token = await self._session.scalar(
            select(RefreshTokenModel).where(RefreshTokenModel.token_hash == token_hash)
        )
        if token:
            token.revoked = True
            await self._session.flush()

    async def revoke_all_user_tokens(self, user_id: UUID) -> None:
        """Revoke all refresh tokens for a user (used on password change, etc)."""
        await self._session.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.user_id == user_id)
            .values(revoked=True)
        )
        await self._session.flush()
