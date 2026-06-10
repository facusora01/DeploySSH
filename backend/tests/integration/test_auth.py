from fastapi import status


class TestAuthRegistration:
    def test_register_client_success(self, client):
        payload = {
            "role": "client",
            "full_name": "Juan Perez",
            "email": "client@test.com",
            "phone": "123456789",
            "password": "password123",
        }

        response = client.post("/api/v1/auth/register", json=payload)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "message" in data
        assert "client@test.com" in data["message"]

    def test_register_profesional_success(self, client):
        payload = {
            "role": "profesional",
            "full_name": "Dra. Gomez",
            "email": "profesional@test.com",
            "phone": "987654321",
            "password": "password123",
            "specialty": "Cardiología",
        }

        response = client.post("/api/v1/auth/register", json=payload)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "message" in data
        assert "profesional@test.com" in data["message"]

    def test_register_profesional_missing_specialty(self, client):
        payload = {
            "role": "profesional",
            "full_name": "Dr. House",
            "email": "house@test.com",
            "phone": "123123123",
            "password": "password123",
        }

        response = client.post("/api/v1/auth/register", json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_invalid_role(self, client):
        payload = {
            "role": "admin",
            "full_name": "Admin User",
            "email": "admin@test.com",
            "phone": "111111111",
            "password": "password123",
        }

        response = client.post("/api/v1/auth/register", json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_existing_user(self, client):
        payload = {
            "role": "client",
            "full_name": "Original User",
            "email": "existente@test.com",
            "phone": "12345678",
            "password": "password123",
        }

        client.post("/api/v1/auth/register", json=payload)
        response = client.post("/api/v1/auth/register", json=payload)

        assert response.status_code == status.HTTP_409_CONFLICT


class TestAuthLogin:
    def test_login_client_success(self, register_and_verify, client):
        register_and_verify({
            "role": "client",
            "full_name": "Juan Perez",
            "email": "login_client@test.com",
            "phone": "123456789",
            "password": "password123",
        })

        response = client.post(
            "/api/v1/auth/login",
            json={"email": "login_client@test.com", "password": "password123"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "login_client@test.com"
        assert data["user"]["role"] == "client"

    def test_login_profesional_success(self, register_and_verify, client):
        register_and_verify({
            "role": "profesional",
            "full_name": "Dra. Gomez",
            "email": "login_pro@test.com",
            "phone": "987654321",
            "password": "password123",
            "specialty": "Cardiología",
        })

        response = client.post(
            "/api/v1/auth/login",
            json={"email": "login_pro@test.com", "password": "password123"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user"]["role"] == "profesional"

    def test_login_unverified_email(self, client):
        client.post(
            "/api/v1/auth/register",
            json={
                "role": "client",
                "full_name": "Sin Verificar",
                "email": "unverified@test.com",
                "phone": "123456789",
                "password": "password123",
            },
        )

        response = client.post(
            "/api/v1/auth/login",
            json={"email": "unverified@test.com", "password": "password123"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_login_wrong_password_unhappy_path(self, register_and_verify, client):
        register_and_verify({
            "role": "client",
            "full_name": "Juan Perez",
            "email": "wrong_pass@test.com",
            "phone": "123456789",
            "password": "password123",
        })

        response = client.post(
            "/api/v1/auth/login",
            json={"email": "wrong_pass@test.com", "password": "password_incorrecta"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_user_not_found_unhappy_path(self, client):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "noexiste@test.com", "password": "password123"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_missing_fields_unhappy_path(self, client):
        response = client.post(
            "/api/v1/auth/login", json={"email": "noexiste@test.com"}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestAuthLogout:
    def test_logout_success(self, register_and_verify, client):
        register_and_verify({
            "role": "client",
            "full_name": "Juan Perez",
            "email": "logout@test.com",
            "phone": "123456789",
            "password": "password123",
        })
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "logout@test.com", "password": "password123"},
        )
        refresh_token = login_response.json()["refresh_token"]

        response = client.post(
            "/api/v1/auth/logout", json={"refresh_token": refresh_token}
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_logout_invalid_token_unhappy_path(self, client):
        response = client.post(
            "/api/v1/auth/logout", json={"refresh_token": "token_invalido"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_already_revoked_token_unhappy_path(self, register_and_verify, client):
        register_and_verify({
            "role": "client",
            "full_name": "Juan Perez",
            "email": "logout_twice@test.com",
            "phone": "123456789",
            "password": "password123",
        })
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "logout_twice@test.com", "password": "password123"},
        )
        refresh_token = login_response.json()["refresh_token"]

        client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
        response = client.post(
            "/api/v1/auth/logout", json={"refresh_token": refresh_token}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAuthRefresh:
    def test_refresh_success(self, register_and_verify, client):
        register_and_verify({
            "role": "client",
            "full_name": "Juan Perez",
            "email": "refresh@test.com",
            "phone": "123456789",
            "password": "password123",
        })
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "refresh@test.com", "password": "password123"},
        )
        old_refresh = login_response.json()["refresh_token"]

        response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": old_refresh}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["refresh_token"] != old_refresh

    def test_refresh_old_token_revoked_after_rotation(self, register_and_verify, client):
        register_and_verify({
            "role": "client",
            "full_name": "Juan Perez",
            "email": "refresh_revoke@test.com",
            "phone": "123456789",
            "password": "password123",
        })
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "refresh_revoke@test.com", "password": "password123"},
        )
        old_refresh = login_response.json()["refresh_token"]

        client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})

        response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": old_refresh}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_invalid_token_unhappy_path(self, client):
        response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "token_invalido"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_missing_token_unhappy_path(self, client):
        response = client.post("/api/v1/auth/refresh", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
