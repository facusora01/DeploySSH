import { useCallback, useEffect, useRef, useState } from "react"
import { Navigate } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import { api, ApiError } from "../utils/api"
import Icon from "../components/Icon"
import "./formulario-config.css"

type FieldType = "text" | "yes_no" | "select"

interface FormField {
  id: string
  field_name: string
  is_required: boolean
  order: number
  field_type: FieldType
  options: string[]
}

interface FieldForm {
  field_name: string
  is_required: boolean
  field_type: FieldType
  options: string[]
}

type Feedback = { type: "success" | "error"; text: string }

const EMPTY_FORM: FieldForm = {
  field_name: "",
  is_required: false,
  field_type: "text",
  options: [],
}

const FIELD_TYPE_LABELS: Record<FieldType, string> = {
  text: "Respuesta libre",
  yes_no: "Sí / No",
  select: "Opciones predefinidas",
}

// Sub-component for managing options list (used in both add and edit forms)
function OptionsEditor({
  options,
  onChange,
}: {
  options: string[]
  onChange: (opts: string[]) => void
}) {
  const [draft, setDraft] = useState("")
  const inputRef = useRef<HTMLInputElement>(null)

  function addOption() {
    const trimmed = draft.trim()
    if (!trimmed || options.includes(trimmed)) return
    onChange([...options, trimmed])
    setDraft("")
    inputRef.current?.focus()
  }

  function removeOption(idx: number) {
    onChange(options.filter((_, i) => i !== idx))
  }

  return (
    <div className="fconfig-options-editor">
      <div className="fconfig-options-input-row">
        <input
          ref={inputRef}
          className="fconfig-input"
          type="text"
          placeholder="Nueva opción..."
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault()
              addOption()
            }
          }}
          maxLength={100}
        />
        <button
          type="button"
          className="fconfig-button fconfig-button--secondary fconfig-options-add-btn"
          onClick={addOption}
          disabled={!draft.trim()}
        >
          <Icon name="plus" size={14} />
          Agregar
        </button>
      </div>
      {options.length > 0 && (
        <ul className="fconfig-options-list">
          {options.map((opt, idx) => (
            <li key={idx} className="fconfig-option-chip">
              <span className="fconfig-option-chip-label">{opt}</span>
              <button
                type="button"
                className="fconfig-option-chip-remove"
                onClick={() => removeOption(idx)}
                aria-label={`Eliminar opción ${opt}`}
              >
                <Icon name="x" size={12} />
              </button>
            </li>
          ))}
        </ul>
      )}
      {options.length === 0 && (
        <p className="fconfig-options-hint">Agregá al menos una opción.</p>
      )}
    </div>
  )
}

// Inline form used for both add and edit
function FieldFormPanel({
  value,
  onChange,
  onSubmit,
  onCancel,
  submitting,
  isAdd,
}: {
  value: FieldForm
  onChange: (f: FieldForm) => void
  onSubmit: (e: React.FormEvent) => void
  onCancel: () => void
  submitting: boolean
  isAdd: boolean
}) {
  return (
    <form
      className={`fconfig-inline-form${isAdd ? " fconfig-inline-form--add" : ""}`}
      onSubmit={onSubmit}
    >
      {/* Field name */}
      <div className="fconfig-form-row">
        <div className="fconfig-form-group fconfig-form-group--name">
          <label className="fconfig-form-label">Nombre del campo</label>
          <input
            className="fconfig-input"
            type="text"
            placeholder="Ej: Obra social, Materia, Motivo de consulta..."
            value={value.field_name}
            onChange={(e) => onChange({ ...value, field_name: e.target.value })}
            autoFocus={isAdd}
            required
            maxLength={200}
          />
        </div>

        {/* Field type */}
        <div className="fconfig-form-group fconfig-form-group--type">
          <label className="fconfig-form-label">Tipo de respuesta</label>
          <select
            className="fconfig-select"
            value={value.field_type}
            onChange={(e) =>
              onChange({ ...value, field_type: e.target.value as FieldType, options: [] })
            }
          >
            {(Object.keys(FIELD_TYPE_LABELS) as FieldType[]).map((t) => (
              <option key={t} value={t}>
                {FIELD_TYPE_LABELS[t]}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Options editor — only for "select" */}
      {value.field_type === "select" && (
        <div className="fconfig-form-group">
          <label className="fconfig-form-label">Opciones disponibles</label>
          <OptionsEditor
            options={value.options}
            onChange={(opts) => onChange({ ...value, options: opts })}
          />
        </div>
      )}

      {/* Required checkbox + actions */}
      <div className="fconfig-inline-footer">
        <label className="fconfig-checkbox-label">
          <input
            type="checkbox"
            className="fconfig-checkbox"
            checked={value.is_required}
            onChange={(e) => onChange({ ...value, is_required: e.target.checked })}
          />
          <span>Obligatorio</span>
        </label>
        <div className="fconfig-inline-actions">
          <button
            type="submit"
            className="fconfig-button fconfig-button--primary"
            disabled={
              submitting ||
              !value.field_name.trim() ||
              (value.field_type === "select" && value.options.length === 0)
            }
          >
            {submitting ? "Guardando..." : "Guardar"}
          </button>
          <button
            type="button"
            className="fconfig-button fconfig-button--secondary"
            onClick={onCancel}
            disabled={submitting}
          >
            Cancelar
          </button>
        </div>
      </div>
    </form>
  )
}

// ─── Main component ───────────────────────────────────────────────────────────

function FormularioConfig() {
  const { user } = useAuth()

  const [fields, setFields] = useState<FormField[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState("")
  const [feedback, setFeedback] = useState<Feedback | null>(null)

  const [showAddForm, setShowAddForm] = useState(false)
  const [addForm, setAddForm] = useState<FieldForm>(EMPTY_FORM)
  const [addSubmitting, setAddSubmitting] = useState(false)

  const [editingId, setEditingId] = useState<string | null>(null)
  const [editForm, setEditForm] = useState<FieldForm>(EMPTY_FORM)
  const [editSubmitting, setEditSubmitting] = useState(false)

  const [deletingId, setDeletingId] = useState<string | null>(null)

  const loadFields = useCallback(async () => {
    setLoading(true)
    setLoadError("")
    try {
      const data = await api.get<FormField[]>("/api/v1/form-fields", true)
      setFields(data)
    } catch (err) {
      setLoadError(
        err instanceof ApiError ? err.message : "No se pudieron cargar los campos."
      )
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadFields()
  }, [loadFields])

  if (!user) return null
  if (user.role !== "profesional") return <Navigate to="/" replace />

  // ── Add ──────────────────────────────────────────────────────────────────

  function openAddForm() {
    setAddForm(EMPTY_FORM)
    setShowAddForm(true)
    setEditingId(null)
  }

  function cancelAdd() {
    setShowAddForm(false)
    setAddForm(EMPTY_FORM)
  }

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault()
    setAddSubmitting(true)
    setFeedback(null)
    try {
      await api.post("/api/v1/form-fields", {
        field_name: addForm.field_name.trim(),
        is_required: addForm.is_required,
        field_type: addForm.field_type,
        options: addForm.field_type === "select" ? addForm.options : [],
        order: fields.length,
      }, true)
      setFeedback({ type: "success", text: "Campo agregado." })
      setShowAddForm(false)
      setAddForm(EMPTY_FORM)
      await loadFields()
    } catch (err) {
      setFeedback({
        type: "error",
        text: err instanceof ApiError ? err.message : "No se pudo agregar el campo.",
      })
    } finally {
      setAddSubmitting(false)
    }
  }

  // ── Edit ─────────────────────────────────────────────────────────────────

  function openEdit(field: FormField) {
    setEditingId(field.id)
    setEditForm({
      field_name: field.field_name,
      is_required: field.is_required,
      field_type: field.field_type,
      options: field.options ?? [],
    })
    setShowAddForm(false)
  }

  function cancelEdit() {
    setEditingId(null)
    setEditForm(EMPTY_FORM)
  }

  async function handleEdit(e: React.FormEvent, fieldId: string) {
    e.preventDefault()
    setEditSubmitting(true)
    setFeedback(null)
    try {
      await api.patch(`/api/v1/form-fields/${fieldId}`, {
        field_name: editForm.field_name.trim(),
        is_required: editForm.is_required,
        field_type: editForm.field_type,
        options: editForm.field_type === "select" ? editForm.options : [],
      }, true)
      setFeedback({ type: "success", text: "Campo actualizado." })
      setEditingId(null)
      await loadFields()
    } catch (err) {
      setFeedback({
        type: "error",
        text: err instanceof ApiError ? err.message : "No se pudo actualizar el campo.",
      })
    } finally {
      setEditSubmitting(false)
    }
  }

  // ── Delete ───────────────────────────────────────────────────────────────

  async function handleDelete(field: FormField) {
    if (!window.confirm(`¿Eliminar el campo "${field.field_name}"?`)) return
    setDeletingId(field.id)
    setFeedback(null)
    try {
      await api.delete(`/api/v1/form-fields/${field.id}`, true)
      setFeedback({ type: "success", text: "Campo eliminado." })
      await loadFields()
    } catch (err) {
      setFeedback({
        type: "error",
        text: err instanceof ApiError ? err.message : "No se pudo eliminar el campo.",
      })
    } finally {
      setDeletingId(null)
    }
  }

  // ── Render ───────────────────────────────────────────────────────────────

  return (
    <div className="fconfig-page">
      <div className="fconfig-container">

        <header className="fconfig-header">
          <div className="fconfig-header-text">
            <h1 className="fconfig-title">Formulario de reserva</h1>
            <p className="fconfig-subtitle">
              Agregá campos personalizados que tus clientes completan al reservar.
              Si no hay campos configurados, el paso de formulario no aparece en el flujo de reserva.
            </p>
          </div>
          {!showAddForm && (
            <button type="button" className="fconfig-add-button" onClick={openAddForm}>
              <Icon name="plus" size={16} />
              <span>Nuevo campo</span>
            </button>
          )}
        </header>

        {feedback && (
          <div className={`fconfig-feedback fconfig-feedback--${feedback.type}`} role="alert">
            <Icon name={feedback.type === "success" ? "check" : "alert"} size={18} />
            <span className="fconfig-feedback-text">{feedback.text}</span>
            <button
              type="button"
              className="fconfig-feedback-close"
              onClick={() => setFeedback(null)}
              aria-label="Cerrar mensaje"
            >
              <Icon name="x" size={16} />
            </button>
          </div>
        )}

        {loading && <p className="fconfig-loading">Cargando campos...</p>}

        {!loading && loadError && (
          <div className="fconfig-error" role="alert">{loadError}</div>
        )}

        {!loading && !loadError && (
          <div className="fconfig-list">

            {showAddForm && (
              <FieldFormPanel
                value={addForm}
                onChange={setAddForm}
                onSubmit={handleAdd}
                onCancel={cancelAdd}
                submitting={addSubmitting}
                isAdd
              />
            )}

            {fields.length === 0 && !showAddForm && (
              <div className="fconfig-empty">
                <div className="fconfig-empty-icon" aria-hidden="true">
                  <Icon name="clipboard" size={36} />
                </div>
                <h2 className="fconfig-empty-title">Sin campos configurados</h2>
                <p className="fconfig-empty-text">
                  El paso de formulario no aparecerá en el flujo de reserva hasta que agregues al menos un campo.
                </p>
                <button type="button" className="fconfig-add-button" onClick={openAddForm}>
                  <Icon name="plus" size={16} />
                  <span>Agregar primer campo</span>
                </button>
              </div>
            )}

            {fields.map((field, index) => (
              <div
                key={field.id}
                className="fconfig-field-row"
                style={{ "--i": index } as React.CSSProperties}
              >
                {editingId === field.id ? (
                  <FieldFormPanel
                    value={editForm}
                    onChange={setEditForm}
                    onSubmit={(e) => handleEdit(e, field.id)}
                    onCancel={cancelEdit}
                    submitting={editSubmitting}
                    isAdd={false}
                  />
                ) : (
                  <>
                    <div className="fconfig-field-info">
                      <span className="fconfig-field-name">{field.field_name}</span>
                      <span className="fconfig-badge fconfig-badge--type">
                        {FIELD_TYPE_LABELS[field.field_type] ?? field.field_type}
                      </span>
                      {field.is_required ? (
                        <span className="fconfig-badge fconfig-badge--required">Obligatorio</span>
                      ) : (
                        <span className="fconfig-badge fconfig-badge--optional">Opcional</span>
                      )}
                      {field.field_type === "select" && field.options.length > 0 && (
                        <span className="fconfig-field-options-preview">
                          {field.options.join(" · ")}
                        </span>
                      )}
                    </div>
                    <div className="fconfig-field-actions">
                      <button
                        type="button"
                        className="fconfig-icon-button"
                        onClick={() => openEdit(field)}
                        aria-label={`Editar campo ${field.field_name}`}
                        title="Editar"
                      >
                        <Icon name="pencil" size={16} />
                      </button>
                      <button
                        type="button"
                        className="fconfig-icon-button fconfig-icon-button--danger"
                        onClick={() => handleDelete(field)}
                        disabled={deletingId === field.id}
                        aria-label={`Eliminar campo ${field.field_name}`}
                        title="Eliminar"
                      >
                        <Icon name="trash" size={16} />
                      </button>
                    </div>
                  </>
                )}
              </div>
            ))}

          </div>
        )}

      </div>
    </div>
  )
}

export default FormularioConfig
