# Implementación del Backend - Appointa

## Resumen

Se implementó el backend de Appointa utilizando FastAPI, PostgreSQL, SQLAlchemy y Docker. El backend permite la gestión de perfiles de clientes y profesionales con autenticación JWT y validación de datos con Pydantic.

## Stack Tecnológico

- **FastAPI**: Framework web moderno y rápido para crear APIs con Python 3.11+
- **PostgreSQL 15**: Base de datos relacional
- **SQLAlchemy 2.0**: ORM para interactuar con la base de datos
- **Alembic**: Herramienta para migraciones de base de datos
- **Pydantic v2**: Validación de datos y definición de schemas
- **JWT (python-jose)**: Autenticación basada en tokens
- **Password Hashing (passlib)**: Encriptación de contraseñas con bcrypt
- **Docker**: Contenerización de la aplicación
- **docker-compose**: Orquestación de múltiples contenedores

## Estructura del Proyecto

```
appointa-backend/
├── app/
│   ├── api/
│   │   ├── deps.py          # Dependencias de autenticación
│   │   └── v1/
│   │       ├── clientes.py   # Endpoints de clientes
│   │       ├── profesionales.py # Endpoints de profesionales
│   │       └── router.py     # Router principal
│   ├── core/
│   │   ├── config.py        # Configuración de la aplicación
│   │   └── security.py      # Funciones de seguridad (JWT, hashing)
│   ├── models/
│   │   ├── base.py          # Base declarativa de SQLAlchemy
│   │   ├── user.py          # Modelo de Usuario
│   │   ├── cliente.py       # Modelo de Cliente
│   │   └── profesional.py   # Modelo de Profesional
│   ├── schemas/
│   │   ├── cliente.py       # Schemas Pydantic para Cliente
│   │   └── profesional.py   # Schemas Pydantic para Profesional
│   ├── utils/
│   ├── database.py          # Configuración de base de datos
│   └── main.py              # Entry point de la aplicación
├── tests/
│   ├── conftest.py          # Fixtures de pytest
│   ├── test_clientes.py     # Tests de clientes
│   └── test_profesionales.py # Tests de profesionales
├── alembic/
│   └── env.py               # Configuración de Alembic
├── Dockerfile               # Configuración de imagen Docker
├── docker-compose.yml       # Orquestación de servicios
├── requirements.txt         # Dependencias de Python
├── .env                     # Variables de entorno
└── start.ps1                # Script de inicio para Windows
```

## Modelos de Datos

### User
- `email`: Email del usuario (único)
- `password_hash`: Contraseña encriptada
- `full_name`: Nombre completo
- `phone`: Teléfono
- `is_active`: Estado de activación
- `role`: Rol (cliente o profesional)
- `created_at`: Fecha de creación
- `updated_at`: Fecha de actualización

### Cliente
- `user_id`: ID del usuario asociado
- `dni`: Documento Nacional de Identidad
- `date_of_birth`: Fecha de nacimiento
- `address`: Dirección
- `city`: Ciudad
- `notes`: Notas adicionales
- `created_at`: Fecha de creación
- `updated_at`: Fecha de actualización

### Profesional
- `user_id`: ID del usuario asociado
- `specialty`: Especialidad médica
- `license_number`: Número de matrícula
- `experience_years`: Años de experiencia
- `bio`: Biografía
- `consultation_fee`: Honorarios de consulta
- `is_verified`: Estado de verificación
- `created_at`: Fecha de creación
- `updated_at`: Fecha de actualización

## Endpoints API

### Clientes
- `GET /api/v1/clientes/me` - Obtener perfil completo del cliente
- `PUT /api/v1/clientes/me` - Actualizar perfil completo del cliente
- `PATCH /api/v1/clientes/me` - Actualización parcial del perfil del cliente

### Profesionales
- `GET /api/v1/profesionales/me` - Obtener perfil completo del profesional
- `PUT /api/v1/profesionales/me` - Editar perfil completo del profesional
- `PATCH /api/v1/profesionales/me` - Actualización parcial del perfil del profesional

### Health Check
- `GET /` - Mensaje de bienvenida
- `GET /health` - Verificar estado de la API

## Seguridad

### Autenticación JWT
- Los endpoints protegidos requieren un token JWT en el header `Authorization: Bearer <token>`
- El token se genera al hacer login y tiene una duración configurada
- El token incluye el ID del usuario y su rol

### Password Hashing
- Las contraseñas se encriptan usando bcrypt antes de almacenarlas
- Nunca se almacenan contraseñas en texto plano

### Role-Based Access Control
- Los endpoints de clientes solo son accesibles por usuarios con rol "cliente"
- Los endpoints de profesionales solo son accesibles por usuarios con rol "profesional"

## Tests

Se implementaron tests de integración para verificar la funcionalidad de edición de perfiles:

### Tests de Cliente
- `test_cliente_update_phone` - Verifica actualización de teléfono
- `test_cliente_update_multiple_fields` - Verifica actualización de múltiples campos

### Tests de Profesional
- `test_profesional_update_phone` - Verifica actualización de teléfono
- `test_profesional_update_multiple_fields` - Verifica actualización de múltiples campos

## Ejecución de Tests

```bash
# Ejecutar tests dentro del contenedor Docker
docker-compose exec api pytest tests/ -v
```

## Configuración

### Variables de Entorno
- `DATABASE_URL`: URL de conexión a PostgreSQL
- `SECRET_KEY`: Clave secreta para JWT
- `ALGORITHM`: Algoritmo de encriptación (HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Tiempo de expiración del token

## Docker

La aplicación está contenerizada con Docker y orquestada con docker-compose. Consulta el archivo `docker-guide.md` para más detalles sobre el uso de Docker.
