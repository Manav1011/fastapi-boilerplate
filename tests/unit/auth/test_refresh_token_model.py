import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from src.apps.user.models import RefreshTokenModel


@pytest.mark.asyncio
async def test_refresh_token_model_creation():
    token = RefreshTokenModel(
        token_hash="hashed_token_value",
        user_id=uuid4(),
        expires_at=datetime.utcnow() + timedelta(days=1),
        revoked=False,
    )
    assert token.revoked is False
    assert token.token_hash == "hashed_token_value"


@pytest.mark.asyncio
async def test_refresh_token_is_expired():
    token = RefreshTokenModel(
        token_hash="hashed_token_value",
        user_id=uuid4(),
        expires_at=datetime.utcnow() - timedelta(days=1),  # Expired
        revoked=False,
    )
    assert token.is_expired is True
    assert token.is_active is False


@pytest.mark.asyncio
async def test_refresh_token_is_active():
    token = RefreshTokenModel(
        token_hash="hashed_token_value",
        user_id=uuid4(),
        expires_at=datetime.utcnow() + timedelta(days=1),  # Not expired
        revoked=False,
    )
    assert token.is_expired is False
    assert token.is_active is True

