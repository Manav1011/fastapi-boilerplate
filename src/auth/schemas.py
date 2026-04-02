from uuid import UUID
from pydantic import BaseModel


class TokenPayload(BaseModel):
    """JWT token payload structure."""
    sub: str  # user_id as string
    type: str  # "access" or "refresh"
    exp: int   # expiration timestamp


class TokenPair(BaseModel):
    """Pair of access and refresh tokens returned to client."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Request body for token refresh."""
    refresh_token: str
