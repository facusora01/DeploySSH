class BaseError(Exception):
    """Base exception class for domain errors.

    Args:
        title (str): The title of the error.
        details (str): Detailed description of the error.
    """

    def __init__(self, title: str, details: str):
        self.title = title
        self.details = details
        super().__init__(f"{title}: {details}")


class UserAlreadyExistsError(BaseError):
    """Exception raised when trying to register with an existing email.

    Args:
        email (str): The email that already exists.
    """

    def __init__(self, email: str):
        super().__init__(
            "User already exists", f"A user with email {email} already exists."
        )


class InvalidCredentialsError(BaseError):
    def __init__(self):
        super().__init__("Invalid credentials", "Email or password is incorrect.")


class InvalidTokenError(BaseError):
    """Exception raised when a token is invalid or expired.

    Args:
        reason (str): The reason why the token is invalid.
    """

    def __init__(self, reason: str = "The token is invalid or expired"):
        super().__init__("Invalid token", reason)


class EmailNotVerifiedError(BaseError):
    def __init__(self):
        super().__init__(
            "Email not verified",
            "Debés confirmar tu correo electrónico antes de iniciar sesión.",
        )


class ServiceNotFoundError(BaseError):
    def __init__(self, service_id: str):
        super().__init__(
            "Service not found",
            f"No service found with id {service_id}.",
        )


class ServiceForbiddenError(BaseError):
    def __init__(self):
        super().__init__(
            "Forbidden",
            "You do not have permission to modify this service.",
        )


class ServiceHasFutureAppointmentsError(BaseError):
    def __init__(self):
        super().__init__(
            "Service has future appointments",
            "Cannot delete a service with future appointments. "
            "Cancel or resolve them first.",
        )


# ──────────── Agenda (US-14) ────────────


class ProfesionalNotFoundError(BaseError):
    def __init__(self, profesional_id: int):
        super().__init__(
            "Profesional not found",
            f"No profesional found with id {profesional_id}.",
        )


class ScheduleBlockNotFoundError(BaseError):
    def __init__(self, block_id: str):
        super().__init__(
            "Schedule block not found",
            f"No schedule block found with id {block_id}.",
        )


class ScheduleBlockForbiddenError(BaseError):
    def __init__(self):
        super().__init__(
            "Forbidden",
            "You do not have permission to modify this schedule block.",
        )


class WeeklyScheduleOverlapError(BaseError):
    """Dos o más franjas horarias del mismo día se superponen."""

    _DAY_NAMES = [
        "lunes",
        "martes",
        "miércoles",
        "jueves",
        "viernes",
        "sábado",
        "domingo",
    ]

    def __init__(self, day_of_week: int):
        day = self._DAY_NAMES[day_of_week]
        super().__init__(
            "Schedule overlap",
            f"Hay franjas horarias superpuestas el {day}. Revisá la configuración.",
        )



class AppointmentNotFoundError(BaseError):
    def __init__(self, appointment_id: str):
        super().__init__(
            "Turno no encontrado",
            f"No se encontró un turno con el ID {appointment_id}.",
        )


class AppointmentAlreadyCancelledError(BaseError):
    def __init__(self):
        super().__init__(
            "Turno ya cancelado",
            "El turno ya se encuentra cancelado.",
        )


class AppointmentForbiddenError(BaseError):
    def __init__(self):
        super().__init__(
            "Permiso denegado",
            "No tenés permiso para realizar esta acción sobre el turno.",
        )


class AppointmentNotFinishedError(BaseError):
    def __init__(self):
        super().__init__(
            "Turno futuro",
            "No se puede marcar la asistencia de un turno de un día futuro.",
        )


class AgendaPausedError(BaseError):
    def __init__(self):
        super().__init__(
            "Agenda pausada",
            "La agenda de este profesional está pausada.",
        )


class SlotUnavailableError(BaseError):
    def __init__(self):
        super().__init__(
            "Horario no disponible",
            "El horario seleccionado ya está completo.",
        )