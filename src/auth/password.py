import bcrypt


async def hash_password(password: str) -> str:
    """
    Hash a password.

    Args:
        password (str): The password to be hashed.

    Returns:
        str: The hashed password.
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


async def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password.

    Args:
        plain_password (str): The plain text password.
        hashed_password (str): The hashed password to compare against.

    Returns:
        bool: True if the plain password matches the hashed password, False otherwise.
    """
    return bcrypt.hashpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
