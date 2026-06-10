# Script para levantar Appointa Backend

param(
    [string]$Action = "up"
)

function Run-Tests {
    param(
        [switch]$Coverage
    )

    Write-Host "Ejecutando tests..." -ForegroundColor Green

    # Verificar que los servicios esten corriendo
    $services = docker compose ps -q
    if (-not $services) {
        Write-Host "Los servicios no estan corriendo. Levantando servicios primero..." -ForegroundColor Yellow
        docker compose up -d
        Start-Sleep -Seconds 10
    }

    if ($Coverage) {
        Write-Host "Ejecutando tests con coverage..." -ForegroundColor Yellow
        docker compose exec back pytest --cov=app --cov-report=term-missing
    } else {
        Write-Host "Ejecutando tests..." -ForegroundColor Yellow
        docker compose exec back pytest -v
    }
}

if ($Action -eq "test") {
    Run-Tests
    exit 0
}

if ($Action -eq "test-coverage") {
    Run-Tests -Coverage
    exit 0
}

Write-Host "Levantando Appointa Backend..." -ForegroundColor Green

# Verificar Docker
Write-Host "Verificando Docker..." -ForegroundColor Yellow
docker --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker no esta instalado" -ForegroundColor Red
    exit 1
}

# Verificar docker-compose
Write-Host "Verificando docker-compose..." -ForegroundColor Yellow
docker-compose --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "docker-compose no esta instalado" -ForegroundColor Red
    exit 1
}


# Crear archivo .env si no existe
if (-not (Test-Path ".env")) {
    Write-Host "Creando archivo .env desde .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
}

# Construir imagenes
Write-Host "Construyendo imagenes Docker..." -ForegroundColor Yellow
docker compose build

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Docker no esta corriendo actualmente" -ForegroundColor Red
    Write-Host "Por favor inicia Docker Desktop y vuelve a ejecutar este script" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Presiona Enter para cerrar..." -ForegroundColor Cyan
    Read-Host
    exit 1
}

# Levantar servicios
Write-Host "Levantando servicios..." -ForegroundColor Yellow
docker compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error al levantar servicios" -ForegroundColor Red
    exit 1
}

# Esperar a que la DB este lista
Write-Host "Esperando a la base de datos..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Aplicar migraciones (el container ya corre 'alembic upgrade head' al arrancar;
# esto es una red de seguridad idempotente y el mecanismo real de schema).
Write-Host "Aplicando migraciones de la base de datos..." -ForegroundColor Yellow
docker compose exec back alembic upgrade head

if ($LASTEXITCODE -ne 0) {
    Write-Host "Advertencia: No se pudieron aplicar las migraciones automaticamente" -ForegroundColor Yellow
    Write-Host "Puedes aplicarlas manualmente ejecutando:" -ForegroundColor Yellow
    Write-Host "docker compose exec back alembic upgrade head" -ForegroundColor Yellow
}

# Mostrar informacion
Write-Host ""
Write-Host "Appointa Backend esta corriendo!" -ForegroundColor Green
Write-Host ""
Write-Host "URLs utiles:" -ForegroundColor Cyan
Write-Host "  API: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  ReDoc: http://localhost:8000/redoc" -ForegroundColor White
Write-Host "  WhatsApp QR: http://localhost:8000/api/v1/whatsapp/auth" -ForegroundColor White
Write-Host "  Health: http://localhost:8000/health" -ForegroundColor White
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "Comandos utiles:" -ForegroundColor Yellow
Write-Host "  Logs backend: docker compose logs -f back" -ForegroundColor White
Write-Host "  Logs WhatsApp: docker compose logs -f whatsapp-service" -ForegroundColor White
Write-Host "  Logs todo: docker compose logs -f" -ForegroundColor White
Write-Host "  Detener: docker compose down" -ForegroundColor White
Write-Host "  Reiniciar: docker compose restart" -ForegroundColor White
Write-Host "  Tests: docker compose exec back pytest" -ForegroundColor White
Write-Host ""
Write-Host "WhatsApp Setup:" -ForegroundColor Green
Write-Host "  1. Abre: http://localhost:8000/api/v1/whatsapp/auth" -ForegroundColor White
Write-Host "  2. Escanea el QR con WhatsApp" -ForegroundColor White
Write-Host "  3. Listo! Los mensajes se enviaran automaticamente" -ForegroundColor White
Write-Host ""
Write-Host "Mostrando logs (Ctrl+C para salir, servicios seguiran corriendo)..." -ForegroundColor Green
docker compose logs -f
