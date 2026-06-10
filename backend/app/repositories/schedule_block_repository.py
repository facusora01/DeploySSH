import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.models.schedule_block import ScheduleBlock


class ScheduleBlockRepository:
    """Repositorio de bloqueos de fechas (vacaciones, feriados)."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        profesional_id: int,
        start_date: date,
        end_date: date,
        reason: str | None = None,
    ) -> ScheduleBlock:
        block = ScheduleBlock(
            profesional_id=profesional_id,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
        )
        self.db.add(block)
        return block

    def get_by_id(self, block_id: uuid.UUID) -> ScheduleBlock | None:
        return self.db.get(ScheduleBlock, block_id)

    def get_by_profesional(self, profesional_id: int) -> list[ScheduleBlock]:
        """Todos los bloqueos del profesional, ordenados por fecha de inicio."""
        return (
            self.db.query(ScheduleBlock)
            .filter(ScheduleBlock.profesional_id == profesional_id)
            .order_by(ScheduleBlock.start_date)
            .all()
        )

    def get_blocks_in_range(
        self,
        profesional_id: int,
        range_start: date,
        range_end: date,
    ) -> list[ScheduleBlock]:
        """Bloqueos que intersectan con el rango [range_start, range_end].

        Útil para el cálculo de disponibilidad: filtra a nivel DB lo que
        realmente afecta al rango pedido y evita traer toda la historia.

        La condición de intersección de intervalos es:
            block_start <= range_end  AND  block_end >= range_start
        """
        return (
            self.db.query(ScheduleBlock)
            .filter(
                ScheduleBlock.profesional_id == profesional_id,
                ScheduleBlock.start_date <= range_end,
                ScheduleBlock.end_date >= range_start,
            )
            .all()
        )

    def delete(self, block: ScheduleBlock) -> None:
        self.db.delete(block)