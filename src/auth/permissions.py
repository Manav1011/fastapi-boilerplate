from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import constants.messages as constants
from db.session import db_session
from exceptions import UnauthorizedError

from auth.jwt import access


class HasPermission:
    """
    A Dependency Injection class that checks the user's permissions.

    This class checks the user based on the provided token payload.
    """

    async def __call__(
        self,
        session: Annotated[AsyncSession, Depends(db_session)],
        payload: Annotated[dict[str, Any], Depends(access)],
    ) -> dict[str, Any] | None:
        """
        Check the user and return the user object if authorized.

        :param session: The database session.
        :param payload: The token payload containing user information.
        :raises UnauthorizedError: If the user is not authorized.
        :return: The user object if authorized, None otherwise.
        """
        # Import here to avoid circular import
        from apps.user.models.user import UserModel

        if not payload:
            raise UnauthorizedError(message=constants.UNAUTHORIZED)

        user = await session.scalar(
            select(UserModel).where(UserModel.id == payload.get("sub"))
        )

        if not user:
            raise UnauthorizedError(message=constants.UNAUTHORIZED)

        return user
