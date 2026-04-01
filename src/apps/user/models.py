import uuid
from typing import Self

from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base, TimeStampMixin, UUIDPrimaryKeyMixin
from auth.role_types import RoleType


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
    role: Mapped[RoleType] = mapped_column()

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
        role: str = RoleType.USER,
    ) -> Self:
        return cls(
            id=uuid.uuid4(),
            first_name=first_name,
            last_name=last_name,
            email=email.lower(),
            phone=phone,
            password=password,
            role=role,
        )
