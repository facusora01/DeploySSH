# Script para arrancar Appointa en un stack Docker SEPARADO y LIMPIO.
#
# Diferencia con start.ps1:
#   - start.ps1     -> project "appointa"        (volumen appointa_postgres_data)
#   - fresh-start   -> project "appointa-fresh"  (volumen appointa-fresh_postgres_data)
#
# Son entornos Docker DISTINTOS: contenedores, red y base de datos separados.
# fresh-start ademas SIEMPRE empieza limpio (borra su propio volumen) y reconstruye.
#
# Como los container_name del compose son fijos (app_back, app_front, etc.), los
# dos stacks NO pueden correr a la vez: este script baja el stack de start.ps1
# antes de levantar el suyo (sin borrar la DB de start.ps1). Es "de a uno".
#
# ADVERTENCIA: borra TODOS los datos de la DB de ESTE stack (appointa-fresh). Irreversible.
#              La DB de start.ps1 (appointa) NO se toca.
#
# Uso:
#   ./fresh-start.ps1          -> pide confirmacion antes de borrar
#   ./fresh-start.ps1 -Force   -> sin confirmacion (para automatizar)

param(
    [switch]$Force
)

$FreshProject = "appointa-fresh"
$MainProject  = "appointa"

Write-Host "Appointa - Stack separado y limpio ($FreshProject)" -ForegroundColor Green
Write-Host ""

# Verificar Docker
Write-Host "Verificando Docker..." -ForegroundColor Yellow
docker --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker no esta instalado o no esta corriendo" -ForegroundColor Red
    Write-Host "Inicia Docker Desktop y volve a ejecutar este script" -ForegroundColor Yellow
    exit 1
}

# Crear archivo .env si no existe
if (-not (Test-Path ".env")) {
    Write-Host "Creando archivo .env desde .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "Revisa el .env y carga GOOGLE_CLIENT_ID / VITE_GOOGLE_CLIENT_ID antes de usar Google Auth." -ForegroundColor Cyan
}

# Confirmacion del borrado (destructivo e irreversible)
if (-not $Force) {
    Write-Host ""
    Write-Host "Esto BORRA la base de datos del stack '$FreshProject' y reconstruye todo." -ForegroundColor Red
    Write-Host "La DB de start.ps1 ('$MainProject') NO se toca. Esta accion es IRREVERSIBLE." -ForegroundColor Red
    $answer = Read-Host "Escribi 'si' para continuar"
    if ($answer -ne "si") {
        Write-Host "Cancelado. No se toco nada." -ForegroundColor Yellow
        exit 0
    }
}

# Bajar el stack de start.ps1 para liberar nombres de contenedor y puertos.
# SIN -v: la base de datos de start.ps1 se conserva.
Write-Host ""
Write-Host "Bajando el stack '$MainProject' (start.ps1) para liberar puertos..." -ForegroundColor Yellow
docker compose -p $MainProject down

# Bajar este stack y borrar SU volumen (arranque limpio).
Write-Host "Bajando y limpiando el stack '$FreshProject'..." -ForegroundColor Yellow
docker compose -p $FreshProject down -v

# Reconstruir imagenes desde cero
Write-Host "Reconstruyendo imagenes..." -ForegroundColor Yellow
docker compose -p $FreshProject build
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error al construir las imagenes. Esta Docker corriendo?" -ForegroundColor Red
    exit 1
}

# Levantar servicios (el back corre 'alembic upgrade head' al arrancar)
Write-Host "Levantando servicios..." -ForegroundColor Yellow
docker compose -p $FreshProject up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error al levantar servicios" -ForegroundColor Red
    exit 1
}

# Esperar a que la DB este lista
Write-Host "Esperando a la base de datos..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Red de seguridad idempotente para migraciones
Write-Host "Aplicando migraciones..." -ForegroundColor Yellow
docker compose -p $FreshProject exec back alembic upgrade head
if ($LASTEXITCODE -ne 0) {
    Write-Host "Advertencia: no se pudieron aplicar las migraciones automaticamente" -ForegroundColor Yellow
    Write-Host "Aplicalas a mano: docker compose -p $FreshProject exec back alembic upgrade head" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Appointa corriendo LIMPIO en el stack '$FreshProject'!" -ForegroundColor Green
Write-Host ""
Write-Host "URLs utiles:" -ForegroundColor Cyan
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "  API docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Health: http://localhost:8000/health" -ForegroundColor White
Write-Host ""
Write-Host "Comandos utiles (recorda el -p $FreshProject):" -ForegroundColor Yellow
Write-Host "  Logs: docker compose -p $FreshProject logs -f" -ForegroundColor White
Write-Host "  Detener: docker compose -p $FreshProject down" -ForegroundColor White
Write-Host "  Volver a start.ps1: bajar este stack y correr ./start.ps1" -ForegroundColor White
Write-Host ""
Write-Host "Mostrando logs (Ctrl+C para salir, servicios seguiran corriendo)..." -ForegroundColor Green
docker compose -p $FreshProject logs -f
