import pytest
from faker import Faker


@pytest.fixture(scope="session")
def faker():
    return Faker()


@pytest.fixture
def user_data(faker):
    return {
        "email": faker.email(),
        "username": faker.user_name(),
        "password": "password123",
    }


@pytest.fixture(autouse=True)
def mock_email(mocker):
    return mocker.patch("app.email.send_verification_email")


@pytest.fixture
def auth_headers(client, user_data):
    # Register and login to get headers
    client.post("/auth/register", json=user_data)
    response = client.post(
        "/auth/login",
        json={"email": user_data["email"], "password": user_data["password"]},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
