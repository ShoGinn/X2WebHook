from unittest import mock

import pytest
import pytest_mock
from x2webhook.db.mongodb import MongoDBClient
from x2webhook.db.user import User

# Assuming User class has a method model_dump() that returns a dictionary
# representation of the user
# and can be initialized with keyword arguments matching the dictionary keys returned
# by model_dump()


# Mock the logger
@pytest.fixture()
def mongodb_logger(mocker: pytest_mock.MockFixture) -> mock.MagicMock:
    return mocker.patch("x2webhook.db.mongodb.logger")


@pytest.fixture()
def mock_mongo_client(monkeypatch: pytest.MonkeyPatch) -> mock.MagicMock:
    mock_client = mock.MagicMock()
    monkeypatch.setattr("pymongo.MongoClient", mock_client)
    return mock_client


@pytest.mark.parametrize(
    ("uri", "db_name", "user_data", "user_id", "cookies", "tweet_id"),
    [
        # Test ID: 1 - Happy path for adding a user
        (
            "mongodb://localhost:27017",
            "testdb",
            {
                "account_to_check": "John Doe",
                "posting_text": "Hello, World!",
                "webhook_url": "https://example.com",
            },
            "user123",
            {"user_cookies": {"session": "xyz"}},
            "tweet123",
        ),
    ],
)
def test_mongodb_client_operations(
    mock_mongo_client: mock.MagicMock,
    uri: str,
    db_name: str,
    user_data: dict,
    user_id: str,
    cookies: dict,
    tweet_id: str,
) -> None:
    # Arrange
    client = MongoDBClient(
        uri, db_name, users_collection="users", cookies_collection="cookies", mongo_client=mock_mongo_client
    )
    user = User(**user_data)

    # Act and Assert for add_user
    client.add_user(user)
    mock_mongo_client[db_name]["users_collection"].insert_one.assert_called_with(user.model_dump())

    # Act and Assert for get_users
    mock_mongo_client[db_name]["users_collection"].find.return_value = [user.model_dump()]
    users = client.get_users()
    assert len(users) == 1
    assert isinstance(users[0], User)

    # Act and Assert for get_user_cookies
    mock_mongo_client[db_name]["cookies_collection"].find_one.return_value = cookies
    retrieved_cookies = client.get_user_cookies()
    assert retrieved_cookies == cookies["user_cookies"]

    # Act and Assert for update_user_cookies
    client.update_user_cookies(cookies)
    mock_mongo_client[db_name]["cookies_collection"].update_one.assert_called_with(
        {}, {"$set": {"user_cookies": cookies}}, upsert=True
    )

    # Act and Assert for update_user_previous_tweet_id
    client.update_user_previous_tweet_id(user_id, tweet_id)
    mock_mongo_client[db_name]["users_collection"].update_one.assert_called_with(
        {"account_to_check": user_id}, {"$set": {"previous_tweet_id": tweet_id}}
    )


def test_mongodb_get_users_validation_error(mock_mongo_client: mock.MagicMock, mongodb_logger: mock.MagicMock) -> None:
    # Arrange
    client = MongoDBClient(
        "mongodb://localhost:27017",
        "testdb",
        users_collection="users",
        cookies_collection="cookies",
        mongo_client=mock_mongo_client,
    )
    mock_mongo_client["testdb"]["users_collection"].find.return_value = [{}]
    # Act
    users = client.get_users()

    # Assert
    assert users == []
    assert mongodb_logger.error.called, "Expected an error to be logged"
