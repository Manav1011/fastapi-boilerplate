import pytest
from uuid import uuid4
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi import Request

from src.auth.middleware import CurrentUser


@pytest.mark.asyncio
async def test_current_user_extracts_user_from_state():
    """Test that CurrentUser dependency returns user from request.state."""
    mock_request = MagicMock(spec=Request)
    mock_user = MagicMock()
    mock_user.id = uuid4()
    mock_request.state.user = mock_user

    current_user = CurrentUser()
    result = await current_user(mock_request)

    assert result == mock_user
