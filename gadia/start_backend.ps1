# Script para iniciar el backend de GADIA
# Ejecutar desde la carpeta gadia/

Write-Host "Iniciando GADIA Backend..." -ForegroundColor Cyan

# Verificar que estamos en el directorio correcto
if (-not (Test-Path ".venv")) {
    Write-Host "Error: No se encontro el entorno virtual (.venv)" -ForegroundColor Red
    Write-Host "   Asegurate de ejecutar este script desde la carpeta gadia/" -ForegroundColor Yellow
    pause
    exit 1
}

# Obtener la ruta del Python del venv
$pythonPath = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $pythonPath)) {
    Write-Host "Error: No se encontro Python en el entorno virtual" -ForegroundColor Red
    Write-Host "   Ruta esperada: $pythonPath" -ForegroundColor Yellow
    pause
    exit 1
}

# Verificar que uvicorn esta instalado
Write-Host "Verificando dependencias..." -ForegroundColor Green
& $pythonPath -m pip show uvicorn 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Uvicorn no encontrado. Instalando dependencias..." -ForegroundColor Yellow
    & $pythonPath -m pip install -r backend/requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error al instalar dependencias" -ForegroundColor Red
        pause
        exit 1
    }
}

# Iniciar el servidor usando el Python del venv
Write-Host "Iniciando servidor en http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "   Presiona CTRL+C para detener el servidor" -ForegroundColor Yellow
Write-Host ""

& $pythonPath -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
