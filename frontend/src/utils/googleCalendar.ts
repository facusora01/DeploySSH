interface CalendarEventParams {
  title: string
  startTime: string
  endTime: string
  details?: string
  location?: string
}

function formatGoogleDate(iso: string): string {
  const date = new Date(iso)
  return date.toISOString().replace(/[-:]/g, "").split(".")[0] + "Z"
}

export function buildGoogleCalendarUrl(params: CalendarEventParams): string {
  const url = new URL("https://calendar.google.com/calendar/render")
  url.searchParams.set("action", "TEMPLATE")
  url.searchParams.set("text", params.title)
  url.searchParams.set(
    "dates",
    `${formatGoogleDate(params.startTime)}/${formatGoogleDate(params.endTime)}`
  )
  if (params.details) url.searchParams.set("details", params.details)
  if (params.location) url.searchParams.set("location", params.location)
  return url.toString()
}