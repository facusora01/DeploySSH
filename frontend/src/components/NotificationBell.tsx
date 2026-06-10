import { useEffect, useRef, useState } from "react"
import { useNavigate } from "react-router-dom"
import {
  useNotifications,
  type Notification,
  type NotificationType,
} from "../hooks/useNotifications"
import Icon from "./Icon"
import type { IconName } from "./Icon"
import "../pages/notification-bell.css"

const TYPE_ICON: Record<NotificationType, IconName> = {
  APPOINTMENT_BOOKED: "calendar",
  APPOINTMENT_CANCELLED_BY_CLIENT: "x",
  APPOINTMENT_CANCELLED_BY_PROFESIONAL: "x",
  REFUND_PENDING: "banknote",
  REFUND_DONE: "check-circle",
  REMINDER: "clock",
  TEAM_INVITATION: "users",
}

// Destino de navegación al hacer click en cada tipo de notificación
const TYPE_ROUTE: Record<NotificationType, string> = {
  APPOINTMENT_BOOKED: "/turnos",
  APPOINTMENT_CANCELLED_BY_CLIENT: "/turnos",        // recibe profesional
  APPOINTMENT_CANCELLED_BY_PROFESIONAL: "/historial", // recibe cliente
  REFUND_PENDING: "/reembolsos",
  REFUND_DONE: "/reembolsos",
  REMINDER: "/turnos",
  TEAM_INVITATION: "/invitaciones",
}

function formatRelative(iso: string): string {
  const date = new Date(iso)
  const diffMs = Date.now() - date.getTime()
  const diffMin = Math.round(diffMs / 60000)
  if (diffMin < 1) return "Recién"
  if (diffMin < 60) return `Hace ${diffMin} min`
  const diffH = Math.round(diffMin / 60)
  if (diffH < 24) return `Hace ${diffH} h`
  return date.toLocaleDateString("es-AR", { day: "numeric", month: "short" })
}

function NotificationBell() {
  const { notifications, unreadCount, markRead, markAllRead } =
    useNotifications()
  const [showDropdown, setShowDropdown] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()

  // Cerrar al hacer click fuera
  useEffect(() => {
    if (!showDropdown) return
    function handleClickOutside(e: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setShowDropdown(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [showDropdown])

  const handleItemClick = (notif: Notification) => {
    if (!notif.is_read) markRead(notif.id)
    setShowDropdown(false)
    const base = TYPE_ROUTE[notif.type] ?? "/turnos"
    const to = notif.appointment_id
      ? `${base}?appointment=${notif.appointment_id}`
      : base
    navigate(to)
  }

  return (
    <div className="notification-bell-container" ref={containerRef}>
      <button
        className="notification-bell-btn"
        onClick={() => setShowDropdown((v) => !v)}
        title="Notificaciones"
        aria-label="Notificaciones"
      >
        <Icon name="bell" size={27} />
        {unreadCount > 0 && (
          <span className="notification-badge">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {showDropdown && (
        <div className="notification-dropdown">
          <div className="notification-header">
            <span className="notification-title">Notificaciones</span>
            <div className="notification-header-actions">
              {unreadCount > 0 && (
                <button
                  className="notification-markall"
                  onClick={markAllRead}
                >
                  Marcar todas
                </button>
              )}
              <button
                className="notification-close"
                onClick={() => setShowDropdown(false)}
                aria-label="Cerrar"
              >
                <Icon name="x" size={16} />
              </button>
            </div>
          </div>

          {notifications.length === 0 ? (
            <div className="notification-empty">
              <p>No tenés notificaciones</p>
            </div>
          ) : (
            <div className="notification-list">
              {notifications.map((notif) => (
                <button
                  key={notif.id}
                  type="button"
                  className={`notification-item ${
                    notif.is_read ? "" : "is-unread"
                  }`}
                  onClick={() => handleItemClick(notif)}
                >
                  <span className="notification-item-icon">
                    <Icon name={TYPE_ICON[notif.type]} size={18} />
                  </span>
                  <span className="notification-item-body">
                    <span className="notification-item-title">
                      {notif.title}
                    </span>
                    <span className="notification-item-message">
                      {notif.message}
                    </span>
                    <span className="notification-item-date">
                      {formatRelative(notif.created_at)}
                    </span>
                  </span>
                  {!notif.is_read && <span className="notification-item-dot" />}
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default NotificationBell
