@echo off
chcp 65001 >nul
title Detener WallasAPI - Servicios

setlocal EnableDelayedExpansion

echo.
echo ============================================================
echo   Deteniendo todos los servicios de WallasAPI
echo ============================================================
echo.

REM --- Detener WallasAPI existente (puerto 8001) ---
echo [INFO] Buscando WallasAPI en puerto 8001...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr :8001 ^| findstr LISTENING 2^>nul') do (
    set PID=%%a
    echo [INFO] Deteniendo WallasAPI (PID %%a)...
    taskkill /PID %%a /F >nul 2>&1
    if !errorlevel! equ 0 (
        echo [OK] WallasAPI detenido.
    ) else (
        echo [WARN] No se pudo detener WallasAPI (PID %%a).
    )
)

REM --- Detener MCP Server existente (puerto 8002) ---
echo.
echo [INFO] Buscando MCP Server en puerto 8002...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr :8002 ^| findstr LISTENING 2^>nul') do (
    set PID=%%a
    echo [INFO] Deteniendo MCP Server (PID %%a)...
    taskkill /PID %%a /F >nul 2>&1
    if !errorlevel! equ 0 (
        echo [OK] MCP Server detenido.
    ) else (
        echo [WARN] No se pudo detener MCP Server (PID %%a).
    )
)

REM --- Detener Camofox Browser existente (puerto 9377) ---
echo.
echo [INFO] Buscando Camofox Browser en puerto 9377...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr :9377 ^| findstr LISTENING 2^>nul') do (
    set PID=%%a
    echo [INFO] Deteniendo Camofox Browser (PID %%a)...
    taskkill /PID %%a /F >nul 2>&1
    if !errorlevel! equ 0 (
        echo [OK] Camofox Browser detenido.
    ) else (
        echo [WARN] No se pudo detener Camofox Browser (PID %%a).
    )
)

REM --- Detener procesos Python relacionados con WallasAPI ---
echo.
echo [INFO] Buscando procesos Python relacionados con WallasAPI...
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO csv 2^>nul ^| findstr /i "wallasapi\|mcp_server\|api_server" 2^>nul') do (
    set PID=%%a
    set PID=!PID:"=!
    echo [INFO] Deteniendo proceso Python relacionado (PID !PID!)...
    taskkill /PID !PID! /F >nul 2>&1
    if !errorlevel! equ 0 (
        echo [OK] Proceso Python detenido.
    ) else (
        echo [WARN] No se pudo detener proceso Python (PID !PID!).
    )
)

REM --- Detener Gravedad Dashboard existente (puerto 5000) ---
echo.
echo [INFO] Buscando Gravedad Dashboard en puerto 5000...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr :5000 ^| findstr LISTENING 2^>nul') do (
    set PID=%%a
    echo [INFO] Deteniendo Gravedad Dashboard (PID %%a)...
    taskkill /PID %%a /F >nul 2>&1
    if !errorlevel! equ 0 (
        echo [OK] Gravedad Dashboard detenido.
    ) else (
        echo [WARN] No se pudo detener Gravedad Dashboard (PID %%a).
    )
)

REM --- Verificar que los puertos estén libres ---
echo.
echo [INFO] Verificando que los puertos estén libres...
set ports=8001 8002 9377 5000
for %%p in (%ports%) do (
    netstat -ano 2^>nul ^| findstr :%%p ^| findstr LISTENING >nul 2>&1
    if !errorlevel! equ 0 (
        echo [WARN] El puerto %%p todavía está ocupado.
    ) else (
        echo [OK] Puerto %%p está libre.
    )
)

echo.
echo ============================================================
echo   Proceso de detención completado.
echo ============================================================
echo.
echo Presiona cualquier tecla para cerrar...
pause >nul
