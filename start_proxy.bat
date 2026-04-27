@echo off
title WallasAPI - El Enrutador de IA Definitivo
cls
echo =======================================================
echo     WallasAPI — El Enrutador de IA Definitivo
echo =======================================================
echo.
echo Iniciando servidor en el puerto 8001...
echo.

:: Cambia el directorio actual para que sea exactamente donde está este script .bat
cd /d "%~dp0"

:: Ejecuta el script principal usando el VENV de D: (no toca disco C:)
"..\venv\Scripts\python.exe" start_proxy.py

:: Si el servidor se cae o cierras el programa, la consola pausará para mostrar el error.
pause
