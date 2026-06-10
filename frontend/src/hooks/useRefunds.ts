import { useEffect, useState } from "react"
import { api } from "../utils/api"

export interface Refund {
  id: string
  appointment_id: string
  amount: number
  status: "PENDING" | "DONE"
  created_at: string
  appointment_start_time: string
  appointment_service_name: string
  appointment_client_name: string
}

interface UseRefundsOptions {
  status?: "PENDING" | "DONE"
}

export function useRefunds(options?: UseRefundsOptions) {
  const [refunds, setRefunds] = useState<Refund[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  const fetchRefunds = async () => {
    try {
      setLoading(true)
      setError("")
      const url = options?.status
        ? `/api/v1/refunds?status_filter=${options.status}`
        : "/api/v1/refunds"
      const data = await api.get<Refund[]>(url, true)
      setRefunds(data)
    } catch (err: any) {
      setError(err.message || "No se pudieron cargar los reembolsos.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchRefunds()
  }, [options?.status])

  return {
    refunds,
    loading,
    error,
    refetch: fetchRefunds,
  }
}
