# Plataforma Web — Monorepo

Setup inicial dockerizado: backend (FastAPI) + frontend (placeholder nginx).

## Estructura

```
.
├── back/           # FastAPI
├── front/          # Frontend (placeholder nginx — reemplazar con Vite/Next/etc)
├── docker-compose.yml
├── Makefile
├── .env.example
└── .gitignore
```

## Quick start

```bash
cp .env.example .env
make up
```

- Back: http://localhost:8000 (health: `/health`, docs: `/docs`)
- Front: http://localhost:3000

### Test Users

Para crear usuarios de prueba, ejecuta:
```bash
make seed
```

**Usuarios por defecto:**

| Email | Password | Rol |
|-------|----------|-----|
| `profesional@example.com` | `password123` | Profesional |
| `cliente@example.com` | `password123` | Cliente |

**Usar credenciales personalizadas** (opcional):
```bash
SEED_PRO_EMAIL="pro@custom.com" \
SEED_PRO_PASSWORD="mipass123" \
SEED_CLIENT_EMAIL="client@custom.com" \
SEED_CLIENT_PASSWORD="otrapass123" \
make seed
```

> ⚠️ **SOLO DESARROLLO** — El script de seed es solo para desarrollo local. Nunca usar en producción.

## Comandos

```bash
make help         # lista todo
make up           # levanta en background
make down         # apaga
make logs         # ver logs
make rebuild      # build sin cache + up
make rebuild-back # builda sin cache el back y levanta
make clean        # borra todo (volúmenes e imágenes locales)
make shell-back   # bash en el back
make shell-front  # sh en el front
make seed         # crea usuarios de prueba (profesional + cliente)
make test         # ejecuta los tests del backend
make test-coverage # ejecuta los tests con coverage
make test-watch   # ejecuta los tests en modo watch
```

## Troubleshooting

### Error: "Multiple head revisions are present" o "relation does not exist" (Alembic/Migrations)

**Síntoma**: El contenedor backend crashea con errores de Alembic o la tabla no existe:
```
ERROR [alembic.util.messaging] Multiple head revisions are present for given argument 'head'
ProgrammingError: (psycopg2.errors.UndefinedTable) relation "form_field_responses" does not exist
```

**Causa**: Conflicto en las migraciones de Alembic después de un merge, o volumen de DB corrupto.

**Solución**:
```bash
# Opción 1 (más rápido): Eliminar el volumen de la DB y dejar que se recree
make clean
make up

# Opción 2 (sin eliminar volumen): Resetear manualmente las migraciones
docker-compose exec app_back alembic downgrade base
docker-compose exec app_back alembic upgrade head
docker-compose restart app_back
```

## Próximos pasos

- **Front**: cuando elijas framework, reemplazar `front/Dockerfile` y el contenido. Ejemplo Vite:
  ```bash
  cd front && npm create vite@latest . -- --template react
  ```
  y actualizar el Dockerfile para usar `node:20-alpine` con `npm run dev`.
- **DB**: descomentar el servicio `db` en `docker-compose.yml` y las vars en `.env`.
