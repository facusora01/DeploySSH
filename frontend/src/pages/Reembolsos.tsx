import { useState } from "react"
import { useAuth } from "../context/AuthContext"
import { api } from "../utils/api"
import { useRefunds, type Refund } from "../hooks/useRefunds"
import Icon from "../components/Icon"
import "./historial.css"
import "./turnos.css"

function formatDateTime(isoStr: string) {
  const d = new Date(isoStr)
  return {
    date: d.toLocaleDateString("es-AR", { day: "numeric", month: "short", year: "numeric" }),
    time: d.toLocaleTimeString("es-AR", { hour: "2-digit", minute: "2-digit" }),
  }
}

function Reembolsos() {
  const { user } = useAuth()
  const isProfesional = user?.role === "profesional"

  // Profesional ve solo pendientes por procesar; cliente ve todos los suyos
  const { refunds, loading, error, refetch } = useRefunds(
    isProfesional ? { status: "PENDING" } : undefined
  )

  const [markingId, setMarkingId] = useState<string | null>(null)
  const [actionError, setActionError] = useState("")

  async function handleMarkDone(refund: Refund) {
    setMarkingId(refund.id)
    setActionError("")
    try {
      await api.patch(`/api/v1/refunds/${refund.id}/mark-done`, {}, true)
      await refetch()
    } catch (err: any) {
      setActionError(err?.message || "No se pudo marcar el reembolso como realizado.")
    } finally {
      setMarkingId(null)
    }
  }

  if (!user) return null

  return (
    <div className="historial-page">
      <header className="turnos-header">
        <h1 className="turnos-title">Reembolsos</h1>
        <p className="turnos-subtitle">
          {isProfesional
            ? "Señas por devolver a tus clientes"
            : "Estado de los reembolsos de tus señas"}
        </p>
      </header>

      {(error || actionError) && (
        <div style={{ background: "var(--error-bg)", color: "var(--error)", padding: "12px", borderRadius: "var(--radius)", fontSize: "14px", marginBottom: "16px" }}>
          {actionError || error}
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: "center", padding: "32px", color: "var(--muted)" }}>
          Cargando reembolsos...
        </div>
      ) : refunds.length === 0 ? (
        <section className="turnos-empty">
          <p className="turnos-empty-title">
            {isProfesional ? "No hay reembolsos pendientes" : "No tenés reembolsos"}
          </p>
          <p className="turnos-empty-text">
            {isProfesional
              ? "Cuando un cliente cancele un turno con seña pagada, va a aparecer acá."
              : "Acá vas a ver el estado de los reembolsos de tus señas."}
          </p>
        </section>
      ) : (
        <div className="historial-list">
          {refunds.map((refund) => {
            const { date, time } = formatDateTime(refund.appointment_start_time)
            const isPending = refund.status === "PENDING"
            return (
              <div key={refund.id} className="historial-row">
                <div className="historial-col-service">
                  <span className="historial-service-name">
                    {refund.appointment_service_name}
                  </span>
                  <span className="historial-notes">
                    {isProfesional
                      ? refund.appointment_client_name
                      : `Seña $${refund.amount.toLocaleString("es-AR")}`}
                  </span>
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
                    <Icon name="banknote" size={13} />
                    ${refund.amount.toLocaleString("es-AR")}
                  </span>
                </div>

                <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                  <div className={`turno-status-badge refund-status--${refund.status.toLowerCase()}`}>
                    {isPending ? "Pendiente de reembolso" : "Reembolsado"}
                  </div>
                  {isProfesional && isPending && (
                    <button
                      className="turno-refund-btn refund-status--pending"
                      onClick={() => handleMarkDone(refund)}
                      disabled={markingId === refund.id}
                    >
                      <Icon name="check" size={14} />
                      {markingId === refund.id ? "Guardando..." : "Marcar realizado"}
                    </button>
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

export default Reembolsos
