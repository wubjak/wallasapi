@echo off
chcp 65001 >nul
title WallasAPI - Enrutador Inteligente de IA

setlocal EnableDelayedExpansion

REM --- Banner visual ---
echo.
python "%~dp0banner.py" 2>nul
if errorlevel 1 (
    echo.
    echo   WallasAPI - Enrutador Inteligente Multi-Proveedor de IA
    echo   powered by wubjak
    echo.
)

REM --- Detectar venv compartido de ProyectoIG ---
set "SCRIPT_DIR=%~dp0"
set "PARENT_DIR=%SCRIPT_DIR%..\"
set "VENV_LOCAL=%SCRIPT_DIR%.venv"
set "VENV_PARENT=%PARENT_DIR%venv"

if exist "%VENV_PARENT%\Scripts\activate.bat" (
    set "VENV_PATH=%VENV_PARENT%"
    echo [INFO] Usando entorno virtual compartido: %VENV_PARENT%
) else (
    if exist "%VENV_LOCAL%\Scripts\activate.bat" (
        set "VENV_PATH=%VENV_LOCAL%"
        echo [INFO] Usando entorno virtual local: %VENV_LOCAL%
    ) else (
        echo [ERROR] No se encontro entorno virtual.
        echo [ERROR] Esperado en: %VENV_PARENT% o %VENV_LOCAL%
        pause
        exit /b 1
    )
)

REM --- Activar venv ---
call "%VENV_PATH%\Scripts\activate.bat"
if errorlevel 1 (
    echo [ERROR] No se pudo activar el entorno virtual.
    pause
    exit /b 1
)

REM --- Verificar Python del venv ---
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no esta disponible en el entorno virtual.
    pause
    exit /b 1
)
echo [OK] Python activo: 
python --version

REM --- Instalar dependencias ---
echo.
echo [INFO] Verificando dependencias...
cd /d "%SCRIPT_DIR%"
python -m pip install -q -r requirements.txt
if errorlevel 1 (
    echo [WARN] Reintentando instalacion...
    python -m pip install -r requirements.txt
)
echo [OK] Dependencias listas.

REM --- Configurar PYTHONPATH para que python -m wallasAPI.api_server funcione ---
REM El package wallasAPI esta en %SCRIPT_DIR%, su padre es %PARENT_DIR%
set "PYTHONPATH=%PARENT_DIR%;%PYTHONPATH%"

REM --- Iniciar servidor ---
echo.
echo ================================================================
echo   API iniciandose en http://localhost:8001
echo   Documentacion interactiva: http://localhost:8001/docs
echo ================================================================
echo.
echo Presiona Ctrl+C para detener el servidor.
echo.

python -m wallasAPI.api_server

if errorlevel 1 (
    echo.
    echo [WARN] Fallo ejecucion como modulo. Intentando ejecucion directa...
    python api_server.py
)

pause
