from datetime import datetime, timedelta
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import Cookie, Depends, Request
from fastapi.openapi.models import HTTPBearer
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer as HTTPBearerSecurity
from fastapi.security.base import SecurityBase
from jwt import DecodeError, ExpiredSignatureError, decode, encode

import constants.messages as constants
from config import settings
from auth.role_types import RoleType
from exceptions import UnauthorizedError, InvalidJWTTokenException, InvalidRoleException


class JWToken(SecurityBase):
    """
    A class for handling JWT tokens.

    This class inherits from :class:`SecurityBase` and provides methods for encoding and decoding JWT tokens.

    Args:
        token_type (Literal["access", "refresh", "admin_access", "admin_refresh"]): The type of token.

    Attributes:
        model: The HTTPBearer model for token extraction.
        scheme_name: The name of the token scheme.
        token_type (Literal["access", "refresh", "admin_access", "admin_refresh"]): The type of token.
    """

    def __init__(
        self, token_type: Literal["access", "refresh", "admin_access", "admin_refresh"]
    ) -> None:
        """
        Initialize the JWToken with the specified token type.

        Args:
            token_type (Literal["access", "refresh", "admin_access", "admin_refresh"]): The type of token.
        """
        self.model = HTTPBearer(name=f"{token_type}Token")
        self.scheme_name = self.__class__.__name__
        self.token_type = token_type

    def encode(self, payload: dict, expire_period: int = 3600) -> str:
        """
        Encode a payload into a JWT token.

        Args:
            payload (dict): The payload to be included in the token.
            expire_period (int, optional): The expiry period of the token in seconds. Defaults to 3600.

        Returns:
            str: The encoded JWT token.
        """
        return encode(
            {
                **payload,
                "type": self.token_type,
                "exp": datetime.utcnow() + timedelta(seconds=expire_period),
            },
            key=settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

    def decode(self, token: str) -> dict[str, Any] | None:
        """
        Decode a JWT token.

        Args:
            token (str): The JWT token to decode.

        Returns:
            Union[dict[str, Any], None]: The decoded token payload.
        """
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

    async def __call__(
        self,
        request: Request,
        access_token: Annotated[
            str | None, Cookie(alias="accessToken", include_in_schema=False)
        ] = None,  # type: ignore
        refresh_token: Annotated[
            str | None, Cookie(alias="refreshToken", include_in_schema=False)
        ] = None,  # type: ignore
        admin_access_token: Annotated[
            str | None, Cookie(alias="adminAccessToken", include_in_schema=False)
        ] = None,  # type: ignore
        admin_refresh_token: Annotated[
            str | None, Cookie(alias="adminRefreshToken", include_in_schema=False)
        ] = None,  # type: ignore
        authorization: Annotated[
            HTTPAuthorizationCredentials, Depends(HTTPBearerSecurity(auto_error=False))
        ] = None,
    ) -> dict[str, Any] | None:
        """
        Extract the token from the request and decode it.

        Args:
            request (Request): The incoming request.
            access_token (str | None, optional): The access token cookie. Defaults to None.
            refresh_token (str | None, optional): The refresh token cookie. Defaults to None.
            admin_access_token (str | None, optional): The admin access token cookie. Defaults to None.
            admin_refresh_token (str | None, optional): The admin refresh token cookie. Defaults to None.

        Returns:
            Union[dict[str, Any], None]: The decoded token payload or None if no token found.
        """
        if authorization:
            try:
                token = authorization.credentials
                return self.decode(token)
            except InvalidJWTTokenException:
                raise UnauthorizedError(message=constants.UNAUTHORIZED)

        token_mapping = {
            constants.ACCESS: access_token,
            constants.REFRESH: refresh_token,
            constants.ADMIN_ACCESS: admin_access_token,
            constants.ADMIN_REFRESH: admin_refresh_token,
        }

        token = token_mapping.get(self.token_type)

        if token:
            return self.decode(token)

        if self.token_type in [
            constants.ACCESS,
            constants.REFRESH,
            constants.ADMIN_ACCESS,
            constants.ADMIN_REFRESH,
        ]:
            raise UnauthorizedError(message=constants.UNAUTHORIZED)
        return None


async def create_tokens(user_id: UUID, role: RoleType) -> dict[str, str]:
    """
    Create access-token and refresh-token for a user.

    Args:
        user_id: The user's UUID.
        role: The user's role type.

    Returns:
        dict[str, str]: A dictionary containing access-token and refresh-token.

    Raises:
        InvalidRoleException: If the role is not USER, ADMIN, or STAFF.
    """
    if role == RoleType.USER:
        access_token = access.encode(
            payload={"id": str(user_id)}, expire_period=int(settings.ACCESS_TOKEN_EXP)
        )
        refresh_token = refresh.encode(
            payload={"id": str(user_id)}, expire_period=int(settings.REFRESH_TOKEN_EXP)
        )
    elif role == RoleType.ADMIN:
        access_token = admin_access.encode(
            payload={"id": str(user_id)}, expire_period=int(settings.ACCESS_TOKEN_EXP)
        )
        refresh_token = admin_refresh.encode(
            payload={"id": str(user_id)}, expire_period=int(settings.REFRESH_TOKEN_EXP)
        )
    elif role == RoleType.STAFF:
        access_token = access.encode(
            payload={"id": str(user_id)}, expire_period=int(settings.ACCESS_TOKEN_EXP)
        )
        refresh_token = refresh.encode(
            payload={"id": str(user_id)}, expire_period=int(settings.REFRESH_TOKEN_EXP)
        )
    else:
        raise InvalidRoleException

    return {"access_token": access_token, "refresh_token": refresh_token}


access = JWToken("access")
refresh = JWToken("refresh")
admin_access = JWToken("admin_access")
admin_refresh = JWToken("admin_refresh")
