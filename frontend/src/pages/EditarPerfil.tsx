import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import { CountrySelect } from "../components/CountrySelect"
import { api } from "../utils/api"
import "./perfil.css"

function EditarPerfil() {
  const navigate = useNavigate()
  const { user, updateUserProfile } = useAuth()

  const [fullName, setFullName] = useState("")
  const [phone, setPhone] = useState("")
  const [countryCode, setCountryCode] = useState("+54")

  // Profesional-specific fields
  const [specialty, setSpecialty] = useState("")
  const [bio, setBio] = useState("")

  // Client-specific fields
  const [dni, setDni] = useState("")
  const [dateOfBirth, setDateOfBirth] = useState("")
  const [address, setAddress] = useState("")
  const [city, setCity] = useState("")
  const [notes, setNotes] = useState("")

  // Local-specific fields
  const [localName, setLocalName] = useState("")
  const [description, setDescription] = useState("")
  const [logoBase64, setLogoBase64] = useState<string>("")
  const [existingLogoUrl, setExistingLogoUrl] = useState<string>("")

  type DaySchedule = { open_time: string; close_time: string; is_closed: boolean }
  const DEFAULT_HOURS: DaySchedule[] = [
    { open_time: "09:00", close_time: "18:00", is_closed: false },
    { open_time: "09:00", close_time: "18:00", is_closed: false },
    { open_time: "09:00", close_time: "18:00", is_closed: false },
    { open_time: "09:00", close_time: "18:00", is_closed: false },
    { open_time: "09:00", close_time: "18:00", is_closed: false },
    { open_time: "09:00", close_time: "18:00", is_closed: false },
    { open_time: "09:00", close_time: "18:00", is_closed: true },
  ]
  const [openingHours, setOpeningHours] = useState<DaySchedule[]>(DEFAULT_HOURS)

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  useEffect(() => {
    if (!user) return
    setLoading(true)

    if (user.role === "client") {
      api.get<any>("/api/v1/clientes/me", true)
        .then((data) => {
          if (data) {
            setFullName(data.full_name || "")
            setDni(data.dni || "")
            setDateOfBirth(data.date_of_birth || "")
            setAddress(data.address || "")
            setCity(data.city || "")
            setNotes(data.notes || "")
            parsePhone(data.phone)
          }
        })
        .catch((err) => console.error("Error fetching client profile:", err))
        .finally(() => setLoading(false))
    } else if (user.role === "profesional") {
      api.get<any>("/api/v1/profesionales/me", true)
        .then((data) => {
          if (data) {
            setFullName(data.full_name || "")
            setSpecialty(data.specialty || "")
            setBio(data.bio || "")
            parsePhone(data.phone)
          }
        })
        .catch((err) => console.error("Error fetching profesional profile:", err))
        .finally(() => setLoading(false))
    } else if (user.role === "local") {
      api.get<any>("/api/v1/locales/me", true)
        .then((data) => {
          if (data) {
            setLocalName(data.local_name || "")
            setAddress(data.address || "")
            setCity(data.city || "")
            setDescription(data.description || "")
            setExistingLogoUrl(data.logo_url || "")
            if (data.opening_hours && data.opening_hours.length === 7) {
              setOpeningHours(data.opening_hours)
            }
            parsePhone(data.phone)
          }
        })
        .catch((err) => console.error("Error fetching local profile:", err))
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [user])

  function parsePhone(phoneStr: string | null | undefined) {
    if (!phoneStr) {
      setPhone("")
      setCountryCode("+54")
      return
    }
    if (phoneStr.includes(" ")) {
      const parts = phoneStr.split(" ")
      setCountryCode(parts[0])
      setPhone(parts.slice(1).join(" "))
    } else {
      setPhone(phoneStr)
    }
  }

  function resizeToBase64(file: File, maxPx = 400, quality = 0.85): Promise<string> {
    return new Promise((resolve, reject) => {
      const img = new Image()
      const url = URL.createObjectURL(file)
      img.onload = () => {
        URL.revokeObjectURL(url)
        const ratio = Math.min(maxPx / img.width, maxPx / img.height, 1)
        const canvas = document.createElement("canvas")
        canvas.width = Math.round(img.width * ratio)
        canvas.height = Math.round(img.height * ratio)
        canvas.getContext("2d")!.drawImage(img, 0, 0, canvas.width, canvas.height)
        resolve(canvas.toDataURL("image/jpeg", quality))
      }
      img.onerror = reject
      img.src = url
    })
  }

  if (!user) return null

  const isClient = user.role === "client"
  const isProfesional = user.role === "profesional"
  const isLocal = user.role === "local"

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setLoading(true)
    try {
      if (isClient) {
        const payload = {
          full_name: fullName.trim() || undefined,
          phone: phone.trim() ? `${countryCode} ${phone.trim()}` : undefined,
          dni: dni.trim() || null,
          date_of_birth: dateOfBirth || null,
          address: address.trim() || null,
          city: city.trim() || null,
          notes: notes.trim() || null,
        }
        await api.put("/api/v1/clientes/me", payload, true)
        await updateUserProfile({
          full_name: fullName.trim() || undefined,
          phone: phone.trim() ? `${countryCode} ${phone.trim()}` : undefined,
        })
      } else if (isProfesional) {
        const payload = {
          full_name: fullName.trim() || undefined,
          phone: phone.trim() ? `${countryCode} ${phone.trim()}` : undefined,
          specialty: specialty.trim() || undefined,
          bio: bio.trim() || null,
        }
        await api.put("/api/v1/profesionales/me", payload, true)
        await updateUserProfile({
          full_name: fullName.trim() || undefined,
          phone: phone.trim() ? `${countryCode} ${phone.trim()}` : undefined,
        })
      } else if (isLocal) {
        const payload: Record<string, unknown> = {
          local_name: localName.trim() || undefined,
          phone: phone.trim() ? `${countryCode} ${phone.trim()}` : undefined,
          address: address.trim() || null,
          city: city.trim() || null,
          description: description.trim() || null,
          opening_hours: openingHours,
        }
        if (logoBase64) payload.logo_url = logoBase64
        await api.put("/api/v1/locales/me", payload, true)
      }
      navigate("/perfil")
    } catch (err: any) {
      setError(err.response?.data?.detail || "Error al actualizar perfil")
    } finally {
      setLoading(false)
    }
  }

  const inputStyle = {
    flex: 1,
    padding: "0.75rem",
    borderRadius: "4px",
    border: "1px solid #ccc",
    backgroundColor: "#fff",
    color: "#000",
  }

  return (
    <div className="perfil-page">
      <div className="perfil-container">
        <header className="perfil-header">
          <div>
            <h1 className="perfil-title">Editar perfil</h1>
            <p className="perfil-subtitle">Actualiza tus datos</p>
          </div>
          <button type="button" className="perfil-edit-button" onClick={() => navigate("/perfil")}>
            Volver
          </button>
        </header>

        <section className="perfil-card">
          {error && <div className="auth-error" style={{ marginBottom: "1rem" }}>{error}</div>}
          <form onSubmit={handleSubmit} style={{ width: "100%" }}>
            <div className="perfil-fields" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              {/* Client fields */}
              {isClient && (
                <>
                  <div className="perfil-field">
                    <label className="perfil-field-label" style={{ display: "block", marginBottom: "0.5rem" }}>
                      Nombre completo
                    </label>
                    <div style={{ display: "flex", gap: "0.5rem" }}>
                      <div style={{ width: "120px", flexShrink: 0 }} />
                      <input
                        type="text"
                        value={fullName}
                        placeholder={user?.full_name || "Tu nombre..."}
                        onChange={(e) => setFullName(e.target.value)}
                        style={inputStyle}
                      />
                    </div>
                  </div>

                  <div className="perfil-field">
                    <label className="perfil-field-label" style={{ display: "block", marginBottom: "0.5rem" }}>
                      Teléfono
                    </label>
                    <div style={{ display: "flex", gap: "0.5rem", position: "relative", zIndex: 2 }}>
                      <CountrySelect value={countryCode} onChange={setCountryCode} />
                      <input
                        type="tel"
                        value={phone}
                        maxLength={15}
                        placeholder="Tu teléfono..."
                        onChange={(e) => setPhone(e.target.value.replace(/[^\d ]/g, ""))}
                        style={inputStyle}
                      />
                    </div>
                  </div>

                  <div className="perfil-field">
                    <label className="perfil-field-label" style={{ display: "block", marginBottom: "0.5rem" }}>
                      DNI
                    </label>
                    <div style={{ display: "flex", gap: "0.5rem" }}>
                      <div style={{ width: "120px", flexShrink: 0 }} />
                      <input
                        type="text"
                        value={dni}
                        placeholder="Tu DNI..."
                        onChange={(e) => setDni(e.target.value)}
                        style={inputStyle}
                      />
                    </div>
                  </div>

                  <div className="perfil-field">
                    <label className="perfil-field-label" style={{ display: "block", marginBottom: "0.5rem" }}>
                      Fecha de nacimiento
                    </label>
                    <div style={{ display: "flex", gap: "0.5rem" }}>
                      <div style={{ width: "120px", flexShrink: 0 }} />
                      <input
                        type="date"
                        value={dateOfBirth}
                        onChange={(e) => setDateOfBirth(e.target.value)}
                        style={inputStyle}
                      />
                    </div>
                  </div>

                  <div className="perfil-field">
                    <label className="perfil-field-label" style={{ display: "block", marginBottom: "0.5rem" }}>
                      Dirección
                    </label>
                    <div style={{ display: "flex", gap: "0.5rem" }}>
                      <div style={{ width: "120px", flexShrink: 0 }} />
                      <input
                        type="text"
                        value={address}
                        placeholder="Tu dirección..."
                        onChange={(e) => setAddress(e.target.value)}
                        style={inputStyle}
                      />
                    </div>
                  </div>

                  <div className="perfil-field">
                    <label className="perfil-field-label" style={{ display: "block", marginBottom: "0.5rem" }}>
                      Ciudad
                    </label>
                    <div style={{ display: "flex", gap: "0.5rem" }}>
                      <div style={{ width: "120px", flexShrink: 0 }} />
                      <input
                        type="text"
                        value={city}
                        placeholder="Tu ciudad..."
                        onChange={(e) => setCity(e.target.value)}
                        style={inputStyle}
                      />
                    </div>
                  </div>

                  <div className="perfil-field">
                    <label className="perfil-field-label" style={{ display: "block", marginBottom: "0.5rem" }}>
                      Notas
                    </label>
                    <div style={{ display: "flex", gap: "0.5rem" }}>
                      <div style={{ width: "120px", flexShrink: 0 }} />
                      <textarea
                        value={notes}
                        placeholder="Notas adicionales..."
                        onChange={(e) => setNotes(e.target.value)}
                        style={{
                          ...inputStyle,
                          minHeight: "100px",
                          resize: "vertical",
                          fontFamily: "inherit",
                        }}
                      />
                    </div>
                  </div>
                </>
              )}

              {/* Profesional fields */}
              {isProfesional && (
                <>
                  <div className="perfil-field">
                    <label className="perfil-field-label" style={{ display: "block", marginBottom: "0.5rem" }}>
                      Nombre completo
                    </label>
                    <div style={{ display: "flex", gap: "0.5rem" }}>
                      <div style={{ width: "120px", flexShrink: 0 }} />
                      <input
                        type="text"
                        value={fullName}
                        placeholder={user?.full_name || "Tu nombre..."}
                        onChange={(e) => setFullName(e.target.value)}
                        style={inputStyle}
                      />
                    </div>
                  </div>

                  <div className="perfil-field">
                    <label className="perfil-field-label" style={{ display: "block", marginBottom: "0.5rem" }}>
                      Teléfono
                    </label>
                    <div style={{ display: "flex", gap: "0.5rem", position: "relative", zIndex: 2 }}>
                      <CountrySelect value={countryCode} onChange={setCountryCode} />
                      <input
                        type="tel"
                        value={phone}
                        maxLength={15}
                        placeholder="Tu teléfono..."
                        onChange={(e) => setPhone(e.target.value.replace(/[^\d ]/g, ""))}
                        style={inputStyle}
                      />
                    </div>
                  </div>

                  <div className="perfil-field">
                    <label className="perfil-field-label" style={{ display: "block", marginBottom: "0.5rem" }}>
                      Especialidad
                    </label>
                    <div style={{ display: "flex", gap: "0.5rem" }}>
                      <div style={{ width: "120px", flexShrink: 0 }} />
                      <input
                        type="text"
                        value={specialty}
                        placeholder="Tu especialidad..."
                        onChange={(e) => setSpecialty(e.target.value)}
                        style={inputStyle}
                      />
                    </div>
                  </div>

                  <div className="perfil-field">
                    <label className="perfil-field-label" style={{ display: "block", marginBottom: "0.5rem" }}>
                      Biografía
                    </label>
                    <div style={{ display: "flex", gap: "0.5rem" }}>
                      <div style={{ width: "120px", flexShrink: 0 }} />
                      <textarea
                        value={bio}
                        placeholder="Contá algo sobre vos..."
                        onChange={(e) => setBio(e.target.value)}
                        style={{
                          ...inputStyle,
                          minHeight: "100px",
                          resize: "vertical",
                          fontFamily: "inherit",
                        }}
                      />
                    </div>
                  </div>
                </>
              )}

              {/* Local fields */}
              {isLocal && (
                <>
                  <div className="perfil-field">
                    <label className="perfil-field-label" style={{ display: "block", marginBottom: "0.5rem" }}>
                      Nombre del local
                    </label>
                    <div style={{ display: "flex", gap: "0.5rem" }}>
                      <div style={{ width: "120px", flexShrink: 0 }} />
                      <input
                        type="text"
                        value={localName}
                        placeholder="Nombre del local..."
                        onChange={(e) => setLocalName(e.target.value)}
                        style={inputStyle}
                      />
                    </div>
                  </div>

                  <div className="perfil-field">
                    <label className="perfil-field-label" style={{ display: "block", marginBottom: "0.5rem" }}>
                      Teléfono
                    </label>
                    <div style={{ display: "flex", gap: "0.5rem", position: "relative", zIndex: 2 }}>
                      <CountrySelect value={countryCode} onChange={setCountryCode} />
                      <input
                        type="tel"
                        value={phone}
                        maxLength={15}
                        placeholder="Teléfono del local..."
                        onChange={(e) => setPhone(e.target.value.replace(/[^\d ]/g, ""))}
                        style={inputStyle}
                      />
                    </div>
                  </div>

                  <div className="perfil-field">
                    <label className="perfil-field-label" style={{ display: "block", marginBottom: "0.5rem" }}>
                      Dirección
                    </label>
                    <div style={{ display: "flex", gap: "0.5rem" }}>
                      <div style={{ width: "120px", flexShrink: 0 }} />
                      <input
                        type="text"
                        value={address}
                        placeholder="Dirección del local..."
                        onChange={(e) => setAddress(e.target.value)}
                        style={inputStyle}
                      />
                    </div>
                  </div>

                  <div className="perfil-field">
                    <label className="perfil-field-label" style={{ display: "block", marginBottom: "0.5rem" }}>
                      Ciudad
                    </label>
                    <div style={{ display: "flex", gap: "0.5rem" }}>
                      <div style={{ width: "120px", flexShrink: 0 }} />
                      <input
                        type="text"
                        value={city}
                        placeholder="Ciudad..."
                        onChange={(e) => setCity(e.target.value)}
                        style={inputStyle}
                      />
                    </div>
                  </div>

                  <div className="perfil-field">
                    <label className="perfil-field-label" style={{ display: "block", marginBottom: "0.5rem" }}>
                      Descripción
                    </label>
                    <div style={{ display: "flex", gap: "0.5rem" }}>
                      <div style={{ width: "120px", flexShrink: 0 }} />
                      <textarea
                        value={description}
                        placeholder="Descripción del local..."
                        onChange={(e) => setDescription(e.target.value)}
                        style={{
                          ...inputStyle,
                          minHeight: "100px",
                          resize: "vertical",
                          fontFamily: "inherit",
                        }}
                      />
                    </div>
                  </div>

                  <div className="perfil-field">
                    <label className="perfil-field-label" style={{ display: "block", marginBottom: "0.5rem" }}>
                      Logo del local
                    </label>
                    <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
                      <div style={{ width: "120px", flexShrink: 0 }} />
                      {(logoBase64 || existingLogoUrl) && (
                        <img
                          src={logoBase64 || existingLogoUrl}
                          alt="Logo actual"
                          style={{ height: "64px", width: "64px", objectFit: "contain", borderRadius: "8px", border: "1px solid #eee" }}
                        />
                      )}
                      <label style={{ cursor: "pointer" }}>
                        <span style={{
                          display: "inline-block",
                          padding: "0.5rem 1rem",
                          backgroundColor: "#f5f5f5",
                          border: "1px solid #ccc",
                          borderRadius: "4px",
                          fontSize: "0.875rem",
                          color: "#333",
                        }}>
                          {logoBase64 ? "Cambiar imagen" : existingLogoUrl ? "Reemplazar logo" : "Elegir imagen"}
                        </span>
                        <input
                          type="file"
                          accept="image/jpeg,image/png,image/gif,image/webp"
                          style={{ display: "none" }}
                          onChange={async (e) => {
                            const file = e.target.files?.[0]
                            if (file) setLogoBase64(await resizeToBase64(file))
                          }}
                        />
                      </label>
                      {logoBase64 && (
                        <span style={{ fontSize: "0.8rem", color: "#888" }}>
                          Se guardará al confirmar
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="perfil-field">
                    <label className="perfil-field-label" style={{ display: "block", marginBottom: "0.75rem" }}>
                      Horarios de apertura
                    </label>
                    {["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"].map((day, idx) => (
                      <div key={idx} style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.5rem" }}>
                        <span style={{ width: "90px", fontSize: "0.9rem", color: "#555" }}>{day}</span>
                        <label style={{ display: "flex", alignItems: "center", gap: "0.3rem", fontSize: "0.85rem", color: "#666" }}>
                          <input
                            type="checkbox"
                            checked={openingHours[idx].is_closed}
                            onChange={(e) => {
                              const updated = [...openingHours]
                              updated[idx] = { ...updated[idx], is_closed: e.target.checked }
                              setOpeningHours(updated)
                            }}
                          />
                          Cerrado
                        </label>
                        {!openingHours[idx].is_closed && (
                          <>
                            <input
                              type="time"
                              value={openingHours[idx].open_time}
                              onChange={(e) => {
                                const updated = [...openingHours]
                                updated[idx] = { ...updated[idx], open_time: e.target.value }
                                setOpeningHours(updated)
                              }}
                              style={{ padding: "0.4rem", borderRadius: "4px", border: "1px solid #ccc" }}
                            />
                            <span style={{ color: "#888" }}>—</span>
                            <input
                              type="time"
                              value={openingHours[idx].close_time}
                              onChange={(e) => {
                                const updated = [...openingHours]
                                updated[idx] = { ...updated[idx], close_time: e.target.value }
                                setOpeningHours(updated)
                              }}
                              style={{ padding: "0.4rem", borderRadius: "4px", border: "1px solid #ccc" }}
                            />
                          </>
                        )}
                      </div>
                    ))}
                  </div>
                </>
              )}

              <div style={{ display: "flex", gap: "0.5rem", marginTop: "1rem" }}>
                <div style={{ width: "120px", flexShrink: 0 }} />
                <button type="submit" className="perfil-edit-button" disabled={loading}>
                  {loading ? "Guardando..." : "Guardar cambios"}
                </button>
              </div>
            </div>
          </form>
        </section>
      </div>
    </div>
  )
}

export default EditarPerfil
