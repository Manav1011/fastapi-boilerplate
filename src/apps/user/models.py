from __future__ import annotations
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base, TimeStampMixin, UUIDPrimaryKeyMixin


class UserModel(Base, UUIDPrimaryKeyMixin, TimeStampMixin):
    """
    Model for representing user information.
    """

    __tablename__ = "users"
    first_name: Mapped[str] = mapped_column(index=True)
    last_name: Mapped[str] = mapped_column(index=True)
    email: Mapped[str] = mapped_column(index=True, unique=True)
    phone: Mapped[str] = mapped_column(index=True, unique=True)
    password: Mapped[str] = mapped_column()

    def __str__(self) -> str:
        return f"<{self.first_name} {self.last_name}>"

    @classmethod
    def create(
        cls,
        first_name: str,
        last_name: str,
        phone: str,
        email: str,
        password: str,
    ) -> Self:
        return cls(
            id=uuid.uuid4(),
            first_name=first_name,
            last_name=last_name,
            email=email.lower(),
            phone=phone,
            password=password,
        )


class RefreshTokenModel(Base, UUIDPrimaryKeyMixin, TimeStampMixin):
    """
    Model for refresh tokens stored in DB.
    Token hash is stored (never plain text) for security.
    """

    __tablename__ = "refresh_tokens"

    token_hash: Mapped[str] = mapped_column(index=True, unique=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    revoked: Mapped[bool] = mapped_column(default=False, nullable=False)

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    @property
    def is_active(self) -> bool:
        return not self.revoked and not self.is_expired
