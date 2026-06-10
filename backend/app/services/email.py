from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.core.config import settings


config = ConnectionConfig(
    MAIL_FROM=settings.smtp_from,
    MAIL_PORT=settings.smtp_port,
    MAIL_SERVER=settings.smtp_host,
    MAIL_STARTTLS=True,
    MAIL_USERNAME=settings.smtp_user,
    MAIL_PASSWORD=settings.smtp_password,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
) if settings.smtp_host else None


async def send_appointment_confirmation(
    recipient_email: str,
    client_name: str,
    service_name: str,
    start_time: str,
    profesional_name: str,
) -> bool:
    if not config:
        print("SMTP no configurado. Configurar SMTP_HOST, SMTP_USER y SMTP_PASSWORD en .env")
        return False

    message = MessageSchema(
        subject="Confirmacion de tu reserva",
        recipients=[recipient_email],
        body=f"""
        <html>
            <body>
                <h2>Reserva confirmada!</h2>
                <p>Hola {client_name},</p>
                <p>Tu reserva ha sido confirmada exitosamente.</p>
                <hr>
                <p><strong>Detalles de tu cita:</strong></p>
                <ul>
                    <li><strong>Servicio:</strong> {service_name}</li>
                    <li><strong>Profesional:</strong> {profesional_name}</li>
                    <li><strong>Fecha y hora:</strong> {start_time}</li>
                </ul>
                <hr>
                <p>Si necesitas cancelar o reprogramar, comunicate con nosotros.</p>
                <p>Hasta pronto!</p>
            </body>
        </html>
        """,
        subtype="html",
    )

    try:
        fm = FastMail(config)
        await fm.send_message(message)
        return True
    except Exception as e:
        print(f"Error enviando email: {e}")
        return False
