import { useEffect, useState } from "react"
import { Link, useNavigate, useSearchParams } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import { api, ApiError } from "../utils/api"
import AuthBackground from "../components/AuthBackground"
import "./auth.css"

interface InvitationInfo {
  local_name: string
  email: string
  status: "pending" | "accepted" | "expired" | "cancelled" | "rejected"
  expired: boolean
  account_exists: boolean
  account_is_profesional: boolean
}

function Shell({ title, subtitle, children }: { title: string; subtitle?: string; children?: React.ReactNode }) {
  return (
    <div className="auth-page">
      <AuthBackground />
      <div className="auth-container">
        <section className="auth-card">
          <header className="auth-header">
            <Link to="/" className="auth-logo">APPOINTA</Link>
            <h1 className="auth-title">{title}</h1>
            {subtitle && <p className="auth-subtitle">{subtitle}</p>}
          </header>
          {children}
        </section>
      </div>
    </div>
  )
}

function Invitacion() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [searchParams] = useSearchParams()
  const token = searchParams.get("token") ?? ""

  const [info, setInfo] = useState<InvitationInfo | null>(null)
  const [loadError, setLoadError] = useState("")
  const [loading, setLoading] = useState(true)
  const [accepting, setAccepting] = useState(false)
  const [acceptError, setAcceptError] = useState("")
  const [accepted, setAccepted] = useState("")
  const [rejected, setRejected] = useState(false)

  useEffect(() => {
    if (!token) return
    api
      .get<InvitationInfo>(`/api/v1/locales/invitations/${token}`)
      .then((data) => setInfo(data))
      .catch((err) => {
        if (err instanceof ApiError && err.status === 404)
          setLoadError("No encontramos esta invitación. Puede haber sido cancelada.")
        else setLoadError("No se pudo cargar la invitación.")
      })
      .finally(() => setLoading(false))
  }, [token])

  async function handleAccept() {
    setAcceptError("")
    setAccepting(true)
    try {
      const res = await api.post<{ message: string }>(
        `/api/v1/locales/invitations/${token}/accept`,
        undefined,
        true,
      )
      setAccepted(res.message)
    } catch (err) {
      if (err instanceof ApiError) setAcceptError(err.message)
      else setAcceptError("No se pudo aceptar la invitación.")
    } finally {
      setAccepting(false)
    }
  }

  async function handleReject() {
    setAcceptError("")
    setAccepting(true)
    try {
      await api.post(
        `/api/v1/locales/invitations/${token}/reject`,
        undefined,
        true,
      )
      setRejected(true)
    } catch (err) {
      if (err instanceof ApiError) setAcceptError(err.message)
      else setAcceptError("No se pudo rechazar la invitación.")
    } finally {
      setAccepting(false)
    }
  }

  if (!token) return <Shell title="Invitación no disponible" subtitle="Link de invitación inválido." />

  if (loading) return <Shell title="Cargando invitación..." />

  if (loadError) return <Shell title="Invitación no disponible" subtitle={loadError} />

  if (!info) return null

  if (accepted) {
    return (
      <Shell title="¡Bienvenido al equipo!" subtitle={accepted}>
        <button className="auth-submit" onClick={() => navigate("/agenda")}>
          Ir a mi agenda
        </button>
      </Shell>
    )
  }

  if (rejected) {
    return (
      <Shell
        title="Invitación rechazada"
        subtitle={`Rechazaste la invitación de ${info.local_name}.`}
      />
    )
  }

  if (info.status === "accepted") {
    return <Shell title="Invitación ya aceptada" subtitle="Esta invitación ya fue utilizada." />
  }

  if (info.status === "rejected") {
    return <Shell title="Invitación rechazada" subtitle="Ya rechazaste esta invitación." />
  }

  if (info.status === "cancelled") {
    return <Shell title="Invitación no disponible" subtitle="Esta invitación fue cancelada por el local." />
  }

  if (info.expired || info.status === "expired") {
    return (
      <Shell
        title="La invitación expiró"
        subtitle={`Pedile a ${info.local_name} que te reenvíe una nueva invitación.`}
      />
    )
  }

  // Invitación válida y pendiente
  const subtitle = `${info.local_name} te invitó a sumarte a su equipo (${info.email}).`

  // Cuenta existe pero no es de profesional → no se puede vincular
  if (info.account_exists && !info.account_is_profesional) {
    return (
      <Shell title="No podemos vincular esta cuenta" subtitle={subtitle}>
        <p className="auth-subtitle" style={{ marginTop: "0.5rem" }}>
          El correo {info.email} ya tiene una cuenta que no es de profesional. Las
          invitaciones solo pueden vincularse a cuentas de profesional.
        </p>
      </Shell>
    )
  }

  // No tiene cuenta → registro como profesional con el token
  if (!info.account_exists) {
    const registerHref = `/register?invitation=${encodeURIComponent(token)}&email=${encodeURIComponent(info.email)}`
    return (
      <Shell title="Sumate al equipo" subtitle={subtitle}>
        <p className="auth-subtitle" style={{ marginTop: "0.5rem" }}>
          Creá tu cuenta de profesional y vas a quedar vinculado automáticamente.
        </p>
        <Link to={registerHref} className="auth-submit" style={{ display: "block", textAlign: "center", textDecoration: "none" }}>
          Crear mi cuenta
        </Link>
      </Shell>
    )
  }

  // Tiene cuenta de profesional → debe estar logueado con ese email para aceptar
  const loggedInAsInvitee =
    Boolean(user) && user!.email.toLowerCase() === info.email.toLowerCase()

  if (!loggedInAsInvitee) {
    const loginHref = `/login?next=${encodeURIComponent(`/invitacion?token=${token}`)}`
    return (
      <Shell title="Sumate al equipo" subtitle={subtitle}>
        <p className="auth-subtitle" style={{ marginTop: "0.5rem" }}>
          Iniciá sesión con {info.email} para aceptar la invitación.
        </p>
        <Link to={loginHref} className="auth-submit" style={{ display: "block", textAlign: "center", textDecoration: "none" }}>
          Iniciar sesión
        </Link>
      </Shell>
    )
  }

  return (
    <Shell title="Sumate al equipo" subtitle={subtitle}>
      {acceptError && (
        <div className="auth-error" role="alert">{acceptError}</div>
      )}
      <button className="auth-submit" disabled={accepting} onClick={handleAccept}>
        {accepting ? "Procesando..." : `Unirme a ${info.local_name}`}
      </button>
      <button
        type="button"
        className="auth-submit"
        disabled={accepting}
        onClick={handleReject}
        style={{
          marginTop: "0.5rem",
          background: "transparent",
          color: "#c0392b",
          border: "1px solid #e6b0aa",
        }}
      >
        Rechazar invitación
      </button>
    </Shell>
  )
}

export default Invitacion
