@echo off
chcp 65001 >nul
title WallasAPI - Enrutador Inteligente de IA

setlocal EnableDelayedExpansion

REM --- Helper: verificar si un comando existe ---
:check_command
    where %1 >nul 2>&1
    exit /b %errorlevel%

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

REM --- Verificar si puerto 8001 esta ocupado ---
echo.
echo [INFO] Verificando si puerto 8001 esta libre...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001 ^| findstr LISTENING') do (
    set PID=%%a
    echo [WARN] Puerto 8001 ocupado por PID %%a
    echo [WARN] Probablemente hay otra instancia de WallasAPI corriendo.
    echo.
    echo Presiona ENTER para matar el proceso anterior y continuar...
    echo O cierra esta ventana y deten el otro proceso manualmente.
    pause >nul
    echo [INFO] Matando proceso %%a...
    taskkill /PID %%a /F >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] No pude matar el proceso. Corre como administrador o cierralo manualmente.
        pause
        exit /b 1
    )
    timeout /t 2 /nobreak >nul
)
echo [OK] Puerto 8001 libre.

REM --- Configurar PYTHONPATH para que python -m wallasAPI.api_server funcione ---
REM El package wallasAPI esta en %SCRIPT_DIR%, su padre es %PARENT_DIR%
set "PYTHONPATH=%PARENT_DIR%;%PYTHONPATH%"

REM --- Iniciar camofox-browser (opcional, en ventana aparte) ---
call :check_command camofox-browser
if %ERRORLEVEL% == 0 (
    echo [INFO] camofox-browser detectado. Iniciando en ventana aparte...
    start "Camofox Browser" cmd /c "camofox-browser server"
    timeout /t 3 /nobreak >nul
) else (
    echo [INFO] camofox-browser no instalado. Omitiendo. Instalar: npm install -g camofox-browser
)

REM --- Iniciar MCP Server en modo HTTP (opcional, en ventana aparte) ---
echo [INFO] MCP Server iniciando en ventana aparte en modo HTTP (puerto 8002)...
start "WallasAPI MCP Server" cmd /c "cd /d %SCRIPT_DIR% && python mcp_server.py --http --port 8002"
timeout /t 2 /nobreak >nul

REM --- Iniciar servidor ---
echo.
echo ================================================================
echo   API iniciandose en http://localhost:8001
echo   Documentacion interactiva: http://localhost:8001/docs
echo   Dashboard de servicios: http://localhost:8001/v1/status/services
echo ================================================================
echo.
echo   Servicios auto-detectados por el dashboard:
echo     - WallasAPI     : http://localhost:8001  (este proceso)
echo     - Camofox       : http://localhost:9377  (ventana separada)
echo     - MCP Server    : http://localhost:8002    (ventana separada)
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
