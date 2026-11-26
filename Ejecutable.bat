@echo off
chcp 65001 > nul
title Sistema Farmacia CUCEI

:: Asegurar que el script se ejecute en la carpeta donde esta guardado
cd /d "%~dp0"

set "VENV_DIR=Librerias"
set "VENV_PY=%~dp0%VENV_DIR%\Scripts\python.exe"
set "SCRIPT_NAME=Login-menu.py"
set "REQ_FILE=requirements.txt"

echo ===================================================
echo          INICIANDO SISTEMA FARMACIA CUCEI
echo ===================================================
echo.

:: 1. Detectar si el entorno virtual existe y si fue creado en esta misma ruta
set "RECREAR_VENV=0"
if not exist "%VENV_PY%" (
    set "RECREAR_VENV=1"
) else (
    "%VENV_PY%" --version > nul 2>&1
    if errorlevel 1 set "RECREAR_VENV=1"
)

if "%RECREAR_VENV%"=="0" goto :VERIFICAR_PAQUETES

:: Si existia una carpeta Librerias corrupta o movida de otra carpeta, limpiarla
if exist "%VENV_DIR%" (
    echo [Aviso] Limpiando entorno virtual anterior o movido de ruta...
    rmdir /s /q "%VENV_DIR%"
)

echo [1/3] Creando entorno virtual "%VENV_DIR%"...
echo Por favor, espere un momento...

:: Preferir Python 3.13 si esta disponible mediante py launcher, o usar python del PATH
py -3.13 --version > nul 2>&1
if not errorlevel 1 (
    py -3.13 -m venv "%VENV_DIR%"
) else (
    python -m venv "%VENV_DIR%"
)

if not exist "%VENV_PY%" (
    echo [ERROR] No se pudo crear el entorno virtual. Verifica que Python este instalado.
    pause
    exit /b 1
)

:VERIFICAR_PAQUETES
:: 2. Verificar que las librerias requeridas esten instaladas en el entorno virtual
"%VENV_PY%" -c "import mysql.connector, fpdf, dotenv, google.genai" > nul 2>&1
if not errorlevel 1 goto :EJECUTAR_APP

echo [2/3] Instalando dependencias desde "%REQ_FILE%"...
if exist "%REQ_FILE%" (
    "%VENV_PY%" -m pip install --upgrade pip
    "%VENV_PY%" -m pip install -r "%REQ_FILE%"
    if errorlevel 1 (
        echo [ERROR] Hubo un problema al instalar las librerias desde "%REQ_FILE%".
        pause
        exit /b 1
    )
) else (
    echo [ADVERTENCIA] No se encontro el archivo "%REQ_FILE%".
)
echo.
echo Instalacion completada con exito.
echo.

:EJECUTAR_APP
:: 3. Ejecutar el script principal directamente con el Python del entorno virtual
echo [Ejecutando] Iniciando "%SCRIPT_NAME%"...
echo.
"%VENV_PY%" "%SCRIPT_NAME%"

if errorlevel 1 (
    echo.
    echo [ERROR] El programa se cerro con un error.
    pause
)
