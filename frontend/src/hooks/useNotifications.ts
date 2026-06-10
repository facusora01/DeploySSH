import { useCallback, useEffect, useRef, useState } from "react"
import { api } from "../utils/api"

export type NotificationType =
  | "APPOINTMENT_BOOKED"
  | "APPOINTMENT_CANCELLED_BY_CLIENT"
  | "APPOINTMENT_CANCELLED_BY_PROFESIONAL"
  | "REFUND_PENDING"
  | "REFUND_DONE"
  | "REMINDER"
  | "TEAM_INVITATION"

export interface Notification {
  id: string
  type: NotificationType
  title: string
  message: string
  appointment_id: string | null
  is_read: boolean
  created_at: string
}

const POLL_INTERVAL_MS = 30_000

export function useNotifications() {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const fetchNotifications = useCallback(async () => {
    try {
      setError("")
      const data = await api.get<Notification[]>("/api/v1/notifications", true)
      setNotifications(data)
    } catch (err: any) {
      setError(err?.message || "No se pudieron cargar las notificaciones.")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchNotifications()
    timerRef.current = setInterval(fetchNotifications, POLL_INTERVAL_MS)
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [fetchNotifications])

  const markRead = useCallback(async (id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
    )
    try {
      await api.patch(`/api/v1/notifications/${id}/read`, undefined, true)
    } catch {
      // si falla, el próximo poll corrige el estado
    }
  }, [])

  const markAllRead = useCallback(async () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })))
    try {
      await api.patch("/api/v1/notifications/read-all", undefined, true)
    } catch {
      // idem
    }
  }, [])

  const unreadCount = notifications.filter((n) => !n.is_read).length

  return {
    notifications,
    unreadCount,
    loading,
    error,
    refetch: fetchNotifications,
    markRead,
    markAllRead,
  }
}
