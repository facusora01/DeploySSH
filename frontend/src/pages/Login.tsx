import { useEffect, useState, type FormEvent } from "react"
import { Link, useNavigate, useSearchParams } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import { ApiError } from "../utils/api"
import AuthCard from "../components/AuthCard"
import TextField from "../components/TextField"
import "./auth.css"

function Login() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const next = searchParams.get("next")
  const { user, login: authLogin } = useAuth()

  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  // Si ya está logueado, no tiene sentido ver el login → al home (o a `next`)
  useEffect(() => {
    if (user) navigate(next || "/", { replace: true })
  }, [user, navigate, next])

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError("")
    setLoading(true)

    try {
      const loggedInUser = await authLogin({ email, password })
      // Si vino con `next` (p. ej. desde una invitación), respetamos ese destino.
      // Si no, perfil para locales, home para el resto.
      const redirectPath = next || (loggedInUser.role === "local" ? "/perfil" : "/")
      navigate(redirectPath, { replace: true })
    } catch (err) {
      if (err instanceof ApiError) {
        setError(
          err.status === 401
            ? "Credenciales inválidas. Verificá tu email y contraseña."
            : err.status === 403
              ? "Debés confirmar tu correo electrónico antes de iniciar sesión. Revisá tu bandeja de entrada."
              : err.message,
        )
      } else {
        setError("Ocurrió un error inesperado.")
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthCard
      title="Bienvenido de nuevo"
      subtitle="Ingresá a tu cuenta para continuar"
      footerText="¿No tenés cuenta?"
      footerLinkLabel="Registrate gratis"
      footerLinkTo="/register"
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

        <TextField
          id="password"
          label="Contraseña"
          type="password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
          autoComplete="current-password"
        />

        {error && <div className="auth-error" role="alert">{error}</div>}

        <div style={{ textAlign: "right", marginTop: "-8px" }}>
          <Link to="/forgot-password" className="auth-footer-link" style={{ fontSize: "0.875rem" }}>
            ¿Olvidaste tu contraseña?
          </Link>
        </div>

        <button type="submit" disabled={loading} className="auth-submit">
          {loading ? "Ingresando..." : "Iniciar sesión"}
        </button>
      </form>
    </AuthCard>
  )
}

export default Login