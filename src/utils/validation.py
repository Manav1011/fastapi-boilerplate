import re
from typing import Match

from pydantic import EmailStr

import constants
from constants.regex import EMAIL_REGEX, FIRST_NAME_REGEX, PHONE_REGEX


def strong_password(password) -> Match[str] | None:
    return re.search(
        r"^(?=[^A-Z]*[A-Z])(?=[^a-z]*[a-z])(?=\D*\d)(?=[^#?!@$%^&*-]*[#?!@$%^&*-]).{8,}$",
        password,
        re.I,
    )


def validate_string_fields(values) -> dict:
    from apps.user.exceptions import EmptyDescriptionException
    for field_name, value in values.items():
        if isinstance(value, str) and not value.strip():
            raise EmptyDescriptionException(
                message=f"{field_name} must not be an empty string"
            )
    return values


def validate_input_fields(
    first_name: str, email: EmailStr, phone: str, password: str
) -> None:
    from apps.user.exceptions import (
        InvalidEmailException,
        InvalidPhoneFormatException,
        WeakPasswordException,
    )
    if not re.match(EMAIL_REGEX, email):
        raise InvalidEmailException

    if not re.search(FIRST_NAME_REGEX, first_name, re.I):
        raise ValueError(constants.INVALID + f"{first_name.replace('_', ' ')}")

    if not re.match(PHONE_REGEX, phone, re.I):
        raise InvalidPhoneFormatException

    if not strong_password(password):
        raise WeakPasswordException


def validate_email(email: str) -> str | None:
    from apps.user.exceptions import InvalidEmailException
    if not re.match(constants.EMAIL_REGEX, email):
        raise InvalidEmailException
    if not isinstance(email, str) and email is not None:
        raise InvalidEmailException
    return email
