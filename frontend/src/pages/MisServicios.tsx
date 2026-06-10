import { useCallback, useEffect, useState, type CSSProperties } from "react"
import { Navigate } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import { api, ApiError } from "../utils/api"
import type {
  Service,
  ServiceCreatePayload,
  ServiceUpdatePayload,
} from "../types/service"
import ServiceFormModal from "../components/ServiceFormModal"
import Icon from "../components/Icon"
import "./servicios.css"

type Feedback = { type: "success" | "error"; text: string }

function MisServicios() {
  const { user } = useAuth()
  const [services, setServices] = useState<Service[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState("")
  const [modalOpen, setModalOpen] = useState(false)
  const [editingService, setEditingService] = useState<Service | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<Feedback | null>(null)

  const loadServices = useCallback(async () => {
    setLoading(true)
    setLoadError("")
    try {
      const data = await api.get<Service[]>("/api/v1/services", true)
      setServices(data)
    } catch (err) {
      setLoadError(
        err instanceof ApiError
          ? err.message
          : "No se pudieron cargar los servicios.",
      )
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadServices()
  }, [loadServices])

  // Guards después de hooks
  if (!user) return null
  if (user.role !== "profesional") return <Navigate to="/" replace />

  function handleCreate() {
    setEditingService(null)
    setModalOpen(true)
  }

  function handleEdit(service: Service) {
    setEditingService(service)
    setModalOpen(true)
  }

  async function handleSubmit(
    payload: ServiceCreatePayload | ServiceUpdatePayload,
  ) {
    if (editingService) {
      await api.patch<Service>(
        `/api/v1/services/${editingService.id}`,
        payload,
        true,
      )
      setFeedback({ type: "success", text: "Servicio actualizado." })
    } else {
      await api.post<Service>("/api/v1/services", payload, true)
      setFeedback({ type: "success", text: "Servicio creado." })
    }
    setModalOpen(false)
    await loadServices()
  }

  async function handleDelete(service: Service) {
    const ok = window.confirm(`¿Eliminar el servicio "${service.name}"?`)
    if (!ok) return

    setDeletingId(service.id)
    setFeedback(null)
    try {
      await api.delete(`/api/v1/services/${service.id}`, true)
      setFeedback({ type: "success", text: "Servicio eliminado." })
      await loadServices()
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setFeedback({
          type: "error",
          text: "Este servicio tiene turnos futuros. Cancelalos o resolvelos antes de eliminarlo.",
        })
      } else {
        setFeedback({
          type: "error",
          text:
            err instanceof ApiError
              ? err.message
              : "No se pudo eliminar el servicio.",
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
    return `$${num.toLocaleString("es-AR", {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    })}`
  }

  function formatDuration(minutes: number): string {
    if (minutes < 60) return `${minutes} min`
    const h = Math.floor(minutes / 60)
    const m = minutes % 60
    return m === 0 ? `${h} h` : `${h} h ${m} min`
  }

  const count = services.length

  return (
    <div className="servicios-page">
      <div className="servicios-container">
        <header className="servicios-header">
          <div className="servicios-header-text">
            <h1 className="servicios-title">Mis servicios</h1>
            <p className="servicios-subtitle">
              Configurá los servicios que ofrecés para que tus clientes
              puedan reservarlos.
            </p>
            {count > 0 && (
              <span className="servicios-count" aria-live="polite">
                {count} {count === 1 ? "servicio activo" : "servicios activos"}
              </span>
            )}
          </div>
          <button
            type="button"
            className="servicios-create-button"
            onClick={handleCreate}
          >
            <Icon name="plus" size={16} />
            <span>Nuevo servicio</span>
          </button>
        </header>

        {feedback && (
          <div
            className={`servicios-feedback servicios-feedback--${feedback.type}`}
            role="alert"
          >
            <Icon
              name={feedback.type === "success" ? "check" : "alert"}
              size={18}
            />
            <span className="servicios-feedback-text">{feedback.text}</span>
            <button
              type="button"
              className="servicios-feedback-close"
              onClick={() => setFeedback(null)}
              aria-label="Cerrar mensaje"
            >
              <Icon name="x" size={16} />
            </button>
          </div>
        )}

        {loading && (
          <p className="servicios-loading">Cargando servicios...</p>
        )}

        {!loading && loadError && (
          <div className="servicios-error" role="alert">
            {loadError}
          </div>
        )}

        {!loading && !loadError && services.length === 0 && (
          <div className="servicios-empty">
            <div className="servicios-empty-icon" aria-hidden="true">
              <Icon name="wrench" size={36} />
            </div>
            <h2 className="servicios-empty-title">
              Todavía no tenés servicios
            </h2>
            <p className="servicios-empty-text">
              Creá tu primer servicio para que tus clientes puedan
              reservarte turnos.
            </p>
            <button
              type="button"
              className="servicios-create-button"
              onClick={handleCreate}
            >
              <Icon name="plus" size={16} />
              <span>Crear primer servicio</span>
            </button>
          </div>
        )}

        {!loading && !loadError && services.length > 0 && (
          <ul className="servicios-grid">
            {services.map((service, index) => (
              <li
                key={service.id}
                className="servicios-card"
                style={{ "--i": index } as CSSProperties}
              >
                <div className="servicios-card-header">
                  <h3 className="servicios-card-name">{service.name}</h3>
                  <div className="servicios-card-actions">
                    <button
                      type="button"
                      className="servicios-icon-button"
                      onClick={() => handleEdit(service)}
                      aria-label={`Editar ${service.name}`}
                      title="Editar"
                    >
                      <Icon name="pencil" size={16} />
                    </button>
                    <button
                      type="button"
                      className="servicios-icon-button servicios-icon-button--danger"
                      onClick={() => handleDelete(service)}
                      disabled={deletingId === service.id}
                      aria-label={`Eliminar ${service.name}`}
                      title="Eliminar"
                    >
                      <Icon name="trash" size={16} />
                    </button>
                  </div>
                </div>

                {service.description && (
                  <p className="servicios-card-description">
                    {service.description}
                  </p>
                )}

                <ul className="servicios-card-meta">
                  <li>
                    <Icon name="clock" size={14} />
                    <span>{formatDuration(service.duration_minutes)}</span>
                  </li>
                  <li>
                    <Icon name="banknote" size={14} />
                    <span>{formatPrice(service.price)}</span>
                  </li>
                  <li>
                    <Icon name="users" size={14} />
                    <span>Cupo {service.max_slots}</span>
                  </li>
                  {service.deposit_active && (
                    <li>
                      <Icon name="lock" size={14} />
                      <span>
                        Seña: ${Number(service.deposit_amount || 0).toLocaleString("es-AR", {
                          minimumFractionDigits: 0,
                          maximumFractionDigits: 2,
                        })}
                        {service.deposit_required ? " (Obligatoria)" : " (Opcional)"}
                      </span>
                    </li>
                  )}
                </ul>
              </li>
            ))}
          </ul>
        )}
      </div>

      <ServiceFormModal
        open={modalOpen}
        initialService={editingService}
        onClose={() => setModalOpen(false)}
        onSubmit={handleSubmit}
      />
    </div>
  )
}

export default MisServicios