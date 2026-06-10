import { Navigate, Outlet } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import Navbar from "./Navbar"

function ProtectedLayout() {
  const { user, loading } = useAuth()

  if (loading) return null
  if (!user) return <Navigate to="/login" replace />

  return (
    <>
      <Navbar />
      <main className="app-main">
        <Outlet />
      </main>
    </>
  )
}

export default ProtectedLayout