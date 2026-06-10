import asyncio
import logging
import httpx
from datetime import datetime
from threading import Event

logger = logging.getLogger(__name__)

client_ready = Event()
WHATSAPP_SERVICE_URL = "http://whatsapp-service:3001"


async def get_qr_code():
    """Obtiene QR code del servicio WhatsApp."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{WHATSAPP_SERVICE_URL}/qr")
            data = response.json()
            return data.get("qr_code")
    except Exception as e:
        logger.error(f"Error obteniendo QR: {e}")
        return None


async def _check_status():
    """Verifica estado de autenticación."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{WHATSAPP_SERVICE_URL}/status")
            data = response.json()
            if data.get("authenticated"):
                client_ready.set()
            return data.get("authenticated", False)
    except Exception:
        return False


async def initialize_whatsapp_client():
    """Inicializa cliente WhatsApp (servicio externo)."""
    logger.info("📱 Conectando con servicio WhatsApp...")

    for attempt in range(10):
        if await _check_status():
            client_ready.set()
            logger.info("✅ Servicio WhatsApp listo")
            return

        await asyncio.sleep(2)

    logger.warning("⚠️ Servicio WhatsApp no respondió (esperando escaneo de QR)")


async def send_whatsapp_message(phone_number: str, message: str, max_retries: int = 2) -> bool:
    """Envía mensaje WhatsApp."""
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{WHATSAPP_SERVICE_URL}/send",
                    json={"phone": phone_number, "message": message}
                )
                data = response.json()

                if data.get("success"):
                    logger.info(f"✅ Mensaje enviado a {phone_number}")
                    return True
                else:
                    error = data.get("error", "desconocido")
                    logger.warning(f"Error WhatsApp: {error}")
                    if "no autenticado" in error.lower():
                        return False

        except Exception as e:
            logger.warning(f"Intento {attempt + 1} fallido: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2)

    return False


async def send_appointment_confirmation(
    phone_number: str, client_name: str, service_name: str, start_time: datetime, profesional_name: str = ""
) -> bool:
    """Envía confirmación de cita por WhatsApp."""
    profesional_info = f"\n👨‍⚕️ *Profesional:* {profesional_name}" if profesional_name else ""
    message = f"""✅ *¡Tu cita está confirmada!*

Hola {client_name},

📅 *Fecha:* {start_time.strftime('%d de %B del %Y')}
⏰ *Hora:* {start_time.strftime('%H:%M')}
💈 *Servicio:* {service_name}{profesional_info}

Nos vemos pronto. Si necesitas cambiar la fecha, avísanos con anticipación.

¡Gracias por confiar en nosotros! 🙌"""
    return await send_whatsapp_message(phone_number, message)


async def send_appointment_reminder(
    phone_number: str, client_name: str, service_name: str, start_time: datetime
) -> bool:
    """Envía recordatorio de cita por WhatsApp."""
    message = f"Recordatorio: Tu cita para {service_name} es hoy a las {start_time.strftime('%H:%M')}"
    return await send_whatsapp_message(phone_number, message)


async def send_refund_pending_whatsapp(
    phone_number: str,
    profesional_name: str,
    client_name: str,
    service_name: str,
    start_time: datetime,
    deposit_amount: float,
) -> bool:
    """Envía notificación de reembolso pendiente por WhatsApp."""
    amount_str = f"${deposit_amount:,.2f}".replace(",", ".")
    message = (
        f"💸 *Reembolso pendiente*\n\n"
        f"Hola {profesional_name},\n"
        f"{client_name} canceló su turno de *{service_name}* "
        f"({start_time.strftime('%d/%m/%Y %H:%M')}).\n"
        f"Seña abonada: *{amount_str}*.\n\n"
        f"Recordá marcarlo como reembolsado en la app."
    )
    return await send_whatsapp_message(phone_number, message)


async def cleanup_whatsapp():
    """Limpia recursos."""
    client_ready.clear()
    logger.info("✅ WhatsApp cleanup completado")
