# Backend Tests

Guía para ejecutar tests del backend.

## Setup

Asegúrate de tener el venv activado:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Ejecutar Tests

### Todos los tests

```bash
pytest backend/tests -v
```

### Solo unit tests

```bash
pytest backend/tests/unit -v
```

### Solo integration tests

```bash
pytest backend/tests/integration -v
```

### Test específico

```bash
pytest backend/tests/test_clientes.py -v
pytest backend/tests/test_profesionales.py -v
```

### Con coverage

```bash
pytest backend/tests --cov=app --cov-report=html
```

## Estado Actual

**✅ 65/65 tests pasando**

### Resultados
- ✅ Integration tests (auth): 11/11 pasando
- ✅ Integration tests (services): 13/13 pasando
- ✅ Unit tests (auth): 11/11 pasando
- ✅ Unit tests (services): 12/12 pasando
- ✅ Unit tests (availability): 3/3 pasando
- ✅ Tests de modelos: 2/2 pasando
- ✅ Total: **65/65 pasando**

## Fixes Aplicados

1. ✅ **Bcrypt incompatibility** - Downgrade de bcrypt 5.0.0 a 3.2.2
2. ✅ **Pydantic v2 warnings** - Migración de `class Config` a `ConfigDict` en 4 archivos
3. ✅ **ServiceService typo** - Corregir `get_by_profesional` → `get_by_professional`
4. ✅ **AvailabilityService test** - Mock `datetime.now()` para test robustness

## Dependencias Instaladas

```
fastapi==0.136.1
sqlalchemy==2.0.49
pydantic==2.13.4
pytest==9.0.3
pytest-cov==7.1.0
testcontainers[postgres]==4.14.2
bcrypt==3.2.2 (compatible con passlib)
email-validator==2.3.0
```
