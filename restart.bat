@echo off
chcp 65001 >nul
title Reiniciar WallasAPI - Servicios

setlocal EnableDelayedExpansion

echo.
echo ============================================================
echo   Reiniciando todos los servicios de WallasAPI
echo ============================================================
echo.

REM --- Ejecutar script de detención ---
echo [INFO] Deteniendo servicios existentes...
call "%~dp0stop.bat"

REM --- Esperar un momento ---
echo.
echo [INFO] Esperando 3 segundos para liberar recursos...
timeout /t 3 /nobreak >nul

REM --- Ejecutar script de inicio ---
echo.
echo [INFO] Iniciando servicios...
call "%~dp0start.bat"

echo.
echo ============================================================
echo   Proceso de reinicio completado.
echo ============================================================
echo.
pause
