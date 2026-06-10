import { useEffect, useMemo, useState } from "react"
import { Navigate } from "react-router-dom"
import Icon from "../components/Icon"
import { useAuth } from "../context/AuthContext"
import { api, ApiError } from "../utils/api"
import "./clientes.css"

interface ClienteSummary {
  id: number
  email: string
  full_name: string
  phone: string | null
  last_appointment_at: string | null
  next_appointment_at: string | null
  appointments_count: number
  notes_count: number
}

interface ClienteAppointment {
  id: string
  service_id: string
  service_name: string
  start_time: string
  end_time: string
  status: string
  notes: string | null
  cancellation_reason: string | null
}

interface ClienteNote {
  id: string
  client_id: number
  profesional_id: number
  content: string
  created_at: string
  updated_at: string
}

interface ClienteProfile {
  id: number
  email: string
  full_name: string
  phone: string | null
  dni: string | null
  date_of_birth: string | null
  address: string | null
  city: string | null
  appointments: ClienteAppointment[]
  notes: ClienteNote[]
}

type Feedback = { type: "success" | "error"; message: string } | null

const statusLabel: Record<string, string> = {
  confirmed: "Confirmado",
  pending: "Pendiente",
  completed: "Completado",
  cancelled: "Cancelado",
  attended: "Asistió",
  no_show: "No asistió",
}

function formatDateTime(value: string | null) {
  if (!value) return "Sin fecha"
  const date = new Date(value)
  return date.toLocaleDateString("es-AR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

function formatShortDate(value: string | null) {
  if (!value) return "Sin turnos"
  return new Date(value).toLocaleDateString("es-AR", {
    day: "2-digit",
    month: "short",
  })
}

function getErrorMessage(error: unknown, fallback: string) {
  if (error instanceof ApiError) return error.message
  if (error instanceof Error) return error.message
  return fallback
}

function Clientes() {
  const { user } = useAuth()
  const [clients, setClients] = useState<ClienteSummary[]>([])
  const [selectedClientId, setSelectedClientId] = useState<number | null>(null)
  const [profile, setProfile] = useState<ClienteProfile | null>(null)
  const [loadingClients, setLoadingClients] = useState(true)
  const [loadingProfile, setLoadingProfile] = useState(false)
  const [error, setError] = useState("")
  const [feedback, setFeedback] = useState<Feedback>(null)
  const [newNote, setNewNote] = useState("")
  const [savingNote, setSavingNote] = useState(false)
  const [editingNoteId, setEditingNoteId] = useState<string | null>(null)
  const [editingContent, setEditingContent] = useState("")
  const [deletingNoteId, setDeletingNoteId] = useState<string | null>(null)

  const isProfesional = user?.role === "profesional"

  const selectedClient = useMemo(
    () => clients.find((client) => client.id === selectedClientId) ?? null,
    [clients, selectedClientId],
  )

  async function fetchClients() {
    setLoadingClients(true)
    setError("")
    try {
      const data = await api.get<ClienteSummary[]>("/api/v1/clientes/profesional", true)
      setClients(data)
      setSelectedClientId((current) => current ?? data[0]?.id ?? null)
    } catch (err) {
      setError(getErrorMessage(err, "No se pudieron cargar tus clientes."))
    } finally {
      setLoadingClients(false)
    }
  }

  async function fetchProfile(clientId: number) {
    setLoadingProfile(true)
    setError("")
    try {
      const data = await api.get<ClienteProfile>(`/api/v1/clientes/${clientId}/profile`, true)
      setProfile(data)
    } catch (err) {
      setProfile(null)
      setError(getErrorMessage(err, "No se pudo cargar el perfil del cliente."))
    } finally {
      setLoadingProfile(false)
    }
  }

  useEffect(() => {
    if (!isProfesional) return
    fetchClients()
  }, [isProfesional])

  useEffect(() => {
    if (!selectedClientId) {
      setProfile(null)
      return
    }
    fetchProfile(selectedClientId)
  }, [selectedClientId])

  if (!user) return null
  if (!isProfesional) return <Navigate to="/turnos" replace />

  async function handleCreateNote() {
    if (!profile || !newNote.trim()) return
    setSavingNote(true)
    setFeedback(null)
    try {
      await api.post(
        `/api/v1/clientes/${profile.id}/notes`,
        { content: newNote.trim() },
        true,
      )
      setNewNote("")
      await fetchProfile(profile.id)
      await fetchClients()
      setFeedback({ type: "success", message: "Nota agregada" })
    } catch (err) {
      setFeedback({
        type: "error",
        message: getErrorMessage(err, "No se pudo agregar la nota."),
      })
    } finally {
      setSavingNote(false)
    }
  }

  function startEditing(note: ClienteNote) {
    setEditingNoteId(note.id)
    setEditingContent(note.content)
    setFeedback(null)
  }

  async function handleUpdateNote(noteId: string) {
    if (!profile || !editingContent.trim()) return
    setSavingNote(true)
    setFeedback(null)
    try {
      await api.put(
        `/api/v1/clientes/${profile.id}/notes/${noteId}`,
        { content: editingContent.trim() },
        true,
      )
      setEditingNoteId(null)
      setEditingContent("")
      await fetchProfile(profile.id)
      setFeedback({ type: "success", message: "Nota actualizada" })
    } catch (err) {
      setFeedback({
        type: "error",
        message: getErrorMessage(err, "No se pudo actualizar la nota."),
      })
    } finally {
      setSavingNote(false)
    }
  }

  async function handleDeleteNote(noteId: string) {
    if (!profile) return
    setDeletingNoteId(noteId)
    setFeedback(null)
    try {
      await api.delete(`/api/v1/clientes/${profile.id}/notes/${noteId}`, true)
      await fetchProfile(profile.id)
      await fetchClients()
      setFeedback({ type: "success", message: "Nota eliminada" })
    } catch (err) {
      setFeedback({
        type: "error",
        message: getErrorMessage(err, "No se pudo eliminar la nota."),
      })
    } finally {
      setDeletingNoteId(null)
    }
  }

  return (
    <div className="clientes-page">
      <header className="clientes-header">
        <div>
          <h1 className="clientes-title">Clientes</h1>
          <p className="clientes-subtitle">Historial y notas privadas de atención</p>
        </div>
        <span className="clientes-count">{clients.length} clientes</span>
      </header>

      {error && (
        <div className="clientes-feedback clientes-feedback--error">
          <Icon name="alert-circle" size={18} />
          <span>{error}</span>
        </div>
      )}

      {loadingClients ? (
        <div className="clientes-loading">Cargando clientes...</div>
      ) : clients.length === 0 ? (
        <section className="clientes-empty">
          <div className="clientes-empty-icon">
            <Icon name="users" size={34} />
          </div>
          <h2 className="clientes-empty-title">Todavía no tenés clientes</h2>
          <p className="clientes-empty-text">
            Cuando una persona reserve un turno con vos, su perfil va a aparecer acá.
          </p>
        </section>
      ) : (
        <div className="clientes-layout">
          <aside className="clientes-sidebar" aria-label="Listado de clientes">
            {clients.map((client) => (
              <button
                key={client.id}
                className={`clientes-list-item ${client.id === selectedClientId ? "is-active" : ""}`}
                onClick={() => setSelectedClientId(client.id)}
              >
                <span className="clientes-list-main">
                  <span className="clientes-list-name">{client.full_name}</span>
                  <span className="clientes-list-contact">{client.phone ?? client.email}</span>
                </span>
                <span className="clientes-list-meta">
                  <span>{client.appointments_count} turnos</span>
                  <span>{client.notes_count} notas</span>
                </span>
              </button>
            ))}
          </aside>

          <main className="clientes-detail">
            {loadingProfile ? (
              <div className="clientes-loading">Cargando perfil...</div>
            ) : !profile || !selectedClient ? (
              <section className="clientes-empty clientes-empty--compact">
                <p className="clientes-empty-title">Seleccioná un cliente</p>
              </section>
            ) : (
              <>
                <section className="clientes-profile">
                  <div className="clientes-profile-main">
                    <h2 className="clientes-profile-name">{profile.full_name}</h2>
                    <div className="clientes-profile-contact">
                      <span>{profile.email}</span>
                      {profile.phone && <span>{profile.phone}</span>}
                    </div>
                  </div>
                  <div className="clientes-profile-stats">
                    <span>
                      <strong>{selectedClient.appointments_count}</strong>
                      turnos
                    </span>
                    <span>
                      <strong>{profile.notes.length}</strong>
                      notas
                    </span>
                  </div>
                </section>

                <section className="clientes-info-grid">
                  <div>
                    <span className="clientes-info-label">DNI</span>
                    <span className="clientes-info-value">{profile.dni ?? "Sin dato"}</span>
                  </div>
                  <div>
                    <span className="clientes-info-label">Nacimiento</span>
                    <span className="clientes-info-value">
                      {profile.date_of_birth ? formatShortDate(profile.date_of_birth) : "Sin dato"}
                    </span>
                  </div>
                  <div>
                    <span className="clientes-info-label">Ciudad</span>
                    <span className="clientes-info-value">{profile.city ?? "Sin dato"}</span>
                  </div>
                  <div>
                    <span className="clientes-info-label">Último turno</span>
                    <span className="clientes-info-value">
                      {formatShortDate(selectedClient.last_appointment_at)}
                    </span>
                  </div>
                  <div>
                    <span className="clientes-info-label">Próximo turno</span>
                    <span className="clientes-info-value">
                      {formatShortDate(selectedClient.next_appointment_at)}
                    </span>
                  </div>
                </section>

                <section className="clientes-section">
                  <div className="clientes-section-header">
                    <h3>Notas privadas</h3>
                    <span>Solo visibles para vos</span>
                  </div>

                  {feedback && (
                    <div className={`clientes-feedback clientes-feedback--${feedback.type}`}>
                      <Icon name={feedback.type === "success" ? "check-circle" : "alert-circle"} size={18} />
                      <span>{feedback.message}</span>
                    </div>
                  )}

                  <div className="clientes-note-form">
                    <textarea
                      value={newNote}
                      onChange={(event) => setNewNote(event.target.value)}
                      placeholder="Agregar preferencias, observaciones clínicas u otros datos útiles..."
                      rows={3}
                    />
                    <button
                      className="clientes-primary-button"
                      onClick={handleCreateNote}
                      disabled={savingNote || !newNote.trim()}
                    >
                      <Icon name="plus" size={16} />
                      Agregar nota
                    </button>
                  </div>

                  {profile.notes.length === 0 ? (
                    <p className="clientes-muted">No hay notas privadas para este cliente.</p>
                  ) : (
                    <div className="clientes-notes-list">
                      {profile.notes.map((note) => (
                        <article key={note.id} className="clientes-note">
                          {editingNoteId === note.id ? (
                            <>
                              <textarea
                                value={editingContent}
                                onChange={(event) => setEditingContent(event.target.value)}
                                rows={3}
                              />
                              <div className="clientes-note-actions">
                                <button
                                  className="clientes-secondary-button"
                                  onClick={() => setEditingNoteId(null)}
                                >
                                  Cancelar
                                </button>
                                <button
                                  className="clientes-primary-button"
                                  onClick={() => handleUpdateNote(note.id)}
                                  disabled={savingNote || !editingContent.trim()}
                                >
                                  <Icon name="check" size={15} />
                                  Guardar
                                </button>
                              </div>
                            </>
                          ) : (
                            <>
                              <p>{note.content}</p>
                              <div className="clientes-note-footer">
                                <span>{formatDateTime(note.updated_at)}</span>
                                <div className="clientes-note-actions">
                                  <button
                                    className="clientes-icon-button"
                                    onClick={() => startEditing(note)}
                                    aria-label="Editar nota"
                                    title="Editar nota"
                                  >
                                    <Icon name="pencil" size={15} />
                                  </button>
                                  <button
                                    className="clientes-icon-button clientes-icon-button--danger"
                                    onClick={() => handleDeleteNote(note.id)}
                                    disabled={deletingNoteId === note.id}
                                    aria-label="Eliminar nota"
                                    title="Eliminar nota"
                                  >
                                    <Icon name="trash" size={15} />
                                  </button>
                                </div>
                              </div>
                            </>
                          )}
                        </article>
                      ))}
                    </div>
                  )}
                </section>

                <section className="clientes-section">
                  <div className="clientes-section-header">
                    <h3>Historial de turnos</h3>
                    <span>Pasados y futuros con vos</span>
                  </div>
                  <div className="clientes-appointments">
                    {profile.appointments.map((appointment) => (
                      <div key={appointment.id} className="clientes-appointment-row">
                        <div className="clientes-appointment-main">
                          <span className="clientes-appointment-service">
                            {appointment.service_name}
                          </span>
                          <span className="clientes-appointment-date">
                            <Icon name="calendar" size={13} />
                            {formatDateTime(appointment.start_time)}
                          </span>
                          {appointment.notes && (
                            <span className="clientes-appointment-note">
                              {appointment.notes}
                            </span>
                          )}
                        </div>
                        <span className={`turno-status-badge turno-status--${appointment.status}`}>
                          {statusLabel[appointment.status] ?? appointment.status}
                        </span>
                      </div>
                    ))}
                  </div>
                </section>
              </>
            )}
          </main>
        </div>
      )}
    </div>
  )
}

export default Clientes
