from fastapi.responses import JSONResponse

from config import settings


def set_auth_cookies(
    response: JSONResponse, tokens: dict[str, str]
) -> JSONResponse:
    """
    Set authentication cookies in an HTTP response.

    Args:
        response: The HTTP response object to set cookies in.
        tokens: A dictionary containing access and refresh tokens.

    Returns:
        The updated HTTP response with the authentication cookies set.
    """
    cookies_params = {
        "domain": settings.COOKIES_DOMAIN,
        "secure": True,
        "samesite": "lax" if settings.is_production else "none",
        "httponly": True,
    }

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
    return response


def delete_cookies(response: JSONResponse) -> JSONResponse:
    """
    Delete authentication cookies from an HTTP response.

    Args:
        response: The HTTP response object to remove cookies from.

    Returns:
        The updated HTTP response with the cookies removed.
    """
    cookie_params = {
        "domain": settings.COOKIES_DOMAIN,
        "secure": True,
        "samesite": "lax" if settings.is_production else "none",
        "httponly": False,
    }

    response.delete_cookie("accessToken", **cookie_params)
    response.delete_cookie("refreshToken", **cookie_params)

    return response
