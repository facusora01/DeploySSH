import { useState, type FormEvent } from "react"
import { Link, useNavigate, useSearchParams } from "react-router-dom"
import { api, ApiError } from "../utils/api"
import AuthBackground from "../components/AuthBackground"
import AuthCard from "../components/AuthCard"
import TextField from "../components/TextField"
import "./auth.css"

function ResetPassword() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  const [newPassword, setNewPassword] = useState("")
  const [confirm, setConfirm] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [successMessage, setSuccessMessage] = useState("")

  const token = searchParams.get("token")

  if (!token) {
    return (
      <div className="auth-page">
        <AuthBackground />
        <div className="auth-container">
          <section className="auth-card">
            <header className="auth-header">
              <Link to="/" className="auth-logo">APPOINTA</Link>
              <h1 className="auth-title">Enlace inválido</h1>
              <p className="auth-subtitle">El enlace para restablecer la contraseña no es válido.</p>
            </header>
            <footer className="auth-footer">
              <p className="auth-footer-text">
                <Link to="/forgot-password" className="auth-footer-link">
                  Solicitá un nuevo enlace
                </Link>
              </p>
            </footer>
          </section>
        </div>
      </div>
    )
  }

  if (successMessage) {
    return (
      <AuthCard
        title="¡Contraseña actualizada!"
        subtitle={successMessage}
        footerText=""
        footerLinkLabel="Iniciá sesión"
        footerLinkTo="/login"
      >
        <div />
      </AuthCard>
    )
  }

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError("")

    if (newPassword !== confirm) {
      setError("Las contraseñas no coinciden.")
      return
    }
    if (newPassword.length < 8) {
      setError("La contraseña debe tener al menos 8 caracteres.")
      return
    }

    setLoading(true)
    try {
      const data = await api.post<{ message: string }>("/api/v1/auth/reset-password", {
        token,
        new_password: newPassword,
      })
      setSuccessMessage(data.message)
      setTimeout(() => navigate("/login", { replace: true }), 3000)
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Ocurrió un error inesperado.",
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthCard
      title="Nueva contraseña"
      subtitle="Elegí una contraseña segura para tu cuenta."
      footerText="¿Recordaste tu contraseña?"
      footerLinkLabel="Iniciá sesión"
      footerLinkTo="/login"
    >
      <form className="auth-form" onSubmit={handleSubmit}>
        <TextField
          id="newPassword"
          label="Nueva contraseña"
          type="password"
          required
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
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
          {loading ? "Guardando..." : "Guardar contraseña"}
        </button>
      </form>
    </AuthCard>
  )
}

export default ResetPassword
