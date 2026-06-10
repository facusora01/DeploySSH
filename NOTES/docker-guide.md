# Guía de Uso de Docker - Appointa Backend

## Requisitos Previos

- Docker Desktop instalado y ejecutándose
- docker-compose instalado (viene con Docker Desktop)

## Estructura de Docker

El proyecto utiliza dos contenedores:
- **db**: Contenedor de PostgreSQL 15
- **api**: Contenedor de FastAPI con la aplicación

## Archivos de Configuración

### Dockerfile
Define cómo construir la imagen de la API:
- Basado en Python 3.11
- Instala dependencias desde requirements.txt
- Expone el puerto 8000
- Ejecuta uvicorn

### docker-compose.yml
Define los servicios:
- **db**: PostgreSQL con configuración de persistencia
- **api**: FastAPI que depende de db

## Iniciar la Aplicación

### Método 1: Script Automático (Windows)

El script `start.ps1` automatiza todo el proceso:

```powershell
.\start.ps1
```

El script:
1. Verifica que Docker esté instalado
2. Verifica que Docker esté ejecutándose
3. Crea archivo .env si no existe
4. Construye las imágenes Docker
5. Inicia los contenedores
6. Espera a que la base de datos esté lista
7. Muestra logs y comandos útiles

### Método 2: Comandos Manuales

```bash
# Cambiar al directorio del backend
cd appointa-backend

# Construir las imágenes
docker-compose build

# Iniciar los contenedores
docker-compose up -d

# Ver logs
docker-compose logs -f
```

## Verificar Estado

```bash
# Ver contenedores en ejecución
docker-compose ps

# Ver logs de la API
docker-compose logs api

# Ver logs de la base de datos
docker-compose logs db
```

## Ejecutar Comandos en Contenedores

```bash
# Ejecutar tests
docker-compose exec api pytest tests/ -v

# Acceder al shell de la API
docker-compose exec api bash

# Acceder a PostgreSQL
docker-compose exec db psql -U appointa -d appointa
```

## Variables de Entorno

El archivo `.env` contiene:

```env
DATABASE_URL=postgresql://appointa:appointa123@db:5432/appointa
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

⚠️ **Importante**: Cambiar `SECRET_KEY` en producción

## Detener la Aplicación

```bash
# Detener contenedores
docker-compose down

# Detener y eliminar volúmenes (borra datos)
docker-compose down -v
```

## Reconstruir después de Cambios

```bash
# Reconstruir imágenes
docker-compose build

# Reiniciar contenedores
docker-compose up -d

# Reconstruir sin caché
docker-compose build --no-cache
```

## Persistencia de Datos

Los datos de PostgreSQL se almacenan en un volumen Docker llamado `appointa_backend_db_data`. Los datos persisten aunque detengas los contenedores.

Para eliminar completamente los datos:

```bash
docker-compose down -v
```

## Solución de Problemas

### Contenedor no inicia

```bash
# Ver logs detallados
docker-compose logs api

# Verificar estado de Docker
docker ps
```

### Error de conexión a base de datos

```bash
# Verificar que db esté corriendo
docker-compose ps db

# Esperar a que db esté lista
docker-compose up db
```

### Puerto ya en uso

Cambia el puerto en docker-compose.yml:

```yaml
services:
  api:
    ports:
      - "8001:8000"  # Cambiar 8000 por 8001
```

### Reconstruir todo desde cero

```bash
# Detener todo
docker-compose down -v

# Eliminar imágenes
docker rmi $(docker images -q appointa-backend-api)

# Reconstruir
docker-compose build --no-cache
docker-compose up -d
```

## Comandos Útiles

```bash
# Ver uso de recursos
docker stats

# Limpiar contenedores detenidos
docker container prune

# Limpiar imágenes no utilizadas
docker image prune -a

# Ver espacio en disco
docker system df
```

## API Documentation

Una vez iniciada la aplicación:

- **API Root**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Desarrollo

Para desarrollo con hot-reload, modifica el Dockerfile o usa volúmenes para montar el código local:

```yaml
services:
  api:
    volumes:
      - .:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
