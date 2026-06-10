from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.appointment import Appointment, AppointmentStatus
from app.core.config import settings


class AppointmentScheduler:
    _instance = None
    scheduler = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppointmentScheduler, cls).__new__(cls)
            cls._instance.scheduler = BackgroundScheduler()
        return cls._instance

    def start(self):
        print(f"[SCHEDULER] start() called, running={self.scheduler.running}")
        if not self.scheduler.running:
            self.scheduler.start()
            print("✅ Appointment reminder scheduler iniciado")
        else:
            print("[SCHEDULER] Already running, skipping start")

    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown()
            print("⏹️ Appointment reminder scheduler detenido")

    def add_reminder_job(self):
        """Agrega un job que verifica cada minuto si hay citas proximas para recordar"""
        print("[SCHEDULER] add_reminder_job() called")
        self.scheduler.add_job(
            check_and_send_reminders,
            trigger=IntervalTrigger(minutes=1),
            id="appointment_reminders",
            name="Check appointment reminders",
            replace_existing=True,
        )
        print("✅ Job de recordatorios agregado")


def check_and_send_reminders():
    """
    Verifica citas que comienzan en ~1 hora y envia recordatorios por WhatsApp.
    Se ejecuta cada minuto.
    """
    print(f"[SCHEDULER] check_and_send_reminders ejecutado")
    try:
        from app.services.whatsapp import send_appointment_reminder

        # Crear sesion directa a la BD
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        now = datetime.utcnow()
        # Buscar citas que comienzan entre 58-62 minutos desde ahora
        one_hour_later = now + timedelta(minutes=60)
        fifty_eight_min_later = now + timedelta(minutes=58)

        print(f"[SCHEDULER] Checking: now={now}, window=[{fifty_eight_min_later} to {one_hour_later}]")

        appointments = db.query(Appointment).filter(
            Appointment.start_time >= fifty_eight_min_later,
            Appointment.start_time <= one_hour_later,
            Appointment.status == AppointmentStatus.CONFIRMED,
        ).all()

        print(f"[SCHEDULER] Found {len(appointments)} appointments in window")

        from app.models.notification import Notification, NotificationType
        from app.services.notification_service import notify_reminder

        def reminder_exists(user_id, appointment_id):
            return (
                db.query(Notification)
                .filter(
                    Notification.user_id == user_id,
                    Notification.appointment_id == appointment_id,
                    Notification.type == NotificationType.REMINDER,
                )
                .first()
                is not None
            )

        for appointment in appointments:
            client = appointment.client
            service = appointment.service
            if not service:
                continue

            # Notificación in-app de recordatorio (cliente y profesional), con dedup
            if client and client.user and not reminder_exists(client.user_id, appointment.id):
                notify_reminder(db, client.user_id, appointment, for_client=True)

            profesional = service.profesional
            if profesional and not reminder_exists(profesional.user_id, appointment.id):
                notify_reminder(db, profesional.user_id, appointment, for_client=False)

            db.commit()

            # Enviar recordatorio por WhatsApp (requiere teléfono del cliente)
            if client and client.user and client.user.phone:
                asyncio.run(
                    send_appointment_reminder(
                        phone_number=client.user.phone,
                        client_name=client.user.full_name,
                        service_name=service.name,
                        start_time=appointment.start_time,
                    )
                )

        db.close()
    except Exception as e:
        print(f"ERROR en check_and_send_reminders: {e}")
