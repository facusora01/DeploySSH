import { useEffect, useRef, useState } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import { api } from "../utils/api"

// Toma "Juan Pérez" → "JP", "Mariana" → "M", etc.
function getInitials(fullName: string): string {
  const parts = fullName.trim().split(/\s+/).filter(Boolean)
  if (parts.length === 0) return "?"
  if (parts.length === 1) return parts[0][0].toUpperCase()
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}

function UserMenu() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const [open, setOpen] = useState(false)
  const [loggingOut, setLoggingOut] = useState(false)
  const [localData, setLocalData] = useState<any>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (user?.role === "local") {
      api.get<any>("/api/v1/locales/me", true)
        .then(data => setLocalData(data))
        .catch(err => console.error("Error fetching local data:", err))
    }
  }, [user])

  // Cerrar al hacer click afuera
  useEffect(() => {
    if (!open) return
    function handleClickOutside(e: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setOpen(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [open])

  // Cerrar al apretar Escape
  useEffect(() => {
    if (!open) return
    function handleEscape(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false)
    }
    document.addEventListener("keydown", handleEscape)
    return () => document.removeEventListener("keydown", handleEscape)
  }, [open])

  if (!user) return null

  async function handleLogout() {
    setLoggingOut(true)
    setOpen(false)
    try {
      await logout()
    } finally {
      navigate("/login", { replace: true })
    }
  }

  function handleNavigate(to: string) {
    setOpen(false)
    navigate(to)
  }

  const isLocal = user.role === "local"
  const displayName = isLocal && localData ? localData.local_name : user.full_name
  const displayInitials = getInitials(displayName)

  return (
    <div className="navbar-user" ref={containerRef}>
      <button
        type="button"
        className="navbar-avatar"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label="Menú de usuario"
        style={isLocal && localData?.logo_url ? { padding: 0, overflow: "hidden" } : undefined}
      >
        {isLocal && localData?.logo_url ? (
          <img
            src={localData.logo_url}
            alt={displayName}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        ) : (
          displayInitials
        )}
      </button>

      {open && (
        <div className="navbar-dropdown" role="menu">
          <div className="navbar-dropdown-header">
            <p className="navbar-dropdown-name">{displayName}</p>
            {!isLocal && <p className="navbar-dropdown-email">{user.email}</p>}
          </div>
          <div className="navbar-dropdown-divider" />
          <button
            type="button"
            role="menuitem"
            className="navbar-dropdown-item"
            onClick={() => handleNavigate("/perfil")}
          >
            Mi perfil
          </button>
          <button
            type="button"
            role="menuitem"
            className="navbar-dropdown-item navbar-dropdown-item--danger"
            onClick={handleLogout}
            disabled={loggingOut}
          >
            {loggingOut ? "Cerrando..." : "Cerrar sesión"}
          </button>
        </div>
      )}
    </div>
  )
}

export default UserMenu