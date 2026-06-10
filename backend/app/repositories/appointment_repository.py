import uuid
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.appointment import Appointment, AppointmentStatus

class AppointmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def count_future_appointments(self, service_id: uuid.UUID) -> int:
        return (
            self.db.query(Appointment)
            .filter(
                Appointment.service_id == service_id,
                Appointment.start_time > datetime.now(),
                Appointment.status != AppointmentStatus.CANCELLED
            )
            .count()
        )

    def get_occupancy_by_service(
        self, service_id: uuid.UUID, start_range: datetime, end_range: datetime
    ) -> list[tuple[datetime, int]]:
        """Devuelve una lista de tuplas (start_time, cantidad_de_turnos)"""
        return (
            self.db.query(Appointment.start_time, func.count(Appointment.id))
            .filter(
                Appointment.service_id == service_id,
                Appointment.start_time >= start_range,
                Appointment.start_time <= end_range,
                Appointment.status != AppointmentStatus.CANCELLED
            )
            .group_by(Appointment.start_time)
            .all()
        )

    def get_by_id(self, appointment_id: uuid.UUID) -> Appointment | None:
        return self.db.get(Appointment, appointment_id)

    def create(self, **fields) -> Appointment:
        appointment = Appointment(**fields)
        self.db.add(appointment)
        return appointment

    def list_by_client(self, client_id: int) -> list[Appointment]:
        return (
            self.db.query(Appointment)
            .filter(Appointment.client_id == client_id)
            .order_by(Appointment.start_time.asc())
            .all()
        )

    def list_by_service_ids(self, service_ids: list[uuid.UUID]) -> list[Appointment]:
        return (
            self.db.query(Appointment)
            .filter(Appointment.service_id.in_(service_ids))
            .order_by(Appointment.start_time.asc())
            .all()
        )

    def count_occupancy(self, service_id: uuid.UUID, start_time: datetime) -> int:
        return (
            self.db.query(Appointment)
            .filter(
                Appointment.service_id == service_id,
                Appointment.start_time == start_time,
                Appointment.status != AppointmentStatus.CANCELLED
            )
            .count()
        )
