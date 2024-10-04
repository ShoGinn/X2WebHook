# Archived

This has been archived due to lack of interest and the twikit being updated past what i'm willing to change this code to.

# X2WebHook - X to Webhook

A simple script that will check on a list of user's last tweets and send them to the specified webhook as simple text if there's a new one, on a configurable timer.

Big thanks to the [Twikit API wrapper](https://github.com/d60/twikit) for making this possible!

## Installation

``poetry install``

1. Rename the ".env_example" file to remove the "_example".
   1. You will need to fill in the values for the X settings and the MongoDB connection string.
2. Run the script with ``poetry run x2webhook``

## Configuration for the MongoDB Database

The script uses MongoDB to store the last tweet ID of each user, so it can check if there's a new tweet since the last check.
When you first run the program it propogates the database with some default users and currently you have to manually add the users you want to check on.

### Required arguments for Database

``account_to_check`` - The x username (not ID) of the person you want to check the tweets of

``posting_text`` - The text that should be sent to the webhook. The variable ``<tweet_link>`` will be replaced with the tweet's URL.

``webhook_url`` - The URL that they webhook data should be sent to

### Optional arguments for Database

``webhook_avatar_url`` - a URL pointing to the image the webhook should use as it's profile picture

``webhook_name`` - a name the webhook should use when posting

### Program Specific

``previous_tweet_id`` - The ID of the last tweet that was sent to the webhook. This is used to check if there's a new tweet since the last check.
