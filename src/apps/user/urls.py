from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Query, Request, Security, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

import constants
from .models import UserModel
from .request import SignInRequest, SignUpRequest, GetUserByIdRequest, DeleteUserByIdRequest
from .response import BaseUserResponse
from .service import UserService
from .repository import UserRepository
from auth.dependencies import get_current_user
from auth.schemas import RefreshRequest, TokenPair
from db.session import db_session
from utils.schema import BaseResponse
from utils.cookies import set_auth_cookies
from config import settings

router = APIRouter(prefix="/api/user", tags=["User"])
protected_router = APIRouter(prefix="/api/user", tags=["User"], dependencies=[Depends(get_current_user)])


def get_user_service(session: Annotated[AsyncSession, Depends(db_session)]) -> UserService:
    return UserService(UserRepository(session))


# ==================== PUBLIC ROUTES ====================

@router.post("/sign-in", status_code=status.HTTP_200_OK, operation_id="sign_in")
async def sign_in(
    body: Annotated[SignInRequest, Body()],
    service: Annotated[UserService, Depends(get_user_service)],
) -> JSONResponse:
    """
    Login endpoint. Validates credentials and issues tokens.
    Refresh token is stored in DB for rotation support.
    """
    tokens = await service.login_user(**body.model_dump())

    # Store refresh token in DB
    user = await service.repository.get_by_email(body.email)
    token_hash = service._hash_token(tokens["refresh_token"])
    await service.repository.create_refresh_token(
        token_hash=token_hash,
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(seconds=int(settings.REFRESH_TOKEN_EXP)),
    )
    await service.repository.session.flush()

    data = {"status": constants.SUCCESS, "code": status.HTTP_200_OK, "data": tokens}
    response = JSONResponse(content=data)
    return set_auth_cookies(response, tokens)


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


# ==================== PROTECTED ROUTES ====================

@protected_router.get("/self", status_code=status.HTTP_200_OK, operation_id="get_self")
async def get_self(
    request: Request,
    service: Annotated[UserService, Depends(get_user_service)],
) -> BaseResponse[BaseUserResponse]:
    user: UserModel = request.state.user
    return BaseResponse(data=await service.get_self(user_id=user.id))


@protected_router.get("/", status_code=status.HTTP_200_OK, operation_id="get_user_by_id")
async def get_user_by_id(
    query: Annotated[GetUserByIdRequest, Query()],
    request: Request,
    service: Annotated[UserService, Depends(get_user_service)],
) -> BaseResponse[BaseUserResponse]:
    user: UserModel = request.state.user
    return BaseResponse(data=await service.get_user_by_id(**query.model_dump()))


@protected_router.delete("/", status_code=status.HTTP_200_OK, operation_id="delete_user_by_id")
async def delete_user_by_id(
    query: Annotated[DeleteUserByIdRequest, Query()],
    request: Request,
    service: Annotated[UserService, Depends(get_user_service)],
) -> BaseResponse[BaseUserResponse]:
    user: UserModel = request.state.user
    return BaseResponse(data=await service.delete_user_by_id(**query.model_dump()))
