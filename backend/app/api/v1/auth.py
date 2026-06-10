from fastapi import APIRouter, Depends, Query, Response, status

from app.api.deps import get_auth_service
from app.schemas.auth_schema import (
    AuthResponse,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    UserInAuthResponse,
)
from app.services.auth_service import AuthService

router = APIRouter()


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a new client or profesional and sends a verification email.",
    responses={
        status.HTTP_201_CREATED: {"description": "User registered — verification email sent"},
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid data"},
        status.HTTP_409_CONFLICT: {"description": "User already exists"},
    },
)
def register(data: RegisterRequest, service: AuthService = Depends(get_auth_service)):
    user = service.register(data)
    return RegisterResponse(
        message=f"Te enviamos un email de confirmación a {user.email}. "
                "Revisalo para activar tu cuenta."
    )


@router.get(
    "/verify-email",
    status_code=status.HTTP_200_OK,
    summary="Verify email address",
    description="Activates a user account using the token sent by email.",
    responses={
        status.HTTP_200_OK: {"description": "Email verified successfully"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Invalid or expired token"},
    },
)
def verify_email(
    token: str = Query(..., description="Verification token from the email link"),
    service: AuthService = Depends(get_auth_service),
):
    service.verify_email(token)
    return {"message": "Tu cuenta fue activada. Ya podés iniciar sesión."}


@router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK,
    summary="Request password reset",
    description="Sends a password reset email if the account exists.",
    responses={
        status.HTTP_200_OK: {"description": "Reset email sent if account exists"},
    },
)
def forgot_password(data: ForgotPasswordRequest, service: AuthService = Depends(get_auth_service)):
    service.forgot_password(data)
    return {"message": "Si existe una cuenta con ese email, te enviamos un enlace para restablecer tu contraseña."}


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Reset password",
    description="Sets a new password using the token from the reset email.",
    responses={
        status.HTTP_200_OK: {"description": "Password reset successfully"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Invalid or expired token"},
    },
)
def reset_password(data: ResetPasswordRequest, service: AuthService = Depends(get_auth_service)):
    service.reset_password(data)
    return {"message": "Tu contraseña fue actualizada. Ya podés iniciar sesión."}


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Login",
    description="Authenticates a user and returns tokens.",
    responses={
        status.HTTP_200_OK: {"description": "Login successful"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Invalid credentials"},
        status.HTTP_403_FORBIDDEN: {"description": "Email not verified"},
    },
)
def login(data: LoginRequest, service: AuthService = Depends(get_auth_service)):
    user, access, refresh = service.login(data)
    return AuthResponse(
        access_token=access,
        refresh_token=refresh,
        user=UserInAuthResponse.model_validate(user),
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Logout user",
    description="Revokes a refresh token for a specific device.",
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "User logged out successfully"},
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid or expired refresh token"
        },
    },
)
def logout(
    data: LogoutRequest, service: AuthService = Depends(get_auth_service)
) -> Response:
    service.logout(data)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh tokens",
    description="Exchanges a valid refresh token for a new access and refresh token pair.",
    responses={
        status.HTTP_200_OK: {"description": "Tokens refreshed successfully"},
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid or expired refresh token"
        },
    },
)
def refresh(data: RefreshRequest, service: AuthService = Depends(get_auth_service)):
    access_token, new_refresh = service.refresh(data)
    return RefreshResponse(
        access_token=access_token,
        refresh_token=new_refresh,
    )
