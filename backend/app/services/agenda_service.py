"""Servicio de configuración de agenda del profesional (US-14).

Responsabilidades:
- CRUD del schedule semanal recurrente (con validación de solapes)
- CRUD de bloqueos de fechas
- Update parcial de settings (buffer entre turnos, pausa global)
- Lectura consolidada de todo el config

No incluye el cálculo de slots disponibles — eso es responsabilidad del
AvailabilityService, que se apoya en los datos que guarda este servicio.
"""
import uuid
from datetime import date, time

from app.core.interfaces.unit_of_work import IUnitOfWork
from app.exceptions.domain_exceptions import (
    ProfesionalNotFoundError,
    ScheduleBlockForbiddenError,
    ScheduleBlockNotFoundError,
    WeeklyScheduleOverlapError,
)
from app.models.profesional import Profesional
from app.models.schedule_block import ScheduleBlock
from app.models.weekly_schedule import WeeklySchedule
from app.schemas.agenda import (
    AgendaConfigResponse,
    WeeklyScheduleSlotIn,
)


class AgendaService:
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    # ──────────── Lectura ────────────

    def get_agenda_config(self, profesional_id: int) -> AgendaConfigResponse:
        """Snapshot completo del config: settings + schedule + blocks."""
        with self.uow:
            profesional = self._get_profesional(profesional_id)
            schedule = self.uow.weekly_schedule_repo.get_by_profesional(
                profesional_id
            )
            blocks = self.uow.schedule_block_repo.get_by_profesional(
                profesional_id
            )
            # La construcción del response sucede DENTRO del with: ahí Pydantic
            # accede a los atributos de los objetos ORM y los serializa. Una
            # vez salimos del with la sesión se cierra, pero la respuesta ya
            # es 100% datos planos.
            return AgendaConfigResponse(
                buffer_minutes=profesional.buffer_minutes,
                agenda_paused=profesional.agenda_paused,
                weekly_schedule=schedule,
                schedule_blocks=blocks,
            )

    # ──────────── Schedule semanal ────────────

    def replace_weekly_schedule(
        self,
        profesional_id: int,
        slots: list[WeeklyScheduleSlotIn],
    ) -> list[WeeklySchedule]:
        """Reemplaza el schedule semanal entero del profesional.

        Antes de tocar la DB valida que no haya solapes entre franjas del
        mismo día. Si las hay, levanta WeeklyScheduleOverlapError y la DB
        queda intacta.
        """
        # Validamos ANTES de abrir la transacción: si está mal, evitamos
        # un delete inútil. Es lógica pura, no requiere sesión.
        self._validate_no_overlaps(slots)

        with self.uow:
            self.uow.weekly_schedule_repo.delete_for_profesional(profesional_id)
            created: list[WeeklySchedule] = []
            for slot in slots:
                new_slot = self.uow.weekly_schedule_repo.create(
                    profesional_id=profesional_id,
                    day_of_week=slot.day_of_week,
                    start_time=slot.start_time,
                    end_time=slot.end_time,
                )
                created.append(new_slot)
            self.uow.commit()
            return created

    # ──────────── Bloqueos ────────────

    def create_block(
        self,
        profesional_id: int,
        start_date: date,
        end_date: date,
        reason: str | None = None,
    ) -> ScheduleBlock:
        """Crea un bloqueo nuevo. Pydantic ya validó date_order y longitud."""
        with self.uow:
            block = self.uow.schedule_block_repo.create(
                profesional_id=profesional_id,
                start_date=start_date,
                end_date=end_date,
                reason=reason,
            )
            self.uow.commit()
            return block

    def delete_block(
        self, block_id: uuid.UUID, profesional_id: int
    ) -> None:
        """Elimina un bloqueo. Falla si no existe o no es del profesional."""
        with self.uow:
            block = self._get_own_block(block_id, profesional_id)
            self.uow.schedule_block_repo.delete(block)
            self.uow.commit()

    # ──────────── Settings ────────────

    def update_settings(
        self,
        profesional_id: int,
        buffer_minutes: int | None = None,
        agenda_paused: bool | None = None,
    ) -> Profesional:
        """PATCH parcial. Solo aplica los campos que vinieron explícitos.

        Pasar None es 'no tocar este campo'. Para distinguir 'no tocar' de
        'poner en 0/False' confiamos en que Pydantic ya hizo el unset/None
        en el schema.
        """
        with self.uow:
            profesional = self._get_profesional(profesional_id)
            if buffer_minutes is not None:
                profesional.buffer_minutes = buffer_minutes
            if agenda_paused is not None:
                profesional.agenda_paused = agenda_paused
            self.uow.commit()
            return profesional

    # ──────────── Helpers ────────────

    def _get_profesional(self, profesional_id: int) -> Profesional:
        profesional = self.uow.profesional_repo.get_by_id(profesional_id)
        if not profesional:
            raise ProfesionalNotFoundError(profesional_id)
        return profesional

    def _get_own_block(
        self, block_id: uuid.UUID, profesional_id: int
    ) -> ScheduleBlock:
        block = self.uow.schedule_block_repo.get_by_id(block_id)
        if not block:
            raise ScheduleBlockNotFoundError(str(block_id))
        if block.profesional_id != profesional_id:
            raise ScheduleBlockForbiddenError()
        return block

    @staticmethod
    def _validate_no_overlaps(slots: list[WeeklyScheduleSlotIn]) -> None:
        """Verifica que no haya dos franjas del mismo día que se pisen.

        Algoritmo: agrupar por día, ordenar por start_time dentro de cada
        día, y chequear que el start del siguiente sea >= end del anterior.
        Las franjas contiguas (end == next_start) NO son overlap, son OK.
        """
        by_day: dict[int, list[tuple[time, time]]] = {}
        for slot in slots:
            by_day.setdefault(slot.day_of_week, []).append(
                (slot.start_time, slot.end_time)
            )

        for day, ranges in by_day.items():
            ranges_sorted = sorted(ranges)
            for i in range(len(ranges_sorted) - 1):
                _, cur_end = ranges_sorted[i]
                next_start, _ = ranges_sorted[i + 1]
                if next_start < cur_end:
                    raise WeeklyScheduleOverlapError(day)