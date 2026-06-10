// Tipos para la feature de servicios del profesional.
// El back devuelve `price` como string porque Pydantic serializa Decimal así.

export interface Service {
  id: string
  profesional_id: number
  name: string
  description: string | null
  duration_minutes: number
  price: string | null
  max_slots: number
  is_active: boolean
  deposit_active: boolean
  deposit_amount: string | null
  deposit_required: boolean
  created_at: string
  updated_at: string
}

export interface ServiceCreatePayload {
  name: string
  description?: string | null
  duration_minutes: number
  price?: number | null
  max_slots?: number
  deposit_active?: boolean
  deposit_amount?: number | null
  deposit_required?: boolean
}

// ServiceUpdate es lo mismo que Create pero todos opcionales — el back acepta
// PATCH parcial. Lo dejamos como type-alias parcial para no repetir.
export type ServiceUpdatePayload = Partial<ServiceCreatePayload>