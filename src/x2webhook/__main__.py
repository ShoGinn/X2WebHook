"""Posts new tweets from a list of X accounts to a Discord webhook."""

from loguru import logger

from x2webhook import __package_name__, __version__
from x2webhook.core import App
from x2webhook.logging.logging import setup_logger
from x2webhook.settings import get_config


def main() -> None:
    """Serve as main entry for the x2webhook application.

    Loads user data, performs X login, and
    continuously retrieves latest tweets.

    Raises:
        ValidationError: If there is an error with the user data.
    """
    settings = get_config()
    setup_logger()
    logger.info(f"Starting {__package_name__} version {__version__}")
    app = App(settings=settings)
    app.run()


if __name__ == "__main__":
    main()
