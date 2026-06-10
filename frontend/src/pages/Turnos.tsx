import { useEffect, useState } from "react"
import { useSearchParams } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import { api } from "../utils/api"
import { useRefunds } from "../hooks/useRefunds"
import Icon from "../components/Icon"
import TurnoModal, { type Appointment } from "../components/TurnoModal"
import AgendaProfesional from "../components/AgendaProfesional"
import DotsBackground from "../components/DotsBackground"
import "./turnos.css"

interface Notification {
  id: string
  type: "success" | "error"
  message: string
}

function Turnos() {
  const { user } = useAuth()
  const isProfesional = user?.role === "profesional"
  const isLocal = user?.role === "local"

  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [cancellingId, setCancellingId] = useState<string | null>(null)
  const [payingDepositId, setPayingDepositId] = useState<string | null>(null)
  const [markingAttendanceId, setMarkingAttendanceId] = useState<string | null>(null)
  const [markingRefundId, setMarkingRefundId] = useState<string | null>(null)
  const [selected, setSelected] = useState<Appointment | null>(null)
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [focusDate, setFocusDate] = useState<Date | null>(null)
  const [searchParams, setSearchParams] = useSearchParams()

  const { refunds, refetch: refetchRefunds } = useRefunds(
    (isProfesional || isLocal) ? { status: "PENDING" } : undefined
  )

  const showNotification = (type: "success" | "error", message: string) => {
    const id = Math.random().toString(36).substring(2, 11)
    setNotifications((prev) => [...prev, { id, type, message }])
    setTimeout(() => {
      setNotifications((prev) => prev.filter((n) => n.id !== id))
    }, 4000)
  }

  const fetchAppointments = async () => {
    if (!user) return
    try {
      const data = await api.get<Appointment[]>("/api/v1/appointments", true)
      if (user.role === "profesional" || user.role === "local") {
        setAppointments(data)
      } else {
        const now = new Date()
        setAppointments(data.filter((a) => new Date(a.end_time) >= now && a.status !== "cancelled"))
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "No se pudieron cargar los turnos.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAppointments()
  }, [user])

  // Al llegar desde una notificación (?appointment=<id>): abrir el turno y
  // posicionar la agenda en su fecha.
  const focusId = searchParams.get("appointment")
  useEffect(() => {
    if (!focusId || appointments.length === 0) return
    const appt = appointments.find((a) => a.id === focusId)
    if (appt) {
      setSelected(appt)
      setFocusDate(new Date(appt.start_time))
    }
    setSearchParams({}, { replace: true })
  }, [focusId, appointments])

  async function handleCancel(apptId: string, reason: string) {
    setCancellingId(apptId)
    setError("")
    try {
      await api.put(`/api/v1/appointments/${apptId}/cancel`, {
        cancellation_reason: reason
      }, true)
      setSelected(null)
      await fetchAppointments()
      showNotification("success", "Turno cancelado correctamente")
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || "No se pudo cancelar el turno."
      setError(msg)
      showNotification("error", msg)
    } finally {
      setCancellingId(null)
    }
  }

  async function handlePayDeposit(apptId: string) {
    setPayingDepositId(apptId)
    setError("")
    try {
      await api.patch(`/api/v1/appointments/${apptId}/pay-deposit`, {}, true)
      await fetchAppointments()
      const updated = appointments.find(a => a.id === apptId)
      if (updated) {
        setSelected({ ...updated, deposit_status: "PAID" })
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "No se pudo procesar el pago de la seña.")
    } finally {
      setPayingDepositId(null)
    }
  }

  async function handleMarkAttendance(apptId: string, status: "attended" | "no_show") {
    setMarkingAttendanceId(apptId)
    setError("")
    try {
      const updated = await api.patch<Appointment>(
        `/api/v1/appointments/${apptId}/attendance`,
        { status },
        true
      )
      await fetchAppointments()
      setSelected((prev) => (prev && prev.id === apptId ? { ...prev, status: updated.status } : prev))
    } catch (err: any) {
      setError(err.response?.data?.detail || "No se pudo actualizar la asistencia del turno.")
    } finally {
      setMarkingAttendanceId(null)
    }
  }

  async function handleMarkRefundDone(refundId: string) {
    setMarkingRefundId(refundId)
    setError("")
    try {
      await api.patch(`/api/v1/refunds/${refundId}/mark-done`, {}, true)
      await refetchRefunds()
      setSelected(null)
      showNotification("success", "Reembolso marcado como realizado")
    } catch (err: any) {
      const msg = err.message || "No se pudo marcar el reembolso como realizado."
      setError(msg)
      showNotification("error", msg)
    } finally {
      setMarkingRefundId(null)
    }
  }

  if (!user) return null

  function formatDate(isoStr: string) {
    const d = new Date(isoStr)
    return d.toLocaleDateString("es-AR", { weekday: "short", day: "numeric", month: "short" })
  }

  function formatTime(isoStr: string) {
    return new Date(isoStr).toLocaleTimeString("es-AR", { hour: "2-digit", minute: "2-digit" })
  }

  const statusLabel: Record<string, string> = {
    confirmed: "Confirmado",
    pending: "Pendiente",
    completed: "Completado",
    cancelled: "Cancelado",
    attended: "Asistió",
    no_show: "No asistió",
  }

  return (
    <>
    <DotsBackground />
    <div className={`turnos-page ${(isProfesional || isLocal) ? "turnos-page--agenda" : ""}`}>
      <header className="turnos-header">
        <h1 className="turnos-title">Turnos</h1>
        <p className="turnos-subtitle">
          {isProfesional ? "Tu agenda de pacientes" : isLocal ? "La agenda de tu equipo" : "Tus próximos turnos"}
        </p>
      </header>

      {error && (
        <div style={{ background: "var(--error-bg)", color: "var(--error)", padding: "12px", borderRadius: "var(--radius)", fontSize: "14px", marginBottom: "16px" }}>
          {error}
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: "center", padding: "32px", color: "var(--muted)" }}>
          Cargando tus turnos...
        </div>
      ) : (isProfesional || isLocal) ? (
        <AgendaProfesional appointments={appointments} onSelect={setSelected} refunds={refunds} focusDate={focusDate} />
      ) : appointments.length === 0 ? (
        <section className="turnos-empty">
          <p className="turnos-empty-title">No tenés turnos programados</p>
          <p className="turnos-empty-text">Cuando agendes un turno, va a aparecer acá.</p>
        </section>
      ) : (
        <div className="turnos-list">
          {appointments.map((appt) => (
            <button
              key={appt.id}
              className="turno-card-compact"
              onClick={() => setSelected(appt)}
            >
              <span className="turno-compact-service">{appt.service_name}</span>
              <span className="turno-compact-meta">
                <span className="turno-compact-meta-item">
                  <Icon name="calendar" size={13} />
                  <span style={{ textTransform: "capitalize" }}>{formatDate(appt.start_time)}</span>
                </span>
                <span className="turno-compact-meta-item">
                  <Icon name="clock" size={13} />
                  {formatTime(appt.start_time)} hs
                </span>
                <span className="turno-compact-meta-item">
                  <Icon name="users" size={13} />
                  {appt.profesional_name}
                </span>
              </span>
              <span className={`turno-status-badge turno-status--${appt.status}`}>
                {statusLabel[appt.status] ?? appt.status}
              </span>
            </button>
          ))}
        </div>
      )}

      {selected && (
        <TurnoModal
          appt={{
            ...selected,
            refund: refunds.find((r) => r.appointment_id === selected.id) || null,
          }}
          isProfesional={isProfesional || isLocal}
          isLocal={isLocal}
          cancellingId={cancellingId}
          onClose={() => setSelected(null)}
          onCancel={handleCancel}
          onPayDeposit={!isProfesional && !isLocal ? handlePayDeposit : undefined}
          payingDepositId={payingDepositId}
          onMarkAttendance={isProfesional ? handleMarkAttendance : undefined}
          markingAttendanceId={markingAttendanceId}
          onMarkRefundDone={isProfesional ? handleMarkRefundDone : undefined}
          markingRefundId={markingRefundId}
        />
      )}

      {notifications.map((notif) => (
        <div
          key={notif.id}
          className={`turnos-notification turnos-notification--${notif.type}`}
        >
          <Icon name={notif.type === "success" ? "check-circle" : "alert-circle"} size={18} />
          <span className="turnos-notification-text">{notif.message}</span>
        </div>
      ))}
    </div>
    </>
  )
}

export default Turnos
