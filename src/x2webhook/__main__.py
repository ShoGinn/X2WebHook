"""Posts new tweets from a list of X accounts to a Discord webhook."""

import importlib.metadata
import time

from loguru import logger
from twikit import Client  # type: ignore[import-untyped]

from x2webhook import __package_name__
from x2webhook.db.mongodb import MongoDBClient
from x2webhook.db.user import load_users_from_db
from x2webhook.logging.logging import setup_logger
from x2webhook.settings import Settings, get_config
from x2webhook.x_engine import get_latest_tweets, x_login


def initialize_clients(settings: Settings) -> tuple[Client, MongoDBClient]:
    """Initialize the twikit and MongoDB clients."""
    mongodb_client = MongoDBClient(
        uri=settings.mongodb_uri,
        db_name=settings.mongodb_db_name,
        users_collection=settings.mongodb_users_collection,
        cookies_collection=settings.mongodb_cookies_collection,
    )
    twikit_client = Client(settings.x_client_language)
    return twikit_client, mongodb_client


def handle_errors(error_count: int, max_errors: int, e: Exception) -> int:
    """Handle errors during the execution of the main loop."""
    error_count += 1
    logger.error(f"Error: {e}. Retrying...")
    if error_count >= max_errors:
        logger.error(f"Maximum number of errors ({max_errors}) reached. Stopping...")
    return error_count


def get_version() -> str:
    """Return the version of the program."""
    try:
        version = importlib.metadata.version(__package__ or __name__)
    except Exception:
        version = "Unknown"
    return version


def main_loop(
    settings: Settings,
    twikit_client: Client,
    mongodb_client: MongoDBClient,
    num_iterations: int | None = None,
) -> None:
    """Loop that continuously retrieves latest tweets."""
    error_count = 0
    max_errors = 5
    iterations = 0
    logger.info(f"Watching for new tweets" f" every {settings.timer_interval!s} seconds.")
    while True:
        try:
            loaded_x_users = load_users_from_db(mongodb_client=mongodb_client)
            get_latest_tweets(
                users=loaded_x_users,
                twikit_client=twikit_client,
                mongodb_client=mongodb_client,
            )
            time.sleep(settings.timer_interval)
        except Exception as e:
            error_count = handle_errors(error_count, max_errors, e)
            if error_count >= max_errors:
                break
        iterations += 1
        if num_iterations is not None and iterations >= num_iterations:
            break


def main() -> None:
    """Serve as main entry for the x2webhook application.

    Loads user data, performs X login, and
    continuously retrieves latest tweets.

    Raises:
        ValidationError: If there is an error with the user data.
    """
    settings = get_config()
    setup_logger()
    logger.info(f"Starting {__package_name__} version {get_version()}")
    twikit_client, mongodb_client = initialize_clients(settings)

    if x_login(
        app_settings=settings,
        twikit_client=twikit_client,
        mongodb_client=mongodb_client,
    ):
        main_loop(settings, twikit_client, mongodb_client)


if __name__ == "__main__":
    main()
