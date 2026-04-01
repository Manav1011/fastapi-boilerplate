from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only

import constants.messages as constants
from db.session import db_session
from auth.role_types import RoleType
from exceptions import UnauthorizedError

from auth.jwt import access, admin_access


class HasPermission:
    """
    A Dependency Injection class that checks the user's permissions.

    This class checks the user's permissions based on the provided token payload.

    """

    def __init__(self, type_: RoleType) -> None:
        """
        Initialize the HasPermission object with the specified permission type.

        Args:
            type_ (RoleType): The type of permission to check.
        """
        self.type = type_

    async def __call__(
        self,
        session: Annotated[AsyncSession, Depends(db_session)],
        payload: Annotated[dict[str, Any], Depends(access)],
    ) -> dict[str, Any] | None:
        """
        Check the user type and return the user object if authorized.

        :param session: The database session.
        :param payload: The token payload containing user information.
        :raises UnauthorizedError: If the user is not authorized.
        :return: The user object if authorized, None otherwise.
        """
        # Import here to avoid circular import
        from apps.user.models.user import UserModel

        if not payload:
            if self.type == RoleType.OPTIONAL:
                return None
            else:
                raise UnauthorizedError(message=constants.UNAUTHORIZED)

        user = await session.scalar(
            select(UserModel).where(UserModel.id == payload.get("id"))
        )

        if not user:
            raise UnauthorizedError(message=constants.UNAUTHORIZED)
        allowed_roles = {
            RoleType.USER: [RoleType.USER],
            RoleType.STAFF: [RoleType.STAFF],
            RoleType.ADMIN: [RoleType.ADMIN],
            RoleType.ANY: [RoleType.USER, RoleType.ADMIN],
            RoleType.OPTIONAL: [RoleType.USER],
        }

        if user.role not in allowed_roles[self.type]:
            raise UnauthorizedError(message=constants.UNAUTHORIZED)

        return user


class AdminHasPermission:
    """
    A Dependency Injection class that checks if the user has admin permissions.
    """

    def __init__(self) -> None:
        """
        Initialize the object to check admin permissions.
        """
        self.type = RoleType.ADMIN

    async def __call__(
        self,
        session: Annotated[AsyncSession, Depends(db_session)],
        payload: Annotated[dict[str, Any], Depends(admin_access)],
    ) -> dict[str, Any]:
        """
        Check if the user has admin permissions.

        :param session: The database session.
        :param payload: The token payload.
        :raises UnauthorizedError: If the user is not authorized.
        :return: The user object if authorized.
        """
        # Import here to avoid circular import
        from apps.user.models.user import UserModel

        if not payload:
            raise UnauthorizedError(message=constants.UNAUTHORIZED)

        user = await session.scalar(
            select(UserModel)
            .options(load_only(UserModel.id, UserModel.role))
            .where(UserModel.id == payload.get("id"))
        )

        if not user or user.role != RoleType.ADMIN:
            raise UnauthorizedError(message=constants.UNAUTHORIZED)
        return user
