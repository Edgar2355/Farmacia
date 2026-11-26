#!/usr/bin/env bash
# ==============================================================================
# Compartir Base de Datos MySQL Local (Puerto 3306) vía Pinggy.io en Linux/macOS
# ==============================================================================

echo "======================================================================="
echo "       COMPARTIR BASE DE DATOS LOCAL (MYSQL 3306) CON EL EQUIPO        "
echo "======================================================================="
echo ""
echo " 1. Asegúrate de tener MySQL / MariaDB encendido en el puerto 3306."
echo " 2. Si te pide contraseña ('password:'), solo presiona [ENTER]."
echo " 3. En unos segundos aparecerá abajo tu URL real de Pinggy"
echo "    (empieza con 'tcp://' y termina con un número de puerto)."
echo " 4. Copia esa URL 'tcp://...' y pásasela a tus compañeros para que la"
echo "    peguen en el botón 'Configurar Servidor / Pinggy' del Login."
echo ""
echo " NOTA: No cierres esta terminal mientras tus compañeros estén conectados."
echo "======================================================================="
echo ""

# Verificar si el usuario tiene llave SSH; si no existe, generarla automáticamente
if [ ! -f "$HOME/.ssh/id_ed25519" ] && [ ! -f "$HOME/.ssh/id_rsa" ]; then
    echo "[Configuración única] Generando llave SSH local para conectar sin contraseña..."
    mkdir -p "$HOME/.ssh"
    chmod 700 "$HOME/.ssh"
    ssh-keygen -t ed25519 -f "$HOME/.ssh/id_ed25519" -N "" >/dev/null 2>&1
    echo "[OK] Llave SSH creada correctamente."
    echo ""
fi

echo "Conectando con el servidor de Pinggy.io, espera unos segundos..."
echo ""

ssh -p 443 -T -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ServerAliveInterval=30 -R0:localhost:3306 tcp@a.pinggy.io

echo ""
echo "[Aviso] El túnel de Pinggy se ha cerrado."
