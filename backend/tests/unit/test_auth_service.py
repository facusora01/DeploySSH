from unittest.mock import MagicMock, patch

import pytest

from app.exceptions.domain_exceptions import UserAlreadyExistsError
from app.models.user import User
from app.schemas.auth_schema import LogoutRequest, RegisterRequest
from app.services.auth_service import AuthService


@pytest.fixture
def mock_uow():
    uow = MagicMock()
    uow.user_repo.get_by_email.return_value = None
    return uow


@pytest.fixture
def auth_service(mock_uow):
    return AuthService(uow=mock_uow)


@pytest.fixture
def mock_uow_with_user():
    uow = MagicMock()
    mock_user = User(
        id=1, email="test@test.com", role="client", password_hash="hashed_pass",
        is_email_verified=True,
    )
    uow.user_repo.get_by_email.return_value = mock_user
    return uow


@pytest.fixture
def auth_service_with_user(mock_uow_with_user):
    return AuthService(uow=mock_uow_with_user)


@patch("app.services.auth_service.get_password_hash")
@patch("app.services.auth_service.create_access_token")
@patch("app.services.auth_service.create_refresh_token")
def test_register_client_happy_path(
    mock_refresh, mock_access, mock_hash, auth_service, mock_uow
):
    mock_hash.return_value = "hashed_pass"
    mock_access.return_value = "mocked_access_token"
    mock_refresh.return_value = ("mocked_refresh_token", "mocked_refresh_hash")

    mock_user = User(id=1, email="test@test.com", role="client")
    mock_uow.user_repo.create_user.return_value = mock_user

    data = RegisterRequest(
        role="client",
        full_name="Juan Perez",
        email="test@test.com",
        phone="12345678",
        password="password123",
    )

    user = auth_service.register(data)

    assert user.id == 1
    mock_uow.client_repo.create_client.assert_called_once_with(user_id=1)
    mock_uow.profesional_repo.create_profesional.assert_not_called()
    mock_uow.commit.assert_called_once()


@patch("app.services.auth_service.get_password_hash")
@patch("app.services.auth_service.create_access_token")
@patch("app.services.auth_service.create_refresh_token")
def test_register_profesional_happy_path(
    mock_refresh, mock_access, mock_hash, auth_service, mock_uow
):
    mock_hash.return_value = "hashed_pass"
    mock_access.return_value = "mocked_access_token"
    mock_refresh.return_value = ("mocked_refresh_token", "mocked_refresh_hash")

    mock_user = User(id=2, email="pro@test.com", role="profesional")
    mock_uow.user_repo.create_user.return_value = mock_user

    data = RegisterRequest(
        role="profesional",
        full_name="Dra. Ana Gomez",
        email="pro@test.com",
        phone="12345678",
        password="password123",
        specialty="Pediatría",
    )

    user = auth_service.register(data)

    mock_uow.profesional_repo.create_profesional.assert_called_once_with(
        user_id=2, specialty="Pediatría"
    )
    mock_uow.client_repo.create_client.assert_not_called()
    mock_uow.commit.assert_called_once()


def test_register_user_already_exists_unhappy_path(auth_service, mock_uow):
    mock_uow.user_repo.get_by_email.return_value = User(id=99, email="existe@test.com")

    data = RegisterRequest(
        role="client",
        full_name="Juan Perez",
        email="existe@test.com",
        phone="12345678",
        password="password123",
    )

    with pytest.raises(UserAlreadyExistsError):
        auth_service.register(data)

    mock_uow.user_repo.create_user.assert_not_called()
    mock_uow.commit.assert_not_called()


class TestAuthServiceLogin:
    @patch("app.services.auth_service.verify_password")
    @patch("app.services.auth_service.create_access_token")
    @patch("app.services.auth_service.create_refresh_token")
    def test_login_client_happy_path(
        self,
        mock_refresh,
        mock_access,
        mock_verify,
        auth_service_with_user,
        mock_uow_with_user,
    ):
        mock_verify.return_value = True
        mock_access.return_value = "mocked_access_token"
        mock_refresh.return_value = ("mocked_refresh_token", "mocked_refresh_hash")

        from app.schemas.auth_schema import LoginRequest

        data = LoginRequest(email="test@test.com", password="password123")

        user, access, refresh = auth_service_with_user.login(data)

        assert user.id == 1
        assert access == "mocked_access_token"
        assert refresh == "mocked_refresh_token"
        mock_uow_with_user.token_repo.create.assert_called_once_with(
            1, "mocked_refresh_hash", "client"
        )
        mock_uow_with_user.commit.assert_called_once()

    @patch("app.services.auth_service.verify_password")
    @patch("app.services.auth_service.create_access_token")
    @patch("app.services.auth_service.create_refresh_token")
    def test_login_profesional_happy_path(
        self, mock_refresh, mock_access, mock_verify, mock_uow_with_user
    ):
        mock_uow_with_user.user_repo.get_by_email.return_value = User(
            id=2, email="pro@test.com", role="profesional", password_hash="hashed_pass",
            is_email_verified=True,
        )
        service = AuthService(uow=mock_uow_with_user)
        mock_verify.return_value = True
        mock_access.return_value = "mocked_access_token"
        mock_refresh.return_value = ("mocked_refresh_token", "mocked_refresh_hash")

        from app.schemas.auth_schema import LoginRequest

        data = LoginRequest(email="pro@test.com", password="password123")

        user, access, refresh = service.login(data)

        assert user.role == "profesional"
        mock_uow_with_user.token_repo.create.assert_called_once_with(
            2, "mocked_refresh_hash", "profesional"
        )
        mock_uow_with_user.commit.assert_called_once()

    @patch("app.services.auth_service.verify_password")
    def test_login_wrong_password_unhappy_path(
        self, mock_verify, auth_service_with_user, mock_uow_with_user
    ):
        from app.exceptions.domain_exceptions import InvalidCredentialsError
        from app.schemas.auth_schema import LoginRequest

        mock_verify.return_value = False

        data = LoginRequest(email="test@test.com", password="wrong_password")

        with pytest.raises(InvalidCredentialsError):
            auth_service_with_user.login(data)

        mock_uow_with_user.commit.assert_not_called()

    def test_login_user_not_found_unhappy_path(self, auth_service, mock_uow):
        from app.exceptions.domain_exceptions import InvalidCredentialsError
        from app.schemas.auth_schema import LoginRequest

        data = LoginRequest(email="noexiste@test.com", password="password123")

        with pytest.raises(InvalidCredentialsError):
            auth_service.login(data)

        mock_uow.commit.assert_not_called()


class TestAuthServiceLogout:
    @patch("app.services.auth_service.encode_refresh_token")
    def test_logout_happy_path(self, mock_encode, auth_service, mock_uow):
        mock_encode.return_value = "hashed_token"
        mock_token = MagicMock()
        mock_uow.token_repo.get_active_refresh_token.return_value = mock_token

        auth_service.logout(LogoutRequest(refresh_token="valid_refresh_token"))

        mock_uow.token_repo.revoke.assert_called_once_with(mock_token)
        mock_uow.commit.assert_called_once()

    @patch("app.services.auth_service.encode_refresh_token")
    def test_logout_invalid_token_unhappy_path(
        self, mock_encode, auth_service, mock_uow
    ):
        from app.exceptions.domain_exceptions import InvalidTokenError

        mock_encode.return_value = "hashed_token"
        mock_uow.token_repo.get_active_refresh_token.return_value = None

        with pytest.raises(InvalidTokenError):
            auth_service.logout(LogoutRequest(refresh_token="invalid_refresh_token"))

        mock_uow.token_repo.revoke.assert_not_called()
        mock_uow.commit.assert_not_called()

    @patch("app.services.auth_service.encode_refresh_token")
    def test_logout_expired_token_unhappy_path(
        self, mock_encode, auth_service, mock_uow
    ):
        from app.exceptions.domain_exceptions import InvalidTokenError

        mock_encode.return_value = "hashed_token"
        mock_uow.token_repo.get_active_refresh_token.return_value = None

        with pytest.raises(InvalidTokenError):
            auth_service.logout(LogoutRequest(refresh_token="expired_refresh_token"))

        mock_uow.commit.assert_not_called()


class TestAuthServiceRefresh:
    @patch("app.services.auth_service.encode_refresh_token")
    @patch("app.services.auth_service.create_access_token")
    @patch("app.services.auth_service.create_refresh_token")
    def test_refresh_happy_path(
        self, mock_refresh, mock_access, mock_encode, auth_service, mock_uow
    ):
        from app.schemas.auth_schema import RefreshRequest

        mock_encode.return_value = "hashed_old_token"
        mock_access.return_value = "new_access_token"
        mock_refresh.return_value = ("new_refresh_token", "new_refresh_hash")

        mock_token = MagicMock()
        mock_token.user_id = 1
        mock_token.role = "client"
        mock_uow.token_repo.get_active_refresh_token.return_value = mock_token

        access, refresh = auth_service.refresh(
            RefreshRequest(refresh_token="old_refresh_token")
        )

        assert access == "new_access_token"
        assert refresh == "new_refresh_token"
        mock_uow.token_repo.revoke.assert_called_once_with(mock_token)
        mock_uow.token_repo.create.assert_called_once_with(
            1, "new_refresh_hash", "client"
        )
        mock_uow.commit.assert_called_once()

    @patch("app.services.auth_service.encode_refresh_token")
    def test_refresh_invalid_token_unhappy_path(
        self, mock_encode, auth_service, mock_uow
    ):
        from app.exceptions.domain_exceptions import InvalidTokenError
        from app.schemas.auth_schema import RefreshRequest

        mock_encode.return_value = "hashed_token"
        mock_uow.token_repo.get_active_refresh_token.return_value = None

        with pytest.raises(InvalidTokenError):
            auth_service.refresh(RefreshRequest(refresh_token="invalid_token"))

        mock_uow.token_repo.revoke.assert_not_called()
        mock_uow.token_repo.create.assert_not_called()
        mock_uow.commit.assert_not_called()

    @patch("app.services.auth_service.encode_refresh_token")
    def test_refresh_expired_token_unhappy_path(
        self, mock_encode, auth_service, mock_uow
    ):
        from app.exceptions.domain_exceptions import InvalidTokenError
        from app.schemas.auth_schema import RefreshRequest

        mock_encode.return_value = "hashed_token"
        mock_uow.token_repo.get_active_refresh_token.return_value = None

        with pytest.raises(InvalidTokenError):
            auth_service.refresh(RefreshRequest(refresh_token="expired_token"))

        mock_uow.commit.assert_not_called()
