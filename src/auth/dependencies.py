from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from auth.jwt import access
from db.session import db_session
from exceptions import UnauthorizedError, InvalidJWTTokenException
from apps.user.models import UserModel


security = HTTPBearer()


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(db_session),
) -> UserModel:
    """
    Dependency that validates Bearer token and returns the current user.
    Raises 401 if no valid token is provided. Also sets request.state.user.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        payload = access.decode(credentials.credentials)
        user_id = UUID(payload["sub"])
    except (UnauthorizedError, InvalidJWTTokenException, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user = await session.scalar(
        select(UserModel).where(UserModel.id == user_id)
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    request.state.user = user
    return user
