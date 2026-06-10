# Appointa Backend

Backend para Appointa - Sistema de gestión de turnos

## Stack Tecnológico

- **FastAPI** - Framework web moderno
- **PostgreSQL** - Base de datos
- **SQLAlchemy** - ORM
- **Pydantic** - Validación de datos
- **Alembic** - Migrations
- **Docker** - Contenedorización

## Estructura del Proyecto

```
appointa-backend/
├── app/
│   ├── api/                    # Endpoints API
│   │   ├── v1/
│   │   │   ├── clientes.py     # Endpoints de clientes
│   │   │   ├── profesionales.py # Endpoints de profesionales
│   │   │   └── router.py       # Router principal
│   ├── core/                   # Configuración core
│   │   ├── config.py           # Settings
│   │   └── security.py         # JWT, password hashing
│   ├── models/                 # Modelos SQLAlchemy
│   │   ├── base.py             # Base model
│   │   ├── user.py             # Usuario base
│   │   ├── cliente.py          # Modelo Cliente
│   │   └── profesional.py      # Modelo Profesional
│   ├── schemas/                # Schemas Pydantic
│   │   ├── cliente.py          # Schemas Cliente
│   │   └── profesional.py      # Schemas Profesional
│   ├── database.py             # Conexión a DB
│   └── main.py                 # Entry point
├── alembic/                    # Migrations
├── tests/                      # Tests
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── start.ps1                   # Script para levantar la app (Windows)
└── .env.example                # Variables de entorno ejemplo
```

## Instalación y Uso

### Requisitos Previos

- Docker Desktop instalado
- docker-compose instalado

### Iniciar la Aplicación

1. **Clonar el repositorio**
   ```bash
   cd appointa-backend
   ```

2. **Configurar variables de entorno**
   ```bash
   cp .env.example .env
   # Editar .env si es necesario
   ```

3. **Levantar la aplicación**
   ```powershell
   # En Windows (PowerShell)
   .\start.ps1
   ```

   Esto automáticamente:
   - Verifica Docker
   - Construye las imágenes
   - Levanta los servicios (API + PostgreSQL)
   - Crea las tablas en la base de datos
   - Muestra los logs

### Comandos Útiles

```powershell
# Ver logs
docker-compose logs -f

# Detener servicios
docker-compose down

# Reiniciar servicios
docker-compose restart

# Entrar al contenedor de la API
docker-compose exec api bash

# Crear tablas manualmente
docker-compose exec api python -c "from app.database import engine, Base; Base.metadata.create_all(bind=engine)"

# Ejecutar migrations (cuando se implementen)
docker-compose exec api alembic upgrade head
```

## API Endpoints

### Clientes

- `GET /api/v1/clientes/me` - Obtener mi perfil
- `PUT /api/v1/clientes/me` - Editar mi perfil completo
- `PATCH /api/v1/clientes/me` - Actualización parcial del perfil

### Profesionales

- `GET /api/v1/profesionales/me` - Obtener mi perfil
- `PUT /api/v1/profesionales/me` - Editar mi perfil completo
- `PATCH /api/v1/profesionales/me` - Actualización parcial del perfil

### General

- `GET /` - Root endpoint
- `GET /health` - Health check

## Documentación API

Una vez levantada la aplicación, la documentación automática está disponible en:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## SCRUM-121: Edición de Perfil Del Cliente y Profesional [BACK]

Este backend implementa los endpoints necesarios para SCRUM-121:

- Formularios de edición de perfiles (Cliente y Profesional)
- Validación de datos simples (texto, números, fechas)
- Sin manejo de imágenes (según el ticket)
- Autenticación JWT
- Persistencia en PostgreSQL

### Campos del Perfil Cliente

- `dni` - Documento nacional de identidad
- `date_of_birth` - Fecha de nacimiento
- `address` - Dirección
- `city` - Ciudad
- `notes` - Notas internas
- `full_name` - Nombre completo
- `phone` - Teléfono

### Campos del Perfil Profesional

- `specialty` - Especialidad
- `license_number` - Matrícula
- `experience_years` - Años de experiencia
- `bio` - Biografía
- `consultation_fee` - Honorarios consulta
- `full_name` - Nombre completo
- `phone` - Teléfono

## Desarrollo

### Ejecutar tests
```bash
docker-compose exec api pytest
```

### Crear nueva migration
```bash
docker-compose exec api alembic revision --autogenerate -m "descripción del cambio"
```

### Aplicar migrations
```bash
docker-compose exec api alembic upgrade head
```

## Troubleshooting

### Error: Docker no está instalado
Instala Docker Desktop desde https://www.docker.com/products/docker-desktop

### Error: Puerto 8000 o 5432 en uso
Modifica los puertos en `docker-compose.yml` si hay conflictos

### Error: No se pueden crear las tablas
Ejecuta manualmente:
```powershell
docker-compose exec api python -c "from app.database import engine, Base; Base.metadata.create_all(bind=engine)"
```

## Licencia

Este proyecto es para uso interno del equipo de desarrollo de Appointa.
