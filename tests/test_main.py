from importlib.metadata import PackageNotFoundError
from unittest.mock import MagicMock, Mock, patch

import pytest
import pytest_mock
from x2webhook import __main__
from x2webhook.settings import Settings


@pytest.fixture()
def metadata_mock(mocker: pytest_mock.MockerFixture) -> MagicMock:
    return mocker.patch("x2webhook.__main__.importlib.metadata")


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
@patch("x2webhook.__main__.MongoDBClient")
@patch("x2webhook.__main__.Client")
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
    twikit_client, mongodb_client = __main__.initialize_clients(settings)

    # Assert
    mock_mongodb_client.assert_called_once_with(
        uri=mongodb_uri, db_name=mongodb_db_name, users_collection="users", cookies_collection="cookies"
    )
    mock_twikit_client.assert_called_once_with(expected_twikit_locale)
    assert isinstance(twikit_client, mock_twikit_client.return_value.__class__), "twikit client should be initialized"
    assert isinstance(
        mongodb_client, mock_mongodb_client.return_value.__class__
    ), "MongoDB client should be initialized"


# Using pytest's parametrize feature to cover various test cases including happy paths, edge cases, and error cases.
@pytest.mark.parametrize(
    ("error_count", "max_errors", "e", "expected_error_count", "expected_logs"),
    [
        # Happy path tests with realistic values
        (0, 5, ValueError("Test error"), 1, ["Error: Test error. Retrying..."]),
        (
            4,
            5,
            RuntimeError("Another error"),
            5,
            [
                "Error: Another error. Retrying...",
                "Maximum number of errors (5) reached. Stopping...",
            ],
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
        ),
    ],
    ids=["happy-path-1", "happy-path-2", "edge-case-1", "error-case-1", "edge-case-2"],
)
@patch("x2webhook.__main__.logger")
def test_handle_errors(
    mock_logger: Mock,
    error_count: int,
    max_errors: int,
    e: Exception,
    expected_error_count: int,
    expected_logs: list,
) -> None:
    # Act
    result = __main__.handle_errors(error_count, max_errors, e)

    # Assert
    assert (
        result == expected_error_count
    ), "The error_count returned by handle_errors does not match the expected value."
    for expected_log in expected_logs:
        mock_logger.error.assert_any_call(expected_log)
    assert mock_logger.error.call_count == len(
        expected_logs
    ), "The number of logged errors does not match the expected number."


# Parametrized tests for various scenarios
@pytest.mark.parametrize(
    (
        "exception_raised",
        "expected_error_count",
        "iterations",
    ),
    [
        (None, 0, 0),
        (Exception("Sample error"), 5, 6),
        (Exception("Sample error"), 1, 1),
    ],
    ids=["HappyPath-1", "EdgeCase-MaxErrorsReached", "ErrorCase-ExceptionRaised"],
)
def test_main_loop(
    exception_raised: Exception,
    expected_error_count: int,
    iterations: int,
) -> None:
    # Arrange
    mock_twikit_client = Mock()
    mock_mongodb_client = Mock()
    app_settings = Mock()
    app_settings.timer_interval = 0
    if exception_raised:
        mock_mongodb_client.get_users.side_effect = exception_raised
    else:
        mock_mongodb_client.get_users.return_value = []

    # Act
    with patch("x2webhook.__main__.handle_errors", return_value=expected_error_count) as mock_handle_errors:
        __main__.main_loop(
            app_settings,
            mock_twikit_client,
            mock_mongodb_client,
            num_iterations=iterations,
        )

    # Assert
    if exception_raised:
        mock_handle_errors.assert_called()
    else:
        mock_handle_errors.assert_not_called()


@patch("x2webhook.__main__.get_config")
@patch("x2webhook.__main__.setup_logger")
@patch("x2webhook.__main__.initialize_clients")
@patch("x2webhook.__main__.x_login")
@patch("x2webhook.__main__.main_loop")
def test_main(
    mock_main_loop: Mock,
    mock_x_login: Mock,
    mock_initialize_clients: Mock,
    mock_setup_logger: Mock,
    mock_get_config: Mock,
) -> None:
    # Arrange
    mock_main_loop.side_effect = [None, None]
    mock_get_config.return_value = Mock()
    mock_initialize_clients.return_value = (Mock(), Mock())

    # Act
    __main__.main()

    # Assert
    mock_get_config.assert_called()
    mock_setup_logger.assert_called()
    mock_initialize_clients.assert_called()
    mock_x_login.assert_called()
    mock_main_loop.assert_called()


@pytest.mark.parametrize(
    ("package_name", "expected_version", "test_id"),
    [
        (__name__, "1.0.0", "happy_path_current_module"),
        (__package__, "2.3.4", "happy_path_current_package"),
        ("nonexistent_package", "Unknown", "error_nonexistent_package"),
    ],
)
def test_get_version(metadata_mock: MagicMock, package_name: str, expected_version: str, test_id: str) -> None:
    # Arrange
    if package_name != "nonexistent_package":
        metadata_mock.version.return_value = expected_version
    else:
        metadata_mock.version.side_effect = PackageNotFoundError
    # Act
    result = __main__.get_version()

    # Assert
    assert result == expected_version, f"Test ID: {test_id}"
