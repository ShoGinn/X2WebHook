import time

from loguru import logger
from twikit.client import Client

from x2webhook.db.mongodb import MongoDBClient
from x2webhook.db.user import load_users_from_db
from x2webhook.settings import Settings
from x2webhook.x_engine import get_latest_tweets, x_login


class App:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.twikit_client, self.mongodb_client = self._init_clients()
        self.error_count = 0
        self.max_errors = 5

    def _init_clients(self) -> tuple[Client, MongoDBClient]:
        """Initialize the twikit and MongoDB clients."""
        mongodb_client = MongoDBClient(
            uri=self.settings.mongodb_uri,
            db_name=self.settings.mongodb_db_name,
            users_collection=self.settings.mongodb_users_collection,
            cookies_collection=self.settings.mongodb_cookies_collection,
        )
        twikit_client = Client(self.settings.x_client_language)
        return twikit_client, mongodb_client

    def maximum_error_handler(self, e: Exception) -> bool:
        """Handle errors during the execution of the main loop."""
        self.error_count += 1
        logger.error(f"Error: {e}. Retrying...")
        if self.error_count >= self.max_errors:
            logger.error(f"Maximum number of errors ({self.max_errors}) reached. Stopping...")
            return True
        return False

    def main_loop(
        self,
        num_iterations: int | None = None,
    ) -> None:
        """Loop that continuously retrieves latest tweets."""
        iterations = 0
        logger.info(f"Watching for new tweets" f" every {self.settings.timer_interval!s} seconds.")
        while True:
            try:
                loaded_x_users = load_users_from_db(mongodb_client=self.mongodb_client)
                get_latest_tweets(
                    users=loaded_x_users,
                    twikit_client=self.twikit_client,
                    mongodb_client=self.mongodb_client,
                )
                time.sleep(self.settings.timer_interval)
            except Exception as e:
                if self.maximum_error_handler(e):
                    break
            iterations += 1
            if num_iterations is not None and iterations >= num_iterations:
                break

    def run(self) -> None:
        if x_login(
            app_settings=self.settings,
            twikit_client=self.twikit_client,
            mongodb_client=self.mongodb_client,
        ):
            self.main_loop()
