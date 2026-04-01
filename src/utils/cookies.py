from fastapi.responses import JSONResponse

from config import settings
from auth.role_types import RoleType


def set_auth_cookies(
    response: JSONResponse, tokens: dict[str, str], role: RoleType
) -> JSONResponse:
    """
    Set authentication cookies in an HTTP response.
    This function takes an HTTP response object and a dictionary of tokens, and sets two cookies,
    "accessToken" and "refreshToken," in the response. These cookies are used for user authentication.
    Args:
        response (Response): The HTTP response object to set cookies in.
        tokens (dict[str, str]): A dictionary containing access and refresh tokens.
        role (role-type): A role type of user
    Returns:
        Response: The updated HTTP response with the authentication cookies set.
    """
    cookies_params = {
        "domain": settings.COOKIES_DOMAIN,
        "secure": True,
        "samesite": "lax" if settings.is_production else "none",
        "httponly": True,
    }

    if role == RoleType.USER:
        response.set_cookie(
            "accessToken",
            tokens["access_token"],
            expires=int(settings.ACCESS_TOKEN_EXP),
            **cookies_params,
        )
        response.set_cookie(
            "refreshToken",
            tokens["refresh_token"],
            expires=int(settings.REFRESH_TOKEN_EXP),
            **cookies_params,
        )
    if role == RoleType.ADMIN:
        response.set_cookie(
            "adminAccessToken",
            tokens["access_token"],
            expires=int(settings.ACCESS_TOKEN_EXP),
            **cookies_params,
        )
        response.set_cookie(
            "adminRefreshToken",
            tokens["refresh_token"],
            expires=int(settings.REFRESH_TOKEN_EXP),
            **cookies_params,
        )
    return response


def delete_cookies(response: JSONResponse, role: RoleType) -> JSONResponse:
    """
    Delete authentication cookies from an HTTP response.
    This function takes an HTTP response object and removes the "accessToken" and "refreshToken" cookies
    from the response, making them invalid for subsequent requests.
    Args:
        response (Response): The HTTP response object to remove cookies from.
        role(Role type): The role type of user.
    Returns:
        Response: The updated HTTP response with the cookies removed.
    """
    cookie_params = {
        "domain": settings.COOKIES_DOMAIN,
        "secure": True,
        "samesite": "lax" if settings.is_production else "none",
        "httponly": False,
    }

    if role == RoleType.USER:
        response.delete_cookie("accessToken", **cookie_params)
        response.delete_cookie("refreshToken", **cookie_params)
    elif role == RoleType.ADMIN:
        response.delete_cookie("adminAccessToken", **cookie_params)
        response.delete_cookie("adminRefreshToken", **cookie_params)

    return response
