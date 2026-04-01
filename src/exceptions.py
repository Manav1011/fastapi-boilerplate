from typing import Optional

from fastapi import status
from httpx import Response

import constants


class CustomException(Exception):
    """
    Base custom exception class for raising necessary exceptions in the app.

    Attributes:
        status_code (int): The HTTP status code associated with the exception.
        message (str): The message associated with the exception.
    """

    status_code = status.HTTP_400_BAD_REQUEST
    message = constants.SOMETHING_WENT_WRONG

    def __init__(self, message: Optional[str] = None):
        """
        Initialize the custom exception with an optional message.

        Args:
            message (Optional[str]): The message to be associated with the exception.
        """
        if message:
            self.message = message


class BadRequestError(CustomException):
    """
    Custom exception for representing a Bad Request (HTTP 400) error.
    """

    status_code = status.HTTP_400_BAD_REQUEST


class UnauthorizedError(CustomException):
    """
    Custom exception for representing an Unauthorized (HTTP 401) error.
    """

    status_code = status.HTTP_401_UNAUTHORIZED


class ForbiddenError(CustomException):
    """
    Custom exception for representing a Forbidden (HTTP 403) error.
    """

    status_code = status.HTTP_403_FORBIDDEN


class NotFoundError(CustomException):
    """
    Custom exception for representing a Not Found (HTTP 404) error.
    """

    status_code = status.HTTP_404_NOT_FOUND


class AlreadyExistsError(CustomException):
    """
    Custom exception for representing a Conflict (HTTP 409) error indicating that the resource already exists.
    """

    status_code = status.HTTP_409_CONFLICT


class UnprocessableEntityError(CustomException):
    """
    Custom exception for representing an Unprocessable Entity (HTTP 422) error.
    """

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class InvalidJWTTokenException(CustomException):
    """
    Custom exception for representing an Unauthorized (HTTP 401) error due to an invalid JWT token.
    """

    status_code = status.HTTP_401_UNAUTHORIZED


class InvalidRoleException(NotFoundError):
    """
    Custom exception to show a generic error message.
    """

    message = constants.INVALID_ROLE


class UnexpectedResponse(Exception):
    """
    Exception raised for an unexpected HTTP response.

    Attributes:
        response (Response): The unexpected HTTP response.
    """

    def __init__(self, response: Response):
        """
        Initialize the exception with the unexpected HTTP response.

        Args:
            response (Response): The unexpected HTTP response.
        """
        self.response = response
