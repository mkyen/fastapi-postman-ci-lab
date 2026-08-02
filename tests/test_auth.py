def test_login_success(client, registered_user):
    """Başarılı giriş senaryosu."""

    response = client.post(
        "/auth/login",
        json=registered_user,
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client, registered_user):
    """Yanlış şifre ile giriş denemesi."""

    response = client.post(
        "/auth/login",
        json={
            "email": registered_user["email"],
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_protected_endpoint_without_token(client):
    """Token olmadan korunan endpoint'e erişim."""

    response = client.get("/tasks")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_protected_endpoint_invalid_token(client):
    """Bozuk token ile erişim."""

    invalid_headers = {
        "Authorization": "Bearer invalid.jwt.token"
    }

    response = client.get(
        "/tasks",
        headers=invalid_headers,
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"