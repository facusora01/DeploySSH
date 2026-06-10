import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import { api, ApiError } from "../utils/api"
import "./perfil.css"

interface ReceivedInvitation {
  id: number
  local_name: string
  status: string
  expires_at: string
  expired: boolean
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("es-AR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

function InvitacionesRecibidas() {
  const navigate = useNavigate()
  const { user } = useAuth()

  const [invitations, setInvitations] = useState<ReceivedInvitation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [busyId, setBusyId] = useState<number | null>(null)

  // Solo profesionales reciben invitaciones a equipos
  useEffect(() => {
    if (user && user.role !== "profesional") navigate("/perfil", { replace: true })
  }, [user, navigate])

  async function load() {
    try {
      const data = await api.get<ReceivedInvitation[]>(
        "/api/v1/locales/invitations/received",
        true,
      )
      setInvitations(data)
    } catch (err) {
      console.error("Error cargando invitaciones recibidas:", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (user?.role === "profesional") load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user])

  async function handleAccept(id: number) {
    setError("")
    setSuccess("")
    setBusyId(id)
    try {
      const res = await api.post<{ message: string }>(
        `/api/v1/locales/invitations/received/${id}/accept`,
        undefined,
        true,
      )
      setSuccess(res.message)
      await load()
    } catch (err) {
      if (err instanceof ApiError) setError(err.message)
      else setError("No se pudo aceptar la invitación.")
    } finally {
      setBusyId(null)
    }
  }

  async function handleReject(id: number) {
    setError("")
    setSuccess("")
    setBusyId(id)
    try {
      const res = await api.post<{ message: string }>(
        `/api/v1/locales/invitations/received/${id}/reject`,
        undefined,
        true,
      )
      setSuccess(res.message)
      await load()
    } catch (err) {
      if (err instanceof ApiError) setError(err.message)
      else setError("No se pudo rechazar la invitación.")
    } finally {
      setBusyId(null)
    }
  }

  if (!user) return null

  return (
    <div className="perfil-page">
      <div className="perfil-container">
        <header className="perfil-header">
          <div>
            <h1 className="perfil-title">Invitaciones recibidas</h1>
            <p className="perfil-subtitle">Locales que te invitaron a su equipo</p>
          </div>
        </header>

        <section
          style={{
            backgroundColor: "#fff",
            borderRadius: "12px",
            padding: "1.75rem",
            boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
          }}
        >
          {error && (
            <p style={{ color: "#c0392b", marginBottom: "0.75rem", fontSize: "0.9rem" }}>{error}</p>
          )}
          {success && (
            <p style={{ color: "#1b7f43", marginBottom: "0.75rem", fontSize: "0.9rem" }}>{success}</p>
          )}

          {loading ? (
            <p style={{ color: "#aaa", fontSize: "0.95rem", margin: 0 }}>Cargando...</p>
          ) : invitations.length === 0 ? (
            <p style={{ color: "#aaa", fontSize: "0.95rem", margin: 0 }}>
              No tenés invitaciones pendientes.
            </p>
          ) : (
            <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              {invitations.map((inv) => (
                <li
                  key={inv.id}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    gap: "1rem",
                    flexWrap: "wrap",
                    padding: "0.75rem 0",
                    borderBottom: "1px solid #f0f0f0",
                  }}
                >
                  <div style={{ minWidth: 0 }}>
                    <p style={{ margin: 0, fontWeight: 500, color: "#333" }}>{inv.local_name}</p>
                    <p style={{ margin: 0, fontSize: "0.8rem", color: inv.expired ? "#c0392b" : "#888" }}>
                      {inv.expired ? "Expirada — pedí que te reenvíen" : `Expira: ${formatDate(inv.expires_at)}`}
                    </p>
                  </div>
                  <div style={{ display: "flex", gap: "0.5rem" }}>
                    <button
                      type="button"
                      className="perfil-edit-button"
                      disabled={busyId === inv.id || inv.expired}
                      onClick={() => handleAccept(inv.id)}
                    >
                      {busyId === inv.id ? "..." : "Aceptar"}
                    </button>
                    <button
                      type="button"
                      className="perfil-edit-button"
                      disabled={busyId === inv.id}
                      onClick={() => handleReject(inv.id)}
                      style={{ color: "#c0392b", borderColor: "#e6b0aa" }}
                    >
                      Rechazar
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  )
}

export default InvitacionesRecibidas
