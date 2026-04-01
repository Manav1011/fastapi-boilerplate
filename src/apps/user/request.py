from uuid import UUID

from utils.schema import CamelCaseModel


class SignInRequest(CamelCaseModel):
    email: str
    password: str


class SignUpRequest(CamelCaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str
    password: str


class GetUserByIdRequest(CamelCaseModel):
    user_id: UUID


class DeleteUserByIdRequest(CamelCaseModel):
    user_id: UUID
