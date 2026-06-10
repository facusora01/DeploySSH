import { useEffect, useState } from "react"
import { useAuth } from "../context/AuthContext"
import { api } from "../utils/api"
import { useRefunds } from "../hooks/useRefunds"
import Icon from "../components/Icon"
import "./historial.css"

interface Refund {
  id: string
  appointment_id: string
  status: "PENDING" | "DONE"
}

interface Appointment {
  id: string
  service_id: string
  service_name: string
  cliente_id: number
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
}

function Historial() {
  const { user } = useAuth()
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const { refunds } = useRefunds()

  useEffect(() => {
    if (!user) return
    api.get<Appointment[]>("/api/v1/appointments", true)
      .then((data) => {
        const now = new Date()
        const past = data.filter(
          (a) => new Date(a.end_time) < now || a.status === "cancelled"
        )
        past.sort((a, b) => new Date(b.start_time).getTime() - new Date(a.start_time).getTime())
        setAppointments(past)
      })
      .catch((err: any) => setError(err.response?.data?.detail || "No se pudo cargar el historial."))
      .finally(() => setLoading(false))
  }, [user])

  if (!user) return null

  const isProfesional = user.role === "profesional"

  function formatDateTime(isoStr: string) {
    const d = new Date(isoStr)
    return {
      date: d.toLocaleDateString("es-AR", { day: "numeric", month: "short", year: "numeric" }),
      time: d.toLocaleTimeString("es-AR", { hour: "2-digit", minute: "2-digit" }),
    }
  }

  const statusLabel: Record<string, string> = {
    confirmed: "Completado",
    cancelled: "Cancelado",
    pending: "Pendiente",
    completed: "Completado",
    attended: "Asistió",
    no_show: "No asistió",
  }

  return (
    <div className="historial-page">
      <header className="turnos-header">
        <h1 className="turnos-title">Historial</h1>
        <p className="turnos-subtitle">Turnos pasados y cancelados</p>
      </header>

      {error && (
        <div style={{ background: "var(--error-bg)", color: "var(--error)", padding: "12px", borderRadius: "var(--radius)", fontSize: "14px", marginBottom: "16px" }}>
          {error}
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: "center", padding: "32px", color: "var(--muted)" }}>
          Cargando historial...
        </div>
      ) : appointments.length === 0 ? (
        <section className="turnos-empty">
          <p className="turnos-empty-title">Sin historial todavía</p>
          <p className="turnos-empty-text">Acá van a aparecer tus turnos pasados y cancelados.</p>
        </section>
      ) : (
        <div className="historial-list">
          {appointments.map((appt) => {
            const { date, time } = formatDateTime(appt.start_time)
            const isCancelled = appt.status === "cancelled"
            const refund = refunds.find((r) => r.appointment_id === appt.id)
            return (
              <div key={appt.id} className={`historial-row ${isCancelled ? "is-cancelled" : ""}`}>
                <div className="historial-col-service">
                  <span className="historial-service-name">{appt.service_name}</span>
                  {appt.notes && (
                    <span className="historial-notes">{appt.notes}</span>
                  )}
                  {isCancelled && appt.cancellation_reason && (
                    <span className="historial-notes" style={{ color: "var(--error)", fontWeight: "500" }}>
                      Motivo: {appt.cancellation_reason}
                    </span>
                  )}
                </div>

                <div className="historial-col-meta">
                  <span className="historial-meta-item">
                    <Icon name="calendar" size={13} />
                    {date}
                  </span>
                  <span className="historial-meta-item">
                    <Icon name="clock" size={13} />
                    {time} hs
                  </span>
                  <span className="historial-meta-item">
                    <Icon name="users" size={13} />
                    {isProfesional ? appt.cliente_name : appt.profesional_name}
                  </span>
                  {isProfesional && appt.cliente_phone && (
                    <span className="historial-meta-item" style={{ color: "var(--muted)" }}>
                      {appt.cliente_phone}
                    </span>
                  )}
                </div>

                <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                  <div className={`turno-status-badge turno-status--${appt.status}`}>
                    {statusLabel[appt.status] ?? appt.status}
                  </div>
                  {!isProfesional && refund && (
                    <div className={`turno-status-badge refund-status--${refund.status.toLowerCase()}`}>
                      {refund.status === "PENDING" ? "Reembolso pendiente" : "Reembolsado"}
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default Historial
