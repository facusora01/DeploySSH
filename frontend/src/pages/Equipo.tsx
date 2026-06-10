import { useEffect, useState, type FormEvent } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import { api, ApiError } from "../utils/api"
import "./perfil.css"
import "./equipo.css"

interface Invitation {
  id: number
  email: string
  status: "pending" | "accepted" | "expired" | "cancelled" | "rejected"
  expires_at: string
  created_at: string
}

interface TeamMember {
  id: number
  full_name: string
  specialty: string
  bio: string | null
  photo_url: string | null
  email: string
}

const STATUS_LABEL: Record<Invitation["status"], string> = {
  pending: "Pendiente",
  accepted: "Aceptada",
  expired: "Expirada",
  cancelled: "Cancelada",
  rejected: "Rechazada",
}

const STATUS_COLOR: Record<Invitation["status"], { bg: string; fg: string }> = {
  pending: { bg: "#fff7e6", fg: "#b26a00" },
  accepted: { bg: "#e9f8ef", fg: "#1b7f43" },
  expired: { bg: "#f1f1f1", fg: "#777" },
  cancelled: { bg: "#f1f1f1", fg: "#777" },
  rejected: { bg: "#fdecea", fg: "#c0392b" },
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

function Equipo() {
  const navigate = useNavigate()
  const { user } = useAuth()

  const [invitations, setInvitations] = useState<Invitation[]>([])
  const [team, setTeam] = useState<TeamMember[]>([])
  const [email, setEmail] = useState("")
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [loading, setLoading] = useState(false)
  const [busyId, setBusyId] = useState<number | null>(null)

  // Solo los locales gestionan equipo
  useEffect(() => {
    if (user && user.role !== "local") navigate("/perfil", { replace: true })
  }, [user, navigate])

  async function loadInvitations() {
    try {
      const data = await api.get<Invitation[]>("/api/v1/locales/me/invitations", true)
      setInvitations(data)
    } catch (err) {
      console.error("Error cargando invitaciones:", err)
    }
  }

  async function loadTeam() {
    try {
      const data = await api.get<TeamMember[]>("/api/v1/locales/me/profesionales", true)
      setTeam(data)
    } catch (err) {
      console.error("Error cargando equipo:", err)
    }
  }

  useEffect(() => {
    if (user?.role === "local") {
      loadInvitations()
      loadTeam()
    }
  }, [user]) // loadInvitations/loadTeam son estables para este efecto

  async function handleInvite(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError("")
    setSuccess("")
    setLoading(true)
    try {
      await api.post("/api/v1/locales/me/invitations", { email: email.trim() }, true)
      setSuccess(`Invitación enviada a ${email.trim()}.`)
      setEmail("")
      await loadInvitations()
    } catch (err) {
      if (err instanceof ApiError) setError(err.message)
      else setError("No se pudo enviar la invitación.")
    } finally {
      setLoading(false)
    }
  }

  async function handleResend(id: number) {
    setError("")
    setSuccess("")
    setBusyId(id)
    try {
      await api.post(`/api/v1/locales/me/invitations/${id}/resend`, undefined, true)
      setSuccess("Invitación reenviada.")
      await loadInvitations()
    } catch (err) {
      if (err instanceof ApiError) setError(err.message)
      else setError("No se pudo reenviar la invitación.")
    } finally {
      setBusyId(null)
    }
  }

  async function handleCancel(id: number) {
    setError("")
    setSuccess("")
    setBusyId(id)
    try {
      await api.delete(`/api/v1/locales/me/invitations/${id}`, true)
      await loadInvitations()
    } catch (err) {
      if (err instanceof ApiError) setError(err.message)
      else setError("No se pudo cancelar la invitación.")
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
            <h1 className="perfil-title">Equipo</h1>
            <p className="perfil-subtitle">Invitá profesionales a tu local</p>
          </div>
        </header>

        {/* Invitar */}
        <section
          style={{
            backgroundColor: "#fff",
            borderRadius: "12px",
            padding: "1.75rem",
            boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
          }}
        >
          <h2
            style={{
              fontSize: "1rem",
              fontWeight: 600,
              color: "#333",
              marginBottom: "1rem",
              textTransform: "uppercase",
              letterSpacing: "0.5px",
            }}
          >
            Invitar profesional
          </h2>
          <form
            onSubmit={handleInvite}
            style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap", alignItems: "center" }}
          >
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="email@profesional.com"
              className="auth-input"
              style={{ flex: "1 1 280px", minWidth: 0 }}
            />
            <button type="submit" disabled={loading} className="perfil-edit-button">
              {loading ? "Enviando..." : "Enviar invitación"}
            </button>
          </form>
          {error && (
            <p style={{ color: "#c0392b", marginTop: "0.75rem", fontSize: "0.9rem" }}>{error}</p>
          )}
          {success && (
            <p style={{ color: "#1b7f43", marginTop: "0.75rem", fontSize: "0.9rem" }}>{success}</p>
          )}
        </section>

        {/* Invitaciones */}
        <section
          style={{
            backgroundColor: "#fff",
            borderRadius: "12px",
            padding: "1.75rem",
            boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
          }}
        >
          <h2
            style={{
              fontSize: "1rem",
              fontWeight: 600,
              color: "#333",
              marginBottom: "1rem",
              textTransform: "uppercase",
              letterSpacing: "0.5px",
            }}
          >
            Invitaciones
          </h2>
          {invitations.length === 0 ? (
            <p style={{ color: "#aaa", fontSize: "0.95rem", margin: 0 }}>
              Todavía no enviaste invitaciones.
            </p>
          ) : (
            <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              {invitations.map((inv) => {
                const color = STATUS_COLOR[inv.status]
                // El local puede reenviar/cancelar mientras no esté aceptada
                const isPending = inv.status !== "accepted"
                return (
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
                      <p style={{ margin: 0, fontWeight: 500, color: "#333" }}>{inv.email}</p>
                      <p style={{ margin: 0, fontSize: "0.8rem", color: "#888" }}>
                        Expira: {formatDate(inv.expires_at)}
                      </p>
                    </div>
                    <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                      <span
                        style={{
                          backgroundColor: color.bg,
                          color: color.fg,
                          padding: "0.25rem 0.6rem",
                          borderRadius: "999px",
                          fontSize: "0.78rem",
                          fontWeight: 600,
                        }}
                      >
                        {STATUS_LABEL[inv.status]}
                      </span>
                      {isPending && (
                        <>
                          <button
                            type="button"
                            className="perfil-edit-button"
                            disabled={busyId === inv.id}
                            onClick={() => handleResend(inv.id)}
                          >
                            Reenviar
                          </button>
                          <button
                            type="button"
                            className="perfil-edit-button"
                            disabled={busyId === inv.id}
                            onClick={() => handleCancel(inv.id)}
                            style={{ color: "#c0392b", borderColor: "#e6b0aa" }}
                          >
                            Cancelar
                          </button>
                        </>
                      )}
                    </div>
                  </li>
                )
              })}
            </ul>
          )}
        </section>

        {/* Equipo actual */}
        <section
          style={{
            backgroundColor: "#fff",
            borderRadius: "12px",
            padding: "1.75rem",
            boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
          }}
        >
          <h2
            style={{
              fontSize: "1rem",
              fontWeight: 600,
              color: "#333",
              marginBottom: "1rem",
              textTransform: "uppercase",
              letterSpacing: "0.5px",
            }}
          >
            Profesionales en el equipo
          </h2>
          {team.length === 0 ? (
            <p style={{ color: "#aaa", fontSize: "0.95rem", margin: 0 }}>
              Todavía no hay profesionales vinculados.
            </p>
          ) : (
            <ul className="equipo-team-list">
              {team.map((m) => (
                <li key={m.id} className="equipo-team-item">
                  <div className="equipo-team-info">
                    {m.photo_url ? (
                      <img src={m.photo_url} alt={m.full_name} className="equipo-team-avatar" />
                    ) : (
                      <div className="equipo-team-avatar equipo-team-avatar--placeholder">
                        {m.full_name.charAt(0).toUpperCase()}
                      </div>
                    )}
                    <div>
                      <p className="equipo-team-name">{m.full_name}</p>
                      <p className="equipo-team-specialty">{m.specialty}</p>
                    </div>
                  </div>
                  <button
                    type="button"
                    className="perfil-edit-button"
                    onClick={() => navigate(`/equipo/${m.id}`)}
                  >
                    Gestionar
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  )
}

export default Equipo
