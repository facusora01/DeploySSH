import { useEffect, useState, type FormEvent } from "react"
import { ApiError } from "../utils/api"
import type {
  Service,
  ServiceCreatePayload,
  ServiceUpdatePayload,
} from "../types/service"
import Icon from "./Icon"

interface ServiceFormModalProps {
  open: boolean
  initialService: Service | null
  onClose: () => void
  onSubmit: (payload: ServiceCreatePayload | ServiceUpdatePayload) => Promise<void>
}

function ServiceFormModal({
  open,
  initialService,
  onClose,
  onSubmit,
}: ServiceFormModalProps) {
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [durationMinutes, setDurationMinutes] = useState("")
  const [price, setPrice] = useState("")
  const [maxSlots, setMaxSlots] = useState("1")
  const [depositActive, setDepositActive] = useState(false)
  const [depositAmount, setDepositAmount] = useState("")
  const [depositRequired, setDepositRequired] = useState(false)
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  const isEdit = initialService !== null

  // Sincroniza el estado del form cuando se abre el modal.
  useEffect(() => {
    if (!open) return
    setError("")
    if (initialService) {
      setName(initialService.name)
      setDescription(initialService.description ?? "")
      setDurationMinutes(String(initialService.duration_minutes))
      setPrice(initialService.price === null ? "" : String(initialService.price))
      setMaxSlots(String(initialService.max_slots))
      setDepositActive(initialService.deposit_active)
      setDepositAmount(initialService.deposit_amount === null ? "" : String(initialService.deposit_amount))
      setDepositRequired(initialService.deposit_required)
    } else {
      setName("")
      setDescription("")
      setDurationMinutes("")
      setPrice("")
      setMaxSlots("1")
      setDepositActive(false)
      setDepositAmount("")
      setDepositRequired(false)
    }
  }, [open, initialService])

  // Esc cierra el modal
  useEffect(() => {
    if (!open) return
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose()
    }
    document.addEventListener("keydown", onKey)
    return () => document.removeEventListener("keydown", onKey)
  }, [open, onClose])

  if (!open) return null

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError("")

    // Validación cliente espejando el back (Pydantic Field constraints)
    const trimmedName = name.trim()
    if (trimmedName.length < 2 || trimmedName.length > 100) {
      setError("El nombre debe tener entre 2 y 100 caracteres.")
      return
    }
    const duration = Number(durationMinutes)
    if (!Number.isInteger(duration) || duration <= 0) {
      setError("La duración debe ser un número entero mayor a 0.")
      return
    }
    let priceValue: number | null = null
    if (price.trim() !== "") {
      const p = Number(price)
      if (isNaN(p) || p < 0) {
        setError("El precio debe ser un número mayor o igual a 0.")
        return
      }
      priceValue = p
    }
    const slots = Number(maxSlots)
    if (!Number.isInteger(slots) || slots < 1) {
      setError("El cupo máximo debe ser un número entero mayor o igual a 1.")
      return
    }

    let depositAmountValue: number | null = null
    if (depositActive) {
      if (depositAmount.trim() === "") {
        setError("El monto de la seña es requerido cuando se activa.")
        return
      }
      const da = Number(depositAmount)
      if (isNaN(da) || da <= 0) {
        setError("El monto de la seña debe ser un número mayor a 0.")
        return
      }
      depositAmountValue = da
    }

    const payload: ServiceCreatePayload = {
      name: trimmedName,
      description: description.trim() === "" ? null : description.trim(),
      duration_minutes: duration,
      price: priceValue,
      max_slots: slots,
      deposit_active: depositActive,
      deposit_amount: depositAmountValue,
      deposit_required: depositActive ? depositRequired : false,
    }

    setLoading(true)
    try {
      await onSubmit(payload)
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "No se pudo guardar el servicio.",
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="servicios-modal-backdrop"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="servicios-modal-title"
    >
      <div className="servicios-modal">
        <header className="servicios-modal-header">
          <h2 id="servicios-modal-title" className="servicios-modal-title">
            {isEdit ? "Editar servicio" : "Nuevo servicio"}
          </h2>
          <button
            type="button"
            className="servicios-modal-close"
            onClick={onClose}
            aria-label="Cerrar"
          >
            <Icon name="x" size={18} />
          </button>
        </header>

        <form className="servicios-modal-form" onSubmit={handleSubmit}>
          <div className="servicios-form-group">
            <label htmlFor="service-name" className="servicios-form-label">
              Nombre <span aria-hidden="true">*</span>
            </label>
            <input
              id="service-name"
              type="text"
              className="servicios-form-input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              minLength={2}
              maxLength={100}
              placeholder="Ej: Consulta general"
              autoFocus
            />
          </div>

          <div className="servicios-form-group">
            <label htmlFor="service-description" className="servicios-form-label">
              Descripción
            </label>
            <textarea
              id="service-description"
              className="servicios-form-textarea"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              placeholder="Opcional: detalles del servicio"
            />
          </div>

          <div className="servicios-form-row">
            <div className="servicios-form-group">
              <label htmlFor="service-duration" className="servicios-form-label">
                Duración (minutos) <span aria-hidden="true">*</span>
              </label>
              <input
                id="service-duration"
                type="number"
                className="servicios-form-input"
                value={durationMinutes}
                onChange={(e) => setDurationMinutes(e.target.value)}
                required
                min={1}
                step={1}
                placeholder="30"
              />
            </div>

            <div className="servicios-form-group">
              <label htmlFor="service-max-slots" className="servicios-form-label">
                Cupo por turno
              </label>
              <input
                id="service-max-slots"
                type="number"
                className="servicios-form-input"
                value={maxSlots}
                onChange={(e) => setMaxSlots(e.target.value)}
                min={1}
                step={1}
              />
              <p className="servicios-form-hint">
                Cuántos clientes pueden reservar el mismo horario.
              </p>
            </div>
          </div>

          <div className="servicios-form-group">
            <label htmlFor="service-price" className="servicios-form-label">
              Precio
            </label>
            <input
              id="service-price"
              type="number"
              className="servicios-form-input"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              min={0}
              step="0.01"
              placeholder="Opcional"
            />
          </div>

          <div className="servicios-form-group">
            <label className="servicios-form-label">Seña</label>
            <div className="servicios-form-checkbox">
              <input
                id="service-deposit-active"
                type="checkbox"
                checked={depositActive}
                onChange={(e) => setDepositActive(e.target.checked)}
              />
              <label htmlFor="service-deposit-active" className="servicios-form-checkbox-label">
                Requerir seña para este servicio
              </label>
            </div>
          </div>

          {depositActive && (
            <>
              <div className="servicios-form-group">
                <label htmlFor="service-deposit-amount" className="servicios-form-label">
                  Monto de la seña ($) <span aria-hidden="true">*</span>
                </label>
                <input
                  id="service-deposit-amount"
                  type="number"
                  className="servicios-form-input"
                  value={depositAmount}
                  onChange={(e) => setDepositAmount(e.target.value)}
                  min={0.01}
                  step="0.01"
                  placeholder="0.00"
                  required
                />
              </div>

              <div className="servicios-form-group">
                <div className="servicios-form-checkbox">
                  <input
                    id="service-deposit-required"
                    type="checkbox"
                    checked={depositRequired}
                    onChange={(e) => setDepositRequired(e.target.checked)}
                  />
                  <label htmlFor="service-deposit-required" className="servicios-form-checkbox-label">
                    La seña es obligatoria
                  </label>
                </div>
                <p className="servicios-form-hint">
                  {depositRequired
                    ? "El cliente debe pagar la seña para confirmar la reserva."
                    : "El cliente puede elegir pagar la seña o no."}
                </p>
              </div>
            </>
          )}

          {error && (
            <div className="servicios-form-error" role="alert">
              {error}
            </div>
          )}

          <div className="servicios-modal-actions">
            <button
              type="button"
              className="servicios-button servicios-button--secondary"
              onClick={onClose}
              disabled={loading}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="servicios-button servicios-button--primary"
              disabled={loading}
            >
              {loading
                ? "Guardando..."
                : isEdit
                  ? "Guardar cambios"
                  : "Crear servicio"}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default ServiceFormModal