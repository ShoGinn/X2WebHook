from typing import Literal
from unittest import mock

import pytest
import pytest_mock
import responses
from pydantic import HttpUrl
from x2webhook.db.user import User
from x2webhook.webhook import create_payload, create_webhook_wait_url, post_tweet


@pytest.fixture()
def mock_session(mocker: pytest_mock.MockerFixture) -> mock.MagicMock:
    return mocker.patch("requests.Session")


@pytest.fixture()
def mock_response() -> mock.MagicMock:
    return mock.MagicMock()


@pytest.fixture()
def payload() -> dict[str, str]:
    return {"message": "Hello, world!"}


# Mocking external dependencies
@pytest.fixture()
def mock_user() -> User:
    return User(
        account_to_check="TestUser",
        webhook_url=HttpUrl("http://example.com/webhook"),  # pyright: ignore[reportCallIssue]
        posting_text="Check out this tweet: <tweet_link>",
        webhook_avatar_url=HttpUrl("http://example.com/avatar.jpg"),  # pyright: ignore[reportCallIssue]
        webhook_name="TestUser",
    )


# Happy path tests with various realistic test values
@pytest.mark.parametrize(
    ("x_user", "tweet_link", "expected_payload"),
    [
        # Test ID: Happy-Path-1
        (
            User(
                account_to_check="TestUser",
                webhook_url=HttpUrl("http://example.com/webhook"),  # pyright: ignore[reportCallIssue]
                posting_text="Check out this tweet: <tweet_link>",
                webhook_avatar_url=HttpUrl("http://example.com/avatar.jpg"),  # pyright: ignore[reportCallIssue]
                webhook_name="TestUser",
            ),
            "http://x.com/tweet/123",
            {
                "content": "Check out this tweet: http://x.com/tweet/123",
                "avatar_url": "http://example.com/avatar.jpg",
                "username": "TestUser",
            },
        ),
        (
            User(
                account_to_check="TestUser",
                webhook_url=HttpUrl("http://example.com/webhook"),  # pyright: ignore[reportCallIssue]
                posting_text="Check out this tweet: <tweet_link>",
                webhook_avatar_url=HttpUrl("http://example.com/avatar.jpg"),  # pyright: ignore[reportCallIssue]
            ),
            "http://x.com/tweet/123",
            {
                "content": "Check out this tweet: http://x.com/tweet/123",
                "avatar_url": "http://example.com/avatar.jpg",
            },
        ),
        (
            User(
                account_to_check="TestUser",
                webhook_url=HttpUrl("http://example.com/webhook"),  # pyright: ignore[reportCallIssue]
                posting_text="Check out this tweet: <tweet_link>",
                webhook_name="TestUser",
            ),
            "http://x.com/tweet/123",
            {
                "content": "Check out this tweet: http://x.com/tweet/123",
                "username": "TestUser",
            },
        ),
        (
            User(
                account_to_check="TestUser",
                webhook_url=HttpUrl("http://example.com/webhook"),  # pyright: ignore[reportCallIssue]
                posting_text="Check out this tweet: <tweet_link>",
            ),
            "http://x.com/tweet/123",
            {
                "content": "Check out this tweet: http://x.com/tweet/123",
            },
        ),
    ],
)
def test_create_payload_happy_path(
    x_user: User,
    tweet_link: str,
    expected_payload: dict[str, str],
) -> None:
    # Act
    payload = create_payload(x_user, tweet_link)

    # Assert
    assert payload == expected_payload, "The payload does not match the expected output."


# Edge cases
@pytest.mark.parametrize(
    ("x_user", "tweet_link", "expected_payload"),
    [
        # Test ID: Edge-Case-1 (empty tweet link)
        (
            User(
                account_to_check="TestUser",
                webhook_url=HttpUrl("http://example.com/webhook"),  # pyright: ignore[reportCallIssue]
                posting_text="Check out this tweet: <tweet_link>",
                webhook_avatar_url=HttpUrl("http://example.com/avatar.jpg"),  # pyright: ignore[reportCallIssue]
                webhook_name="TestUser",
            ),
            "",
            {
                "content": "Check out this tweet: ",
                "avatar_url": "http://example.com/avatar.jpg",
                "username": "TestUser",
            },
        ),
    ],
)
def test_create_payload_edge_cases(
    x_user: User,
    tweet_link: Literal["", "http://x.com/tweet/101"],
    expected_payload: dict[str, str],
) -> None:
    # Act
    payload = create_payload(x_user, tweet_link)

    # Assert
    assert payload == expected_payload, "The payload does not match the expected output for edge cases."


@pytest.mark.parametrize(
    ("webhook_url", "expected", "kwargs", "test_id"),
    [
        # Happy path tests
        (
            "http://example.com",
            "http://example.com?wait=true",
            {"add_wait": True},
            "id=happy_path_no_params",
        ),
        (
            "http://example.com?",
            "http://example.com?wait=true",
            {"add_wait": True},
            "id=happy_path_empty_param",
        ),
        (
            "http://example.com/webhook",
            "http://example.com/webhook?wait=true",
            {"add_wait": True},
            "id=happy_path_with_path",
        ),
        (
            "https://example.com/webhook?param=value",
            "https://example.com/webhook?param=value&wait=true",
            {"add_wait": True},
            "id=happy_path_with_other_param",
        ),
        (
            "http://example.com/webhook?wait=true",
            "http://example.com/webhook",
            {"add_wait": False},
            "id=happy_path_remove_wait",
        ),
        # Edge cases
        (
            "http://example.com?wait=true",
            "http://example.com?wait=true",
            {"add_wait": True},
            "id=edge_case_already_has_wait_true",
        ),
        (
            "http://example.com/webhook?wait=false&wait=true",
            "http://example.com/webhook?wait=true",
            {"add_wait": True},
            "id=edge_case_conflicting_wait_param",
        ),
        # Error cases are not applicable here as the function does not raise errors or
        # handle inputs that could lead to errors.
    ],
)
def test_create_webhook_wait_url(webhook_url: str, expected: str, test_id: str, kwargs: dict[str, bool]) -> None:
    # Act
    result = create_webhook_wait_url(webhook_url, **kwargs)

    # Assert
    assert result == expected, f"Test {test_id} failed. Expected {expected}, got {result}"


# Parametrized test cases for happy path, edge cases, and error cases
@pytest.mark.parametrize(
    ("wait_for_response", "expected_url"),
    [
        ({"wait_for_response": True}, "https://example.com/webhook?wait=true"),
        ({"wait_for_response": False}, "https://example.com/webhook"),
    ],
)
def test_post_tweet_happy_path(
    mock_user: User,
    payload: dict[str, str],
    wait_for_response: dict[str, bool],
    expected_url: str,
) -> None:
    with (
        mock.patch("x2webhook.webhook.post") as mock_post,
        mock.patch(
            "x2webhook.webhook.create_webhook_wait_url",
            return_value=expected_url,
        ) as mock_create_url,
    ):
        mock_post.return_value = (
            mock.MagicMock(),
            None,
        )  # Simulating successful request

        # Arrange

        # Act
        post_tweet(mock_user, payload, **wait_for_response)

        # Assert
        mock_create_url.assert_called_with(str(mock_user.webhook_url), add_wait=wait_for_response["wait_for_response"])
        mock_post.assert_called_with(
            expected_url,
            json=payload,
        )


def test_post_tweet_error_cases(
    mock_user: User, payload: dict[str, str], http_responses: responses.RequestsMock
) -> None:
    http_responses.add(
        responses.POST,
        str(mock_user.webhook_url),
        status=500,
    )
    post_tweet(mock_user, payload, wait_for_response=True)
    # The function should log the error message
