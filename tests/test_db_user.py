from typing import Any, cast
from unittest import mock

import pytest
import pytest_mock
from pydantic import HttpUrl, ValidationError
from x2webhook.db.mongodb import MongoDBClient
from x2webhook.db.user import User, create_default_users, load_users_from_db


# Mock the logger
@pytest.fixture()
def user_logger(mocker: pytest_mock.MockFixture) -> mock.MagicMock:
    return mocker.patch("x2webhook.db.user.logger")


@pytest.fixture()
def mock_mongo_client(monkeypatch: pytest.MonkeyPatch) -> mock.MagicMock:
    mock_client = mock.MagicMock()
    monkeypatch.setattr("pymongo.MongoClient", mock_client)
    return mock_client


# Mock MongoDBClient for testing without a real database connection
class MockMongoDBClient:
    def __init__(self) -> None:
        self.users: list = []

    def add_user(self, user: list) -> None:
        self.users.append(user)

    def get_users(self) -> list[User] | None:
        return self.users or None


# User model tests
@pytest.mark.parametrize(
    (
        "test_id",
        "account_to_check",
        "posting_text",
        "webhook_url",
        "webhook_name",
        "webhook_avatar_url",
        "previous_tweet_id",
    ),
    [
        (
            "happy_path_1",
            "ThePSF",
            "Check out this tweet",
            "https://example.com/webhook",
            "Example Webhook",
            "https://example.com/avatar.png",
            "12345",
        ),
        (
            "happy_path_2",
            "X",
            "New tweet alert!",
            "https://example.com/webhook2",
            None,
            None,
            None,
        ),
        (
            "edge_case_long_text",
            "ThePSF",
            "x" * 280,
            "https://example.com/webhook",
            None,
            None,
            None,
        ),
        (
            "error_case_invalid_url",
            "ThePSF",
            "Check out this tweet",
            "not_a_url",
            None,
            None,
            None,
        ),
    ],
)
def test_user_model(
    test_id: str,
    account_to_check: str,
    posting_text: str,
    webhook_url: str,
    webhook_name: str,
    webhook_avatar_url: str,
    previous_tweet_id: str,
) -> None:
    # Arrange
    if test_id.startswith("error_case"):
        with pytest.raises(ValidationError):
            User(
                account_to_check=account_to_check,
                posting_text=posting_text,
                webhook_url=HttpUrl(webhook_url),  # pyright: ignore[reportCallIssue]
                webhook_name=webhook_name,
                webhook_avatar_url=(HttpUrl(webhook_avatar_url) if webhook_avatar_url else None),  # pyright: ignore[reportCallIssue]
                previous_tweet_id=previous_tweet_id,
            )
    else:
        # Act
        user = User(
            account_to_check=account_to_check,
            posting_text=posting_text,
            webhook_url=HttpUrl(webhook_url),  # pyright: ignore[reportCallIssue]
            webhook_name=webhook_name,
            webhook_avatar_url=(HttpUrl(webhook_avatar_url) if webhook_avatar_url else None),  # pyright: ignore[reportCallIssue]
            previous_tweet_id=previous_tweet_id,
        )

        # Assert
        assert user.account_to_check == account_to_check
        assert user.posting_text == posting_text
        assert str(user.webhook_url) == webhook_url
        assert user.webhook_name == webhook_name
        assert (
            str(user.webhook_avatar_url) == webhook_avatar_url
            if webhook_avatar_url
            else user.webhook_avatar_url is None
        )
        assert user.previous_tweet_id == previous_tweet_id


# create_default_users function tests
def test_create_default_users() -> None:
    # Arrange
    mongodb_client = cast(MongoDBClient, MockMongoDBClient())

    # Act
    number_of_users = 2
    users = create_default_users(mongodb_client)

    # Assert
    assert len(users) == number_of_users
    assert all(isinstance(user, User) for user in users)


def test_create_default_users_with_failure(mock_mongo_client: mock.MagicMock) -> None:
    # Arrange
    mongodb_client = MongoDBClient(
        "mongodb://localhost:27017",
        "testdb",
        users_collection="users",
        cookies_collection="cookies",
        mongo_client=mock_mongo_client,
    )
    mock_mongo_client["testdb"]["users_collection"].find.return_value = [{}]
    users = create_default_users(mongodb_client)
    assert len(users) == 0


# load_users_from_db function tests
@pytest.mark.parametrize(
    ("test_id", "initial_users", "expected_log_message"),
    [
        (
            "happy_path_existing_users",
            [
                User(
                    account_to_check="ExistingUser",
                    posting_text="Existing text",
                    webhook_url=HttpUrl("https://example.com/webhook"),  # pyright: ignore[reportCallIssue]
                )
            ],
            None,
        ),
        (
            "happy_path_no_users",
            [],
            "No users found in the database, creating default users...",
        ),
        (
            "validation_error",
            [
                User(
                    account_to_check="",
                    posting_text="Existing text",
                    webhook_url=HttpUrl("https://example.com/webhook"),  # pyright: ignore[reportCallIssue]
                )
            ],
            None,
        ),
    ],
)
def test_load_users_from_db(
    test_id: str,
    initial_users: list[Any],
    expected_log_message: str,
    user_logger: mock.MagicMock,
) -> None:
    # Arrange
    mongodb_client = cast(MongoDBClient, MockMongoDBClient())
    for user in initial_users:
        mongodb_client.add_user(user)

    # Act
    users = load_users_from_db(mongodb_client)

    # Assert
    if expected_log_message:
        assert user_logger.mock_calls == [
            mock.call.error(expected_log_message)
        ], f"Test {test_id} failed. Expected log message: {expected_log_message}"

    assert len(users) > 0
    assert all(isinstance(user, User) for user in users)
