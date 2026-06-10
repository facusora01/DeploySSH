import { useState, type FormEvent } from "react"
import { api, ApiError } from "../utils/api"
import AuthCard from "../components/AuthCard"
import TextField from "../components/TextField"
import "./auth.css"

function ForgotPassword() {
  const [email, setEmail] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [successMessage, setSuccessMessage] = useState("")

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError("")
    setLoading(true)

    try {
      const data = await api.post<{ message: string }>("/api/v1/auth/forgot-password", { email })
      setSuccessMessage(data.message)
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Ocurrió un error inesperado.",
      )
    } finally {
      setLoading(false)
    }
  }

  if (successMessage) {
    return (
      <AuthCard
        title="Revisá tu correo"
        subtitle={successMessage}
        footerText="¿Recordaste tu contraseña?"
        footerLinkLabel="Iniciá sesión"
        footerLinkTo="/login"
      >
        <div />
      </AuthCard>
    )
  }

  return (
    <AuthCard
      title="Olvidé mi contraseña"
      subtitle="Ingresá tu email y te enviamos un enlace para restablecerla."
      footerText="¿Recordaste tu contraseña?"
      footerLinkLabel="Iniciá sesión"
      footerLinkTo="/login"
    >
      <form className="auth-form" onSubmit={handleSubmit}>
        <TextField
          id="email"
          label="Correo electrónico"
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="tu@email.com"
          autoComplete="email"
        />

        {error && <div className="auth-error" role="alert">{error}</div>}

        <button type="submit" disabled={loading} className="auth-submit">
          {loading ? "Enviando..." : "Enviar enlace"}
        </button>
      </form>
    </AuthCard>
  )
}

export default ForgotPassword
