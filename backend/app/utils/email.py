import httpx
from datetime import datetime
from app.core.config import settings

SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"


def _send(to_email: str, subject: str, text: str, html: str) -> None:
    if not settings.sendgrid_api_key:
        print(f"[EMAIL] {subject} → {to_email}")
        return

    httpx.post(
        SENDGRID_API_URL,
        headers={
            "Authorization": f"Bearer {settings.sendgrid_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "personalizations": [{"to": [{"email": to_email}]}],
            "from": {"email": settings.smtp_from},
            "subject": subject,
            "content": [
                {"type": "text/plain", "value": text},
                {"type": "text/html", "value": html},
            ],
        },
        timeout=10,
    )

def send_verification_email(to_email: str, full_name: str, token: str) -> None:
    url = f"{settings.frontend_url}/verify-email?token={token}"
    text = (
        f"Hola {full_name},\n\n"
        f"Hacé clic en el siguiente enlace para confirmar tu cuenta:\n{url}\n\n"
        f"Este enlace expira en {settings.email_verification_expire_hours} horas."
    )
    html = (
        f"<html><body>"
        f"<p>Hola <strong>{full_name}</strong>,</p>"
        f"<p>Hacé clic en el siguiente enlace para confirmar tu cuenta:</p>"
        f'<p><a href="{url}">Confirmar mi cuenta</a></p>'
        f"<p>Este enlace expira en {settings.email_verification_expire_hours} horas.</p>"
        f"</body></html>"
    )
    _send(to_email, "Confirmá tu cuenta en Appointa", text, html)


def send_local_invitation_email(to_email: str, local_name: str, token: str) -> None:
    url = f"{settings.frontend_url}/invitacion?token={token}"
    text = (
        f"Hola,\n\n"
        f"{local_name} te invitó a sumarte a su equipo en Appointa.\n"
        f"Hacé clic en el siguiente enlace para aceptar la invitación:\n{url}\n\n"
        f"Si todavía no tenés una cuenta, el enlace te va a llevar a crear una.\n"
        f"Este enlace expira en {settings.invitation_expire_hours} horas."
    )
    html = (
        f"<html><body>"
        f"<p>Hola,</p>"
        f"<p><strong>{local_name}</strong> te invitó a sumarte a su equipo en Appointa.</p>"
        f'<p><a href="{url}">Aceptar invitación</a></p>'
        f"<p>Si todavía no tenés una cuenta, el enlace te va a llevar a crear una.</p>"
        f"<p>Este enlace expira en {settings.invitation_expire_hours} horas.</p>"
        f"</body></html>"
    )
    _send(to_email, f"{local_name} te invitó a su equipo en Appointa", text, html)


def send_reset_password_email(to_email: str, full_name: str, token: str) -> None:
    url = f"{settings.frontend_url}/reset-password?token={token}"
    text = (
        f"Hola {full_name},\n\n"
        f"Recibimos una solicitud para restablecer tu contraseña.\n"
        f"Hacé clic en el siguiente enlace:\n{url}\n\n"
        f"Este enlace expira en 1 hora. Si no solicitaste esto, ignorá este mensaje."
    )
    html = (
        f"<html><body>"
        f"<p>Hola <strong>{full_name}</strong>,</p>"
        f"<p>Recibimos una solicitud para restablecer tu contraseña.</p>"
        f'<p><a href="{url}">Restablecer contraseña</a></p>'
        f"<p>Este enlace expira en 1 hora. Si no solicitaste esto, ignorá este mensaje.</p>"
        f"</body></html>"
    )
    _send(to_email, "Restablecé tu contraseña en Appointa", text, html)


def send_appointment_cancellation_email(
    to_email: str,
    full_name: str,
    service_name: str,
    start_time: datetime,
    profesional_name: str,
) -> None:
    formatted_date = start_time.strftime("%d/%m/%Y a las %H:%M")
    text = (
        f"Hola {full_name},\n\n"
        f"Te confirmamos que tu turno para '{service_name}' con {profesional_name} "
        f"el día {formatted_date} ha sido cancelado correctamente.\n\n"
        f"¡Esperamos verte pronto!"
    )
    html = (
        f"<html><body>"
        f"<p>Hola <strong>{full_name}</strong>,</p>"
        f"<p>Tu turno para <strong>{service_name}</strong> con <strong>{profesional_name}</strong> "
        f"el día <strong>{formatted_date}</strong> fue cancelado.</p>"
        f"<p>¡Esperamos verte pronto!</p>"
        f"</body></html>"
    )
    _send(to_email, f"Cancelación de turno: {service_name}", text, html)


def send_refund_pending_email(
    to_email: str,
    full_name: str,
    client_name: str,
    service_name: str,
    start_time: datetime,
    deposit_amount: float,
) -> None:
    formatted_date = start_time.strftime("%d/%m/%Y a las %H:%M")
    amount_str = f"${deposit_amount:,.2f}".replace(",", ".")
    text = (
        f"Hola {full_name},\n\n"
        f"El cliente {client_name} canceló su turno para '{service_name}' "
        f"del {formatted_date}.\n"
        f"La seña abonada fue de {amount_str}.\n\n"
        f"Por favor, realizá el reembolso y marcalo como completado en la app."
    )
    html = (
        f"<html><body>"
        f"<p>Hola <strong>{full_name}</strong>,</p>"
        f"<p><strong>{client_name}</strong> canceló su turno para "
        f"<strong>{service_name}</strong> del <strong>{formatted_date}</strong>.</p>"
        f"<p>Seña abonada: <strong>{amount_str}</strong>.</p>"
        f"<p>Por favor, realizá el reembolso y marcalo como completado en la app.</p>"
        f"</body></html>"
    )
    _send(to_email, f"Seña a reembolsar: {client_name} - {service_name}", text, html)