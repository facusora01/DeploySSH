# SCRUM-121: Edición de Perfil del Cliente y Profesional [BACK]

## Información del Ticket

- **Key**: SCRUM-121
- **ID**: 10185
- **Summary**: Edición de Perfil Del Cliente y Profesional [BACK]
- **Description**: Permitir la carga de datos simples mediante un formulario. No incluye imágenes
- **Issue Type**: Task
- **Priority**: Medium
- **Status**: Completado
- **Status Category**: Done
- **Story Points**: 2
- **Sprint**: SCRUM Sprint 1 (ID: 35)

## Asignación

- **Assignee**: SORASIO FACUNDO (fsorasio@fi.uba.ar)
- **Reporter**: amurseli

## Fechas

- **Created**: 2026-05-09T15:05:33.546-0300
- **Updated**: 2026-05-11T03:00:00.000-0300

## Sprint

- **ID**: 35
- **Name**: SCRUM Sprint 1
- **State**: Active
- **Board ID**: 1
- **Start Date**: 2026-05-09T18:18:17.419Z
- **End Date**: 2026-05-13T18:18:00.000Z

## Issue Links

- **Blocks**: SCRUM-123 - Edición de Perfil Del Cliente y Profesional [FRONT] (Status: Por hacer)

## Stack Tecnológico Implementado

- FastAPI
- Python 3.11+
- PostgreSQL 15
- SQLAlchemy 2.0
- Alembic
- Pydantic v2
- JWT (python-jose)
- Password Hashing (passlib)
- Docker
- docker-compose

## Endpoints Implementados

### Clientes

| Método | Path | Descripción |
|--------|------|-------------|
| GET | /api/v1/clientes/me | Obtener perfil completo del cliente |
| PUT | /api/v1/clientes/me | Actualizar perfil completo del cliente |
| PATCH | /api/v1/clientes/me | Actualización parcial del perfil del cliente |

### Profesionales

| Método | Path | Descripción |
|--------|------|-------------|
| GET | /api/v1/profesionales/me | Obtener perfil completo del profesional |
| PUT | /api/v1/profesionales/me | Editar perfil completo del profesional |
| PATCH | /api/v1/profesionales/me | Actualización parcial del perfil del profesional |

## Campos Implementados

### Cliente

- full_name
- phone
- dni
- date_of_birth
- address
- city
- notes

### Profesional

- full_name
- phone
- specialty
- license_number
- experience_years
- bio
- consultation_fee

## Restricciones

- No incluye manejo de imágenes
- Datos simples mediante formulario
- Validación con Pydantic
- Autenticación JWT requerida

## Estado de Implementación

```json
{
  "completed": true,
  "endpoints_implemented": true,
  "schemas_implemented": true,
  "authentication_implemented": true,
  "database_models_implemented": true,
  "docker_configured": true,
  "api_running": true,
  "tested": true
}
```

## Tests

Se implementaron tests de integración para verificar la funcionalidad de edición de perfiles:

- Tests de actualización de teléfono para cliente y profesional
- Tests de actualización de múltiples campos para cliente y profesional
- Todos los tests pasan exitosamente

## Próximos Pasos

- El ticket bloqueado SCRUM-123 (Frontend) puede comenzar su desarrollo
- Los endpoints están listos para ser integrados con el frontend
