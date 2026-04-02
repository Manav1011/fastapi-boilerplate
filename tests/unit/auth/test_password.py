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
