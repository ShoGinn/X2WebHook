"""Webhook functions for posting tweets to a Discord webhook."""

from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from loguru import logger

from x2webhook.addons.requests import post
from x2webhook.db.user import User


def create_payload(user: User, tweet_link: str) -> dict[str, str]:
    """Create a payload for posting a tweet to a webhook.

    Args:
        user (User): The X user information.
        tweet_link (str): The link to the tweet to include in the payload.

    Returns:
        dict: A payload dictionary for posting the tweet to a webhook.
    """
    content_text = user.posting_text.replace("<tweet_link>", tweet_link)
    payload = {
        "content": content_text,
    }
    if user.webhook_avatar_url is not None:
        payload["avatar_url"] = str(user.webhook_avatar_url)
    if user.webhook_name is not None:
        payload["username"] = user.webhook_name

    return payload


def create_webhook_wait_url(webhook_url: str, *, add_wait: bool) -> str:
    """Create a webhook URL with the wait parameter set to true.

    Args:
        webhook_url (str): The base webhook URL.

    Returns:
        str: The webhook URL with the wait parameter set to true.
    """
    url_parts = urlparse(webhook_url)
    query = parse_qs(url_parts.query)
    if add_wait:
        query.update({"wait": ["true"]})
    else:
        query.pop("wait", None)
    url_parts = url_parts._replace(query=urlencode(query, doseq=True))
    return urlunparse(url_parts)


def post_tweet(user: User, payload: dict[str, str], *, wait_for_response: bool = True) -> None:
    """Post a tweet payload to the specified webhook URL.

    Args:
        user (User): The X user information.
        payload (dict): The payload to post to the webhook URL.

    Returns:
        None
    """
    webhook_wait_url = create_webhook_wait_url(str(user.webhook_url), add_wait=wait_for_response)

    req, errors = post(
        webhook_wait_url,
        json=payload,
    )
    if errors:
        logger.error(f"Failed to post tweet for {user.account_to_check}")
        logger.error(f"Errors: {errors}")
        return
    if req is not None:
        logger.info(f"Posted tweet for {user.account_to_check} successfully")
