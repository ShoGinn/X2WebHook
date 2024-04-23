from unittest.mock import Mock, patch

import pytest
from x2webhook.core import App
from x2webhook.settings import Settings


# Parametrized test cases for happy path, edge cases, and error cases
@pytest.mark.parametrize(
    ("mongodb_uri", "mongodb_db_name", "expected_twikit_locale"),
    [
        pytest.param("mongodb://localhost:27017", "db_name", "en-US", id="happy_path_local_mongodb"),
        pytest.param("mongodb+srv://user:pass@cluster", "db_name", "en-US", id="happy_path_atlas_mongodb"),
        pytest.param("mongodb://user:pass@localhost:27017", "db_name", "en-US", id="edge_case_with_auth"),
        pytest.param("", "db_name", "en-US", id="error_case_empty_mongodb_uri", marks=pytest.mark.xfail),
        pytest.param(
            "invalid_uri",
            "db_name",
            "en-US",
            id="error_case_invalid_mongodb_uri",
            marks=pytest.mark.xfail,
        ),
    ],
)
@patch("x2webhook.core.MongoDBClient")
@patch("x2webhook.core.Client")
def test_initialize_clients(
    mock_twikit_client: Mock,
    mock_mongodb_client: Mock,
    mongodb_uri: str,
    mongodb_db_name: str,
    expected_twikit_locale: str,
) -> None:
    # Arrange
    settings = Settings(mongodb_uri=mongodb_uri, mongodb_db_name=mongodb_db_name)

    # Act
    app = App(settings)

    # Assert
    mock_mongodb_client.assert_called_once_with(
        uri=mongodb_uri, db_name=mongodb_db_name, users_collection="users", cookies_collection="cookies"
    )
    mock_twikit_client.assert_called_once_with(expected_twikit_locale)
    assert isinstance(
        app.twikit_client, mock_twikit_client.return_value.__class__
    ), "twikit client should be initialized"
    assert isinstance(
        app.mongodb_client, mock_mongodb_client.return_value.__class__
    ), "MongoDB client should be initialized"


# Using pytest's parametrize feature to cover various test cases including happy paths, edge cases, and error cases.
@pytest.mark.parametrize(
    ("error_count", "max_errors", "e", "expected_error_count", "expected_logs", "expected_result"),
    [
        # Happy path tests with realistic values
        (0, 5, ValueError("Test error"), 1, ["Error: Test error. Retrying..."], False),
        (
            4,
            5,
            RuntimeError("Another error"),
            5,
            [
                "Error: Another error. Retrying...",
                "Maximum number of errors (5) reached. Stopping...",
            ],
            True,
        ),
        # Edge case: error_count is just below max_errors
        (
            4,
            5,
            Exception("Edge case error"),
            5,
            [
                "Error: Edge case error. Retrying...",
                "Maximum number of errors (5) reached. Stopping...",
            ],
            True,
        ),
        # Error case: error_count starts equal to max_errors (should log max errors reached immediately)
        (
            5,
            5,
            Exception("Max errors reached"),
            6,
            [
                "Error: Max errors reached. Retrying...",
                "Maximum number of errors (5) reached. Stopping...",
            ],
            True,
        ),
        # Edge case: max_errors is 0, should always log max errors reached
        (
            0,
            0,
            Exception("Zero max errors"),
            1,
            [
                "Error: Zero max errors. Retrying...",
                "Maximum number of errors (0) reached. Stopping...",
            ],
            True,
        ),
    ],
    ids=["happy-path-1", "happy-path-2", "edge-case-1", "error-case-1", "edge-case-2"],
)
@patch("x2webhook.core.logger")
def test_handle_errors(
    mock_logger: Mock,
    error_count: int,
    max_errors: int,
    e: Exception,
    expected_error_count: int,
    expected_logs: list,
    expected_result: bool,  # noqa: FBT001
) -> None:
    # Act
    app = App(Settings())
    app.error_count = error_count
    app.max_errors = max_errors
    result = app.maximum_error_handler(e)

    # Assert
    assert result == expected_result, "The return value of handle_errors does not match the expected value."
    assert (
        app.error_count == expected_error_count
    ), "The error_count returned by handle_errors does not match the expected value."
    for expected_log in expected_logs:
        mock_logger.error.assert_any_call(expected_log)
    assert mock_logger.error.call_count == len(
        expected_logs
    ), "The number of logged errors does not match the expected number."


# Parametrized tests for various scenarios
@patch("x2webhook.core.App._init_clients")
@patch("x2webhook.core.logger")
@pytest.mark.parametrize(
    (
        "exception_raised",
        "expected_error_count",
        "iterations",
    ),
    [
        (None, 0, 0),
        (Exception("Sample error"), 6, 6),
        (Exception("Sample error"), 1, 1),
    ],
    ids=["HappyPath-1", "EdgeCase-MaxErrorsReached", "ErrorCase-ExceptionRaised"],
)
def test_main_loop(
    mock_logger: Mock,
    mock_init_clients: Mock,
    exception_raised: Exception,
    expected_error_count: int,
    iterations: int,
) -> None:
    # Arrange
    mock_twikit_client = Mock()
    mock_mongodb_client = Mock()
    mock_init_clients.return_value = (mock_twikit_client, mock_mongodb_client)
    app_settings = Mock()
    app_settings.timer_interval = 0
    if exception_raised:
        mock_mongodb_client.get_users.side_effect = exception_raised
    else:
        mock_mongodb_client.get_users.return_value = []

    # Act
    app = App(app_settings)
    app.main_loop(
        num_iterations=iterations,
    )

    # Assert
    if exception_raised:
        assert mock_logger.error.call_count == expected_error_count
    else:
        assert mock_logger.error.call_count == 0


@patch("x2webhook.core.App.main_loop")
@patch("x2webhook.core.x_login")
def test_run_normal(mock_x_login: Mock, mock_main_loop: Mock) -> None:
    # Arrange
    mock_x_login.return_value = True
    app = App(Settings())
    app.run()
    assert mock_x_login.called
    assert mock_main_loop.called


@patch("x2webhook.core.App.main_loop")
@patch("x2webhook.core.x_login")
def test_run_error(mock_x_login: Mock, mock_main_loop: Mock) -> None:
    # Arrange
    mock_x_login.return_value = False
    app = App(Settings())
    app.run()
    assert mock_x_login.called
    assert not mock_main_loop.called
