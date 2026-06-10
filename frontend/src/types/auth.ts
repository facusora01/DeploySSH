export type UserRole = "client" | "profesional" | "local"

export interface User {
  id: number
  email: string
  full_name: string
  phone?: string
  public_link?: string
  role: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

export interface LoginPayload {
  email: string
  password: string
}

export interface RegisterPayload {
  role: UserRole
  full_name: string
  email: string
  phone: string
  password: string
  specialty?: string
  local_name?: string
  invitation_token?: string
}