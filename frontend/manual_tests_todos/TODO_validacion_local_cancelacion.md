# TODO: Validación UI — Cancelación de turnos en locales

Pasos para verificar el funcionamiento completo desde la interfaz.

---

## Prerrequisitos

- [x ] Tener una cuenta `local` registrada (ej: `local@test.com`)
- [x] Tener al menos un profesional vinculado al local (desde `/equipo`)
- [x] Tener al menos un cliente con un turno reservado con ese profesional
- [x] Tener otro profesional que **no** pertenezca al local (para probar el caso negativo)

---

## 1. Vista de la agenda del equipo

- [x] Iniciar sesión como `local`
- [x] Ir a `/turnos`
- [x] Verificar que el subtítulo dice **"La agenda de tu equipo"** (no "Tus próximos turnos")
- [x] Verificar que se muestra la agenda en formato calendario (igual que para profesionales), no la lista simple
- [x] Verificar que aparecen los turnos de **todos** los profesionales del equipo
- [x] Verificar que los turnos de profesionales externos **no** aparecen

---

## 2. Apertura del modal de turno

- [x] Hacer clic en un turno de la agenda
- [x] Verificar que el modal muestra el **nombre del cliente** (no del profesional)
- [x] Verificar que se muestra el **teléfono del cliente** (si tiene)
- [x] Verificar que **no** aparece el botón "Pagar seña"
- [x] Verificar que **no** aparece el botón "Google Calendar"
- [x] Verificar que **no** aparecen los botones "Asistió / No asistió"

---

## 3. Flujo de cancelación con motivo

- [x] En el modal de un turno activo, hacer clic en **"Cancelar turno"**
- [x] Verificar que aparece el **formulario de motivo** (no el `window.confirm()` del cliente)
- [x] Intentar confirmar con el campo vacío → botón debe estar **deshabilitado**
- [x] Intentar confirmar con menos de 5 caracteres → botón debe estar **deshabilitado**
- [x] Escribir un motivo válido (≥ 5 chars) → botón se **habilita**
- [x] Confirmar la cancelación
- [x] Verificar que aparece la **notificación de éxito** "Turno cancelado correctamente"
- [x] Verificar que el turno aparece en la agenda con el badge **"Cancelado"**
- [x] Verificar que el modal se cierra automáticamente

---

## 4. Verificar estado del turno cancelado

- [x] Hacer clic nuevamente sobre el turno cancelado en la agenda
- [x] Verificar que el modal muestra el **motivo de cancelación** ingresado
- [x] Verificar que el botón "Cancelar turno" **no aparece** (turno ya cancelado)

---

## 5. Cancelación con seña pagada → flujo de reembolso

- [x] Usar un turno donde el depósito esté en estado **PAID**
- [x] Cancelar el turno como local con un motivo válido
- [x] Verificar que el modal del turno cancelado muestra la sección de **reembolso** con estado "Pendiente de reembolso"
- [x] Verificar (en logs del backend o email de prueba) que se envió el **email de reembolso pendiente** al profesional

---

## 6. Casos de error

- [o] Intentar cancelar vía API un turno de un profesional externo al local → debe retornar **403**
- [o] Intentar cancelar un turno ya cancelado → debe retornar **400** con mensaje "ya se encuentra cancelado"
- [o] Intentar cancelar sin `cancellation_reason` o con motivo muy corto → debe retornar **422**

---

## 7. Verificación de emails (requiere acceso a logs/Mailtrap/MailHog)

- [x] Cancelación normal → el **cliente** recibe email de cancelación con nombre del servicio y profesional
- [x] Cancelación con depósito → el **profesional** recibe email de reembolso pendiente con monto

---

## 8. Regresión — profesional y cliente sin cambios

- [x] Iniciar sesión como **profesional** → `/turnos` sigue mostrando su agenda personal
- [x] Iniciar sesión como **cliente** → `/turnos` sigue mostrando la lista de próximos turnos
- [x] Cliente puede seguir cancelando con `window.confirm()` (sin formulario de motivo)
- [x] Profesional puede seguir cancelando con formulario de motivo
