from enum import Enum
import sys

# Python 3.10 compatibility for StrEnum
if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    class StrEnum(str, Enum):
        pass


class RoleType(StrEnum):
    """
    Enumeration of user role types.

    Defines different roles that users can have in the system, including:
    - ADMIN: Administrator role.
    - STAFF: Staff role.
    - USER: Regular user role.
    - ANY: Represents any role.
    - OPTIONAL: Represents an optional role.

    These roles are represented as strings for convenience.

    Attributes:
        ADMIN: Administrator role.
        STAFF: Staff role.
        USER: Regular user role.
        ANY: Represents any role.
        OPTIONAL: Represents an optional role.
    """

    ADMIN = "ADMIN"
    STAFF = "STAFF"
    USER = "USER"
    ANY = "ANY"
    OPTIONAL = "OPTIONAL"
