import { useCallback, useEffect, useMemo, useState, type CSSProperties, type FormEvent } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import { api, ApiError } from "../utils/api"
import type { Service, ServiceCreatePayload, ServiceUpdatePayload } from "../types/service"
import type {
  AgendaConfigResponse,
  ScheduleBlockCreatePayload,
  ScheduleBlockOut,
  TeamScheduleBlockOut,
} from "../types/agenda"
import ServiceFormModal from "../components/ServiceFormModal"
import BlockFormModal from "../components/BlockFormModal"
import Icon from "../components/Icon"
import "./servicios.css"
import "./agenda.css"
import "./gestionar-profesional.css"

// ── Types ──────────────────────────────────────────────────────────────────

type Tab = "perfil" | "servicios" | "horarios"
type Feedback = { type: "success" | "error"; text: string }

interface BajaPreviewItem {
  id: string
  start_time: string
  service_name: string
  client_name: string
}

interface TeamMember {
  id: number
  full_name: string
  email: string
  specialty: string
  bio: string | null
  photo_url: string | null
}

// Agenda types
type DraftSlot = {
  clientKey: string
  day_of_week: number
  start_time: string
  end_time: string
}
type SlotEdit = {
  clientKey: string
  start_time: string
  end_time: string
  isNew: boolean
}

const DAYS = [
  { value: 0, label: "Lunes" },
  { value: 1, label: "Martes" },
  { value: 2, label: "Miércoles" },
  { value: 3, label: "Jueves" },
  { value: 4, label: "Viernes" },
  { value: 5, label: "Sábado" },
  { value: 6, label: "Domingo" },
]

// ── Main component ─────────────────────────────────────────────────────────

function GestionarProfesional() {
  const { profesionalId } = useParams<{ profesionalId: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()

  const [member, setMember] = useState<TeamMember | null>(null)
  const [loadError, setLoadError] = useState("")
  const [tab, setTab] = useState<Tab>("perfil")

  const base = `/api/v1/locales/me/profesionales/${profesionalId}`

  const loadMember = useCallback(async () => {
    setLoadError("")
    try {
      const data = await api.get<TeamMember>(base, true)
      setMember(data)
    } catch (err) {
      setLoadError(
        err instanceof ApiError ? err.message : "No se pudo cargar el profesional.",
      )
    }
  }, [base])

  useEffect(() => {
    if (user?.role === "local") loadMember()
  }, [user, loadMember])

  if (!user) return null
  if (user.role !== "local") {
    navigate("/", { replace: true })
    return null
  }

  if (loadError) {
    return (
      <div className="gp-page">
        <div className="gp-container">
          <button type="button" className="gp-back" onClick={() => navigate("/equipo")}>
            ← Volver al equipo
          </button>
          <div className="gp-load-error">{loadError}</div>
        </div>
      </div>
    )
  }

  if (!member) {
    return (
      <div className="gp-page">
        <div className="gp-container">
          <p className="gp-loading">Cargando...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="gp-page">
      <div className="gp-container">
        {/* Header */}
        <div className="gp-header">
          <button type="button" className="gp-back" onClick={() => navigate("/equipo")}>
            ← Volver al equipo
          </button>
          <div className="gp-header-info">
            {member.photo_url ? (
              <img src={member.photo_url} alt={member.full_name} className="gp-avatar" />
            ) : (
              <div className="gp-avatar gp-avatar--placeholder">
                {member.full_name.charAt(0).toUpperCase()}
              </div>
            )}
            <div>
              <h1 className="gp-name">{member.full_name}</h1>
              <p className="gp-specialty">{member.specialty}</p>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="gp-tabs" role="tablist">
          {(["perfil", "servicios", "horarios"] as Tab[]).map((t) => (
            <button
              key={t}
              type="button"
              role="tab"
              aria-selected={tab === t}
              className={`gp-tab${tab === t ? " gp-tab--active" : ""}`}
              onClick={() => setTab(t)}
            >
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>

        {/* Tab panels */}
        {tab === "perfil" && (
          <TabPerfil member={member} base={base} onSaved={loadMember} />
        )}
        {tab === "servicios" && (
          <TabServicios base={base} />
        )}
        {tab === "horarios" && (
          <TabHorarios base={base} />
        )}
      </div>
    </div>
  )
}

// ── Tab Perfil ─────────────────────────────────────────────────────────────

function TabPerfil({
  member,
  base,
  onSaved,
}: {
  member: TeamMember
  base: string
  onSaved: () => Promise<void>
}) {
  const navigate = useNavigate()
  const [specialty, setSpecialty] = useState(member.specialty)
  const [bio, setBio] = useState(member.bio ?? "")
  const [photoUrl, setPhotoUrl] = useState(member.photo_url ?? "")
  const [saving, setSaving] = useState(false)
  const [feedback, setFeedback] = useState<Feedback | null>(null)

  // Baja state
  const [showBajaModal, setShowBajaModal] = useState(false)
  const [bajaPreview, setBajaPreview] = useState<BajaPreviewItem[]>([])
  const [bajaConfirming, setBajaConfirming] = useState(false)
  const [bajaError, setBajaError] = useState("")

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setSaving(true)
    setFeedback(null)
    try {
      await api.patch(
        base,
        {
          specialty: specialty.trim() || undefined,
          bio: bio.trim() || null,
          photo_url: photoUrl.trim() || null,
        },
        true,
      )
      setFeedback({ type: "success", text: "Perfil actualizado." })
      await onSaved()
    } catch (err) {
      setFeedback({
        type: "error",
        text: err instanceof ApiError ? err.message : "No se pudo guardar.",
      })
    } finally {
      setSaving(false)
    }
  }

  async function handleDarDeBaja() {
    setBajaError("")
    try {
      const preview = await api.get<{ future_count: number; appointments: BajaPreviewItem[] }>(
        `${base}/baja-preview`,
        true,
      )
      if (preview.future_count === 0) {
        if (!window.confirm(`¿Dar de baja a ${member.full_name}? Perderá el vínculo con el local.`)) return
        await executeBaja()
      } else {
        setBajaPreview(preview.appointments)
        setShowBajaModal(true)
      }
    } catch (err) {
      setBajaError(err instanceof ApiError ? err.message : "No se pudo obtener la vista previa.")
    }
  }

  async function executeBaja() {
    setBajaConfirming(true)
    try {
      await api.delete(base, true)
      navigate("/equipo")
    } catch (err) {
      setBajaError(err instanceof ApiError ? err.message : "No se pudo dar de baja al profesional.")
      setShowBajaModal(false)
    } finally {
      setBajaConfirming(false)
    }
  }

  return (
    <div className="gp-panel">
      <form onSubmit={handleSubmit} className="gp-form">
        <div className="gp-form-group">
          <label className="gp-form-label" htmlFor="gp-specialty">
            Especialidad <span aria-hidden="true">*</span>
          </label>
          <input
            id="gp-specialty"
            type="text"
            className="auth-input"
            value={specialty}
            onChange={(e) => setSpecialty(e.target.value)}
            required
            minLength={2}
          />
        </div>

        <div className="gp-form-group">
          <label className="gp-form-label" htmlFor="gp-bio">
            Descripción
          </label>
          <textarea
            id="gp-bio"
            className="gp-textarea"
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            rows={4}
            placeholder="Breve descripción del profesional..."
          />
        </div>

        <div className="gp-form-group">
          <label className="gp-form-label" htmlFor="gp-photo">
            URL de foto
          </label>
          <input
            id="gp-photo"
            type="url"
            className="auth-input"
            value={photoUrl}
            onChange={(e) => setPhotoUrl(e.target.value)}
            placeholder="https://..."
          />
          {photoUrl && (
            <img src={photoUrl} alt="Vista previa" className="gp-photo-preview" />
          )}
        </div>

        {feedback && (
          <div
            className={`gp-feedback gp-feedback--${feedback.type}`}
            role="alert"
          >
            {feedback.text}
          </div>
        )}

        <button type="submit" className="perfil-edit-button" disabled={saving}>
          {saving ? "Guardando..." : "Guardar cambios"}
        </button>

        <div className="gp-danger-zone">
          <p className="gp-danger-desc">
            Dar de baja desvincula al profesional del local y cancela sus turnos futuros. Esta acción no se puede deshacer.
          </p>
          <button
            type="button"
            className="gp-danger-button"
            onClick={handleDarDeBaja}
            disabled={bajaConfirming}
          >
            Dar de baja
          </button>
        </div>

        {bajaError && (
          <div className="gp-feedback gp-feedback--error" role="alert">
            {bajaError}
          </div>
        )}
      </form>

      <BajaModal
        open={showBajaModal}
        memberName={member.full_name}
        appointments={bajaPreview}
        confirming={bajaConfirming}
        onClose={() => setShowBajaModal(false)}
        onConfirm={executeBaja}
      />
    </div>
  )
}

// ── Tab Servicios ──────────────────────────────────────────────────────────

function TabServicios({ base }: { base: string }) {
  const [services, setServices] = useState<Service[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState("")
  const [modalOpen, setModalOpen] = useState(false)
  const [editingService, setEditingService] = useState<Service | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<Feedback | null>(null)

  const servicesUrl = `${base}/services`

  const loadServices = useCallback(async () => {
    setLoading(true)
    setLoadError("")
    try {
      const data = await api.get<Service[]>(servicesUrl, true)
      setServices(data)
    } catch (err) {
      setLoadError(
        err instanceof ApiError ? err.message : "No se pudieron cargar los servicios.",
      )
    } finally {
      setLoading(false)
    }
  }, [servicesUrl])

  useEffect(() => {
    loadServices()
  }, [loadServices])

  async function handleSubmit(payload: ServiceCreatePayload | ServiceUpdatePayload) {
    if (editingService) {
      await api.patch<Service>(`${servicesUrl}/${editingService.id}`, payload, true)
      setFeedback({ type: "success", text: "Servicio actualizado." })
    } else {
      await api.post<Service>(servicesUrl, payload, true)
      setFeedback({ type: "success", text: "Servicio creado." })
    }
    setModalOpen(false)
    await loadServices()
  }

  async function handleDelete(service: Service) {
    if (!window.confirm(`¿Eliminar el servicio "${service.name}"?`)) return
    setDeletingId(service.id)
    setFeedback(null)
    try {
      await api.delete(`${servicesUrl}/${service.id}`, true)
      setFeedback({ type: "success", text: "Servicio eliminado." })
      await loadServices()
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setFeedback({
          type: "error",
          text: "Este servicio tiene turnos futuros. Cancelalos antes de eliminarlo.",
        })
      } else {
        setFeedback({
          type: "error",
          text: err instanceof ApiError ? err.message : "No se pudo eliminar el servicio.",
        })
      }
    } finally {
      setDeletingId(null)
    }
  }

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

  return (
    <div className="gp-panel">
      <div className="servicios-header" style={{ marginBottom: "1rem" }}>
        <div className="servicios-header-text">
          <h2 className="servicios-title" style={{ fontSize: "1.1rem" }}>Servicios</h2>
          {services.length > 0 && (
            <span className="servicios-count" aria-live="polite">
              {services.length} {services.length === 1 ? "servicio activo" : "servicios activos"}
            </span>
          )}
        </div>
        <button
          type="button"
          className="servicios-create-button"
          onClick={() => { setEditingService(null); setModalOpen(true) }}
        >
          <Icon name="plus" size={16} />
          <span>Nuevo servicio</span>
        </button>
      </div>

      {feedback && (
        <div className={`servicios-feedback servicios-feedback--${feedback.type}`} role="alert">
          <Icon name={feedback.type === "success" ? "check" : "alert"} size={18} />
          <span className="servicios-feedback-text">{feedback.text}</span>
          <button type="button" className="servicios-feedback-close" onClick={() => setFeedback(null)} aria-label="Cerrar mensaje">
            <Icon name="x" size={16} />
          </button>
        </div>
      )}

      {loading && <p className="servicios-loading">Cargando servicios...</p>}

      {!loading && loadError && (
        <div className="servicios-error" role="alert">{loadError}</div>
      )}

      {!loading && !loadError && services.length === 0 && (
        <div className="servicios-empty">
          <div className="servicios-empty-icon" aria-hidden="true">
            <Icon name="wrench" size={36} />
          </div>
          <h3 className="servicios-empty-title">Este profesional no tiene servicios</h3>
          <p className="servicios-empty-text">Creá el primer servicio para que sus clientes puedan reservar.</p>
          <button type="button" className="servicios-create-button" onClick={() => { setEditingService(null); setModalOpen(true) }}>
            <Icon name="plus" size={16} />
            <span>Crear primer servicio</span>
          </button>
        </div>
      )}

      {!loading && !loadError && services.length > 0 && (
        <ul className="servicios-grid">
          {services.map((service, index) => (
            <li key={service.id} className="servicios-card" style={{ "--i": index } as CSSProperties}>
              <div className="servicios-card-header">
                <h3 className="servicios-card-name">{service.name}</h3>
                <div className="servicios-card-actions">
                  <button type="button" className="servicios-icon-button" onClick={() => { setEditingService(service); setModalOpen(true) }} aria-label={`Editar ${service.name}`} title="Editar">
                    <Icon name="pencil" size={16} />
                  </button>
                  <button type="button" className="servicios-icon-button servicios-icon-button--danger" onClick={() => handleDelete(service)} disabled={deletingId === service.id} aria-label={`Eliminar ${service.name}`} title="Eliminar">
                    <Icon name="trash" size={16} />
                  </button>
                </div>
              </div>
              {service.description && <p className="servicios-card-description">{service.description}</p>}
              <ul className="servicios-card-meta">
                <li><Icon name="clock" size={14} /><span>{formatDuration(service.duration_minutes)}</span></li>
                <li><Icon name="banknote" size={14} /><span>{formatPrice(service.price)}</span></li>
                <li><Icon name="users" size={14} /><span>Cupo {service.max_slots}</span></li>
                {service.deposit_active && (
                  <li>
                    <Icon name="lock" size={14} />
                    <span>
                      Seña: ${Number(service.deposit_amount || 0).toLocaleString("es-AR", { minimumFractionDigits: 0, maximumFractionDigits: 2 })}
                      {service.deposit_required ? " (Obligatoria)" : " (Opcional)"}
                    </span>
                  </li>
                )}
              </ul>
            </li>
          ))}
        </ul>
      )}

      <ServiceFormModal
        open={modalOpen}
        initialService={editingService}
        onClose={() => setModalOpen(false)}
        onSubmit={handleSubmit}
      />
    </div>
  )
}

// ── Tab Horarios ───────────────────────────────────────────────────────────

function TabHorarios({ base }: { base: string }) {
  const agendaBase = `${base}/agenda`

  const [server, setServer] = useState<AgendaConfigResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState("")
  const [draftBuffer, setDraftBuffer] = useState(0)
  const [draftSlots, setDraftSlots] = useState<DraftSlot[]>([])
  const [editing, setEditing] = useState<SlotEdit | null>(null)
  const [blockModalOpen, setBlockModalOpen] = useState(false)
  const [feedback, setFeedback] = useState<Feedback | null>(null)
  const [saving, setSaving] = useState(false)
  const [togglingPause, setTogglingPause] = useState(false)

  const resetDraftsFromServer = useCallback((data: AgendaConfigResponse) => {
    setDraftBuffer(data.buffer_minutes)
    setDraftSlots(
      data.weekly_schedule.map((s) => ({
        clientKey: s.id,
        day_of_week: s.day_of_week,
        start_time: s.start_time.slice(0, 5),
        end_time: s.end_time.slice(0, 5),
      })),
    )
    setEditing(null)
  }, [])

  const refresh = useCallback(async () => {
    try {
      const data = await api.get<AgendaConfigResponse>(agendaBase, true)
      setServer(data)
      resetDraftsFromServer(data)
      setLoadError("")
    } catch (err) {
      setLoadError(
        err instanceof ApiError ? err.message : "No se pudo cargar la agenda.",
      )
    } finally {
      setLoading(false)
    }
  }, [agendaBase, resetDraftsFromServer])

  useEffect(() => {
    refresh()
  }, [refresh])

  useEffect(() => {
    if (feedback) {
      const timer = setTimeout(() => setFeedback(null), 5000)
      return () => clearTimeout(timer)
    }
  }, [feedback])

  const bufferDirty = server ? draftBuffer !== server.buffer_minutes : false

  const scheduleDirty = useMemo(() => {
    if (!server) return false
    const fp = (s: { day_of_week: number; start_time: string; end_time: string }) =>
      `${s.day_of_week}|${s.start_time.slice(0, 5)}|${s.end_time.slice(0, 5)}`
    return JSON.stringify(draftSlots.map(fp).sort()) !== JSON.stringify(server.weekly_schedule.map(fp).sort())
  }, [server, draftSlots])

  const isDirty = bufferDirty || scheduleDirty

  async function handleSave() {
    if (!server) return
    setSaving(true)
    setFeedback(null)
    try {
      if (bufferDirty) {
        await api.patch(`${agendaBase}/settings`, { buffer_minutes: draftBuffer }, true)
      }
      if (scheduleDirty) {
        await api.put(
          `${agendaBase}/schedule`,
          {
            slots: draftSlots.map((s) => ({
              day_of_week: s.day_of_week,
              start_time: `${s.start_time}:00`,
              end_time: `${s.end_time}:00`,
            })),
          },
          true,
        )
      }
      await refresh()
      setFeedback({ type: "success", text: "Agenda guardada." })
    } catch (err) {
      setFeedback({
        type: "error",
        text: err instanceof ApiError ? err.message : "No se pudo guardar la agenda.",
      })
    } finally {
      setSaving(false)
    }
  }

  function handleDiscard() {
    if (!server) return
    resetDraftsFromServer(server)
    setFeedback(null)
  }

  async function handleTogglePause(nextValue: boolean) {
    if (!server) return
    setTogglingPause(true)
    setFeedback(null)
    const prev = server.agenda_paused
    setServer({ ...server, agenda_paused: nextValue })
    try {
      await api.patch(`${agendaBase}/settings`, { agenda_paused: nextValue }, true)
      setFeedback({
        type: "success",
        text: nextValue ? "Agenda pausada." : "Agenda activada.",
      })
    } catch (err) {
      setServer({ ...server, agenda_paused: prev })
      setFeedback({
        type: "error",
        text: err instanceof ApiError ? err.message : "No se pudo cambiar el estado.",
      })
    } finally {
      setTogglingPause(false)
    }
  }

  function startEditingSlot(slot: DraftSlot) {
    setEditing({ clientKey: slot.clientKey, start_time: slot.start_time, end_time: slot.end_time, isNew: false })
  }

  function startAddingSlot(dayOfWeek: number) {
    const newKey = `new-${Date.now()}-${Math.random()}`
    setDraftSlots((prev) => [...prev, { clientKey: newKey, day_of_week: dayOfWeek, start_time: "09:00", end_time: "10:00" }])
    setEditing({ clientKey: newKey, start_time: "09:00", end_time: "10:00", isNew: true })
  }

  function confirmEdit() {
    if (!editing) return
    if (editing.start_time >= editing.end_time) {
      setFeedback({ type: "error", text: "El horario de inicio debe ser anterior al de fin." })
      return
    }
    setDraftSlots((prev) =>
      prev.map((s) =>
        s.clientKey === editing.clientKey
          ? { ...s, start_time: editing.start_time, end_time: editing.end_time }
          : s,
      ),
    )
    setEditing(null)
  }

  function cancelEdit() {
    if (!editing) return
    if (editing.isNew) setDraftSlots((prev) => prev.filter((s) => s.clientKey !== editing.clientKey))
    setEditing(null)
  }

  function deleteSlot(clientKey: string) {
    setDraftSlots((prev) => prev.filter((s) => s.clientKey !== clientKey))
    if (editing?.clientKey === clientKey) setEditing(null)
  }

  const slotsByDay = useMemo(() => {
    const grouped: Record<number, DraftSlot[]> = {}
    for (const day of DAYS) grouped[day.value] = []
    for (const slot of draftSlots) {
      if (grouped[slot.day_of_week] !== undefined) grouped[slot.day_of_week].push(slot)
    }
    for (const day in grouped) grouped[day].sort((a, b) => a.start_time.localeCompare(b.start_time))
    return grouped
  }, [draftSlots])

  async function handleCreateBlock(payload: ScheduleBlockCreatePayload) {
    const result = await api.post<TeamScheduleBlockOut>(`${agendaBase}/blocks`, payload, true)
    setFeedback({
      type: "success",
      text:
        result.cancelled_count > 0
          ? `Bloqueo creado. Se cancel${
              result.cancelled_count === 1 ? "ó" : "aron"
            } ${result.cancelled_count} turno${
              result.cancelled_count === 1 ? "" : "s"
            }.`
          : "Bloqueo creado.",
    })
    await refresh()
  }

  async function handleDeleteBlock(block: ScheduleBlockOut) {
    const label = block.reason || formatBlockDates(block.start_date, block.end_date)
    if (!window.confirm(`¿Eliminar el bloqueo "${label}"?`)) return
    try {
      await api.delete(`${agendaBase}/blocks/${block.id}`, true)
      setFeedback({ type: "success", text: "Bloqueo eliminado." })
      await refresh()
    } catch (err) {
      setFeedback({
        type: "error",
        text: err instanceof ApiError ? err.message : "No se pudo eliminar el bloqueo.",
      })
    }
  }

  function formatBlockDates(startISO: string, endISO: string): string {
    if (startISO === endISO) return formatDate(startISO)
    return `${formatDate(startISO)} → ${formatDate(endISO)}`
  }

  function formatDate(iso: string): string {
    const [year, month, day] = iso.split("-").map(Number)
    return new Date(year, month - 1, day).toLocaleDateString("es-AR", {
      day: "numeric",
      month: "short",
      year: "numeric",
    })
  }

  if (loading) return <div className="gp-panel gp-panel--horarios"><p className="agenda-loading">Cargando agenda...</p></div>
  if (loadError) return <div className="gp-panel gp-panel--horarios"><div className="agenda-error">{loadError}</div></div>
  if (!server) return null

  return (
    <div className="gp-panel gp-panel--horarios">
      {/* Header con guardar/descartar */}
      <div className="agenda-header" style={{ marginBottom: "1.25rem" }}>
        <div className="agenda-header-text">
          <h2 className="agenda-title" style={{ fontSize: "1.1rem" }}>Horarios</h2>
        </div>
        <div className="agenda-header-actions">
          {isDirty && (
            <button type="button" className="agenda-discard-button" onClick={handleDiscard} disabled={saving}>
              Descartar
            </button>
          )}
          <button type="button" className="agenda-save-button" onClick={handleSave} disabled={!isDirty || saving}>
            {saving ? "Guardando..." : isDirty ? "Guardar cambios" : "Sin cambios"}
          </button>
        </div>
      </div>

      {feedback && (
        <div className={`agenda-feedback agenda-feedback--${feedback.type}`} role="alert">
          <Icon name={feedback.type === "success" ? "check" : "alert"} size={18} />
          <span className="agenda-feedback-text">{feedback.text}</span>
          <button type="button" className="agenda-feedback-close" onClick={() => setFeedback(null)} aria-label="Cerrar mensaje">
            <Icon name="x" size={16} />
          </button>
        </div>
      )}

      {/* Estado */}
      <section className="agenda-section">
        <h2 className="agenda-section-title">Estado</h2>
        <div className={`agenda-pause-card ${server.agenda_paused ? "is-paused" : ""}`}>
          <div className="agenda-pause-info">
            <h3 className="agenda-pause-title">Pausar agenda</h3>
            <p className="agenda-pause-text">
              Mientras esté pausada no se aceptan nuevas reservas.
            </p>
          </div>
          <label className="agenda-switch">
            <input
              type="checkbox"
              checked={server.agenda_paused}
              onChange={(e) => handleTogglePause(e.target.checked)}
              disabled={togglingPause}
            />
            <span className="agenda-switch-track"><span className="agenda-switch-thumb" /></span>
            <span className="agenda-switch-label">{server.agenda_paused ? "Pausada" : "Activa"}</span>
          </label>
        </div>

        <div className="agenda-field-card">
          <div className="agenda-field-info">
            <h3 className="agenda-field-title">Tiempo entre turnos</h3>
            <p className="agenda-field-text">Minutos de descanso entre cada turno.</p>
          </div>
          <div className="agenda-field-input">
            <input
              type="number"
              min={0}
              max={240}
              value={draftBuffer}
              onChange={(e) => setDraftBuffer(Math.max(0, Number(e.target.value) || 0))}
            />
            <span>min</span>
          </div>
        </div>
      </section>

      {/* Horarios semanales */}
      <section className="agenda-section">
        <div className="agenda-section-block-header">
          <h2 className="agenda-section-title">Horarios semanales</h2>
          <p className="agenda-section-desc">Franjas horarias por día. Los días sin franja no se ofrecen a los clientes.</p>
        </div>
        <div className="agenda-week">
          {DAYS.map((day) => {
            const slots = slotsByDay[day.value]
            return (
              <div key={day.value} className="agenda-day-row">
                <div className="agenda-day-name">{day.label}</div>
                <div className="agenda-day-slots">
                  {slots.length === 0 && <span className="agenda-day-empty">Sin horario</span>}
                  {slots.map((slot) => {
                    const isEditing = editing?.clientKey === slot.clientKey
                    if (isEditing && editing) {
                      return (
                        <div key={slot.clientKey} className="agenda-slot-editor">
                          <input type="time" value={editing.start_time} onChange={(e) => setEditing({ ...editing, start_time: e.target.value })} autoFocus />
                          <span className="agenda-slot-sep">—</span>
                          <input type="time" value={editing.end_time} onChange={(e) => setEditing({ ...editing, end_time: e.target.value })} />
                          <button type="button" className="agenda-slot-iconbtn agenda-slot-iconbtn--ok" onClick={confirmEdit} aria-label="Confirmar"><Icon name="check" size={14} /></button>
                          <button type="button" className="agenda-slot-iconbtn agenda-slot-iconbtn--cancel" onClick={cancelEdit} aria-label="Cancelar"><Icon name="x" size={14} /></button>
                        </div>
                      )
                    }
                    return (
                      <div key={slot.clientKey} className="agenda-slot-chip" role="button" tabIndex={0} onClick={() => startEditingSlot(slot)} onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); startEditingSlot(slot) } }} title="Editar franja">
                        <Icon name="clock" size={12} />
                        <span>{slot.start_time} — {slot.end_time}</span>
                        <button type="button" className="agenda-slot-chip-delete" onClick={(e) => { e.stopPropagation(); deleteSlot(slot.clientKey) }} aria-label={`Eliminar franja ${slot.start_time} a ${slot.end_time}`}>
                          <Icon name="x" size={12} />
                        </button>
                      </div>
                    )
                  })}
                  <button type="button" className="agenda-day-add" onClick={() => startAddingSlot(day.value)} disabled={editing !== null} title={editing !== null ? "Terminá de editar la franja actual" : "Agregar franja"}>
                    <Icon name="plus" size={14} />
                    <span>agregar</span>
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      </section>

      {/* Bloqueos */}
      <section className="agenda-section">
        <div className="agenda-section-header">
          <div>
            <h2 className="agenda-section-title">Bloqueos</h2>
            <p className="agenda-section-desc">Vacaciones, feriados, días no laborables.</p>
          </div>
          <button type="button" className="agenda-add-block-button" onClick={() => setBlockModalOpen(true)}>
            <Icon name="plus" size={16} />
            <span>Nuevo bloqueo</span>
          </button>
        </div>
        {server.schedule_blocks.length === 0 ? (
          <div className="agenda-blocks-empty"><Icon name="calendar" size={32} /><p>No hay bloqueos cargados.</p></div>
        ) : (
          <ul className="agenda-blocks-list">
            {server.schedule_blocks.map((block) => (
              <li key={block.id} className="agenda-block">
                <div className="agenda-block-icon" aria-hidden="true"><Icon name="calendar" size={18} /></div>
                <div className="agenda-block-info">
                  <div className="agenda-block-dates">{formatBlockDates(block.start_date, block.end_date)}</div>
                  {block.reason && <div className="agenda-block-reason">{block.reason}</div>}
                </div>
                <button type="button" className="agenda-block-delete" onClick={() => handleDeleteBlock(block)} aria-label="Eliminar bloqueo" title="Eliminar bloqueo">
                  <Icon name="trash" size={16} />
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      <BlockFormModal
        open={blockModalOpen}
        onClose={() => setBlockModalOpen(false)}
        onSubmit={handleCreateBlock}
      />
    </div>
  )
}

// ── Helpers ────────────────────────────────────────────────────────────────

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("es-AR", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

// ── BajaModal ──────────────────────────────────────────────────────────────

function BajaModal({
  open,
  memberName,
  appointments,
  confirming,
  onClose,
  onConfirm,
}: {
  open: boolean
  memberName: string
  appointments: BajaPreviewItem[]
  confirming: boolean
  onClose: () => void
  onConfirm: () => void
}) {
  if (!open) return null
  return (
    <div className="agenda-modal-backdrop" onClick={onClose}>
      <div className="agenda-modal" onClick={(e) => e.stopPropagation()}>
        <header className="agenda-modal-header">
          <h2>Dar de baja a {memberName}</h2>
          <button type="button" onClick={onClose} aria-label="Cerrar">×</button>
        </header>
        <div className="agenda-modal-body">
          <p>
            Este profesional tiene <strong>{appointments.length} turno(s) futuro(s)</strong> que serán cancelados:
          </p>
          <ul style={{ margin: "0.75rem 0", paddingLeft: "1.25rem", display: "flex", flexDirection: "column", gap: "0.3rem" }}>
            {appointments.map((a) => (
              <li key={a.id} style={{ fontSize: "0.88rem" }}>
                {formatDateTime(a.start_time)} — {a.service_name} ({a.client_name})
              </li>
            ))}
          </ul>
          <p style={{ fontSize: "0.88rem", color: "var(--muted, #888)" }}>
            Los clientes serán notificados automáticamente.
          </p>
        </div>
        <footer className="agenda-modal-footer">
          <button type="button" className="agenda-modal-cancel" onClick={onClose}>
            Cancelar
          </button>
          <button
            type="button"
            className="gp-danger-button"
            onClick={onConfirm}
            disabled={confirming}
          >
            {confirming ? "Procesando..." : "Confirmar baja"}
          </button>
        </footer>
      </div>
    </div>
  )
}

export default GestionarProfesional
