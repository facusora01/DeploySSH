import { useEffect, useState, useMemo } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { api } from "../utils/api"
import type { Service } from "../types/service"
import type { WeeklyScheduleSlotOut, ScheduleBlockOut } from "../types/agenda"
import Icon from "../components/Icon"
import "./perfil.css"

const DAYS = [
  { value: 0, label: "Lunes" },
  { value: 1, label: "Martes" },
  { value: 2, label: "Miércoles" },
  { value: 3, label: "Jueves" },
  { value: 4, label: "Viernes" },
  { value: 5, label: "Sábado" },
  { value: 6, label: "Domingo" },
]

interface PublicProfileData {
  id: number
  full_name: string
  role: string
  phone: string | null
  specialty: string | null
  bio: string | null
  experience_years: number | null
  services?: Service[] | null
  weekly_schedule?: WeeklyScheduleSlotOut[] | null
  schedule_blocks?: ScheduleBlockOut[] | null
}
  
function PublicProfile() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [profile, setProfile] = useState<PublicProfileData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  const slotsByDay = useMemo(() => {
    const grouped: Record<number, WeeklyScheduleSlotOut[]> = {}
    for (const day of DAYS) grouped[day.value] = []
    if (profile?.weekly_schedule) {
      for (const slot of profile.weekly_schedule) {
        if (grouped[slot.day_of_week] !== undefined) {
          grouped[slot.day_of_week].push(slot)
        }
      }
    }
    for (const day in grouped) {
      grouped[day].sort((a, b) => a.start_time.slice(0, 5).localeCompare(b.start_time.slice(0, 5)))
    }
    return grouped
  }, [profile?.weekly_schedule])

  useEffect(() => {
    async function loadProfile() {
      try {
        const data = await api.get<PublicProfileData>(`/api/v1/users/${id}/public`, false)
        setProfile(data)
      } catch (err: any) {
        setError(err.response?.data?.detail || "No se pudo cargar el perfil.")
      } finally {
        setLoading(false)
      }
    }
    if (id) loadProfile()
  }, [id])

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
          <button className="perfil-edit-button" style={{ marginTop: "1rem" }} onClick={() => navigate(-1)}>Volver</button>
        </div>
      </div>
    )
  }

  const isProfesional = profile.role === "profesional"
  const roleLabel = isProfesional ? "Profesional" : "Cliente"
  const avatarEmoji = isProfesional ? "👨‍⚕️" : "👤"

  function formatPrice(rawPrice: string | null): string {
    if (rawPrice === null) return "Sin precio"
    const num = Number(rawPrice)
    if (isNaN(num)) return "Sin precio"
    return `$${num.toLocaleString("es-AR", { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`
  }

  function formatDuration(minutes: number): string {
    if (minutes < 60) return `${minutes} min`
    const h = Math.floor(minutes / 60)
    const m = minutes % 60
    return m === 0 ? `${h} h` : `${h} h ${m} min`
  }

  function formatBlockDates(startISO: string, endISO: string): string {
    if (startISO === endISO) return formatDate(startISO)
    return `${formatDate(startISO)} → ${formatDate(endISO)}`
  }

  function formatDate(iso: string): string {
    const [year, month, day] = iso.split("-").map(Number)
    const d = new Date(year, month - 1, day)
    return d.toLocaleDateString("es-AR", {
      day: "numeric",
      month: "short",
      year: "numeric",
    })
  }

  return (
    <div className="perfil-page">
      <div className="perfil-container">
        <header className="perfil-header">
          <div>
            <h1 className="perfil-title">Perfil de {profile.full_name}</h1>
            <p className="perfil-subtitle">{roleLabel}</p>
          </div>
          <button
            type="button"
            className="perfil-edit-button"
            onClick={() => navigate(-1)}
          >
            Volver
          </button>
        </header>

        <section className="perfil-card">
          <div className="perfil-avatar" aria-hidden="true">
            {avatarEmoji}
          </div>
          <div className="perfil-info">
            <div>
              <h2 className="perfil-name">{profile.full_name}</h2>
            </div>
            <dl className="perfil-fields">
              <div className="perfil-field">
                <dt className="perfil-field-label">Teléfono</dt>
                <dd className="perfil-field-value">{profile.phone || "No registrado"}</dd>
              </div>
              <div className="perfil-field">
                <dt className="perfil-field-label">Rol</dt>
                <dd className="perfil-field-value">{roleLabel}</dd>
              </div>
              {isProfesional && (
                <>
                  <div className="perfil-field">
                    <dt className="perfil-field-label">Especialidad</dt>
                    <dd className="perfil-field-value">{profile.specialty || "No registrada"}</dd>
                  </div>
                  {profile.experience_years !== null && (
                    <div className="perfil-field">
                      <dt className="perfil-field-label">Años de exp.</dt>
                      <dd className="perfil-field-value">{profile.experience_years}</dd>
                    </div>
                  )}
                  {profile.bio && (
                    <div className="perfil-field" style={{ gridColumn: "1 / -1" }}>
                      <dt className="perfil-field-label">Biografía</dt>
                      <dd className="perfil-field-value" style={{ whiteSpace: "pre-wrap" }}>{profile.bio}</dd>
                    </div>
                  )}
                  {profile.services && profile.services.length > 0 && (
                    <div style={{ gridColumn: "1 / -1", marginTop: "1rem" }}>
                      <h3 className="perfil-section-title">Servicios publicados</h3>
                      <ul className="perfil-services">
                        {profile.services.map((s) => (
                          <li key={s.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "1rem", flexWrap: "wrap" }}>
                            <div style={{ flex: "1 1 250px" }}>
                              <div className="perfil-service-meta">
                                <strong>{s.name}</strong>
                                <span>{formatPrice(s.price)}</span>
                              </div>
                              <div>
                                {s.description && <div className="perfil-service-description">{s.description}</div>}
                                <div className="perfil-service-duration">{formatDuration(s.duration_minutes)}</div>
                                {s.deposit_active && (
                                  <div className="perfil-service-deposit" style={{ marginTop: "0.5rem", fontSize: "0.85rem", color: "#666" }}>
                                    <Icon name="lock" size={12} style={{ marginRight: "0.25rem" }} />
                                    Seña: ${Number(s.deposit_amount || 0).toLocaleString("es-AR", {
                                      minimumFractionDigits: 0,
                                      maximumFractionDigits: 2,
                                    })} ({s.deposit_required ? "obligatoria" : "opcional"})
                                  </div>
                                )}
                              </div>
                            </div>
                            <button
                              type="button"
                              className="perfil-edit-button"
                              style={{ padding: "0.5rem 1rem", fontSize: "0.85rem", whiteSpace: "nowrap", alignSelf: "center" }}
                              onClick={() => navigate(`/form/${s.id}`)}
                            >
                              Reservar turno
                            </button>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* HORARIOS SEMANALES */}
                  <div className="perfil-agenda-section">
                    <h3 className="perfil-section-title">Horarios de atención</h3>
                    <div className="perfil-agenda-grid">
                      {DAYS.map((day) => {
                        const slots = slotsByDay[day.value]
                        return (
                          <div key={day.value} className="perfil-agenda-day-card">
                            <span className="perfil-agenda-day-name">{day.label}</span>
                            <div className="perfil-agenda-slots">
                              {slots.length === 0 ? (
                                <span className="perfil-agenda-empty">Sin horario</span>
                              ) : (
                                slots.map((slot) => (
                                  <span key={slot.id} className="perfil-agenda-slot">
                                    <Icon name="clock" size={12} />
                                    {slot.start_time.slice(0, 5)} — {slot.end_time.slice(0, 5)}
                                  </span>
                                ))
                              )}
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>

                  {/* BLOQUEOS / VACACIONES */}
                  {profile.schedule_blocks && profile.schedule_blocks.length > 0 && (
                    <div className="perfil-blocks-section">
                      <h3 className="perfil-section-title">Bloqueos de agenda (vacaciones/feriados)</h3>
                      <ul className="perfil-blocks-list">
                        {profile.schedule_blocks.map((block) => (
                          <li key={block.id} className="perfil-block-item">
                            <Icon name="calendar" size={16} />
                            <span className="perfil-block-dates">
                              {formatBlockDates(block.start_date, block.end_date)}
                            </span>
                            {block.reason && (
                              <>
                                <span>•</span>
                                <span className="perfil-block-reason">{block.reason}</span>
                              </>
                            )}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </>
              )}
            </dl>
          </div>
        </section>
      </div>
    </div>
  )
}

export default PublicProfile
