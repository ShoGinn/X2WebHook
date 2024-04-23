"""X-related functions for fetching and posting tweets."""

from loguru import logger
from twikit import Client  # type: ignore[import-untyped]
from twikit.tweet import Tweet  # type: ignore[import-untyped]
from twikit.utils import Result  # type: ignore[import-untyped]

from x2webhook.db.mongodb import MongoDBClient
from x2webhook.db.user import User
from x2webhook.settings import Settings
from x2webhook.webhook import create_payload, post_tweet


def get_non_retweet(tweets: Result[Tweet]) -> Tweet | None:
    """Get the first non-retweet tweet from a list of tweets.

    Args:
        tweets (list): A list of tweet objects.

    Returns:
        object: The first non-retweet tweet object,
                or None if no non-retweet tweet is found.
    """
    return next((tweet for tweet in tweets if not tweet.text.startswith("RT @")), None)


def fetch_tweets(twikit_client: Client, account_to_check: str) -> Result[Tweet]:
    """Fetch tweets for a specified X account.

    Args:
        account_to_check (str): The X account screen name to fetch tweets for.

    Returns:
        list: A list of up to 20 tweets for the specified X account.
    """
    user = twikit_client.get_user_by_screen_name(account_to_check)
    return user.get_tweets("Tweets", 20)


def check_new_tweets(user_tweets: Result[Tweet], previous_tweet_id: str | None) -> Tweet | None:
    """Check for new tweets since the last checked tweet.

    Args:
        user_tweets (list): List of user's tweets to check for new tweets.
        previous_tweet_id (str): ID of the previously checked tweet.

    Returns:
        Tweet or None: The latest tweet if it's new, otherwise None.
    """
    last_tweet = get_non_retweet(user_tweets)
    if last_tweet is None or previous_tweet_id == last_tweet.id:
        return None
    return last_tweet


def get_latest_tweets(users: list[User], twikit_client: Client, mongodb_client: MongoDBClient) -> None:
    """Retrieve and processes the latest tweets for a list of X users.

    Args:
        users (list): List of User objects representing X users to check.

    Returns:
        None
    """
    for user in users:
        user_tweets = fetch_tweets(twikit_client=twikit_client, account_to_check=user.account_to_check)
        last_tweet = check_new_tweets(user_tweets, user.previous_tweet_id)
        if last_tweet is None:
            logger.debug("No new tweets found, moving on...")
            continue
        tweet_link = f"https://x.com/{user.account_to_check}/status/{last_tweet.id}"
        payload = create_payload(user, tweet_link)
        post_tweet(user, payload)
        mongodb_client.update_user_previous_tweet_id(user.account_to_check, last_tweet.id)


def validate_user(twikit_client: Client) -> bool:
    """Validate the user's credentials by fetching the user's profile.

    Args:
        twikit_client (Client): The Twikit client instance.

    Returns:
        bool: True if the user's credentials are valid, False otherwise.
    """
    try:
        twikit_client.user()
        return True
    except Exception as e:
        logger.error(f"Error validating user: {e}")
        return False


def login_with_cookies(twikit_client: Client, cookies: dict) -> None:
    """Login to X using the provided cookies."""
    logger.info("Using stored cookies for login.")
    twikit_client.set_cookies(cookies)
    if not validate_user(twikit_client):
        raise ValueError("Invalid cookies provided. Please login again.")


def login_with_credentials(twikit_client: Client, mongodb_client: MongoDBClient, app_settings: Settings) -> bool:
    """Login to X using the provided credentials."""
    # Check to make sure the authentication information is provided
    if not app_settings.x_username or not app_settings.x_email or not app_settings.x_password.get_secret_value():
        raise ValueError("X credentials are missing or incomplete.")
    logger.info("Logging in to X...")
    twikit_client.http.client.cookies.clear()  # TODO: Remove this once the twikit library is updated
    try:
        twikit_client.login(
            auth_info_1=app_settings.x_username,
            auth_info_2=app_settings.x_email,
            password=app_settings.x_password.get_secret_value(),
        )
        logger.info("Successfully logged in to X.")
        store_cookies(mongodb_client, twikit_client)
        return True
    except Exception as e:
        logger.error(f"Error logging in to X: {e}")
        logger.error("Please check your X credentials and run the program again.")
        return False


def store_cookies(mongodb_client: MongoDBClient, twikit_client: Client) -> None:
    """Store the cookies in the database for future use."""
    cookies = twikit_client.get_cookies()
    mongodb_client.update_user_cookies(cookies)
    logger.info("Cookies saved for future use.")


def x_login(app_settings: Settings, twikit_client: Client, mongodb_client: MongoDBClient) -> bool:
    """Login to X using the provided credentials or cookies."""
    if stored_cookies := mongodb_client.get_user_cookies():
        try:
            login_with_cookies(twikit_client, stored_cookies)
            return True
        except ValueError as e:
            logger.error(f"Error logging in with stored cookies: {e}")
    return login_with_credentials(twikit_client, mongodb_client, app_settings)
