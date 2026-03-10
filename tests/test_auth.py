import pytest
from app.auth import create_token
from datetime import timedelta


def test_register_user_success(client, user_data, mock_email):
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 201
    assert (
        response.json()["message"]
        == "Registration successful. Please verify your email."
    )
    assert mock_email.called
    assert mock_email.call_args[0][0] == user_data["email"]


def test_register_user_duplicate(client, user_data):
    client.post("/auth/register", json=user_data)
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_register_invalid_email(client, user_data):
    user_data["email"] = "not-an-email"
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 422


def test_register_weak_password(client, user_data):
    user_data["password"] = "short"
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 400
    assert "password" in response.json()["detail"].lower()


def test_register_short_username(client, user_data):
    user_data["username"] = "ab"
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 422


def test_register_long_username(client, user_data):
    user_data["username"] = "a" * 51
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 422


def test_register_long_email(client, user_data):
    user_data["email"] = "a" * 92 + "@test.com"
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 422


def test_login_success(client, user_data):
    client.post("/auth/register", json=user_data)
    response = client.post(
        "/auth/login",
        json={"email": user_data["email"], "password": user_data["password"]},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()
    assert "token_type" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_invalid_credentials(client):
    invalid_credentials_email = "wrong@example.com"
    response = client.post(
        "/auth/login", json={"email": invalid_credentials_email, "password": "pass"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_create_token_with_delta():
    token = create_token(data={"sub": "test"}, expires_delta=timedelta(minutes=5))
    assert token is not None


def test_verify_email_success(client, user_data, mocker):
    # Setup: Register user
    client.post("/auth/register", json=user_data)

    # Generate a verification token manually for testing
    verify_token = create_token(
        data={"sub": user_data["email"]}, token_type="verification"
    )

    # Action: Verify email
    response = client.post("/auth/verify-email", json={"token": verify_token})

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == "Email verified successfully"

    # Check DB status - list users should now show is_verified=True
    login_resp = client.post(
        "/auth/login",
        json={"email": user_data["email"], "password": user_data["password"]},
    )
    token = login_resp.json()["access_token"]
    users_resp = client.get("/users/", headers={"Authorization": f"Bearer {token}"})
    assert users_resp.json()[0]["is_verified"] is True


def test_verify_email_invalid_token(client):
    response = client.post("/auth/verify-email", json={"token": "invalid-token"})
    assert response.status_code == 400
    assert "Invalid or expired" in response.json()["detail"]


def test_verify_email_wrong_token_type(client, user_data):
    # Use an access token instead of a verification token
    token = create_token(data={"sub": user_data["email"]}, token_type="access")
    response = client.post("/auth/verify-email", json={"token": token})
    assert response.status_code == 400


def test_verify_email_user_not_found(client, user_data):
    # Token for a user not in DB
    non_existent_user_email = "ghost@example.com"
    token = create_token(
        data={"sub": non_existent_user_email}, token_type="verification"
    )
    response = client.post("/auth/verify-email", json={"token": token})
    assert response.status_code == 400
    assert response.json()["detail"] == "User not found"
