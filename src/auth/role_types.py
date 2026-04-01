from enum import StrEnum


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
