import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react"
import {
  api,
  ACCESS_TOKEN_KEY,
  REFRESH_TOKEN_KEY,
  setOnAuthFailure,
} from "../utils/api"
import type {
  AuthResponse,
  LoginPayload,
  RegisterPayload,
  User,
} from "../types/auth"

const USER_KEY = "appointa_user"

interface AuthContextValue {
  user: User | null
  loading: boolean
  login: (payload: LoginPayload) => Promise<User>
  register: (payload: RegisterPayload) => Promise<string>
  logout: () => Promise<void>
  updateUserProfile: (data: { full_name?: string, phone?: string }) => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const stored = localStorage.getItem(USER_KEY)
    if (stored) {
      try {
        setUser(JSON.parse(stored) as User)
      } catch {
        localStorage.removeItem(USER_KEY)
      }
    }
    setLoading(false)
  }, [])

  // Cuando el api detecta sesión muerta (refresh falló), limpiamos el user.
  // Esto hace que ProtectedRoute redirija solo a /login.
  useEffect(() => {
    setOnAuthFailure(() => {
      localStorage.removeItem(USER_KEY)
      setUser(null)
    })
  }, [])

  function persistSession(data: AuthResponse) {
    localStorage.setItem(ACCESS_TOKEN_KEY, data.access_token)
    localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token)
    localStorage.setItem(USER_KEY, JSON.stringify(data.user))
    setUser(data.user)
  }

  async function login(payload: LoginPayload): Promise<User> {
    const data = await api.post<AuthResponse>("/api/v1/auth/login", payload)
    persistSession(data)
    return data.user
  }

  async function register(payload: RegisterPayload): Promise<string> {
    const data = await api.post<{ message: string }>("/api/v1/auth/register", payload)
    return data.message
  }

  async function logout() {
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)

    // Intentamos revocar el refresh token en el back.
    // Si falla (red, token ya vencido, etc.) igual hacemos logout local —
    // priorizar la UX: el usuario quiere salir, no queremos bloquearlo.
    if (refreshToken) {
      try {
        await api.post("/api/v1/auth/logout", { refresh_token: refreshToken })
      } catch {
        // ignore
      }
    }

    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    setUser(null)
  }

  async function updateUserProfile(data: { full_name?: string, phone?: string }) {
    const updatedUser = await api.put<User>("/api/v1/users/me", data, true)
    localStorage.setItem(USER_KEY, JSON.stringify(updatedUser))
    setUser(updatedUser)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, updateUserProfile }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth debe usarse dentro de <AuthProvider>")
  return ctx
}