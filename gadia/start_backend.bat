@echo off
REM Script para iniciar el backend de GADIA (versión .bat)
REM Ejecutar desde la carpeta gadia/ o hacer doble clic

echo 🚀 Iniciando GADIA Backend...

REM Verificar que estamos en el directorio correcto
if not exist ".venv" (
    echo ❌ Error: No se encontró el entorno virtual (.venv)
    echo    Asegúrate de ejecutar este script desde la carpeta gadia/
    pause
    exit /b 1
)

REM Usar el Python del venv directamente
echo 📦 Iniciando servidor con entorno virtual...
echo ✅ Servidor disponible en http://127.0.0.1:8000
echo    Presiona CTRL+C para detener el servidor
echo.

.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

pause

