import { useEffect, useState, type FormEvent } from "react"
import { ApiError } from "../utils/api"
import type {
  ScheduleBlockCreatePayload,
  TeamScheduleBlockConflict,
} from "../types/agenda"
import Icon from "./Icon"

interface BlockFormModalProps {
  open: boolean
  onClose: () => void
  onSubmit: (payload: ScheduleBlockCreatePayload) => Promise<void>
}

function BlockFormModal({ open, onClose, onSubmit }: BlockFormModalProps) {
  if (!open) return null

  return <BlockFormDialog onClose={onClose} onSubmit={onSubmit} />
}

function todayISO() {
  return new Date().toISOString().slice(0, 10)
}

function BlockFormDialog({
  onClose,
  onSubmit,
}: Pick<BlockFormModalProps, "onClose" | "onSubmit">) {
  const [startDate, setStartDate] = useState(todayISO)
  const [endDate, setEndDate] = useState(todayISO)
  const [reason, setReason] = useState("")
  const [error, setError] = useState("")
  const [conflict, setConflict] = useState<TeamScheduleBlockConflict | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose()
    }
    document.addEventListener("keydown", onKey)
    return () => document.removeEventListener("keydown", onKey)
  }, [onClose])

  function handleStartDateChange(value: string) {
    setStartDate(value)
    setConflict(null)
  }

  function handleEndDateChange(value: string) {
    setEndDate(value)
    setConflict(null)
  }

  function handleReasonChange(value: string) {
    setReason(value)
    setConflict(null)
  }

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError("")

    if (!startDate || !endDate) {
      setError("Las fechas son obligatorias.")
      return
    }
    if (endDate < startDate) {
      setError("La fecha de fin debe ser igual o posterior a la de inicio.")
      return
    }

    const trimmedReason = reason.trim()
    const payload: ScheduleBlockCreatePayload = {
      start_date: startDate,
      end_date: endDate,
      reason: trimmedReason === "" ? null : trimmedReason,
      confirm_cancel_appointments: conflict !== null,
    }

    setLoading(true)
    try {
      await onSubmit(payload)
      onClose()
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        const detail = parseBlockConflict(err.detail)
        if (detail) {
          setConflict(detail)
          setError("")
          return
        }
      }
      setError(err instanceof ApiError ? err.message : "No se pudo crear el bloqueo.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="agenda-modal-backdrop"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="agenda-block-modal-title"
    >
      <div className="agenda-modal">
        <header className="agenda-modal-header">
          <h2 id="agenda-block-modal-title" className="agenda-modal-title">
            Nuevo bloqueo
          </h2>
          <button
            type="button"
            className="agenda-modal-close"
            onClick={onClose}
            aria-label="Cerrar"
          >
            <Icon name="x" size={18} />
          </button>
        </header>

        <form className="agenda-modal-form" onSubmit={handleSubmit}>
          <div className="agenda-modal-row">
            <div className="agenda-modal-group">
              <label htmlFor="block-start" className="agenda-modal-label">
                Desde <span aria-hidden="true">*</span>
              </label>
              <input
                id="block-start"
                type="date"
                className="agenda-modal-input"
                value={startDate}
                onChange={(e) => handleStartDateChange(e.target.value)}
                required
              />
            </div>
            <div className="agenda-modal-group">
              <label htmlFor="block-end" className="agenda-modal-label">
                Hasta <span aria-hidden="true">*</span>
              </label>
              <input
                id="block-end"
                type="date"
                className="agenda-modal-input"
                value={endDate}
                onChange={(e) => handleEndDateChange(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="agenda-modal-group">
            <label htmlFor="block-reason" className="agenda-modal-label">
              Motivo
            </label>
            <input
              id="block-reason"
              type="text"
              className="agenda-modal-input"
              value={reason}
              onChange={(e) => handleReasonChange(e.target.value)}
              maxLength={200}
              placeholder="Opcional: vacaciones, feriado, etc."
            />
            <p className="agenda-modal-hint">
              Aparece como referencia. No lo ven tus clientes.
            </p>
          </div>

          {error && (
            <div className="agenda-modal-error" role="alert">
              {error}
            </div>
          )}

          {conflict && (
            <div className="agenda-block-conflict" role="alert">
              <div className="agenda-block-conflict-header">
                <Icon name="alert" size={18} />
                <div>
                  <h3>Hay turnos reservados en ese rango</h3>
                  <p>
                    Se cancelarán {conflict.affected_count} turno
                    {conflict.affected_count === 1 ? "" : "s"} y se notificará a
                    los clientes.
                  </p>
                </div>
              </div>
              <ul className="agenda-block-conflict-list">
                {conflict.appointments.map((appointment) => (
                  <li key={appointment.id}>
                    <span className="agenda-block-conflict-date">
                      {formatAppointmentDate(appointment.start_time)}
                    </span>
                    <span>{appointment.service_name}</span>
                    <span className="agenda-block-conflict-client">
                      {appointment.client_name}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="agenda-modal-actions">
            <button
              type="button"
              className="agenda-modal-button agenda-modal-button--secondary"
              onClick={onClose}
              disabled={loading}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="agenda-modal-button agenda-modal-button--primary"
              disabled={loading}
            >
              {loading
                ? conflict
                  ? "Cancelando..."
                  : "Creando..."
                : conflict
                  ? "Crear y cancelar turnos"
                  : "Crear bloqueo"}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function parseBlockConflict(detail: unknown): TeamScheduleBlockConflict | null {
  if (!detail || typeof detail !== "object") return null
  const value = detail as Partial<TeamScheduleBlockConflict>
  if (!Array.isArray(value.appointments)) return null
  if (typeof value.affected_count !== "number") return null
  return {
    message:
      typeof value.message === "string"
        ? value.message
        : "El bloqueo afecta turnos reservados.",
    affected_count: value.affected_count,
    appointments: value.appointments,
  }
}

function formatAppointmentDate(iso: string): string {
  return new Date(iso).toLocaleString("es-AR", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  })
}

export default BlockFormModal
