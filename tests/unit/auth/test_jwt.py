import pytest
from uuid import uuid4
from src.auth.jwt import create_tokens, access


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
