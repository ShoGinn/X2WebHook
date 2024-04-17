"""A Helper module for requests."""

import json
from typing import Any

import requests
from loguru import logger


class RequestsHelper:
    """A wrapper around :class:`requests.Session`.

    which enables generically handling HTTP requests

    """

    @classmethod
    def request(  # noqa: PLR0912
        cls,
        *args: Any,
        url: str,
        method: str,
        raise_for_status: bool = True,
        path_to_errors: tuple | None = None,
        **kwargs: Any,
    ) -> tuple:
        """Execute an HTTP request using the provided URL and method.

        Args:
            url (str): The URL to send the request to.
            method (str): The HTTP method to use for the request.
            raise_for_status (bool, optional): Whether to raise an exception if the
                            response status code indicates an error. Defaults to True.
            path_to_errors (Optional[tuple], optional): A tuple representing the path
                        to the error messages in the response JSON. Defaults to None.
            **kwargs: Additional keyword arguments to be passed to the
                        `requests.Session.request` method.

        Returns:
            tuple: A tuple containing the response object and any error messages.

        Raises:
            requests.RequestException: If an error occurs while sending the request.

        Example:
            ```python
            session = requests.Session()
            response, errors = request(
                url="https://example.com", method="GET", session=session
                )
            if response is not None:
                print("Request successful!")
                print("Response:", response.text)
            else:
                print("Request failed!")
                print("Errors:", errors)
            ```

        """
        session = kwargs.get("session", requests.Session())
        if "timeout" not in kwargs:
            kwargs["timeout"] = (5, 20)
        logger.trace(f"sending a {method.upper()} request to {url} with args: {args} " f"kwargs: {kwargs}")

        if raise_for_status:
            try:
                rsp = session.request(method, url, *args, **kwargs)
                logger.trace(f"response: {rsp.text}")
                errors = None
                rsp.raise_for_status()
            except requests.RequestException as exc:
                if exc.response is not None:
                    rsp = exc.response
                    if path_to_errors:
                        try:
                            errors = rsp.json()
                            for arg in path_to_errors:
                                if errors.get(arg):
                                    errors = errors[arg]
                        except json.decoder.JSONDecodeError:
                            errors = [rsp.text]
                    else:
                        errors = [rsp.text]
                    if not isinstance(errors, list):
                        errors = [errors]
                else:
                    rsp = None
                    errors = [str(exc)]
                logger.trace(f"errors when trying to access {url}: {errors}")
        logger.trace(f"returning response {rsp}, errors {errors}")
        return rsp, errors


def get(url: str, *args: Any, **kwargs: Any) -> tuple:
    """Send an HTTP GET request to the specified URL.

    Args:
        url (str): The URL to send the GET request to.
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.

    Returns:
        tuple: A tuple containing the response object and any error messages.

    Example:
        ```python
        response, errors = get(
            "https://example.com", headers={"Authorization": "Bearer token"}
            )
        if response is not None:
            print("Request successful!")
            print("Response:", response.text)
        else:
            print("Request failed!")
            print("Errors:", errors)
        ```

    """
    return RequestsHelper.request(*args, url=url, method="get", **kwargs)


def post(url: str, *args: Any, **kwargs: Any) -> tuple:
    """Send an HTTP POST request to the specified URL.

    Args:
        url (str): The URL to send the POST request to.
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.

    Returns:
        tuple: A tuple containing the response object and any error messages.

    Example:
        ```python
        response, errors = post("https://example.com", data={"key": "value"})
        if response is not None:
            print("Request successful!")
            print("Response:", response.text)
        else:
            print("Request failed!")
            print("Errors:", errors)
        ```

    """
    return RequestsHelper.request(*args, url=url, method="post", **kwargs)
