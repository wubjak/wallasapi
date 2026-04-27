@echo off
chcp 65001 >nul

echo ================================================
echo   Subiendo WallasAPI a GitHub
echo   Usuario: wubjak
echo   Repo: wallasapi
echo ================================================
echo.

cd /d "D:\ProyectoIG\wallasAPI"

echo [1/3] Configurando remote origin...
git remote add origin https://github.com/wubjak/wallasapi.git 2>nul
if errorlevel 1 (
    echo [INFO] Remote ya existe. Actualizando...
    git remote set-url origin https://github.com/wubjak/wallasapi.git
)

echo [2/3] Cambiando branch a main...
git branch -M main

echo [3/3] Haciendo push a GitHub...
echo.
echo -----------------------------------------------
echo  ATENCION: Cuando pida password,
echo  pega tu Personal Access Token (NO tu password)
echo -----------------------------------------------
echo.
git push -u origin main

echo.
if errorlevel 1 (
    echo [ERROR] El push fallo. Verifica tu token.
    echo.
    echo  Posibles causas:
    echo  - No creaste el repo en github.com/new
    echo  - El token no tiene permiso 'repo'
    echo  - El token fue ingresado incorrectamente
    echo.
    pause
) else (
    echo [OK] WallasAPI subido exitosamente!
    echo    https://github.com/wubjak/wallasapi
    echo.
    pause
)
