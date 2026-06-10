"""Schemas para la configuración de agenda del profesional.

Cubre tres conceptos del dominio:
- WeeklySchedule: franjas horarias semanales recurrentes
- ScheduleBlock: bloqueos de fechas (vacaciones, feriados)
- AgendaSettings: buffer entre turnos + pausa global
"""
from datetime import date, datetime, time
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ──────────── Weekly schedule ────────────


class WeeklyScheduleSlotIn(BaseModel):
    """Una franja horaria semanal recurrente (input)."""

    day_of_week: int = Field(..., ge=0, le=6, description="0=Lunes, 6=Domingo")
    start_time: time
    end_time: time

    @model_validator(mode="after")
    def _check_times(self):
        if self.start_time >= self.end_time:
            raise ValueError("start_time debe ser anterior a end_time")
        return self


class WeeklyScheduleSlotOut(WeeklyScheduleSlotIn):
    """Una franja horaria semanal recurrente (output con id)."""

    id: UUID

    model_config = ConfigDict(from_attributes=True)


class WeeklyScheduleUpdate(BaseModel):
    """Reemplaza el schedule semanal completo del profesional logueado.

    Mandar `slots=[]` borra todas las franjas (profesional sin horarios).
    """

    slots: list[WeeklyScheduleSlotIn] = Field(default_factory=list)


# ──────────── Schedule blocks ────────────


class ScheduleBlockCreate(BaseModel):
    """Bloqueo de fechas (vacaciones, feriados, día puntual)."""

    start_date: date
    end_date: date
    reason: Optional[str] = Field(None, max_length=200)

    @model_validator(mode="after")
    def _check_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date debe ser mayor o igual a start_date")
        return self


class TeamScheduleBlockCreate(ScheduleBlockCreate):
    """Bloqueo creado por el admin del local para un profesional del equipo.

    Si el bloqueo pisa turnos activos, el primer intento devuelve 409 con el
    detalle. El admin debe reenviar confirm_cancel_appointments=True para crear
    el bloqueo y cancelar esos turnos automáticamente.
    """

    confirm_cancel_appointments: bool = False


class ScheduleBlockOut(ScheduleBlockCreate):
    """Bloqueo de fechas (output con id)."""

    id: UUID

    model_config = ConfigDict(from_attributes=True)


class BlockedAppointmentPreview(BaseModel):
    id: UUID
    start_time: datetime
    service_name: str
    client_name: str
    client_email: str


class TeamScheduleBlockOut(ScheduleBlockOut):
    affected_count: int = 0
    cancelled_count: int = 0
    cancelled_appointments: list[BlockedAppointmentPreview] = Field(
        default_factory=list
    )


# ──────────── Agenda settings ────────────


class AgendaSettingsUpdate(BaseModel):
    """PATCH parcial sobre el config global del profesional.

    Ambos campos son opcionales — si el front manda solo uno, el otro queda
    intacto en la DB.
    """

    buffer_minutes: Optional[int] = Field(None, ge=0, le=240)
    agenda_paused: Optional[bool] = None


# ──────────── Config completo (GET /agenda) ────────────


class AgendaConfigResponse(BaseModel):
    """Snapshot completo del config de agenda del profesional logueado."""

    buffer_minutes: int
    agenda_paused: bool
    weekly_schedule: list[WeeklyScheduleSlotOut]
    schedule_blocks: list[ScheduleBlockOut]
