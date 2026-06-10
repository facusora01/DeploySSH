import { useEffect, useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { api } from "../utils/api"
import "./perfil.css"

const DAYS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

interface HourGroup {
  from: number
  to: number
  open_time: string
  close_time: string
}

function groupOpenHours(hours: DaySchedule[]): HourGroup[] {
  const groups: HourGroup[] = []
  let i = 0
  while (i < hours.length) {
    if (hours[i].is_closed) { i++; continue }
    const { open_time, close_time } = hours[i]
    let j = i + 1
    while (j < hours.length && !hours[j].is_closed && hours[j].open_time === open_time && hours[j].close_time === close_time) j++
    groups.push({ from: i, to: j - 1, open_time, close_time })
    i = j
  }
  return groups
}

function formatDayRange(from: number, to: number): string {
  if (from === to) return DAYS[from]
  if (to === from + 1) return `${DAYS[from]} y ${DAYS[to]}`
  return `${DAYS[from]} a ${DAYS[to]}`
}

interface ServiceData {
  id: string
  name: string
  description: string | null
  duration_minutes: number
  price: number | null
}

interface ProfesionalData {
  id: number
  full_name: string
  specialty: string
  bio: string | null
  public_link: string | null
  services: ServiceData[]
}

interface DaySchedule {
  open_time: string
  close_time: string
  is_closed: boolean
}

interface LocalPublicData {
  id: number
  local_name: string
  logo_url: string | null
  description: string | null
  address: string | null
  city: string | null
  opening_hours: DaySchedule[] | null
  profesionales: ProfesionalData[]
}

function formatPrice(price: number | null): string {
  if (price === null) return "Sin precio"
  return `$${price.toLocaleString("es-AR", { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`
}

function formatDuration(minutes: number): string {
  if (minutes < 60) return `${minutes} min`
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return m === 0 ? `${h} h` : `${h} h ${m} min`
}

function PublicLocalProfile() {
  const { slug } = useParams<{ slug: string }>()
  const navigate = useNavigate()
  const [profile, setProfile] = useState<LocalPublicData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [showLogo, setShowLogo] = useState(false)

  useEffect(() => {
    async function load() {
      try {
        const data = await api.get<LocalPublicData>(`/api/v1/locales/${slug}/public`, false)
        setProfile(data)
      } catch (err: any) {
        setError(err.response?.data?.detail || "No se pudo cargar el perfil del local.")
      } finally {
        setLoading(false)
      }
    }
    if (slug) load()
  }, [slug])

  if (loading) {
    return (
      <div className="perfil-page">
        <div className="perfil-container" style={{ textAlign: "center", padding: "2rem" }}>
          Cargando perfil...
        </div>
      </div>
    )
  }

  if (error || !profile) {
    return (
      <div className="perfil-page">
        <div className="perfil-container" style={{ textAlign: "center", padding: "2rem" }}>
          <h2 style={{ color: "red" }}>Error</h2>
          <p>{error}</p>
          <button className="perfil-edit-button" style={{ marginTop: "1rem" }} onClick={() => navigate(-1)}>
            Volver
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="perfil-page">
      <div className="perfil-container">
        {/* Header */}
        <header className="perfil-header">
          <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
            {profile.logo_url && (
              <img
                src={profile.logo_url}
                alt={`Logo de ${profile.local_name}`}
                onClick={() => setShowLogo(true)}
                style={{ height: "56px", width: "56px", objectFit: "cover", borderRadius: "8px", border: "1px solid #eee", cursor: "zoom-in" }}
              />
            )}
            <div>
              <h1 className="perfil-title">{profile.local_name}</h1>
              <p className="perfil-subtitle">Local</p>
            </div>
          </div>
        </header>

        {/* Info card — only render if there's something to show */}
        {(profile.address || profile.city || profile.description) && (
          <section className="perfil-card">
            <div className="perfil-info" style={{ width: "100%" }}>
              <dl className="perfil-fields">
                {profile.address && (
                  <div className="perfil-field">
                    <dt className="perfil-field-label">Dirección</dt>
                    <dd className="perfil-field-value">{profile.address}</dd>
                  </div>
                )}
                {profile.city && (
                  <div className="perfil-field">
                    <dt className="perfil-field-label">Ciudad</dt>
                    <dd className="perfil-field-value">{profile.city}</dd>
                  </div>
                )}
                {profile.description && (
                  <div className="perfil-field" style={{ gridColumn: "1 / -1" }}>
                    <dt className="perfil-field-label">Descripción</dt>
                    <dd className="perfil-field-value" style={{ whiteSpace: "pre-wrap" }}>{profile.description}</dd>
                  </div>
                )}
              </dl>
            </div>
          </section>
        )}

        {/* Horarios de apertura */}
        {profile.opening_hours && profile.opening_hours.length === 7 && groupOpenHours(profile.opening_hours).length > 0 && (
          <section className="perfil-card" style={{ flexDirection: "column" }}>
            <h2 className="perfil-section-title">Horarios de apertura</h2>
            <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              {groupOpenHours(profile.opening_hours).map((g, i) => (
                <li key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "0.5rem 0", borderBottom: "1px solid var(--border)" }}>
                  <span style={{ fontWeight: 500, color: "var(--text-h)" }}>{formatDayRange(g.from, g.to)}</span>
                  <span style={{ color: "var(--text)" }}>{g.open_time} — {g.close_time} hs</span>
                </li>
              ))}
            </ul>
          </section>
        )}

        {/* Profesionales */}
        <section className="perfil-card" style={{ flexDirection: "column" }}>
          <h2 className="perfil-section-title">Nuestro equipo</h2>
          {profile.profesionales.length === 0 ? (
            <div className="perfil-empty">
              <div className="perfil-empty-icon" aria-hidden="true">👥</div>
              <p className="perfil-empty-text">No hay profesionales asociados aún.</p>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
              {profile.profesionales.map((prof, idx) => (
                <div
                  key={prof.id}
                  style={{
                    borderBottom: idx < profile.profesionales.length - 1 ? "1px solid var(--border)" : "none",
                    paddingBottom: idx < profile.profesionales.length - 1 ? "1.5rem" : 0,
                  }}
                >
                  <h3 style={{ margin: "0 0 0.15rem", fontSize: "1rem", fontWeight: 600, color: "var(--text-h)", textTransform: "capitalize" }}>{prof.full_name.toLowerCase()}</h3>
                  <p style={{ margin: "0 0 0.75rem", fontSize: "0.875rem", color: "var(--muted)" }}>{prof.specialty}</p>
                  {prof.bio && <p style={{ margin: "0 0 0.75rem", fontSize: "0.875rem", color: "var(--text)", lineHeight: 1.5 }}>{prof.bio}</p>}
                  {prof.services.length > 0 && (
                    <ul className="perfil-services">
                      {prof.services.map((s) => (
                        <li key={s.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "1rem" }}>
                          <div style={{ flex: "1 1 0", minWidth: 0 }}>
                            <strong style={{ display: "block", fontSize: "0.9375rem", fontWeight: 600, color: "var(--text-h)" }}>{s.name}</strong>
                            {s.description && <div className="perfil-service-description">{s.description}</div>}
                            <div className="perfil-service-duration">{formatDuration(s.duration_minutes)}</div>
                          </div>
                          <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "0.4rem", flexShrink: 0 }}>
                            <span style={{ color: "var(--accent)", fontWeight: 600, fontSize: "0.875rem" }}>{formatPrice(s.price)}</span>
                            <button
                              type="button"
                              className="perfil-edit-button"
                              style={{ padding: "0.5rem 1rem", fontSize: "0.85rem", whiteSpace: "nowrap" }}
                              onClick={() => navigate(`/form/${s.id}`)}
                            >
                              Reservar turno
                            </button>
                          </div>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>
      </div>

      {showLogo && profile.logo_url && (
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
            src={profile.logo_url}
            alt={`Logo de ${profile.local_name}`}
            style={{ maxWidth: "90vw", maxHeight: "90vh", objectFit: "contain", borderRadius: "8px" }}
          />
        </div>
      )}
    </div>
  )
}

export default PublicLocalProfile
