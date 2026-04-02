from datetime import datetime, timedelta
from typing import Literal
from uuid import UUID

from fastapi.security.base import SecurityBase
from jwt import DecodeError, ExpiredSignatureError, decode, encode

import constants.messages as constants
from config import settings
from exceptions import UnauthorizedError, InvalidJWTTokenException


class JWToken(SecurityBase):
    """
    JWT encoder/decoder. Handles access and refresh token types.
    Does NOT handle cookie extraction - that moves to middleware.
    """

    def __init__(self, token_type: str) -> None:
        self.model = None  # No security scheme needed for direct use
        self.scheme_name = self.__class__.__name__
        self.token_type = token_type

    def encode(self, payload: dict, expire_period: int = 3600) -> str:
        """Encode payload into JWT token."""
        return encode(
            {
                **payload,
                "type": self.token_type,
                "exp": datetime.utcnow() + timedelta(seconds=expire_period),
            },
            key=settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

    def decode(self, token: str) -> dict:
        """Decode and validate JWT token."""
        try:
            payload = decode(
                token,
                key=settings.JWT_SECRET_KEY,
                algorithms=settings.JWT_ALGORITHM,
                options={"verify_signature": True, "verify_exp": True},
            )
            if payload.get("type") != self.token_type:
                raise UnauthorizedError(constants.UNAUTHORIZED)
            return payload
        except DecodeError:
            raise InvalidJWTTokenException(constants.INVALID_TOKEN)
        except ExpiredSignatureError:
            raise InvalidJWTTokenException(constants.EXPIRED_TOKEN)

    async def __call__(self, *args, **kwargs):
        """
        Deprecated: JWToken is no longer callable as dependency.
        Use CurrentUser dependency instead for protected routes.
        """
        raise NotImplementedError(
            "JWToken dependency injection is deprecated. "
            "Use CurrentUser dependency from auth.middleware instead."
        )


async def create_tokens(user_id: UUID) -> dict[str, str]:
    """
    Create access-token and refresh-token for a user.
    """
    access_token = access.encode(
        payload={"sub": str(user_id)}, expire_period=int(settings.ACCESS_TOKEN_EXP)
    )
    refresh_token = refresh.encode(
        payload={"sub": str(user_id)}, expire_period=int(settings.REFRESH_TOKEN_EXP)
    )
    return {"access_token": access_token, "refresh_token": refresh_token}


access = JWToken("access")
refresh = JWToken("refresh")
# Temporary aliases for backward compatibility - admin tokens will be refactored separately
admin_access = access
admin_refresh = refresh
