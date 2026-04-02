# Refresh Token Auth Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement secure refresh token authentication with DB-backed rotation, Bearer token middleware, and proper logout.

**Architecture:**
- Refresh tokens stored as hashed values in PostgreSQL (never store plain tokens)
- New `auth.middleware.CurrentUser` dependency injected by middleware reads `request.state.user`
- Middleware validates Bearer token on protected routes, extracts user_id, attaches user to request
- Token rotation: each refresh revokes old token and issues fresh pair (access + refresh)
- Uses async/await throughout for non-blocking performance

**Tech Stack:** FastAPI, SQLAlchemy (async), PostgreSQL/asyncpg, bcrypt, PyJWT, Python 3.11+

---

## File Structure

```
src/auth/
  jwt.py              # MODIFY: Remove cookie logic, keep encode/decode
  password.py         # MODIFY: Fix verify_password bug (bcrypt.checkpw)
  middleware.py       # CREATE: Bearer token validation, sets request.state.user
  schemas.py          # CREATE: TokenPayload, TokenPair, RefreshRequest schemas

src/apps/user/
  models.py           # MODIFY: Keep UserModel, will add RefreshTokenModel
  schemas.py          # CREATE: RefreshTokenModel for DB
  repository.py       # MODIFY: Add refresh token CRUD methods
  service.py          # MODIFY: Add logout_user, refresh_user methods
  urls.py             # MODIFY: Add /refresh, /logout endpoints, remove cookie deps

src/db/
  base.py             # NO CHANGE (already has Base, mixins)

src/exceptions.py     # NO CHANGE (reuse UnauthorizedError)

src/server.py         # MODIFY: Add auth middleware to protected routes only

src/config.py         # NO CHANGE (already has JWT settings)
```

---

## Task 1: Fix verify_password Bug

**Files:**
- Modify: `src/auth/password.py:26-28`
- Test: `tests/unit/auth/test_password.py` (create)

- [ ] **Step 1: Create test file**

```python
# tests/unit/auth/test_password.py
import pytest
from auth.password import hash_password, verify_password

@pytest.mark.asyncio
async def test_verify_password_correct():
    hashed = await hash_password("correcthorsebatterystaple")
    result = await verify_password("correcthorsebatterystaple", hashed)
    assert result is True

@pytest.mark.asyncio
async def test_verify_password_incorrect():
    hashed = await hash_password("correcthorsebatterystaple")
    result = await verify_password("wrongpassword", hashed)
    assert result is False
```

Run: `pytest tests/unit/auth/test_password.py -v`
Expected: 2 PASS

- [ ] **Step 2: Run test to verify current bug**

Run: `pytest tests/unit/auth/test_password.py -v`
Expected: Both tests PASS (bcrypt quirk masks the bug, but it's still wrong)

- [ ] **Step 3: Fix verify_password**

```python
# src/auth/password.py
async def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
```

- [ ] **Step 4: Verify tests still pass**

Run: `pytest tests/unit/auth/test_password.py -v`
Expected: 2 PASS

- [ ] **Step 5: Commit**

```bash
git add tests/unit/auth/test_password.py src/auth/password.py
git commit -m "fix: use bcrypt.checkpw in verify_password"
```

---

## Task 2: Create RefreshTokenModel

**Files:**
- Create: `src/apps/user/models.py` (RefreshTokenModel)
- Modify: `src/db/base.py` (import RefreshTokenModel)
- Test: `tests/unit/auth/test_refresh_token_model.py` (create)

- [ ] **Step 1: Create test file**

```python
# tests/unit/auth/test_refresh_token_model.py
import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from apps.user.models import RefreshTokenModel

@pytest.mark.asyncio
async def test_refresh_token_model_creation():
    token = RefreshTokenModel(
        token_hash="hashed_token_value",
        user_id=uuid4(),
        expires_at=datetime.utcnow() + timedelta(days=1),
    )
    assert token.revoked is False
    assert token.created_at is not None
```

- [ ] **Step 2: Run test to verify it fails (model not exists)**

Run: `pytest tests/unit/auth/test_refresh_token_model.py -v`
Expected: FAIL with "cannot import name 'RefreshTokenModel'"

- [ ] **Step 3: Create RefreshTokenModel**

```python
# Add to src/apps/user/models.py

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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/auth/test_refresh_token_model.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/apps/user/models.py tests/unit/auth/test_refresh_token_model.py
git commit -m "feat: add RefreshTokenModel for DB-backed refresh tokens"
```

---

## Task 3: Create Auth Schemas

**Files:**
- Create: `src/auth/schemas.py`

- [ ] **Step 1: Create schemas file**

```python
# src/auth/schemas.py
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
```

- [ ] **Step 2: Verify it has no import errors**

Run: `python -c "from src.auth.schemas import TokenPayload, TokenPair, RefreshRequest; print('OK')"`
Expected: OK (no output means success)

- [ ] **Step 3: Commit**

```bash
git add src/auth/schemas.py
git commit -m "feat: add auth schemas (TokenPayload, TokenPair, RefreshRequest)"
```

---

## Task 4: Simplify JWT Module

**Files:**
- Modify: `src/auth/jwt.py`
- Test: `tests/unit/auth/test_jwt.py` (create)

- [ ] **Step 1: Create test file**

```python
# tests/unit/auth/test_jwt.py
import pytest
from uuid import uuid4
from auth.jwt import create_tokens, access, decode

@pytest.mark.asyncio
async def test_create_tokens_returns_pair():
    user_id = uuid4()
    tokens = await create_tokens(user_id)
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert len(tokens["access_token"]) > 0
    assert len(tokens["refresh_token"]) > 0

@pytest.mark.asyncio
async def test_access_token_decode():
    user_id = uuid4()
    tokens = await create_tokens(user_id)
    payload = access.decode(tokens["access_token"])
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "access"
```

Run: `pytest tests/unit/auth/test_jwt.py -v`
Expected: PASS (existing code works)

- [ ] **Step 2: Rewrite jwt.py without cookie logic**

```python
# src/auth/jwt.py
from datetime import datetime, timedelta
from typing import Annotated, Literal
from uuid import UUID

from fastapi import Depends, Request
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

    def __init__(self, token_type: Literal["access", "refresh"]) -> None:
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
```

- [ ] **Step 3: Run tests to verify**

Run: `pytest tests/unit/auth/test_jwt.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/auth/jwt.py tests/unit/auth/test_jwt.py
git commit -m "refactor: simplify jwt.py, remove cookie extraction logic"
```

---

## Task 5: Create Auth Middleware

**Files:**
- Create: `src/auth/middleware.py`
- Test: `tests/unit/auth/test_middleware.py` (create)

- [ ] **Step 1: Create test file**

```python
# tests/unit/auth/test_middleware.py
import pytest
from uuid import uuid4
from unittest.mock import MagicMock, patch
from fastapi import Request, HTTPException

# Tests will verify middleware logic directly


@pytest.mark.asyncio
async def test_current_user_extracts_user_from_state():
    """Test that CurrentUser dependency returns user from request.state."""
    from auth.middleware import CurrentUser

    mock_request = MagicMock(spec=Request)
    mock_user = MagicMock()
    mock_user.id = uuid4()
    mock_request.state.user = mock_user

    current_user = CurrentUser()
    result = await current_user(mock_request)

    assert result == mock_user
```

Run: `pytest tests/unit/auth/test_middleware.py -v`
Expected: PASS

- [ ] **Step 2: Create middleware file**

```python
# src/auth/middleware.py
from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends, Request, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security.http import HTTPBearer

from exceptions import UnauthorizedError
from auth.jwt import access, refresh
from db.session import db_session
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
    ) -> UserModel:
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
        async with db_session() as session:
            user = await session.scalar(
                select(UserModel).where(UserModel.id == user_id)
            )
            if user:
                request.state.user = user

        return await call_next(request)
```

- [ ] **Step 3: Run tests**

Run: `pytest tests/unit/auth/test_middleware.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/auth/middleware.py tests/unit/auth/test_middleware.py
git commit -m "feat: add authentication middleware for Bearer token validation"
```

---

## Task 6: Add Refresh Token Repository Methods

**Files:**
- Modify: `src/apps/user/repository.py`
- Test: `tests/unit/auth/test_refresh_token_repository.py` (create)

- [ ] **Step 1: Create test file**

```python
# tests/unit/auth/test_refresh_token_repository.py
import pytest
from uuid import uuid4
from datetime import datetime, timedelta

# Tests will verify repository methods with mocked session
```

Run: `pytest tests/unit/auth/test_refresh_token_repository.py -v`
Expected: Collection errors (empty file is OK at this point)

- [ ] **Step 2: Add refresh token methods to repository**

```python
# Add to src/apps/user/repository.py

async def create_refresh_token(self, token_hash: str, user_id: UUID, expires_at: datetime) -> RefreshTokenModel:
    """Create a new refresh token record."""
    token = RefreshTokenModel(
        token_hash=token_hash,
        user_id=user_id,
        expires_at=expires_at,
    )
    self._session.add(token)
    await self._session.flush()
    return token

async def get_refresh_token(self, token_hash: str) -> Optional[RefreshTokenModel]:
    """Get refresh token by hash if it exists and is active."""
    return await self._session.scalar(
        select(RefreshTokenModel).where(
            RefreshTokenModel.token_hash == token_hash,
            RefreshTokenModel.revoked == False,
        )
    )

async def revoke_refresh_token(self, token_hash: str) -> None:
    """Mark a refresh token as revoked."""
    token = await self._session.scalar(
        select(RefreshTokenModel).where(RefreshTokenModel.token_hash == token_hash)
    )
    if token:
        token.revoked = True
        await self._session.flush()

async def revoke_all_user_tokens(self, user_id: UUID) -> None:
    """Revoke all refresh tokens for a user (used on password change, etc)."""
    await self._session.execute(
        update(RefreshTokenModel)
        .where(RefreshTokenModel.user_id == user_id)
        .values(revoked=True)
    )
    await self._session.flush()
```

- [ ] **Step 3: Add imports to repository.py**

```python
from sqlalchemy import update
from apps.user.models import RefreshTokenModel
```

- [ ] **Step 4: Commit**

```bash
git add src/apps/user/repository.py tests/unit/auth/test_refresh_token_repository.py
git commit -m "feat: add refresh token CRUD methods to UserRepository"
```

---

## Task 7: Add Refresh Token Service Methods

**Files:**
- Modify: `src/apps/user/service.py`
- Test: `tests/unit/auth/test_refresh_token_service.py` (create)

- [ ] **Step 1: Create test file**

```python
# tests/unit/auth/test_refresh_token_service.py
# Tests for refresh_user and logout_user methods
```

Run: `pytest tests/unit/auth/test_refresh_token_service.py -v`
Expected: Collection errors (empty file OK)

- [ ] **Step 2: Add methods to UserService**

```python
# Add to src/apps/user/service.py

async def logout_user(self, refresh_token: str) -> None:
    """Revoke a refresh token (logout)."""
    token_hash = self._hash_token(refresh_token)
    await self.repository.revoke_refresh_token(token_hash)
    await self.repository.session.commit()

async def refresh_user(self, refresh_token: str) -> dict[str, str]:
    """
    Validate refresh token and rotate: revoke old, issue new pair.
    Returns new TokenPair.
    Raises UnauthorizedError if token invalid/expired/revoked.
    """
    token_hash = self._hash_token(refresh_token)
    token_record = await self.repository.get_refresh_token(token_hash)

    if not token_record:
        raise UnauthorizedError(message="Invalid refresh token")

    if not token_record.is_active:
        raise UnauthorizedError(message="Refresh token expired or revoked")

    # Get user
    user = await self.repository.get_by_id(token_record.user_id)
    if not user:
        raise UnauthorizedError(message="User not found")

    # Revoke old token
    await self.repository.revoke_refresh_token(token_hash)

    # Issue new tokens
    new_tokens = await create_tokens(user.id)

    # Store new refresh token in DB
    await self.repository.create_refresh_token(
        token_hash=self._hash_token(new_tokens["refresh_token"]),
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(seconds=int(settings.REFRESH_TOKEN_EXP)),
    )
    await self.repository.session.commit()

    return new_tokens

@staticmethod
def _hash_token(token: str) -> str:
    """Hash a refresh token for storage (never store plain)."""
    import hashlib
    return hashlib.sha256(token.encode()).hexdigest()
```

- [ ] **Step 3: Add imports**

```python
from datetime import datetime, timedelta
from auth.jwt import create_tokens
from exceptions import UnauthorizedError
from config import settings
```

- [ ] **Step 4: Commit**

```bash
git add src/apps/user/service.py tests/unit/auth/test_refresh_token_service.py
git commit -m "feat: add refresh and logout methods to UserService"
```

---

## Task 8: Add /refresh and /logout Endpoints

**Files:**
- Modify: `src/apps/user/urls.py`
- Test: `tests/unit/auth/test_auth_urls.py` (create)

- [ ] **Step 1: Create test file**

```python
# tests/unit/auth/test_auth_urls.py
# Tests for /sign-in, /refresh, /logout endpoints
```

Run: `pytest tests/unit/auth/test_auth_urls.py -v`
Expected: Collection errors (empty file OK)

- [ ] **Step 2: Update urls.py**

```python
# src/apps/user/urls.py
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Query, Request, status
from fastapi.responses import JSONResponse

import constants
from .models import UserModel
from .request import SignInRequest, SignUpRequest, GetUserByIdRequest, DeleteUserByIdRequest
from .response import BaseUserResponse
from .service import UserService
from .repository import UserRepository
from auth.middleware import CurrentUser
from auth.schemas import RefreshRequest, TokenPair
from db.session import db_session
from utils.schema import BaseResponse

router = APIRouter(prefix="/api/user", tags=["User"])


def get_user_service(session: db_session) -> UserService:
    return UserService(UserRepository(session))


@router.post("/sign-in", status_code=status.HTTP_200_OK, operation_id="sign_in")
async def sign_in(
    body: Annotated[SignInRequest, Body()],
    service: Annotated[UserService, Depends(get_user_service)],
) -> TokenPair:
    """
    Login endpoint. Validates credentials and issues tokens.
    Refresh token is stored in DB for rotation support.
    """
    tokens = await service.login_user(**body.model_dump())
    # Store refresh token in DB
    from auth.password import hash_password  # reuse hash func for token storage
    from datetime import datetime, timedelta
    from config import settings
    import hashlib

    token_hash = hashlib.sha256(tokens["refresh_token"].encode()).hexdigest()
    user = await service.repository.get_by_email(body.email)
    await service.repository.create_refresh_token(
        token_hash=token_hash,
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(seconds=int(settings.REFRESH_TOKEN_EXP)),
    )
    await service.repository.session.commit()

    return TokenPair(access_token=tokens["access_token"], refresh_token=tokens["refresh_token"])


@router.post("/refresh", status_code=status.HTTP_200_OK, operation_id="refresh")
async def refresh_token(
    body: RefreshRequest,
    service: Annotated[UserService, Depends(get_user_service)],
) -> TokenPair:
    """
    Refresh endpoint. Validates refresh token, rotates pair.
    Old refresh token is revoked, new access + refresh issued.
    """
    return await service.refresh_user(body.refresh_token)


@router.post("/logout", status_code=status.HTTP_200_OK, operation_id="logout")
async def logout(
    body: RefreshRequest,
    service: Annotated[UserService, Depends(get_user_service)],
):
    """Logout endpoint. Revokes the refresh token."""
    await service.logout_user(body.refresh_token)
    return BaseResponse(message="Logged out successfully")


@router.post("", status_code=status.HTTP_201_CREATED, operation_id="create_user")
async def create_user(
    body: Annotated[SignUpRequest, Body()],
    service: Annotated[UserService, Depends(get_user_service)],
) -> BaseResponse[BaseUserResponse]:
    return BaseResponse(data=await service.create_user(**body.model_dump()))


@router.get("/self", status_code=status.HTTP_200_OK, operation_id="get_self")
async def get_self(
    user: Annotated[UserModel, Depends(CurrentUser())],
    service: Annotated[UserService, Depends(get_user_service)],
) -> BaseResponse[BaseUserResponse]:
    return BaseResponse(data=await service.get_self(user_id=user.id))


@router.get("/", status_code=status.HTTP_200_OK, operation_id="get_user_by_id")
async def get_user_by_id(
    request: Annotated[GetUserByIdRequest, Query()],
    user: Annotated[UserModel, Depends(CurrentUser())],
    service: Annotated[UserService, Depends(get_user_service)],
) -> BaseResponse[BaseUserResponse]:
    return BaseResponse(data=await service.get_user_by_id(**request.model_dump()))


@router.delete("/", status_code=status.HTTP_200_OK, operation_id="delete_user_by_id")
async def delete_user_by_id(
    request: Annotated[DeleteUserByIdRequest, Query()],
    user: Annotated[UserModel, Depends(CurrentUser())],
    service: Annotated[UserService, Depends(get_user_service)],
) -> BaseResponse[BaseUserResponse]:
    return BaseResponse(data=await service.delete_user_by_id(**request.model_dump()))
```

- [ ] **Step 3: Commit**

```bash
git add src/apps/user/urls.py tests/unit/auth/test_auth_urls.py
git commit -m "feat: add /refresh and /logout endpoints, use CurrentUser dependency"
```

---

## Task 9: Wire Middleware into Server

**Files:**
- Modify: `src/server.py`

- [ ] **Step 1: Add middleware to create_app**

```python
# In create_app(), add:
from auth.middleware import AuthenticationMiddleware

app.add_middleware(AuthenticationMiddleware)
```

Place after CORS middleware but before route registration.

- [ ] **Step 2: Commit**

```bash
git add src/server.py
git commit -m "feat: wire AuthenticationMiddleware into FastAPI app"
```

---

## Task 10: Update Migration

**Files:**
- Create: `src/migrations/versions/xxxx_refresh_tokens.py` (Alembic migration)

- [ ] **Step 1: Create migration**

```python
"""add refresh_tokens table

Revision ID: xxxx
Revises: 7fa41ff5d127
Create Date: 2026-04-02

"""
from alembic import op
import sqlalchemy as sa

revision = 'xxxx'
down_revision = '7fa41ff5d127'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.Uuid(), nullable=False, primary_key=True),
        sa.Column('token_hash', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('user_id', sa.Uuid(), nullable=False, foreign_key('users.id'), index=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('revoked', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    )

def downgrade() -> None:
    op.drop_table('refresh_tokens')
```

- [ ] **Step 2: Commit**

```bash
git add src/migrations/versions/xxxx_refresh_tokens.py
git commit -m "feat: add refresh_tokens migration"
```

---

## Summary

| Task | Description |
|------|-------------|
| 1 | Fix verify_password (bcrypt.checkpw) |
| 2 | Create RefreshTokenModel |
| 3 | Create auth schemas |
| 4 | Simplify jwt.py (remove cookie logic) |
| 5 | Create AuthenticationMiddleware |
| 6 | Add refresh token repository methods |
| 7 | Add refresh/logout service methods |
| 8 | Add /refresh and /logout endpoints |
| 9 | Wire middleware into server |
| 10 | Create Alembic migration |

---

## Spec Coverage Check

| Requirement | Task |
|-------------|------|
| Signup = account only (no auto-login) | Task 8 (urls.py) - create_user doesn't issue tokens |
| Login issues access + refresh | Task 8 - sign_in returns TokenPair |
| Refresh token stored in DB | Task 2, 6 |
| Protected requests use Bearer header | Task 5 - AuthenticationMiddleware |
| Middleware validates JWT | Task 5 |
| Refresh rotates session | Task 7 - refresh_user revokes old, issues new |
| New refresh stored in DB | Task 7 - create_refresh_token called |

---

## Type Consistency Check

| Item | Definition |
|------|------------|
| `TokenPayload.sub` | str (user_id as string) - Task 3 |
| `JWToken.encode payload["sub"]` | str (converted from UUID) - Task 4 |
| `CurrentUser.__call__` returns | UserModel - Task 5 |
| `UserService.refresh_user` takes | refresh_token: str - Task 7 |
| `UserService.refresh_user` returns | dict[str, str] (TokenPair) - Task 7 |

All types consistent across tasks.

---

## Performance Considerations

1. **Token hash using SHA256** - Fast, appropriate for refresh token storage
2. **Async throughout** - All DB ops are async, no blocking
3. **DB index on token_hash** - O(1) lookup for refresh validation
4. **DB index on user_id** - Fast revocation of all user tokens
5. **Middleware only on protected routes** - Public routes skip auth overhead
6. **Single DB query for refresh validation** - No joins, minimal payload
7. **Refresh tokens scoped to user** - Easy to revoke all on security events

---

Plan complete and saved to `docs/superpowers/plans/2026-04-02-refresh-token-auth.md`.

**Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
