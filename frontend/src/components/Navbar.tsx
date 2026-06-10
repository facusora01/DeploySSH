import { NavLink } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import "../pages/navbar.css"
import UserMenu from "./UserMenu"
import NotificationBell from "./NotificationBell"

interface NavItem {
  to: string
  label: string
  end?: boolean
}

const BASE_NAV_ITEMS: NavItem[] = [
  { to: "/turnos", label: "Turnos" },
  { to: "/historial", label: "Historial" },
  { to: "/reembolsos", label: "Reembolsos" },
]

const PROFESIONAL_NAV_ITEMS: NavItem[] = [
  { to: "/servicios", label: "Servicios" },
  { to: "/clientes", label: "Clientes" },
  { to: "/agenda", label: "Agenda" },
  { to: "/formulario", label: "Formulario" },
]

const LOCAL_NAV_ITEMS: NavItem[] = [
  { to: "/equipo", label: "Equipo" },
]

function Navbar() {
  const { user } = useAuth()
  const isProfesional = user?.role === "profesional"
  const isLocal = user?.role === "local"
  const navItems = isProfesional
    ? [...BASE_NAV_ITEMS, ...PROFESIONAL_NAV_ITEMS]
    : isLocal
      ? [...BASE_NAV_ITEMS, ...LOCAL_NAV_ITEMS]
      : BASE_NAV_ITEMS

  return (
    <nav className="navbar" aria-label="Navegación principal">
      <div className="navbar-inner">
        <NavLink to="/" className="navbar-logo">
          APPOINTA
        </NavLink>

        <ul className="navbar-items">
          {navItems.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `navbar-item ${isActive ? "is-active" : ""}`
                }
              >
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>

        <div className="navbar-actions">
          <NotificationBell />
          <UserMenu />
        </div>
      </div>
    </nav>
  )
}

export default Navbar
