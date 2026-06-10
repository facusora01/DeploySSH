import { useEffect, useState, type FormEvent } from "react"
import { Link, useNavigate, useSearchParams } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import { ApiError } from "../utils/api"
import AuthCard from "../components/AuthCard"
import AuthBackground from "../components/AuthBackground"
import TextField from "../components/TextField"
import type { UserRole } from "../types/auth"
import "./auth.css"

function Register() {
  const navigate = useNavigate()
  const { user, register } = useAuth()
  const [searchParams] = useSearchParams()

  // Si el usuario llegó desde un link de invitación de un local, lo registramos
  // como profesional con el email ya fijado, y al completar queda vinculado.
  const invitationToken = searchParams.get("invitation")
  const invitedEmail = searchParams.get("email")
  const isInvited = Boolean(invitationToken)

  const [role, setRole] = useState<UserRole>(isInvited ? "profesional" : "client")
  const [fullName, setFullName] = useState("")
  const [email, setEmail] = useState(invitedEmail ?? "")
  const [phone, setPhone] = useState("")
  const [specialty, setSpecialty] = useState("")
  const [localName, setLocalName] = useState("")
  const [password, setPassword] = useState("")
  const [confirm, setConfirm] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const [successMessage, setSuccessMessage] = useState("")

  // Si ya está logueado, no tiene sentido ver el register
  useEffect(() => {
    if (user) navigate("/", { replace: true })
  }, [user, navigate])

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError("")

    // Validaciones de cliente antes de pegarle al back
    if (password !== confirm) {
      setError("Las contraseñas no coinciden.")
      return
    }
    if (password.length < 8) {
      setError("La contraseña debe tener al menos 8 caracteres.")
      return
    }
    if (role === "profesional" && !specialty.trim()) {
      setError("Como profesional, tenés que indicar tu especialidad.")
      return
    }
    if (role === "local" && !localName.trim()) {
      setError("Tenés que indicar el nombre del local.")
      return
    }

    setLoading(true)
    try {
      const message = await register({
        role,
        full_name: fullName,
        email,
        phone,
        password,
        ...(role === "profesional" ? { specialty } : {}),
        ...(role === "local" ? { local_name: localName } : {}),
        ...(invitationToken ? { invitation_token: invitationToken } : {}),
      })
      setSuccessMessage(message)
    } catch (err) {
      if (err instanceof ApiError) {
        setError(
          err.status === 409
            ? "Ya existe una cuenta con ese email."
            : err.message,
        )
      } else {
        setError("Ocurrió un error inesperado.")
      }
    } finally {
      setLoading(false)
    }
  }

  if (successMessage) {
    return (
      <div className="auth-page">
        <AuthBackground />
        <div className="auth-container">
          <section className="auth-card">
            <header className="auth-header">
              <Link to="/" className="auth-logo">APPOINTA</Link>
              <h1 className="auth-title">Revisá tu correo</h1>
              <p className="auth-subtitle">{successMessage}</p>
            </header>
            <footer className="auth-footer">
              <p className="auth-footer-text">
                ¿Ya confirmaste?{" "}
                <Link to="/login" className="auth-footer-link">
                  Iniciá sesión
                </Link>
              </p>
            </footer>
          </section>
        </div>
      </div>
    )
  }

  return (
    <AuthCard
      title="Creá tu cuenta"
      subtitle="Empezá a usar Appointa en minutos"
      footerText="¿Ya tenés cuenta?"
      footerLinkLabel="Iniciá sesión"
      footerLinkTo="/login"
    >
      <form className="auth-form" onSubmit={handleSubmit}>
        {/* Si vino por invitación, el rol queda fijado a profesional */}
        {isInvited && (
          <div
            className="auth-info"
            role="status"
            style={{
              backgroundColor: "#eef6ff",
              border: "1px solid #cfe3ff",
              color: "#1d4ed8",
              borderRadius: "8px",
              padding: "0.75rem 1rem",
              fontSize: "0.9rem",
            }}
          >
            Un local te invitó a su equipo. Creá tu cuenta de profesional y vas a
            quedar vinculado automáticamente.
          </div>
        )}

        {/* Selector de rol: segmented control (oculto si vino por invitación) */}
        {!isInvited && (
        <div className="auth-form-group">
          <span className="auth-label">¿Cómo querés usar Appointa?</span>
          <div className="auth-role-selector" role="radiogroup">
            <button
              type="button"
              role="radio"
              aria-checked={role === "client"}
              className={`auth-role-option ${role === "client" ? "is-active" : ""}`}
              onClick={() => setRole("client")}
            >
              Como cliente
            </button>
            <button
              type="button"
              role="radio"
              aria-checked={role === "profesional"}
              className={`auth-role-option ${role === "profesional" ? "is-active" : ""}`}
              onClick={() => setRole("profesional")}
            >
              Como profesional
            </button>
            <button
              type="button"
              role="radio"
              aria-checked={role === "local"}
              className={`auth-role-option ${role === "local" ? "is-active" : ""}`}
              onClick={() => setRole("local")}
            >
              Como local
            </button>
          </div>
        </div>
        )}

        <TextField
          id="fullName"
          label="Nombre completo"
          type="text"
          required
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          placeholder="Tu nombre y apellido"
          autoComplete="name"
        />

        <TextField
          id="email"
          label="Correo electrónico"
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="tu@email.com"
          autoComplete="email"
          readOnly={isInvited && Boolean(invitedEmail)}
        />

        <TextField
          id="phone"
          label="Teléfono"
          type="tel"
          required
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          placeholder="+54 11 1234 5678"
          autoComplete="tel"
        />

        {/* Specialty solo si es profesional */}
        {role === "profesional" && (
          <TextField
            id="specialty"
            label="Especialidad"
            type="text"
            required
            value={specialty}
            onChange={(e) => setSpecialty(e.target.value)}
            placeholder="Ej: peluquería, kinesiología, abogacía..."
          />
        )}

        {/* Local name solo si es local */}
        {role === "local" && (
          <TextField
            id="localName"
            label="Nombre del local"
            type="text"
            required
            value={localName}
            onChange={(e) => setLocalName(e.target.value)}
            placeholder="Ej: Salón Beauty, Clínica Dental..."
          />
        )}

        <TextField
          id="password"
          label="Contraseña"
          type="password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Mínimo 8 caracteres"
          autoComplete="new-password"
        />

        <TextField
          id="confirm"
          label="Confirmar contraseña"
          type="password"
          required
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          placeholder="Repetí tu contraseña"
          autoComplete="new-password"
        />

        {error && <div className="auth-error" role="alert">{error}</div>}

        <button type="submit" disabled={loading} className="auth-submit">
          {loading ? "Creando cuenta..." : "Crear cuenta"}
        </button>
      </form>
    </AuthCard>
  )
}

export default Register