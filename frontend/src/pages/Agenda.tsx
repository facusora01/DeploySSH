import { useCallback, useEffect, useMemo, useState } from "react"
import { Navigate } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import { api, ApiError } from "../utils/api"
import type {
  AgendaConfigResponse,
  ScheduleBlockCreatePayload,
  ScheduleBlockOut,
} from "../types/agenda"
import Icon from "../components/Icon"
import BlockFormModal from "../components/BlockFormModal"
import "./agenda.css"

// Días de la semana en convención del back: 0=Lun ... 6=Dom (matchea date.weekday()).
const DAYS = [
  { value: 0, label: "Lunes" },
  { value: 1, label: "Martes" },
  { value: 2, label: "Miércoles" },
  { value: 3, label: "Jueves" },
  { value: 4, label: "Viernes" },
  { value: 5, label: "Sábado" },
  { value: 6, label: "Domingo" },
]

type Feedback = { type: "success" | "error"; text: string }

// Slot draft: lo que muestra el front. clientKey es para React; en slots
// existentes coincide con el UUID del back, en nuevos es un id temporal.
type DraftSlot = {
  clientKey: string
  day_of_week: number
  start_time: string // "HH:MM"
  end_time: string
}

// Estado del editor inline (qué slot estás editando + qué valores se van mostrando).
type SlotEdit = {
  clientKey: string
  start_time: string
  end_time: string
  isNew: boolean // si es nuevo: al cancelar, se borra del draft
}

function Agenda() {
  const { user } = useAuth()

  // Estado del server (snapshot del último GET exitoso)
  const [server, setServer] = useState<AgendaConfigResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState("")

  // Drafts (lo que el usuario está editando; se persiste con "Guardar")
  const [draftBuffer, setDraftBuffer] = useState(0)
  const [draftSlots, setDraftSlots] = useState<DraftSlot[]>([])
  const [editing, setEditing] = useState<SlotEdit | null>(null)

  // UI state
  const [blockModalOpen, setBlockModalOpen] = useState(false)
  const [feedback, setFeedback] = useState<Feedback | null>(null)
  const [saving, setSaving] = useState(false)
  const [togglingPause, setTogglingPause] = useState(false)

  // Resetea drafts desde el server (al cargar y al descartar cambios)
  const resetDraftsFromServer = useCallback((data: AgendaConfigResponse) => {
    setDraftBuffer(data.buffer_minutes)
    setDraftSlots(
      data.weekly_schedule.map((s) => ({
        clientKey: s.id,
        day_of_week: s.day_of_week,
        // Back devuelve "HH:MM:SS"; en el front usamos "HH:MM" para input type=time
        start_time: s.start_time.slice(0, 5),
        end_time: s.end_time.slice(0, 5),
      })),
    )
    setEditing(null)
  }, [])

  const refresh = useCallback(async () => {
    try {
      const data = await api.get<AgendaConfigResponse>("/api/v1/agenda", true)
      setServer(data)
      resetDraftsFromServer(data)
      setLoadError("")
    } catch (err) {
      setLoadError(
        err instanceof ApiError
          ? err.message
          : "No se pudo cargar la agenda.",
      )
    } finally {
      setLoading(false)
    }
  }, [resetDraftsFromServer])

  useEffect(() => {
    refresh()
  }, [refresh])

  useEffect(() => {
    if (feedback) {
      const timer = setTimeout(() => {
        setFeedback(null)
      }, 5000)
      return () => clearTimeout(timer)
    }
  }, [feedback])

  // Guards después de hooks
  if (!user) return null
  if (user.role !== "profesional") return <Navigate to="/" replace />

  // ──────────── Dirty check ────────────
  const bufferDirty = server ? draftBuffer !== server.buffer_minutes : false

  // eslint-disable-next-line react-hooks/rules-of-hooks
  const scheduleDirty = useMemo(() => {
    if (!server) return false
    const fingerprint = (s: { day_of_week: number; start_time: string; end_time: string }) =>
      `${s.day_of_week}|${s.start_time.slice(0, 5)}|${s.end_time.slice(0, 5)}`
    const draftFp = draftSlots.map(fingerprint).sort()
    const serverFp = server.weekly_schedule.map(fingerprint).sort()
    return JSON.stringify(draftFp) !== JSON.stringify(serverFp)
  }, [server, draftSlots])

  const isDirty = bufferDirty || scheduleDirty

  // ──────────── Save / Discard ────────────
  async function handleSave() {
    if (!server) return
    setSaving(true)
    setFeedback(null)
    try {
      // Settings se actualizan con PATCH parcial — solo si cambió el buffer.
      if (bufferDirty) {
        await api.patch(
          "/api/v1/agenda/settings",
          { buffer_minutes: draftBuffer },
          true,
        )
      }
      // Schedule se manda entero con PUT (el back reemplaza todo).
      if (scheduleDirty) {
        await api.put(
          "/api/v1/agenda/schedule",
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
      // El back devuelve 409 con detail descriptivo (ej: solapes).
      setFeedback({
        type: "error",
        text:
          err instanceof ApiError
            ? err.message
            : "No se pudo guardar la agenda.",
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

  // ──────────── Pause toggle (PATCH inmediato) ────────────
  async function handleTogglePause(nextValue: boolean) {
    if (!server) return
    setTogglingPause(true)
    setFeedback(null)
    // Optimistic update
    const previousValue = server.agenda_paused
    setServer({ ...server, agenda_paused: nextValue })
    try {
      await api.patch(
        "/api/v1/agenda/settings",
        { agenda_paused: nextValue },
        true,
      )
      setFeedback({
        type: "success",
        text: nextValue
          ? "Agenda pausada. No se aceptan nuevas reservas."
          : "Agenda activada.",
      })
    } catch (err) {
      // Rollback
      setServer({ ...server, agenda_paused: previousValue })
      setFeedback({
        type: "error",
        text:
          err instanceof ApiError
            ? err.message
            : "No se pudo cambiar el estado de la agenda.",
      })
    } finally {
      setTogglingPause(false)
    }
  }

  // ──────────── Slot editing ────────────
  function startEditingSlot(slot: DraftSlot) {
    setEditing({
      clientKey: slot.clientKey,
      start_time: slot.start_time,
      end_time: slot.end_time,
      isNew: false,
    })
  }

  function startAddingSlot(dayOfWeek: number) {
    const newKey = `new-${Date.now()}-${Math.random()}`
    const newSlot: DraftSlot = {
      clientKey: newKey,
      day_of_week: dayOfWeek,
      start_time: "09:00",
      end_time: "10:00",
    }
    setDraftSlots((prev) => [...prev, newSlot])
    setEditing({
      clientKey: newKey,
      start_time: "09:00",
      end_time: "10:00",
      isNew: true,
    })
  }

  function confirmEdit() {
    if (!editing) return
    if (editing.start_time >= editing.end_time) {
      setFeedback({
        type: "error",
        text: "El horario de inicio debe ser anterior al de fin.",
      })
      return
    }
    setDraftSlots((prev) =>
      prev.map((s) =>
        s.clientKey === editing.clientKey
          ? {
              ...s,
              start_time: editing.start_time,
              end_time: editing.end_time,
            }
          : s,
      ),
    )
    setEditing(null)
  }

  function cancelEdit() {
    if (!editing) return
    // Si era nuevo y nunca confirmó, lo borramos del draft.
    if (editing.isNew) {
      setDraftSlots((prev) =>
        prev.filter((s) => s.clientKey !== editing.clientKey),
      )
    }
    setEditing(null)
  }

  function deleteSlot(clientKey: string) {
    setDraftSlots((prev) => prev.filter((s) => s.clientKey !== clientKey))
    if (editing?.clientKey === clientKey) setEditing(null)
  }

  // ──────────── Slot grouping para render ────────────
  // eslint-disable-next-line react-hooks/rules-of-hooks
  const slotsByDay = useMemo(() => {
    const grouped: Record<number, DraftSlot[]> = {}
    for (const day of DAYS) grouped[day.value] = []
    for (const slot of draftSlots) {
      if (grouped[slot.day_of_week] !== undefined) {
        grouped[slot.day_of_week].push(slot)
      }
    }
    for (const day in grouped) {
      grouped[day].sort((a, b) => a.start_time.localeCompare(b.start_time))
    }
    return grouped
  }, [draftSlots])

  // ──────────── Bloqueos ────────────
  async function handleCreateBlock(payload: ScheduleBlockCreatePayload) {
    await api.post<ScheduleBlockOut>("/api/v1/agenda/blocks", payload, true)
    setFeedback({ type: "success", text: "Bloqueo creado." })
    await refresh()
  }

  async function handleDeleteBlock(block: ScheduleBlockOut) {
    const label = block.reason || formatBlockDates(block.start_date, block.end_date)
    if (!window.confirm(`¿Eliminar el bloqueo "${label}"?`)) return
    try {
      await api.delete(`/api/v1/agenda/blocks/${block.id}`, true)
      setFeedback({ type: "success", text: "Bloqueo eliminado." })
      await refresh()
    } catch (err) {
      setFeedback({
        type: "error",
        text:
          err instanceof ApiError
            ? err.message
            : "No se pudo eliminar el bloqueo.",
      })
    }
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

  // ──────────── Render ────────────
  if (loading) {
    return (
      <div className="agenda-page">
        <div className="agenda-container">
          <p className="agenda-loading">Cargando agenda...</p>
        </div>
      </div>
    )
  }

  if (loadError) {
    return (
      <div className="agenda-page">
        <div className="agenda-container">
          <div className="agenda-error">{loadError}</div>
        </div>
      </div>
    )
  }

  if (!server) return null

  return (
    <div className="agenda-page">
      <div className="agenda-container">
        {/* HEADER */}
        <header className="agenda-header">
          <div className="agenda-header-text">
            <h1 className="agenda-title">Mi agenda</h1>
            <p className="agenda-subtitle">
              Configurá tus horarios de atención y bloqueos.
            </p>
          </div>
          <div className="agenda-header-actions">
            {isDirty && (
              <button
                type="button"
                className="agenda-discard-button"
                onClick={handleDiscard}
                disabled={saving}
              >
                Descartar
              </button>
            )}
            <button
              type="button"
              className="agenda-save-button"
              onClick={handleSave}
              disabled={!isDirty || saving}
            >
              {saving
                ? "Guardando..."
                : isDirty
                  ? "Guardar cambios"
                  : "Sin cambios"}
            </button>
          </div>
        </header>

        {/* FEEDBACK */}
        {feedback && (
          <div
            className={`agenda-feedback agenda-feedback--${feedback.type}`}
            role="alert"
          >
            <Icon
              name={feedback.type === "success" ? "check" : "alert"}
              size={18}
            />
            <span className="agenda-feedback-text">{feedback.text}</span>
            <button
              type="button"
              className="agenda-feedback-close"
              onClick={() => setFeedback(null)}
              aria-label="Cerrar mensaje"
            >
              <Icon name="x" size={16} />
            </button>
          </div>
        )}

        {/* ESTADO */}
        <section className="agenda-section">
          <h2 className="agenda-section-title">Estado</h2>

          <div
            className={`agenda-pause-card ${server.agenda_paused ? "is-paused" : ""}`}
          >
            <div className="agenda-pause-info">
              <h3 className="agenda-pause-title">Pausar agenda</h3>
              <p className="agenda-pause-text">
                Mientras esté pausada no se aceptan nuevas reservas. Los
                turnos existentes se mantienen.
              </p>
            </div>
            <label className="agenda-switch">
              <input
                type="checkbox"
                checked={server.agenda_paused}
                onChange={(e) => handleTogglePause(e.target.checked)}
                disabled={togglingPause}
              />
              <span className="agenda-switch-track">
                <span className="agenda-switch-thumb" />
              </span>
              <span className="agenda-switch-label">
                {server.agenda_paused ? "Pausada" : "Activa"}
              </span>
            </label>
          </div>

          <div className="agenda-field-card">
            <div className="agenda-field-info">
              <h3 className="agenda-field-title">Tiempo entre turnos</h3>
              <p className="agenda-field-text">
                Minutos de descanso obligatorio entre cada turno.
              </p>
            </div>
            <div className="agenda-field-input">
              <input
                type="number"
                min={0}
                max={240}
                value={draftBuffer}
                onChange={(e) =>
                  setDraftBuffer(Math.max(0, Number(e.target.value) || 0))
                }
              />
              <span>min</span>
            </div>
          </div>
        </section>

        {/* HORARIOS SEMANALES */}
        <section className="agenda-section">
          <div className="agenda-section-block-header">
            <h2 className="agenda-section-title">Horarios semanales</h2>
            <p className="agenda-section-desc">
              Definí tus franjas horarias por día. Los días sin franja no se
              ofrecen a los clientes.
            </p>
          </div>

          <div className="agenda-week">
            {DAYS.map((day) => {
              const slots = slotsByDay[day.value]
              return (
                <div key={day.value} className="agenda-day-row">
                  <div className="agenda-day-name">{day.label}</div>
                  <div className="agenda-day-slots">
                    {slots.length === 0 && (
                      <span className="agenda-day-empty">
                        Sin horario
                      </span>
                    )}
                    {slots.map((slot) => {
                      const isEditing = editing?.clientKey === slot.clientKey
                      if (isEditing && editing) {
                        return (
                          <div
                            key={slot.clientKey}
                            className="agenda-slot-editor"
                          >
                            <input
                              type="time"
                              value={editing.start_time}
                              onChange={(e) =>
                                setEditing({
                                  ...editing,
                                  start_time: e.target.value,
                                })
                              }
                              autoFocus
                            />
                            <span className="agenda-slot-sep">—</span>
                            <input
                              type="time"
                              value={editing.end_time}
                              onChange={(e) =>
                                setEditing({
                                  ...editing,
                                  end_time: e.target.value,
                                })
                              }
                            />
                            <button
                              type="button"
                              className="agenda-slot-iconbtn agenda-slot-iconbtn--ok"
                              onClick={confirmEdit}
                              aria-label="Confirmar"
                              title="Confirmar"
                            >
                              <Icon name="check" size={14} />
                            </button>
                            <button
                              type="button"
                              className="agenda-slot-iconbtn agenda-slot-iconbtn--cancel"
                              onClick={cancelEdit}
                              aria-label="Cancelar"
                              title="Cancelar"
                            >
                              <Icon name="x" size={14} />
                            </button>
                          </div>
                        )
                      }
                      return (
                        <div
                          key={slot.clientKey}
                          className="agenda-slot-chip"
                          role="button"
                          tabIndex={0}
                          onClick={() => startEditingSlot(slot)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter" || e.key === " ") {
                              e.preventDefault()
                              startEditingSlot(slot)
                            }
                          }}
                          title="Editar franja"
                        >
                          <Icon name="clock" size={12} />
                          <span>
                            {slot.start_time} — {slot.end_time}
                          </span>
                          <button
                            type="button"
                            className="agenda-slot-chip-delete"
                            onClick={(e) => {
                              e.stopPropagation()
                              deleteSlot(slot.clientKey)
                            }}
                            aria-label={`Eliminar franja ${slot.start_time} a ${slot.end_time}`}
                          >
                            <Icon name="x" size={12} />
                          </button>
                        </div>
                      )
                    })}
                    <button
                      type="button"
                      className="agenda-day-add"
                      onClick={() => startAddingSlot(day.value)}
                      disabled={editing !== null}
                      title={
                        editing !== null
                          ? "Terminá de editar la franja actual"
                          : "Agregar franja"
                      }
                    >
                      <Icon name="plus" size={14} />
                      <span>agregar</span>
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        </section>

        {/* BLOQUEOS */}
        <section className="agenda-section">
          <div className="agenda-section-header">
            <div>
              <h2 className="agenda-section-title">Bloqueos</h2>
              <p className="agenda-section-desc">
                Fechas en las que no atendés: vacaciones, feriados, días
                puntuales.
              </p>
            </div>
            <button
              type="button"
              className="agenda-add-block-button"
              onClick={() => setBlockModalOpen(true)}
            >
              <Icon name="plus" size={16} />
              <span>Nuevo bloqueo</span>
            </button>
          </div>

          {server.schedule_blocks.length === 0 ? (
            <div className="agenda-blocks-empty">
              <Icon name="calendar" size={32} />
              <p>No tenés ningún bloqueo cargado.</p>
            </div>
          ) : (
            <ul className="agenda-blocks-list">
              {server.schedule_blocks.map((block) => (
                <li key={block.id} className="agenda-block">
                  <div className="agenda-block-icon" aria-hidden="true">
                    <Icon name="calendar" size={18} />
                  </div>
                  <div className="agenda-block-info">
                    <div className="agenda-block-dates">
                      {formatBlockDates(block.start_date, block.end_date)}
                    </div>
                    {block.reason && (
                      <div className="agenda-block-reason">{block.reason}</div>
                    )}
                  </div>
                  <button
                    type="button"
                    className="agenda-block-delete"
                    onClick={() => handleDeleteBlock(block)}
                    aria-label="Eliminar bloqueo"
                    title="Eliminar bloqueo"
                  >
                    <Icon name="trash" size={16} />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      <BlockFormModal
        open={blockModalOpen}
        onClose={() => setBlockModalOpen(false)}
        onSubmit={handleCreateBlock}
      />
    </div>
  )
}

export default Agenda