from uuid import UUID

from utils.schema import CamelCaseModel


class BaseUserResponse(CamelCaseModel):
    id: UUID
    first_name: str
    last_name: str
