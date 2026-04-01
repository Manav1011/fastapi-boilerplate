from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Query, status
from fastapi.responses import JSONResponse

import constants
from .models import UserModel
from .request import SignInRequest, SignUpRequest, GetUserByIdRequest, DeleteUserByIdRequest
from .response import BaseUserResponse
from .service import UserService
from .repository import UserRepository
from auth.permissions import HasPermission
from auth.role_types import RoleType
from db.session import db_session
from utils.schema import BaseResponse
from utils.cookies import set_auth_cookies

router = APIRouter(prefix="/api/user", tags=["User"])


def get_user_service(session: db_session) -> UserService:
    return UserService(UserRepository(session))


@router.post("/sign-in", status_code=status.HTTP_200_OK, operation_id="sign_in")
async def sign_in(
    body: Annotated[SignInRequest, Body()],
    service: Annotated[UserService, Depends(get_user_service)],
) -> JSONResponse:
    res = await service.login_user(**body.model_dump())
    data = {"status": constants.SUCCESS, "code": status.HTTP_200_OK, "data": res}
    response = JSONResponse(content=data)
    return set_auth_cookies(response, res, RoleType.USER)


@router.post("", status_code=status.HTTP_201_CREATED, operation_id="create_user")
async def create_user(
    body: Annotated[SignUpRequest, Body()],
    service: Annotated[UserService, Depends(get_user_service)],
) -> BaseResponse[BaseUserResponse]:
    return BaseResponse(data=await service.create_user(**body.model_dump()))


@router.get("/self", status_code=status.HTTP_200_OK, operation_id="get_self")
async def get_self(
    user: Annotated[UserModel, Depends(HasPermission(RoleType.USER))],
    service: Annotated[UserService, Depends(get_user_service)],
) -> BaseResponse[BaseUserResponse]:
    return BaseResponse(data=await service.get_self(user_id=user.id))


@router.get("/", status_code=status.HTTP_200_OK, dependencies=[Depends(HasPermission(RoleType.USER))], operation_id="get_user_by_id")
async def get_user_by_id(
    request: Annotated[GetUserByIdRequest, Query()],
    service: Annotated[UserService, Depends(get_user_service)],
) -> BaseResponse[BaseUserResponse]:
    return BaseResponse(data=await service.get_user_by_id(**request.model_dump()))


@router.delete("/", status_code=status.HTTP_200_OK, dependencies=[Depends(HasPermission(RoleType.USER))], operation_id="delete_user_by_id")
async def delete_user_by_id(
    request: Annotated[DeleteUserByIdRequest, Query()],
    service: Annotated[UserService, Depends(get_user_service)],
) -> BaseResponse[BaseUserResponse]:
    return BaseResponse(data=await service.delete_user_by_id(**request.model_dump()))
