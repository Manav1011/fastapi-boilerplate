import uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class TimeStampMixin:
    """
    A mixin class to add automatic timestamp fields.

    Adds `created_at` and `updated_at` fields to a model,
    automatically set to the current UTC time on creation and updated on modification.
    """

    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        server_default=func.now(),
        onupdate=datetime.utcnow,
        nullable=False,
    )


class UUIDPrimaryKeyMixin:
    """
    A mixin class to add a primary key field in a model.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4(), nullable=False
    )


class Base(DeclarativeBase):
    """
    Base class for defining database tables.
    """

    pass
