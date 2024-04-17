"""The user module for working with X users."""

from typing import TYPE_CHECKING, Any

from loguru import logger
from pydantic import BaseModel, Field, HttpUrl, field_serializer
from pydantic_core import Url

if TYPE_CHECKING:
    from x2webhook.db.mongodb import MongoDBClient


class User(BaseModel):
    """Represents a user with X account information and webhook details.

    Attributes:
        account_to_check (str): The X account to check.
        posting_text (str): The text to post.
        webhook_url (HttpUrl): The URL of the webhook.
        webhook_name (str, optional): The name of the webhook.
        webhook_avatar_url (HttpUrl, optional): The avatar URL of the webhook.
        previous_tweet_id (str, optional): The ID of the previous tweet.
    """

    account_to_check: str = Field(..., description="The X account to check.")
    posting_text: str = Field(..., description="The text to post.")
    webhook_url: HttpUrl = Field(..., description="The URL of the webhook.")
    webhook_name: str | None = Field(default=None, description="The name of the webhook.")
    webhook_avatar_url: HttpUrl | None = Field(default=None, description="The avatar URL of the webhook.")
    previous_tweet_id: str | None = Field(default=None, description="The ID of the previous tweet.")

    @field_serializer("*")
    def url2str(self, val: Any | str) -> str:  # noqa: ANN401
        """Convert the given value to a string representation.

        If the value is an instance of the `Url` class, it is converted to a string.
        Otherwise, the value is returned as is.

        Parameters:
            val: The value to be converted.

        Returns:
            str: The string representation of the value.
        """
        return str(val) if isinstance(val, Url) else val


def create_default_users(mongodb_client: "MongoDBClient") -> list[User]:
    """Create and adds two default users to the database.

    Returns:
        list: A list of User objects representing the default users.
    """
    # Define two default users
    user1 = User(
        account_to_check="ThePSF",
        posting_text="Check out this super wholesome tweet - <tweet_link>",
        webhook_avatar_url=HttpUrl("https://i.imgur.com/tyRc1sC.png"),  # pyright: ignore[reportCallIssue]
        webhook_name="Wholesome Memes",
        webhook_url=HttpUrl("https://discord.com/api/webhooks/123/abc"),  # pyright: ignore[reportCallIssue]
    )
    user2 = User(
        account_to_check="X",
        posting_text="Doctor, a new tweet has arrived! <tweet_link>",
        webhook_url=HttpUrl("https://discord.com/api/webhooks/123/abc"),  # pyright: ignore[reportCallIssue]
    )
    # Add the default users to the database
    mongodb_client.add_user(user1)
    mongodb_client.add_user(user2)
    # Load the users again
    modified_users = mongodb_client.get_users()
    if not modified_users:
        logger.error("Failed to create default users.")
        return []
    return modified_users


def load_users_from_db(mongodb_client: "MongoDBClient") -> list[User]:
    """Load the users from the MongoDB.

    Returns:
        list: The contents of the users collection in the MongoDB database.
    """
    users = mongodb_client.get_users()
    if not users:
        logger.error("No users found in the database, creating default users...")
        users = create_default_users(mongodb_client)
    return users
