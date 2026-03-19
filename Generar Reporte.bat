@echo off
chcp 65001 >nul
cd /d "%~dp0"

:: Detectar Python (probar python3 primero, luego python)
set PYTHON=
where python3 >nul 2>&1 && set PYTHON=python3
if not defined PYTHON (
    where python >nul 2>&1 && set PYTHON=python
)
if not defined PYTHON (
    echo.
    echo  ============================================
    echo   Python no esta instalado.
    echo   Descargalo en: https://python.org
    echo  ============================================
    echo.
    pause
    exit /b 1
)

:: Verificar que es Python 3
%PYTHON% -c "import sys; assert sys.version_info[0]>=3" >nul 2>&1 || (
    echo.
    echo  Se requiere Python 3. La version instalada es Python 2.
    echo  Descarga Python 3 en: https://python.org
    echo.
    pause
    exit /b 1
)

:: Instalar dependencias si faltan
%PYTHON% -c "import PIL" >nul 2>&1 || (
    echo Instalando dependencias ^(primera vez^)...
    %PYTHON% -m pip install pillow -q
)

:: Ejecutar la app
%PYTHON% app.py
if errorlevel 1 (
    echo.
    echo Ocurrio un error al ejecutar la aplicacion.
    pause
)
