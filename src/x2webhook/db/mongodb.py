"""This module contains the functions to interact with the MongoDB database."""

from loguru import logger
from pydantic import ValidationError
from pymongo import MongoClient

from x2webhook.db.user import User


class MongoDBClient:
    """A class representing a MongoDB client.

    Args:
        uri (str): The URI of the MongoDB server.
        db_name (str): The name of the database to connect to.

    Attributes:
        client: The MongoClient instance.
        db: The database instance.

    Methods:
        get_users: Retrieves all users from the database.
        add_user: Adds a new user to the database.
        update_user: Updates an existing user in the database.
        delete_user: Deletes a user from the database.
    """

    def __init__(
        self,
        uri: str,
        db_name: str,
        users_collection: str,
        cookies_collection: str,
        mongo_client: MongoClient | None = None,
    ):
        """Initialize a MongoDB object.

        Args:
            uri (str): The URI of the MongoDB server.
            db_name (str): The name of the database to connect to.
        """
        self.client = mongo_client or MongoClient(uri)
        self.db = self.client[db_name]
        self.users_collection = self.db[users_collection]
        self.cookies_collection = self.db[cookies_collection]

    def get_users(self) -> list[User]:
        """Retrieve all users from the database.

        Returns:
            A cursor object containing all the users.
        """
        try:
            users_data = self.users_collection.find()
            user_object = [User(**user_data) for user_data in users_data]
        except ValidationError as e:
            logger.error(f"Error: {e}. Please check your user data.")
            return []
        return user_object

    def add_user(self, user: User) -> None:
        """Add a user to the database.

        Parameters:
        - user: The user to add to the database.

        Returns:
        - None
        """
        self.users_collection.insert_one(user.model_dump())

    def get_user_cookies(self) -> dict | None:
        """Retrieve the cookies for a user from the database.

        Returns:
            str: The cookies of the user.
        """
        cookies = self.cookies_collection.find_one()
        return cookies.get("user_cookies") if cookies else None

    def update_user_cookies(self, cookies: dict) -> None:
        """Update the cookies for a user in the database.

        Args:
            cookies (dict): The cookies of the user.

        Returns:
            None
        """
        self.cookies_collection.update_one({}, {"$set": {"user_cookies": cookies}}, upsert=True)

    def update_user_previous_tweet_id(self, user_id: str, tweet_id: str) -> None:
        """Update the previous tweet ID for a user in the database.

        Args:
            user_id (str): The ID of the user.
            tweet_id (str): The ID of the previous tweet.

        Returns:
            None
        """
        self.users_collection.update_one({"account_to_check": user_id}, {"$set": {"previous_tweet_id": tweet_id}})
