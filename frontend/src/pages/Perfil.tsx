import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import { api } from "../utils/api"
import Icon from "../components/Icon"
import "./perfil.css"

// Estos campos no están en la response actual del backend.
// Los dejamos como placeholders hasta que el back los exponga.
const PLACEHOLDER_MEMBER_SINCE = new Date().toLocaleDateString("es-AR")
const PLACEHOLDER_LAST_LOGIN = "Hoy"
type Appointment = {
  id: string
  date: string
  time: string
  status: "pending" | "completed"
  professional?: string
  patient?: string
}
const PLACEHOLDER_APPOINTMENTS: Appointment[] = []

function Perfil() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [copied, setCopied] = useState(false)
  const [clientData, setClientData] = useState<any>(null)
  const [localData, setLocalData] = useState<any>(null)
  const [showLogo, setShowLogo] = useState(false)

  useEffect(() => {
    if (!user) return

    if (user.role === "client") {
      api.get<any>("/api/v1/clientes/me", true)
        .then(data => setClientData(data))
        .catch(err => console.error("Error fetching client profile:", err))
    } else if (user.role === "local") {
      api.get<any>("/api/v1/locales/me", true)
        .then(data => setLocalData(data))
        .catch(err => console.error("Error fetching local profile:", err))
    }
  }, [user])

  if (!user) return null

  const isProfesional = user.role === "profesional"
  const isLocal = user.role === "local"
  const roleLabel = isProfesional ? "Profesional" : isLocal ? "Local" : "Cliente"
  const avatarEmoji = isProfesional ? "👨‍⚕️" : isLocal ? "🏢" : "👤"

  // Manejador para que las action-cards (que son <div>) sean accesibles por teclado.
  function handleCardKeyDown(
    e: React.KeyboardEvent<HTMLDivElement>,
    action: () => void,
  ) {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault()
      action()
    }
  }

  return (
    <div className="perfil-page">
      <div className="perfil-container">
        <header className="perfil-header">
          <div>
            <h1 className="perfil-title">Mi perfil</h1>
            <p className="perfil-subtitle">{roleLabel}</p>
          </div>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            {(isProfesional || (isLocal && localData?.public_link)) && (
              <div style={{ position: "relative" }}>
                <button
                  type="button"
                  className="perfil-edit-button"
                  onClick={() => {
                    const url = isProfesional
                      ? `${window.location.origin}/p/${user.public_link || user.id}`
                      : `${window.location.origin}/local/${localData.public_link}`
                    navigator.clipboard.writeText(url).then(() => {
                      setCopied(true)
                      setTimeout(() => setCopied(false), 2000)
                    })
                  }}
                >
                  Compartir Perfil
                </button>
                {copied && (
                  <div style={{
                    position: "absolute",
                    bottom: "110%",
                    left: "50%",
                    transform: "translateX(-50%)",
                    backgroundColor: "#333",
                    color: "#fff",
                    padding: "0.4rem 0.75rem",
                    borderRadius: "4px",
                    fontSize: "0.8rem",
                    whiteSpace: "nowrap",
                    zIndex: 10,
                    boxShadow: "0 2px 4px rgba(0,0,0,0.2)"
                  }}>
                    ¡Copiado en portapapeles!
                  </div>
                )}
              </div>
            )}
            <button
              type="button"
              className="perfil-edit-button"
              onClick={() => navigate("/perfil/editar")}
            >
              Editar perfil
            </button>
          </div>
        </header>

        <section className="perfil-card">
          {isLocal && localData?.logo_url ? (
            <img
              src={localData.logo_url}
              alt="Logo del local"
              onClick={() => setShowLogo(true)}
              style={{ height: "64px", width: "64px", objectFit: "cover", borderRadius: "8px", border: "1px solid #eee", flexShrink: 0, cursor: "zoom-in" }}
            />
          ) : (
            <div className="perfil-avatar" aria-hidden="true">
              {avatarEmoji}
            </div>
          )}
          <div className="perfil-info">
            <div>
              <h2 className="perfil-name">{isLocal && localData ? localData.local_name : user.full_name}</h2>
              <p className="perfil-email">{user.email}</p>
            </div>
            <dl className="perfil-fields">
              {!isLocal && (
                <div className="perfil-field">
                  <dt className="perfil-field-label">Teléfono</dt>
                  <dd className="perfil-field-value">{user.phone || "No registrado"}</dd>
                </div>
              )}
              <div className="perfil-field">
                <dt className="perfil-field-label">Tipo de usuario</dt>
                <dd className="perfil-field-value">{roleLabel}</dd>
              </div>
              <div className="perfil-field">
                <dt className="perfil-field-label">Estado</dt>
                <dd className="perfil-field-value">Activo</dd>
              </div>
              <div className="perfil-field">
                <dt className="perfil-field-label">Miembro desde</dt>
                <dd className="perfil-field-value">{PLACEHOLDER_MEMBER_SINCE}</dd>
              </div>
              <div className="perfil-field">
                <dt className="perfil-field-label">Último acceso</dt>
                <dd className="perfil-field-value">{PLACEHOLDER_LAST_LOGIN}</dd>
              </div>
              {!isProfesional && clientData && (
                <>
                  <div className="perfil-field">
                    <dt className="perfil-field-label">DNI</dt>
                    <dd className="perfil-field-value">{clientData.dni || "No registrado"}</dd>
                  </div>
                  <div className="perfil-field">
                    <dt className="perfil-field-label">Fecha de nacimiento</dt>
                    <dd className="perfil-field-value">
                      {clientData.date_of_birth ? new Date(clientData.date_of_birth + "T00:00:00").toLocaleDateString("es-AR") : "No registrado"}
                    </dd>
                  </div>
                  <div className="perfil-field">
                    <dt className="perfil-field-label">Dirección</dt>
                    <dd className="perfil-field-value">{clientData.address || "No registrado"}</dd>
                  </div>
                  <div className="perfil-field">
                    <dt className="perfil-field-label">Ciudad</dt>
                    <dd className="perfil-field-value">{clientData.city || "No registrado"}</dd>
                  </div>
                  <div className="perfil-field" style={{ gridColumn: "1 / -1" }}>
                    <dt className="perfil-field-label">Notas</dt>
                    <dd className="perfil-field-value" style={{ whiteSpace: "pre-wrap" }}>{clientData.notes || "Ninguna"}</dd>
                  </div>
                </>
              )}
              {isLocal && localData && (
                <>
                  <div className="perfil-field">
                    <dt className="perfil-field-label">Titular</dt>
                    <dd className="perfil-field-value">{user.full_name}</dd>
                  </div>
                  <div className="perfil-field">
                    <dt className="perfil-field-label">Dirección</dt>
                    <dd className="perfil-field-value">{localData.address || "No registrado"}</dd>
                  </div>
                  <div className="perfil-field">
                    <dt className="perfil-field-label">Ciudad</dt>
                    <dd className="perfil-field-value">{localData.city || "No registrado"}</dd>
                  </div>
                  <div className="perfil-field">
                    <dt className="perfil-field-label">Teléfono</dt>
                    <dd className="perfil-field-value">{localData.phone || "No registrado"}</dd>
                  </div>
                </>
              )}
            </dl>
          </div>
        </section>

        {isLocal && localData && (
          <section style={{ backgroundColor: "#fff", borderRadius: "12px", padding: "1.75rem", boxShadow: "0 1px 3px rgba(0,0,0,0.05)" }}>
            <h2 style={{ fontSize: "1rem", fontWeight: "600", color: "#333", marginBottom: "1rem", textTransform: "uppercase", letterSpacing: "0.5px" }}>Descripción</h2>
            <p style={{ whiteSpace: "pre-wrap", wordBreak: "break-word", lineHeight: "1.7", color: localData.description ? "#555" : "#aaa", fontSize: "0.95rem", margin: 0 }}>
              {localData.description || "No registrado"}
            </p>
          </section>
        )}

        {isLocal && localData && (() => {
          const hours: Array<{ open_time: string; close_time: string; is_closed: boolean }> = localData.opening_hours || []
          if (hours.length !== 7) return null
          const days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
          const groups: Array<{ from: number; to: number; open_time: string; close_time: string }> = []
          let i = 0
          while (i < hours.length) {
            if (hours[i].is_closed) { i++; continue }
            const { open_time, close_time } = hours[i]
            let j = i + 1
            while (j < hours.length && !hours[j].is_closed && hours[j].open_time === open_time && hours[j].close_time === close_time) j++
            groups.push({ from: i, to: j - 1, open_time, close_time })
            i = j
          }
          const label = (from: number, to: number) =>
            from === to ? days[from] : to === from + 1 ? `${days[from]} y ${days[to]}` : `${days[from]} a ${days[to]}`
          return (
            <section style={{ backgroundColor: "#fff", borderRadius: "12px", padding: "1.75rem", boxShadow: "0 1px 3px rgba(0,0,0,0.05)" }}>
              <h2 style={{ fontSize: "1rem", fontWeight: "600", color: "#333", marginBottom: "1rem", textTransform: "uppercase", letterSpacing: "0.5px" }}>Horarios de apertura</h2>
              {groups.length === 0 ? (
                <p style={{ color: "#aaa", fontSize: "0.95rem", margin: 0 }}>No registrado</p>
              ) : (
                <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                  {groups.map((g, idx) => (
                    <li key={idx} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "0.5rem 0", borderBottom: "1px solid #f0f0f0" }}>
                      <span style={{ fontWeight: 500, color: "#333" }}>{label(g.from, g.to)}</span>
                      <span style={{ color: "#555" }}>{g.open_time} — {g.close_time} hs</span>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          )
        })()}

        <section className="perfil-appointments">
          <h2 className="perfil-section-title">
            {isProfesional ? "Mis turnos como profesional" : "Próximos turnos"}
          </h2>

          {PLACEHOLDER_APPOINTMENTS.length === 0 ? (
            <div className="perfil-empty">
              <div className="perfil-empty-icon" aria-hidden="true">📅</div>
              <h3 className="perfil-empty-title">
                {isProfesional
                  ? "No tenés turnos asignados"
                  : "No tenés turnos programados"}
              </h3>
              <p className="perfil-empty-text">
                {isProfesional
                  ? "Cuando tus clientes agenden turnos, aparecerán acá"
                  : "Cuando agendes un turno, va a aparecer acá"}
              </p>
            </div>
          ) : (
            <ul className="perfil-appointment-list">
              {PLACEHOLDER_APPOINTMENTS.map((apt) => (
                <li key={apt.id} className="perfil-appointment">
                  <div>
                    <p className="perfil-appointment-time">
                      {apt.date} — {apt.time}
                    </p>
                    <p className="perfil-appointment-person">
                      {isProfesional
                        ? `Paciente: ${apt.patient}`
                        : `Con ${apt.professional}`}
                    </p>
                  </div>
                  <span
                    className={`perfil-appointment-status perfil-appointment-status--${apt.status}`}
                  >
                    {apt.status === "completed" ? "Completado" : "Pendiente"}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="perfil-actions">
          <div className="perfil-action-card is-disabled">
            <div className="perfil-action-icon" aria-hidden="true">📅</div>
            <p className="perfil-action-title">Nuevo turno</p>
          </div>
          <div className="perfil-action-card is-disabled">
            <div className="perfil-action-icon" aria-hidden="true">📋</div>
            <p className="perfil-action-title">Mi historial</p>
          </div>
          {isProfesional ? (
            <div
              className="perfil-action-card"
              role="button"
              tabIndex={0}
              onClick={() => navigate("/servicios")}
              onKeyDown={(e) => handleCardKeyDown(e, () => navigate("/servicios"))}
              aria-label="Ir a mis servicios"
            >
              <div
                className="perfil-action-icon"
                style={{ color: "var(--accent)", display: "inline-flex" }}
                aria-hidden="true"
              >
                <Icon name="wrench" size={28} />
              </div>
              <p className="perfil-action-title">Mis servicios</p>
            </div>
          ) : isLocal ? (
            <div
              className="perfil-action-card"
              role="button"
              tabIndex={0}
              onClick={() => navigate("/equipo")}
              onKeyDown={(e) => handleCardKeyDown(e, () => navigate("/equipo"))}
              aria-label="Gestionar equipo"
            >
              <div className="perfil-action-icon" aria-hidden="true">👥</div>
              <p className="perfil-action-title">Mi equipo</p>
            </div>
          ) : (
            <div className="perfil-action-card is-disabled">
              <div className="perfil-action-icon" aria-hidden="true">⚙️</div>
              <p className="perfil-action-title">Configuración</p>
            </div>
          )}
        </section>
      </div>

      {showLogo && localData?.logo_url && (
        <div
          onClick={() => setShowLogo(false)}
          style={{
            position: "fixed", inset: 0, zIndex: 1000,
            backgroundColor: "rgba(0,0,0,0.85)",
            display: "flex", alignItems: "center", justifyContent: "center",
            cursor: "zoom-out",
          }}
        >
          <img
            src={localData.logo_url}
            alt="Logo del local"
            style={{ maxWidth: "90vw", maxHeight: "90vh", objectFit: "contain", borderRadius: "8px" }}
          />
        </div>
      )}
    </div>
  )
}

export default Perfil