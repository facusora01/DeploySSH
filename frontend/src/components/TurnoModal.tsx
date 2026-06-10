import { useState } from "react"
import { useNavigate } from "react-router-dom"
import Icon from "./Icon"
import { buildGoogleCalendarUrl } from "../utils/googleCalendar"

export interface FormFieldAnswer {
  field_id: string
  field_name: string
  answer: string
}

export interface Refund {
  id: string
  appointment_id: string
  status: "PENDING" | "DONE"
  amount: number
}

export interface Appointment {
  id: string
  service_name: string
  cliente_name: string
  cliente_phone: string | null
  profesional_name: string
  profesional_public_link: string
  start_time: string
  end_time: string
  notes: string | null
  status: string
  cancellation_reason?: string | null
  deposit_status?: string
  deposit_amount?: number | null
  refund?: Refund | null
  form_responses: FormFieldAnswer[]
}

interface Props {
  appt: Appointment
  isProfesional: boolean
  isLocal?: boolean
  cancellingId: string | null
  onClose: () => void
  onCancel: (id: string, reason: string) => void
  onPayDeposit?: (appointmentId: string) => Promise<void>
  payingDepositId?: string | null
  onMarkAttendance?: (appointmentId: string, status: "attended" | "no_show") => Promise<void>
  markingAttendanceId?: string | null
  onMarkRefundDone?: (refundId: string) => Promise<void>
  markingRefundId?: string | null
}

const statusLabel: Record<string, string> = {
  confirmed: "Confirmado",
  pending: "Pendiente",
  completed: "Completado",
  cancelled: "Cancelado",
  attended: "Asistió",
  no_show: "No asistió",
}

function formatDateLong(isoStr: string) {
  return new Date(isoStr).toLocaleDateString("es-AR", {
    weekday: "long", day: "numeric", month: "long", year: "numeric",
  })
}

function formatTime(isoStr: string) {
  return new Date(isoStr).toLocaleTimeString("es-AR", { hour: "2-digit", minute: "2-digit" })
}

function TurnoModal({
  appt,
  isProfesional,
  isLocal = false,
  cancellingId,
  onClose,
  onCancel,
  onPayDeposit,
  payingDepositId,
  onMarkAttendance,
  markingAttendanceId,
  onMarkRefundDone,
  markingRefundId,
}: Props) {
  const navigate = useNavigate()
  const [showCancelConfirm, setShowCancelConfirm] = useState(false)
  const [reason, setReason] = useState("")

  // Se puede marcar asistencia para turnos de hoy o de días pasados, no para días futuros
  const apptDay = new Date(appt.start_time)
  apptDay.setHours(0, 0, 0, 0)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const isFutureDay = apptDay > today
  const attendanceDone = appt.status === "attended" || appt.status === "no_show"
  const canMarkAttendance =
    isProfesional &&
    !!onMarkAttendance &&
    !isFutureDay &&
    appt.status !== "cancelled" &&
    !attendanceDone
  const isMarking = markingAttendanceId === appt.id

  const isCancelled = appt.status === "cancelled"

  return (
    <div className="turno-modal-overlay" onClick={onClose}>
      <div className="turno-modal" onClick={(e) => e.stopPropagation()}>
        <div className="turno-modal-header">
          <h2 className="turno-modal-title">{appt.service_name}</h2>
          <button className="turno-modal-close" onClick={onClose}>
            <Icon name="x" size={18} />
          </button>
        </div>

        <div className="turno-modal-body">
          <span className={`turno-status-badge turno-status--${appt.status}`}>
            {statusLabel[appt.status] ?? appt.status}
          </span>

          <div className="turno-modal-detail-row">
            <Icon name="calendar" size={15} />
            <span style={{ textTransform: "capitalize" }}>{formatDateLong(appt.start_time)}</span>
          </div>
          <div className="turno-modal-detail-row">
            <Icon name="clock" size={15} />
            <span>{formatTime(appt.start_time)} hs</span>
          </div>
          <div className="turno-modal-detail-row">
            <Icon name="users" size={15} />
            {isProfesional ? (
              <span>{appt.cliente_name}</span>
            ) : appt.profesional_public_link ? (
              <button
                type="button"
                className="turno-modal-link"
                onClick={() => { onClose(); navigate(`/p/${appt.profesional_public_link}`) }}
              >
                {appt.profesional_name}
              </button>
            ) : (
              <span>{appt.profesional_name}</span>
            )}
          </div>
          {isProfesional && appt.cliente_phone && (
            <div className="turno-modal-detail-row">
              <Icon name="users" size={15} />
              <span>{appt.cliente_phone}</span>
            </div>
          )}
          {isLocal && (
            <div className="turno-modal-detail-row">
              <Icon name="users" size={15} />
              <span>{appt.profesional_name}</span>
            </div>
          )}
          {appt.notes && (
            <div className="turno-notes" style={{ marginTop: "4px" }}>
              <strong>Nota:</strong> {appt.notes}
            </div>
          )}
          {isCancelled && appt.cancellation_reason && (
            <div className="turno-notes" style={{ marginTop: "8px", borderTop: "1px solid var(--border)", paddingTop: "8px" }}>
              <strong>Motivo de cancelación:</strong> {appt.cancellation_reason}
            </div>
          )}
          {appt.deposit_status && appt.deposit_amount && (
            <div style={{ marginTop: "12px", paddingTop: "12px", borderTop: "1px solid var(--border)" }}>
              <div style={{ fontSize: "12px", color: "var(--muted)", marginBottom: "8px" }}>Seña</div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontWeight: "600" }}>${appt.deposit_amount.toLocaleString("es-AR")}</span>
                <span style={{
                  fontSize: "12px",
                  padding: "4px 8px",
                  borderRadius: "4px",
                  backgroundColor: appt.deposit_status === "PENDING" ? "var(--warning-bg, #fef3c7)" : "var(--success-bg, #dcfce7)",
                  color: appt.deposit_status === "PENDING" ? "var(--warning, #d97706)" : "var(--success, #16a34a)",
                }}>
                  {appt.deposit_status === "PENDING" ? "Pendiente" : appt.deposit_status === "PAID" ? "Pagada" : appt.deposit_status}
                </span>
              </div>
              {appt.deposit_status === "PAID" && appt.refund && (
                <div style={{ marginTop: "8px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontSize: "12px", color: "var(--muted)" }}>Reembolso</span>
                  <span style={{
                    fontSize: "12px",
                    padding: "4px 8px",
                    borderRadius: "4px",
                    backgroundColor: appt.refund.status === "DONE" ? "var(--success-bg, #dcfce7)" : "#fef3c7",
                    color: appt.refund.status === "DONE" ? "var(--success, #16a34a)" : "#d97706",
                  }}>
                    {appt.refund.status === "PENDING" ? "Pendiente de reembolso" : "Reembolsado"}
                  </span>
                </div>
              )}
            </div>
          )}
          {isProfesional && appt.form_responses?.length > 0 && (
            <div className="turno-form-responses">
              <p className="turno-form-responses-title">Formulario completado por el cliente:</p>
              <ul className="turno-form-responses-list">
                {appt.form_responses.map((r) => (
                  <li key={r.field_id} className="turno-form-response-item">
                    <span className="turno-form-response-label">{r.field_name}:</span>
                    <span className="turno-form-response-value">{r.answer}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {showCancelConfirm && (
            <div className="turno-cancel-form" style={{ marginTop: "16px", borderTop: "1px solid var(--border)", paddingTop: "16px" }}>
              <label style={{ display: "block", fontSize: "14px", fontWeight: "600", marginBottom: "8px" }}>
                Motivo de cancelación
              </label>
              <textarea
                className="turno-cancel-textarea"
                placeholder="Explicá por qué cancelás el turno (mín. 5 caracteres)..."
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                style={{
                  width: "100%",
                  minHeight: "80px",
                  padding: "8px",
                  borderRadius: "var(--radius)",
                  border: "1px solid var(--border)",
                  fontSize: "14px",
                  marginBottom: "8px",
                }}
              />
              <div style={{ display: "flex", gap: "8px" }}>
                <button
                  className="turno-cancel-confirm-btn"
                  onClick={() => onCancel(appt.id, reason)}
                  disabled={reason.length < 5 || !!cancellingId}
                  style={{
                    flex: 1,
                    padding: "8px",
                    backgroundColor: "var(--error, #ef4444)",
                    color: "white",
                    border: "none",
                    borderRadius: "var(--radius)",
                    fontWeight: "600",
                    cursor: reason.length < 5 ? "not-allowed" : "pointer",
                    opacity: reason.length < 5 ? 0.6 : 1,
                  }}
                >
                  {cancellingId ? "Cancelando..." : "Confirmar cancelación"}
                </button>
                <button
                  className="turno-cancel-abort-btn"
                  onClick={() => setShowCancelConfirm(false)}
                  style={{
                    padding: "8px 16px",
                    backgroundColor: "var(--bg-card)",
                    border: "1px solid var(--border)",
                    borderRadius: "var(--radius)",
                    fontWeight: "600",
                    cursor: "pointer",
                  }}
                >
                  Volver
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="turno-modal-footer">
          {canMarkAttendance && !showCancelConfirm && (
            <>
              <button
                className="turno-attendance-btn turno-attendance-btn--yes"
                onClick={() => onMarkAttendance!(appt.id, "attended")}
                disabled={isMarking}
              >
                <Icon name="check" size={14} />
                {isMarking ? "Guardando..." : "Asistió"}
              </button>
              <button
                className="turno-attendance-btn turno-attendance-btn--no"
                onClick={() => onMarkAttendance!(appt.id, "no_show")}
                disabled={isMarking}
              >
                <Icon name="x" size={14} />
                {isMarking ? "Guardando..." : "No asistió"}
              </button>
            </>
          )}
          {!isProfesional && appt.deposit_status === "PENDING" && onPayDeposit && !showCancelConfirm && (
            <button
              className="turno-pay-btn"
              onClick={() => onPayDeposit(appt.id)}
              disabled={payingDepositId === appt.id}
              style={{
                padding: "8px 16px",
                backgroundColor: "var(--primary, #3b82f6)",
                color: "white",
                border: "none",
                borderRadius: "var(--radius)",
                cursor: "pointer",
                fontSize: "14px",
                fontWeight: "600",
                opacity: payingDepositId === appt.id ? 0.7 : 1,
              }}
            >
              {payingDepositId === appt.id ? "Pagando seña..." : "Pagar seña"}
            </button>
          )}
          {isProfesional && appt.refund && appt.refund.status === "PENDING" && onMarkRefundDone && (
            <button
              className="turno-refund-btn"
              onClick={() => onMarkRefundDone(appt.refund!.id)}
              disabled={markingRefundId === appt.refund.id}
            >
              <Icon name="check" size={14} />
              {markingRefundId === appt.refund.id ? "Guardando..." : "Marcar reembolso como realizado"}
            </button>
          )}
          {!isProfesional && !showCancelConfirm && (
            <a
              href={buildGoogleCalendarUrl({
                title: `Turno: ${appt.service_name} con ${appt.profesional_name}`,
                startTime: appt.start_time,
                endTime: appt.end_time,
                details: appt.notes || undefined,
              })}
              target="_blank"
              rel="noopener noreferrer"
              className="turno-calendar-btn"
            >
              <Icon name="calendar" size={14} />
              Google Calendar
            </a>
          )}
          {appt.status !== "cancelled" && !showCancelConfirm && (
            <button
              className="turno-cancel-btn"
              onClick={() => {
                if (isProfesional) {
                  setShowCancelConfirm(true)
                } else {
                  if (window.confirm("¿Querés cancelar este turno? Una vez cancelado no podrás revertirlo.")) {
                    onCancel(appt.id, "El cliente decidió cancelar el turno")
                  }
                }
              }}
              disabled={cancellingId === appt.id}
            >
              {cancellingId === appt.id ? "Cancelando..." : "Cancelar turno"}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default TurnoModal
