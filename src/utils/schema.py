from typing import Any, Generic, TypeVar

from fastapi import status as st
from pydantic import BaseModel
from pydantic.alias_generators import to_camel


class CamelCaseModel(BaseModel):
    """
    A schemas for Camelcase.
    """

    class Config:
        """
        Configuration class for Pydantic models.
        This class defines configuration options for Pydantic models within the codebase.
        """

        alias_generator = to_camel
        populate_by_name = True
        arbitrary_types_allowed = True
        from_attributes = True


BaseDataField = TypeVar("BaseDataField", bound=CamelCaseModel)


class BaseResponse(CamelCaseModel, Generic[BaseDataField]):
    """
    Base response class for API responses.
    This class represents a base response structure for API responses. It includes fields
    for status, code, and data, which can be customized for specific responses.
    """

    status: str = "SUCCESS"
    code: int = st.HTTP_200_OK
    data: BaseDataField | None = None

    def __init__(
        self, data: Any, status: str = "SUCCESS", code: int = st.HTTP_200_OK
    ) -> None:
        super().__init__()
        self.data = data
        self.status = status
        self.code = code


class BaseValidationResponse(CamelCaseModel, Generic[BaseDataField]):
    """
    Base validation response class for API responses.
    This class represents a base response structure for validation error responses in API responses.
    It includes fields for status, code, and a message, which typically contains details about validation errors.
    """

    status: str = "Error"
    code: int = st.HTTP_422_UNPROCESSABLE_ENTITY
    message: dict


class SuccessResponse(CamelCaseModel):
    """
    A schemas model success response.
    """

    message: str = "SUCCESS"
