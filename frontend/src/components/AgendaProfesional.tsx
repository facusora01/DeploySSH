import { useEffect, useMemo, useState } from "react"
import Icon from "./Icon"
import type { Appointment, Refund } from "./TurnoModal"

type ViewMode = "day" | "week"

interface Props {
  appointments: Appointment[]
  onSelect: (appt: Appointment) => void
  refunds?: Refund[]
  focusDate?: Date | null
}

const statusLabel: Record<string, string> = {
  confirmed: "Confirmado",
  pending: "Pendiente",
  completed: "Completado",
  cancelled: "Cancelado",
  attended: "Asistió",
  no_show: "No asistió",
}

function startOfDay(d: Date) {
  const x = new Date(d)
  x.setHours(0, 0, 0, 0)
  return x
}

function addDays(d: Date, n: number) {
  const x = new Date(d)
  x.setDate(x.getDate() + n)
  return x
}

function sameDay(a: Date, b: Date) {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  )
}

// Lunes como primer día de la semana
function startOfWeek(d: Date) {
  const x = startOfDay(d)
  const dow = (x.getDay() + 6) % 7
  return addDays(x, -dow)
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString("es-AR", { hour: "2-digit", minute: "2-digit" })
}

function AgendaProfesional({ appointments, onSelect, refunds = [], focusDate }: Props) {
  const [view, setView] = useState<ViewMode>("day")
  const [cursor, setCursor] = useState<Date>(() => startOfDay(new Date()))

  // Posicionar el calendario en la fecha del turno enfocado (desde notificación)
  useEffect(() => {
    if (focusDate) setCursor(startOfDay(focusDate))
  }, [focusDate])

  const refundMap = useMemo(
    () => new Map(refunds.map((r) => [r.appointment_id, r])),
    [refunds]
  )

  const sorted = useMemo(
    () =>
      [...appointments].sort(
        (a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
      ),
    [appointments]
  )

  function shift(dir: number) {
    setCursor((c) => addDays(c, dir * (view === "week" ? 7 : 1)))
  }

  const weekStart = startOfWeek(cursor)
  const weekDays = Array.from({ length: 7 }, (_, i) => addDays(weekStart, i))

  const dayAppts = sorted.filter((a) => sameDay(new Date(a.start_time), cursor))

  const rangeLabel =
    view === "day"
      ? cursor.toLocaleDateString("es-AR", {
          weekday: "long",
          day: "numeric",
          month: "long",
          year: "numeric",
        })
      : `${weekStart.toLocaleDateString("es-AR", { day: "numeric", month: "short" })} – ${addDays(
          weekStart,
          6
        ).toLocaleDateString("es-AR", { day: "numeric", month: "short", year: "numeric" })}`

  function renderCard(appt: Appointment, compact = false) {
    const refund = refundMap.get(appt.id)

    if (compact) {
      return (
        <div key={appt.id} style={{ position: "relative" }}>
          <button
            className={`cal-chip turno-status--${appt.status} ${appt.status === "cancelled" ? "is-cancelled" : ""}`}
            onClick={() => onSelect(appt)}
            title={`${formatTime(appt.start_time)} · ${appt.cliente_name} · ${statusLabel[appt.status] ?? appt.status}${refund ? ` · Reembolso ${refund.status === "PENDING" ? "pendiente" : "realizado"}` : ""}`}
          >
            <span className="cal-chip-time">{formatTime(appt.start_time)}</span>
            <span className="cal-chip-client">{appt.cliente_name}</span>
          </button>
          {refund && appt.status === "cancelled" && (
            <span className={`cal-chip-refund-badge refund-status--${refund.status.toLowerCase()}`}>
              {refund.status === "PENDING" ? "💸" : "✓"}
            </span>
          )}
        </div>
      )
    }

    return (
      <button
        key={appt.id}
        className={`turno-card-compact cal-card ${appt.status === "cancelled" ? "is-cancelled" : ""}`}
        onClick={() => onSelect(appt)}
      >
        <span className="cal-card-time">
          <Icon name="clock" size={13} />
          {formatTime(appt.start_time)}
        </span>
        <span className="turno-compact-service">{appt.service_name}</span>
        <span className="turno-compact-meta-item">
          <Icon name="users" size={13} />
          {appt.cliente_name}
        </span>
        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <span className={`turno-status-badge turno-status--${appt.status}`}>
            {statusLabel[appt.status] ?? appt.status}
          </span>
          {refund && appt.status === "cancelled" && (
            <span className={`turno-status-badge refund-status--${refund.status.toLowerCase()}`}>
              {refund.status === "PENDING" ? "Reembolso pendiente" : "Reembolsado"}
            </span>
          )}
        </div>
      </button>
    )
  }

  return (
    <div className="cal-pro">
      <div className="cal-toolbar">
        <div className="cal-view-toggle">
          <button
            className={view === "day" ? "is-active" : ""}
            onClick={() => setView("day")}
          >
            Día
          </button>
          <button
            className={view === "week" ? "is-active" : ""}
            onClick={() => setView("week")}
          >
            Semana
          </button>
        </div>

        <div className="cal-nav">
          <button
            className="cal-nav-btn cal-today-btn"
            onClick={() => setCursor(startOfDay(new Date()))}
          >
            Hoy
          </button>
          <div className="cal-nav-cluster">
            <button className="cal-nav-btn" onClick={() => shift(-1)} aria-label="Anterior">
              <Icon name="chevron-right" size={16} style={{ transform: "rotate(180deg)" }} />
            </button>
            <span className="cal-range" style={{ textTransform: "capitalize" }}>
              {rangeLabel}
            </span>
            <button className="cal-nav-btn" onClick={() => shift(1)} aria-label="Siguiente">
              <Icon name="chevron-right" size={16} />
            </button>
          </div>
        </div>
      </div>

      {view === "day" ? (
        dayAppts.length === 0 ? (
          <section className="turnos-empty">
            <p className="turnos-empty-title">No tenés turnos este día</p>
            <p className="turnos-empty-text">Probá navegando a otra fecha.</p>
          </section>
        ) : (
          <div className="turnos-list">{dayAppts.map((a) => renderCard(a))}</div>
        )
      ) : (
        <div className="cal-week">
          {weekDays.map((day) => {
            const dayItems = sorted.filter((a) => sameDay(new Date(a.start_time), day))
            const isToday = sameDay(day, new Date())
            return (
              <div key={day.toISOString()} className={`cal-week-col ${isToday ? "is-today" : ""}`}>
                <div className="cal-week-head">
                  <span className="cal-week-dow">
                    {day.toLocaleDateString("es-AR", { weekday: "short" })}
                  </span>
                  <span className="cal-week-daynum">{day.getDate()}</span>
                </div>
                <div className="cal-week-body">
                  {dayItems.length === 0 ? (
                    <span className="cal-week-empty">Sin turnos</span>
                  ) : (
                    dayItems.map((a) => renderCard(a, true))
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default AgendaProfesional
