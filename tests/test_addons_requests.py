"""Test module for the requests module."""

from json.decoder import JSONDecodeError
from unittest import mock

import pytest
import pytest_mock
import requests
from x2webhook.addons.requests import RequestsHelper, get, post


@pytest.fixture()
def requests_logger(mocker: pytest_mock.MockerFixture) -> mock.MagicMock:
    return mocker.patch("x2webhook.addons.requests.logger")


@pytest.fixture()
def mock_session(mocker: pytest_mock.MockerFixture) -> mock.MagicMock:
    return mocker.patch("requests.Session")


@pytest.fixture()
def mock_response() -> mock.MagicMock:
    return mock.MagicMock()


class TestRequestsHelper:
    def test_request(
        self,
        requests_logger: mock.MagicMock,
        mock_session: mock.MagicMock,
        mock_response: mock.MagicMock,
    ) -> None:
        """Test the request method."""
        mock_session.request.return_value = mock_response
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_response.text = '{"success": true}'
        mock_response.raise_for_status.return_value = None
        response, errors = RequestsHelper.request(url="https://example.com", method="GET", session=mock_session)
        assert response == mock_response
        assert errors is None
        requests_logger.trace.assert_has_calls(
            [
                mock.call(
                    "sending a GET request to https://example.com with args: () kwargs:"
                    f" {{'session': {mock_session}, 'timeout': (5, 20)}}"
                ),
                mock.call(f"response: {mock_response.text}"),
                mock.call(f"returning response {mock_response}, errors {errors}"),
            ]
        )

    def test_request_errors(
        self,
        requests_logger: mock.MagicMock,
        mock_session: mock.MagicMock,
        mock_response: mock.MagicMock,
    ) -> None:
        """Test the request method."""
        mock_session.request.return_value = mock_response
        mock_response.status_code = 400
        mock_response.json.return_value = {"fails": True}
        mock_response.text = '{"fail": true}'
        mock_response.raise_for_status.side_effect = requests.RequestException(response=mock_response)
        response, errors = RequestsHelper.request(url="https://example.com", method="GET", session=mock_session)
        assert response == mock_response
        assert errors == [mock_response.text]
        requests_logger.trace.assert_has_calls(
            [
                mock.call(
                    "sending a GET request to https://example.com with args: () kwargs:"
                    f" {{'session': {mock_session}, 'timeout': (5, 20)}}"
                ),
                mock.call(f"response: {mock_response.text}"),
                mock.call(f"errors when trying to access https://example.com: {errors}"),
                mock.call(f"returning response {mock_response}, errors {errors}"),
            ]
        )

    def test_request_errors_no_response(
        self,
        requests_logger: mock.MagicMock,
        mock_session: mock.MagicMock,
        mock_response: mock.MagicMock,
    ) -> None:
        """Test the request method."""
        mock_session.request.return_value = mock_response
        mock_response.status_code = 400
        mock_response.json.return_value = {"fails": True}
        mock_response.text = '{"fail": true}'
        mock_response.raise_for_status.side_effect = requests.RequestException()
        response, errors = RequestsHelper.request(url="https://example.com", method="GET", session=mock_session)
        assert errors == [""]
        assert response is None
        requests_logger.trace.assert_has_calls(
            [
                mock.call(
                    "sending a GET request to https://example.com with args: () kwargs:"
                    f" {{'session': {mock_session}, 'timeout': (5, 20)}}"
                ),
                mock.call(f"response: {mock_response.text}"),
                mock.call(f"errors when trying to access https://example.com: {errors}"),
                mock.call(f"returning response None, errors {errors}"),
            ]
        )

    def test_request_errors_path_for_errors(
        self,
        requests_logger: mock.MagicMock,
        mock_session: mock.MagicMock,
        mock_response: mock.MagicMock,
    ) -> None:
        """Test the request method."""
        mock_session.request.return_value = mock_response
        mock_response.status_code = 400
        mock_response.json.return_value = {"fails": True}
        mock_response.text = '{"fail": true}'
        mock_response.raise_for_status.side_effect = requests.RequestException(response=mock_response)
        response, errors = RequestsHelper.request(
            url="https://example.com",
            method="GET",
            session=mock_session,
            path_to_errors=("fails",),
        )
        assert response == mock_response
        assert errors == [True]
        requests_logger.trace.assert_has_calls(
            [
                mock.call(
                    "sending a GET request to https://example.com with args: () kwargs:"
                    f" {{'session': {mock_session}, 'timeout': (5, 20)}}"
                ),
                mock.call(f"response: {mock_response.text}"),
                mock.call(f"errors when trying to access https://example.com: {errors}"),
                mock.call(f"returning response {mock_response}, errors {errors}"),
            ]
        )

    def test_request_errors_path_for_errors_failed_json(
        self,
        requests_logger: mock.MagicMock,
        mock_session: mock.MagicMock,
        mock_response: mock.MagicMock,
    ) -> None:
        """Test the request method."""
        mock_session.request.return_value = mock_response
        mock_response.status_code = 400
        mock_response.json.side_effect = JSONDecodeError("Expecting value", "", 0)
        mock_response.text = "not json"
        mock_response.raise_for_status.side_effect = requests.RequestException(response=mock_response)
        response, errors = RequestsHelper.request(
            url="https://example.com",
            method="GET",
            session=mock_session,
            path_to_errors=("fails",),
        )
        assert response == mock_response
        assert errors == [mock_response.text]
        requests_logger.trace.assert_has_calls(
            [
                mock.call(
                    "sending a GET request to https://example.com with args: () kwargs:"
                    f" {{'session': {mock_session}, 'timeout': (5, 20)}}"
                ),
                mock.call(f"response: {mock_response.text}"),
                mock.call(f"errors when trying to access https://example.com: {errors}"),
                mock.call(f"returning response {mock_response}, errors {errors}"),
            ]
        )

    def test_get_request(
        self,
        requests_logger: mock.MagicMock,
        mock_session: mock.MagicMock,
        mock_response: mock.MagicMock,
    ) -> None:
        """Test the request method."""
        mock_session.request.return_value = mock_response
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_response.text = '{"success": true}'
        mock_response.raise_for_status.return_value = None
        response, errors = get(url="https://example.com", session=mock_session)
        assert response == mock_response
        assert errors is None
        requests_logger.trace.assert_has_calls(
            [
                mock.call(
                    "sending a GET request to https://example.com with args: () kwargs:"
                    f" {{'session': {mock_session}, 'timeout': (5, 20)}}"
                ),
                mock.call(f"response: {mock_response.text}"),
                mock.call(f"returning response {mock_response}, errors {errors}"),
            ]
        )

    def test_post_request(
        self,
        requests_logger: mock.MagicMock,
        mock_session: mock.MagicMock,
        mock_response: mock.MagicMock,
    ) -> None:
        """Test the request method."""
        mock_session.request.return_value = mock_response
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_response.text = '{"success": true}'
        mock_response.raise_for_status.return_value = None
        response, errors = post(url="https://example.com", session=mock_session)
        assert response == mock_response
        assert errors is None
        requests_logger.trace.assert_has_calls(
            [
                mock.call(
                    "sending a POST request to https://example.com with args: "
                    "() kwargs:"
                    f" {{'session': {mock_session}, 'timeout': (5, 20)}}"
                ),
                mock.call(f"response: {mock_response.text}"),
                mock.call(f"returning response {mock_response}, errors {errors}"),
            ]
        )
