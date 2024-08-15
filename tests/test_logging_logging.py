import datetime
from unittest.mock import Mock

import pytest
from pytest_mock import MockerFixture

from x2webhook.logging.logging import setup_logger, structured_formatter
from x2webhook.settings import AppEnv


# Mocking get_config to control the environment setting for tests
class MockConfig:
    def __init__(self, app_env: str) -> None:
        self.app_env = app_env
        self.log_level = "DEBUG"


@pytest.mark.parametrize(
    ("env", "expected_output", "test_id"),
    [
        (AppEnv.prod, True, "happy_path_prod_debug"),
        (AppEnv.stage, True, "happy_path_stage_info"),
        (AppEnv.qa, True, "happy_path_qa_warning"),
        (AppEnv.dev, True, "happy_path_dev_error"),
        (AppEnv.test, True, "happy_path_test_debug"),
        (AppEnv.local, True, "happy_path_local_info"),
        ("unknown_env", False, "error_case_unknown_env"),
    ],
)
def test_setup_logger(
    env: str,
    expected_output: bool,  # noqa: FBT001
    test_id: str,
    mocker: MockerFixture,
) -> None:
    # Arrange
    def mock_get_config() -> MockConfig:
        return MockConfig(app_env=env)

    mocker.patch("x2webhook.logging.logging.get_config", mock_get_config)

    # Act and Assert
    if expected_output:
        try:
            setup_logger()
            assert True  # If no exception is raised, the setup was successful
        except Exception as e:
            pytest.fail(f"Unexpected exception for {test_id}: {e}")
    else:
        with pytest.raises(RuntimeError) as exc_info:
            setup_logger()
        assert str(exc_info.value) == f"Unknown environment: {env}, Exiting...", f"Failed {test_id}"


def test_structured_formatter() -> None:
    # Arrange
    level = Mock()
    level.name = "INFO"
    file = Mock()
    file.path = "test_file.py"

    record = {
        "time": datetime.datetime.fromtimestamp(1234567890.0, tz=datetime.timezone.utc),
        "level": level,
        "message": "This is a test message",
        "file": file,
        "line": 42,
        "extra": {"__json_serialized": '{"key": "value"}'},
    }
    expected_output = "{extra[__json_serialized]}\n"
    # Act
    result = structured_formatter(record)  # type: ignore[arg-type]

    # Assert
    assert result == expected_output
