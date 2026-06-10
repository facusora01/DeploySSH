// Tipos espejo del back para la feature de agenda (US-14).
// El back devuelve `start_time` y `end_time` como "HH:MM:SS" y las fechas
// como "YYYY-MM-DD" — los manejamos como strings.

export interface WeeklyScheduleSlotOut {
  id: string
  day_of_week: number // 0=Lunes ... 6=Domingo
  start_time: string
  end_time: string
}

export interface WeeklyScheduleSlotIn {
  day_of_week: number
  start_time: string
  end_time: string
}

export interface ScheduleBlockOut {
  id: string
  start_date: string
  end_date: string
  reason: string | null
}

export interface ScheduleBlockCreatePayload {
  start_date: string
  end_date: string
  reason?: string | null
  confirm_cancel_appointments?: boolean
}

export interface BlockedAppointmentPreview {
  id: string
  start_time: string
  service_name: string
  client_name: string
  client_email: string
}

export interface TeamScheduleBlockOut extends ScheduleBlockOut {
  affected_count: number
  cancelled_count: number
  cancelled_appointments: BlockedAppointmentPreview[]
}

export interface TeamScheduleBlockConflict {
  message: string
  affected_count: number
  appointments: BlockedAppointmentPreview[]
}

export interface AgendaConfigResponse {
  buffer_minutes: number
  agenda_paused: boolean
  weekly_schedule: WeeklyScheduleSlotOut[]
  schedule_blocks: ScheduleBlockOut[]
}

export interface AgendaSettingsUpdatePayload {
  buffer_minutes?: number
  agenda_paused?: boolean
}
