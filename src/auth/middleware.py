from typing import TYPE_CHECKING, Optional
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security.http import HTTPBearer

from exceptions import UnauthorizedError, InvalidJWTTokenException
from auth.jwt import access
from db.session import db_session
from sqlalchemy import select

if TYPE_CHECKING:
    from apps.user.models import UserModel


# HTTPBearer for extracting Authorization header
bearer_scheme = HTTPBearer(auto_error=False)


class CurrentUser:
    """
    Dependency that returns the current authenticated user.
    MUST be used after AuthenticationMiddleware has run.
    """

    async def __call__(
        self,
        request: Request,
    ):
        from apps.user.models import UserModel

        user = getattr(request.state, "user", None)
        if not user:
            raise UnauthorizedError(message="Not authenticated")
        return user


class AuthenticationMiddleware:
    """
    Middleware that validates Bearer tokens and attaches user to request.state.
    Runs on every request - protected routes check request.state.user.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, request: Request, call_next):
        # Skip auth for public endpoints
        path = request.url.path
        if path in ["/api/user/sign-in", "/api/user", "/docs", "/openapi.json", "/redoc"]:
            return await call_next(request)

        auth_header: Optional[HTTPAuthorizationCredentials] = await bearer_scheme(request)

        if not auth_header:
            # No Authorization header - try to process anyway (protected routes will reject)
            return await call_next(request)

        try:
            payload = access.decode(auth_header.credentials)
            user_id = UUID(payload["sub"])
        except (UnauthorizedError, InvalidJWTTokenException, ValueError):
            # Invalid token - let protected routes handle rejection
            return await call_next(request)

        # Load user from DB and attach to request.state
        from apps.user.models import UserModel

        async with db_session() as session:
            user = await session.scalar(
                select(UserModel).where(UserModel.id == user_id)
            )
            if user:
                request.state.user = user

        return await call_next(request)
