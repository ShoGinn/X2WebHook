from typing import TYPE_CHECKING
from unittest.mock import MagicMock, Mock, patch

import pytest
from pydantic import SecretStr
from twikit.utils import Result  # type: ignore[import-untyped]
from x2webhook.x_engine import (
    check_new_tweets,
    fetch_tweets,
    get_latest_tweets,
    get_non_retweet,
    login_with_cookies,
    login_with_credentials,
    x_login,
)

if TYPE_CHECKING:
    from x2webhook.settings import Settings


def tweet_generator(count: int) -> list:
    return [f"Tweet {i+1}" for i in range(count)]


def create_mock_tweet_result(text: str, tweet_id: str) -> Result:
    return Result(results=[create_mock_tweet(text, tweet_id)])


def create_mock_tweet(text: str, tweet_id: str = "123456") -> MagicMock:
    mock_tweet = MagicMock()
    mock_tweet.id = tweet_id
    mock_tweet.text = text
    return mock_tweet


def get_mock_user(count: int) -> MagicMock:
    mock_user = MagicMock()
    mock_user.get_tweets.return_value = Result(results=tweet_generator(count))
    return mock_user


def get_mock_empty_user() -> MagicMock:
    mock_empty_user = MagicMock()
    mock_empty_user.get_tweets.return_value = Result(results=[])
    return mock_empty_user


def get_mock_twikit_client() -> MagicMock:
    mock_twikit_client = MagicMock()

    def side_effect(screen_name: str) -> MagicMock:
        if screen_name == "valid_user":
            return get_mock_user(count=10)
        elif screen_name == "error_user":
            raise NameError("User not found")
        else:
            return get_mock_empty_user()

    mock_twikit_client.get_user_by_screen_name.side_effect = side_effect
    return mock_twikit_client


# Test cases for parametrized tests
@pytest.mark.parametrize(
    ("test_id", "tweets_input", "expected_output"),
    [
        # Happy path tests
        (
            "happy-1",
            Result(
                [
                    create_mock_tweet("First tweet"),
                    create_mock_tweet("RT @user: Retweet"),
                    create_mock_tweet("Another tweet"),
                ]
            ),
            "First tweet",
        ),
        (
            "happy-2",
            Result(
                [
                    create_mock_tweet("RT @user: Retweet"),
                    create_mock_tweet("Second tweet is not a retweet"),
                ]
            ),
            "Second tweet is not a retweet",
        ),
        ("happy-3", Result([create_mock_tweet("All new tweet here")]), "All new tweet here"),
        # Edge cases
        ("edge-1", Result([]), None),  # Empty list
        (
            "edge-2",
            Result(
                [
                    create_mock_tweet("RT @user: Only retweets"),
                    create_mock_tweet("RT @another: Another retweet"),
                ]
            ),
            None,
        ),  # Only retweets
        (
            "edge-3",
            Result(
                [
                    create_mock_tweet("🚀 Launch tweet"),
                    create_mock_tweet("RT @space: Retweet about space"),
                ]
            ),
            "🚀 Launch tweet",
        ),  # Emoji in tweet
        # Error cases are not applicable here as the function is designed to return None if no suitable tweet is found,
        # and does not raise exceptions based on input types or values.
    ],
)
def test_get_non_retweet(test_id: str, tweets_input: "Result", expected_output: str | None) -> None:
    # Act
    result = get_non_retweet(tweets_input)

    # Assert
    if expected_output is None:
        assert result is None, f"Test {test_id} failed: Expected None, got {result}"
    else:
        assert (  # noqa: PT018
            result is not None and result.text == expected_output
        ), f"Test {test_id} failed: Expected '{expected_output}', got '{result.text}'"  # type: ignore[union-attr]


@pytest.mark.parametrize(
    ("client", "account_to_check", "expected_result", "test_id"),
    [
        # Happy path tests
        (
            get_mock_twikit_client(),
            "valid_user",
            tweet_generator(10),
            "happy_path_valid_user",
        ),
        # Edge cases
        (
            get_mock_twikit_client(),
            "",
            [],
            "edge_case_empty_username",
        ),
        (
            get_mock_twikit_client(),
            "non_existing_user",
            Result(results=[]),
            "edge_case_non_existing_user",
        ),
    ],
)
def test_fetch_tweets(
    client: MagicMock,
    account_to_check: str,
    expected_result: list[str] | Result,
    test_id: str,
) -> None:
    # Act
    result = fetch_tweets(client, account_to_check)
    # Assert
    assert len(result) == len(expected_result), f"Test failed for {test_id}"


@pytest.mark.parametrize(
    ("previous_tweet_id", "tweet_text", "tweet_id", "expected_result", "test_id"),
    [
        # Happy path tests
        ("1234", "New tweet", "1235", "New tweet", "happy_path_new_tweet"),
        ("1234", "RT @user: Retweet", "1235", None, "happy_path_retweet"),
        ("123456", "Another new tweet", "123456", None, "happy_path_old_tweet"),
    ],
)
def test_check_new_tweets(
    previous_tweet_id: str,
    tweet_text: str,
    tweet_id: str,
    expected_result: str | None,
    test_id: str,
) -> None:
    # Arrange
    user_tweets = create_mock_tweet_result(tweet_text, tweet_id)

    # Act
    result = check_new_tweets(user_tweets, previous_tweet_id)
    # Assert
    if expected_result is None:
        assert result is None, f"Test failed for {test_id}"
    elif result is not None:
        assert result.text == expected_result, f"Test failed for {test_id}"


@patch("x2webhook.x_engine.fetch_tweets")
@patch("x2webhook.x_engine.get_non_retweet")
@patch("x2webhook.x_engine.post_tweet")
def test_get_latest_tweets(
    mock_post_tweet: Mock,
    mock_get_non_retweet: Mock,
    mock_fetch_tweets: Mock,
) -> None:
    # Arrange
    mock_twikit_client = Mock()
    mock_mongodb_client = Mock()
    users = [Mock(), Mock()]
    mock_fetch_tweets.return_value = Result([Mock(), Mock()])
    mock_get_non_retweet.return_value = Mock()

    # Act
    get_latest_tweets(users, mock_twikit_client, mock_mongodb_client)  # type: ignore[arg-type]

    # Assert
    assert mock_fetch_tweets.call_count == len(users)
    assert mock_get_non_retweet.call_count == len(users)
    assert mock_mongodb_client.update_user_previous_tweet_id.call_count == len(users)
    assert mock_post_tweet.call_count == len(users)
    # Add more assertions based on your MongoDB operations


@patch("x2webhook.x_engine.fetch_tweets")
@patch("x2webhook.x_engine.get_non_retweet")
@patch("x2webhook.x_engine.post_tweet")
def test_get_latest_tweets_no_new_tweets(
    mock_post_tweet: Mock,
    mock_get_non_retweet: Mock,
    mock_fetch_tweets: Mock,
) -> None:
    # Arrange
    mock_twikit_client = Mock()
    mock_mongodb_client = Mock()
    users = [Mock(), Mock()]
    mock_fetch_tweets.return_value = Result([Mock(), Mock()])
    mock_get_non_retweet.return_value = None

    # Act
    get_latest_tweets(users, mock_twikit_client, mock_mongodb_client)  # type: ignore[arg-type]

    # Assert
    assert mock_fetch_tweets.call_count == len(users)
    assert mock_get_non_retweet.call_count == len(users)
    assert mock_mongodb_client.update_user_previous_tweet_id.call_count == 0
    assert mock_post_tweet.call_count == 0

    # Add more assertions based on your MongoDB operations


def test_login_with_cookies() -> None:
    # Arrange
    mock_twikit_client = Mock()
    cookies = {"session": "1234"}

    # Act
    login_with_cookies(mock_twikit_client, cookies)

    # Assert
    mock_twikit_client.set_cookies.assert_called_once_with(cookies)


def test_login_with_credentials() -> None:
    # Arrange
    mock_twikit_client = Mock()
    app_settings: "Settings" = Mock()
    app_settings.x_username = "test_user"
    app_settings.x_email = "none@none.com"
    app_settings.x_password = SecretStr("test_password")

    # Act
    login_with_credentials(mock_twikit_client, app_settings)

    # Assert
    mock_twikit_client.login.assert_called_once_with(
        auth_info_1=app_settings.x_username,
        auth_info_2=app_settings.x_email,
        password=app_settings.x_password.get_secret_value(),
    )


def test_login_with_credentials_no_credentials_error() -> None:
    # Arrange
    mock_twikit_client = Mock()
    app_settings: "Settings" = Mock()
    app_settings.x_username = ""
    app_settings.x_email = ""

    # Act & Assert
    with pytest.raises(ValueError, match="X credentials are missing or incomplete."):
        login_with_credentials(mock_twikit_client, app_settings)


@patch("x2webhook.x_engine.login_with_cookies")
@patch("x2webhook.x_engine.login_with_credentials")
def test_x_login_no_cookies(mock_login_with_credentials: Mock, mock_login_with_cookies: Mock) -> None:
    # Arrange
    mock_twikit_client = Mock()
    mock_mongodb_client = Mock()
    app_settings = Mock()
    mock_mongodb_client.get_user_cookies.return_value = {}

    # Act
    x_login(app_settings, mock_twikit_client, mock_mongodb_client)

    # Assert
    mock_login_with_credentials.assert_called_once_with(mock_twikit_client, app_settings)
    mock_login_with_cookies.assert_not_called()
    mock_mongodb_client.get_user_cookies.assert_called_once()
    mock_mongodb_client.update_user_cookies.assert_called_once()


@patch("x2webhook.x_engine.login_with_cookies")
@patch("x2webhook.x_engine.login_with_credentials")
def test_x_login_with_cookies(mock_login_with_credentials: Mock, mock_login_with_cookies: Mock) -> None:
    # Arrange
    mock_twikit_client = Mock()
    mock_mongodb_client = Mock()
    app_settings = Mock()
    mock_mongodb_client.get_user_cookies.return_value = {"test": "cookies"}

    # Act
    x_login(app_settings, mock_twikit_client, mock_mongodb_client)

    # Assert
    mock_login_with_credentials.assert_not_called()
    mock_login_with_cookies.assert_called_once_with(mock_twikit_client, {"test": "cookies"})
    mock_mongodb_client.get_user_cookies.assert_called_once()
    mock_mongodb_client.update_user_cookies.assert_not_called()
