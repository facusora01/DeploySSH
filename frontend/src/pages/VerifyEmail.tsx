import { useEffect, useState } from "react"
import { Link, useSearchParams } from "react-router-dom"
import { api, ApiError } from "../utils/api"
import AuthBackground from "../components/AuthBackground"
import "./auth.css"

type Status = "loading" | "success" | "error"

function VerifyEmail() {
  const [searchParams] = useSearchParams()
  const [status, setStatus] = useState<Status>("loading")
  const [message, setMessage] = useState("")

  useEffect(() => {
    const token = searchParams.get("token")
    if (!token) {
      setStatus("error")
      setMessage("El enlace de verificación no es válido.")
      return
    }

    api
      .get<{ message: string }>(`/api/v1/auth/verify-email?token=${encodeURIComponent(token)}`)
      .then((data) => {
        setStatus("success")
        setMessage(data.message)
      })
      .catch((err) => {
        setStatus("error")
        setMessage(
          err instanceof ApiError
            ? err.message
            : "El enlace de verificación es inválido o ya expiró.",
        )
      })
  }, [searchParams])

  return (
    <div className="auth-page">
      <AuthBackground />
      <div className="auth-container">
        <section className="auth-card">
          <header className="auth-header">
            <Link to="/" className="auth-logo">APPOINTA</Link>
            <h1 className="auth-title">
              {status === "loading" && "Verificando tu cuenta..."}
              {status === "success" && "¡Cuenta verificada!"}
              {status === "error" && "Enlace inválido"}
            </h1>
            <p className="auth-subtitle">
              {status === "loading" && "Un momento, por favor."}
              {status !== "loading" && message}
            </p>
          </header>

          {status !== "loading" && (
            <div style={{ marginTop: "24px", textAlign: "center" }}>
              <Link to="/login" className="auth-submit" style={{ display: "inline-block", textDecoration: "none" }}>
                Ir al inicio de sesión
              </Link>
            </div>
          )}

          <footer className="auth-footer">
            <p className="auth-footer-text">
              ¿No tenés cuenta?{" "}
              <Link to="/register" className="auth-footer-link">
                Registrate gratis
              </Link>
            </p>
          </footer>
        </section>
      </div>
    </div>
  )
}

export default VerifyEmail
