
def test_register_valid_user(client):
    response = client.post(
        "/user/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPassword123"
        }
    )

    assert response.status_code == 200


def test_register_invalid_email(client):
    response = client.post(
        "/user/register",
        json={
            "username": "testuser",
            "email": "invalid-email",
            "password": "TestPassword123"
        }
    )

    assert response.status_code == 422


def test_login_wrong_password(client):
    response = client.post(
        "/user/login",
        data={
            "username": "test@example.com",
            "password": "WrongPassword123"
        }
    )

    assert response.status_code == 200
    assert response.json()["message"] == "User not found" or \
           response.json()["message"] == "Invalid password"
