from typing import Any

from httpx import AsyncClient, Response

from exceptions import UnexpectedResponse


class HTTPClient:
    """
    HTTP client for making HTTP requests to a specified base URL.

    This class provides methods to perform GET, POST, PUT, PATCH,
    and DELETE requests with custom headers and parameters.
    """

    def __init__(
        self, base_url: str | None = "", headers: dict[str, str] | None = None
    ) -> None:
        self.base_url = base_url
        self.headers = headers

    async def get(
        self,
        url: str | None = None,
        headers: dict[str, str] | None = None,
        query_params: dict[str, str] | None = None,
        path_params: dict[str, str] | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """
        Send a GET request.

        :param url: The URL to send the request to. Defaults to None.
        :param headers: Headers to include in the request. Defaults to None.
        :param query_params: Query parameters to include in the request. Defaults to None.
        :param path_params: Path parameters to include in the request. Defaults to None.

        :return: The JSON response from the server.
        """
        if url and path_params:
            url = url.format(**path_params)
        async with AsyncClient(
            base_url=self.base_url, headers=headers, timeout=None
        ) as session:
            response = await session.get(url, headers=headers, params=query_params)
            response.raise_for_status()
            return response.json()

    async def post(
        self,
        url: str | None = None,
        headers: dict[str, str] | None = None,
        query_params: dict[str, str] | None = None,
        path_params: dict[str, str] | None = None,
        json: dict[str, str] | dict[str, dict[str, Any]] | None = None,
        content: Any | None = None,
        return_error: bool | None = False,
    ) -> Response | Any:
        """
        Send a POST request.

        :param url: The URL to send the request to. Defaults to None.
        :param headers: Headers to include in the request. Defaults to None.
        :param query_params: Query parameters to include in the request. Defaults to None.
        :param path_params: Path parameters to include in the request. Defaults to None.
        :param json: JSON payload to include in the request body. Defaults to None.
        :param content: Raw content to include in the request body. Defaults to None.
        :param return_error: Whether to return the response on error. Defaults to False.

        :return: The JSON response from the server or the full response if return_error is True.
        """
        if url and path_params:
            url = url.format(**path_params)
        async with AsyncClient(
            base_url=self.base_url, headers=headers, timeout=None
        ) as session:
            response = await session.post(
                url, headers=headers, params=query_params, json=json, content=content
            )
            if response.status_code in [200, 201, 203, 204]:
                return response.json()
            if return_error:
                return response
            raise UnexpectedResponse(response=response)

    async def put(
        self,
        url: str | None = None,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
        path_params: dict[str, str] | None = None,
        json: str | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """
        Send a PUT request.

        :param url: The URL to send the request to. Defaults to None.
        :param headers: Headers to include in the request. Defaults to None.
        :param params: Query parameters to include in the request. Defaults to None.
        :param path_params: Path parameters to include in the request. Defaults to None.
        :param json: JSON payload to include in the request body. Defaults to None.

        :return: The JSON response from the server.
        """
        if url and path_params:
            url = url.format(**path_params)
        async with AsyncClient(
            base_url=self.base_url, headers=headers, timeout=None
        ) as session:
            response = await session.put(url, headers=headers, params=params, json=json)
            response.raise_for_status()
            return response.json()

    async def patch(
        self,
        url: str | None = None,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
        path_params: dict[str, str] | None = None,
        json: str | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """
        Send a PATCH request.

        :param url: The URL to send the request to. Defaults to None.
        :param headers: Headers to include in the request. Defaults to None.
        :param params: Query parameters to include in the request. Defaults to None.
        :param path_params: Path parameters to include in the request. Defaults to None.
        :param json: JSON payload to include in the request body. Defaults to None.

        :return: The JSON response from the server.
        """
        if url and path_params:
            url = url.format(**path_params)
        async with AsyncClient(
            base_url=self.base_url, headers=headers, timeout=None
        ) as session:
            response = await session.patch(
                url, headers=headers, params=params, json=json
            )
            response.raise_for_status()
            return response.json()

    async def delete(
        self,
        url: str | None = None,
        headers: dict[str, str] | None = None,
        query_params: dict[str, str] | None = None,
        path_params: dict[str, str] | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """
        Deletes a resource at the specified URL.

        :param url: The URL of the resource to delete. If not specified, the URL of the current instance will be used.
        :param headers: A dictionary of HTTP headers to include with the request.
        :param query_params: A dictionary of query string parameters to include with the request.
        :param path_params: A dictionary of path parameters to include with the request.

        :return: A dictionary or list of dictionaries representing the deleted resource(s).
        """
        if url and path_params:
            url = url.format(**path_params)
        async with AsyncClient(
            base_url=self.base_url, headers=headers, timeout=None
        ) as session:
            response = await session.delete(url, headers=headers, params=query_params)
            response.raise_for_status()
            return response.json()
