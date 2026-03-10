import pytest


def test_list_users_success(client, auth_headers, faker):
    # Setup: Register another user manually to test list content
    another_user_data = {
        "email": faker.email(),
        "username": faker.user_name(),
        "password": "password123",
    }
    client.post("/auth/register", json=another_user_data)

    response = client.get("/users/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    assert any(u["email"] == another_user_data["email"] for u in data)


def test_list_users_unauthorized(client):
    response = client.get("/users/")
    assert response.status_code == 401


def test_list_users_invalid_token(client):
    response = client.get("/users/", headers={"Authorization": "Bearer invalid-token"})
    assert response.status_code == 401


def test_list_users_wrong_token_type(client, user_data):
    from app.auth import create_token

    token = create_token(data={"sub": user_data["email"]}, token_type="refresh")
    response = client.get("/users/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_list_users_not_found(client):
    from app.auth import create_token

    non_existent_user_email = "ghost@example.com"
    token = create_token(data={"sub": non_existent_user_email})
    response = client.get("/users/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
