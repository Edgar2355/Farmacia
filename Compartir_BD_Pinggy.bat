@echo off
chcp 65001 > nul
title Compartir Base de Datos MySQL (Tunel Pinggy.io) - Farmacia CUCEI

echo =======================================================================
echo        COMPARTIR BASE DE DATOS LOCAL (MYSQL 3306) CON EL EQUIPO
echo =======================================================================
echo.
echo  1. Asegurate de tener XAMPP / MySQL encendido en el puerto 3306.
echo  2. Si te pide contrasena ("password:"), solo presiona [ENTER].
echo  3. En unos segundos aparecera abajo tu URL real de Pinggy
echo     (empieza con "tcp://" y termina con un numero de puerto).
echo  4. Copia esa URL "tcp://..." y pasasela a tus companeros para que la
echo     peguen en el boton "Configurar Servidor / Pinggy" del Login.
echo.
echo  NOTA: No cierres esta ventana mientras tus companeros esten conectados.
echo =======================================================================
echo.

:: Verificar si el usuario tiene llave SSH; si no existe, generarla automaticamente
:: (Pinggy.io requiere una llave SSH o cierra la conexion si tardas en dar Enter)
if not exist "%USERPROFILE%\.ssh\id_ed25519" (
    if not exist "%USERPROFILE%\.ssh\id_rsa" (
        echo [Configuracion unica] Generando llave SSH local para conectar sin contrasena...
        if not exist "%USERPROFILE%\.ssh" mkdir "%USERPROFILE%\.ssh"
        ssh-keygen -t ed25519 -f "%USERPROFILE%\.ssh\id_ed25519" -N "" > nul 2>&1
        echo [OK] Llave SSH creada correctamente.
        echo.
    )
)

echo Conectando con el servidor de Pinggy.io, espera unos segundos...
echo.

ssh -p 443 -T -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL -o ServerAliveInterval=30 -R0:localhost:3306 tcp@a.pinggy.io

echo.
echo [Aviso] El tunel de Pinggy se ha cerrado.
pause
