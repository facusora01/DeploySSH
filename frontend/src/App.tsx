import { Routes, Route, Navigate } from "react-router-dom"
import Landing from "./pages/Landing"
import Login from "./pages/Login"
import Register from "./pages/Register"
import VerifyEmail from "./pages/VerifyEmail"
import ForgotPassword from "./pages/ForgotPassword"
import ResetPassword from "./pages/ResetPassword"
import Turnos from "./pages/Turnos"
import Historial from "./pages/Historial"
import Reembolsos from "./pages/Reembolsos"
import Perfil from "./pages/Perfil"
import EditarPerfil from "./pages/EditarPerfil"
import PublicProfile from "./pages/PublicProfile"
import MisServicios from "./pages/MisServicios"
import Clientes from "./pages/Clientes"
import Agenda from "./pages/Agenda"
import ReservarTurno from "./pages/ReservarTurno"
import FormularioConfig from "./pages/FormularioConfig"
import PublicLocalProfile from "./pages/PublicLocalProfile"
import Equipo from "./pages/Equipo"
import GestionarProfesional from "./pages/GestionarProfesional"
import Invitacion from "./pages/Invitacion"
import InvitacionesRecibidas from "./pages/InvitacionesRecibidas"
import ProtectedLayout from "./components/ProtectedLayout"

function App() {
  return (
    <Routes>
      {/* Pública: la landing redirige a /turnos si hay sesión */}
      <Route path="/" element={<Landing />} />

      {/* Rutas protegidas: comparten layout con navbar */}
      <Route element={<ProtectedLayout />}>
        <Route path="/turnos" element={<Turnos />} />
        <Route path="/historial" element={<Historial />} />
        <Route path="/reembolsos" element={<Reembolsos />} />
        <Route path="/perfil" element={<Perfil />} />
        <Route path="/perfil/editar" element={<EditarPerfil />} />
        <Route path="/p/:id" element={<PublicProfile />} />
        <Route path="/servicios" element={<MisServicios />} />
        <Route path="/clientes" element={<Clientes />} />
        <Route path="/agenda" element={<Agenda />} />
        <Route path="/formulario" element={<FormularioConfig />} />
        <Route path="/form/:servicio" element={<ReservarTurno />} />
        <Route path="/equipo" element={<Equipo />} />
          <Route path="/equipo/:profesionalId" element={<GestionarProfesional />} />
        <Route path="/invitaciones" element={<InvitacionesRecibidas />} />
      </Route>

      {/* Perfil público de local — sin auth requerido */}
      <Route path="/local/:slug" element={<PublicLocalProfile />} />

      {/* Aceptar invitación a un equipo — maneja logueado y no logueado */}
      <Route path="/invitacion" element={<Invitacion />} />

      {/* Rutas públicas de auth */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/verify-email" element={<VerifyEmail />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
