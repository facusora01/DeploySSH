export const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000"

const ACCESS_TOKEN_KEY = "appointa_access_token"
const REFRESH_TOKEN_KEY = "appointa_refresh_token"

// Callback que el AuthContext registra. Lo llamamos cuando el refresh falla
// (sesión expirada) para que el Context limpie su estado y la app reaccione.
let onAuthFailureCallback: (() => void) | null = null
export function setOnAuthFailure(cb: () => void) {
  onAuthFailureCallback = cb
}

export class ApiError extends Error {
  status: number
  detail?: unknown

  constructor(message: string, status: number, detail?: unknown) {
    super(message)
    this.name = "ApiError"
    this.status = status
    this.detail = detail
  }
}

function extractErrorMessage(body: unknown, fallback: string): string {
  if (!body || typeof body !== "object") return fallback
  const detail = (body as { detail?: unknown }).detail
  if (typeof detail === "string") return detail
  if (detail && typeof detail === "object" && "message" in detail) {
    return String((detail as { message: unknown }).message)
  }
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0]
    if (first && typeof first === "object" && "msg" in first) {
      return String((first as { msg: unknown }).msg)
    }
  }
  return fallback
}

interface RawRequestOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE"
  body?: unknown
  token?: string | null // si viene, lo manda como Bearer
}

// Llamada cruda al back. NO maneja refresh por sí sola.
async function rawRequest<T>(path: string, options: RawRequestOptions = {}): Promise<T> {
  const { method = "GET", body, token } = options

  const headers: Record<string, string> = { "Content-Type": "application/json" }
  if (token) headers["Authorization"] = `Bearer ${token}`

  let response: Response
  try {
    response = await fetch(`${API_URL}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    })
  } catch {
    throw new ApiError("No se pudo conectar con el servidor.", 0)
  }

  if (response.status === 204) return undefined as T

  let data: unknown = null
  try {
    data = await response.json()
  } catch {
    // sin body válido
  }

  if (!response.ok) {
    const detail =
      data && typeof data === "object" && "detail" in data
        ? (data as { detail?: unknown }).detail
        : undefined
    throw new ApiError(
      extractErrorMessage(data, "Ocurrió un error inesperado."),
      response.status,
      detail,
    )
  }
  return data as T
}

// --- Refresh con deduplicación ---
// Si hay un refresh en vuelo, las demás requests esperan al mismo Promise.
let refreshInFlight: Promise<string> | null = null

interface RefreshResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

async function performRefresh(): Promise<string> {
  const currentRefresh = localStorage.getItem(REFRESH_TOKEN_KEY)
  if (!currentRefresh) throw new ApiError("No hay refresh token", 401)

  const data = await rawRequest<RefreshResponse>("/api/v1/auth/refresh", {
    method: "POST",
    body: { refresh_token: currentRefresh },
  })

  localStorage.setItem(ACCESS_TOKEN_KEY, data.access_token)
  localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token)
  return data.access_token
}

function refreshAccessToken(): Promise<string> {
  if (!refreshInFlight) {
    refreshInFlight = performRefresh().finally(() => {
      refreshInFlight = null
    })
  }
  return refreshInFlight
}

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE"
  body?: unknown
  auth?: boolean
}

// Cliente público con manejo de refresh transparente.
async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, auth = false } = options

  if (!auth) {
    return rawRequest<T>(path, { method, body })
  }

  const token = localStorage.getItem(ACCESS_TOKEN_KEY)
  try {
    return await rawRequest<T>(path, { method, body, token })
  } catch (err) {
    if (!(err instanceof ApiError) || err.status !== 401) throw err

    // 401 → intento refrescar una sola vez
    let newToken: string
    try {
      newToken = await refreshAccessToken()
    } catch {
      // El refresh falló (refresh token vencido/revocado) → sesión muerta
      localStorage.removeItem(ACCESS_TOKEN_KEY)
      localStorage.removeItem(REFRESH_TOKEN_KEY)
      onAuthFailureCallback?.()
      throw new ApiError("Sesión expirada.", 401)
    }

    // Reintento con el token nuevo
    return rawRequest<T>(path, { method, body, token: newToken })
  }
}

export const api = {
  get: <T>(path: string, auth = false) => request<T>(path, { method: "GET", auth }),
  post: <T>(path: string, body?: unknown, auth = false) =>
    request<T>(path, { method: "POST", body, auth }),
  put: <T>(path: string, body?: unknown, auth = false) =>
    request<T>(path, { method: "PUT", body, auth }),
  patch: <T>(path: string, body?: unknown, auth = false) =>
    request<T>(path, { method: "PATCH", body, auth }),
  delete: <T>(path: string, auth = false) =>
    request<T>(path, { method: "DELETE", auth }),

}

export { ACCESS_TOKEN_KEY, REFRESH_TOKEN_KEY }
