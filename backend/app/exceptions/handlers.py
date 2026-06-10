from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.exceptions.domain_exceptions import (
    AgendaPausedError,
    AppointmentAlreadyCancelledError,
    AppointmentForbiddenError,
    AppointmentNotFinishedError,
    AppointmentNotFoundError,
    BaseError,
    EmailNotVerifiedError,
    InvalidCredentialsError,
    InvalidTokenError,
    ProfesionalNotFoundError,
    ScheduleBlockForbiddenError,
    ScheduleBlockNotFoundError,
    ServiceForbiddenError,
    ServiceHasFutureAppointmentsError,
    ServiceNotFoundError,
    SlotUnavailableError,
    UserAlreadyExistsError,
    WeeklyScheduleOverlapError,
)


def _build_error_response(e: BaseError, request: Request, status_code: int):
    """Build a standardized error response.

    Args:
        e (BaseError): The exception instance.
        request (Request): The incoming request.
        status_code (int): The HTTP status code for the response.


    Returns:
        JSONResponse: A JSON response with error details.
    """

    return JSONResponse(
        status_code=status_code,
        content={
            "type": f"/errors/{e.title.lower().replace(' ', '-')}",
            "title": e.title,
            "status": status_code,
            "detail": e.details,
            "instance": request.url.path,
        },
        media_type="application/problem+json",
    )


async def user_already_exists_handler(request: Request, exc: UserAlreadyExistsError):
    """Handle UserAlreadyExistsError exceptions."""
    return _build_error_response(exc, request, status.HTTP_409_CONFLICT)


async def invalid_credentials_handler(request: Request, exc: InvalidCredentialsError):
    return _build_error_response(exc, request, status.HTTP_401_UNAUTHORIZED)


async def invalid_token_handler(request: Request, exc: InvalidTokenError):
    """Handle InvalidTokenError exceptions."""
    return _build_error_response(exc, request, status.HTTP_401_UNAUTHORIZED)


async def email_not_verified_handler(request: Request, exc: EmailNotVerifiedError):
    return _build_error_response(exc, request, status.HTTP_403_FORBIDDEN)


async def service_not_found_handler(request: Request, exc: ServiceNotFoundError):
    return _build_error_response(exc, request, status.HTTP_404_NOT_FOUND)


async def service_forbidden_handler(request: Request, exc: ServiceForbiddenError):
    return _build_error_response(exc, request, status.HTTP_403_FORBIDDEN)


async def service_has_future_appointments_handler(
    request: Request, exc: ServiceHasFutureAppointmentsError
):
    return _build_error_response(exc, request, status.HTTP_409_CONFLICT)


# ──────────── Agenda (US-14) ────────────


async def profesional_not_found_handler(
    request: Request, exc: ProfesionalNotFoundError
):
    return _build_error_response(exc, request, status.HTTP_404_NOT_FOUND)


async def schedule_block_not_found_handler(
    request: Request, exc: ScheduleBlockNotFoundError
):
    return _build_error_response(exc, request, status.HTTP_404_NOT_FOUND)


async def schedule_block_forbidden_handler(
    request: Request, exc: ScheduleBlockForbiddenError
):
    return _build_error_response(exc, request, status.HTTP_403_FORBIDDEN)


async def weekly_schedule_overlap_handler(
    request: Request, exc: WeeklyScheduleOverlapError
):
    return _build_error_response(exc, request, status.HTTP_409_CONFLICT)


# ──────────── Appointments ────────────

async def appointment_not_found_handler(request: Request, exc: AppointmentNotFoundError):
    return _build_error_response(exc, request, status.HTTP_404_NOT_FOUND)

async def appointment_already_cancelled_handler(request: Request, exc: AppointmentAlreadyCancelledError):
    return _build_error_response(exc, request, status.HTTP_400_BAD_REQUEST)

async def appointment_forbidden_handler(request: Request, exc: AppointmentForbiddenError):
    return _build_error_response(exc, request, status.HTTP_403_FORBIDDEN)

async def appointment_not_finished_handler(request: Request, exc: AppointmentNotFinishedError):
    return _build_error_response(exc, request, status.HTTP_400_BAD_REQUEST)

async def agenda_paused_handler(request: Request, exc: AgendaPausedError):
    return _build_error_response(exc, request, status.HTTP_400_BAD_REQUEST)

async def slot_unavailable_handler(request: Request, exc: SlotUnavailableError):
    return _build_error_response(exc, request, status.HTTP_400_BAD_REQUEST)


def register_exception_handlers(app: FastAPI):
    """Register exception handlers with the FastAPI app."""
    app.add_exception_handler(UserAlreadyExistsError, user_already_exists_handler)
    app.add_exception_handler(InvalidCredentialsError, invalid_credentials_handler)
    app.add_exception_handler(InvalidTokenError, invalid_token_handler)
    app.add_exception_handler(EmailNotVerifiedError, email_not_verified_handler)
    app.add_exception_handler(ServiceNotFoundError, service_not_found_handler)
    app.add_exception_handler(ServiceForbiddenError, service_forbidden_handler)
    app.add_exception_handler(
        ServiceHasFutureAppointmentsError, service_has_future_appointments_handler
    )
    app.add_exception_handler(ProfesionalNotFoundError, profesional_not_found_handler)
    app.add_exception_handler(
        ScheduleBlockNotFoundError, schedule_block_not_found_handler
    )
    app.add_exception_handler(
        ScheduleBlockForbiddenError, schedule_block_forbidden_handler
    )
    app.add_exception_handler(
        WeeklyScheduleOverlapError, weekly_schedule_overlap_handler
    )
    app.add_exception_handler(AppointmentNotFoundError, appointment_not_found_handler)
    app.add_exception_handler(AppointmentAlreadyCancelledError, appointment_already_cancelled_handler)
    app.add_exception_handler(AppointmentForbiddenError, appointment_forbidden_handler)
    app.add_exception_handler(AppointmentNotFinishedError, appointment_not_finished_handler)
    app.add_exception_handler(AgendaPausedError, agenda_paused_handler)
    app.add_exception_handler(SlotUnavailableError, slot_unavailable_handler)