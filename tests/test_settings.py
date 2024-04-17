import pytest
from pydantic import SecretStr
from x2webhook.settings import AppEnv, LogLevel, Settings, get_config


# Define a fixture for environment setup if needed
@pytest.fixture()
def _load_env(monkeypatch: pytest.MonkeyPatch) -> None:
    # Example of setting environment variables if needed for tests
    monkeypatch.setenv("X2WEBHOOK_X_USERNAME", "test_user")


# Happy path tests
@pytest.mark.parametrize(
    (
        "app_env",
        "log_level",
        "x_username",
        "x_password",
        "x_email",
        "timer_interval",
        "mongodb_uri",
        "test_id",
    ),
    [
        (
            AppEnv.local,
            LogLevel.debug,
            "user1",
            "pass1",
            "email1@test.com",
            300,
            "mongodb://localhost:27017",
            "happy_path_default",
        ),
        (
            AppEnv.prod,
            LogLevel.error,
            "user2",
            "pass2",
            "email2@test.com",
            600,
            "mongodb://remotehost:27017",
            "happy_path_production",
        ),
        # Add more test cases as needed
    ],
    ids=lambda test_id: test_id,
)
def test_settings_happy_path(
    app_env: AppEnv,
    log_level: LogLevel,
    x_username: str,
    x_password: str,
    x_email: str,
    timer_interval: int,
    mongodb_uri: str,
    test_id: str,  # noqa: ARG001
) -> None:
    # Arrange
    # In this case, all inputs are provided via test parameters, so we skip
    # directly to Act

    # Act
    settings = Settings(
        app_env=app_env,
        log_level=log_level,
        x_username=x_username,
        x_password=SecretStr(x_password),
        x_email=x_email,
        timer_interval=timer_interval,
        mongodb_uri=mongodb_uri,
    )

    # Assert
    assert settings.app_env == app_env
    assert settings.log_level == log_level
    assert settings.x_username == x_username
    assert settings.x_password.get_secret_value() == x_password
    assert settings.x_email == x_email
    assert settings.timer_interval == timer_interval
    assert settings.mongodb_uri == mongodb_uri


# Edge cases
# Here you would define tests for edge cases, such as minimal/maximal values
# or unexpected but valid inputs


# Error cases
# Tests for error cases would include providing invalid types or formats for each field
# Pydantic should raise validation errors for these, which you can catch and assert
@pytest.mark.parametrize(
    "test_id",
    [
        ("happy_path_default_settings"),
        # Add more IDs for different configurations if applicable and testable
    ],
)
def test_get_config(test_id: str) -> None:
    # Arrange
    # (In this case, there's nothing to arrange since the function takes no parameters
    # and has no setup.)

    # Act
    result = get_config()

    # Assert
    assert isinstance(result, Settings), f"get_config should return an instance of Settings for {test_id}"
    # Here you might also assert on default values or states of the Settings instance,
    # assuming there are any that can be checked. This would depend on the
    # implementation details of the Settings class.
