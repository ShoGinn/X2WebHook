"""This module contains the settings for the application."""

import os
from enum import Enum

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnv(str, Enum):
    """Enumeration representing the different application environments.

    Attributes:
        local (str): Local development environment.
        test (str): Testing environment.
        dev (str): Development environment.
        qa (str): Quality assurance environment.
        stage (str): Staging environment.
        prod (str): Production environment.
    """

    local = "local"
    test = "test"
    dev = "dev"
    qa = "qa"
    stage = "stage"
    prod = "prod"


class LogLevel(str, Enum):
    """Represents the log levels for logging messages.

    The available log levels are:
    - trace: For very detailed logging, typically used for debugging purposes.
    - debug: For debugging information.
    - info: For general information.
    - success: For successful operations.
    - warning: For warnings that may indicate potential issues.
    - error: For errors that occurred but did not prevent the program from continuing.
    - critical: For critical errors that may cause the program to terminate.

    Each log level is represented by a string value.
    """

    trace = "TRACE"
    debug = "DEBUG"
    info = "INFO"
    success = "SUCCESS"
    warning = "WARNING"
    error = "ERROR"
    critical = "CRITICAL"


class Settings(BaseSettings):
    """Represents the settings for the x2webhook application."""

    model_config = SettingsConfigDict(env_prefix="x2webhook_")
    app_env: AppEnv = AppEnv.local
    log_level: LogLevel = LogLevel.debug

    x_client_language: str = "en-US"
    x_username: str = ""
    x_password: SecretStr = SecretStr("")
    x_email: str = ""

    timer_interval: int = 300
    mongodb_uri: str = Field(default="mongodb://localhost:27017")
    mongodb_db_name: str = "x2webhook"
    mongodb_users_collection: str = "users"
    mongodb_cookies_collection: str = "cookies"


def get_config() -> Settings:
    """Return the configuration settings.

    Returns:
        Settings: An instance of the Settings class representing the configuration.
    """
    env_file = None if "PYTEST_CURRENT_TEST" in os.environ else ".env"
    env_file_encoding = None if "PYTEST_CURRENT_TEST" in os.environ else "utf-8"
    return Settings(_env_file=env_file, _env_file_encoding=env_file_encoding)  # type: ignore[call-arg]
