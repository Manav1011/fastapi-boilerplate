from uuid import UUID

from .exceptions import (
    DuplicateEmailException,
    InvalidCredentialsException,
    UserNotFoundException,
)
from .models import UserModel
from .repository import UserRepository
from auth.password import hash_password, verify_password
from auth.jwt import create_tokens
from auth.role_types import RoleType


class UserService:
    """Business logic for user operations."""

    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    async def get_self(self, user_id: UUID) -> UserModel:
        return await self.repository.get_by_id(user_id)

    async def login_user(self, email: str, password: str) -> dict[str, str]:
        user = await self.repository.get_by_email_role(email, RoleType.USER)
        if not user:
            raise InvalidCredentialsException

        if not await verify_password(hashed_password=user.password, plain_password=password):
            raise InvalidCredentialsException

        return await create_tokens(user_id=user.id, role=user.role)

    async def create_user(
        self,
        first_name: str,
        last_name: str,
        email: str,
        phone: str,
        password: str,
    ) -> UserModel:
        existing = await self.repository.get_by_email_or_phone(email, phone)
        if existing:
            raise DuplicateEmailException

        user = UserModel.create(
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            password=await hash_password(password),
            email=email,
        )
        self.repository.add(user)
        await self.repository.session.commit()
        await self.repository.session.refresh(user)
        return user

    async def get_user_by_id(self, user_id: UUID) -> UserModel:
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundException
        return user

    async def delete_user_by_id(self, user_id: UUID) -> UserModel:
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundException
        await self.repository.delete(user_id)
        await self.repository.session.commit()
        return user
