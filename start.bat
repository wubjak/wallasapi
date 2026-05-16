@echo off
chcp 65001 >nul
title WallasAPI - Enrutador Inteligente de IA

setlocal

REM --- Ir al directorio donde esta este .bat ---
cd /d "%~dp0"
set "WALLAS_DIR=%CD%"
set "PROJECT_DIR=%CD%\.."

set "VENV_PATH=%PROJECT_DIR%\venv"

echo [DEBUG] Directorio del script: %WALLAS_DIR%
echo [DEBUG] Buscando venv en: %VENV_PATH%

if exist "%VENV_PATH%\Scripts\activate.bat" (
    echo [INFO] Activando entorno virtual: %VENV_PATH%
    call "%VENV_PATH%\Scripts\activate.bat"
    if errorlevel 1 (
        echo [ERROR] No se pudo activar el entorno virtual.
        pause
        exit /b 1
    )
) else (
    echo [WARN] No se encontro entorno virtual en %VENV_PATH%
    echo [WARN] Intentando con Python del sistema...
)

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no esta disponible.
    pause
    exit /b 1
)
echo [OK] Python activo:
python --version

echo [INFO] Verificando dependencias...
python -m pip install -q -r requirements.txt 2>nul
echo [OK] Dependencias listas.

REM --- Solo matar WallasAPI propio si esta ocupando el puerto 8001 ---
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr :8001 ^| findstr LISTENING 2^>nul') do (
    echo [INFO] Deteniendo instancia anterior en puerto 8001 - PID %%a...
    taskkill /PID %%a /F >nul 2>&1
    timeout /t 2 /nobreak >nul
)

set "PYTHONPATH=%PROJECT_DIR%;%PYTHONPATH%"

echo.
echo ================================================================
echo   WallasAPI iniciandose en http://localhost:8001
echo   Documentacion interactiva: http://localhost:8001/docs
echo ================================================================
echo.
echo Presiona Ctrl+C para detener.
echo.

python api_server.py
if errorlevel 1 goto :FALLBACK

:END
echo.
echo [INFO] Servidor detenido. Presiona cualquier tecla para cerrar...
pause >nul
exit /b 0

:FALLBACK
echo.
echo [WARN] Fallo ejecucion directa (codigo %ERRORLEVEL%).
echo.
echo Posibles causas:
echo   1. Puerto 8001 ocupado
echo   2. Error de importacion en api_server.py
echo   3. Variables de entorno faltantes
echo.
echo Para diagnosticar manualmente:
echo   cd /d "%WALLAS_DIR%"
echo   set PYTHONPATH="%PROJECT_DIR%"
echo   python api_server.py
echo.
pause >nul
goto :END
