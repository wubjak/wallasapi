@echo off
chcp 65001 >nul
title WallasAPI - Minimal Start

cd /d "%~dp0"

REM Detectar venv compartido de ProyectoIG
set "VENV_PARENT=%~dp0..\venv"

if exist "%VENV_PARENT%\Scripts\activate.bat" (
    call "%VENV_PARENT%\Scripts\activate.bat"
    echo [OK] Entorno virtual activado: %VENV_PARENT%
) else (
    echo [ERROR] No se encontro venv en %VENV_PARENT%
    echo [INFO] Asegurate de tener el venv creado en d:\ProyectoIG\venv
    pause
    exit /b 1
)

set "PYTHONPATH=%~dp0..\;%PYTHONPATH%"

echo [INFO] Iniciando WallasAPI en http://localhost:8001
echo [INFO] Presiona Ctrl+C para detener.
echo.

python api_server.py
if errorlevel 1 (
    echo.
    echo [ERROR] WallasAPI termino con codigo %errorlevel%
    echo [TIP] Revisa que el puerto 8001 no este ocupado y que las dependencias esten instaladas.
    pause
)
