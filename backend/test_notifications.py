"""
Script para testear funciones de email y WhatsApp
Requiere credenciales SMTP en .env y numero de telefono valido
"""
import asyncio
import sys
from datetime import datetime, timedelta

# Testeo 1: Verificar imports
print("[TEST 1] Verificando imports...")
try:
    from app.services.email import send_appointment_confirmation
    print("[OK] Email service importada")
except Exception as e:
    print(f"[ERROR] Error importando email service: {e}")
    sys.exit(1)

try:
    from app.services.whatsapp import send_whatsapp_reminder
    print("[OK] WhatsApp service importada")
except Exception as e:
    print(f"[ERROR] Error importando WhatsApp service: {e}")
    sys.exit(1)

try:
    from app.services.scheduler import AppointmentScheduler
    print("[OK] Scheduler importado")
except Exception as e:
    print(f"[ERROR] Error importando scheduler: {e}")
    sys.exit(1)

# Testeo 2: Verificar config SMTP
print("\n[TEST 2] Verificando config SMTP...")
try:
    from app.core.config import settings
    if settings.smtp_host and settings.smtp_user and settings.smtp_password:
        print(f"[OK] SMTP configurado: {settings.smtp_host}:{settings.smtp_port}")
    else:
        print("[WARN] SMTP no completamente configurado")
        print(f"   - smtp_host: {settings.smtp_host or '(vacio)'}")
        print(f"   - smtp_user: {settings.smtp_user or '(vacio)'}")
        print(f"   - smtp_password: {settings.smtp_password or '(vacio)'}")
except Exception as e:
    print(f"[ERROR] Error verificando config: {e}")

# Testeo 3: Test email async
print("\n[TEST 3] Test email (async)...")
async def test_email():
    try:
        result = await send_appointment_confirmation(
            recipient_email="test@example.com",
            client_name="Test User",
            service_name="Test Service",
            start_time="21/05/2026 14:00",
            profesional_name="Test Profesional",
        )
        if result:
            print("[OK] Email enviado correctamente")
        else:
            print("[WARN] Email retorno False (probablemente falta config SMTP)")
    except Exception as e:
        print(f"[ERROR] Error enviando email: {e}")

try:
    asyncio.run(test_email())
except Exception as e:
    print(f"[ERROR] Error en test email: {e}")

# Testeo 4: Test WhatsApp async
print("\n[TEST 4] Test WhatsApp (async)...")
async def test_whatsapp():
    try:
        result = await send_whatsapp_reminder(
            phone_number="5491234567890",
            client_name="Test User",
            service_name="Test Service",
            start_time=datetime.now() + timedelta(minutes=16),
        )
        if result:
            print("[OK] WhatsApp programado correctamente")
        else:
            print("[WARN] WhatsApp retorno False")
    except Exception as e:
        print(f"[WARN] Error en WhatsApp (normal si no hay navegador): {e}")

try:
    asyncio.run(test_whatsapp())
except Exception as e:
    print(f"[WARN] Error en test WhatsApp: {e}")

# Testeo 5: Scheduler
print("\n[TEST 5] Verificando Scheduler...")
try:
    scheduler = AppointmentScheduler()
    if scheduler.scheduler:
        print("[OK] Scheduler instancia creada")
        print(f"   - Running: {scheduler.scheduler.running}")
        print("   - (No iniciado en test)")
    else:
        print("[ERROR] Error creando scheduler")
except Exception as e:
    print(f"[ERROR] Error en scheduler: {e}")

print("\n" + "="*60)
print("IMPORTANTE:")
print("="*60)
print("Para que email funcione, agrega a .env:")
print("  SMTP_HOST=smtp.gmail.com")
print("  SMTP_PORT=587")
print("  SMTP_USER=tu_email@gmail.com")
print("  SMTP_PASSWORD=tu_app_password")
print("\nPara WhatsApp: abri https://web.whatsapp.com/ primero")
print("para que pywhatkit pueda enviar.")
