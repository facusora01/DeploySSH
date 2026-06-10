import uuid

from sqlalchemy.orm import Session

from app.models.service import Service


class ServiceRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        profesional_id: int,
        name: str,
        duration_minutes: int,
        price: float | None = None,
        description: str | None = None,
        max_slots: int = 1,
        deposit_active: bool = False,
        deposit_amount: float | None = None,
        deposit_required: bool = False,
    ) -> Service:
        service = Service(
            profesional_id=profesional_id,
            name=name,
            duration_minutes=duration_minutes,
            price=price,
            description=description,
            max_slots=max_slots,
            deposit_active=deposit_active,
            deposit_amount=deposit_amount,
            deposit_required=deposit_required,
        )
        self.db.add(service)
        return service

    def get_by_id(self, servicio_id: uuid.UUID) -> Service | None:
        return self.db.get(Service, servicio_id)

    def get_by_profesional(
        self, profesional_id: int, include_inactive: bool = False
    ) -> list[Service]:
        query = self.db.query(Service).filter(
            Service.profesional_id == profesional_id
        )
        if not include_inactive:
            query = query.filter(Service.is_active == True)
        return query.all()

    def update(self, servicio: Service, **fields) -> Service:
        for key, value in fields.items():
            if hasattr(servicio, key):
                setattr(servicio, key, value)
        return servicio

    def get_by_professional(
        self, profesional_id: int, include_inactive: bool = False
    ) -> list[Service]:
        return self.get_by_profesional(profesional_id, include_inactive)

    def soft_delete(self, servicio: Service) -> Service:
        servicio.is_active = False
        return servicio

    def get_all_active(self) -> list[Service]:
        return self.db.query(Service).filter(Service.is_active == True).all()